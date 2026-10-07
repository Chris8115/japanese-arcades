"""Audit/optimize exported arcade models, leaving editable art and texture pixels intact.

python scripts/optimize_models.py --write
python scripts/optimize_models.py --check --report build/verification/model-audit.json

Run after an individual model generator, before building. A normal Gradle build
uses the checked-in optimized assets and does not require Python or Pillow.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets'
CATALOG = ASSETS / 'funpackcustom'


def local_resource(identifier, prefix='', suffix=''):
    namespace, name = identifier.split(':', 1)
    return ASSETS / namespace / (prefix + name + suffix)


def children(model):
    return model.get('children', {}).values()


def optimize_json(model, inherited=None):
    from catalog_json_geometry import optimize_model
    textures = {**(inherited or {}), **model.get('textures', {})}
    # Resolve aliases in a temporary effective model, retaining the original texture
    # declarations and parent/child structure in the exported result.
    effective = {**model, 'textures': textures}
    result, stats = optimize_model(effective, ASSETS)
    if 'textures' in model:
        result['textures'] = copy.deepcopy(model['textures'])
    else:
        result.pop('textures', None)
    for name, child in model.get('children', {}).items():
        result['children'][name], child_stats = optimize_json(child, textures)
        for key, value in child_stats.items():
            if isinstance(value, (int, float)):
                stats[key] = stats.get(key, 0) + value
    return result, stats


def audit():
    """Count actual exported source faces, following parents and composite children."""
    models = {}
    for path in sorted((CATALOG / 'models').rglob('*.json')):
        models[path] = json.loads(path.read_text(encoding='utf-8'))
    obj_counts = {}
    for path in sorted((CATALOG / 'models').rglob('*.obj')):
        lines = path.read_text(encoding='utf-8').splitlines()
        obj_counts[path] = {
            'faces': sum(line.startswith('f ') for line in lines),
            'vertices': sum(line.startswith('v ') for line in lines),
            'uvs': sum(line.startswith('vt ') for line in lines),
        }

    def faces(model, seen=()):
        count = sum(len(e['faces']) for e in model.get('elements', []))
        if model.get('loader') == 'neoforge:obj':
            path = local_resource(model['model'])
            assert path in obj_counts, f'Missing OBJ: {path}'
            count += obj_counts[path]['faces']
        for child in children(model):
            count += faces(child, seen)
        parent = model.get('parent', '')
        if not count and parent.startswith('funpackcustom:'):
            path = local_resource(parent, 'models/', '.json')
            assert path in models and path not in seen, f'Missing/cyclic model parent: {parent}'
            count = faces(models[path], (*seen, path))
        return count

    def validate(model, inherited=None):
        textures = {**(inherited or {}), **model.get('textures', {})}
        for key, identifier in textures.items():
            seen = set()
            while identifier.startswith('#'):
                assert identifier not in seen, f'Cyclic texture reference: {key}'
                seen.add(identifier)
                assert identifier[1:] in textures, f'Unresolved texture: {identifier}'
                identifier = textures[identifier[1:]]
            if identifier.startswith('funpackcustom:'):
                assert local_resource(identifier, 'textures/', '.png').is_file(), identifier
        for element in model.get('elements', []):
            assert len(element['from']) == len(element['to']) == 3
            assert all(b >= a for a, b in zip(element['from'], element['to'])), element.get('name')
            for face in element['faces'].values():
                if face['texture'].startswith('#'):
                    assert face['texture'][1:] in textures, face['texture']
        for child in children(model):
            validate(child, textures)

    for model in models.values():
        validate(model)
    textures = []
    for path in sorted((CATALOG / 'textures').rglob('*.png')):
        with Image.open(path) as image:
            width, height = image.size
        textures.append({'path': path.relative_to(CATALOG).as_posix(), 'width': width, 'height': height,
                         'animated': path.with_suffix('.png.mcmeta').is_file(),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        'item_source_faces': {path.stem: faces(model) for path, model in models.items() if path.parent.name == 'item'},
        'json_source_faces': sum(sum(len(e['faces']) for e in m.get('elements', []))
                                 for model in models.values() for m in walk(model)),
        'obj_source_faces': sum(v['faces'] for v in obj_counts.values()),
        'obj_vertices': sum(v['vertices'] for v in obj_counts.values()),
        'model_bytes': sum(path.stat().st_size for path in (CATALOG / 'models').rglob('*') if path.is_file()),
        'textures': textures,
    }


def walk(model):
    yield model
    for child in children(model):
        yield from walk(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true', help='Apply conservative geometry optimizations.')
    mode.add_argument('--check', action='store_true', help='Fail if an export still needs optimization.')
    parser.add_argument('--report', type=Path, help='Save the complete machine-readable audit.')
    args = parser.parse_args()
    before = audit()
    changes = {}
    if args.write or args.check:
        from obj_mesh_optimizer import optimize_obj
        for path in sorted((CATALOG / 'models').rglob('*.json')):
            source = json.loads(path.read_text(encoding='utf-8'))
            result, stats = optimize_json(source)
            if result != source:
                changes[path.relative_to(CATALOG).as_posix()] = stats
                if args.write:
                    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        for path in sorted((CATALOG / 'models').rglob('*.obj')):
            source = path.read_text(encoding='utf-8')
            result, stats = optimize_obj(source)
            if result != source:
                changes[path.relative_to(CATALOG).as_posix()] = stats
                if args.write:
                    path.write_text(result, encoding='utf-8')
    after = audit() if args.write else before
    assert before['textures'] == after['textures'], 'The optimizer must never modify textures.'
    report = {'before': before, 'after': after, 'changes': changes}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Item model                      Source faces')
    for name, count in after['item_source_faces'].items():
        print(f'{name:32} {before["item_source_faces"][name]:>7,} -> {count:>7,}')
    print(f'Model files: {before["model_bytes"]:,} -> {after["model_bytes"]:,} bytes; '
          f'{len(changes)} {"optimized" if args.write else "pending"} files; '
          f'{len(after["textures"])} unchanged textures.')
    if args.check and changes:
        raise SystemExit('Run python scripts/optimize_models.py --write after regenerating assets.')


if __name__ == '__main__':
    main()
