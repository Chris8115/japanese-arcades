"""Export maimai's smooth exterior through NeoForge's bundled OBJ loader."""
import base64
import json
import math
import uuid
from collections import defaultdict

from PIL import Image
from maimai_profile_geometry import shape_point, BEND_LEVELS
from obj_mesh_optimizer import optimize_obj

FACE_INDICES = {'north': (2,1,0,3), 'east': (6,5,1,2), 'south': (7,4,5,6),
                'west': (3,0,4,7), 'up': (3,7,6,2), 'down': (4,0,1,5)}


def clip(poly, axis, level, above):
    """Clip position/UV pairs together, maintaining outward winding."""
    result = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ina = a[0][axis] >= level-1e-9 if above else a[0][axis] <= level+1e-9
        inb = b[0][axis] >= level-1e-9 if above else b[0][axis] <= level+1e-9
        if ina:
            result.append(a)
        if ina != inb:
            t = (level-a[0][axis]) / (b[0][axis]-a[0][axis])
            result.append(([p+t*(q-p) for p,q in zip(a[0],b[0])],
                           [p+t*(q-p) for p,q in zip(a[1],b[1])]))
    unique = []
    for entry in result:
        if not unique or any(abs(a-b)>1e-8 for a,b in zip(entry[0],unique[-1][0])):
            unique.append(entry)
    if len(unique)>1 and all(abs(a-b)<1e-8 for a,b in zip(unique[0][0],unique[-1][0])):
        unique.pop()
    return unique


def pieces(poly, axis, levels):
    result = [poly]
    for level in levels:
        following = []
        for part in result:
            low, high = min(v[0][axis] for v in part), max(v[0][axis] for v in part)
            if low+1e-8 < level < high-1e-8:
                following.extend(p for p in (clip(part,axis,level,False),
                                              clip(part,axis,level,True)) if len(p)>=3)
            else:
                following.append(part)
        result = following
    return result


def quads(poly):
    if len(poly)<=4:
        return [poly]
    return [[poly[0],poly[i],poly[i+1]] for i in range(1,len(poly)-1)]


def cube_vertices(e):
    a,b=e['from'],e['to']
    vertices=[[a[0],a[1],a[2]],[b[0],a[1],a[2]],[b[0],b[1],a[2]],[a[0],b[1],a[2]],
              [a[0],a[1],b[2]],[b[0],a[1],b[2]],[b[0],b[1],b[2]],[a[0],b[1],b[2]]]
    if 'rotation' in e:
        r=e['rotation'];o=r['origin'];c=math.cos(math.radians(r['angle']));s=math.sin(math.radians(r['angle']))
        i,j={'x':(1,2),'y':(2,0),'z':(0,1)}[r['axis']]
        for v in vertices:
            x,y=v[i]-o[i],v[j]-o[j]
            v[i],v[j]=o[i]+x*c-y*s,o[j]+x*s+y*c
    return vertices


def make_meshes(elements):
    meshes=[]
    # The shape function interpolates these same secants for every vertex,
    # including tiny hardware endpoints between grid levels. Hardware remains
    # joined without splitting the entire cabinet at all of its local edges.
    curve_levels=BEND_LEVELS
    for e in elements:
        vertices=cube_vertices(e)
        for direction,indices in FACE_INDICES.items():
            if direction not in e['faces']:
                continue
            face=e['faces'][direction]
            u0,v0,u1,v1=face['uv']
            coords=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)]
            turns=face.get('rotation',0)//90
            coords=coords[turns:]+coords[:turns]
            poly=list(zip([vertices[i] for i in indices],coords))
            # Only the curved transition needs subdivision. Upper screens are
            # single inclined planes with uninterrupted artwork and no treads.
            for band,part in enumerate(pieces(poly,1,curve_levels)):
                shaped=[(shape_point(v,e['_group']),uv) for v,uv in part]
                for fragment,quad in enumerate(quads(shaped)):
                    meshes.append({'name':e['name']+' '+direction+' %d-%d'%(band,fragment),
                                   'group':e['_group'],'source_direction':direction,
                                   'texture':face['texture'],'glow':'neoforge_data' in face,
                                   'vertices':[v for v,uv in quad],'uv':[uv for v,uv in quad]})
    return meshes


def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def material_name(mesh):
    return mesh['texture'][1:]+('_lit' if mesh['glow'] else '_surface')


def write_obj(path,meshes,transform):
    lines=['# maimai DX smooth profile; coordinates in Minecraft block units.',
           'mtllib japanesearcades:models/block/maimai.mtl','o maimai']
    current=None;index=1
    for mesh in meshes:
        material=material_name(mesh)
        if current!=material:
            lines.append('usemtl '+material);current=material
        for point in mesh['vertices']:
            lines.append('v '+' '.join('%.9f'%v for v in transform(point)))
        for u,v in mesh['uv']:
            lines.append('vt %.9f %.9f'%(u/16,1-v/16))
        lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(mesh['vertices']))))
        index+=len(mesh['vertices'])
    optimized,statistics=optimize_obj('\n'.join(lines)+'\n')
    path.write_text(optimized,encoding='utf-8')
    return statistics


