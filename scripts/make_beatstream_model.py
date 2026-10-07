"""Export the actual BeatStream cabinet, independently of the original Nostalgia.

Source screen and topper pixels/alpha are copied into padded texture canvases;
the source illustrations are immutable and are never repainted or resampled.
"""
from __future__ import annotations
import base64
import copy
import json
import math
import uuid
from pathlib import Path
from PIL import Image

from beatstream_cabinet_geometry import build_cabinet
from beatstream_console_geometry import build_console, build_marquee
from beatstream_surface_art import PALETTE, build_surface_art
from beatstream_speaker_geometry import build_speakers, build_separator

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
ART=ROOT/'art/beatstream'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
for directory in (ART,TEXTURES,MODEL): directory.mkdir(parents=True,exist_ok=True)

def pack_source(filename,key):
    source=ART/filename
    if not source.exists(): raise SystemExit('Missing original BeatStream artwork: '+str(source))
    im=Image.open(source)
    mode='RGBA' if 'A' in im.getbands() else 'RGB'
    size=tuple(1<<(n-1).bit_length() for n in im.size)
    packed=Image.new(mode,size,(0,0,0,0) if mode=='RGBA' else (12,15,20))
    packed.paste(im,(0,0))
    packed.save(TEXTURES/('beatstream_'+key+'.png'))
    return im,tuple(n/p for n,p in zip(im.size,size))

screens_source,screen_scale=pack_source('screens-source.png','screens')
assert screens_source.width==screens_source.height*2,'Screens are two equal side-by-side panels'
topper_source,topper_scale=pack_source('topper-source.png','topper')
assert 'A' in topper_source.getbands() and topper_source.getextrema()[3][0]==0,'Topper needs source transparency'
build_surface_art(TEXTURES)
KEYS=list(PALETTE)

def uv(name):
    i=KEYS.index(name)
    return [(i%4)*4,(i//4)*4,(i%4+1)*4,(i//4+1)*4]

elements=[]

def cube(name,start,end,material='black',*,north=None,east=None,west=None,south=None,up=None,down=None,rotation=None,glow=False,group='Cabinet'):
    faces={direction:{'uv':uv(material),'texture':'#materials'} for direction in ('north','east','south','west','up','down')}
    for direction,override in (('north',north),('east',east),('west',west),('south',south),('up',up),('down',down)):
        if override:
            texture,coords=override
            scale=screen_scale if texture=='screens' else topper_scale if texture=='topper' else (1,1)
            faces[direction]={'uv':[v*scale[i%2] for i,v in enumerate(coords)],'texture':'#'+texture}
    element={'name':name,'from':list(start),'to':list(end),'faces':faces,'_group':group}
    if rotation:
        axis,angle,origin=rotation
        element['rotation']={'axis':axis,'angle':angle,'origin':list(origin),'rescale':False}
    if glow:
        if glow is True: element['shade']=False
        for direction,face in faces.items():
            if glow is True or direction in glow:
                face['neoforge_data']={'block_light':15,'sky_light':15,'ambient_occlusion':False}
    assert all(a<b for a,b in zip(start,end)),name
    elements.append(element)

def cutout_sprite(name,start,end,material,*,group='Diecut topper'):
    """Extrude source-alpha silhouette; select direct pixels for each front UV."""
    alpha=topper_source.getchannel('A')
    bounds=alpha.point(lambda value:255 if value>=128 else 0).getbbox()
    assert bounds,'Empty source topper'
    px0,py0,px1,py1=bounds
    # A finer64-column silhouette retains ears/hair/corners without imposing a
    # rectangular printed slab; greedy rectangles keep the native mesh compact.
    cols=64;rows=32
    mask=[]
    for row in range(rows):
        active=[]
        for col in range(cols):
            box=(round(px0+(px1-px0)*col/cols),round(py0+(py1-py0)*row/rows),round(px0+(px1-px0)*(col+1)/cols),round(py0+(py1-py0)*(row+1)/rows))
            region=alpha.crop(box)
            # Any significant authored alpha keeps the silhouette coverage; the
            # actual PNG alpha still cuts tiny corners inside the outer cells.
            active.append(sum(region.histogram()[128:])>=region.width*region.height*.18)
        mask.append(active)
    for row in range(rows):
        col=0
        while col<cols:
            if not mask[row][col]: col+=1;continue
            first=col
            while col<cols and mask[row][col]: col+=1
            bottom=row+1
            while bottom<rows and all(mask[bottom][x] for x in range(first,col)): bottom+=1
            for y in range(row,bottom):
                for x in range(first,col): mask[y][x]=False
            x0=start[0]+(end[0]-start[0])*first/cols
            x1=start[0]+(end[0]-start[0])*col/cols
            y0=end[1]-(end[1]-start[1])*bottom/rows
            y1=end[1]-(end[1]-start[1])*row/rows
            tex=[(px0+(px1-px0)*first/cols)/topper_source.width*16,(py0+(py1-py0)*row/rows)/topper_source.height*16,(px0+(px1-px0)*col/cols)/topper_source.width*16,(py0+(py1-py0)*bottom/rows)/topper_source.height*16]
            cube(name+' row%02d col%02d'%(row,first),(x0,y0,start[2]),(x1,y1,end[2]),material,north=('topper',tex),group=group)

build_cabinet(cube,uv)
build_console(cube,uv)
build_marquee(cube,cutout_sprite)
mesh_faces=build_speakers(uv)+build_separator(uv)
texture_paths={key:'japanesearcades:block/beatstream_'+key for key in ('materials','screens','topper','trim','controls','side','triangle','speaker')}
texture_paths['particle']=texture_paths['materials']

# Minecraft's north-facing UVs run from +X to -X when viewed from the front.
# Mirror our front-view coordinates so the ornaments stay on the photographed right.
for e in elements:
    x0,x1=e['from'][0],e['to'][0]
    e['from'][0],e['to'][0]=16-x1,16-x0
    e['faces']['east'],e['faces']['west']=e['faces']['west'],e['faces']['east']
    if 'rotation' in e:
        e['rotation']['origin'][0]=16-e['rotation']['origin'][0]
        if e['rotation']['axis'] in ('y','z'): e['rotation']['angle']*=-1

def strip_element(element):
    return {k:copy.deepcopy(v) for k,v in element.items() if not k.startswith('_')}

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def write_speakers_obj(path,transform):
    lines=['# BeatStream rigid speaker prisms; native block-space units.',
           'mtllib japanesearcades:models/block/beatstream_speakers.mtl']
    index=1
    for face in mesh_faces:
        lines.append('usemtl '+('speaker_lit' if face['glow'] else 'materials_surface'))
        lines.extend('v '+' '.join('%.9f'%v for v in transform(p)) for p in face['vertices'])
        lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in face['uv'])
        lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(face['vertices']))))
        index+=len(face['vertices'])
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def speaker_wrapper(path):
    return {'parent':'minecraft:block/block','loader':'neoforge:obj',
            'model':'japanesearcades:models/'+path,'automatic_culling':False,
            'shade_quads':True,'flip_v':True,'emissive_ambient':True,
            'ambientocclusion':True,'render_type':'minecraft:cutout_mipped_all',
            'textures':texture_paths}

