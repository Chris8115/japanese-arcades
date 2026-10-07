"""Build the two-player beatmania IIDX LIGHTNING MODEL cabinet.

Eight native static multiblock meshes retain its two-block-wide console,
recessed upper frame and low front standing platform. The only idle motion is
a sixteen-frame vanilla atlas animation on the two metal turntable tops.
"""
from __future__ import annotations
import base64
from collections import defaultdict
import json
import math
from pathlib import Path
import uuid
from PIL import Image, ImageDraw, ImageFont
from ddr_mesh_export import pieces, quads
from obj_mesh_optimizer import optimize_obj
from iidx_artwork import pack_artwork
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/beatmania-iidx-lightning'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
for path in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):
    path.mkdir(parents=True,exist_ok=True)

COLORS={'black':'#12131a','dark':'#252632','steel':'#484d5a','edge':'#747b87',
    'silver':'#b6c0c9','white':'#eef1f3','rubber':'#08090e','purple':'#953ad4',
    'violet':'#bd63f2','pink':'#f0b9ff','blue':'#5342e5','cyan':'#80d7f0',
    'plum':'#583874','grille':'#20212a','cream':'#dbe0e9','chrome':'#d9e0e6'}
KEYS=list(COLORS)
atlas=Image.new('RGB',(256,256));d=ImageDraw.Draw(atlas)
for i,color in enumerate(COLORS.values()):
    x,y=i%4*64,i//4*64;d.rectangle((x,y,x+63,y+63),fill=color)
atlas.save(TEX/'beatmania_iidx_lightning_materials.png')
def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

controls=Image.new('RGB',(1024,512),'#767b83');d=ImageDraw.Draw(controls)
for x in range(0,1024,8):d.line((x,0,x,512),fill='#737880',width=1)
for x in (20,762):
    d.rectangle((x,35,x+240,464),fill='#171921',outline='#b8bdc7',width=4)
    d.line((x+12,454,x+226,454),fill='#a3abb6',width=3)
for x in (280,531):
    d.rectangle((x,104,x+214,459),fill='#52545f',outline='#bbc2cb',width=4)
    d.rectangle((x+5,110,x+209,452),outline='#383b45',width=4)
    d.text((x+24,131),'01' if x==280 else '02',font=font(23,True),fill='#d7dde8')
    for px in (x+12,x+202):
        for py in (116,447):d.ellipse((px-3,py-3,px+3,py+3),fill='#242631')
for x in (27,998):
    for y in (21,489):
        d.ellipse((x-5,y-5,x+5,y+5),fill='#c3c9cf');d.line((x-3,y,x+3,y),fill='#4c535e',width=2)
d.text((512,42),'beatmania IIDX',anchor='mm',font=font(23),fill='#dde2e7')
d.text((512,76),'LIGHTNING MODEL',anchor='mm',font=font(13),fill='#c2c8d0')
controls.save(TEX/'beatmania_iidx_lightning_controls.png')

