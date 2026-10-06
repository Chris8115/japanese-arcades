"""Hatsune Miku shelf figure, authored as small layered solid meshes.

The north-facing sculpt has an oversized head, deliberately stepped fringe,
long separate twin tails and a tailored outfit. Coordinates are model units.
"""
import math

from figure_geometry import FigureGeometry


COLORS = {
    'base': '#222936', 'base_edge': '#141c27', 'base_top': '#37434b',
    'base_teal': '#128e99', 'base_shine': '#40bdc2',
    'hair': '#24aeb4', 'hair_light': '#3cc3c3', 'hair_high': '#60d2cb',
    'hair_mid': '#199aa5', 'hair_shadow': '#117e90', 'hair_deep': '#116779',
    'skin': '#f2d7cb', 'skin_light': '#ffe6d8', 'skin_shadow': '#dfbcba',
    'blush': '#efb7bd', 'mouth': '#c48a95',
    'white': '#fcf5e7', 'eye_white': '#f4eeec', 'lash': '#2d3846',
    'iris_dark': '#226d83', 'iris': '#35a9b7', 'iris_light': '#80e0d7',
    'pupil': '#244b60',
    'shirt': '#b8bcc6', 'shirt_light': '#d1d0d4', 'shirt_mid': '#a0a6b4',
    'shirt_shadow': '#808b9e',
    'tie': '#38c9c7', 'tie_dark': '#158f9f', 'tie_light': '#70e1d7',
    'cloth': '#282e3a', 'cloth_light': '#3d4351', 'cloth_mid': '#323946',
    'cloth_dark': '#1b2330', 'boot': '#25303b', 'boot_light': '#3b4653',
    'sole': '#16212c', 'teal_trim': '#33c6c7', 'trim_dark': '#158897',
    'headset': '#292837', 'headset_light': '#414053',
    'pink': '#d24b86', 'pink_light': '#ec77a9', 'pink_dark': '#922e62',
    'gold': '#e9c66e', 'gold_dark': '#947145', 'red_mark': '#c9777f',
}


def _octagon(x0, x1, z0, z1, bevel):
    return [(x0 + bevel, z0), (x1 - bevel, z0), (x1, z0 + bevel),
            (x1, z1 - bevel), (x1 - bevel, z1), (x0 + bevel, z1),
            (x0, z1 - bevel), (x0, z0 + bevel)]


def _loft(g, name, rings, material, side_materials=None):
    """Closed eight-sided cross sections: (y,x0,x1,z0,z1,bevel)."""
    layers = [[(x, y, z) for x, z in _octagon(x0, x1, z0, z1, b)]
              for y, x0, x1, z0, z1, b in rings]
    for k, (lower, upper) in enumerate(zip(layers, layers[1:])):
        for i in range(8):
            j = (i + 1) % 8
            mat = side_materials[i] if side_materials else material
            g.face(f'{name} side {k} {i}',
                   [lower[i], upper[i], upper[j], lower[j]], mat)
    for label, layer, reverse in [('bottom', layers[0], False),
                                   ('top', layers[-1], True)]:
        center = tuple(sum(p[i] for p in layer) / len(layer) for i in range(3))
        for i in range(8):
            edge = [layer[i], layer[(i + 1) % 8]]
            if reverse:
                edge.reverse()
            g.face(f'{name} {label} {i}', [center, *edge], material)


def _plate(g, name, x0, y0, x1, y1, z, material):
    g.face(name, [(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)], material)


