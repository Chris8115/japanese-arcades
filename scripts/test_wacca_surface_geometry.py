"""Run exterior extraction regressions with python scripts/test_wacca_surface_geometry.py.

Pass --model to additionally audit the current saved WACCA geometry.
"""
import copy
import importlib.util
import itertools
import json
import random
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('surface', ROOT/'scripts/wacca_surface_geometry.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def box(name, low, high):
    return {'name': name, 'from': list(low), 'to': list(high), '_group': 'Checks',
            'faces': {d: {'texture': '#test', 'uv': [0, 0, 16, 16],
                         'neoforge_data': {'block_light': 15}} for d in m.FACE_AXES}}


def area(elements):
    total = 0
    for e in elements:
        for direction in e['faces']:
            _, _, a, b, _, _ = m.FACE_AXES[direction]
            total += (e['to'][a]-e['from'][a])*(e['to'][b]-e['from'][b])
    return total


def overlap_check(elements):
    planes = {}
    for e in elements:
        if 'rotation' in e:
            continue
        for direction in e['faces']:
            axis, sign, a, b, _, _ = m.FACE_AXES[direction]
            p = e['from'][axis] if sign < 0 else e['to'][axis]
            planes.setdefault((direction, round(p, 6)), []).append(
                (e['from'][a], e['to'][a], e['from'][b], e['to'][b]))
    for rects in planes.values():
        for a, b in itertools.combinations(rects, 2):
            assert min(a[1], b[1])-max(a[0], b[0]) <= m.EPSILON or min(a[3], b[3])-max(a[2], b[2]) <= m.EPSILON


original = [box('left', (0, 0, 0), (1, 1, 1)), box('right', (1, 0, 0), (2, 1, 1))]
saved = copy.deepcopy(original)
result, stats = m.optimize_surfaces(original)
assert area(result) == 10
assert original == saved
assert all('east' not in e['faces'] for e in result if e['name'] == 'left')
assert all('west' not in e['faces'] for e in result if e['name'] == 'right')
overlap_check(result)

result, _ = m.optimize_surfaces([box('first', (0, 0, 0), (1, 1, 1)), box('last', (0, 0, 0), (1, 1, 1))])
assert len(result) == 1 and result[0]['name'] == 'last' and area(result) == 6

result, _ = m.optimize_surfaces([box('deep', (0, 0, 0), (1, 1, 3)), box('shallow', (1, 0, 1), (2, 1, 3))])
east = [e for e in result if e['name'].startswith('deep') and 'east' in e['faces']]
assert len(east) == 1 and east[0]['from'][2] == 0 and east[0]['to'][2] == 1
assert abs(east[0]['faces']['east']['uv'][0]-32/3) < 1e-7
overlap_check(result)

result, _ = m.optimize_surfaces([box('panel', (0, 0, 0), (2, 2, 1)), box('occluder', (1, 0, -1), (2, 1, .5))])
fronts = [e for e in result if e['name'].startswith('panel') and 'north' in e['faces']]
assert len(fronts) == 2
assert sorted(tuple(e['faces']['north']['uv']) for e in fronts) == [(0, 0, 8, 8), (8, 0, 16, 16)]
assert all(e['faces']['north']['neoforge_data']['block_light'] == 15 for e in fronts)
overlap_check(result)

result, _ = m.optimize_surfaces([box('thin_remainder', (0, 0, 0), (1, 1, 1)),
                                box('near_full_cover', (.0005, 0, -1), (1, 1, .5))])
assert not any(e['name'].startswith('thin_remainder') and 'north' in e['faces'] for e in result)
assert m.MIN_SPAN*.35/16 > 1e-5

for direction, spec in m.FACE_AXES.items():
    face = {'uv': [0, 0, 16, 16], 'texture': '#test'}
    cropped = m._crop_uv(face, (0, 2, 0, 2), (0, 1, 0, 1), *spec[4:])['uv']
    assert cropped == ([0, 0, 8, 8] if spec[4:] == (1, 1) else
                       [8, 8, 16, 16] if spec[4:] == (-1, -1) else [0, 8, 8, 16])
for rotation, expected in ((90, [0, 8, 8, 16]), (180, [8, 8, 16, 16]), (270, [8, 0, 16, 8])):
    assert m._crop_uv({'uv': [0, 0, 16, 16], 'rotation': rotation}, (0, 2, 0, 2), (0, 1, 0, 1), 1, 1)['uv'] == expected

rotated = box('rotated', (0, 0, 0), (10, 10, 10))
rotated['rotation'] = {'axis': 'x', 'angle': 22.5, 'origin': [0, 0, 0]}
result, _ = m.optimize_surfaces([box('small', (1, 1, 1), (2, 2, 2)), rotated])
assert any(e == rotated for e in result) and area([e for e in result if e['name'] == 'small']) == 6

rng = random.Random(614)
for trial in range(30):
    es, occupied = [], set()
    for i in range(8):
        low = [rng.randrange(4) for _ in range(3)]
        high = [x+rng.randrange(1, 4) for x in low]
        es.append(box(str(i), low, high))
        occupied.update(itertools.product(*(range(a, b) for a, b in zip(low, high))))
    expected = 0
    for voxel in occupied:
        for axis in range(3):
            for sign in (-1, 1):
                adjacent = list(voxel); adjacent[axis] += sign
                expected += tuple(adjacent) not in occupied
    result, _ = m.optimize_surfaces(es)
    assert abs(area(result)-expected) < 1e-6, (trial, area(result), expected)
    overlap_check(result)
print('Synthetic checks passed: adjacency, source priority, depth steps, partial clipping, six UV directions, UV rotations, fullbright, rotated exclusion, 30 union-oracle cases.')

if '--model' in sys.argv:
    start = time.monotonic()
    model = json.loads((ROOT/'art/wacca/geometry.json').read_text(encoding='utf-8'))
    result = model['elements']
    overlap_check(result)
    assert all(all(b > a for a, b in zip(e['from'], e['to'])) for e in result)
    assert len({e['name'] for e in result}) == len(result)
    for e in result:
        for direction in e['faces']:
            for axis in m.FACE_AXES[direction][2:4]:
                span = e['to'][axis]-e['from'][axis]
                assert span >= m.MIN_SPAN-m.EPSILON, (e['name'], direction, span)
                offset = 0 if axis == 1 else 5.2
                item_span = round(e['to'][axis]*.35+offset, 5)-round(e['from'][axis]*.35+offset, 5)
                assert item_span/16 > 1e-5, ('Inventory winding tolerance', e['name'], direction, item_span)
    print({'model_elements': len(result), 'model_faces': sum(len(e['faces']) for e in result)},
          'audit_seconds', round(time.monotonic()-start, 2))
    print('Current full WACCA model: no same-direction coplanar overlap remains.')
