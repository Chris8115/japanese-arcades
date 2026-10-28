"""Export the reference-based Bombergirl Rainbow cabinet as three static OBJ sections."""
from pathlib import Path
from collections import defaultdict
import base64
import json
import math
import uuid
from PIL import Image
from ddr_mesh_export import pieces, quads
from obj_mesh_optimizer import optimize_obj
from bombergirl_geometry import build
from bombergirl_textures import generate

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/bombergirl'
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def main():
    for directory in (ART, ASSETS/'models/block', ASSETS/'models/item', ASSETS/'blockstates'):
        directory.mkdir(parents=True, exist_ok=True)
    paths = generate()
    textures = {key: 'japanesearcades:block/bombergirl_' + key for key in paths}
    textures['particle'] = textures['materials']
    geometry, metadata = build()
    surfaces = geometry.faces
    assert len({f['name'] for f in surfaces}) == len(surfaces), 'Duplicate face names'
    for face in surfaces:
        assert 3 <= len(face['vertices']) <= 4 and len(face['uv']) == len(face['vertices']), face['name']
        assert face['texture'][1:] in paths, face['name']
        assert all(math.isfinite(v) for p in face['vertices'] for v in p), face['name']
        assert all(-1e-8 <= v <= 16+1e-8 for uv in face['uv'] for v in uv), (face['name'], face['uv'])
        face['uv'] = [[max(0,min(16,value)) for value in uv] for uv in face['uv']]
        a,b,c = face['vertices'][:3]
        ab = [b[i]-a[i] for i in range(3)]; ac = [c[i]-a[i] for i in range(3)]
        cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
        assert sum(v*v for v in cross) > 1e-16, ('Degenerate face', face['name'])
        if len(face['vertices']) == 4:
            d = face['vertices'][3]
            assert abs(sum(cross[i]*(d[i]-a[i]) for i in range(3))) < 1e-6, ('Nonplanar quad', face['name'])

    def obj(path, faces, transform):
        lines = ['# Bombergirl Rainbow cabinet; units are blocks.',
                 'mtllib japanesearcades:models/block/bombergirl.mtl']
        index = 1; last = None
        for face in faces:
            material = face['texture'][1:] + ('_glow' if face['glow'] else '_surface')
            if material != last:
                lines.append('usemtl ' + material); last = material
            lines.extend('v ' + ' '.join('%.9f' % value for value in transform(point)) for point in face['vertices'])
            lines.extend('vt %.9f %.9f' % (u/16, 1-v/16) for u,v in face['uv'])
            lines.append('f ' + ' '.join('%d/%d' % (index+i,index+i) for i in range(len(face['vertices']))))
            index += len(face['vertices'])
        optimized, stats = optimize_obj('\n'.join(lines) + '\n')
        path.write_text(optimized, encoding='utf-8')
        # Count the final shipped faces, not merely the source surfaces.
        stats['exported_faces'] = sum(line.startswith('f ') for line in optimized.splitlines())
        return stats

    def wrapper(name, item=False):
        model = {'parent':'minecraft:block/block', 'loader':'neoforge:obj',
                 'model':'japanesearcades:models/' + name + '.obj', 'automatic_culling':False,
                 'shade_quads':True, 'flip_v':True, 'emissive_ambient':True,
                 'ambientocclusion':not item, 'render_type':'minecraft:cutout_mipped_all', 'textures':textures}
        if item:
            model.update({'gui_light':'front', 'display':{
                'gui':{'rotation':[10,225,0], 'translation':[0,-5.2,0], 'scale':[.37,.37,.37]},
                'ground':{'translation':[0,0,0], 'scale':[.20,.20,.20]},
                'fixed':{'rotation':[0,180,0], 'translation':[0,-7,0], 'scale':[.36,.36,.36]},
                'thirdperson_righthand':{'rotation':[75,45,0], 'scale':[.27,.27,.27]},
                'firstperson_righthand':{'rotation':[0,45,0], 'translation':[0,-3,0], 'scale':[.35,.35,.35]}}})
        return model

    parts = {key:[] for key in ('base','console','marquee')}
    for face in surfaces:
        for fragment in pieces(list(zip(face['vertices'], face['uv'])), 1, [16,32]):
            for poly in quads(fragment):
                row = min(2,max(0,int(sum(p[1] for p,uv in poly)/len(poly)//16)))
                parts[tuple(parts)[row]].append({**face, 'vertices':[p for p,uv in poly], 'uv':[uv for p,uv in poly]})
    statistics = {}
    for row,(part,faces) in enumerate(parts.items()):
        name = 'block/bombergirl_' + part
        statistics[part] = obj(ASSETS/'models'/(name+'.obj'), faces,
                              lambda p,row=row: [p[0]/16,(p[1]-row*16)/16,p[2]/16])
        write_json(ASSETS/'models'/(name+'.json'), wrapper(name))
    statistics['item'] = obj(ASSETS/'models/item/bombergirl.obj', surfaces, lambda p:[v/16 for v in p])
    write_json(ASSETS/'models/item/bombergirl.json', wrapper('item/bombergirl', True))
    material_lines=[]
    for key,glow in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
        material_lines.extend(['newmtl '+key+('_glow' if glow else '_surface'),
                               'Ka '+('1 1 1' if glow else '0 0 0'), 'Kd 1 1 1', 'map_Kd #'+key, ''])
    (ASSETS/'models/block/bombergirl.mtl').write_text('\n'.join(material_lines),encoding='utf-8')
    write_json(ASSETS/'blockstates/bombergirl.json', {'variants':{
        'facing='+direction+',part='+part: {'model':'japanesearcades:block/bombergirl_'+part, **({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in parts}})
    statistics['placed_faces'] = sum(statistics[key]['exported_faces'] for key in parts)
    statistics['inventory_faces'] = statistics['item']['exported_faces']
    bounds = [[min(p[i] for f in surfaces for p in f['vertices']), max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
    write_json(ART/'geometry.json', {**metadata, 'textures':textures, 'meshes':surfaces, 'bounds':bounds, 'statistics':statistics})

    keys=list(paths); sizes={key:Image.open(path).size for key,path in paths.items()}
    groups=defaultdict(list); elements=[]
    for f in surfaces:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'bombergirl/'+f['name'])); key=f['texture'][1:]
        width,height=sizes[key]; vertices=['v'+str(i) for i in range(len(f['vertices']))]
        elements.append({'name':f['name'], 'type':'mesh', 'uuid':uid, 'origin':[0,0,0], 'rotation':[0,0,0],
            'vertices':dict(zip(vertices,f['vertices'])), 'faces':{'face':{'vertices':vertices,
                'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(vertices,f['uv'])}, 'texture':keys.index(key)}},
            'visibility':True, 'export':True})
        groups[f['group']].append(uid)
    textures_bb=[]
    for i,(key,path) in enumerate(paths.items()):
        width,height=sizes[key]
        textures_bb.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'bombergirl/'+key)), 'width':width,'height':height,
            'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
            'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(ART/'bombergirl.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':"Bombergirl Rainbow",'model_identifier':'bombergirl','visible_box':[2,3,2],
        'resolution':{'width':256,'height':256}, 'elements':elements,'textures':textures_bb,
        'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'bombergirl/group/'+name)),
                    'origin':[8,0,8],'children':children} for name,children in groups.items()]})
    # Apply the same lossless aligned-UV crop workflow as the larger cabinets.
    # Register only this generator's resources; shared cabinet lists stay intact.
    from compact_cabinet_textures import CABINETS, compact_cabinet
    CABINETS['bombergirl']=('bombergirl','make_bombergirl_model.py',
        ['bombergirl_'+key for key in paths if key!='materials'])
    compaction=compact_cabinet('bombergirl')
    write_json(ART/'texture_compaction.json',compaction)
    print(json.dumps({'bounds':bounds,'placed_faces':statistics['placed_faces'],
                      'inventory_faces':statistics['inventory_faces']}, indent=2))

if __name__ == '__main__':
    main()
