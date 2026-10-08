"""Read-only audit of exported models, texture sprites and the release archive.

This reports counts and memory estimates, not FPS predictions. It does not resize
or modify runtime assets. Animated PNG source memory and stitched-frame memory
are reported separately. Actual atlas allocations require native-client capture.
"""
from __future__ import annotations

import argparse
import collections
import functools
import hashlib
import json
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / 'src/main/resources'
ASSETS = RESOURCES / 'assets/japanesearcades'
MODELS = ASSETS / 'models'
TEXTURES = ASSETS / 'textures'
MIB = 1024 * 1024
CABINETS = ('nostalgia_op3', 'beatstream', 'sound_voltex_valkyrie', 'sound_voltex_nemsys',
            'wacca', 'chunithm', 'ongeki', 'groove_coaster', 'museca', 'project_diva',
            'chrono_circle', 'music_diver', 'popn_music', 'maimai', 'ddr_supernova',
            'beatmania_iidx_lightning', 'taiko', 'initial_d', 'jubeat')


def mip_bytes(width, height, levels=4):
    return sum(max(1, width >> i) * max(1, height >> i) * 4 for i in range(levels + 1))


def resource_path(resource, kind='models', extension='.json'):
    namespace, path = resource.split(':', 1)
    return RESOURCES / 'assets' / namespace / kind / (path + extension)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def count_geometry(data, visited):
    if data.get('loader') == 'neoforge:obj':
        path = resource_path(data['model'], '', '')
        return sum(line.startswith('f ') for line in path.read_text(encoding='utf-8').splitlines())
    if data.get('loader') == 'neoforge:composite':
        return sum(count_geometry(child, visited) for child in data['children'].values())
    if 'elements' in data:
        return sum(len(element.get('faces', {})) for element in data['elements'])
    parent = data.get('parent', '')
    if parent.startswith('japanesearcades:') and parent not in visited:
        return count_geometry(json.loads(resource_path(parent).read_text(encoding='utf-8')), visited | {parent})
    return 0


@functools.lru_cache(None)
def model_count(resource):
    return count_geometry(json.loads(resource_path(resource).read_text(encoding='utf-8')), {resource})


def cabinet_counts():
    result = []
    for cabinet in CABINETS:
        variants = json.loads((ASSETS / 'blockstates' / (cabinet + '.json')).read_text(encoding='utf-8'))['variants']
        # A full north-facing assembled object contains every part/side variant
        # once. Alternate compass facings are rotations, not additional pieces.
        north = [(state, spec) for state, spec in variants.items() if 'facing=north' in state.split(',')]
        rows = [{'state': state, 'model': spec['model'], 'faces': model_count(spec['model'])} for state, spec in north]
        full = model_count('japanesearcades:item/' + cabinet)
        gui = model_count('japanesearcades:item/gui/' + cabinet)
        result.append({'id': cabinet, 'world_faces': sum(row['faces'] for row in rows),
                       'full_item_faces': full, 'gui_faces': gui, 'world_parts': rows})
    return sorted(result, key=lambda row: row['world_faces'], reverse=True)


def references():
    refs = collections.defaultdict(list)
    for path in RESOURCES.rglob('*.json'):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue
        for value in set(strings(data)):
            if value.startswith('japanesearcades:'):
                refs[value].append(path.relative_to(ROOT).as_posix())
    return refs


