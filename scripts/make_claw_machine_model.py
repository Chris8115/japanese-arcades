"""Native eighteen-cell claw cabinet and editable preview source.

The cabinet is48x48x32 model units. Every static cuboid is clipped into its own
16-unit block cell, with continuous face UVs. The live claw and stock are drawn
by ClawMachineRenderer; the preview includes a separately marked parked rig.
"""
from __future__ import annotations
import base64
import copy
import json
import math
import uuid
from collections import defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/claw_machine'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
for path in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates',ASSETS/'textures/entity'):
    path.mkdir(parents=True,exist_ok=True)
COLORS={'white':'#eff2f3','shade':'#d4dde1','silver':'#aab9c2','black':'#152331',
        'pink':'#efa0c8','hotpink':'#db458f','cyan':'#47e7f5','dark':'#3a4c5b',
        'blue':'#238bbc','paper':'#ffffff','rubber':'#222b32','softcyan':'#b9f8ff',
        'yellow':'#f7d851','green':'#88dda1','red':'#f0678b','glass':'#d9faff'}
KEYS=list(COLORS)
atlas=Image.new('RGBA',(256,256));draw=ImageDraw.Draw(atlas)
for i,(name,color) in enumerate(COLORS.items()):
    x,y=(i%4)*64,(i//4)*64
    draw.rectangle((x,y,x+63,y+63),fill=color)
atlas.save(TEX/'claw_machine_materials.png')
Image.new('RGBA',(16,16),'white').save(ASSETS/'textures/entity/claw_machine.png')

font=lambda size:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size)
sign=Image.new('RGB',(1536,160),'#f9fcfd');d=ImageDraw.Draw(sign)
for x in range(-80,1580,180):
    d.polygon([(x,0),(x+115,0),(x+35,160),(x-80,160)],fill='#dcfaff')
d.line((0,13,1535,13),fill='#ef8fbf',width=12)
d.line((0,149,1535,149),fill='#acbdc7',width=5)
d.text((768,85),'CLAW TRIPLE',font=font(95),anchor='mm',fill='#d6378b',stroke_width=3,stroke_fill='white')
sign.save(TEX/'claw_machine_sign.png')
label=Image.new('RGB',(512,160),'#f4c0de');d=ImageDraw.Draw(label)
d.rectangle((9,9,502,150),outline='white',width=4)
d.text((256,80),'PRIZE OUT',font=font(57),anchor='mm',fill='white')
label.save(TEX/'claw_machine_prize_out.png')
controls=Image.new('RGB',(512,128),'#102d3e');d=ImageDraw.Draw(controls)
d.rectangle((8,8,503,119),outline='#67e8f3',width=3)
d.text((256,40),'MOVE  •  DROP  •  WIN',font=font(26),anchor='mm',fill='white')
d.text((256,87),'PRESS TO PLAY',font=font(29),anchor='mm',fill='#f8c6e0')
controls.save(TEX/'claw_machine_controls.png')
glass=Image.new('RGBA',(512,512),(0,0,0,0));d=ImageDraw.Draw(glass)
# Sparse real edge catches preserve clear views of the fifteen live prizes.
d.line((5,18,5,492),fill=(191,239,250,170),width=2)
d.line((506,18,506,492),fill=(229,251,255,140),width=2)
d.line((18,6,490,6),fill=(205,247,255,140),width=2)
d.line((24,108,53,73),fill=(237,252,255,140),width=2)
d.line((32,131,77,76),fill=(237,252,255,140),width=2)
glass.save(TEX/'claw_machine_glass.png')
textures={key:'japanesearcades:block/claw_machine_'+key for key in ('materials','sign','prize_out','controls','glass')}
textures['particle']=textures['materials']

