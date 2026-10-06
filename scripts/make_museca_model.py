"""Build the MUSECA cabinet with native Java cuboids.

Source illustrations are packed unchanged and mapped using their native aspect.
The reclining portrait monitor, five spinners, folded marquee and prism column follow the supplied references.
"""
from __future__ import annotations
import base64
import copy
import json
import math
import uuid
from pathlib import Path
from PIL import Image
from museca_shell_geometry import build_shell
from museca_upper_geometry import build_upper
from museca_textures import build_textures
from wacca_surface_geometry import optimize_surfaces

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/museca'
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
for path in (ART,TEXTURES,MODEL):path.mkdir(parents=True,exist_ok=True)
PALETTE,KEYS=build_textures(TEXTURES)

source_scales={}
for key,source_name,target_name in (
        ('display','display-artwork-source.png','museca_display.png'),
        ('marquee','marquee-artwork-source.png','museca_marquee.png')):
    source=Image.open(ART/source_name).convert('RGBA' if key=='branding' else 'RGB')
    size=tuple(1<<(n-1).bit_length() for n in source.size)
    packed=Image.new(source.mode,size,(0,0,0,0) if key=='branding' else PALETTE['black'])
    packed.paste(source,(0,0))
    packed.save(TEXTURES/target_name)
    source_scales[key]=tuple(n/p for n,p in zip(source.size,size))

