"""Box-built Hatsune Miku shelf figure.

The reference is a little Minecraft sculpture: chunky isotropic hair voxels,
stepped rectangular clothes, and a tiny painted pixel face. Every surface in
this authoring file belongs to a cuboid or a flat square color patch. There
are deliberately no lofts, rounded outlines, tubes or tapered mesh panels.
"""
import math

from figure_geometry import FigureGeometry


COLORS = {
    'base': '#252b35', 'base_dark': '#19212b', 'base_top': '#39434c',
    'base_teal': '#218d96',
    'hair': '#22b0b4', 'hair_light': '#39bfc0', 'hair_pale': '#4cc9c6',
    'hair_mid': '#21a4ad', 'hair_shadow': '#198e9b', 'hair_deep': '#137d8c',
    'hair_soft': '#2bb6b8', 'hair_cool': '#279ea8',
    'skin': '#f0d2c6', 'skin_light': '#f8dbce', 'skin_shade': '#dfbcb4',
    'blush': '#e8b2b6', 'cheek_pale': '#f0c6c0', 'eye_dark': '#294c5a', 'eye_teal': '#3c919e',
    'eye_light': '#81c5c5', 'eye_pale': '#d7e0d9',
    'shirt': '#b8bac4', 'shirt_light': '#c9cbd1', 'shirt_shade': '#969da9',
    'shirt_dark': '#7e8798',
    'tie': '#2fbabd', 'tie_light': '#51ceca', 'tie_dark': '#19929f',
    'cloth': '#262c37', 'cloth_light': '#3b414d', 'cloth_mid': '#303744',
    'cloth_dark': '#1a2230', 'boot': '#242d38', 'boot_light': '#35424d',
    'teal': '#38c4c5', 'teal_shade': '#238d9c', 'sole': '#161e28',
    'headset': '#262736', 'headset_light': '#363545',
    'pink': '#cf4282', 'pink_light': '#e26a9e', 'pink_dark': '#90305f',
    'gold': '#d8bd70', 'meter': '#318e9c',
    'face_base': '#edc5cc', 'face_edge': '#526171', 'face_lash': '#253240',
    'face_pupil': '#245c70', 'face_iris': '#3696a5', 'face_iris_light': '#77c2c7',
    'face_sclera': '#c2b9c3', 'face_cheek': '#e5aebe', 'face_mouth': '#dfa4b8',
}


class _Cubes:
    """Union of equal-sided cubes; emit only exposed square surfaces."""
    STEP = .25

    def __init__(self, step=.25, origin=(0,0,0)):
        self.STEP = step
        self.origin = origin
        self.cells = {}

    def box(self, lo, hi, color):
        bounds = []
        for low, high, origin in zip(lo, hi, self.origin):
            a, b = round((low-origin) / self.STEP), round((high-origin) / self.STEP)
            assert abs(origin+a*self.STEP-low) < 1e-7, (low, high)
            assert abs(origin+b*self.STEP-high) < 1e-7, (low, high)
            bounds.append(range(a, b))
        for x in bounds[0]:
            for y in bounds[1]:
                for z in bounds[2]:
                    self.cells[x, y, z] = color

    def grid_box(self, lo, hi, color):
        for x in range(lo[0],hi[0]):
            for y in range(lo[1],hi[1]):
                for z in range(lo[2],hi[2]):
                    self.cells[x,y,z] = color

    def emit(self, g, name):
        faces = {
            'north': ((0, 0, -1), ((0,1,0), (1,1,0), (1,0,0), (0,0,0))),
            'south': ((0, 0, 1), ((0,0,1), (1,0,1), (1,1,1), (0,1,1))),
            'west': ((-1, 0, 0), ((0,0,0), (0,0,1), (0,1,1), (0,1,0))),
            'east': ((1, 0, 0), ((1,0,1), (1,0,0), (1,1,0), (1,1,1))),
            'up': ((0, 1, 0), ((0,1,0), (0,1,1), (1,1,1), (1,1,0))),
            'down': ((0, -1, 0), ((0,0,0), (1,0,0), (1,0,1), (0,0,1))),
        }
        for (x, y, z), color in sorted(self.cells.items()):
            for side, (normal, offsets) in faces.items():
                neighbor = (x + normal[0], y + normal[1], z + normal[2])
                if neighbor in self.cells:
                    continue
                ox,oy,oz=self.origin
                points = [(ox+(x+dx)*self.STEP,oy+(y+dy)*self.STEP,
                           oz+(z+dz)*self.STEP) for dx,dy,dz in offsets]
                g.face(f'{name} cube {x} {y} {z} {side}', points, color)


