"""Lossless JSON surface-removal regressions; no catalog assets are written."""
import copy
import itertools
import random
import tempfile
from pathlib import Path

from PIL import Image
from catalog_json_geometry import FACE_AXES, optimize_model


def box(name, low, high, texture='#solid'):
    return {'name': name, 'from': list(low), 'to': list(high),
            'faces': {direction: {'texture': texture, 'uv': [1, 2, 14, 15]}
                      for direction in FACE_AXES}}


def model(*elements):
    return {'textures': {'solid': 'test:solid', 'glass': 'test:glass', 'alias': '#solid'},
            'elements': list(elements)}


def run(source):
    saved = copy.deepcopy(source)
    result, stats = optimize_model(source, assets)
    assert source == saved, 'Input mutated'
    again, repeated = optimize_model(result, assets)
    assert again == result, 'Optimization must be idempotent'
    assert repeated['removed_hidden_faces'] == repeated['removed_duplicate_faces'] == 0
    assert stats['input_faces'] - stats['output_faces'] == stats['removed_hidden_faces'] + stats['removed_duplicate_faces']
    original = {e['name']: e for e in source['elements']}
    for e in result['elements']:
        before = original[e['name']]
        assert {k:v for k,v in e.items() if k != 'faces'} == {k:v for k,v in before.items() if k != 'faces'}
        assert all(face == before['faces'][side] for side, face in e['faces'].items()), 'UV or metadata changed'
    return result, stats


def nearest(source, origin, direction):
    axis, sign, u, v = FACE_AXES[direction]
    # Rays originate outside, then travel opposite the visible face's normal.
    hits = []
    for e in source['elements']:
        if direction not in e['faces']:
            continue
        low, high = e['from'], e['to']
        plane = high[axis] if sign > 0 else low[axis]
        distance = (origin[axis] - plane) * sign
        if distance >= 0 and low[u] < origin[u] < high[u] and low[v] < origin[v] < high[v]:
            hits.append(distance)
    return min(hits) if hits else None


with tempfile.TemporaryDirectory(prefix='catalog-model-check-') as temp:
    assets = Path(temp)
    (assets/'test/textures').mkdir(parents=True)
    Image.new('RGBA', (16, 16), (12, 34, 56, 255)).save(assets/'test/textures/solid.png')
    glass = Image.new('RGBA', (16, 16), (255, 255, 255, 255))
    glass.putpixel((3, 3), (255, 255, 255, 0))
    glass.save(assets/'test/textures/glass.png')

    result, stats = run(model(box('left', (0,0,0), (1,1,1)), box('right', (1,0,0), (2,1,1))))
    assert stats['output_faces'] == 10 and stats['removed_hidden_faces'] == 2
    result, stats = run(model(box('inner', (1,1,1), (2,2,2)), box('outer', (0,0,0), (3,3,3))))
    assert [e['name'] for e in result['elements']] == ['outer']

    # Union of two boxes covers a source face, though neither does alone.
    panel = box('panel', (0,0,0), (2,2,1)); panel['faces'] = {'north': panel['faces']['north']}
    result, stats = run(model(panel, box('a', (0,0,-1), (1,2,.5)), box('b', (1,0,-1), (2,2,.5))))
    assert not any(e['name'] == 'panel' for e in result['elements'])
    result, _ = run(model(panel, box('half', (0,0,-1), (1,2,.5))))
    assert next(e for e in result['elements'] if e['name'] == 'panel') == panel, 'No partial-face fragmentation'
    result, _ = run(model(panel, box('a', (0,0,-1), (1,2,.5)), box('gap', (1+1e-10,0,-1), (2,2,.5))))
    assert any(e['name'] == 'panel' for e in result['elements']), 'Tiny real gaps cannot be rounded away'

    for texture in ('#glass', '#missing'):
        result, stats = run(model(box('inner', (1,1,1), (2,2,2)), box('shell', (0,0,0), (3,3,3), texture)))
        assert next(e for e in result['elements'] if e['name'] == 'inner')['faces'].keys() == FACE_AXES.keys()
    unclosed = box('not_a_solid', (0,0,0), (3,3,3)); del unclosed['faces']['down']
    result, _ = run(model(box('inner', (1,1,1), (2,2,2)), unclosed))
    assert len(next(e for e in result['elements'] if e['name'] == 'inner')['faces']) == 6
    tinted = box('tinted', (0,0,0), (3,3,3))
    tinted['faces']['north']['tintindex'] = 0
    result, _ = run(model(box('inner', (1,1,1), (2,2,2)), tinted))
    assert len(next(e for e in result['elements'] if e['name'] == 'inner')['faces']) == 6

    left = box('left', (0,0,0), (1,1,1)); right = box('right', (1,0,0), (2,1,1))
    left['rotation'] = right['rotation'] = {'axis':'x', 'angle':22.5, 'origin':[0,0,0], 'rescale':False}
    assert run(model(left, right))[1]['output_faces'] == 10
    right['rotation'] = {**right['rotation'], 'origin':[0,1,0]}
    assert run(model(left, right))[1]['output_faces'] == 12

    first = box('first', (0,0,0), (1,1,1)); other = copy.deepcopy(first); other['name'] = 'other'
    assert run(model(first, other))[1]['removed_duplicate_faces'] == 6
    for change in ('uv', 'glow', 'shade', 'rotation'):
        a = copy.deepcopy(panel); b = copy.deepcopy(panel); b['name'] = 'different'
        if change == 'uv': b['faces']['north']['uv'][0] += .25
        if change == 'glow': b['faces']['north']['neoforge_data'] = {'block_light':15, 'sky_light':15}
        if change == 'shade': b['shade'] = False
        if change == 'rotation': b['faces']['north']['rotation'] = 90
        assert run(model(a, b))[1]['removed_duplicate_faces'] == 0
    source = model(first, other); source['render_type'] = 'minecraft:translucent'
    assert run(source)[0] == source
    source = model(box('tiny', (0,0,0), (.00001,1,1), '#alias'))
    assert run(source)[0] == source

    # External silhouette visibility oracle across randomized opaque unions.
    rng = random.Random(7241)
    rays = 0
    for trial in range(24):
        es = []
        for i in range(10):
            low = [rng.randrange(5) for _ in range(3)]
            high = [v+rng.randrange(1,4) for v in low]
            es.append(box(str(i), low, high))
        source = model(*es); result, _ = run(source)
        for direction, (axis, sign, u, v) in FACE_AXES.items():
            for a, b in itertools.product((.25, 1.25, 2.25, 3.25, 4.25, 5.25, 6.25), repeat=2):
                origin = [0.,0.,0.]; origin[axis] = 10 if sign > 0 else -3
                origin[u], origin[v] = a, b
                assert nearest(source, origin, direction) == nearest(result, origin, direction)
                rays += 1
    print('PASS: adjacency, containment, union coverage, partial-face retention, tiny gaps, alpha, unknown textures, incomplete solids, tint, same/different rotations, exact duplicates, UV/emission/shade preservation, aliases, translucency, idempotence, and', rays, 'external visibility rays.')
