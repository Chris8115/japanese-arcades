"""Run exterior extraction regressions with python scripts/test_wacca_surface_geometry.py.

Pass --model to additionally audit the current saved WACCA geometry.
"""
import copy
import importlib.util
import itertools
import json
import math
from collections import Counter, defaultdict
import random
import struct
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

def audit_meshes(meshes, palette_size):
    """Check the replacement bowl's actual surfaces, not its declared segment count."""
    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    def sub(a, b):
        return tuple(x-y for x, y in zip(a, b))

    def dot(a, b):
        return sum(x*y for x, y in zip(a, b))

    def canonical(points):
        return min(tuple(points[i:]+points[:i]) for i in range(len(points)))

    def boundary_loops(faces):
        # Shared edges must close at the angular seam. An annulus has only its
        # inner and outer boundary loops, with no cracks or T-junctions.
        edges = Counter()
        for face in faces:
            points = [tuple(round(v, 6) for v in p) for p in face['vertices']]
            edges.update(tuple(sorted((a, b))) for a, b in zip(points, points[1:]+points[:1]))
        assert all(count <= 2 for count in edges.values()), 'Non-manifold smooth surface edge'
        boundary = defaultdict(set)
        for (a, b), count in edges.items():
            if count == 1:
                boundary[a].add(b)
                boundary[b].add(a)
        assert boundary and all(len(neighbors) == 2 for neighbors in boundary.values()), 'Open or branched bowl boundary'
        unseen = set(boundary)
        loops = 0
        while unseen:
            loops += 1
            pending = [unseen.pop()]
            while pending:
                for neighbor in boundary[pending.pop()]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        pending.append(neighbor)
        return loops

    palette_faces = white_faces = 0
    oriented = set()
    cone = []
    for face in meshes:
        name, points, uv = face['name'], face['vertices'], face['uv']
        assert len(points) in (3, 4) and len(points) == len(uv), ('Invalid mesh face', name)
        assert all(math.isfinite(v) for p in points+uv for v in p), ('Non-finite mesh value', name)
        assert all(-1e-7 <= v <= 16+1e-7 for p in uv for v in p), ('Mesh UV outside sprite', name)
        normal = cross(sub(points[1], points[0]), sub(points[2], points[0]))
        magnitude = math.sqrt(dot(normal, normal))
        assert magnitude > 1e-10, ('Degenerate mesh face', name)
        normal = tuple(v/magnitude for v in normal)
        assert all(abs(dot(normal, sub(p, points[0]))) < 1e-5 for p in points), ('Non-planar mesh face', name)
        identity = (face['texture'], face.get('glow', False), canonical([
            (tuple(round(v, 6) for v in p), tuple(round(v, 6) for v in t)) for p, t in zip(points, uv)]))
        assert identity not in oriented, ('Duplicate same-facing textured surface', name)
        oriented.add(identity)
        if face['texture'] == '#materials':
            palette_faces += 1
            for axis, dimension in enumerate(palette_size):
                values = [p[axis]*dimension/16 for p in uv]
                low, high = min(values), max(values)
                tile_size = dimension/4
                tile = int(((low+high)/2)//tile_size)
                assert 0 <= tile < 4 and low >= tile*tile_size+8-1e-6 and high <= (tile+1)*tile_size-8+1e-6, (
                    'Mesh palette UV lacks mip-4 edge guard', name, axis, low, high)
            if 'white' in face.get('group', '').lower() and 'rim' in face.get('group', '').lower():
                white_faces += 1
                uv_area = abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(uv, uv[1:]+uv[:1])))/2
                assert uv_area > 1e-8, ('White rim needs a two-dimensional interior UV patch', name)
        if face['texture'] == '#leds':
            cone.append(face)
            center = [sum(p[i] for p in points)/len(points) for i in range(3)]
            radial = (center[0]-8, center[1]-28.2, 0)
            assert normal[2] < -.1 and dot(normal, radial) < 0, ('Reversed touch-cone surface', name)
            # Remove the existing backward lean before comparing the recess depth.
            samples = sorted((math.hypot(p[0]-8, p[1]-28.2), p[2]-.1*(p[1]-17.2)) for p in points)
            assert samples[0][1] > samples[-1][1]+1e-5, ('Flat or inverted touch-cone depth', name)
    assert palette_faces and white_faces, 'Mesh palette/white-rim checks must exercise visible faces'
    assert cone and boundary_loops(cone) == 2, 'Touch cone must close with exactly two circular boundary loops'
    print({'mesh_faces': len(meshes), 'mesh_palette_faces_with_mip4_guard': palette_faces,
           'white_rim_mesh_faces_with_2d_uvs': white_faces, 'continuous_cone_faces': len(cone)})