def _hair_lock(g, name, outline, front, back, color, edge=None):
    # Ear clipping preserves the concave pixel steps along the fringe/tips;
    # a center triangle fan would incorrectly fill those small notches.
    outline = list(outline)
    area = sum(p[0] * q[1] - q[0] * p[1]
               for p, q in zip(outline, outline[1:] + outline[:1]))
    if area < 0:
        outline.reverse()
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    indices = list(range(len(outline)))
    triangles = []
    while len(indices) > 3:
        for k, current in enumerate(indices):
            prev, nxt = indices[k - 1], indices[(k + 1) % len(indices)]
            a, b, c = outline[prev], outline[current], outline[nxt]
            if cross(a, b, c) <= 1e-8:
                continue
            if any(cross(a, b, outline[j]) >= -1e-8 and
                   cross(b, c, outline[j]) >= -1e-8 and
                   cross(c, a, outline[j]) >= -1e-8
                   for j in indices if j not in (prev, current, nxt)):
                continue
            triangles.append((prev, current, nxt))
            indices.pop(k)
            break
        else:
            raise ValueError('Cannot triangulate ' + name)
    triangles.append(tuple(indices))
    for i, triangle in enumerate(triangles):
        points = [outline[j] for j in triangle]
        g.face(f'{name} front {i}', [(*p, front) for p in reversed(points)], color)
        g.face(f'{name} back {i}', [(*p, back) for p in points], color)
    for i, p in enumerate(outline):
        q = outline[(i + 1) % len(outline)]
        g.face(f'{name} edge {i}', [(*p, front), (*q, front), (*q, back), (*p, back)], edge or color)


def _tail(g, side):
    name = 'left twin tail' if side > 0 else 'right twin tail'
    start = len(g.faces)
    _loft(g, name + ' core', [
        (2.05, 11.55, 12.65, 7.82, 9.14, .20),
        (2.75, 11.60, 13.00, 7.30, 9.50, .24),
        (5.25, 11.25, 13.20, 7.08, 9.66, .30),
        (8.10, 10.94, 13.02, 6.98, 9.55, .28),
        (10.7, 10.54, 12.58, 7.03, 9.35, .26),
        (12.55, 10.38, 12.08, 7.12, 9.25, .24),
        (13.30, 10.34, 11.62, 7.35, 9.05, .22),
    ], 'hair', ['hair_light', 'hair_mid', 'hair_mid', 'hair_shadow',
                'hair_shadow', 'hair_deep', 'hair_mid', 'hair'])
    # Front locks follow the same flow as the core with unequal staggered tips.
    _hair_lock(g, name + ' outer ribbon', [
        (11.54, 12.90), (12.03, 12.90), (12.03, 10.45),
        (12.42, 10.45), (12.42, 7.45), (12.75, 7.45),
        (12.75, 3.15), (12.36, 3.15), (12.36, 2.55),
        (11.93, 2.55), (11.93, 6.40), (11.66, 6.40),
        (11.66, 9.50), (11.54, 9.50),
    ], 6.93, 7.24, 'hair_light', 'hair_mid')
    _hair_lock(g, name + ' inner ribbon', [
        (10.53, 12.32), (11.10, 12.32), (11.10, 9.48),
        (11.42, 9.48), (11.42, 7.14), (11.78, 7.14),
        (11.78, 3.02), (11.33, 3.02), (11.33, 3.70),
        (10.98, 3.70), (10.98, 7.76), (10.64, 7.76),
        (10.64, 10.15), (10.53, 10.15),
    ], 6.79, 7.17, 'hair', 'hair_shadow')
    _hair_lock(g, name + ' narrow sheen', [
        (11.34, 12.18), (11.60, 12.18), (11.60, 10.16),
        (11.89, 10.16), (11.89, 7.97), (11.63, 7.97),
        (11.63, 9.73), (11.34, 9.73),
    ], 6.86, 7.04, 'hair_high')
    # A darker back strand makes the ponytail have volume from rear views too.
    _hair_lock(g, name + ' back layer', [
        (11.28, 12.35), (11.80, 12.35), (11.80, 10.18),
        (12.19, 10.18), (12.19, 7.45), (12.55, 7.45),
        (12.55, 3.46), (12.01, 3.46), (12.01, 6.61),
        (11.63, 6.61), (11.63, 9.24), (11.28, 9.24),
    ], 9.22, 9.73, 'hair_mid')
    if side < 0:
        g.transform(start, lambda x, y, z: (16 - x, y, z))
        for face in g.faces[start:]:
            face['vertices'].reverse()
            face['uv'].reverse()


