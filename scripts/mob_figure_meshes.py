"""Bake captured vanilla mob quads into inexpensive, non-ticking collectibles.

The development-only capture contains the actual 1.21.1 renderer output; no
entity renderer or animation is shipped as part of the figure block rendering.
Geometry is uniformly scaled into the existing display and packaging envelope.
"""
import base64
import copy
import hashlib
import io
import json
import math
import uuid
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
ART = ROOT / 'art/mob_figures'
CAPTURE = ART / 'vanilla_meshes'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def texture_file(resource):
    namespace, path = resource.split(':', 1)
    assert namespace == 'japanesearcades', resource
    return ASSETS / 'textures' / (path + '.png')


def copy_texture(source):
    namespace, path = source.split(':', 1)
    relative = path.removeprefix('textures/').removesuffix('.png')
    original = CAPTURE / 'textures' / namespace / path
    target = ASSETS / 'textures/block/mob_figures' / namespace / (relative + '.png')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_bytes() != original.read_bytes():
        target.write_bytes(original.read_bytes())
    return 'japanesearcades:block/mob_figures/' + namespace + '/' + relative


def bounds(faces):
    return [[min(v[i] for f in faces for v in f['vertices']),
             max(v[i] for f in faces for v in f['vertices'])] for i in range(3)]


def normal(vertices):
    a, b, c = vertices[:3]
    u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
    return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]


def flattened_materials(mob, data):
    """Bake matching vanilla skin overlays once, avoiding coplanar surfaces.

    Eyes, villager clothing and tropical-fish markings reuse base positions/UVs.
    Fur, armor and wind have different geometry and remain separate meshes.
    This is shader/texture baking of the captured render data, not new artwork.
    """
    groups = {}
    for p in data['primitives']:
        groups.setdefault(p['material'], []).append(p)
    signatures = {i:{tuple(sorted(tuple(round(x,5) for x in v[:5]) for v in p['vertices']))
                     for p in primitives} for i,primitives in groups.items()}
    resources, merged, baked = {}, set(), {}
    def colored(i):
        source = data['materials'][i]['texture']
        namespace, path = source.split(':',1)
        im = Image.open(CAPTURE/'textures'/namespace/path).convert('RGBA')
        colors = {tuple(round(x) for x in v[5:9]) for p in groups[i] for v in p['vertices']}
        assert len(colors) == 1, (mob, i, 'Overlay material has varying tint')
        return ImageChops.multiply(im, Image.new('RGBA', im.size, next(iter(colors))))
    for i,mat in enumerate(data['materials']):
        if i not in signatures:
            continue
        for base in range(i):
            if base in merged or data['materials'][base].get('recommended_exclusion') or base not in signatures:
                continue
            if not signatures[i].issubset(signatures[base]):
                continue
            base_image = baked.get(base)
            if base_image is None:
                base_image = colored(base)
            overlay = colored(i)
            if overlay.size != base_image.size:
                continue
            # Warden repeats its base skin for lighting; it contributes no
            # extra printed features and must not obscure the cyan layers.
            if mat['texture'] != data['materials'][base]['texture']:
                baked[base] = Image.alpha_composite(base_image, overlay)
            merged.add(i)
            break
    for i,im in baked.items():
        resource = f'japanesearcades:block/mob_figures/baked/{mob}_{i}'
        path = texture_file(resource)
        path.parent.mkdir(parents=True, exist_ok=True)
        im.save(path)
        resources[i] = resource
    return resources, merged


