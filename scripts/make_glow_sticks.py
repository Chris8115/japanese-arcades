"""Build small, static concert penlights; no block entity or animated renderer.

Run with Python + Pillow. Mesh coordinates use Minecraft model pixels; shared
OBJ geometry and materials are recolored by seven tiny tube textures. The light
tube alone uses NeoForge OBJ ambient emission. Handles remain normally shaded.
"""
import json
import math
from pathlib import Path

from PIL import Image
from obj_mesh_optimizer import optimize_obj

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
DATA = ROOT / 'src/main/resources/data/japanesearcades'
ART = ROOT / 'art/glow_sticks'
COLORS = {
    'blue': (32, 155, 255),
    'red': (255, 47, 65),
    'yellow': (255, 222, 30),
    'green': (50, 246, 111),
    'pink': (255, 83, 191),
    'purple': (172, 71, 255),
    'orange': (255, 134, 32),
}
SIDES = 12
DISPLAY = {
    'gui': {'rotation': [8, -22, -28], 'translation': [0, 1, 0], 'scale': [1.03]*3},
    'ground': {'translation': [0, 3, 0], 'scale': [.55]*3},
    'fixed': {'translation': [0, 1, 0], 'scale': [.8]*3},
    'firstperson_righthand': {'rotation': [0, 0, -10], 'translation': [-1.5, 3.75, 0], 'scale': [.6]*3},
    'firstperson_lefthand': {'rotation': [0, 0, -10], 'translation': [-1.5, 3.75, 0], 'scale': [.6]*3},
    'thirdperson_righthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 3.9], 'scale': [.65]*3},
    'thirdperson_lefthand': {'rotation': [90, 0, 0], 'translation': [0, 1, 3.9], 'scale': [.65]*3},
    'head': {'translation': [0, 12, 0], 'scale': [.8]*3},
}


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def textures():
    folder = ASSETS / 'textures/block'
    folder.mkdir(parents=True, exist_ok=True)
    # Small procedural material swatches: plastic, rubber and brushed collar.
    palette = Image.new('RGB', (16, 16))
    for y in range(16):
        for x in range(16):
            color = (239, 243, 246) if x < 8 and y < 8 else (
                (185, 199, 211) if y < 8 else ((52, 61, 77) if x < 8 else (106, 124, 143)))
            palette.putpixel((x, y), color)
    palette.save(folder / 'glow_stick_handle.png')
    for name, rgb in COLORS.items():
        tube = Image.new('RGB', (16, 16))
        for y in range(16):
            for x in range(16):
                # Broad diffused highlight wraps around a closed cylindrical tube.
                highlight = .06 + .32 * max(0, math.cos((x / 16 - .22) * math.tau))**6
                strength = .92 + .08 * math.sin(math.pi * y / 15)
                color = tuple(round((c + (255-c) * highlight) * strength) for c in rgb)
                tube.putpixel((x, y), color)
        tube.save(folder / f'{name}_glow_stick.png')