def texture_audit(refs, exact_replication):
    rows, byte_groups, decoded_groups = [], collections.defaultdict(list), collections.defaultdict(list)
    for path in sorted(TEXTURES.rglob('*.png')):
        relative = path.relative_to(TEXTURES).as_posix()
        resource = 'japanesearcades:' + relative[:-4]
        raw = path.read_bytes()
        with Image.open(path) as source:
            width, height, mode = source.width, source.height, source.mode
            image = source.convert('RGBA')
        meta_path = path.with_name(path.name + '.mcmeta')
        metadata = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.is_file() else {}
        animation = metadata.get('animation')
        if animation is not None:
            if 'width' in animation:
                frame_w = animation['width']
                frame_h = animation.get('height', height)
            elif 'height' in animation:
                frame_w, frame_h = width, animation['height']
            else:
                frame_w = frame_h = min(width, height)
        else:
            frame_w, frame_h = width, height
        category = relative.split('/')[0]
        atlas = 'blocks' if category in ('block', 'item') else 'paintings' if category == 'painting' else 'direct/other'
        byte_hash = hashlib.sha256(raw).hexdigest()
        decoded_hash = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
        byte_groups[byte_hash].append(resource)
        decoded_groups[decoded_hash].append(resource)
        replicate = 1
        if exact_replication and min(width, height) >= 512:
            for factor in (2, 4, 8, 16):
                if width % factor or height % factor:
                    break
                tiny = image.resize((width // factor, height // factor), Image.Resampling.NEAREST)
                restored = tiny.resize(image.size, Image.Resampling.NEAREST)
                if ImageChops.difference(image, restored).getbbox(alpha_only=False) is None:
                    replicate = factor
                else:
                    break
        rows.append({'resource': resource, 'file': path.relative_to(ROOT).as_posix(), 'dimensions': [width, height],
                     'mode': mode, 'png_bytes': len(raw), 'decoded_rgba_bytes': width * height * 4,
                     'atlas': atlas, 'animated': animation is not None,
                     'frame_dimensions': [frame_w, frame_h], 'frame_count': width // frame_w * (height // frame_h),
                     'frame_rgba_bytes': frame_w * frame_h * 4, 'frame_rgba_with_4_mips': mip_bytes(frame_w, frame_h),
                     'byte_sha256': byte_hash, 'decoded_rgba_sha256': decoded_hash,
                     'resource_json_references': refs.get(resource, []),
                     'exact_nearest_replication_factor': replicate})
    by_resource = {row['resource']: row for row in rows}
    duplicate_rows = []
    for group in decoded_groups.values():
        if len(group) > 1:
            atlases = collections.defaultdict(list)
            for resource in group:
                atlases[by_resource[resource]['atlas']].append(resource)
            saved = sum(sum(by_resource[resource]['frame_rgba_with_4_mips'] for resource in members[1:])
                        for atlas, members in atlases.items() if atlas != 'direct/other')
            duplicate_rows.append({'resources': group, 'exact_pixels': True,
                                   'same_atlas_redundant_sprite_bytes_with_mips': saved})
    return rows, duplicate_rows


def archive_audit(path):
    extensions, categories = collections.defaultdict(lambda: [0, 0, 0]), collections.defaultdict(lambda: [0, 0, 0])
    entries = []
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            extension = Path(item.filename).suffix or '<none>'
            category = '/'.join(item.filename.split('/')[:4]) if item.filename.startswith('assets/') else item.filename.split('/')[0]
            for key, table in ((extension, extensions), (category, categories)):
                table[key][0] += 1
                table[key][1] += item.file_size
                table[key][2] += item.compress_size
            entries.append({'path': item.filename, 'uncompressed': item.file_size, 'compressed': item.compress_size})
    return {'file': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size, 'extensions_count_uncompressed_compressed': dict(extensions),
            'categories_count_uncompressed_compressed': dict(categories),
            'largest_entries': sorted(entries, key=lambda row: row['compressed'], reverse=True)[:30]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar', type=Path, default=ROOT / 'build/libs/japanesearcades-0.1.0.jar')
    parser.add_argument('--output', type=Path, default=ROOT / 'art/performance/asset-audit.json')
    parser.add_argument('--exact-replication', action='store_true', help='Find losslessly reducible nearest-neighbor-expanded images.')
    args = parser.parse_args()
    refs = references()
    textures, duplicates = texture_audit(refs, args.exact_replication)
    atlas_groups = collections.defaultdict(list)
    for texture in textures:
        atlas_groups[texture['atlas']].append(texture)
    atlas_totals = {atlas: {'sprite_count': len(group),
                           'source_decoded_bytes': sum(row['decoded_rgba_bytes'] for row in group),
                           'frame_pixels': sum(row['frame_rgba_bytes'] // 4 for row in group),
                           'sprite_frame_bytes_with_mips': sum(row['frame_rgba_with_4_mips'] for row in group)}
                    for atlas, group in atlas_groups.items()}
    unused = [row['resource'] for row in textures if row['atlas'] == 'blocks' and not row['resource_json_references']]
    report = {'method': 'Actual exported OBJ f records, JSON face declarations, PNG decoded dimensions and native animation metadata; no FPS inference',
              'notes': ['Block/item directory sprites are stitched even when no model references them.',
                        'Unreferenced candidates require code/MTL/dynamic lookup review before removal.',
                        'Atlas byte figures below are summed sprite area, not power-of-two stitched allocation.',
                        'Painting/item texture copies serve separate atlases; eliminating a file copy alone does not reduce GPU memory.'],
              'atlas_sprite_totals': atlas_totals, 'textures': sorted(textures, key=lambda row: row['frame_rgba_with_4_mips'], reverse=True),
              'decoded_identical_groups': duplicates, 'unreferenced_block_item_candidates': unused,
              'cabinet_faces': cabinet_counts(), 'release_archive': archive_audit(args.jar)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'atlas_totals': atlas_totals,
                      'unreferenced_candidates': unused,
                      'exact_replicated': [{'resource': row['resource'], 'factor': row['exact_nearest_replication_factor']}
                                           for row in textures if row['exact_nearest_replication_factor'] > 1],
                      'same_atlas_duplicate_mip_bytes': sum(row['same_atlas_redundant_sprite_bytes_with_mips'] for row in duplicates),
                      'cabinet_faces': [{key: value for key, value in row.items() if key != 'world_parts'} for row in report['cabinet_faces']],
                      'jar_sha256': report['release_archive']['sha256']}, indent=2))


if __name__ == '__main__':
    main()