def bake_texture_repeat(mob, textures, faces):
    """Entity UVs may repeat; atlas sprites cannot. Tile then remap fish fins."""
    for key, resource in list(textures.items()):
        used = [f for f in faces if f['texture'] == '#'+key]
        coords = [uv for f in used for uv in f['uv']]
        if not coords:
            continue
        x0 = min(0, math.floor(min(uv[0] for uv in coords)/16 + 1e-7))
        y0 = min(0, math.floor(min(uv[1] for uv in coords)/16 + 1e-7))
        x1 = max(1, math.ceil(max(uv[0] for uv in coords)/16 - 1e-7))
        y1 = max(1, math.ceil(max(uv[1] for uv in coords)/16 - 1e-7))
        if (x0,y0,x1,y1) == (0,0,1,1):
            continue
        original = Image.open(texture_file(resource)).convert('RGBA')
        w,h = original.size
        tile = Image.new('RGBA', (w*(x1-x0), h*(y1-y0)))
        for x in range(x1-x0):
            for y in range(y1-y0):
                tile.paste(original, (x*w,y*h))
        target = f'japanesearcades:block/mob_figures/baked/{mob}_{key}_repeat'
        path = texture_file(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        tile.save(path)
        textures[key] = target
        for face in used:
            face['uv'] = [[(u-16*x0)/(x1-x0), (v-16*y0)/(y1-y0)] for u,v in face['uv']]


def capture_faces(mob):
    data = json.loads((CAPTURE / (mob + '.json')).read_text(encoding='utf-8'))
    materials = data['materials']
    flattened, merged = flattened_materials(mob, data)
    textures, faces, omissions = {}, [], []
    forward = data.get('forward_vector', [0, 0, 1])
    turn = -1 if forward[2] > 0 else 1
    seen = set()
    for index, primitive in enumerate(data['primitives']):
        material = materials[primitive['material']]
        if primitive['material'] in merged:
            continue
        excluded = material.get('recommended_exclusion', False)
        if excluded:
            omissions.append({'material': primitive['material'], 'reason': material.get('exclusion_reason', 'Animated effect')})
            continue
        source = material.get('texture')
        if not source:
            raise ValueError((mob, 'Untextured primitive', material))
        key = 'skin' + str(primitive['material'])
        if key not in textures:
            textures[key] = flattened.get(primitive['material']) or copy_texture(source)
        stream = primitive['vertices']
        count = 3 if primitive['mode'] == 'TRIANGLES' else 4
        assert len(stream) % count == 0, (mob, index, len(stream))
        for start in range(0, len(stream), count):
            verts = stream[start:start+count]
            if all(v[8] == 0 for v in verts):
                continue
            positions = [[v[0]*turn, v[1], v[2]*turn] for v in verts]
            if math.sqrt(sum(x*x for x in normal(positions))) < 1e-10:
                continue
            uvs = [[v[3]*16, v[4]*16] for v in verts]
            colors = [[1,1,1,1] if primitive['material'] in flattened else
                      [v[5]/255, v[6]/255, v[7]/255, 1] for v in verts]
            if mob == 'tropical_fish' and source.endswith('/tropical_a.png'):
                # Select the vanilla orange/white Kob palette; geometry and
                # markings remain the captured small tropical-fish variant.
                # DyeColor.ORANGE.getTextureDiffuseColor() in 1.21.1 is F9801D.
                colors = [[249/255,128/255,29/255,1] for _ in verts]
            expected = [sum(v[i] for v in verts) * (turn if i != 10 else 1) for i in (9, 10, 11)]
            if sum(a*b for a,b in zip(normal(positions), expected)) < 0:
                positions.reverse(); uvs.reverse(); colors.reverse()
            signature = (key, tuple(sorted(tuple(round(x,6) for x in p)+tuple(round(x,6) for x in uv)
                                          for p,uv in zip(positions,uvs))))
            if signature in seen:
                continue
            seen.add(signature)
            f = {'name': f'{mob} surface {index}-{start//count}', 'group': mob.replace('_', ' ').title(),
                 'texture': '#'+key, 'vertices': positions, 'uv': uvs, 'glow': False, 'colors': colors}
            faces.append(f)
            if material.get('no_cull', material.get('noCull', False)):
                back = copy.deepcopy(f)
                back['name'] += ' reverse'
                for field in ('vertices', 'uv', 'colors'):
                    back[field].reverse()
                faces.append(back)
    assert faces, (mob, 'No displayable geometry')
    bake_texture_repeat(mob, textures, faces)
    original_bounds = bounds(faces)
    dimensions = [hi-lo for lo,hi in original_bounds]
    scale = min(limit / size for limit,size in zip((7.3,10.45,7.0),dimensions) if size > 1e-8)
    center = [(lo+hi)/2 for lo,hi in original_bounds]
    for f in faces:
        f['vertices'] = [[round(8+(p[0]-center[0])*scale, 7),
                          round(.73+(p[1]-original_bounds[1][0])*scale, 7),
                          round(8+(p[2]-center[2])*scale, 7)] for p in f['vertices']]
    return textures, faces, {'source': str((CAPTURE/(mob+'.json')).relative_to(ROOT)).replace('\\','/'),
                            'sha256': hashlib.sha256((CAPTURE/(mob+'.json')).read_bytes()).hexdigest(),
                            'source_bounds': original_bounds, 'uniform_scale': scale,
                            'flattened_materials': sorted(merged),
                            'display_variant': 'orange/white Kob' if mob == 'tropical_fish' else 'captured vanilla variant',
                            'omitted_effects': list({json.dumps(x,sort_keys=True):x for x in omissions}.values())}


def export_mesh(name, mob, textures, faces, boxed, core):
    textures = dict(textures)
    textures['package'] = 'japanesearcades:block/' + mob + '_figure_package'
    textures['particle'] = textures['package']
    extents = bounds(faces)
    limits = ((3,13),(0,14),(4,12)) if boxed else ((4,12),(0,11.5),(4,12))
    assert all(lo >= floor-1e-5 and hi <= ceiling+1e-5
               for (lo,hi),(floor,ceiling) in zip(extents,limits)), (name, extents)
    assert len(faces) < 1000, (name, len(faces))
    write(ART/(name+'.geometry.json'), {'textures': textures, 'meshes': faces,
                                      'bounds': extents, 'face_count': len(faces)})
    lines = ['# Static vanilla mob collectible: '+mob,
             'mtllib japanesearcades:models/block/'+name+'.mtl']
    index = 1
    for face in faces:
        lines.append('usemtl '+face['texture'][1:])
        lines.extend('v '+' '.join(f'{v/16:.9f}' for v in p) for p in face['vertices'])
        lines.extend(f'vt {u/16:.9f} {v/16:.9f}' for u,v in face['uv'])
        direction = normal(face['vertices'])
        magnitude = math.sqrt(sum(v*v for v in direction))
        assert magnitude > 1e-12, (name, face['name'], 'Degenerate exported face')
        # ObjModel does not calculate normals for a four-field colored index.
        # Explicit normals preserve lighting for v/vt/vn/vc colored vertices.
        lines.extend('vn '+' '.join(f'{v/magnitude:.9f}' for v in direction) for _ in face['vertices'])
        colors = face.get('colors', [face.get('color', [1,1,1,1])]*len(face['vertices']))
        lines.extend('vc '+' '.join(f'{v:.7f}' for v in c) for c in colors)
        lines.append('f '+' '.join(f'{index+i}/{index+i}/{index+i}/{index+i}' for i in range(len(face['vertices']))))
        index += len(face['vertices'])
    (ASSETS/'models/block'/(name+'.obj')).write_text('\n'.join(lines)+'\n', encoding='utf-8')
    mtl = []
    for key in textures:
        if key == 'particle':
            continue
        mtl.extend(['newmtl '+key, 'Ka 0 0 0', 'Kd 1 1 1', 'map_Kd #'+key, ''])
    (ASSETS/'models/block'/(name+'.mtl')).write_text('\n'.join(mtl), encoding='utf-8')
    model = {'parent': 'minecraft:block/block', 'loader': 'neoforge:obj',
             'model': 'japanesearcades:models/block/'+name+'.obj', 'automatic_culling': False,
             'shade_quads': True, 'flip_v': False, 'emissive_ambient': False,
             'ambientocclusion': True, 'render_type': 'minecraft:cutout', 'textures': textures}
    write(ASSETS/'models/block'/(name+'.json'), model)
    model = copy.deepcopy(model)
    model.update({'gui_light':'front', 'ambientocclusion':False, 'display':{
        'gui':{'rotation':[14,205,0],'translation':[0,0,0],'scale':[1,1,1] if boxed else [1.12,1.12,1.12]},
        'ground':{'translation':[0,2,0],'scale':[.5,.5,.5]},
        'fixed':{'rotation':[0,180,0],'scale':[.8,.8,.8]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.4,.4,.4]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,1,0],'scale':[.55,.55,.55]}}})
    write(ASSETS/'models/item'/(name+'.json'), model)
    write(ASSETS/'blockstates'/(name+'.json'), {'variants':{
        'facing='+direction:{'model':'japanesearcades:block/'+name,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270))}})
    write(core.LOOT/(name+'.json'), {'type':'minecraft:block','pools':[{'rolls':1,
        'conditions':[{'condition':'minecraft:survives_explosion'}],
        'entries':[{'type':'minecraft:item','name':'japanesearcades:'+name}]}]})
    export_blockbench(name, textures, faces)
    print(f'{name}: {len(faces)} baked faces, bounds={extents}')
    return {'model':name, 'placed_faces':len(faces), 'inventory_faces':len(faces), 'bounds':extents}