details=Image.new('RGB',(1024,1024),'#181921');d=ImageDraw.Draw(details)
# Four printed regions: grille, contactless reader, rear vent and warning card.
for y in range(12,502,9):
    for x in range(10+(y//9%2)*4,505,9):d.rectangle((x,y,x+2,y+2),fill='#30313d')
d.ellipse((95,95,417,417),outline='#232432',width=8)
d.rectangle((512,0,1023,511),fill='#131621')
d.rounded_rectangle((557,130,978,372),radius=13,fill='#dce3e7',outline='#737d8b',width=8)
d.rounded_rectangle((652,168,786,313),radius=16,outline='#858e99',width=8)
for r in (22,39,58):d.arc((719-r,241-r,719+r,241+r),-60,60,fill='#9aabbc',width=5)
d.text((868,228),'e-amusement',anchor='mm',font=font(21,True),fill='#667486')
d.text((868,288),'PASS',anchor='mm',font=font(24),fill='#737a87')
d.rectangle((0,512,511,1023),fill='#242630')
for y in range(550,982,29):d.line((37,y,476,y),fill='#0b0d13',width=11)
d.rectangle((512,512,1023,1023),fill='#c8cfd9')
d.rectangle((529,533,1006,610),fill='#50377b')
d.text((768,572),'LIGHTNING MODEL',anchor='mm',font=font(36,True),fill='#f0e6fb')
for y in (678,722,766,810,854):d.line((564,y,973,y),fill='#5e6879',width=5)
details.save(TEX/'beatmania_iidx_lightning_details.png')

floor=Image.new('RGB',(1024,1024),'#15141d');d=ImageDraw.Draw(floor)
d.rectangle((16,16,1007,1007),outline='#a8a7b4',width=10)
d.rectangle((35,35,988,988),outline='#434051',width=4)
for x in (38,985):
    for y in (38,986):d.ellipse((x-5,y-5,x+5,y+5),fill='#d2c8de')
d.text((188,345),'01',anchor='mm',font=font(136,True),fill='#cac6d1')
d.text((836,345),'02',anchor='mm',font=font(136,True),fill='#cac6d1')
d.rectangle((81,272,113,420),fill='#a09aa9');d.rectangle((911,272,943,420),fill='#a09aa9')
d.polygon([(352,209),(567,166),(720,320),(566,499),(343,422),(429,310)],outline='#d5c9e3',width=10)
d.text((522,332),'IIDX',anchor='mm',font=font(131,True),fill='#d8cce4')
d.text((512,769),'beatmania IIDX',anchor='mm',font=font(91),fill='#ddd7e4')
d.text((512,911),'LIGHTNING MODEL',anchor='mm',font=font(33),fill='#7b708d')
floor.save(TEX/'beatmania_iidx_lightning_floor.png')

# A static metal record with one restrained moving index mark. Only a 256px
# atlas sprite advances; the cabinet and physical platter never re-tessellate.
frames=Image.new('RGB',(256,4096),'#535763')
for frame in range(16):
    disk=Image.new('RGB',(256,256),'#656b76');d=ImageDraw.Draw(disk)
    for r in range(121,28,-4):
        tone=118+(r%12);d.ellipse((128-r,128-r,128+r,128+r),outline=(tone,tone+5,tone+13),width=1)
    d.ellipse((94,94,162,162),fill='#252734',outline='#b4b9c7',width=3)
    d.text((128,128),'IIDX',anchor='mm',font=font(16,True),fill='#b6a5cf')
    angle=math.tau*frame/16
    points=[]
    for r,a in ((112,angle-.027),(120,angle-.027),(120,angle+.027),(112,angle+.027)):
        points.append((128+r*math.sin(a),128-r*math.cos(a)))
    d.polygon(points,fill='#edc8ff')
    frames.paste(disk,(0,frame*256))
    if frame==0:disk.save(ART/'turntable-frame.png')
frames.save(TEX/'beatmania_iidx_lightning_turntable.png')
(TEX/'beatmania_iidx_lightning_turntable.png.mcmeta').write_text(
    json.dumps({'animation':{'width':256,'height':256,'frametime':10,'interpolate':False}})+'\n',encoding='utf-8')
packed=pack_artwork()
SCALES={key:(value['uv'][2]/16,value['uv'][3]/16) for key,value in packed.items()}


surfaces=[]
group='Cabinet'

def tile(material):
    i=KEYS.index(material);u=i%4*4;v=i//4*4
    return [(u+1,v+1),(u+1,v+3),(u+3,v+3),(u+3,v+1)]

def face(name,points,material='white',texture='materials',uv=None,glow=False):
    coordinates=uv or tile(material)[:len(points)]
    if texture in SCALES:
        su,sv=SCALES[texture];coordinates=[(u*su,v*sv) for u,v in coordinates]
    surfaces.append({'name':name,'group':group,'texture':'#'+texture,'glow':glow,
                     'vertices':[list(p) for p in points],'uv':[list(p) for p in coordinates]})

def box(name,lo,hi,material='black',omit=()):
    x,y,z=lo;X,Y,Z=hi
    v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for side,ids in {'north':(3,2,1,0),'south':(4,5,6,7),'west':(0,4,7,3),
                     'east':(1,2,6,5),'up':(3,7,6,2),'down':(0,1,5,4)}.items():
        if side not in omit:face(name+' '+side,[v[i] for i in ids],material)

def polygon_faces(points):
    """Triangulate an arbitrary simple CCW polygon; keep convex quads intact."""
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if len(points)<=4 and all(cross(points[i-1],points[i],points[(i+1)%len(points)])>0 for i in range(len(points))):
        return [tuple(range(len(points)))]
    remaining=list(range(len(points)));triangles=[]
    while len(remaining)>3:
        for j,index in enumerate(remaining):
            prev,nxt=remaining[j-1],remaining[(j+1)%len(remaining)]
            a,b,c=points[prev],points[index],points[nxt]
            if cross(a,b,c)<=1e-9:continue
            if any(cross(a,b,points[k])>=-1e-9 and cross(b,c,points[k])>=-1e-9 and cross(c,a,points[k])>=-1e-9
                   for k in remaining if k not in (prev,index,nxt)):continue
            triangles.append((prev,index,nxt));remaining.pop(j);break
        else:raise AssertionError(('Polygon could not be triangulated',points))
    triangles.append(tuple(remaining));return triangles

def prism(name,outline,z0,z1,material='white',front=True,back=True):
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))
    if area<0:outline=list(reversed(outline))
    for i,indices in enumerate(polygon_faces(outline)):
        if front:face(name+' front '+str(i),[(*outline[k],z0) for k in reversed(indices)],material)
        if back:face(name+' back '+str(i),[(*outline[k],z1) for k in indices],material)
    for i,a in enumerate(outline):
        b=outline[(i+1)%len(outline)]
        face(name+' edge '+str(i),[(*a,z0),(*b,z0),(*b,z1),(*a,z1)],material)