def export_mesh_assets(elements,textures,statistics,root,raw_meshes=()):
    art=root/'art/maimai';assets=root/'src/main/resources/assets/japanesearcades'
    block=assets/'models/block';mesh=make_meshes(elements)
    for face in raw_meshes:
        for band,part in enumerate(pieces(list(zip(face['vertices'],face['uv'])),1,BEND_LEVELS)):
            shaped=[(shape_point(p,face['group']),uv) for p,uv in part]
            for fragment,poly in enumerate(quads(shaped)):
                mesh.append({**face,'name':face['name']+' bend %d-%d'%(band,fragment),
                             'vertices':[p for p,uv in poly],'uv':[uv for p,uv in poly]})
    names=[side+'_'+part for side in ('primary','secondary') for part in ('base','console','marquee')]
    parts={name:[] for name in names}
    for face in mesh:
        poly=list(zip(face['vertices'],face['uv']))
        for colpiece in pieces(poly,0,[16]):
            for vertical in pieces(colpiece,1,[16,32]):
                for fragment in quads(vertical):
                    center=[sum(v[0][k] for v in fragment)/len(fragment) for k in range(3)]
                    col=0 if center[0]<16 else 1
                    row=min(2,max(0,int(center[1]//16)))
                    parts[names[col*3+row]].append({**face,'vertices':[v for v,uv in fragment],
                                                  'uv':[uv for v,uv in fragment]})

    def wrapper(obj):
        return {'parent':'minecraft:block/block','loader':'neoforge:obj',
                'model':'japanesearcades:models/'+obj,'automatic_culling':False,
                'shade_quads':True,'flip_v':True,'emissive_ambient':True,
                'ambientocclusion':True,'render_type':'minecraft:cutout_mipped_all',
                'textures':textures}

    optimized={}
    for i,(name,faces) in enumerate(parts.items()):
        col,row=i//3,i%3
        optimized[name]=write_obj(block/('maimai_'+name+'.obj'),faces,
                  lambda v,col=col,row=row: [(v[0]-16*col)/16,(v[1]-16*row)/16,v[2]/16])
        write_json(block/('maimai_'+name+'.json'),wrapper('block/maimai_'+name+'.obj'))
    materials=[]
    for texture,lit in sorted({(m['texture'][1:],m['glow']) for m in mesh}):
        materials.extend(['newmtl '+texture+('_lit' if lit else '_surface'),
                          'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1',
                          'map_Kd #'+texture,''])
    (block/'maimai.mtl').write_text('\n'.join(materials),encoding='utf-8')
    variants={}
    for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
        for side in ('primary','secondary'):
            for part in ('base','console','marquee'):
                variant={'model':'japanesearcades:block/maimai_'+side+'_'+part}
                if rotation:variant['y']=rotation
                variants['facing='+facing+',part='+part+',side='+side]=variant
    write_json(assets/'blockstates/maimai.json',{'variants':variants})
    optimized['item']=write_obj(assets/'models/item/maimai.obj',mesh,
              lambda v:[((v[0]-16)*.33+8)/16,v[1]*.33/16,((v[2]-1)*.33+8)/16])
    item=wrapper('item/maimai.obj');item.update({'ambientocclusion':False,'gui_light':'front',
        'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                   'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                   'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                   'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                   'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
    write_json(assets/'models/item/maimai.json',item)

    specs=[(key,assets/'textures/block'/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indexes={'#'+key:i for i,(key,path) in enumerate(specs)}
    sizes=[Image.open(path).size for key,path in specs]
    bb=[];groups=defaultdict(list)
    for face in mesh:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'maimai/surface/'+face['name']))
        index=indexes[face['texture']];w,h=sizes[index]
        keys=['v'+str(i) for i in range(len(face['vertices']))]
        bb.append({'name':face['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],
                   'rotation':[0,0,0],'vertices':dict(zip(keys,face['vertices'])),
                   'faces':{'face':{'vertices':keys,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,face['uv'])},
                                    'texture':index}},'visibility':True,'export':True})
        groups[face['group']].append(uid)
    bbtextures=[]
    for i,(identifier,path) in enumerate(specs):
        w,h=sizes[i]
        bbtextures.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
                           'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'maimai/'+identifier)),
                           'width':w,'height':h,'uv_width':w,'uv_height':h,
                           'relative_path':'../../src/main/resources/assets/japanesearcades/textures/block/'+path.name,
                           'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                           'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(art/'maimai.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'maimai DX','model_identifier':'maimai','visible_box':[3,4,1.5],
        'resolution':{'width':256,'height':256},'elements':bb,'textures':bbtextures,
        'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'maimai/group/'+name)),
                     'origin':[16,0,8],'children':children} for name,children in groups.items()]})
    statistics['smooth_profile_faces']=len(mesh)
    statistics['runtime_section_faces']={name:len(faces) for name,faces in parts.items()}
    statistics['optimized_native']=optimized
    statistics['shared_bend_levels']=list(BEND_LEVELS)
    statistics['closed_button_layer_faces']=len(raw_meshes)
    write_json(art/'geometry.json',{'textures':textures,'meshes':mesh,'surface_optimization':statistics})
    print('Exported',len(mesh),'smooth faces; runtime sections:',statistics['runtime_section_faces'])
    print('Optimized runtime faces:',{key:value['output_faces'] for key,value in optimized.items()})