def _eye(g, center, name):
    # A coplanar pixel mosaic: no white rectangular foundation, stacked eye
    # layers, protruding pupils or lower rim. The cream sliver and tiny glint
    # sit beside the teal pixels rather than on raised plaques.
    pixels = [
        ' LLLLL ',
        ' WDDDD ',
        ' WHDDD ',
        ' WDPID ',
        ' WDPID ',
        ' WIiii ',
        '  iii  ',
    ]
    palette = {'L': 'lash', 'W': 'eye_white', 'D': 'iris_dark',
               'H': 'white', 'P': 'pupil', 'I': 'iris', 'i': 'iris_light'}
    size_x, size_y = .18, .20
    for row, line in enumerate(pixels):
        for column, pixel in enumerate(line):
            if pixel == ' ':
                continue
            x0 = center + (column - 3.5) * size_x
            y1 = 11.51 - row * size_y
            _plate(g, f'{name} painted pixel {row} {column}',
                   x0, y1 - size_y, x0 + size_x, y1, 5.059, palette[pixel])


def _arm(g, side):
    name = 'left arm' if side > 0 else 'right arm'
    start = len(g.faces)
    _loft(g, name + ' bare shoulder', [
        (7.60, 9.45, 10.35, 6.32, 7.86, .10),
        (8.45, 9.44, 10.25, 6.35, 7.89, .13),
        (8.70, 9.45, 10.02, 6.46, 7.83, .14),
    ], 'skin', ['skin_light', 'skin', 'skin', 'skin_shadow',
                'skin_shadow', 'skin_shadow', 'skin', 'skin_light'])
    _loft(g, name + ' detached sleeve', [
        (5.75, 9.18, 10.58, 5.94, 7.98, .12),
        (6.14, 9.25, 10.53, 6.01, 7.97, .13),
        (7.75, 9.42, 10.35, 6.23, 7.88, .10),
    ], 'cloth', ['cloth_mid', 'cloth', 'cloth_dark', 'cloth_dark',
                'cloth_dark', 'cloth_dark', 'cloth_light', 'cloth_mid'])
    _loft(g, name + ' cuff teal edging', [
        (5.69, 9.18, 10.59, 5.94, 7.98, .12),
        (5.87, 9.18, 10.59, 5.94, 7.98, .12),
    ], 'teal_trim')
    _loft(g, name + ' hand', [
        (5.21, 9.49, 10.35, 6.34, 7.51, .14),
        (5.70, 9.38, 10.29, 6.24, 7.59, .12),
    ], 'skin', ['skin_light', 'skin', 'skin_shadow', 'skin_shadow',
                'skin_shadow', 'skin_shadow', 'skin', 'skin_light'])
    g.box(name + ' thumb', (9.22, 5.37, 6.31), (9.47, 5.73, 6.81), 'skin')
    _plate(g, name + ' sleeve control inset', 9.65, 7.06, 10.21, 7.55, 6.175, 'cloth_dark')
    _plate(g, name + ' sleeve gold meter', 9.73, 7.27, 9.90, 7.48, 6.162, 'gold')
    _plate(g, name + ' sleeve teal meter', 9.97, 7.14, 10.14, 7.48, 6.161, 'trim_dark')
    _plate(g, name + ' sleeve lower seam', 9.46, 6.11, 9.61, 6.63, 6.002, 'cloth_light')
    angle = math.radians(18 if side > 0 else 23)
    c, s = math.cos(angle), math.sin(angle)
    def pose(x, y, z):
        x, y = x - 9.64, y - 8.48
        x, y = c * x - s * y + 9.64, s * x + c * y + 8.48
        return (x if side > 0 else 16 - x, y, z)
    g.transform(start, pose)
    if side < 0:
        for face in g.faces[start:]:
            face['vertices'].reverse()
            face['uv'].reverse()