def uv(name):
    i=KEYS.index(name)
    return [(i%4)*4+.125,(i//4)*4+.125,(i%4+1)*4-.125,(i//4+1)*4-.125]

elements=[]
def box(name,lo,hi,material='white',*,group='Cabinet',glow=False,faces=None,**printed):
    face={side:{'texture':'#materials','uv':uv(material)} for side in ('north','south','east','west','up','down')}
    for side,(key,coords) in printed.items():face[side]={'texture':'#'+key,'uv':coords}
    if faces is not None:face={key:value for key,value in face.items() if key in faces}
    if glow:
        for side,data in face.items():
            if glow is True or side in glow:data['neoforge_data']={'block_light':15,'sky_light':15,'ambient_occlusion':False}
    elements.append({'name':name,'from':list(lo),'to':list(hi),'faces':face,'_group':group})

# Base stands off the floor on four broad adjustable feet.
for x in (2,44):
    for z in (3,27):
        box('Rubber foot '+str((x,z)),(x,0,z),(x+2,.65,z+2),'rubber',group='Feet and pedestal')
        box('Chrome foot '+str((x,z)),(x+.4,.45,z+.4),(x+1.6,1.7,z+1.6),'silver',group='Feet and pedestal')
box('Inset bottom plinth',(1.3,1.05,1.3),(46.7,2.2,30.7),'shade',group='Feet and pedestal')
box('White lower pedestal',(.65,2.1,1.65),(47.35,17.55,30.65),'white',faces=('east','west','south','down'),group='Feet and pedestal')
box('Front lower sill',(.65,2.1,.6),(47.35,4,1.85),'white',group='Front service and chute')
box('Front upper fascia',(.65,11.5,.6),(47.35,17.55,1.85),'white',group='Front service and chute')
box('Prize port left wall',(.65,4,.6),(3,11.5,1.85),'white',group='Front service and chute')
box('Service and control front wall',(13,4,.6),(47.35,11.5,1.85),'white',group='Front service and chute')
# The delivery shaft is a real enclosed cavity, open only toward the player
# and through the prize-floor aperture. Its interior faces must remain visible
# from oblique angles instead of exposing the hollow pedestal behind them.
box('Dark chute recess',(3,4,6.05),(13,17.55,6.4),'dark',group='Front service and chute')
box('Chute bottom return',(3,3.9,.65),(13,4.25,6.4),'shade',group='Front service and chute')
# Start behind the existing 1.85-deep front jambs, rather than duplicating
# their inward side faces (which would shimmer from either oblique view).
box('Chute interior left wall',(2.75,4,1.85),(3,17.55,6.4),'shade',group='Front service and chute')
box('Chute interior right wall',(13,4,1.85),(13.25,17.55,6.4),'shade',group='Front service and chute')
# Four ceiling strips enclose the X4..12/Z1.8..4.6 top opening. The rear
# collar separates it from the nearest prize pad without moving that prize.
box('Chute ceiling left',(3,17.25,.68),(4,17.45,6.4),'shade',group='Front service and chute')
box('Chute ceiling right',(12,17.25,.68),(13,17.45,6.4),'shade',group='Front service and chute')
box('Chute ceiling front',(4,17.25,.68),(12,17.45,1.8),'shade',group='Front service and chute')
box('Chute ceiling rear',(4,17.25,4.6),(12,17.45,6.4),'shade',group='Front service and chute')
for x in (2.55,13):box('Prize door pink side '+str(x),(x,3.6,.42),(x+.45,11.95,.66),'pink',group='Front service and chute')
box('Prize door pink top',(2.55,11.5,.42),(13.45,12.1,.66),'pink',group='Front service and chute')
box('Prize out printed flap',(3.1,4.0,.36),(12.9,6.1,.53),'pink',north=('prize_out',[0,0,16,16]),group='Front service and chute')
box('Service door seam',(29.2,3.25,.53),(43.8,13.35,.68),'shade',group='Front service and chute')
box('Service door face',(29.45,3.50,.48),(43.55,13.1,.57),'white',group='Front service and chute')
box('Coin slot metal bezel',(33.1,11.7,.31),(34.5,13.1,.51),'silver',group='Front service and chute')
box('Coin slot',(33.72,11.92,.26),(33.92,12.85,.33),'black',group='Front service and chute')
box('Service lock',(41.0,8.1,.29),(41.8,8.9,.52),'silver',group='Front service and chute')
box('Service lock slot',(41.36,8.23,.25),(41.46,8.77,.3),'black',group='Front service and chute')
for i in range(9):box('Speaker slit %d'%i,(24.0,6.25+i*.32,.47),(27.4,6.38+i*.32,.59),'shade',group='Front service and chute')
for side,x0,x1 in (('left',.50,.68),('right',47.32,47.50)):
    box(side+' side pink sash',(x0,15.6,2),(x1,16.5,30.3),'pink',group='Side trim')
    for z in (5,25):box(side+' side cover screw '+str(z),(x0,5.5,z),(x1,5.8,z+.3),'silver',group='Side trim')

# The live prize field has a separate true delivery hole at the front-left.
# Cover the full pedestal rim. A .02-unit cap overhang prevents coplanar side
# faces at the shell/posts, while staying within the original outer trim bounds.
# The lower pedestal intentionally has no solid top across the chute opening.
box('Prize floor rear',(.63,17.45,4.6),(47.37,18,30.67),'paper',group='Glass display floor')
box('Prize floor front left',(.63,17.45,1.8),(4,18,4.6),'paper',group='Glass display floor')
box('Prize floor front right',(12,17.45,1.8),(47.37,18,4.6),'paper',group='Glass display floor')
# The U-shaped rim ends behind the pink belt and ahead of the front stock row.
# Side bars meet the rear bar edge-to-edge, avoiding overlapping top faces.
for x in (4,11.75):box('Chute aperture side '+str(x),(x,17.8,2.3),(x+.25,18.13,4.4),'silver',group='Glass display floor')
box('Chute aperture back',(4,17.8,4.4),(12,18.13,4.6),'silver',group='Glass display floor')
GRID_COLUMNS=5
for row in range(3):
    for col in range(GRID_COLUMNS):
        x,z=8+32*col/(GRID_COLUMNS-1),24-8*row
        box('Stock pad rim %d'%(row*GRID_COLUMNS+col),(x-3.2,18.0,z-3.1),(x+3.2,18.12,z+3.1),'softcyan',group='Fifteen prize positions')
        box('Stock pad %d'%(row*GRID_COLUMNS+col),(x-2.95,18.115,z-2.85),(x+2.95,18.18,z+2.85),'paper',group='Fifteen prize positions')

# Thin structural posts carry cyan lighting without opaque glass walls.
for x in (.65,46.1):
    for z in (1.15,29.4):
        box('Corner white upright '+str((x,z)),(x,17.4,z),(x+1.25,44.1,z+1.4),'white',group='Glass enclosure')
        box('Corner cyan light '+str((x,z)),(x+.36,18.4,z-.13),(x+.9,43.25,z+.03),'cyan',glow=('north',),group='Glass enclosure')
        box('Corner silver side '+str((x,z)),(x+.1,18.4,z+.12),(x+.24,43.3,z+1.15),'silver',group='Glass enclosure')
box('Front clear glass',(1.95,18.25,1.13),(46.05,43.2,1.15),'glass',faces=('north','south'),north=('glass',[0,0,16,16]),south=('glass',[0,0,16,16]),group='Glass panes')
for x in (1.48,46.50):
    box('Side clear glass '+str(x),(x,18.25,2.6),(x+.02,43.2,29.35),'glass',faces=('east','west'),east=('glass',[0,0,16,16]),west=('glass',[0,0,16,16]),group='Glass panes')
box('Rear clear glass',(1.95,18.25,30.24),(46.05,43.2,30.26),'glass',faces=('north','south'),north=('glass',[0,0,16,16]),south=('glass',[0,0,16,16]),group='Glass panes')
for y in (18.1,26.3,34.5,42.7):box('Rear glass support rail '+str(y),(1.9,y,29.6),(46.1,y+.18,29.88),'shade',group='Glass enclosure')
for x in (16,32):box('Rear glass slim mullion '+str(x),(x-.09,18.1,29.58),(x+.09,43,29.82),'shade',group='Glass enclosure')
box('Lower front pink belt',(.6,17.35,.7),(47.4,18.05,2.2),'pink',group='Glass enclosure')

# A broad compact marquee, layered cyan cap and white/pink manufactured frame.
box('Upper white canopy',(.6,43.2,1.0),(47.4,47.0,30.9),'white',group='Marquee canopy')
box('Upper pink sash',(.58,46.18,.94),(47.42,46.88,30.96),'pink',group='Marquee canopy')
box('Raised white crown',(1.2,46.9,1.55),(46.8,47.45,30.45),'paper',group='Marquee canopy')
box('Cyan canopy crown',(1.7,47.4,2.05),(46.3,47.98,29.95),'cyan',glow=True,group='Marquee canopy')
box('Front cyan roof lip',(.5,47.05,.8),(47.5,47.65,1.18),'cyan',glow=True,group='Marquee canopy')
box('Claw Triple front marquee',(2.0,43.65,.85),(46.0,46.10,1.04),'white',north=('sign',[0,0,16,16]),glow=('north',),group='Marquee canopy')
for x in (.48,47.38):box('Side marquee '+str(x),(x,43.75,3),(x+.14,45.95,28.4),'white',east=('sign',[0,0,16,16]),west=('sign',[0,0,16,16]),group='Marquee canopy')
for z in (5.0,27.0):box('Fixed ceiling running rail '+str(z),(3,41.4,z),(45,41.85,z+.5),'silver',group='Static gantry rails')
for x in (3,44.5):box('Fixed gantry length rail '+str(x),(x,41.7,3),(x+.5,42.15,29),'dark',group='Static gantry rails')

# A centered operator deck clears the reflected front-left chute completely.
# Its white cap rises above the belt, so the screen bezel has its own surface
# rather than sharing the belt's Y18.05 top plane.
box('Control deck support',(12.5,14.8,.1),(33.5,17.5,4.4),'shade',group='Player controls')
box('Control deck white cap',(12.2,17.45,0),(33.8,18.10,4.65),'white',group='Player controls')
box('Control screen bezel',(23.2,18.08,.65),(32.2,18.30,3.8),'black',group='Player controls')
box('Control screen',(23.5,18.305,.88),(31.9,18.325,3.57),'blue',up=('controls',[16,16,0,0]),glow=('up',),group='Player controls')
box('Joystick chrome stem',(16.45,18.10,1.8),(16.85,19.40,2.2),'silver',group='Player controls')
box('Joystick cyan handle',(15.95,19.10,1.3),(17.35,19.95,2.7),'cyan',group='Player controls')
box('Drop button silver socket',(19.3,18.10,1.3),(21.2,18.29,3.0),'silver',group='Player controls')
box('Drop pink button',(19.55,18.28,1.55),(20.95,18.63,2.75),'hotpink',group='Player controls')

# The viewer stands north looking south: high model X is the viewer's left.
# Reflect the authored service/chute assembly, while retaining readable labels.
for e in elements:
    if e['_group'] in ('Front service and chute','Glass display floor'):
        e['from'][0],e['to'][0]=48-e['to'][0],48-e['from'][0]
for e in elements:
    if e['_group']=='Fifteen prize positions':
        e['from'][0],e['to'][0]=48-e['to'][0],48-e['from'][0]

# This parked rig is editable in Blockbench and present in the item preview only.
# World models exclude it; the BER draws the moving counterpart from live poses.
static_elements=elements
elements=[]
box('Parked moving cross rail',(3,41.8,2.68),(45,42.25,3.32),'silver',group='Parked dynamic rig preview')
box('Parked trolley',(38.0,40.6,1.75),(42.0,42.65,4.25),'dark',group='Parked dynamic rig preview')
box('Parked trolley cyan face',(38.3,40.85,1.65),(41.7,41.8,1.77),'cyan',glow=True,group='Parked dynamic rig preview')
box('Parked cable',(39.90,39.95,2.9),(40.1,41.4,3.1),'rubber',group='Parked dynamic rig preview')
box('Parked claw palm',(38.55,38.5,1.55),(41.45,40.0,4.45),'silver',group='Parked dynamic rig preview')
box('Parked claw pink stripe',(38.5,39.1,1.5),(41.5,39.45,4.5),'pink',group='Parked dynamic rig preview')
for label,x,z in (('left',37.65,3),('right',42.35,3),('rear',40,5.35)):
    box('Parked '+label+' finger',(x-.2,35.0,z-.2),(x+.2,38.7,z+.2),'silver',group='Parked dynamic rig preview')
    box('Parked '+label+' finger grip',(x-.35,34.9,z-.35),(x+.35,35.45,z+.35),'rubber',group='Parked dynamic rig preview')
preview_elements=elements
elements=static_elements

# Actual parked BER finger segments, retained as editable mesh faces in the
# source/Blender scene. The tiny inventory icon uses simpler native cuboids.
preview_meshes=[]
def rod_mesh(name,a,b,radius,color):
    direction=[b[i]-a[i] for i in range(3)]
    length=math.sqrt(sum(v*v for v in direction));direction=[v/length for v in direction]
    tangent=[direction[2],0,-direction[0]]
    tlength=math.sqrt(sum(v*v for v in tangent));tangent=[v/tlength for v in tangent]
    bitangent=[direction[1]*tangent[2]-direction[2]*tangent[1],direction[2]*tangent[0]-direction[0]*tangent[2],direction[0]*tangent[1]-direction[1]*tangent[0]]
    verts=[]
    for end in (a,b):
        for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
            verts.append([end[i]+radius*(u*tangent[i]+v*bitangent[i]) for i in range(3)])
    coords=uv(color);uvs=[[coords[0],coords[1]],[coords[0],coords[3]],[coords[2],coords[3]],[coords[2],coords[1]]]
    for index,face in enumerate(((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))):
        preview_meshes.append({'name':name+' face '+str(index),'vertices':[verts[j] for j in face],
                               'texture':'#materials','uv':uvs,'glow':False})
for finger in range(3):
    angle=math.radians(90+120*finger);dx,dz=math.cos(angle),math.sin(angle)
    p=lambda radius,y:[40+dx*radius,36.5+y,3+dz*radius]
    rod_mesh('Parked articulated finger %d upper'%finger,p(.95,2.1),p(3.1,.45),.19,'silver')
    rod_mesh('Parked articulated finger %d lower'%finger,p(3.1,.45),p(2.9,-1.3),.19,'silver')
    rod_mesh('Parked articulated finger %d grip'%finger,p(2.9,-1.3),p(2.45,-1.45),.25,'rubber')
scene_preview_elements=[e for e in preview_elements if 'finger' not in e['name']]

def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def clipped_uv(face,side,oldlo,oldhi,lo,hi):
    # Vanilla face U/V directions, preserving printed art across cell splits.
    axes={'north':(0,True,1,True),'south':(0,False,1,True),
          'east':(2,True,1,True),'west':(2,False,1,True),
          'up':(0,False,2,False),'down':(0,False,2,True)}
    uaxis,ureverse,vaxis,vreverse=axes[side]
    result=[]
    for axis,reverse,a,b in ((uaxis,ureverse,face['uv'][0],face['uv'][2]),(vaxis,vreverse,face['uv'][1],face['uv'][3])):
        extent=oldhi[axis]-oldlo[axis]
        t0,t1=(lo[axis]-oldlo[axis])/extent,(hi[axis]-oldlo[axis])/extent
        if reverse:t0,t1=1-t1,1-t0
        result.append((a+(b-a)*t0,a+(b-a)*t1))
    return [result[0][0],result[1][0],result[0][1],result[1][1]]

parts={i:[] for i in range(18)}
for source in elements:
    a,b=source['from'],source['to']
    for y in range(3):
        for z in range(2):
            for x in range(3):
                origin=[16*x,16*y,16*z]
                lo=[max(a[i],origin[i]) for i in range(3)];hi=[min(b[i],origin[i]+16) for i in range(3)]
                if any(hi[i]<=lo[i]+1e-8 for i in range(3)):continue
                e={k:copy.deepcopy(v) for k,v in source.items() if not k.startswith('_')}
                e['from']=[lo[i]-origin[i] for i in range(3)];e['to']=[hi[i]-origin[i] for i in range(3)]
                for side,face in e['faces'].items():face['uv']=clipped_uv(source['faces'][side],side,a,b,lo,hi)
                parts[x+3*z+6*y].append(e)
for part,values in parts.items():
    write_json(ASSETS/'models/block'/('claw_machine_'+str(part)+'.json'),{'parent':'minecraft:block/block','render_type':'minecraft:cutout','textures':textures,'elements':values})
write_json(ASSETS/'blockstates/claw_machine.json',{'variants':{
    'facing='+facing+',part='+str(part):{'model':'japanesearcades:block/claw_machine_'+str(part),**({'y':angle} if angle else {})}
    for facing,angle in (('north',0),('east',90),('south',180),('west',270)) for part in parts}})
item=[]
for source in elements+preview_elements:
    e={k:copy.deepcopy(v) for k,v in source.items() if not k.startswith('_')}
    for key in ('from','to'):e[key]=[e[key][0]*.30+.8,e[key][1]*.30+.5,e[key][2]*.30+3.2]
    item.append(e)
write_json(ASSETS/'models/item/claw_machine.json',{'gui_light':'front','ambientocclusion':False,'textures':textures,'elements':item,
    'display':{'gui':{'rotation':[15,225,0],'scale':[.86,.86,.86]},'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
               'fixed':{'rotation':[0,180,0],'scale':[.9,.9,.9]},'thirdperson_righthand':{'rotation':[75,45,0],'scale':[.45,.45,.45]}}})

metadata={'dimensions':[48,48,32],'part_formula':'x+3*z+6*y','grid':[{'slot':r*GRID_COLUMNS+c,'center':[40-32*c/(GRID_COLUMNS-1),20.5,24-8*r]}for r in range(3)for c in range(GRID_COLUMNS)],
          'claw':{'grip_parked_y':36.5,'grip_lowered_y':20.5,'x_origin':8,'x_span':32,'z_origin':8,'z_span':16,'chute':[40,8,3]},
          'static_elements':len(elements),'part_elements':{str(k):len(v) for k,v in parts.items()}}
write_json(ART/'geometry.json',{'textures':textures,'elements':elements,'preview_elements':scene_preview_elements,'preview_meshes':preview_meshes,'metadata':metadata})
specs=[(key,TEX/(value.split('/')[-1]+'.png'))for key,value in textures.items()if key!='particle']
indices={'#'+key:i for i,(key,path)in enumerate(specs)}
sizes=[Image.open(path).size for key,path in specs]
bb=[];groups=defaultdict(list)
for e in elements+scene_preview_elements:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'claw-machine/'+e['name']))
    faces={}
    for side,f in e['faces'].items():
        idx=indices[f['texture']];w,h=sizes[idx]
        faces[side]={'texture':idx,'uv':[value*(w if j%2==0 else h)/16 for j,value in enumerate(f['uv'])]}
    bb.append({'name':e['name'],'type':'cube','uuid':uid,'from':e['from'],'to':e['to'],'origin':[0,0,0],'rotation':[0,0,0],
               'faces':faces,'box_uv':False,'visibility':True,'export':True})
    groups[e['_group']].append(uid)
