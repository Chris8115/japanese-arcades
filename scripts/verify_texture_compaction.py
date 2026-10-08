"""Independently verify cropped artwork, all remapped UVs, and geometry records.

Reads the untouched snapshots made by compact_cabinet_textures. Native mip
generation is checked separately in Minecraft; this check proves integer crop
alignment, retained RGBA bytes, every UV correspondence and unchanged geometry.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT/'src/main/resources/assets'
MODELS = ASSETS/'japanesearcades/models'
BACKUP = ROOT/'build/verification/texture-compaction/original'
REPORTS = ROOT/'art/performance/texture-compaction'
CROPS = {}
CHECKS = {'uv_points': 0, 'max_source_pixel_error': 0.0, 'obj_faces': 0,
          'json_faces': 0, 'blockbench_faces': 0, 'files_checked': [], 'textures_checked': []}


def resolve(resource, textures):
    while resource and resource.startswith('#'):
        resource = textures[resource[1:]]
    return resource


def pairs(uv):
    if isinstance(uv, dict):
        return list(uv.values())
    if uv and isinstance(uv[0], list):
        return uv
    return [uv[i:i+2] for i in range(0, len(uv), 2)]


def check_uv(old, new, crop, units=16, flipped=False):
    for source_point, target_point in zip(pairs(old), pairs(new), strict=True):
        for axis in (0, 1):
            source, target = source_point[axis], target_point[axis]
            if flipped and axis == 1:
                source, target = units-source, units-target
            if crop:
                before = source/units*crop['before_size'][axis]
                after = target/units*crop['after_size'][axis]+crop['rectangle'][axis]
            else:
                before, after = source, target
            error = abs(before-after)
            assert error < 1e-7, (source_point, target_point, crop, error)
            CHECKS['max_source_pixel_error'] = max(CHECKS['max_source_pixel_error'], error)
        CHECKS['uv_points'] += 1


def check_json(old, new, textures=None, bbtextures=None, path=''):
    assert type(old) is type(new), path
    if isinstance(old, dict):
        assert old.keys() == new.keys(), path
        if isinstance(old.get('textures'), dict):
            textures = {**(textures or {}), **old['textures']}
        crop = None
        if 'texture' in old and 'uv' in old:
            if bbtextures is not None:
                crop = bbtextures.get(old['texture'])
                if crop:
                    for a, b in zip(pairs(old['uv']), pairs(new['uv']), strict=True):
                        assert all(abs(a[i]-b[i]-crop['rectangle'][i]) < 1e-7 for i in (0, 1)), path
                else:
                    assert old['uv'] == new['uv'], path
                CHECKS['blockbench_faces'] += 1
            else:
                crop = CROPS.get(resolve(old['texture'], textures or {}))
                check_uv(old['uv'], new['uv'], crop)
                CHECKS['json_faces'] += 1
        for key in old:
            if key == 'uv' and 'texture' in old:
                continue
            check_json(old[key], new[key], textures, bbtextures, path+'/'+key)
    elif isinstance(old, list):
        assert len(old) == len(new), path
        for i, (a, b) in enumerate(zip(old, new, strict=True)):
            check_json(a, b, textures, bbtextures, path+'/'+str(i))
    else:
        assert old == new, (path, old, new)


def contexts(data, inherited=None):
    textures = {**(inherited or {}), **data.get('textures', {})}
    if data.get('loader') == 'neoforge:obj':
        yield data['model'], textures, data.get('flip_v', False), data.get('mtl_override')
    for child in data.get('children', {}).values():
        yield from contexts(child, textures)


def resource_path(resource):
    namespace, path = resource.split(':', 1)
    return ASSETS/namespace/path


def parse_obj(text):
    material, uv, faces, other = None, [], [], []
    for line in text.splitlines():
        if line.startswith('vt '):
            uv.append([float(value) for value in line.split()[1:3]])
        elif line.startswith('f '):
            points = [vertex.split('/') for vertex in line.split()[1:]]
            faces.append((material, points))
        else:
            other.append(line)
            if line.startswith('usemtl '):
                material = line[7:].strip()
    return uv, faces, other


def check_obj(path, old, new, binding):
    textures, flip, override = binding
    maps, material = {}, None
    libraries = [resource_path(override)] if override else [resource_path(line[7:].strip()) if ':' in line[7:] else path.parent/line[7:].strip()
                                                         for line in old.splitlines() if line.startswith('mtllib ')]
    for library in libraries:
        for line in library.read_text(encoding='utf-8').splitlines():
            if line.startswith('newmtl '):
                material = line[7:].strip()
            elif line.startswith('map_Kd '):
                maps[material] = resolve(line.split()[-1], textures)
    before_uv, before_faces, before_other = parse_obj(old)
    after_uv, after_faces, after_other = parse_obj(new)
    assert before_other == after_other, 'Geometry or OBJ configuration changed: '+str(path)
    assert len(before_faces) == len(after_faces)
    for (material, a), (other_material, b) in zip(before_faces, after_faces, strict=True):
        assert material == other_material
        assert len(a) == len(b)
        for va, vb in zip(a, b, strict=True):
            assert va[0] == vb[0] and va[2:] == vb[2:], 'Position/normal/color indices changed'
            index_a, index_b = int(va[1]), int(vb[1])
            ua = before_uv[index_a-1 if index_a > 0 else index_a]
            ub = after_uv[index_b-1 if index_b > 0 else index_b]
            check_uv(ua, ub, CROPS.get(maps.get(material)), 1, flip)
        CHECKS['obj_faces'] += 1


def main():
    paths = set()
    for manifest in sorted(REPORTS.glob('*.json')):
        if manifest.stem == 'verification':
            continue
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if 'textures' in data and isinstance(data['textures'], dict):
            CROPS.update(data['textures'])
            paths.update(data['files'])
    bindings = {}
    for path in MODELS.rglob('*.json'):
        for resource, textures, flip, override in contexts(json.loads(path.read_text(encoding='utf-8'))):
            bindings[resource_path(resource)] = (textures, flip, override)
    for resource, crop in CROPS.items():
        relative = Path('src/main/resources/assets')/resource.replace(':', '/textures/')
        relative = relative.with_suffix('.png')
        with Image.open(BACKUP/relative) as old, Image.open(ROOT/relative) as new:
            expected = old.crop(crop['rectangle']).convert('RGBA')
            actual = new.convert('RGBA')
            assert expected.size == actual.size and expected.tobytes() == actual.tobytes()
            assert hashlib.sha256(actual.tobytes()).hexdigest() == crop['retained_rgba_sha256']
            assert all(value % 16 == 0 for value in crop['rectangle'])
        CHECKS['textures_checked'].append(resource)
    for relative in sorted(paths):
        path, backup = ROOT/relative, BACKUP/relative
        if path.suffix == '.obj':
            check_obj(path, backup.read_text(encoding='utf-8'), path.read_text(encoding='utf-8'), bindings[path])
        elif path.suffix == '.json':
            check_json(json.loads(backup.read_text(encoding='utf-8')), json.loads(path.read_text(encoding='utf-8')))
        elif path.suffix == '.bbmodel':
            old, new = json.loads(backup.read_text(encoding='utf-8')), json.loads(path.read_text(encoding='utf-8'))
            bbtextures = {}
            for i, (a, b) in enumerate(zip(old['textures'], new['textures'], strict=True)):
                resource = a.get('namespace', 'japanesearcades')+':'+a.get('folder', 'block')+'/'+Path(a['name']).stem
                if resource in CROPS:
                    crop = CROPS[resource]
                    bbtextures[i] = crop
                    old_image = Image.open(io.BytesIO(base64.b64decode(a['source'].split(',', 1)[1])))
                    new_image = Image.open(io.BytesIO(base64.b64decode(b['source'].split(',', 1)[1])))
                    assert old_image.crop(crop['rectangle']).convert('RGBA').tobytes() == new_image.convert('RGBA').tobytes()
                    for key in ('width', 'height', 'uv_width', 'uv_height', 'source'):
                        a[key] = b[key]
            check_json(old, new, bbtextures=bbtextures)
        CHECKS['files_checked'].append(relative)
    CHECKS['passed'] = True
    CHECKS['pixels_saved'] = sum(crop['pixels_saved'] for crop in CROPS.values())
    CHECKS['native_mip_check'] = 'Separate Minecraft MipmapGenerator verification required for levels 0..4'
    (REPORTS/'verification.json').write_text(json.dumps(CHECKS, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: value if not isinstance(value, list) else len(value) for key, value in CHECKS.items()}, indent=2))


if __name__ == '__main__':
    main()