def uv(name):
    i=KEYS.index(name)
    # Eight native pixels keep sampling inside this 64px material tile through
    # mip level 4. Exact tile/sprite boundaries can pick up neighboring colours.
    inset=.5
    return [(i%4)*4+inset,(i//4)*4+inset,(i%4)*4+4-inset,(i//4)*4+4-inset]


elements=[]


def cube(name,start,end,material='black',*,north=None,east=None,west=None,south=None,
         up=None,down=None,rotation=None,glow=False,group='Cabinet',faces_only=None):
    assert all(b>a for a,b in zip(start,end)),(name,start,end)
    faces={side:{'uv':uv(material),'texture':'#materials'} for side in ('north','east','south','west','up','down')}
    for direction,override in (('north',north),('east',east),('west',west),('south',south),('up',up),('down',down)):
        if override:
            texture,coordinates=override
            scale=source_scales.get(texture,(1,1))
            faces[direction]={'uv':[v*scale[i%2] for i,v in enumerate(coordinates)],'texture':'#'+texture}
    element={'name':name,'from':list(start),'to':list(end),'faces':faces,'_group':group}
    if rotation:
        axis,angle,origin=rotation
        assert angle in (-45,-22.5,0,22.5,45),(name,angle)
        element['rotation']={'axis':axis,'angle':angle,'origin':list(origin),'rescale':False}
    if glow:
        for side,face in faces.items():
            if glow is True or side in glow:
                face['neoforge_data']={'block_light':15,'sky_light':15,'ambient_occlusion':False}
    if faces_only:
        element['faces']={side:face for side,face in faces.items() if side in faces_only}
    elements.append(element)


def polygon(name,points,z0,z1,material,*,group='Sculpted panels',glow=False,front=None,rotation=None,step=.25):
    minx,maxx=min(x for x,y in points),max(x for x,y in points)
    miny,maxy=min(y for x,y in points),max(y for x,y in points)
    count=max(1,math.ceil((maxy-miny)/step));dy=(maxy-miny)/count
    rows=[];active={}
    for i in range(count):
        y=miny+(i+.5)*dy;cross=[]
        for a,b in zip(points,points[1:]+points[:1]):
            if min(a[1],b[1])<=y<max(a[1],b[1]):
                cross.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
        cross.sort();following={}
        for j in range(0,len(cross)-1,2):
            left=max(minx,round(cross[j]/step)*step)
            right=min(maxx,round(cross[j+1]/step)*step)
            if right<=left:continue
            key=(left,right)
            if key in active:
                rect=active.pop(key);rect[3]=miny+(i+1)*dy
            else:rect=[left,right,miny+i*dy,miny+(i+1)*dy]
            following[key]=rect
        rows.extend(active.values());active=following
    rows.extend(active.values())
    for i,(left,right,bottom,top) in enumerate(rows):
        override=None
        if front:
            tex,(u0,v0,u1,v1)=front
            override=(tex,[u0+(left-minx)/(maxx-minx)*(u1-u0),v0+(maxy-top)/(maxy-miny)*(v1-v0),
                           u0+(right-minx)/(maxx-minx)*(u1-u0),v0+(maxy-bottom)/(maxy-miny)*(v1-v0)])
        cube(name+' segment %02d'%i,(left,bottom,z0),(right,top,z1),material,
             north=override,rotation=rotation,glow=glow,group=group)


build_shell(cube,polygon)
build_upper(cube,polygon,ART)

texture_paths={
    'materials':'funpackcustom:block/museca_materials','details':'funpackcustom:block/museca_details',
    'display':'funpackcustom:block/museca_display',
    'branding':'funpackcustom:block/museca_branding','marquee':'funpackcustom:block/museca_marquee','particle':'funpackcustom:block/museca_materials',
}

# Minecraft's north-facing UVs run from +X to -X when viewed from the front.
# Mirror our front-view coordinates so the ornaments stay on the photographed right.
for e in elements:
    x0,x1=e['from'][0],e['to'][0]
    e['from'][0],e['to'][0]=16-x1,16-x0
    east=e['faces'].pop('east',None)
    west=e['faces'].pop('west',None)
    if east is not None:e['faces']['west']=east
    if west is not None:e['faces']['east']=west
    if 'rotation' in e:
        e['rotation']['origin'][0]=16-e['rotation']['origin'][0]
        if e['rotation']['axis'] in ('y','z'): e['rotation']['angle']*=-1

# Bake only the opaque exterior. Adjacent pieces do not need internal faces;
# clipped overlaps have exactly one surface owner, eliminating coplanar fights.
# Alpha-bearing cutout pieces must not occlude opaque geometry in the union.
alpha_groups=set()
marquee=[e for e in elements if e['_group'] in alpha_groups]
opaque=[e for e in elements if e['_group'] not in alpha_groups]
elements,surface_details=optimize_surfaces(opaque)
elements.extend(marquee)
surface_details['alpha_elements']=len(marquee)
surface_details['total_exported_faces']=sum(len(e['faces']) for e in elements)

def strip_element(element):
    return {k:copy.deepcopy(v) for k,v in element.items() if not k.startswith('_')}

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

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
    write_json(MODEL / ('museca_'+part+'.json'),
               {'parent':'minecraft:block/block','ambientocclusion':True,'render_type':'minecraft:cutout_mipped_all',
                'textures':texture_paths,'elements':parts[part]})
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'funpackcustom:block/museca_'+part}
        if rotation: variant['y']=rotation
        variants['facing='+facing+',part='+part]=variant
write_json(ASSETS / 'blockstates/museca.json', {'variants':variants})

# An explicitly scaled complete model for inventory rendering (vanilla element bounds).
item_elements=[]
for source in elements:
    e=strip_element(source)
    for key in ('from','to'):
        e[key]=[round(e[key][0]*0.35+5.2,5),round(e[key][1]*0.35,5),round(e[key][2]*0.35+5.2,5)]
    if 'rotation' in e:
        o=e['rotation']['origin'];e['rotation']['origin']=[o[0]*.35+5.2,o[1]*.35,o[2]*.35+5.2]
    item_elements.append(e)
write_json(ASSETS / 'models/item/museca.json',
           {'ambientocclusion':False,'gui_light':'front','render_type':'minecraft:cutout_mipped_all','textures':texture_paths,'elements':item_elements,
            'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                       'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                       'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                       'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                       'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})

artwork=TEXTURES / 'museca_display.png'
if not artwork.exists():
    raise SystemExit('Missing original artwork sheet: '+str(artwork))
im=Image.open(artwork)
assert all(n & (n-1) == 0 for n in im.size), 'Artwork must have power-of-two dimensions'

# Blockbench's free format preserves the complete cabinet and named groups.
texture_specs = [(key,TEXTURES/(value.split('/')[-1]+'.png')) for key,value in texture_paths.items() if key!='particle']
texture_indices = {'#'+key:i for i,(key,path) in enumerate(texture_specs)}
texture_sizes = [Image.open(path).size for key,path in texture_specs]
bb_elements=[]
groups={}
for source in elements:
    e=strip_element(source)
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'funpackcustom/museca/'+e['name']+'/'+str(e['from'])))
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
    for direction in ('north','east','south','west','up','down'):
        if direction not in bbfaces:
            bbfaces[direction]={'uv':[0,0,0,0],'texture':None}
    bb_elements.append({'name':e['name'],'type':'cube','uuid':uid,'from':e['from'],'to':e['to'],
                        'origin':origin,'rotation':rotation,'faces':bbfaces,'box_uv':False,
                        'color':1,'rescale':False,'autouv':0,'visibility':True,'export':True,
                        'shade':e.get('shade',True)})
    groups.setdefault(source['_group'],[]).append(uid)
bbtextures=[]
for i,(identifier,path) in enumerate(texture_specs):
    texture=Image.open(path)
    bbtextures.append({'path':str(path),'name':path.name,'folder':'block','namespace':'funpackcustom',
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'museca/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/funpackcustom/textures/block/'+path.name,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                       'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'museca.bbmodel',
           {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
            'name':'MUSECA','model_identifier':'museca','visible_box':[2,4,1.5],
            'resolution':{'width':256,'height':256},'elements':bb_elements,'textures':bbtextures,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'museca/group/'+name)),
                         'origin':[8,0,8],'children':children} for name,children in groups.items()]})
write_json(ART/'geometry.json', {'textures':texture_paths,'elements':elements,'surface_optimization':surface_details})
print('Generated',len(elements),'surface elements; section counts:',{name:len(values) for name,values in parts.items()})
print('Exterior surfaces:',surface_details)
print('Editable model:',ART/'museca.bbmodel')