for face in preview_meshes:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'claw-machine/'+face['name']))
    idx=indices[face['texture']];w,h=sizes[idx];keys=['v'+str(i) for i in range(4)]
    bb.append({'name':face['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
               'vertices':dict(zip(keys,face['vertices'])),
               'faces':{'face':{'vertices':keys,'texture':idx,'uv':{key:[u*w/16,v*h/16] for key,(u,v) in zip(keys,face['uv'])}}},
               'visibility':True,'export':False})
    groups['Parked dynamic rig preview'].append(uid)
bbtextures=[]
for i,(key,path)in enumerate(specs):
    w,h=sizes[i]
    bbtextures.append({'name':path.name,'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'claw-machine/'+key)),
                       'width':w,'height':h,'uv_width':w,'uv_height':h,'mode':'bitmap','particle':i==0,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()})
write_json(ART/'claw-machine.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'Claw Triple Machine','model_identifier':'claw_machine','resolution':{'width':256,'height':256},'elements':bb,'textures':bbtextures,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'claw-machine/group/'+name)),'origin':[24,0,16],'children':children}for name,children in groups.items()]})
assert len(set(e['name']for e in elements))==len(elements)
assert all(all(0<=v<=16 for key in ('from','to')for v in e[key])for part in parts.values()for e in part)
print('Claw cabinet exported:',metadata)
