"""Conservative, dependency-free post-export optimization of static OBJ meshes.

Only adjacent coplanar faces with the same affine UV mapping can merge. Their
union must remain a convex triangle/quad. Curves, UV seams, explicit normals,
material/object/group/smoothing boundaries, and nonplanar quads remain intact.
Exact position/UV/normal declarations are indexed once. This reduces file and
loader overhead independently of the face-count reduction.

The public API does not write files: ``optimize_obj(text) -> (text, stats)``.
Run after an authoring export; the original authoring model is not modified.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
import math


# Exported coordinates have nine decimal places. Permit only rounding-scale
# plane/UV error; never decimate curved outlines or move an original vertex.
PLANE_EPS = 1e-8
UV_EPS = 2e-8
ALLOWED_DIRECTIVES = {"v", "vt", "vn", "f", "o", "g", "s", "usemtl", "mtllib"}


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _length(a):
    return math.sqrt(_dot(a, a))


@dataclass
class _Face:
    refs: list
    run: int
    plane: object = None
    mapping: object = None


def _measure(face, positions, uvs):
    """Return an oriented plane and affine UV map, or refuse the face."""
    if len(face.refs) not in (3, 4) or any(t is None or n is not None for _, t, n in face.refs):
        return
    ps = [positions[p] for p, _, _ in face.refs]
    ts = [uvs[t] for _, t, _ in face.refs]
    if any(len(p) != 3 for p in ps) or any(len(t) != 2 for t in ts):
        return
    normal = [0.0, 0.0, 0.0]
    for a, b in zip(ps, ps[1:] + ps[:1]):
        c = _cross(a, b)
        normal = [x + y for x, y in zip(normal, c)]
    size = _length(normal)
    if size < 1e-14:
        return
    normal = tuple(v / size for v in normal)
    if any(abs(_dot(normal, _sub(p, ps[0]))) > PLANE_EPS for p in ps):
        return
    # Choose a well-conditioned basis rather than relying on the first three
    # corners (a clipped polygon may contain collinear corners).
    first = max(range(1, len(ps)), key=lambda i: _dot(_sub(ps[i], ps[0]), _sub(ps[i], ps[0])))
    e = _sub(ps[first], ps[0])
    second = max((i for i in range(1, len(ps)) if i != first),
                 key=lambda i: _length(_cross(e, _sub(ps[i], ps[0]))))
    f = _sub(ps[second], ps[0])
    ee, ef, ff = _dot(e, e), _dot(e, f), _dot(f, f)
    determinant = ee * ff - ef * ef
    if determinant <= 1e-24:
        return
    gradients = []
    for axis in (0, 1):
        de, df = ts[first][axis] - ts[0][axis], ts[second][axis] - ts[0][axis]
        a, b = (de * ff - df * ef) / determinant, (df * ee - de * ef) / determinant
        gradients.append(tuple(a * x + b * y for x, y in zip(e, f)))
    mapping = (ps[0], ts[0], gradients)
    if any(not _uv_matches(mapping, p, uv) for p, uv in zip(ps, ts)):
        return
    face.plane = (normal, ps[0], size / 2)
    face.mapping = mapping


def _uv_matches(mapping, p, uv):
    origin, base, gradients = mapping
    relative = _sub(p, origin)
    return all(abs(base[i] + _dot(gradients[i], relative) - uv[i]) <= UV_EPS for i in (0, 1))


def _edges(face):
    refs = face.refs
    return [(refs[i][0], refs[(i + 1) % len(refs)][0]) for i in range(len(refs))]


def _join(a, b, positions, uvs):
    if a.run != b.run or a.plane is None or b.plane is None:
        return None
    normal, origin, area_a = a.plane
    if _dot(normal, b.plane[0]) < 1 - 1e-10:
        return None
    if any(abs(_dot(normal, _sub(positions[p], origin))) > PLANE_EPS
           or not _uv_matches(a.mapping, positions[p], uvs[t]) for p, t, _ in b.refs):
        return None
    matches = [(i, j) for i, edge_a in enumerate(_edges(a)) for j, edge_b in enumerate(_edges(b))
               if edge_a == edge_b[::-1]]
    if len(matches) != 1:
        return None
    i, j = matches[0]
    refs = a.refs[i + 1:] + a.refs[:i + 1]
    refs += [b.refs[(j + 2 + k) % len(b.refs)] for k in range(len(b.refs) - 2)]
    # Remove only straight, forward boundary joins. UVs already share the same
    # affine mapping, so interpolated pixels on a removed corner are identical.
    changed = True
    while changed and len(refs) > 3:
        changed = False
        for k in range(len(refs)):
            before, here, after = (positions[refs[q % len(refs)][0]] for q in (k - 1, k, k + 1))
            incoming, outgoing = _sub(here, before), _sub(after, here)
            if (_dot(incoming, outgoing) >= 0
                    and _length(_cross(incoming, outgoing)) <= PLANE_EPS * (_length(incoming) + _length(outgoing))):
                refs.pop(k)
                changed = True
                break
    if len(refs) not in (3, 4) or len({r[0] for r in refs}) != len(refs):
        return None
    ps = [positions[p] for p, _, _ in refs]
    if any(_dot(normal, _cross(_sub(ps[(k + 1) % len(ps)], ps[k]),
                              _sub(ps[(k + 2) % len(ps)], ps[(k + 1) % len(ps)]))) <= 1e-14
           for k in range(len(ps))):
        return None
    candidate = _Face(refs, a.run)
    _measure(candidate, positions, uvs)
    if candidate.plane is None:
        return None
    if abs(candidate.plane[2] - area_a - b.plane[2]) > max(1e-12, (area_a + b.plane[2]) * 1e-8):
        return None
    return candidate


def optimize_obj(text):
    """Return optimized OBJ text and JSON-serializable audit statistics.

    Unsupported syntax returns the input byte-for-byte with a ``skipped``
    reason. Explicit normals are preserved and indexed, but their faces do not
    merge. No material order is changed; merging stays within a contiguous
    object/group/smoothing/material run.
    """
    raw = {"v": [], "vt": [], "vn": []}
    data = {"v": [], "vt": [], "vn": []}
    indexes = {"v": {}, "vt": {}, "vn": {}}
    refs_to_unique = {"v": [], "vt": [], "vn": []}
    events, faces, run = [], [], 0
    original_lines = text.splitlines()
    stats = {"input_bytes": len(text.encode("utf-8")), "input_faces": 0,
             "merged_faces": 0, "deduplicated_positions": 0, "deduplicated_uvs": 0,
             "deduplicated_normals": 0}

    def reject(reason):
        stats.update(skipped=reason, output_bytes=stats["input_bytes"], output_faces=stats["input_faces"])
        return text, stats

    try:
        for line in original_lines:
            content = line.split("#", 1)[0].strip()
            if not content:
                events.append(line)
                continue
            words = content.split()
            kind = words[0]
            if kind not in ALLOWED_DIRECTIVES:
                return reject("unsupported OBJ directive: " + kind)
            if kind in raw:
                values = tuple(float(v) for v in words[1:])
                if not all(math.isfinite(v) for v in values):
                    return reject("non-finite declaration")
                if len(values) not in ({3, 4} if kind == "v" else {1, 2, 3} if kind == "vt" else {3}):
                    return reject("unsupported " + kind + " declaration")
                index = indexes[kind].get(values)
                if index is None:
                    index = len(data[kind])
                    indexes[kind][values] = index
                    data[kind].append(values)
                    raw[kind].append(content)
                refs_to_unique[kind].append(index)
                continue
            if kind != "f":
                # A state boundary is deliberately retained even if it repeats
                # an earlier state. This also preserves transparent draw order.
                run += 1
                events.append(line)
                continue
            stats["input_faces"] += 1
            face_refs = []
            for word in words[1:]:
                fields = word.split("/")
                if len(fields) > 3:
                    return reject("unsupported face index")
                fields += [""] * (3 - len(fields))
                ref = []
                for field, declaration in zip(fields, ("v", "vt", "vn")):
                    if not field:
                        ref.append(None)
                        continue
                    number = int(field)
                    count = len(refs_to_unique[declaration])
                    actual = number - 1 if number > 0 else count + number
                    if number == 0 or actual < 0 or actual >= count:
                        return reject("invalid or forward face index")
                    ref.append(refs_to_unique[declaration][actual])
                if ref[0] is None:
                    return reject("face without position")
                face_refs.append(tuple(ref))
            if len(face_refs) < 3:
                return reject("face has fewer than three vertices")
            face = _Face(face_refs, run)
            _measure(face, data["v"], data["vt"])
            events.append(len(faces))
            faces.append(face)
    except (ValueError, IndexError, OverflowError, ZeroDivisionError):
        return reject("unsupported or malformed numeric geometry")

    edges = defaultdict(set)

    def register(index, add):
        face = faces[index]
        if face is not None and face.plane is not None:
            for edge in _edges(face):
                key = (face.run, min(edge), max(edge))
                if add:
                    edges[key].add(index)
                else:
                    edges[key].discard(index)

    for index in range(len(faces)):
        register(index, True)
    pending = deque(range(len(faces)))
    while pending:
        index = pending.popleft()
        face = faces[index]
        if face is None or face.plane is None:
            continue
        neighbors = set()
        for edge in _edges(face):
            neighbors.update(edges[(face.run, min(edge), max(edge))])
        for other in sorted(neighbors - {index}):
            candidate = _join(face, faces[other], data["v"], data["vt"])
            if candidate is None:
                continue
            first, second = sorted((index, other))
            register(first, False)
            register(second, False)
            faces[first], faces[second] = candidate, None
            register(first, True)
            pending.append(first)
            stats["merged_faces"] += 1
            break

    # Put declarations before any face: a merged face can reference vertices
    # originally declared later in the stream. Object/material state remains in
    # the original order, while OBJ declarations are global by specification.
    lines = raw["v"] + raw["vt"] + raw["vn"]
    for event in events:
        if isinstance(event, str):
            lines.append(event)
        elif faces[event] is not None:
            words = []
            for v, t, n in faces[event].refs:
                word = str(v + 1)
                if t is not None or n is not None:
                    word += "/" + (str(t + 1) if t is not None else "")
                if n is not None:
                    word += "/" + str(n + 1)
                words.append(word)
            lines.append("f " + " ".join(words))
    result = "\n".join(lines) + "\n"
    stats.update(output_faces=sum(face is not None for face in faces),
                 output_bytes=len(result.encode("utf-8")),
                 deduplicated_positions=len(refs_to_unique["v"]) - len(data["v"]),
                 deduplicated_uvs=len(refs_to_unique["vt"]) - len(data["vt"]),
                 deduplicated_normals=len(refs_to_unique["vn"]) - len(data["vn"]))
    return result, stats
