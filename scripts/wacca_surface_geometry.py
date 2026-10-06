"""Extract the visible exterior of opaque axis-aligned cabinet cuboids.

This removes both internal faces and same-facing coplanar overlaps. Rotated
elements are passed through unchanged and never participate as occluders.
UV directions follow Minecraft 1.21.1 FaceInfo/BlockFaceUV after the generator's
global X mirror. Every emitted element retains strictly positive dimensions.
"""

import copy


EPSILON = 1e-6
# FaceBakery compares vertices with a 1e-5 *block-unit* tolerance. Keep a margin
# after the inventory model's .35 scale and five-decimal coordinate rounding.
MIN_SPAN = .001
FACE_AXES = {
    'north': (2, -1, 0, 1, -1, -1),
    'south': (2, 1, 0, 1, 1, -1),
    'east': (0, 1, 2, 1, -1, -1),
    'west': (0, -1, 2, 1, 1, -1),
    'up': (1, 1, 0, 2, 1, 1),
    'down': (1, -1, 0, 2, 1, -1),
}


def _rounded(value):
    return round(value, 8)


def _valid(rect):
    return rect[1]-rect[0] >= MIN_SPAN and rect[3]-rect[2] >= MIN_SPAN


def _subtract(rect, cover):
    left, right = max(rect[0], cover[0]), min(rect[1], cover[1])
    bottom, top = max(rect[2], cover[2]), min(rect[3], cover[3])
    if right-left <= EPSILON or top-bottom <= EPSILON:
        return [rect]
    pieces = ((rect[0], left, rect[2], rect[3]),
              (right, rect[1], rect[2], rect[3]),
              (left, right, rect[2], bottom),
              (left, right, top, rect[3]))
    return [tuple(_rounded(value) for value in piece) for piece in pieces if _valid(piece)]


def _merge_rectangles(rectangles):
    """Rejoin adjacent pieces without reintroducing any clipped-away area."""
    previous = None
    while previous != len(rectangles):
        previous = len(rectangles)
        for horizontal in (True, False):
            groups = {}
            for a, b, c, d in rectangles:
                key, run = ((c, d), (a, b)) if horizontal else ((a, b), (c, d))
                groups.setdefault(key, []).append(run)
            joined = []
            for key in sorted(groups):
                spans = sorted(groups[key])
                start, end = spans[0]
                for a, b in spans[1:]:
                    if abs(a-end) <= EPSILON:
                        end = b
                    else:
                        joined.append((start, end, *key) if horizontal else (*key, start, end))
                        start, end = a, b
                joined.append((start, end, *key) if horizontal else (*key, start, end))
            rectangles = joined
    return sorted(rectangles)


def _crop_uv(face, original, clipped, u_sign, v_sign):
    """Crop UVs in face-local coordinates, also preserving quarter-turn UVs."""
    a, b, c, d = original
    p, q, r, s = clipped
    us = ((p-a)/(b-a), (q-a)/(b-a))
    vs = ((r-c)/(d-c), (s-c)/(d-c))
    if u_sign < 0:
        us = (1-us[1], 1-us[0])
    if v_sign < 0:
        vs = (1-vs[1], 1-vs[0])
    rotation = face.get('rotation', 0)
    if rotation == 90:
        us, vs = vs, (1-us[1], 1-us[0])
    elif rotation == 180:
        us, vs = (1-us[1], 1-us[0]), (1-vs[1], 1-vs[0])
    elif rotation == 270:
        us, vs = (1-vs[1], 1-vs[0]), us
    else:
        assert rotation == 0, 'Only Minecraft quarter-turn UV rotations are supported'
    u0, v0, u1, v1 = face['uv']
    result = copy.deepcopy(face)
    result['uv'] = [_rounded(u0+(u1-u0)*us[0]), _rounded(v0+(v1-v0)*vs[0]),
                    _rounded(u0+(u1-u0)*us[1]), _rounded(v0+(v1-v0)*vs[1])]
    return result


def optimize_surfaces(elements):
    """Return an exterior-only model and counts; leave the input untouched."""
    boxes = []
    for index, element in enumerate(elements):
        if 'rotation' in element:
            continue
        low = tuple(_rounded(value) for value in element['from'])
        high = tuple(_rounded(value) for value in element['to'])
        assert all(b > a for a, b in zip(low, high)), element['name']
        boxes.append((index, low, high))
    cache = {}

    def candidates(direction, plane):
        key = (direction, plane)
        if key in cache:
            return cache[key]
        axis, sign, first, second, _, _ = FACE_AXES[direction]
        found = []
        for index, low, high in boxes:
            if sign > 0:
                crosses = low[axis] <= plane+EPSILON and high[axis] > plane+EPSILON
                tied = abs(high[axis]-plane) <= EPSILON and low[axis] < plane-EPSILON
            else:
                crosses = high[axis] >= plane-EPSILON and low[axis] < plane-EPSILON
                tied = abs(low[axis]-plane) <= EPSILON and high[axis] > plane+EPSILON
            if crosses or tied:
                found.append((index, tied and not crosses,
                              (low[first], high[first], low[second], high[second])))
        cache[key] = found
        return found

    output = []
    hidden_faces = 0
    split_source_faces = 0
    rotated_count = 0
    for index, source in enumerate(elements):
        if 'rotation' in source:
            output.append(copy.deepcopy(source))
            rotated_count += 1
            continue
        low = [_rounded(value) for value in source['from']]
        high = [_rounded(value) for value in source['to']]
        whole_faces, pieces = {}, []
        for direction, face in source['faces'].items():
            axis, sign, first, second, u_sign, v_sign = FACE_AXES[direction]
            plane = low[axis] if sign < 0 else high[axis]
            original = (low[first], high[first], low[second], high[second])
            if not _valid(original):
                hidden_faces += 1
                continue
            remaining = [original]
            for other_index, tied, cover in candidates(direction, plane):
                if other_index == index or (tied and other_index < index):
                    continue
                if (cover[1] <= original[0]+EPSILON or cover[0] >= original[1]-EPSILON
                        or cover[3] <= original[2]+EPSILON or cover[2] >= original[3]-EPSILON):
                    continue
                remaining = [part for rect in remaining for part in _subtract(rect, cover)]
                if not remaining:
                    break
            if not remaining:
                hidden_faces += 1
                continue
            remaining = _merge_rectangles(remaining)
            if remaining == [original]:
                whole_faces[direction] = copy.deepcopy(face)
                continue
            split_source_faces += 1
            for part_index, rect in enumerate(remaining):
                part = copy.deepcopy(source)
                part['name'] = source['name']+' exterior '+direction+' %03d'%part_index
                part['from'], part['to'] = list(low), list(high)
                part['from'][first], part['to'][first] = rect[0], rect[1]
                part['from'][second], part['to'][second] = rect[2], rect[3]
                part['faces'] = {direction: _crop_uv(face, original, rect, u_sign, v_sign)}
                pieces.append(part)
        if whole_faces:
            whole = copy.deepcopy(source)
            whole['faces'] = whole_faces
            output.append(whole)
        output.extend(pieces)
    stats = {
        'input_elements': len(elements), 'output_elements': len(output),
        'input_faces': sum(len(e['faces']) for e in elements),
        'output_faces': sum(len(e['faces']) for e in output),
        'fully_hidden_faces': hidden_faces, 'clipped_source_faces': split_source_faces,
        'rotated_elements_preserved': rotated_count,
    }
    return output, stats