def export_blockbench(name, textures, faces):
    texdata, indices = [], {}
    for key, resource in textures.items():
        if key == 'particle':
            continue
        filename = texture_file(resource)
        w,h = Image.open(filename).size
        indices[key] = len(texdata)
        texdata.append({'name':filename.name,'id':str(len(texdata)),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+key)), 'width':w,'height':h,
            'uv_width':w,'uv_height':h,'source':'data:image/png;base64,'+base64.b64encode(filename.read_bytes()).decode(),
            'mode':'bitmap','visible':True})
    elements, tinted = [], {}
    for f in faces:
        keys = ['v'+str(i) for i in range(len(f['vertices']))]
        texture = indices[f['texture'][1:]]
        colors = f.get('colors', [[1,1,1,1]])
        tint = tuple(round(v*255) for v in colors[0])
        assert all(tuple(round(v*255) for v in c) == tint for c in colors), (name, 'Non-uniform authoring tint')
        if tint != (255,255,255,255):
            tint_key = (texture,tint)
            if tint_key not in tinted:
                original = Image.open(texture_file(textures[f['texture'][1:]])).convert('RGBA')
                colored = ImageChops.multiply(original,Image.new('RGBA',original.size,tint))
                encoded = io.BytesIO(); colored.save(encoded,format='PNG')
                entry = copy.deepcopy(texdata[texture])
                entry.update({'id':str(len(texdata)), 'name':entry['name']+'_tint_'+'_'.join(map(str,tint)),
                    'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/tint/'+str(tint_key))),
                    'source':'data:image/png;base64,'+base64.b64encode(encoded.getvalue()).decode()})
                tinted[tint_key] = len(texdata)
                texdata.append(entry)
            texture = tinted[tint_key]
        w,h = texdata[texture]['width'],texdata[texture]['height']
        elements.append({'name':f['name'], 'type':'mesh',
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+f['name'])), 'origin':[0,0,0], 'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])), 'faces':{'face':{'vertices':keys,
            'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture}},
            'visibility':True,'export':True})
    write(ART/(name+'.bbmodel'), {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':name, 'resolution':{'width':64,'height':64}, 'elements':elements, 'textures':texdata,
        'outliner':[e['uuid'] for e in elements]})


def export_captured_mob(mob, core):
    textures, miniature, provenance = capture_faces(mob)
    base = core.Geometry(mob)
    base.base()
    loose = core.meshes(base.elements) + miniature
    package = core.meshes(core.packaging(mob).elements)
    packed = copy.deepcopy(loose)
    for face in packed:
        face['vertices'] = [[x,y+.6,z] for x,y,z in face['vertices']]
    audit = []
    for name, faces, boxed in ((mob+'_figure',loose,False),
                               (mob+'_figure_box',package,True),
                               ('boxed_'+mob+'_figure',package+packed,True)):
        # Empty boxes need only their single print texture, never a mob skin.
        entry = export_mesh(name,mob,textures if name != mob+'_figure_box' else {},faces,boxed,core)
        entry['vanilla_capture'] = provenance
        audit.append(entry)
    return audit