def _square(g, name, x, y, z, size, color):
    g.face(name, [(x,y+size,z), (x+size,y+size,z),
                  (x+size,y,z), (x,y,z)], color)


def _crown():
    # Twelve true cubes span the already-narrowed head. Nothing squeezes
    # these .375-unit cells afterward; each exposed pixel stays square.
    hair = _Cubes(step=.375, origin=(5.75,8.25,5.0))
    block = hair.grid_box
    for lo,hi,color in [
        ((0,6,2),(12,9,13),'hair'),
        ((1,9,2),(11,10,13),'hair_soft'),
        ((2,10,3),(10,11,12),'hair_light'),
        ((3,11,4),(9,12,11),'hair_soft'),
    ]:
        block(lo,hi,color)

    # Five broad coherent fringe groups replace the crowded narrow ribs.
    # The fringe ends one hair pixel lower, with small side locks extending
    # to the cheek line. The crown, tails and painted face stay in place.
    block((0,2,2),(1,9,4),'hair_mid')
    block((1,3,2),(2,10,4),'hair')
    block((1,0,1),(2,10,4),'hair')
    block((0,7,2),(2,9,7),'hair')
    block((2,5,0),(3,8,4),'hair_light')
    block((3,4,0),(5,8,4),'hair_soft')
    block((2,8,1),(5,10,5),'hair_light')
    block((3,10,2),(5,11,6),'hair_soft')
    block((5,3,0),(6,8,4),'hair')
    block((6,4,0),(7,8,4),'hair_soft')
    block((5,8,1),(7,11,5),'hair')
    block((7,4,1),(8,8,4),'hair_light')
    block((8,5,1),(9,8,4),'hair_light')
    block((9,4,1),(10,8,4),'hair_soft')
    block((7,8,1),(10,10,5),'hair_light')
    block((7,10,3),(9,11,6),'hair_soft')
    block((10,3,2),(11,10,5),'hair')
    block((10,0,1),(11,10,5),'hair')
    block((11,2,2),(12,9,4),'hair_mid')
    block((10,7,2),(12,9,7),'hair')

    # The side and back layers are broad connected clumps, with just one
    # cube of height/depth offset at their ends, rather than stripe noise.
    block((0,1,4),(2,9,10),'hair_mid')
    block((0,2,10),(2,9,13),'hair')
    block((10,1,4),(12,9,10),'hair_mid')
    block((10,2,10),(12,9,13),'hair')
    block((0,2,11),(3,9,14),'hair_mid')
    block((3,0,11),(6,10,14),'hair')
    block((6,1,11),(9,10,14),'hair_soft')
    block((9,2,11),(12,9,14),'hair_mid')
    # A handful of square crown accents continue the fringe directions.
    block((3,11,4),(5,12,7),'hair_light')
    block((5,11,6),(7,12,9),'hair')
    block((7,10,3),(9,11,6),'hair_soft')
    block((7,11,8),(9,12,11),'hair_light')
    return hair