def side_prism(name,outline,x0,x1,material='white'):
    start=len(surfaces);prism(name,outline,x0,x1,material)
    # Local polygon coordinates are Z,Y. Swap Z/X, reversing handedness.
    for f in surfaces[start:]:
        f['vertices']=[[p[2],p[1],p[0]] for p in reversed(f['vertices'])]
        f['uv'].reverse()

def decal(name,rect,z,texture,region=(0,0,16,16),glow=False):
    x,y,X,Y=rect;u,v,U,V=region
    face(name,[(X,Y,z),(X,y,z),(x,y,z),(x,Y,z)],texture=texture,
         uv=[(u,v),(u,V),(U,V),(U,v)],glow=glow)

def ribbon(name,points,width,z,material,glow=False):
    for i,(a,b) in enumerate(zip(points,points[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length*width/2,dx/length*width/2
        face(name+' '+str(i),[(a[0]-nx,a[1]-ny,z),(a[0]+nx,a[1]+ny,z),
            (b[0]+nx,b[1]+ny,z),(b[0]-nx,b[1]-ny,z)],material,glow=glow)

def rotate_y_since(start,cx,cz,angle):
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    for f in surfaces[start:]:
        for p in f['vertices']:
            x,z=p[0]-cx,p[2]-cz;p[0],p[2]=cx+c*x+s*z,cz-s*x+c*z

def top_disc(name,x,y,z,profile,segments=20):
    """A short lathed control knob, with the top closed by simple triangles."""
    for j,(a,b) in enumerate(zip(profile,profile[1:])):
        ra,ya,material=a;rb,yb,_=b
        for i in range(segments):
            t,u=i*math.tau/segments,(i+1)*math.tau/segments
            pts=[(x+ra*math.cos(t),y+ya,z+ra*math.sin(t)),
                 (x+rb*math.cos(t),y+yb,z+rb*math.sin(t)),
                 (x+rb*math.cos(u),y+yb,z+rb*math.sin(u)),
                 (x+ra*math.cos(u),y+ya,z+ra*math.sin(u))]
            face(name+' ring%d %d'%(j,i),pts,material)
    r,yy,mat=profile[-1]
    for i in range(segments):
        t,u=i*math.tau/segments,(i+1)*math.tau/segments
        face(name+' top '+str(i),[(x,y+yy,z),(x+r*math.cos(u),y+yy,z+r*math.sin(u)),
                                 (x+r*math.cos(t),y+yy,z+r*math.sin(t))],mat)

def front_ring(name,x,y,z,profile,segments=24):
    """Concave speaker cone/recess built from circular annuli facing north."""
    for j,(a,b) in enumerate(zip(profile,profile[1:])):
        ra,za,material,glow=a;rb,zb,_,_=b
        for i in range(segments):
            ta,tb=i*math.tau/segments,(i+1)*math.tau/segments
            face(name+' %d %d'%(j,i),list(reversed([(x+ra*math.cos(ta),y+ra*math.sin(ta),z+za),
                (x+ra*math.cos(tb),y+ra*math.sin(tb),z+za),
                (x+rb*math.cos(tb),y+rb*math.sin(tb),z+zb),
                (x+rb*math.cos(ta),y+rb*math.sin(ta),z+zb)])),material,glow=glow)

# Low standing platform, printed mat and restrained side strips. This is a
# flat standing floor, not a bank of raised dance controls.
group='Low standing platform'
box('Standing platform black plinth',(.10,0,-15.80),(31.90,.70,15.75),'rubber')
box('Front standing platform metal casing',(0,.25,-16),(32,1.01,.20),'silver')
box('Rear cabinet floor pan',(.43,.67,.02),(31.57,1.13,15.57),'black')
box('Printed mat black backing',(4.01,1.012,-15.11),(27.99,1.06,-.23),'black',('down',))
face('IIDX 01 02 standing floor graphic',[(27.79,1.071,-.38),(27.79,1.071,-14.97),
    (4.21,1.071,-14.97),(4.21,1.071,-.38)],texture='floor',uv=[(0,0),(0,16),(16,16),(16,0)])
for x in (.30,28.40):
    face('Platform side brushed steel '+str(x),[(x+3.29,1.04,.04),(x+3.29,1.04,-15.38),
        (x,1.04,-15.38),(x,1.04,.04)],'edge')
    for j in range(2):
        xx=x+.68+j*.37
        face('Floor purple stripe %s %d'%(x,j),[(xx+.11,1.052,-.10),(xx+.11,1.052,-14.81),
             (xx,1.052,-14.81),(xx,1.052,-.10)],'violet',glow=True)

group='Angular silver and black lower cabinet'
side_prism('Central angled black pedestal',[(.95,1.14),(14.72,1.14),(14.72,18.02),
    (1.44,18.02),(1.55,6.01),(2.28,5.30)],10.48,21.52,'black')
box('Central coin door surround',(11.20,5.90,1.33),(20.80,16.71,1.57),'steel',('south',))
box('Central black coin service door',(11.52,6.23,1.285),(20.48,16.40,1.34),'dark',('south',))
box('Inset door frame',(12.02,6.78,1.248),(19.98,15.98,1.29),'black',('south',))
box('Inset charcoal door',(12.24,7.01,1.224),(19.76,15.75,1.25),'dark',('south',))
box('Coin inlet silver bezel',(14.36,11.99,1.132),(17.64,13.85,1.24),'silver',('south',))
box('Coin black insertion slot',(14.70,12.77,1.098),(17.30,13.11,1.14),'rubber',('south',))
decal('Coin door printed instructions',(14.60,10.48,17.40,11.82),1.207,'details',(8,8,16,16))
for x in (12.43,19.49):
    box('Door long hinge '+str(x),(x-.10,7.62,1.191),(x+.10,9.64,1.24),'steel')
box('Door chrome lock',(19.38,10.27,1.136),(19.76,10.68,1.218),'silver')
for x in (10.13,21.16):
    side_prism('Angled pedestal silver side rail '+str(x),[(.82,1.11),(1.25,1.11),(2.52,5.55),
        (1.78,6.15),(1.78,17.78),(1.32,17.78),(1.32,6.25),(2.03,5.43)],x,x+.72,'silver')
for x in (1.12,26.42):
    side_prism('Tapered lower outer leg '+str(x),[(.05,1.12),(4.16,17.96),(13.76,17.96),(13.76,1.12)],x,x+4.46,'steel')
    side_prism('Tapered lower leg inner black '+str(x),[(.60,1.50),(4.43,17.36),(12.9,17.36),(12.9,1.50)],x+.19,x+4.20,'dark')
    # Front strip follows exactly the slanted manufactured leg face.
    for left,right,material in ((x+.24,x+.76,'black'),(x+.35,x+.64,'violet')):
        face('Lower leg LED %s %s'%(x,material),[(right,17.40,3.97),(right,1.56,.105),
             (left,1.56,.105),(left,17.40,3.97)],material,glow=material=='violet')
for x in (7.94,24.06):
    box('Recessed woofer black chamber '+str(x),(x-2.35,3.4,4.78),(x+2.35,16.15,12.82),'black')
    box('Purple woofer upper fascia '+str(x),(x-2.25,10.6,4.05),(x+2.25,15.92,4.82),'plum',('south',))
    front_ring('Recessed purple woofer '+str(x),x,8.24,4.05,
        [(2.01,0,'steel',False),(1.79,.03,'purple',False),(1.55,.35,'violet',True),
         (1.01,.58,'plum',False),(.045,.48,'purple',False)],24)
    box('Woofer upper vent '+str(x),(x-2.03,15.94,3.95),(x+2.03,17.55,4.82),'rubber')

# The main monitor remains a separate landscape rectangle set back from the
# forward arms. Above it, a deep recess has an opaque black rear backing.
group='Rear landscape display and supporting frame'
box('Rear wide lower spine',(3.16,17.60,11.05),(28.84,38.03,15.18),'black',('down',))
for x in (1.94,28.72):
    box('Tall rear structural post '+str(x),(x,17.72,13.79),(x+1.34,44.77,15.21),'steel')
box('Landscape monitor thick outer frame',(4.32,24.45,8.38),(27.68,38.12,11.26),'dark')
box('Landscape display black bezel',(4.56,24.70,8.20),(27.44,37.88,8.43),'rubber',('south',))
box('Main screen inner metal gasket',(4.93,25.02,8.165),(27.07,37.57,8.23),'edge',('south',))
decal('Landscape HEROIC VERSE main display',(5.05,25.10,26.95,37.41875),8.148,'display',glow=True)
box('Rear monitor removable service panel',(5.02,25.0,15.185),(26.98,36.89,15.225),'dark')
face('Rear wide printed ventilation',[(8.0,34.0,15.238),(24.0,34.0,15.238),(24.0,36.0,15.238),(8.0,36.0,15.238)],
     texture='details',uv=[(0,16),(8,16),(8,8),(0,8)])

group='Glossy black upper rear backing'
box('Opaque upper speaker recess backing',(3.16,38.03,14.82),(28.84,44.00,15.18),'black')

group='Pale inner side baffles'
for x0,x1 in ((1.46,4.34),(27.66,30.54)):
    box('Light metal inner side baffle '+str(x0),(x0,20.80,12.95),(x1,44.70,13.15),'cream')

group='Four black directional speaker boxes'
for x,y in ((2.70,32.16),(29.30,32.16),(10.04,40.55),(21.96,40.55)):
    upper=y>38;w=3.52 if upper else 3.31;h=2.78 if upper else 4.51
    z=8.09 if upper else 8.04
    box('Speaker enclosure %s %s'%(x,y),(x-w/2,y-h/2,z),(x+w/2,y+h/2,z+2.60),'black')
    box('Speaker dark bezel %s %s'%(x,y),(x-w/2+.07,y-h/2+.07,z-.08),
        (x+w/2-.07,y+h/2-.07,z+.01),'dark',('south',))
    decal('Black printed speaker grille %s %s'%(x,y),(x-w/2+.19,y-h/2+.19,x+w/2-.19,y+h/2-.19),
        z-.096,'details',(0,0,8,8))
    if upper:box('Upper speaker mounting stalk '+str(x),(x-.19,y+h/2,9.06),(x+.19,44.24,9.51),'steel')

group='Upper character banners'
for right,x0,x1 in ((False,1.46,4.34),(True,27.66,30.54)):
    box('Character banner backing '+str(right),(x0,37.12,9.06),(x1,44.77,9.19),'silver')
    # Map each half of the paired 3:4 artwork to its own narrow 3:8 banner.
    region=(8,0,16,16) if right else (0,0,8,16)
    decal('HEROIC VERSE character banner '+str(right),(x0+.06,37.20,x1-.06,44.56),9.044,'banners',region)

# One wide, shallow metal shelf with two turntables and two seven-key banks.
group='Wide two-player control console'
side_prism('Full console black cabinet', [(-3.52,16.96),(-3.52,18.03),(9.50,19.55),(9.50,18.10)],.38,31.62,'black')
def deck_y(z):return 18.32+(z+1.04)*.12
# The printed sheet clears the housing's slightly different slope at both ends.
face('Two-player printed metal console',[(31.35,deck_y(9.34)+.05,9.34),(31.35,deck_y(-3.41)+.05,-3.41),
    (.65,deck_y(-3.41)+.05,-3.41),(.65,deck_y(9.34)+.05,9.34)],texture='controls',uv=[(0,0),(0,16),(16,16),(16,0)])
box('Console silver front nosing',(.32,17.40,-3.68),(31.68,18.05,-3.47),'silver')
box('Console dark front lip',(.45,17.07,-3.69),(31.55,17.41,-3.47),'dark')
for x in (.42,31.25):
    side_prism('Console steel side edge '+str(x),[(-3.48,17.97),(-3.48,18.16),(9.51,19.71),(9.51,19.52)],x,x+.33,'silver')

group='Two large turntables'
for x in (4.64,27.36):
    z=1.00;y=deck_y(z)
    begin=len(surfaces)
    top_disc('Metal turntable '+str(x),x,y,z,
        [(3.49,0,'black'),(3.47,.18,'violet'),(3.23,.30,'pink'),(3.13,.45,'steel'),(2.98,.47,'silver')],32)
    # The top annulus carries radial UVs of one animated square atlas tile.
    for f in surfaces[begin:]:
        if ' top ' in f['name']:
            f['texture']='#turntable'
            f['uv']=[[8+(x-p[0])/2.98*8,8+(p[2]-z)/2.98*8] for p in f['vertices']]
        if ' ring1 ' in f['name'] or ' ring2 ' in f['name']:f['glow']=True
    for f in surfaces[begin:]:
        for p in f['vertices']:p[1]+=(p[2]-z)*.12

group='Fourteen staggered keyboard buttons and centre starts'
for cx in (11.70,20.30):
    for row,offsets,z in ((0,(-2.175,-.725,.725,2.175),-1.3),(1,(-1.45,0,1.45),.56)):
        for j,offset in enumerate(offsets):
            x=cx+offset;y=deck_y(z);begin=len(surfaces)
            box('Key dark socket %.2f %d %d'%(cx,row,j),(x-.68,y-.06,z-.75),(x+.68,y+.10,z+.75),'black',('down',))
            box('Key blue illuminated edge %.2f %d %d'%(cx,row,j),(x-.61,y+.09,z-.67),(x+.61,y+.23,z+.67),'blue',('down',))
            box('Key pale top %.2f %d %d'%(cx,row,j),(x-.49,y+.22,z-.55),(x+.49,y+.33,z+.55),'cream',('down',))
            for f in surfaces[begin:]:
                for p in f['vertices']:p[1]+=(p[2]-z)*.12
for x,z in ((14.76,2.12),(17.24,2.12),(16.0,3.70)):
    y=deck_y(z)
    box('Small centre START bezel %s %s'%(x,z),(x-.45,y-.02,z-.45),(x+.45,y+.13,z+.45),'steel',('down',))
    box('Small blue centre START button %s %s'%(x,z),(x-.31,y+.13,z-.30),(x+.31,y+.27,z+.30),'blue',('down',))

# Touchscreen and both contactless readers share precisely the same slanted
# panel plane. This avoids an overlay being hidden inside its support wedge.
group='Lower touchscreen and paired contactless readers'
side_prism('Sloped lower touch-panel housing',[(4.90,19.12),(4.90,19.50),(9.16,25.05),(10.12,25.05)],5.57,26.43,'black')
def touch_z(z):return 4.90+(z-3.72)*(4.26/5.44)
def touch_y(z):return 19.50+(z-4.90)*(5.55/4.26)+.028
def touch_decal(name,x0,x1,z0,z1,texture,region=(0,0,16,16),glow=False,normal_offset=0):
    z0,z1=touch_z(z0),touch_z(z1)
    u,v,U,V=region
    # Layered artwork must sit above its metal surround along the actual
    # sloping face normal, not share the same plane and depth-buffer value.
    slope=5.55/4.26
    dy=normal_offset/math.sqrt(1+slope*slope);dz=-slope*dy
    def point(x,z):return (x,touch_y(z)+dy,z+dz)
    face(name,[point(x1,z1),point(x1,z0),point(x0,z0),point(x0,z1)],
         texture=texture,uv=[(u,v),(u,V),(U,V),(U,v)],glow=glow)
touch_decal('Lower silver touchscreen surround',9.82,22.18,3.91,8.85,'materials',(4.9,4.9,7.1,7.1))
touch_decal('Lower HEROIC VERSE touchscreen',10.10,21.90,4.13,8.65,'display',glow=True,normal_offset=.04)
for x0,x1 in ((5.91,9.29),(22.71,26.09)):
    touch_decal('Contactless e-amusement reader '+str(x0),x0,x1,4.13,6.70,'details',(8,0,16,8))
    xx=x0-.18 if x0<16 else x1+.12
    z0,z1=touch_z(4.04),touch_z(8.73)
    face('Purple lower-panel side strip '+str(x0),[(xx+.12,touch_y(z1),z1),(xx+.12,touch_y(z0),z0),
        (xx,touch_y(z0),z0),(xx,touch_y(z1),z1)],'violet',glow=True)

# Slim forward-leaning illuminated pillars. These are separate from the
# setback monitor and leave a deep front recess before the black upper backing.
group='Forward leaning purple light columns'
column=[(.86,19.20),(3.47,19.20),(3.47,42.70),(2.79,44.09),(1.38,44.09),(.86,43.35)]
for right in (False,True):
    start=len(surfaces)
    outline=[(32-x,y) for x,y in column] if right else column
    prism('Main angular LED pillar '+str(right),outline,2.17,3.48,'steel')
    inset=[(1.10,19.43),(3.22,19.43),(3.22,42.62),(2.62,43.78),(1.53,43.78),(1.10,43.21)]
    if right:inset=[(32-x,y) for x,y in inset]
    prism('LED pillar black recessed face '+str(right),inset,2.137,2.20,'black',back=False)
    for j,pts in enumerate(([(1.71,20.2),(1.71,31.70)],[(1.71,32.36),(1.71,42.7),(2.15,43.20),(2.72,42.89)])):
        if right:pts=[(32-x,y) for x,y in pts]
        ribbon('Broad purple pillar lamp %s %d'%(right,j),pts,.47,2.119,'violet',True)
        ribbon('Pillar bright lamp core %s %d'%(right,j),pts,.19,2.107,'pink',True)
    for f in surfaces[start:]:
        for p in f['vertices']:p[2]+=5.63-(p[1]-19.20)*.365
    x0,x1=(1.89,3.04) if not right else (28.96,30.11)
    side_prism('Upper pillar rear connector '+str(right),[(.50,41.92),(6.58,43.46),(6.58,44.44),(.29,42.90)],x0,x1,'black')

group='High HEROIC VERSE marquee and recessed roof frame'
box('High roof back crossmember',(2.1,43.73,10.26),(29.9,44.61,14.96),'black')
box('High roof panel',(3.10,44.0,5.64),(28.90,44.42,13.98),'dark')
cap=[(.87,44.39),(1.21,46.45),(3.37,47.85),(28.63,47.85),(30.79,46.45),(31.13,44.39),
     (29.09,42.99),(2.91,42.99)]
prism('Angular top marquee casing',cap,5.00,8.70,'steel')
prism('Top dark sign inset',[(3.11,43.12),(28.89,43.12),(28.30,47.78),(3.70,47.78)],4.959,5.02,'black',back=False)
# The original wider artwork contains extra scenery above/below its central
# title. Crop UVs only to its centre half; preserve every source pixel on disk.
decal('HEROIC VERSE high marquee',(3.88,43.24,28.12,47.68),4.939,'marquee',(0,4,16,12),glow=True)
for right in (False,True):
    pts=[(1.69,44.78),(1.92,45.92),(3.01,46.70)]
    if right:pts=[(32-x,y) for x,y in pts]
    ribbon('Purple angular marquee end '+str(right),pts,.66,4.946,'violet',True)
    ribbon('Bright marquee end core '+str(right),pts,.26,4.930,'pink',True)
for x in (10.04,21.96):
    # A narrow ceiling light links the overhead speaker to its roof mount.
    face('Underside roof purple strip '+str(x),[(x-.09,43.980,6.00),(x+.09,43.980,6.00),
        (x+.09,43.980,12.30),(x-.09,43.980,12.30)],'violet',glow=True)


textures={key:'japanesearcades:block/beatmania_iidx_lightning_'+key for key in ('materials','controls','details','floor','turntable','display','marquee','banners')}
textures['particle']=textures['materials']
def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def obj(path,faces):
    lines=['# beatmania IIDX LIGHTNING MODEL efficient native cabinet, coordinates in blocks.',
           'mtllib japanesearcades:models/block/beatmania_iidx_lightning.mtl'];index=1;last=None
    for f in faces:
        material=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
        if material!=last:lines.append('usemtl '+material);last=material
        lines.extend('v '+' '.join('%.9f'%(v/16) for v in p) for p in f['vertices'])
        lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
        lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
        index+=len(f['vertices'])
    optimized,stats=optimize_obj('\n'.join(lines)+'\n')
    path.write_text(optimized,encoding='utf-8');return stats

def wrapper(name,item=False):
    model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name+'.obj',
           'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
           'ambientocclusion':not item,'render_type':'minecraft:solid','textures':textures}
    if item:model.update({'gui_light':'front','display':{
        'gui':{'rotation':[10,225,0],'translation':[0,-5.2,0],'scale':[.37,.37,.37]},
        'ground':{'translation':[0,0,0],'scale':[.20,.20,.20]},
        'fixed':{'rotation':[0,180,0],'translation':[0,-7,0],'scale':[.36,.36,.36]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,0,0],'scale':[.27,.27,.27]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,-3,0],'scale':[.35,.35,.35]}}})
    return model

