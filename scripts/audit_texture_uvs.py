"""Read-only coverage bounds for textures actually used by exported model faces."""
from __future__ import annotations
import collections
import functools
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets'
MODELS = ASSETS / 'japanesearcades/models'
TEXTURES = ASSETS / 'japanesearcades/textures'
USAGE = collections.defaultdict(list)
WARNINGS = []


def path_for(resource, category='', extension=''):
    namespace, path = resource.split(':', 1)
    return ASSETS / namespace / category / (path + extension)


@functools.lru_cache(None)
def material_maps(path):
    material, result = None, {}
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'newmtl':
            material = ' '.join(parts[1:])
        elif parts[0] == 'map_Kd':
            result[material] = parts[-1]
    return result


@functools.lru_cache(None)
def obj_usage(path, override):
    uv, material, libraries, faces = [], None, {}, []
    if override:
        libraries.update(material_maps(path_for(override)))
    for line in path.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'mtllib' and not override:
            name = ' '.join(parts[1:])
            library = path_for(name) if ':' in name else path.parent / name
            libraries.update(material_maps(library))
        elif parts[0] == 'usemtl':
            material = ' '.join(parts[1:])
        elif parts[0] == 'vt':
            uv.append(tuple(float(v) for v in parts[1:3]))
        elif parts[0] == 'f':
            indices = [point.split('/') for point in parts[1:]]
            if any(len(point) < 2 or not point[1] for point in indices):
                points = [(0, 0), (0, 1), (1, 1), (1, 0)]
            else:
                points = [uv[int(point[1])-1 if int(point[1]) > 0 else int(point[1])] for point in indices]
            faces.append((material, points))
    return [(libraries.get(material, material), points) for material, points in faces]


def resolve_texture(name, textures):
    seen = set()
    while name and name.startswith('#') and name not in seen:
        seen.add(name)
        name = textures.get(name[1:])
    return name


def add_usage(name, textures, points, model):
    resource = resolve_texture(name, textures)
    if resource and resource.startswith('japanesearcades:'):
        USAGE[resource].append((points, model))


def inspect_model(data, inherited, model, depth=0):
    if depth > 12:
        raise ValueError('Model inheritance cycle: ' + model)
    textures = dict(inherited)
    textures.update(data.get('textures', {}))
    if data.get('loader') == 'neoforge:obj':
        for material, points in obj_usage(path_for(data['model']), data.get('mtl_override')):
            points = [(u, 1-v if data.get('flip_v', False) else v) for u, v in points]
            add_usage(material, textures, points, model)
    elif data.get('loader') == 'neoforge:composite':
        for child in data['children'].values():
            inspect_model(child, textures, model, depth+1)
    elif 'elements' in data:
        for element in data['elements']:
            for face in element.get('faces', {}).values():
                u0, v0, u1, v1 = face.get('uv', [0, 0, 16, 16])
                add_usage(face['texture'], textures, [(u0/16, v0/16), (u1/16, v0/16), (u1/16, v1/16), (u0/16, v1/16)], model)
    elif data.get('parent', '').startswith('japanesearcades:'):
        parent = json.loads(path_for(data['parent'], 'models', '.json').read_text(encoding='utf-8'))
        parent['textures'] = {**parent.get('textures', {}), **textures}
        inspect_model(parent, {}, model, depth+1)


def main():
    for path in sorted(MODELS.rglob('*.json')):
        try:
            inspect_model(json.loads(path.read_text(encoding='utf-8')), {}, path.relative_to(MODELS).as_posix())
        except (ValueError, KeyError, FileNotFoundError) as exc:
            WARNINGS.append({'model': path.relative_to(MODELS).as_posix(), 'error': str(exc)})
    rows = []
    for resource, references in USAGE.items():
        path = path_for(resource, 'textures', '.png')
        if not path.is_file():
            WARNINGS.append({'resource': resource, 'error': 'texture file not found'})
            continue
        with Image.open(path) as im:
            width, height = im.size
        if width * height < 512 * 512:
            continue
        meta = path.with_name(path.name + '.mcmeta')
        animation = json.loads(meta.read_text(encoding='utf-8')).get('animation') if meta.exists() else None
        if animation:
            width, height = animation.get('width', min(width, height)), animation.get('height', min(width, height))
        coords = [uv for points, _ in references for uv in points]
        min_u, min_v = min(uv[0] for uv in coords), min(uv[1] for uv in coords)
        max_u, max_v = max(uv[0] for uv in coords), max(uv[1] for uv in coords)
        # Include a 16px source guard and align boundaries to the original mip
        # grid. This is conservative: the present audit never alters pixels/UVs.
        left = max(0, math.floor(min_u * width / 16) * 16 - 16)
        top = max(0, math.floor(min_v * height / 16) * 16 - 16)
        right = min(width, math.ceil(max_u * width / 16) * 16 + 16)
        bottom = min(height, math.ceil(max_v * height / 16) * 16 + 16)
        crop_w, crop_h = right-left, bottom-top
        unique = {tuple(tuple(round(v, 7) for v in uv) for uv in points) for points, _ in references}
        mask = Image.new('1', (width, height))
        draw = ImageDraw.Draw(mask)
        whole_uv_faces = 0
        for points in unique:
            us, vs = [p[0] for p in points], [p[1] for p in points]
            if min(us) <= 0 and max(us) >= 1 and min(vs) <= 0 and max(vs) >= 1:
                whole_uv_faces += 1
            draw.polygon([(u * width, v * height) for u, v in points], fill=1)
        referenced_pixels = sum(mask.histogram()[1:])
        rows.append({'resource': resource, 'dimensions': [width, height], 'animated': bool(animation),
                     'uv_bounds': [min_u, min_v, max_u, max_v], 'unique_uv_polygons': len(unique),
                     'whole_texture_uv_faces': whole_uv_faces,
                     'referenced_pixel_coverage_fraction': referenced_pixels / (width*height),
                     'guarded_crop_rectangle': [left, top, right, bottom], 'guarded_crop_dimensions': [crop_w, crop_h],
                     'lossless_guarded_crop_pixel_savings': max(0, width*height-crop_w*crop_h),
                     'lossless_guarded_crop_mip_bytes_saved': round(max(0, width*height-crop_w*crop_h)*4*4/3),
                     'models': sorted({model for _, model in references})})
    rows.sort(key=lambda row: row['lossless_guarded_crop_pixel_savings'], reverse=True)
    report = {'method': 'Every exported model OBJ/JSON face; resolved material texture aliases and flip_v;16px guarded/aligned crop bounds',
              'caveats': ['UV polygon raster coverage is diagnostic; models may use islands spanning the full image.',
                          'Crop candidates still require authoring/runtime remap and mip verification.',
                          'Animated textures require identical crop on every frame, not just the source strip.'],
              'warnings': WARNINGS, 'textures': rows,
              'summed_guarded_crop_pixel_savings': sum(row['lossless_guarded_crop_pixel_savings'] for row in rows)}
    destination = ROOT / 'art/performance/texture-uv-audit.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'warnings': WARNINGS, 'summed_guarded_crop_pixel_savings': report['summed_guarded_crop_pixel_savings'],
                      'best_candidates': [{k:v for k,v in row.items() if k != 'models'} for row in rows[:25]]}, indent=2))


if __name__ == '__main__':
    main()
