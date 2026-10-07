"""Original, reference-inspired two-block arcade ordering kiosk.

Geometry uses model units (16/block), with the front facing north (-Z). The
runtime OBJ meshes are UV-clipped at Y=16, preserving a seamless leaning face.
All signs and interface graphics are original utility artwork.
"""
import base64
import json
import math
import uuid
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from ddr_mesh_export import pieces, quads

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/arcade_kiosk'
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
TEX = ASSETS / 'textures/block'
for path in (ART, TEX, ASSETS/'models/block', ASSETS/'models/item', ASSETS/'blockstates'):
    path.mkdir(parents=True, exist_ok=True)

COLORS = {'white':'#f1f3f3','ivory':'#d4dbdf','edge':'#9ea9b2','red':'#e92635',
    'red_dark':'#a91629','red_light':'#f6555a','black':'#171c22','dark':'#333c45',
    'silver':'#b5c1c8','teal':'#0c6470','mint':'#63dbd4','pink':'#ffe1eb',
    'light':'#fff7fa','gold':'#ead78b','navy':'#263d50','blue':'#2eafc2'}
KEYS = list(COLORS)
atlas=Image.new('RGBA',(256,256));d=ImageDraw.Draw(atlas)
for i,color in enumerate(COLORS.values()):
    x,y=(i%4)*64,(i//4)*64;d.rectangle((x,y,x+63,y+63),fill=color)
atlas.save(TEX/'arcade_kiosk_materials.png')

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

# Portrait idle screen. These are static decorative controls; the actual
# inventory screen opens through the block's normal interaction.
screen=Image.new('RGB',(1024,2048),'#f4faf8');d=ImageDraw.Draw(screen)
for r in range(1600,1100,-20):
    d.ellipse((-r+620,-r-80,r+620,r-80),outline='#d9efeb',width=12)
d.polygon([(0,0),(330,0),(1024,920),(1024,1120)],fill='#cfefec')
d.polygon([(0,560),(1024,1650),(1024,1810),(0,720)],fill='#e2f2ec')
d.line((0,472,1024,1500),fill='#63c8c8',width=12)
d.line((0,506,1024,1534),fill='#cadcd3',width=4)
d.rounded_rectangle((63,72,961,202),radius=22,fill='#0b6470')
d.text((512,137),'FUN PACK  /  ARCADE',anchor='mm',font=font(48,True),fill='white')
d.text((512,480),'ARCADE',anchor='mm',font=font(130,True),fill='#183944')
d.text((512,605),'ORDER',anchor='mm',font=font(150,True),fill='#183944')
d.line((320,720,704,720),fill='#de4252',width=10)
d.text((512,814),'BUILD YOUR ARCADE',anchor='mm',font=font(42,True),fill='#387984')
for x,label,kind in ((86,'MACHINES','machine'),(539,'PRIZES','prize')):
    d.rounded_rectangle((x,990,x+398,1420),radius=35,fill='#ffffff',outline='#badbd9',width=5)
    if kind=='machine':
        d.rounded_rectangle((x+132,1052,x+266,1268),radius=12,fill='#2b5362')
        d.rounded_rectangle((x+152,1080,x+247,1180),radius=4,fill='#69ccc8')
        d.polygon([(x+132,1203),(x+266,1203),(x+285,1235),(x+116,1235)],fill='#e85061')
        d.rectangle((x+122,1268,x+277,1287),fill='#2b5362')
    else:
        d.rounded_rectangle((x+106,1135,x+291,1285),radius=10,fill='#e6556a')
        d.rectangle((x+88,1111,x+310,1148),fill='#f07787')
        d.rectangle((x+183,1112,x+215,1285),fill='#f5dd96')
        d.ellipse((x+141,1066,x+201,1118),outline='#d9b352',width=13)
        d.ellipse((x+200,1066,x+260,1118),outline='#d9b352',width=13)
    d.text((x+199,1345),label,anchor='mm',font=font(41,True),fill='#264c58')
d.rounded_rectangle((86,1615,938,1755),radius=35,fill='#0b7881')
d.text((512,1685),'TOUCH TO BROWSE',anchor='mm',font=font(54,True),fill='white')
d.text((512,1880),'MATERIALS IN.  ARCADE OUT.',anchor='mm',font=font(34,True),fill='#5d8790')
for x in (464,512,560):d.ellipse((x-7,1954,x+7,1968),fill='#3faeb7')
screen.save(TEX/'arcade_kiosk_screen.png')

details=Image.new('RGB',(1024,1024),'#eff5f4');d=ImageDraw.Draw(details)
d.rectangle((0,0,1024,256),fill='#0a525d')
for x in range(-100,1100,135):
    d.line((x,250,x+150,0),fill='#23727a',width=4)
d.text((512,87),'ARCADE',anchor='mm',font=font(108,True),fill='white')
d.text((512,195),'ORDER',anchor='mm',font=font(90,True),fill='#90e1dc')
d.rectangle((0,272,1024,474),fill='#d9e6e6')
for i in range(5):
    x=13+i*201
    d.rounded_rectangle((x,283,x+189,463),radius=10,fill=('#f3ead0' if i%2==0 else '#e7f6f4'))
    d.polygon([(x+15,457),(x+183,295),(x+183,347),(x+64,457)],fill=('#e2d9ac' if i%2==0 else '#cce6e7'))
    d.text((x+94,361),'ORDER',font=font(26,True),anchor='mm',fill='#366776')
d.rectangle((0,500,1024,642),fill='#eff4f4')
d.text((512,571),'TAP TO ORDER',font=font(72,True),anchor='mm',fill='#244e61')
d.rectangle((0,672,1024,798),fill='#16343f')
d.text((512,735),'COLLECT & PLAY',font=font(64,True),anchor='mm',fill='#deeceb')
d.text((512,905),'ARCADE ORDER',font=font(85,True),anchor='mm',fill='#0e6975')
details.save(TEX/'arcade_kiosk_details.png')

surfaces=[];group='Cabinet casing'
def tile(material):
    i=KEYS.index(material);u=(i%4)*4;v=(i//4)*4
    return [(u+1,v+1),(u+1,v+3),(u+3,v+3),(u+3,v+1)]
def face(name,points,material='white',texture='materials',uv=None,glow=False):
    surfaces.append({'name':name,'group':group,'texture':'#'+texture,'glow':glow,
        'vertices':[list(p) for p in points],'uv':uv or tile(material)[:len(points)]})
def box(name,lo,hi,material='white'):
    x,y,z=lo;X,Y,Z=hi
    v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for side,ids in {'north':(3,2,1,0),'south':(4,5,6,7),'west':(0,4,7,3),
        'east':(1,2,6,5),'up':(3,7,6,2),'down':(0,1,5,4)}.items():
        face(name+' '+side,[v[i] for i in ids],material)
def roundrect(x0,y0,x1,y1,r,n=7):
    r=min(r,(x1-x0)/2,(y1-y0)/2);out=[]
    for cx,cy,start in ((x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)):
        for i in range(n+1):
            a=math.radians(start+i*90/n);p=(cx+r*math.cos(a),cy+r*math.sin(a))
            if not out or math.dist(p,out[-1])>1e-8:out.append(p)
    if math.dist(out[0],out[-1])<1e-8:out.pop()
    return out
def prism(name,outline,z0,z1,material='white',glow=False,front=True):
    cx=sum(p[0] for p in outline)/len(outline);cy=sum(p[1] for p in outline)/len(outline)
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        if front:face(name+' front '+str(i),[(cx,cy,z0),(*q,z0),(*p,z0)],material,glow=glow)
        face(name+' back '+str(i),[(cx,cy,z1),(*p,z1),(*q,z1)],material)
        face(name+' edge '+str(i),[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material)
def rounded(name,rect,z0,z1,r=.2,material='white',glow=False):
    prism(name,roundrect(*rect,r),z0,z1,material,glow)
def disc(name,x,y,r,z0,z1,material='silver',count=36):
    prism(name,[(x+r*math.cos(i*math.tau/count),y+r*math.sin(i*math.tau/count)) for i in range(count)],z0,z1,material)
def decal(name,rect,z,texture='details',region=(0,0,16,16),glow=False):
    x0,y0,x1,y1=rect;u0,v0,u1,v1=region
    face(name,[(x1,y1,z),(x1,y0,z),(x0,y0,z),(x0,y1,z)],texture=texture,
        uv=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)],glow=glow)
def front_frame(name,outer,inner,levels,materials):
    outlines=[roundrect(*rect,r) for rect,r,z in levels]
    for k,(a,b) in enumerate(zip(outlines,outlines[1:])):
        za,zb=levels[k][2],levels[k+1][2]
        for i,p in enumerate(a):
            j=(i+1)%len(a)
            face(name+' band %d %d'%(k,i),[(*p,za),(*b[i],zb),(*b[j],zb),(*a[j],za)],materials[k])

# Feet and pedestal occupy a narrow, sensible footprint, without overhangs.
rounded('Bottom charcoal chassis',(1.15,0,14.85,.45),2.85,13.6,.16,'black')
rounded('Silver plinth',(1.05,.27,14.95,1.02),2.6,13.75,.16,'silver')
rounded('White pedestal carcass',(1.45,.92,14.55,11.40),3.20,13.22,.36,'white')
rounded('Lower kick plate',(1.73,1.0,14.27,3.84),3.16,3.24,.10,'ivory')
box('Kick plate top hairline',(1.76,3.85,3.15),(14.24,3.88,3.23),'edge')
rounded('Upper black main chassis',(1.75,10.9,14.25,28.42),5.05,12.80,.48,'black')
rounded('White pedestal service face',(1.65,3.99,14.35,11.43),3.135,3.23,.28,'white')

# Wraparound white side panels follow the leaning front, while rear stays straight.
profile=[(1.02,3.23),(11.1,3.23),(28.18,5.01),(28.18,12.81),(1.02,12.81)]
for x,sign in ((1.46,-1),(14.54,1)):
    for i in range(1,len(profile)-1):
        pts=[(x,*profile[0]),(x,*profile[i]),(x,*profile[i+1])]
        face('White side shell %s %d'%(x,i),pts[::-1] if sign<0 else pts,'white')
    # A broad dark inset with a custom teal stripe lends the side its silhouette.
    inset=[(5.2,6.48),(11.7,5.62),(26.9,6.90),(26.9,12.05),(5.2,12.05)]
    for i in range(1,len(inset)-1):
        pts=[(x+sign*.02,*inset[0]),(x+sign*.02,*inset[i]),(x+sign*.02,*inset[i+1])]
        face('Black side inset %s %d'%(x,i),pts[::-1] if sign<0 else pts,'black')
    pts=[(x+sign*.033,7.8,7.08),(x+sign*.033,9.0,6.91),(x+sign*.033,24.1,10.85),(x+sign*.033,22.9,11.01)]
    face('Teal side diagonal '+str(x),pts[::-1] if sign<0 else pts,'teal')

group='Lower service details'
disc('Speaker chrome bezel',8.0,9.55,.95,3.075,3.17,'silver',48)
disc('Speaker grille',8.0,9.55,.84,3.054,3.10,'edge',48)
for row in range(-4,5):
    for col in range(-4,5):
        x=col*.145+(row%2)*.07;y=row*.145
        if x*x+y*y<.65*.65:disc('Speaker perforation %d %d'%(row,col),8+x,9.55+y,.033,3.045,3.063,'dark',8)
rounded('Recessed collection tray',(5.77,5.41,10.23,6.85),3.077,3.16,.10,'edge')
rounded('Collection tray shadow',(6.02,5.70,9.98,6.65),3.059,3.08,.05,'dark')
box('Collection tray upper shadow',(6.05,6.42,3.045),(9.96,6.64,3.061),'black')
box('Collection tray lower sill',(5.99,5.63,2.97),(10.01,5.78,3.10),'silver')
rounded('Payment assembly metal surround',(2.33,8.73,3.76,10.83),3.07,3.21,.12,'silver')
rounded('Payment black slot',(2.52,9.03,3.54,9.53),2.99,3.08,.07,'black')
box('Payment slot lip',(2.60,9.10,2.96),(3.49,9.23,3.02),'edge')
box('Small silver coin inlet',(2.91,10.03,3.03),(3.10,10.54,3.11),'dark')
rounded('Blank left service panel',(11.51,9.18,12.93,10.61),3.104,3.18,.07,'ivory')
disc('Service lock rim',2.34,4.55,.23,3.049,3.15,'silver',24)
box('Service key notch',(2.31,4.41,3.038),(2.37,4.69,3.056),'dark')
for x in (2.06,13.94):
    for y in (1.47,11.05):disc('Pedestal fixing %s %s'%(x,y),x,y,.074,3.10,3.15,'silver',12)

# Build the display as one assembly, then shear it back slightly around Y=11.
# This makes screen, bezel and light fins agree on precisely the same plane.
group='Leaning red display';lean_start=len(surfaces)
rounded('Deep red display molding',(1.32,10.92,14.68,28.61),3.20,4.47,.96,'red_dark')
prism('Molding rounded scarlet sides',roundrect(1.43,11.02,14.57,28.50,.91),2.94,3.34,'red',front=False)
front_frame('Rolled red frame',None,None,[
    ((1.48,11.06,14.52,28.47),.92,2.94),
    ((1.72,11.23,14.28,28.24),.89,2.70),
    ((2.30,11.60,13.70,27.80),.59,2.66),
    ((2.71,11.99,13.29,27.42),.38,2.99)],['red_light','red','red_dark'])
rounded('Inset black control glass',(2.72,12.01,13.28,27.42),2.978,3.19,.34,'black')
rounded('Portrait touchscreen inner rim',(3.76,14.80,12.24,24.68),2.940,2.986,.10,'edge')
decal('Portrait arcade ordering screen',(3.89,14.94,12.11,24.54),2.926,'screen',glow=True)
rounded('Upper screen silver frame',(3.24,24.99,12.76,27.02),2.943,3.00,.12,'silver')
decal('Small landscape product screen',(3.40,25.13,12.60,26.88),2.929,region=(0,4.25,16,7.42),glow=True)
rounded('Contactless reader lower',(4.00,12.99,6.39,14.25),2.929,3.005,.16,'white')
decal('Reader label',(4.12,13.21,6.28,14.06),2.915,region=(0,7.81,16,10.03))
disc('Contactless status lamp',4.22,13.02,.065,2.90,2.93,'mint',12)
rounded('Small dark service touchpad',(8.93,13.08,10.53,14.28),2.931,3.03,.09,'dark')
for x,y in ((3.10,12.4),(12.89,12.4),(3.10,24.76),(12.89,24.76)):
    disc('Black panel screw %s %s'%(x,y),x,y,.065,2.927,2.986,'edge',12)
for x in (7.49,8.04,8.59):disc('Touch console indicator '+str(x),x,14.49,.041,2.912,2.949,'edge',12)

group='Illuminated side fins'
for left in (False,True):
    raw=[(1.78,14.85),(2.62,15.64),(3.09,19.44),(2.65,23.83),(1.78,24.48)]
    outline=[(16-x,y) if left else (x,y) for x,y in raw]
    if left:outline.reverse()
    prism('White light column backing '+str(left),outline,2.49,2.96,'ivory')
    raw=[(1.94,15.15),(2.44,15.81),(2.88,19.44),(2.46,23.60),(1.94,24.09)]
    outline=[(16-x,y) if left else (x,y) for x,y in raw]
    if left:outline.reverse()
    prism('Pale illuminated column '+str(left),outline,2.462,2.51,'pink',True)
    # Slim zigzag facets preserve the angular light-column reference detail.
    zig=[(2.03,23.68),(2.71,20.05),(2.13,18.07),(2.45,15.83)]
    if left:zig=[(16-x,y) for x,y in zig]
    for i,(a,b) in enumerate(zip(zig,zig[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];dist=math.hypot(dx,dy);nx,ny=-dy/dist*.024,dx/dist*.024
        pts=[(a[0]+nx,a[1]+ny,2.448),(b[0]+nx,b[1]+ny,2.448),(b[0]-nx,b[1]-ny,2.448),(a[0]-nx,a[1]-ny,2.448)]
        # All small front details use an outward (-Z) winding.
        if ((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0]))>0:pts.reverse()
        face('Light facet line %s %d'%(left,i),pts,'light',glow=True)
for f in surfaces[lean_start:]:
    for p in f['vertices']:p[2]+=(p[1]-11)*.105

group='Raised teal marquee'
for x in (4.35,11.65):box('Marquee support '+str(x),(x-.20,28.29,6.06),(x+.20,29.66,6.54),'dark')
rounded('Marquee charcoal back',(2.35,29.21,13.65,32),5.16,6.14,.18,'dark')
rounded('Marquee teal face',(2.44,29.29,13.56,31.92),5.03,5.23,.12,'teal')
decal('ARCADE ORDER illuminated marquee',(2.58,29.44,13.42,31.78),5.016,region=(0,0,16,4),glow=True)
for x in (2.52,13.48):
    for y in (29.38,31.83):disc('Marquee fixing %s %s'%(x,y),x,y,.047,5.01,5.08,'silver',12)

group='Rear service panel'
rounded('Back service door',(2.04,2.00,13.96,26.83),12.79,12.875,.19,'dark')
for x in (2.57,13.43):
    for y in (2.50,26.30):box('Rear service fixing %s %s'%(x,y),(x-.05,y-.05,12.879),(x+.05,y+.05,12.90),'edge')
for row in range(9):box('Rear upper ventilation '+str(row),(4.80,23.22+row*.22,12.88),(11.20,23.32+row*.22,12.93),'black')
for row in range(5):box('Rear lower ventilation '+str(row),(5.83,4.15+row*.26,13.219),(10.17,4.27+row*.26,13.245),'dark')

# The reference is a slender upright terminal, considerably narrower than a
# rhythm cabinet. Keep a generous one-cell placement footprint around it.
for f in surfaces:
    for p in f['vertices']:p[0]=8+(p[0]-8)*.78

def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
textures={name:'japanesearcades:block/arcade_kiosk_'+name for name in ('materials','screen','details')}
textures['particle']=textures['materials']

def obj(path,faces):
    lines=['# Original arcade ordering kiosk. Coordinates in blocks.',
        'mtllib japanesearcades:models/block/arcade_kiosk.mtl'];index=1;last=None
    for f in faces:
        material=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
        if last!=material:lines.append('usemtl '+material);last=material
        lines.extend('v '+' '.join('%.8f'%(v/16) for v in p) for p in f['vertices'])
        lines.extend('vt %.8f %.8f'%(u/16,1-v/16) for u,v in f['uv'])
        lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
        index+=len(f['vertices'])
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def wrapper(name,item=False):
    data={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name+'.obj',
        'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
        'ambientocclusion':not item,'render_type':'minecraft:cutout_mipped_all','textures':textures}
    if item:data.update({'gui_light':'front','display':{
        'gui':{'rotation':[12,225,0],'translation':[0,-4,0],'scale':[.48,.48,.48]},
        'ground':{'translation':[0,1,0],'scale':[.25,.25,.25]},
        'fixed':{'rotation':[0,180,0],'translation':[0,-6,0],'scale':[.5,.5,.5]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,0,0],'scale':[.27,.27,.27]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,-3,0],'scale':[.4,.4,.4]}}})
    return data