def build():
    g = FigureGeometry(COLORS)
    g.group = 'Beveled display plinth'
    _loft(g, 'display base', [
        (0.00, 2.75, 13.25, 3.75, 12.25, .26),
        (.18, 2.50, 13.50, 3.50, 12.50, .30),
        (.90, 2.50, 13.50, 3.50, 12.50, .30),
        (1.08, 2.72, 13.28, 3.72, 12.28, .28),
    ], 'base', ['base', 'base', 'base_edge', 'base_edge',
                'base_edge', 'base_edge', 'base', 'base'])
    _loft(g, 'display base teal inlay', [
        (.88, 2.51, 13.49, 3.51, 12.49, .30),
        (1.015, 2.67, 13.33, 3.67, 12.33, .28),
    ], 'base_teal')
    g.box('display base top pad', (3.10, 1.075, 4.15), (12.90, 1.13, 11.85), 'base_top')

    g.group = 'Long layered turquoise twin tails'
    _tail(g, 1)
    _tail(g, -1)

    g.group = 'Thigh boots and legs'
    for side in (-1, 1):
        name = 'left boot' if side > 0 else 'right boot'
        center = 8 + side * 1.03
        _loft(g, name + ' sole', [
            (1.13, center - .65, center + .65, 5.42, 8.46, .17),
            (1.35, center - .67, center + .67, 5.38, 8.49, .18),
        ], 'sole')
        _loft(g, name + ' foot', [
            (1.35, center - .65, center + .65, 5.44, 8.45, .17),
            (1.76, center - .64, center + .64, 5.44, 8.40, .18),
            (2.08, center - .50, center + .50, 6.10, 8.31, .13),
        ], 'boot', ['boot_light', 'boot', 'boot', 'cloth_dark',
                    'cloth_dark', 'cloth_dark', 'boot', 'boot_light'])
        _loft(g, name + ' shaft', [
            (1.75, center - .48, center + .48, 6.17, 8.28, .10),
            (3.30, center - .58, center + .58, 6.23, 8.30, .10),
            (4.16, center - .62, center + .62, 6.20, 8.33, .11),
        ], 'boot', ['boot_light', 'boot', 'cloth_dark', 'cloth_dark',
                    'cloth_dark', 'cloth_dark', 'boot', 'boot_light'])
        _loft(g, name + ' teal thigh edging', [
            (4.04, center - .62, center + .62, 6.19, 8.34, .11),
            (4.17, center - .62, center + .62, 6.19, 8.34, .11),
        ], 'trim_dark')
        _loft(g, name + ' exposed thigh', [
            (4.17, center - .55, center + .55, 6.31, 8.22, .10),
            (5.46, center - .59, center + .59, 6.36, 8.29, .10),
        ], 'skin', ['skin_light', 'skin', 'skin', 'skin_shadow',
                    'skin_shadow', 'skin_shadow', 'skin', 'skin_light'])
        _plate(g, name + ' toe accent', center - .23, 1.40, center + .19, 1.69, 5.425, 'teal_trim')
        _plate(g, name + ' shin accent', center - .35, 3.29, center - .09, 3.85, 6.178, 'trim_dark')
        _plate(g, name + ' shin shine', center - .30, 3.60, center - .11, 3.85, 6.167, 'teal_trim')

    g.group = 'Pleated skirt and sleeveless tunic'
    # Sixteen tailored panels alternate subtly shaded, broad folds.
    for i in range(16):
        a, b = math.tau * i / 16, math.tau * (i + 1) / 16
        def point(t, y, rx, rz):
            return (8 + rx * math.cos(t), y, 7.42 + rz * math.sin(t))
        top = [point(a, 6.35, 1.39, 1.19), point(b, 6.35, 1.39, 1.19)]
        bottom = [point(a, 5.04, 2.13, 1.87), point(b, 5.04, 2.13, 1.87)]
        g.face(f'skirt pleat {i}', [bottom[0], top[0], top[1], bottom[1]],
               ('cloth', 'cloth_light', 'cloth_mid', 'cloth_dark')[i % 4])
        hem = [point(a, 4.87, 2.13, 1.87), point(b, 4.87, 2.13, 1.87)]
        g.face(f'skirt teal hem {i}', [hem[0], bottom[0], bottom[1], hem[1]],
               'teal_trim' if i % 2 else 'trim_dark')
        inner = [point(a, 4.87, 1.94, 1.69), point(b, 4.87, 1.94, 1.69)]
        g.face(f'skirt underside {i}', [hem[0], hem[1], inner[1], inner[0]], 'cloth_dark')
    _loft(g, 'tunic fitted body', [
        (6.04, 6.41, 9.59, 5.98, 8.91, .15),
        (7.07, 6.62, 9.38, 6.06, 8.70, .17),
        (8.38, 6.47, 9.53, 6.04, 8.72, .16),
        (8.79, 6.76, 9.24, 6.38, 8.52, .18),
    ], 'shirt', ['shirt_light', 'shirt', 'shirt_mid', 'shirt_shadow',
                'shirt_mid', 'shirt_shadow', 'shirt_mid', 'shirt'])
    # Pointed split vest hems overlap the skirt in front.
    _hair_lock(g, 'left pointed vest hem', [(6.43, 6.32), (7.65, 6.32),
            (7.67, 5.61), (7.12, 5.31), (6.35, 5.55)], 5.90, 6.08, 'shirt')
    _hair_lock(g, 'right pointed vest hem', [(8.35, 6.32), (9.57, 6.32),
            (9.65, 5.55), (8.88, 5.31), (8.33, 5.61)], 5.90, 6.08, 'shirt_light')
    g.box('neck', (7.39, 8.65, 6.68), (8.61, 9.58, 8.26), 'skin')
    _hair_lock(g, 'left collar', [(6.99, 8.65), (7.88, 8.70), (7.77, 8.10), (7.31, 8.30)],
            6.006, 6.35, 'shirt_light')
    _hair_lock(g, 'right collar', [(8.12, 8.70), (9.01, 8.65), (8.69, 8.30), (8.23, 8.10)],
            6.006, 6.35, 'shirt_light')
    _hair_lock(g, 'tie knot', [(7.71, 8.56), (8.29, 8.56), (8.24, 8.14), (7.76, 8.14)],
            5.933, 6.15, 'tie_dark')
    _hair_lock(g, 'long turquoise tie', [(7.80, 8.17), (8.20, 8.17), (8.42, 6.05),
            (8.00, 5.72), (7.58, 6.05)], 5.905, 6.16, 'tie')
    _plate(g, 'tie slim highlight', 7.82, 6.42, 7.98, 7.98, 5.891, 'tie_light')
    _plate(g, 'tunic lapel gold pin', 8.92, 8.10, 9.17, 8.33, 6.015, 'gold')
    _plate(g, 'tunic side teal piping left', 6.52, 6.39, 6.64, 7.74, 5.958, 'trim_dark')
    _plate(g, 'tunic side teal piping right', 9.36, 6.39, 9.48, 7.74, 5.958, 'trim_dark')
    _plate(g, 'tunic back center seam', 7.91, 6.26, 8.09, 8.47, 8.917, 'shirt_shadow')
    g.faces[-1]['vertices'].reverse()
    g.faces[-1]['uv'].reverse()

    g.group = 'Detached sleeves and small hands'
    _arm(g, 1)
    _arm(g, -1)

    g.group = 'Chibi face and expression'
    # The face remains a broad flat drawing plane; the perimeter takes just
    # a few softened steps into the cheeks and short chin.
    _loft(g, 'head skin', [
        (9.03, 6.36, 9.64, 5.45, 9.50, .40),
        (9.20, 5.88, 10.12, 5.21, 9.71, .40),
        (9.47, 5.56, 10.44, 5.06, 9.85, .37),
        (10.31, 5.38, 10.62, 5.06, 9.91, .35),
        (12.53, 5.38, 10.62, 5.06, 9.91, .35),
        (13.04, 5.83, 10.17, 5.31, 9.72, .30),
    ], 'skin', ['skin_light', 'skin', 'skin', 'skin_shadow',
                'skin_shadow', 'skin_shadow', 'skin', 'skin'])
    _eye(g, 6.83, 'left teal eye')
    _eye(g, 9.17, 'right teal eye')
    _plate(g, 'left soft blush', 5.99, 9.86, 6.49, 10.01, 5.059, 'blush')
    _plate(g, 'right soft blush', 9.51, 9.86, 10.01, 10.01, 5.059, 'blush')
    _plate(g, 'tiny smiling mouth', 7.88, 9.66, 8.12, 9.71, 5.059, 'mouth')

    g.group = 'Stepped crown and layered bangs'
    _loft(g, 'crown core', [
        (11.94, 5.22, 10.78, 5.18, 10.14, .25),
        (13.38, 5.12, 10.88, 5.04, 10.28, .26),
        (13.83, 5.51, 10.49, 5.30, 10.08, .26),
        (14.08, 6.18, 9.82, 5.70, 9.76, .25),
    ], 'hair', ['hair', 'hair_light', 'hair_mid', 'hair_shadow',
                'hair_mid', 'hair_shadow', 'hair_light', 'hair_light'])
    # Crown terraces form a small coherent sweep instead of random noise.
    g.box('crown top center terrace', (6.78, 14.08, 6.23), (9.44, 14.28, 8.94), 'hair_light')
    g.box('crown front sheen terrace', (6.09, 13.84, 5.37), (8.81, 14.07, 6.38), 'hair_high')
    g.box('crown side terrace', (9.69, 13.35, 6.00), (10.98, 13.70, 8.18), 'hair')
    _hair_lock(g, 'left outer face framing lock', [
        (5.29, 13.29), (6.16, 13.29), (6.16, 11.63), (6.42, 11.63),
        (6.42, 10.10), (6.13, 10.10), (6.13, 9.56), (5.49, 9.56),
        (5.49, 10.14), (5.21, 10.14),
    ], 4.78, 5.50, 'hair', 'hair_mid')
    _hair_lock(g, 'right outer face framing lock', [
        (9.80, 13.40), (10.67, 13.40), (10.67, 11.35), (10.87, 11.35),
        (10.87, 10.08), (10.57, 10.08), (10.57, 9.66), (10.01, 9.66),
        (10.01, 10.36), (9.76, 10.36),
    ], 4.80, 5.49, 'hair_mid', 'hair_shadow')
    _hair_lock(g, 'left brow sweep', [
        (6.10, 13.51), (7.17, 13.51), (7.17, 12.31), (7.48, 12.31),
        (7.48, 11.52), (7.20, 11.52), (7.20, 11.24), (6.73, 11.24),
        (6.73, 11.74), (6.32, 11.74), (6.32, 12.28), (6.10, 12.28),
    ], 4.64, 5.22, 'hair_light', 'hair')
    _hair_lock(g, 'central long pointed bang', [
        (7.14, 13.69), (8.29, 13.69), (8.29, 12.01), (8.55, 12.01),
        (8.55, 11.18), (8.22, 11.18), (8.22, 10.80), (7.82, 10.80),
        (7.82, 11.34), (7.42, 11.34), (7.42, 12.17), (7.14, 12.17),
    ], 4.49, 5.22, 'hair', 'hair_mid')
    _hair_lock(g, 'right parted bang', [
        (8.26, 13.58), (9.79, 13.58), (9.79, 12.54), (10.04, 12.54),
        (10.04, 11.72), (9.58, 11.72), (9.58, 11.99), (9.07, 11.99),
        (9.07, 11.55), (8.68, 11.55), (8.68, 12.47), (8.26, 12.47),
    ], 4.61, 5.28, 'hair_light', 'hair')
    _plate(g, 'left fringe slim highlight', 6.32, 12.36, 6.60, 13.19, 4.639, 'hair_high')
    _plate(g, 'central fringe highlight', 7.40, 12.07, 7.70, 13.33, 4.489, 'hair_light')
    _plate(g, 'right fringe high edge', 9.42, 12.62, 9.68, 13.25, 4.609, 'hair_high')
    # A continuous bob covers the back of the head beneath the stepped locks.
    _hair_lock(g, 'back bob underlayer', [
        (5.24, 12.15), (10.76, 12.15), (10.76, 9.50), (10.28, 9.50),
        (10.28, 9.18), (5.72, 9.18), (5.72, 9.50), (5.24, 9.50),
    ], 9.48, 10.16, 'hair_mid', 'hair_shadow')
    # Four overlapping ribbons soften the lower edge around the neck.
    for i, (x0, x1, end, color) in enumerate([
        (5.24, 6.85, 9.03, 'hair_mid'), (6.70, 8.39, 8.98, 'hair'),
        (8.22, 9.77, 9.07, 'hair_light'), (9.65, 10.76, 9.22, 'hair_mid'),
    ]):
        _hair_lock(g, f'back bob ribbon {i}', [(x0, 13.35), (x1, 13.35),
            (x1, end + .45), (x1 - .23, end + .45), (x1 - .23, end),
            (x0 + .24, end), (x0 + .24, end + .34), (x0, end + .34)],
            9.63, 10.38 + (i % 2) * .12, color)

    g.group = 'Headset and magenta hair clips'
    for side in (-1, 1):
        name = 'left headset' if side > 0 else 'right headset'
        center = 8 + side * 2.89
        g.box(name + ' dark ear shell', (center - .39, 10.60, 5.81),
              (center + .39, 12.55, 7.51), 'headset')
        g.box(name + ' ear front cushion', (center - .44, 10.88, 5.71),
              (center + .44, 12.24, 6.05), 'headset_light')
        g.box(name + ' pink narrow accent', (center - .16, 10.94, 5.67),
              (center + .16, 12.18, 5.79), 'pink')
        g.box(name + ' accent light', (center - .14, 11.86, 5.65),
              (center + .14, 12.18, 5.73), 'pink_light')
        clipx = 8 + side * 2.16
        g.box(name + ' hair ribbon dark body', (clipx - .28, 12.96, 6.24),
              (clipx + .28, 14.39, 7.39), 'headset')
        g.box(name + ' ribbon magenta front', (clipx - .11, 13.17, 6.219),
              (clipx + .11, 14.35, 6.26), 'pink')
        g.box(name + ' ribbon pink top', (clipx - .11, 14.35, 6.25),
              (clipx + .11, 14.40, 7.31), 'pink_dark')

    # A compact body and a wider head follow the reference's shelf-chibi
    # proportions. The plinth remains identical, while tails blend between
    # the two scales so their roots meet the hair and tips reach the boots.
    anchor, body_scale, head_scale = 9.03, .82, 1.10
    head_bottom = 1.13 + (anchor - 1.13) * body_scale
    head_groups = {'Chibi face and expression', 'Stepped crown and layered bangs',
                   'Headset and magenta hair clips'}
    for face in g.faces:
        group = face['group']
        if group == 'Beveled display plinth':
            continue
        points = []
        for x, y, z in face['vertices']:
            if group == 'Stepped crown and layered bangs' and z < 5.06:
                z = 5.06 + (z - 5.06) * .30
            if group in head_groups:
                x = 8 + (x - 8) * head_scale
                y = head_bottom + (y - anchor) * head_scale
            elif group == 'Long layered turquoise twin tails':
                x = 8 + (x - 8) * 1.10
                y = (1.13 + (y - 1.13) * body_scale if y <= anchor else
                     head_bottom + (y - anchor) * head_scale)
            else:
                x = 8 + (x - 8) * .95
                y = 1.13 + (y - 1.13) * body_scale
            points.append([x, y, z])
        face['vertices'] = points
    return g
