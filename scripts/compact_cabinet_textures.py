"""Losslessly trim unused artwork sprite borders after cabinet export.

Only the explicitly selected artwork sprites are eligible. Source illustrations
remain untouched. Runtime OBJ/JSON UVs and editable geometry/Blockbench projects
are remapped together. Sixteen-pixel alignment and a sixteen-pixel sampling guard
preserve Minecraft's four mip levels. Running twice is a no-op.

Each affected cabinet generator calls compact_cabinet() after all its exports.
The command-line form handles already-exported assets and records before/after
pixel hashes and UV correspondence checks in art/performance/texture-compaction.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image

import audit_texture_uvs as audit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
MODELS = ASSETS / 'models'
ART = ROOT / 'art'
REPORTS = ART / 'performance/texture-compaction'

# Asset-directory name, source generator, eligible runtime artwork sprites.
CABINETS = {
    'chunithm': ('chunithm', 'make_chunithm_model.py', ['chunithm_branding', 'chunithm_display']),
    'nostalgia': ('nostalgia-op3', 'make_nostalgia_model.py', ['nostalgia_artwork', 'nostalgia_marquee']),
    'wacca': ('wacca', 'make_wacca_model.py', ['wacca_branding', 'wacca_display']),
    'chrono_circle': ('chrono_circle', 'make_chrono_circle_model.py', ['chrono_circle_header', 'chrono_circle_display']),
    'iidx': ('beatmania-iidx-lightning', 'make_iidx_model.py', ['beatmania_iidx_lightning_banners', 'beatmania_iidx_lightning_marquee', 'beatmania_iidx_lightning_display']),
    'ddr': ('ddr_supernova', 'make_ddr_model.py', ['ddr_supernova_display', 'ddr_supernova_header']),
    'maimai': ('maimai', 'make_maimai_model.py', ['maimai_display', 'maimai_header']),
    'ongeki': ('ongeki', 'make_ongeki_model.py', ['ongeki_marquee', 'ongeki_display']),
    'valkyrie': ('sound-voltex-valkyrie', 'make_valkyrie_model.py', ['valkyrie_branding', 'valkyrie_display']),
    'beatstream': ('beatstream', 'make_beatstream_model.py', ['beatstream_topper', 'beatstream_screens']),
    'project_diva': ('project_diva', 'make_project_diva_model.py', ['project_diva_header', 'project_diva_display']),
    'groove_coaster': ('groove_coaster', 'make_groove_coaster_model.py', ['groove_coaster_display']),
    'museca': ('museca', 'make_museca_model.py', ['museca_display', 'museca_marquee']),
    'nemsys': ('sound-voltex-nemsys', 'make_nemsys_model.py', ['sound_voltex_nemsys_display', 'sound_voltex_nemsys_marquee']),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def crop_transform(uv, crop, scale=16):
    """Model units -> source pixels -> cropped pixels -> model units."""
    width, height = crop['before_size']
    left, top, right, bottom = crop['rectangle']
    result = [(uv[0] / scale * width - left) / (right-left) * scale,
              (uv[1] / scale * height - top) / (bottom-top) * scale]
    restored = [result[0] / scale * (right-left) + left,
                result[1] / scale * (bottom-top) + top]
    error = max(abs(restored[i] - uv[i] / scale * [width, height][i]) for i in (0, 1))
    crop['max_pixel_coordinate_error'] = max(crop['max_pixel_coordinate_error'], error)
    crop['uv_points_checked'] += 1
    return result


def remap_coordinates(uv, crop):
    if isinstance(uv, dict):
        return {key: crop_transform(point, crop) for key, point in uv.items()}
    if uv and isinstance(uv[0], list):
        return [crop_transform(point, crop) for point in uv]
    return [number for index in range(0, len(uv), 2)
            for number in crop_transform(uv[index:index+2], crop)]


def remap_json(data, crops, textures=None):
    """Runtime and authoring JSON share the same model-unit face UV convention."""
    changed = False
    if isinstance(data, list):
        for child in data:
            changed |= remap_json(child, crops, textures)
    elif isinstance(data, dict):
        textures = {**(textures or {}), **(data.get('textures', {}) if isinstance(data.get('textures'), dict) else {})}
        if isinstance(data.get('texture'), str) and 'uv' in data:
            texture = audit.resolve_texture(data['texture'], textures)
            if texture in crops:
                data['uv'] = remap_coordinates(data['uv'], crops[texture])
                changed = True
        for key, child in data.items():
            if key not in ('textures', 'uv'):
                changed |= remap_json(child, crops, textures)
    return changed


def obj_contexts(data, textures=None):
    textures = {**(textures or {}), **data.get('textures', {})}
    if data.get('loader') == 'neoforge:obj':
        yield audit.path_for(data['model']), textures, bool(data.get('flip_v', False)), data.get('mtl_override')
    for child in data.get('children', {}).values():
        yield from obj_contexts(child, textures)


def remap_obj(path, contexts, crops):
    lines = path.read_text(encoding='utf-8').splitlines()
    vertices = [tuple(float(value) for value in line.split()[1:3]) for line in lines if line.startswith('vt ')]
    # Shared OBJ exports must resolve materials identically in every model using
    # them. Fail before writing if a future model introduces a conflicting alias.
    material_transforms = {}
    for textures, flip_v, override in contexts:
        libraries = {}
        if override:
            libraries.update(audit.material_maps(audit.path_for(override)))
        else:
            for line in lines:
                if line.startswith('mtllib '):
                    name = line[7:].strip()
                    libraries.update(audit.material_maps(audit.path_for(name) if ':' in name else path.parent/name))
        current = {material: (audit.resolve_texture(texture, textures), flip_v) for material, texture in libraries.items()}
        if material_transforms and current != material_transforms:
            raise ValueError(f'Inconsistent material aliases for {path}')
        material_transforms = current
    material, output, new_vertices, mapping = None, [], [], {}
    changed = False
    for line in lines:
        if line.startswith('usemtl '):
            material = line[7:].strip()
        if line.startswith('f '):
            resource, flip_v = material_transforms.get(material, (None, False))
            if resource in crops:
                crop = crops[resource]
                points = []
                for vertex in line.split()[1:]:
                    fields = vertex.split('/')
                    if len(fields) < 2 or not fields[1]:
                        raise ValueError(f'Explicit UVs required for cropped texture: {path}')
                    index = int(fields[1])
                    absolute_index = index-1 if index > 0 else len(vertices)+index
                    key = (absolute_index, resource, flip_v)
                    if key not in mapping:
                        u, v = vertices[absolute_index]
                        point = crop_transform([u, 1-v if flip_v else v], crop, 1)
                        if flip_v:
                            point[1] = 1-point[1]
                        new_vertices.append('vt ' + ' '.join(format(n, '.16g') for n in point))
                        mapping[key] = len(vertices)+len(new_vertices)
                    fields[1] = str(mapping[key])
                    points.append('/'.join(fields))
                line = 'f ' + ' '.join(points)
                changed = True
        output.append(line)
    if not changed:
        return None
    # All indices are absolute. Put the new vt records before any faces.
    first_face = next(i for i, line in enumerate(output) if line.startswith('f '))
    output[first_face:first_face] = new_vertices
    return ('\n'.join(output) + '\n').encode('utf-8')


def remap_blockbench(data, crops, texture_bytes):
    mappings = {}
    for index, texture in enumerate(data['textures']):
        resource = texture.get('namespace', 'japanesearcades') + ':' + texture.get('folder', 'block').strip('/') + '/' + Path(texture['name']).stem
        if resource in crops:
            crop = crops[resource]
            left, top, right, bottom = crop['rectangle']
            if [texture['width'], texture['height']] != crop['before_size']:
                raise ValueError('Blockbench texture size does not match runtime texture: ' + resource)
            mappings[index] = (left, top)
            texture.update(width=right-left, height=bottom-top, uv_width=right-left, uv_height=bottom-top,
                           source='data:image/png;base64,' + base64.b64encode(texture_bytes[resource]).decode('ascii'))
    for element in data['elements']:
        for face in element.get('faces', {}).values():
            if face.get('texture') in mappings:
                offset = mappings[face['texture']]
                if isinstance(face['uv'], dict):
                    face['uv'] = {key: [v-offset[i] for i, v in enumerate(point)] for key, point in face['uv'].items()}
                else:
                    face['uv'] = [v-offset[i % 2] for i, v in enumerate(face['uv'])]
    return bool(mappings)


def compact_cabinet(name, *, dry_run=False):
    art_name, generator, names = CABINETS[name]
    resources = {'japanesearcades:block/' + value for value in names}
    model_data = {path: json.loads(path.read_text(encoding='utf-8')) for path in sorted(MODELS.rglob('*.json'))}
    audit.USAGE.clear()
    audit.obj_usage.cache_clear()
    for path, data in model_data.items():
        audit.inspect_model(data, {}, path.relative_to(MODELS).as_posix())
    crops, writes, texture_bytes = {}, {}, {}
    for resource in sorted(resources):
        references = audit.USAGE.get(resource)
        if not references:
            raise ValueError('No runtime model uses ' + resource)
        path = audit.path_for(resource, 'textures', '.png')
        if path.with_name(path.name + '.mcmeta').exists():
            raise ValueError('Animated sprites are deliberately excluded: ' + resource)
        with Image.open(path) as source:
            source.load()
            width, height = source.size
            coords = [uv for polygon, _ in references for uv in polygon]
            bounds = [min(uv[0] for uv in coords)*width, min(uv[1] for uv in coords)*height,
                      max(uv[0] for uv in coords)*width, max(uv[1] for uv in coords)*height]
            if bounds[0] < -1e-5 or bounds[1] < -1e-5 or bounds[2] > width+1e-5 or bounds[3] > height+1e-5:
                raise ValueError('Wrapped/repeated UVs cannot be cropped: ' + resource)
            rectangle = [max(0, math.floor(round(bounds[0], 5)/16)*16-16),
                         max(0, math.floor(round(bounds[1], 5)/16)*16-16),
                         min(width, math.ceil(round(bounds[2], 5)/16)*16+16),
                         min(height, math.ceil(round(bounds[3], 5)/16)*16+16)]
            if rectangle == [0, 0, width, height]:
                continue
            cropped = source.crop(rectangle)
            assert all(value % 16 == 0 for value in rectangle), (resource, rectangle)
            # Minecraft's mip generator chooses an alpha blend path globally.
            # Require cropping to preserve the existence of fully transparent
            # pixels as well as every retained RGBA byte.
            old_transparent = 'A' in source.getbands() and source.getchannel('A').getextrema()[0] == 0
            new_transparent = 'A' in cropped.getbands() and cropped.getchannel('A').getextrema()[0] == 0
            if old_transparent != new_transparent:
                raise ValueError('Crop changes mip alpha mode: ' + resource)
            stream = io.BytesIO()
            cropped.save(stream, format='PNG')
            texture_bytes[resource] = stream.getvalue()
            writes[path] = stream.getvalue()
            crops[resource] = {'before_size': [width, height], 'after_size': list(cropped.size),
                               'rectangle': rectangle, 'sampled_pixel_bounds': bounds,
                               'source_rgba_sha256': digest(source.convert('RGBA').tobytes()),
                               'retained_rgba_sha256': digest(cropped.convert('RGBA').tobytes()),
                               'pixels_saved': width*height-cropped.width*cropped.height,
                               'mip_alignment': 16, 'sampling_guard_pixels': 16,
                               'has_fully_transparent_pixels': bool(old_transparent),
                               'uv_points_checked': 0, 'max_pixel_coordinate_error': 0,
                               'model_references': sorted({model for _, model in references})}
    if not crops:
        return {'cabinet': name, 'changed': False, 'pixels_saved': 0}
    contexts = {}
    for path, data in model_data.items():
        for obj_path, textures, flip_v, override in obj_contexts(data):
            contexts.setdefault(obj_path, []).append((textures, flip_v, override))
        if remap_json(data, crops):
            writes[path] = json_bytes(data)
    for path, bindings in contexts.items():
        if not any(audit.resolve_texture(value, textures) in crops
                   for textures, _, _ in bindings for value in textures.values()):
            continue
        updated = remap_obj(path, bindings, crops)
        if updated is not None:
            writes[path] = updated
    geometry_path = ART / art_name / 'geometry.json'
    geometry = json.loads(geometry_path.read_text(encoding='utf-8'))
    if remap_json(geometry, crops):
        writes[geometry_path] = json_bytes(geometry)
    for path in (ART/art_name).glob('*.bbmodel'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if remap_blockbench(data, crops, texture_bytes):
            writes[path] = json_bytes(data)
    receipt = {'cabinet': name, 'generator': generator, 'changed': True,
               'method': 'Integer pixel crop; remapped source-pixel UV coordinates; no resampling or geometry changes',
               'pixels_saved': sum(crop['pixels_saved'] for crop in crops.values()),
               'textures': crops, 'files': [path.relative_to(ROOT).as_posix() for path in sorted(writes)]}
    if not dry_run:
        # All validation and serialization have succeeded before the first write.
        backup = ROOT / 'build/verification/texture-compaction/original'
        for path, content in writes.items():
            original = backup / path.relative_to(ROOT)
            original.parent.mkdir(parents=True, exist_ok=True)
            if not original.exists():
                original.write_bytes(path.read_bytes())
            path.write_bytes(content)
        REPORTS.mkdir(parents=True, exist_ok=True)
        (REPORTS/f'{name}.json').write_bytes(json_bytes(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cabinet', choices=list(CABINETS), action='append')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    for cabinet in args.cabinet or CABINETS:
        result = compact_cabinet(cabinet, dry_run=args.dry_run)
        print(json.dumps({key: result[key] for key in ('cabinet', 'changed', 'pixels_saved')}))


if __name__ == '__main__':
    main()