split={'lower':[],'upper':[]}
for f in surfaces:
    for part in pieces(list(zip(f['vertices'],f['uv'])),1,[16]):
        for poly in quads(part):
            half='upper' if sum(p[0][1] for p in poly)/len(poly)>=16 else 'lower'
            offset=16 if half=='upper' else 0
            split[half].append({**f,'vertices':[[p[0],p[1]-offset,p[2]] for p,uv in poly],'uv':[uv for p,uv in poly]})
for half,faces in split.items():
    name='block/arcade_kiosk_'+half
    obj(ASSETS/'models'/(name+'.obj'),faces);write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
obj(ASSETS/'models/item/arcade_kiosk.obj',surfaces)
write_json(ASSETS/'models/item/arcade_kiosk.json',wrapper('item/arcade_kiosk',True))
mtl=[]
for key in ('materials','screen','details'):
    for glow in (False,True):
        mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
            'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/arcade_kiosk.mtl').write_text('\n'.join(mtl),encoding='utf-8')
write_json(ASSETS/'blockstates/arcade_kiosk.json',{'variants':{
    'facing='+direction+',half='+half:{'model':'japanesearcades:block/arcade_kiosk_'+half,**({'y':angle} if angle else {})}
    for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for half in ('lower','upper')}})

bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,
    'statistics':{'authoring_faces':len(surfaces),**{half+'_faces':len(faces) for half,faces in split.items()}},
    'notes':'Original native geometry. One horizontal block, two high. North-facing -Z; leaning screen uses 0.105 Z per Y. Runtime split at Y=16.'})

groups=defaultdict(list);elements=[]
assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
for f in surfaces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'arcade_kiosk/'+f['name']))
    key=f['texture'][1:];texture_index=('materials','screen','details').index(key)
    width,height={'materials':(256,256),'screen':(1024,2048),'details':(1024,1024)}[key]
    keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
        'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_index}},'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,(key,width,height) in enumerate((('materials',256,256),('screen',1024,2048),('details',1024,1024))):
    p=TEX/('arcade_kiosk_'+key+'.png')
    bbtex.append({'name':p.name,'folder':'block','namespace':'japanesearcades','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'arcade_kiosk/'+key)),'width':width,'height':height,
        'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'arcade_kiosk.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'Arcade Ordering Kiosk','model_identifier':'arcade_kiosk','visible_box':[1,2,1],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'arcade_kiosk/group/'+name)),
        'origin':[8,0,8],'children':children} for name,children in groups.items()]})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    assert all(0<=p[0]<=16 and 0<=p[1]<=32 and 0<=p[2]<=16 for p in f['vertices']),f['name']
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])
print('Kiosk mesh exported:',len(surfaces),'faces; bounds',bounds,'split',{k:len(v) for k,v in split.items()})
