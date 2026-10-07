"""Conservative, lossless face removal for native Minecraft JSON models.

``optimize_model(model, assets_root)`` returns a copied model and integer stats.
``assets_root`` contains namespace folders, for example ``src/main/resources/assets``.
Callers resolve parent textures and recurse through composite children. This
module neither writes files nor changes texture pixels, coordinates, UVs or poses.

Only closed six-face boxes whose textures are proven opaque can occlude faces.
Partial occlusion never splits a face: the retained part is already hidden by
the nearer opaque solid, so drawing the original quad avoids fragment growth.
"""
from __future__ import annotations

import copy
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


FACE_AXES = {
    'north': (2, -1, 0, 1), 'south': (2, 1, 0, 1),
    'east': (0, 1, 2, 1), 'west': (0, -1, 2, 1),
    'up': (1, 1, 0, 2), 'down': (1, -1, 0, 2),
}


def _subtract(rect, cover):
    """Rectangle coverage only: exact endpoints, no rounding or minimum span."""
    left, right = max(rect[0], cover[0]), min(rect[1], cover[1])
    bottom, top = max(rect[2], cover[2]), min(rect[3], cover[3])
    if right <= left or top <= bottom:
        return [rect]
    return [part for part in (
        (rect[0], left, rect[2], rect[3]),
        (right, rect[1], rect[2], rect[3]),
        (left, right, rect[2], bottom),
        (left, right, top, rect[3]),
    ) if part[1] > part[0] and part[3] > part[2]]


def _signature(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _valid_box(element):
    return (len(element.get('from', ())) == 3 and len(element.get('to', ())) == 3
            and all(b > a for a, b in zip(element['from'], element['to'])))


def _opaque_checker(textures, assets_root):
    cache = {}
    assets_root = Path(assets_root).resolve()

    def opaque(reference):
        visited = set()
        while reference.startswith('#'):
            if reference in visited:
                return False
            visited.add(reference)
            reference = textures.get(reference[1:], '')
            if not isinstance(reference, str) or not reference:
                return False
        if reference in cache:
            return cache[reference]
        namespace, separator, path = reference.partition(':')
        if not separator:
            namespace, path = 'minecraft', namespace
        candidate = (assets_root / namespace / 'textures' / (path + '.png')).resolve()
        if not candidate.is_relative_to(assets_root):
            return False
        try:
            with Image.open(candidate) as texture:
                # Entire animated sheets must be opaque in every frame too.
                result = texture.convert('RGBA').getchannel('A').getextrema() == (255, 255)
        except (OSError, ValueError):
            result = False
        cache[reference] = result
        return result

    return opaque


def optimize_model(model, assets_root):
    """Remove fully hidden or exactly repeated opaque faces; retain all detail.

    Unknown textures, tint callbacks, alpha images and translucent models are
    conservative exclusions. Rotated elements share occlusion only when their
    complete rotation dictionaries match. Metadata is preserved verbatim.
    """
    result = copy.deepcopy(model)
    elements = model.get('elements', [])
    stats = {'input_elements': len(elements), 'output_elements': len(elements),
             'input_faces': sum(len(e.get('faces', {})) for e in elements),
             'output_faces': sum(len(e.get('faces', {})) for e in elements),
             'removed_hidden_faces': 0, 'removed_duplicate_faces': 0,
             'opaque_occluders': 0}
    # Blended layers can accumulate alpha even for repeated surfaces.
    if not elements or 'translucent' in model.get('render_type', ''):
        return result, stats

    opaque = _opaque_checker(model.get('textures', {}), assets_root)

    def opaque_face(face):
        # Tint providers are executable client code and may alter alpha.
        return (face.get('tintindex', -1) < 0 and 'color' not in face
                and 'color' not in face.get('neoforge_data', {})
                and opaque(face.get('texture', '')))

    occluders = defaultdict(list)
    for index, element in enumerate(elements):
        faces = element.get('faces', {})
        if (_valid_box(element) and set(faces) == set(FACE_AXES)
                and all(opaque_face(face) for face in faces.values())):
            pose = _signature(element.get('rotation'))
            occluders[pose].append((index, element['from'], element['to']))
            stats['opaque_occluders'] += 1

    candidates_cache = {}

    def candidates(pose, direction, plane):
        key = pose, direction, plane
        if key not in candidates_cache:
            axis, sign, u, v = FACE_AXES[direction]
            found = []
            for index, low, high in occluders.get(pose, ()):
                # A box must extend beyond this outward-facing plane. Equal
                # same-facing boundary planes are NOT hidden; only exact
                # duplicates may be removed separately below.
                crosses = (low[axis] <= plane < high[axis] if sign > 0
                           else low[axis] < plane <= high[axis])
                if crosses:
                    found.append((index, (low[u], high[u], low[v], high[v])))
            candidates_cache[key] = found
        return candidates_cache[key]

    seen = set()
    output = []
    for index, source in enumerate(elements):
        if not _valid_box(source):
            output.append(copy.deepcopy(source))
            continue
        element = copy.deepcopy(source)
        low, high = source['from'], source['to']
        pose = _signature(source.get('rotation'))
        # Keep all render-affecting metadata, including shade and future
        # extensions. Names and private authoring annotations are not rendered.
        element_style = _signature({k: v for k, v in source.items()
                                    if k not in ('name', 'from', 'to', 'faces')
                                    and not k.startswith('_')})
        for direction, face in source.get('faces', {}).items():
            if direction not in FACE_AXES:
                continue
            axis, sign, u, v = FACE_AXES[direction]
            plane = low[axis] if sign < 0 else high[axis]
            rect = (low[u], high[u], low[v], high[v])
            remaining = [rect]
            for other_index, cover in candidates(pose, direction, plane):
                if other_index == index:
                    continue
                remaining = [part for piece in remaining for part in _subtract(piece, cover)]
                if not remaining:
                    del element['faces'][direction]
                    stats['removed_hidden_faces'] += 1
                    break
            if not remaining:
                continue
            if opaque_face(face):
                key = direction, plane, rect, element_style, _signature(face)
                if key in seen:
                    del element['faces'][direction]
                    stats['removed_duplicate_faces'] += 1
                    continue
                seen.add(key)
        if element.get('faces'):
            output.append(element)
    result['elements'] = output
    stats['output_elements'] = len(output)
    stats['output_faces'] = sum(len(e.get('faces', {})) for e in output)
    return result, stats