def _tail(side):
    # Wider long clumps use the same isotropic cells as the head. Each broad
    # band is connected, with quiet color regions and no tiny surface holes.
    hair = _Cubes(step=.375, origin=(7.875,1.75,6.875))
    bands = [
        (26,28,6,9,1,6),
        (23,26,7,11,0,8),
        (20,23,8,12,0,8),
        (16,20,9,13,0,9),
        (12,16,9,14,0,9),
        (7,12,10,15,0,9),
        (4,7,10,15,0,8),
        (2,4,10,14,1,8),
        (1,2,11,14,2,7),
        (0,1,11,13,3,6),
    ]
    for y0,y1,x0,x1,z0,z1 in bands:
        for x in range(x0,x1):
            relative=x-x0
            front=z0+(1 if relative==0 else 0)
            back=z1-(1 if x==x1-1 else 0)
            color=('hair','hair','hair_soft','hair_soft','hair_mid')[min(relative,4)]
            hair.grid_box((x,y0,front),(x+1,y1,back),color)
    for lo,hi,color in [
        ((9,16,0),(11,21,3),'hair_light'),
        ((9,11,-1),(11,17,2),'hair_soft'),
        ((10,6,-1),(12,12,2),'hair'),
        ((10,3,0),(12,7,3),'hair_soft'),
        ((11,1,2),(13,4,5),'hair'),
        ((13,2,4),(14,5,7),'hair_mid'),
        ((7,24,1),(9,27,4),'hair_light'),
    ]:
        hair.grid_box(lo,hi,color)
    if side<0:
        hair.cells={(-x-1,y,z):color for (x,y,z),color in hair.cells.items()}
        hair.origin=(8.125,1.75,6.875)
    return hair


def _arm(g, side):
    name = 'left arm' if side > 0 else 'right arm'
    start = len(g.faces)
    g.box(name+' bare upper arm', (9.30,6.45,6.50), (10.15,7.65,7.85), 'skin')
    g.box(name+' shoulder light', (9.30,6.72,6.485), (9.78,7.48,6.50), 'skin_light')
    g.box(name+' sleeve upper', (9.28,5.65,6.42), (10.23,6.53,7.88), 'cloth')
    g.box(name+' sleeve middle', (9.18,4.95,6.30), (10.33,5.65,7.98), 'cloth_mid')
    g.box(name+' sleeve lower', (9.08,4.45,6.20), (10.43,4.95,8.08), 'cloth')
    g.box(name+' cuff teal', (9.08,4.24,6.20), (10.43,4.45,8.08), 'teal')
    g.box(name+' small square hand', (9.48,3.94,6.53), (10.13,4.24,7.58), 'skin_light')
    _square(g,name+' gold display pixel',9.60,6.08,6.419,.23,'gold')
    _square(g,name+' cyan display pixel',9.87,6.08,6.419,.23,'meter')
    _square(g,name+' dark sleeve stitch',9.28,5.19,6.299,.25,'cloth_light')
    _square(g,name+' small sleeve stitch',9.77,4.59,6.199,.22,'cloth_light')
    angle = math.radians(17 if side > 0 else 29)
    cosine, sine = math.cos(angle), math.sin(angle)
    def pose(x, y, z):
        x, y = x-9.58, y-7.50
        x, y = cosine*x-sine*y+9.58, sine*x+cosine*y+7.50
        return (x if side > 0 else 16-x, y, z)
    g.transform(start, pose)
    if side < 0:
        for face in g.faces[start:]:
            face['vertices'].reverse()
            face['uv'].reverse()


def _paint_face(g):
    # A single Minecraft-scale face grid follows the reference's dark upper
    # eyes, turquoise lower iris, warm pink skin and soft lower cheek pixels.
    rows = ('SSSSSSSS', 'SSSSSSSS', 'SSSSSSSS', 'HDDSSDDH',
            'WPISSIPW', 'WILSSLIW', 'BSSMMSSB')
    colors = {'S':'face_base', 'H':'face_edge', 'D':'face_lash',
              'W':'face_sclera', 'P':'face_pupil', 'I':'face_iris',
              'L':'face_iris_light', 'B':'face_cheek', 'M':'face_mouth'}
    step = 3.28 / 8
    for row, cells in enumerate(rows):
        for column, color in enumerate(cells):
            _square(g, f'reference face pixel {row} {column}',
                    6.36+column*step, 8+(6-row)*step, 5.739, step, colors[color])