sections={'cabinet_base':(0,0),'cabinet_console':(0,1),'cabinet_marquee':(0,2),'platform':(1,0)}
parts={side+'_'+section:[] for side in ('primary','secondary') for section in sections}
for f in surfaces:
    fragments=[list(zip(f['vertices'],f['uv']))]
    for axis,levels in ((0,[16]),(1,[16,32])):
        fragments=[piece for fragment in fragments for piece in pieces(fragment,axis,levels)]
    if f['group']=='Low standing platform':
        fragments=[piece for fragment in fragments for piece in pieces(fragment,2,[0])]
    for fragment in fragments:
        for poly in quads(fragment):
            center=[sum(p[k] for p,uv in poly)/len(poly) for k in range(3)]
            col=0 if center[0]<16 else 1;row=min(2,max(0,int(center[1]//16)))
            floor=f['group']=='Low standing platform' and center[2]<0
            section='platform' if floor else ('cabinet_base','cabinet_console','cabinet_marquee')[row]
            depth=1 if floor else 0;name=('primary_' if col==0 else 'secondary_')+section
            parts[name].append({**f,'vertices':[[p[0]-col*16,p[1]-row*16,p[2]+depth*16] for p,uv in poly],
                               'uv':[uv for p,uv in poly]})
stats={}
for part,faces in parts.items():
    name='block/beatmania_iidx_lightning_'+part
    stats[part]=obj(ASSETS/'models'/(name+'.obj'),faces)
    write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
item_meshes=[{**f,'vertices':[[(p[0]-16)*.30+8,p[1]*.30,p[2]*.30+8] for p in f['vertices']]} for f in surfaces]
stats['item']=obj(ASSETS/'models/item/beatmania_iidx_lightning.obj',item_meshes)
item=wrapper('item/beatmania_iidx_lightning',True)
item['display']={
    'gui':{'rotation':[15,225,0],'scale':[.95,.95,.95]},
    'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
    'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
    'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
    'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}
write_json(ASSETS/'models/item/beatmania_iidx_lightning.json',item)
mtl=[]
for key,glow in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
    mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/beatmania_iidx_lightning.mtl').write_text('\n'.join(mtl),encoding='utf-8')
variants={}
for direction,angle in (('north',0),('east',90),('south',180),('west',270)):
    for part in parts:
        side,section=part.split('_',1)
        variants['facing='+direction+',section='+section+',side='+side]={
            'model':'japanesearcades:block/beatmania_iidx_lightning_'+part,**({'y':angle} if angle else {})}
write_json(ASSETS/'blockstates/beatmania_iidx_lightning.json',{'variants':variants})
bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,
    'preview_textures':{'turntable':'art/beatmania-iidx-lightning/turntable-frame.png'},
    'statistics':{'authoring_faces':len(surfaces),'optimized':stats},
    'notes':'Two-wide eight-cell cabinet: six rear cabinet cells and two low standing platform cells. Elevated frontal overhangs remain in rear cabinet meshes. One native animated platter texture.'})


groups=defaultdict(list);elements=[]
assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
texture_keys=[key for key in textures if key!='particle']
texture_files={key:(ART/'turntable-frame.png' if key=='turntable' else TEX/('beatmania_iidx_lightning_'+key+'.png')) for key in texture_keys}
sizes={key:Image.open(path).size for key,path in texture_files.items()}
for f in surfaces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'beatmania_iidx_lightning/'+f['name']));key=f['texture'][1:]
    width,height=sizes[key];keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
        'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_keys.index(key)}},
        'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,key in enumerate(texture_keys):
    path=texture_files[key];width,height=sizes[key]
    bbtex.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'beatmania_iidx_lightning/'+key)),'width':width,'height':height,
        'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'beatmania-iidx-lightning.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'beatmania IIDX LIGHTNING MODEL','model_identifier':'beatmania_iidx_lightning','visible_box':[2,3,2],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'beatmania_iidx_lightning/group/'+name)),
                'origin':[16,0,0],'children':children} for name,children in groups.items()]})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])
print('beatmania IIDX LIGHTNING MODEL:',len(surfaces),'authoring faces; bounds',bounds)
print('Optimized native meshes:',stats)