class Mesh:
    def __init__(self):
        self.faces = []

    def face(self, name, vertices, material, uv=None):
        if uv is None:
            uv = [(0.25, 0.25)] * len(vertices)
        self.faces.append({'name': name, 'vertices': vertices, 'material': material, 'uv': uv})

    def band(self, name, y0, r0, y1, r1, material='plastic'):
        for i in range(SIDES):
            a, b = [(n / SIDES + 1 / (2*SIDES)) * math.tau for n in (i, i+1)]
            points = [(8+r0*math.cos(a), y0, 8+r0*math.sin(a)),
                      (8+r1*math.cos(a), y1, 8+r1*math.sin(a)),
                      (8+r1*math.cos(b), y1, 8+r1*math.sin(b)),
                      (8+r0*math.cos(b), y0, 8+r0*math.sin(b))]
            uv = None if material != 'tube' else [(i/SIDES, 1), (i/SIDES, 0), ((i+1)/SIDES, 0), ((i+1)/SIDES, 1)]
            self.face(name, points, material, uv)

    def cap(self, name, y, r, material, upward):
        for i in range(SIDES):
            a, b = [(n / SIDES + 1 / (2*SIDES)) * math.tau for n in (i, i+1)]
            points = [(8, y, 8), (8+r*math.cos(b), y, 8+r*math.sin(b)), (8+r*math.cos(a), y, 8+r*math.sin(a))]
            if not upward:
                points.reverse()
            self.face(name, points, material)

    def box(self, name, low, high, material):
        x0, y0, z0 = low
        x1, y1, z1 = high
        for points in (
            [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
            [(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
            [(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
            [(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],
            [(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],
            [(x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)],
        ):
            self.face(name, points, material)

    def strap(self):
        # A thin closed ribbon loop attached beside the handle; 48 faces total.
        start = len(self.faces)
        for i in range(12):
            a, b = [n / 12 * math.tau for n in (i, i+1)]
            def p(angle, outer, z):
                return (9.7+(.9 if outer else .74)*math.cos(angle),
                        1.38+(1.08 if outer else .91)*math.sin(angle), z)
            self.face('Wrist loop front', [p(a,1,7.9), p(b,1,7.9), p(b,0,7.9), p(a,0,7.9)], 'rubber')
            self.face('Wrist loop back', [p(a,0,8.05), p(b,0,8.05), p(b,1,8.05), p(a,1,8.05)], 'rubber')
            self.face('Wrist loop outer', [p(a,1,8.05), p(b,1,8.05), p(b,1,7.9), p(a,1,7.9)], 'rubber')
            self.face('Wrist loop inner', [p(a,0,7.9), p(b,0,7.9), p(b,0,8.05), p(a,0,8.05)], 'rubber')
        for face in self.faces[start:]:
            face['vertices'].reverse()


def geometry():
    mesh = Mesh()
    mesh.band('Base bevel', 0, .85, .25, 1.0)
    mesh.cap('Grip bottom', 0, .85, 'plastic', False)
    mesh.band('Color identification ring', .25, 1.0, .5, 1.0, 'tube')
    mesh.band('Grip lower taper', .5, 1.0, .72, .92)
    mesh.band('White grip', .72, .92, 3.9, .92)
    mesh.band('Collar bevel', 3.9, .92, 4.12, 1.27)
    mesh.band('Silver collar', 4.12, 1.27, 4.38, 1.27, 'silver')
    mesh.band('Upper collar bevel', 4.38, 1.27, 4.7, 1.12)
    mesh.band('Diffused luminous tube', 4.7, 1.12, 12.98, 1.12, 'tube')
    mesh.band('Rounded tube end', 12.98, 1.12, 13.3, .85, 'tube')
    mesh.cap('Luminous end cap', 13.3, .85, 'tube', True)
    mesh.box('Recessed power button', (7.7, 2.55, 7.035), (8.3, 3.15, 7.135), 'rubber')
    mesh.box('Color status indicator', (7.87, 2.1, 7.025), (8.13, 2.29, 7.12), 'tube')
    mesh.strap()
    return mesh


def export_obj(mesh, wall=False):
    vertices, uvs, vertex_ids, uv_ids, lines = [], [], {}, {}, []
    material = None
    def transform(point):
        x, y, z = point
        if wall:
            angle = math.radians(22.5)
            y, z = 1.5+y*math.cos(angle)-(z-8)*math.sin(angle), 1.4+y*math.sin(angle)+(z-8)*math.cos(angle)
        return (x/16, y/16, z/16)
    for face in mesh.faces:
        if material != face['material']:
            material = face['material']
            lines.append('usemtl ' + material)
        refs = []
        for vertex, uv in zip(face['vertices'], face['uv']):
            p = tuple(round(c, 9) for c in transform(vertex))
            # Solid palette quadrants are accessed through each material.
            t = (round(uv[0], 9), round(1-uv[1], 9))
            if p not in vertex_ids:
                vertices.append(p)
                vertex_ids[p] = len(vertices)
            if t not in uv_ids:
                uvs.append(t)
                uv_ids[t] = len(uvs)
            refs.append(f'{vertex_ids[p]}/{uv_ids[t]}')
        lines.append('f ' + ' '.join(refs))
    return '\n'.join(['# Japanese Arcades concert penlight; static baked geometry',
                      'mtllib japanesearcades:models/block/glow_stick.mtl',
                      *('v '+' '.join(f'{c:.9f}' for c in p) for p in vertices),
                      *('vt '+' '.join(f'{c:.9f}' for c in uv) for uv in uvs), *lines]) + '\n'


def run():
    textures()
    mesh = geometry()
    # UVs for the three normally-lit material swatches in the shared handle map.
    for face in mesh.faces:
        if face['material'] == 'silver':
            face['uv'] = [(.75, .25)] * len(face['vertices'])
        elif face['material'] == 'rubber':
            face['uv'] = [(.25, .75)] * len(face['vertices'])
    folder = ASSETS / 'models/block'
    folder.mkdir(parents=True, exist_ok=True)
    materials = []
    for name in ('plastic', 'silver', 'rubber', 'tube'):
        materials += [f'newmtl {name}', 'Kd 1 1 1',
                      ('Ka 1 1 1' if name == 'tube' else 'Ka 0 0 0'),
                      'd 1', f'map_Kd #{"tube" if name == "tube" else "handle"}', '']
    (folder / 'glow_stick.mtl').write_text('\n'.join(materials), encoding='utf-8')
    # Reuse the upright mesh for inventory and floor placement.
    for wall in (False, True):
        name = 'glow_stick_wall' if wall else 'glow_stick'
        text = export_obj(mesh, wall)
        if wall:
            bracket = Mesh()
            bracket.box('Low profile wall clip', (7.4, 1.15, 0), (8.6, 2.05, 1.65), 'silver')
            # The wall clip is already in world-model coordinates.
            base = Mesh()
            for face in mesh.faces:
                angle = math.radians(22.5)
                base.faces.append({**face, 'vertices':[(x, 1.5+y*math.cos(angle)-(z-8)*math.sin(angle),
                                                      1.4+y*math.sin(angle)+(z-8)*math.cos(angle))
                                                     for x,y,z in face['vertices']]})
            for face in bracket.faces:
                face['uv'] = [(.75,.25)] * len(face['vertices'])
            base.faces += bracket.faces
            text = export_obj(base)
        text, _ = optimize_obj(text)
        (folder / f'{name}.obj').write_text(text, encoding='utf-8')
        write(folder / f'{name}.json', {
            'parent':'minecraft:block/block', 'loader':'neoforge:obj',
            'model':f'japanesearcades:models/block/{name}.obj',
            'automatic_culling':False, 'shade_quads':True, 'flip_v':True,
            'emissive_ambient':True, 'ambientocclusion':False,
            'render_type':'minecraft:solid',
            'textures':{'handle':'japanesearcades:block/glow_stick_handle'},
            'display':DISPLAY,
        })
    for color in COLORS:
        path = f'{color}_glow_stick'
        for wall in (False, True):
            suffix = '_wall' if wall else ''
            write(folder / f'{path}{suffix}.json', {
                'parent':f'japanesearcades:block/glow_stick{suffix}',
                'textures':{'tube':f'japanesearcades:block/{path}',
                            'particle':f'japanesearcades:block/{path}'},
            })
        write(ASSETS / f'models/item/{path}.json', {'parent':f'japanesearcades:block/{path}'})
        variants = {'facing=up':{'model':f'japanesearcades:block/{path}'}}
        for direction, rotation in [('south',0),('west',90),('north',180),('east',270)]:
            variants[f'facing={direction}'] = {'model':f'japanesearcades:block/{path}_wall', 'y':rotation}
        write(ASSETS / f'blockstates/{path}.json', {'variants':variants})
        write(DATA / f'loot_table/blocks/{path}.json', {
            'type':'minecraft:block',
            'pools':[{'rolls':1, 'entries':[{'type':'minecraft:item','name':f'japanesearcades:{path}'}],
                      'conditions':[{'condition':'minecraft:survives_explosion'}]}],
            'random_sequence':f'japanesearcades:blocks/{path}',
        })
    lang_path = ASSETS / 'lang/en_us.json'
    lang = json.loads(lang_path.read_text(encoding='utf-8'))
    for color in COLORS:
        lang[f'block.japanesearcades.{color}_glow_stick'] = f'{color.title()} Concert Glow Stick'
    write(lang_path, lang)
    # Measure final exported face records rather than deriving a budget from parts.
    counts = {name:sum(line.startswith('f ') for line in (folder/f'{name}.obj').read_text().splitlines())
              for name in ('glow_stick','glow_stick_wall')}
    assert max(counts.values()) < 10000
    write(ART / 'geometry.json', {
        'colors':list(COLORS), 'model_pixel_height':13.3, 'tube_sides':SIDES,
        'faces':{'placed_floor':counts['glow_stick'], 'placed_wall':counts['glow_stick_wall'],
                 'inventory_per_item':counts['glow_stick'], 'dual_wield':counts['glow_stick']*2},
        'rendering':'Static solid baked OBJ; tube material emissive, handle normally lit; no block entity.',
        'textures':'Eight 16x16 textures, one handle plus seven color tubes.',
        'hand_transforms':'Both hands provided; Minecraft mirrors the left hand natively.',
    })
    print(json.dumps(counts))


if __name__ == '__main__':
    run()