def build():
    g = FigureGeometry(COLORS)
    g.group = 'Square display base'
    g.box('square dark display base', (2.50,0,3.50), (13.50,.80,12.50), 'base')
    g.box('square teal base inlay', (2.50,.80,3.50), (13.50,.92,12.50), 'base_teal')
    g.box('square base top', (2.65,.92,3.65), (13.35,1.00,12.35), 'base_top')

    g.group = 'Voxel twin tails'
    _tail(1).emit(g,'left twin tail')
    _tail(-1).emit(g,'right twin tail')

    g.group = 'Square boots stockings and thighs'
    for side in (-1,1):
        name = 'left leg' if side > 0 else 'right leg'
        x = 8 + side*.95
        g.box(name+' sole', (x-.56,1.00,5.75), (x+.56,1.20,8.25), 'sole')
        g.box(name+' square toe', (x-.55,1.20,5.78), (x+.55,1.57,8.23), 'boot')
        g.box(name+' foot upper step', (x-.50,1.57,6.00), (x+.50,1.83,8.18), 'boot_light')
        g.box(name+' ankle', (x-.47,1.83,6.50), (x+.47,2.15,8.15), 'boot')
        g.box(name+' lower stocking', (x-.50,2.15,6.50), (x+.50,2.85,8.15), 'cloth_dark')
        g.box(name+' upper stocking', (x-.54,2.85,6.47), (x+.54,3.62,8.18), 'boot')
        g.box(name+' teal stocking edge', (x-.54,3.62,6.47), (x+.54,3.77,8.18), 'teal_shade')
        g.box(name+' bare thigh', (x-.48,3.77,6.56), (x+.48,4.48,8.13), 'skin_light')
        _square(g,name+' toe teal square',x-.12,1.24,5.779,.28,'teal')
        _square(g,name+' shin teal square',x-.23,3.05,6.469,.27,'teal_shade')
        _square(g,name+' lower shin square',x-.09,2.44,6.499,.23,'teal_shade')

    g.group = 'Box pleated skirt'
    skirt = _Cubes()
    skirt.box((6.75,4.75,6.50),(9.25,5.25,8.50),'cloth_dark')
    skirt.box((6.50,4.50,6.25),(9.50,4.75,8.75),'cloth')
    skirt.box((6.25,4.25,6.00),(9.75,4.50,9.00),'cloth_mid')
    skirt.box((6.25,4.00,6.00),(9.75,4.25,9.00),'teal_shade')
    for index in range(7):
        x = 6.25 + index*.50
        shade = 'cloth_light' if index%2==0 else 'cloth'
        skirt.box((x,4.25,5.75),(x+.25,4.75,6.50),shade)
        skirt.box((x,4.00,5.75),(x+.25,4.25,6.25),'teal')
        skirt.box((x,4.25,8.50),(x+.25,4.75,9.25),shade)
        skirt.box((x,4.00,8.75),(x+.25,4.25,9.25),'teal')
    for index in range(5):
        z=6.25+index*.50
        for side in (-1,1):
            x0,x1=(6.00,6.50) if side<0 else (9.50,10.00)
            skirt.box((x0,4.25,z),(x1,4.75,z+.25),'cloth')
            skirt.box((x0,4.00,z),(x1,4.25,z+.25),'teal')
    skirt.emit(g,'skirt pleat')

    g.group = 'Stepped gray tunic and turquoise tie'
    shirt = _Cubes()
    shirt.box((6.75,5.00,6.25),(9.25,6.00,8.50),'shirt')
    shirt.box((7.00,6.00,6.25),(9.00,7.00,8.50),'shirt')
    shirt.box((6.75,7.00,6.50),(9.25,7.50,8.50),'shirt_light')
    shirt.box((7.00,7.50,6.75),(9.00,7.75,8.25),'shirt')
    shirt.box((6.75,5.25,6.25),(7.00,5.75,6.50),'shirt_shade')
    shirt.box((8.75,5.50,6.25),(9.25,6.00,6.50),'shirt_light')
    shirt.box((7.00,6.25,8.25),(7.25,7.00,8.50),'shirt_shade')
    shirt.box((8.50,5.25,8.25),(9.00,6.25,8.50),'shirt_shade')
    for side in (-1,1):
        x0,x1=(6.50,7.50) if side<0 else (8.50,9.50)
        shirt.box((x0,4.75,6.00),(x1,5.25,6.50),'shirt_light')
        x0,x1=(6.75,7.50) if side<0 else (8.50,9.25)
        shirt.box((x0,4.50,6.00),(x1,4.75,6.50),'shirt')
        x0,x1=(7.00,7.25) if side<0 else (8.75,9.00)
        shirt.box((x0,4.25,6.00),(x1,4.50,6.50),'shirt_light')
    shirt.emit(g,'tunic cloth')
    g.box('neck', (7.40,7.45,6.85), (8.60,8.35,8.18), 'skin')
    g.box('left collar upper', (7.00,7.30,6.48),(7.70,7.55,6.72),'shirt_light')
    g.box('left collar point', (7.35,7.05,6.23),(7.70,7.30,6.50),'shirt_light')
    g.box('right collar upper',(8.30,7.30,6.48),(9.00,7.55,6.72),'shirt_light')
    g.box('right collar point',(8.30,7.05,6.23),(8.65,7.30,6.50),'shirt_light')
    g.box('tie square knot',(7.75,7.12,6.19),(8.25,7.50,6.45),'tie_dark')
    g.box('tie upper narrow length',(7.82,6.20,6.19),(8.18,7.12,6.40),'tie')
    g.box('tie lower step',(7.72,5.45,6.16),(8.28,6.20,6.40),'tie')
    g.box('tie square flared end',(7.58,5.08,5.93),(8.42,5.45,6.20),'tie')
    g.box('tie end tip',(7.82,4.84,5.93),(8.18,5.08,6.20),'tie_light')
    _square(g,'small tunic badge',8.60,6.87,6.499,.18,'gold')

    g.group = 'Angled cuboid sleeves'
    _arm(g,1)
    _arm(g,-1)

    g.group = 'Flat Minecraft pixel face'
    # Keep the painted face just in front of the crown core at z5.75;
    # coplanar skin/hair layers self-shadowed into black forehead strips.
    g.box('flat square head skin', (6.00,8.00,5.74),(10.00,11.50,9.50),'face_base')
    _paint_face(g)

    g.group = 'Chunky cubic crown and fringe'
    _crown().emit(g,'head hair')

    g.group = 'Block headset and magenta hair ties'
    for side in (-1,1):
        name='left headset' if side>0 else 'right headset'
        def box(label,lo,hi,color):
            if side<0:
                lo,hi=(16-hi[0],lo[1],lo[2]),(16-lo[0],hi[1],hi[2])
            g.box(name+' '+label,lo,hi,color)
        box('square earpiece',(10.30,9.12,5.70),(10.85,11.07,7.18),'headset')
        box('earpiece front step',(10.23,9.42,5.48),(10.80,10.86,5.73),'headset_light')
        box('earpiece magenta pixel',(10.39,9.75,5.43),(10.64,10.48,5.50),'pink')
        box('earpiece top pink square',(10.39,10.55,5.43),(10.64,10.80,5.50),'pink_dark')
        box('upper hair clip upright',(9.96,11.75,6.35),(10.42,13.45,6.88),'headset')
        box('upper hair clip top corner',(9.96,13.20,6.35),(10.42,13.45,7.45),'headset')
        box('hair clip magenta line',(10.09,12.13,6.30),(10.29,13.34,6.37),'pink')
        box('hair clip bright cap',(10.09,13.22,6.30),(10.29,13.45,6.37),'pink_light')
    for face in g.faces:
        narrow = face['group'] == 'Block headset and magenta hair ties'
        narrow |= face['name'].startswith('flat square head skin ')
        if narrow:
            face['vertices'] = [[8+(x-8)*.82,y,z] for x,y,z in face['vertices']]
    return g