if '--model' in sys.argv:
    start = time.monotonic()
    model = json.loads((ROOT/'art/wacca/geometry.json').read_text(encoding='utf-8'))
    result = model.get('legacy_elements', model.get('elements', []))
    assert result, 'Cuboid clipping regression must still cover the preserved cabinet hardware'
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
    # A collapsed UV row at a palette/sprite boundary bypasses FaceBakery's
    # inward UV shrink. At mip level four, the nearest sample can then come
    # from the neighbouring black tile or an unrelated Minecraft atlas sprite.
    # Check the sampling footprint, including clipped faces, rather than just
    # checking that the nominal UVs lie within the overall 0..16 sprite range.
    namespace, texture_path = model['textures']['materials'].split(':', 1)
    palette_path = ROOT/'src/main/resources/assets'/namespace/'textures'/(texture_path+'.png')
    palette_bytes = palette_path.read_bytes()
    assert palette_bytes[:8] == b'\x89PNG\r\n\x1a\n'
    palette_size = struct.unpack('>II', palette_bytes[16:24])
    mip_level = 4
    half_texel_guard = (1 << mip_level)/2
    palette_faces = white_ledges = 0
    for e in result:
        for direction, face in e['faces'].items():
            if face['texture'] != '#materials':
                continue
            palette_faces += 1
            for axis, dimension in enumerate(palette_size):
                tile_size = dimension/4
                endpoints = [face['uv'][axis]*dimension/16,
                             face['uv'][axis+2]*dimension/16]
                low, high = min(endpoints), max(endpoints)
                tile = int(((low+high)/2)//tile_size)
                assert 0 <= tile < 4, ('Palette tile out of range', e['name'], direction, face['uv'])
                assert low >= tile*tile_size+half_texel_guard-1e-6, (
                    'Palette UV lacks mip-4 edge guard', e['name'], direction, axis, low, high)
                assert high <= (tile+1)*tile_size-half_texel_guard+1e-6, (
                    'Palette UV lacks mip-4 edge guard', e['name'], direction, axis, low, high)
            if e['_group'] == 'White outer ring' and direction in ('up', 'down'):
                white_ledges += 1
                assert abs(face['uv'][2]-face['uv'][0]) > 1e-8 and abs(face['uv'][3]-face['uv'][1]) > 1e-8, (
                    'White rim ledge must use a two-dimensional interior UV patch', e['name'], direction, face['uv'])
    if model.get('meshes'):
        audit_meshes(model['meshes'], palette_size)
        assert palette_faces, 'Preserved cuboid palette checks must exercise visible faces'
    else:
        assert palette_faces and white_ledges, 'Palette/white-ledge regression checks must exercise visible faces'
    print({'palette_faces_with_mip4_guard': palette_faces,
           'white_ledges_with_2d_uvs': white_ledges, 'guard_source_pixels': half_texel_guard})
    print({'model_elements': len(result), 'model_faces': sum(len(e['faces']) for e in result)},
          'audit_seconds', round(time.monotonic()-start, 2))
    print('Current full WACCA model: no same-direction coplanar overlap remains.')