def with_speakers(cabinet,path):
    return {'parent':'minecraft:block/block','loader':'neoforge:composite',
            'ambientocclusion':cabinet.get('ambientocclusion',True),
            'textures':texture_paths,
            'children':{'cabinet':cabinet,'speakers':speaker_wrapper(path)},
            'item_render_order':['cabinet','speakers']}

write_speakers_obj(MODEL/'beatstream_speakers.obj',lambda p:[p[0]/16,(p[1]-16)/16,p[2]/16])
write_speakers_obj(ASSETS/'models/item/beatstream_speakers.obj',lambda p:[(p[0]*.35+5.2)/16,p[1]*.35/16,(p[2]*.35+5.2)/16])
(MODEL/'beatstream_speakers.mtl').write_text(
    'newmtl materials_surface\nKa 0 0 0\nKd 1 1 1\nmap_Kd #materials\n\n'
    'newmtl speaker_lit\nKa 1 1 1\nKd 1 1 1\nmap_Kd #speaker\n',encoding='utf-8')

part_names = ['base','console','marquee']
parts = {part:[] for part in part_names}
for source in elements:
    e=strip_element(source)
    center=(e['from'][1]+e['to'][1])/2
    index=min(2,max(0,int(center//16)))
    for key in ('from','to'): e[key][1]=round(e[key][1]-index*16,5)
    if 'rotation' in e: e['rotation']['origin'][1]-=index*16
    for coords in (e['from'],e['to']):
        assert all(-16 <= v <= 32 for v in coords), (e['name'],coords)
    parts[part_names[index]].append(e)
for part in part_names:
    model={'parent':'minecraft:block/block','ambientocclusion':True,'render_type':'minecraft:cutout',
           'textures':texture_paths,'elements':parts[part]}
    if part=='console': model=with_speakers(model,'block/beatstream_speakers.obj')
    write_json(MODEL / ('beatstream_'+part+'.json'),model)
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'japanesearcades:block/beatstream_'+part}
        if rotation: variant['y']=rotation
        variants['facing='+facing+',part='+part]=variant
write_json(ASSETS / 'blockstates/beatstream.json', {'variants':variants})

# An explicitly scaled complete model for inventory rendering (vanilla element bounds).
item_elements=[]
for source in elements:
    e=strip_element(source)
    for key in ('from','to'):
        e[key]=[round(e[key][0]*0.35+5.2,5),round(e[key][1]*0.35,5),round(e[key][2]*0.35+5.2,5)]
    if 'rotation' in e:
        o=e['rotation']['origin'];e['rotation']['origin']=[o[0]*.35+5.2,o[1]*.35,o[2]*.35+5.2]
    item_elements.append(e)
write_json(ASSETS / 'models/item/beatstream.json',
           {'ambientocclusion':False,'gui_light':'front','textures':texture_paths,'elements':item_elements,
            'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                       'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                       'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                       'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                       'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})

# Both children use the same already-scaled coordinates. Keep held/GUI display
# transforms only on the composite so the meshes cannot drift from the shell.
item_path=ASSETS/'models/item/beatstream.json'
native_item=json.loads(item_path.read_text())
item_display=native_item.pop('display')
native_item['render_type']='minecraft:cutout'
item_model=with_speakers(native_item,'item/beatstream_speakers.obj')
item_model.update({'display':item_display,'gui_light':'front','ambientocclusion':False})
write_json(item_path,item_model)

# Blockbench's free format preserves the complete cabinet and named groups.
texture_specs = [(key,TEXTURES/(value.split('/')[-1]+'.png')) for key,value in texture_paths.items() if key!='particle']
texture_indices = {'#'+key:i for i,(key,path) in enumerate(texture_specs)}
texture_sizes = [Image.open(path).size for key,path in texture_specs]
bb_elements=[]
groups={}
for source in elements:
    e=strip_element(source)
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'japanesearcades/beatstream/'+e['name']+'/'+str(e['from'])))
    rot=e.get('rotation')
    rotation=[0,0,0]
    origin=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
    if rot:
        rotation['xyz'.index(rot['axis'])]=rot['angle'];origin=rot['origin']
    bbfaces={}
    for direction,face in e['faces'].items():
        index=texture_indices[face['texture']]
        width,height=texture_sizes[index]
        bbfaces[direction]={'uv':[v*(width if i%2==0 else height)/16 for i,v in enumerate(face['uv'])], 'texture':index}
    bb_elements.append({'name':e['name'],'type':'cube','uuid':uid,'from':e['from'],'to':e['to'],
                        'origin':origin,'rotation':rotation,'faces':bbfaces,'box_uv':False,
                        'color':1,'rescale':False,'autouv':0,'visibility':True,'export':True,
                        'shade':e.get('shade',True)})
    groups.setdefault(source['_group'],[]).append(uid)
for face in mesh_faces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'beatstream/'+face['name']))
    index=texture_indices[face['texture']]
    width,height=texture_sizes[index]
    keys=['v'+str(i) for i in range(len(face['vertices']))]
    bb_elements.append({'name':face['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
                        'vertices':dict(zip(keys,face['vertices'])),
                        'faces':{'face':{'vertices':keys,'texture':index,
                                         'uv':{key:[u*width/16,v*height/16] for key,(u,v) in zip(keys,face['uv'])}}},
                        'visibility':True,'export':True})
    groups.setdefault(face['group'],[]).append(uid)
bbtextures=[]
for i,(identifier,path) in enumerate(texture_specs):
    texture=Image.open(path)
    bbtextures.append({'path':str(path),'name':path.name,'folder':'block','namespace':'japanesearcades',
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'beatstream/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/japanesearcades/textures/block/'+path.name,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                       'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'beatstream.bbmodel',
           {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
            'name':'BeatStream','model_identifier':'beatstream','visible_box':[2,4,1.5],
            'resolution':{'width':256,'height':256},'elements':bb_elements,'textures':bbtextures,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'beatstream/group/'+name)),
                         'origin':[8,0,8],'children':children} for name,children in groups.items()]})
write_json(ART/'geometry.json', {'textures':texture_paths,'elements':elements,'meshes':mesh_faces})
print('Generated',len(elements),'cuboids; section counts:',{name:len(values) for name,values in parts.items()})
print('Rigid speaker and separator polygons:',len(mesh_faces))
print('Editable model:',ART/'beatstream.bbmodel')
