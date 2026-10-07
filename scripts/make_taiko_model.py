"""Native curved geometry for the classic lantern Taiko no Tatsujin cabinet.

The two tilted drumheads share exact hit-plane coordinates with the runtime.
Meshes are clipped into a two-wide, two-deep ten-cell multiblock with seamless
UV interpolation. Artwork is generated separately by taiko_textures.py.
"""
import base64
import argparse
import json
import math
import uuid
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw
from ddr_mesh_export import pieces, quads
from obj_mesh_optimizer import optimize_obj
from taiko_textures import build_textures

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/taiko'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
for path in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):
    path.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reuse-textures',action='store_true',help='Regenerate only geometry, preserving existing texture pixels.')
args=parser.parse_args()
if not args.reuse_textures:build_textures(TEX)

COLORS={'cream':'#ece0af','head':'#f0e4bc','rim':'#d9c996','orange':'#ac501c',
    'orange_light':'#c5732c','orange_dark':'#743710','wood':'#60331c','wood_light':'#996033',
    'gold':'#a37932','gold_light':'#c09a59','black':'#181615','dark':'#302824',
    'white':'#ebe9df','silver':'#aeb7b8','red':'#b3282f','lantern':'#fff0ce'}
KEYS=list(COLORS)
atlas=Image.new('RGB',(256,256));d=ImageDraw.Draw(atlas)
for i,col in enumerate(COLORS.values()):
    x,y=(i%4)*64,(i//4)*64;d.rectangle((x,y,x+63,y+63),fill=col)
if not args.reuse_textures:atlas.save(TEX/'taiko_materials.png')

surfaces=[];group='Cabinet'
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
def roundrect(x0,y0,x1,y1,r,n=3):
    r=min(r,(x1-x0)/2,(y1-y0)/2);out=[]
    for cx,cy,start in ((x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)):
        for i in range(n+1):
            a=math.radians(start+i*90/n);p=(cx+r*math.cos(a),cy+r*math.sin(a))
            if not out or math.dist(p,out[-1])>1e-8:out.append(p)
    if math.dist(out[0],out[-1])<1e-8:out.pop()
    return out
def prism(name,outline,z0,z1,material='white',glow=False,front=True,back=True):
    cx=sum(p[0] for p in outline)/len(outline);cy=sum(p[1] for p in outline)/len(outline)
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        if front:face(name+' front '+str(i),[(cx,cy,z0),(*q,z0),(*p,z0)],material,glow=glow)
        if back:face(name+' back '+str(i),[(cx,cy,z1),(*p,z1),(*q,z1)],material)
        face(name+' edge '+str(i),[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material)
def rounded(name,rect,z0,z1,r=.2,material='white',glow=False):
    prism(name,roundrect(*rect,r),z0,z1,material,glow)
def sculpted_prism(name,outline,z0,z1,material='wood'):
    """Ear-clip a concave carved saddle so there are no overlapping fan faces."""
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    remaining=list(range(len(outline)));triangles=[]
    while len(remaining)>3:
        found=False
        for j,index in enumerate(remaining):
            prev,next_=remaining[j-1],remaining[(j+1)%len(remaining)]
            a,b,c=outline[prev],outline[index],outline[next_]
            if cross(a,b,c)<=1e-10:continue
            if any(cross(a,b,outline[k])>=-1e-10 and cross(b,c,outline[k])>=-1e-10 and cross(c,a,outline[k])>=-1e-10
                   for k in remaining if k not in (prev,index,next_)):continue
            triangles.append((prev,index,next_));remaining.pop(j);found=True;break
        assert found,('Cannot triangulate saddle',name)
    triangles.append(tuple(remaining))
    for i,triangle in enumerate(triangles):
        face(name+' front '+str(i),[(*outline[k],z0) for k in reversed(triangle)],material)
        face(name+' back '+str(i),[(*outline[k],z1) for k in triangle],material)
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        face(name+' edge '+str(i),[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material)
def disc(name,x,y,r,z0,z1,material='silver',count=40,back=True):
    prism(name,[(x+r*math.cos(i*math.tau/count),y+r*math.sin(i*math.tau/count)) for i in range(count)],z0,z1,material,back=back)
def decal(name,rect,z,texture,region=(0,0,16,16),glow=False):
    x0,y0,x1,y1=rect;u0,v0,u1,v1=region
    face(name,[(x1,y1,z),(x1,y0,z),(x0,y0,z),(x0,y1,z)],texture=texture,
        uv=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)],glow=glow)
def ring(name,x,y,outer,inner,z,material,count=64):
    for i in range(count):
        a=i*math.tau/count;b=(i+1)*math.tau/count
        face(name+' '+str(i),[(x+outer*math.cos(a),y+outer*math.sin(a),z),
            (x+inner*math.cos(a),y+inner*math.sin(a),z),
            (x+inner*math.cos(b),y+inner*math.sin(b),z),
            (x+outer*math.cos(b),y+outer*math.sin(b),z)],material)
def tube(name,points,radius,material='dark',segments=8):
    for k,(a,b) in enumerate(zip(points,points[1:])):
        vec=[b[i]-a[i] for i in range(3)];length=math.sqrt(sum(v*v for v in vec));n=[v/length for v in vec]
        ref=(0,1,0) if abs(n[1])<.9 else (1,0,0)
        u=[n[1]*ref[2]-n[2]*ref[1],n[2]*ref[0]-n[0]*ref[2],n[0]*ref[1]-n[1]*ref[0]]
        size=math.sqrt(sum(v*v for v in u));u=[v/size for v in u]
        v=[n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0]]
        def pt(center,angle):return [center[i]+radius*(u[i]*math.cos(angle)+v[i]*math.sin(angle)) for i in range(3)]
        for j in range(segments):
            t=j*math.tau/segments;s=(j+1)*math.tau/segments
            face(name+' %d %d'%(k,j),[pt(a,t),pt(a,s),pt(b,s),pt(b,t)],material)

# White upright rear cabinet, recessed bronze console, and broad marquee.
rounded('Lower rear white cabinet',(1.0,.65,31.0,20.10),1.50,14.75,.40,'white')
rounded('Upper white cabinet backing',(1.0,19.95,31.0,39.55),8.40,14.75,.40,'white')
for x in (1.0,30.70):box('Upper white cabinet side wall '+str(x),(x,19.97,1.52),(x+.30,39.53,14.64),'white')
rounded('Rear charcoal plinth',(1.13,.25,30.87,1.08),1.35,14.55,.20,'black')
rounded('Console recessed bronze back wall',(1.38,20.05,30.62,39.45),7.18,8.43,.28,'gold')
rounded('Deep black CRT bezel',(7.63,24.95,24.37,38.22),1.18,2.8,.34,'dark')
rounded('Recessed CRT glass outer edge',(8.22,26.63,23.78,38.04),1.135,1.20,.30,'black')
decal('Festival CRT screen',(8.50,27.0,23.50,37.78),1.119,'screen',glow=True)
rounded('CRT bottom control plate',(7.88,25.03,24.12,26.71),1.11,1.19,.11,'dark')
box('CRT warning white label',(13.13,25.32,1.09),(18.87,25.94,1.13),'cream')
for i in range(5):box('Warning tiny line '+str(i),(14.3,25.40+i*.095,1.075),(18.44,25.43+i*.095,1.10),'silver')
box('Warning yellow square',(13.32,25.45,1.074),(14.12,25.80,1.10),'gold_light')
rounded('Top instruction silver strip',(7.88,38.06,24.12,39.56),1.115,1.23,.10,'gold_light')
decal('How to play instruction strip',(8.06,38.18,23.94,39.40),1.097,'instructions')
for x in (1.14,6.95,24.12,29.88):rounded('Bronze side column '+str(x),(x,20.11,x+.92,39.43),.96,1.6,.12,'gold')
for x in (1.38,24.74):
    rounded('Upper lantern ledge '+str(x),(x,38.69,x+5.88,39.72),.50,4.34,.12,'gold_light')
    rounded('Lantern lower ledge '+str(x),(x,28.19,x+5.88,28.85),.54,4.25,.12,'gold_light')
    rounded('Lower speaker recess '+str(x),(x+.46,21.00,x+5.42,27.92),1.067,1.30,.13,'dark')
    rounded('Lower speaker grille '+str(x),(x+.80,21.41,x+5.07,27.57),1.051,1.11,.10,'black')
    for row in range(10):box('Speaker vent %s %s'%(x,row),(x+1.02,21.77+row*.54,1.039),(x+4.82,21.86+row*.54,1.074),'dark')
rounded('Marquee red enclosure',(.30,39.60,31.70,48.0),1.36,5.1,.15,'red')
rounded('Marquee slim inner bronze lip',(.64,39.90,31.36,47.69),1.18,1.41,.10,'gold_light')
decal('Taiko no Tatsujin festival marquee',(.88,40.13,31.12,47.45),1.164,'marquee',glow=True)
box('Marquee upper red edge',(.32,47.72,1.11),(31.68,47.96,5.12),'red')

group='Festival cabinet art'
for x,side in ((.979,'left'),(31.021,'right')):
    pts=[(x,37.80,14.25),(x,1.37,14.25),(x,1.37,2.04),(x,37.80,2.04)]
    uvs=[(0,0),(0,16),(16,16),(16,0)]
    if side=='left':
        uvs=[(16-u,v) for u,v in uvs]
        pts.reverse();uvs.reverse()
    face('Tall festival side art '+side,pts,texture='side',uv=uvs)
for x in (1.2,30.45):box('Side red rear trim '+str(x),(x,1.23,14.55),(x+.35,39.53,14.92),'red')
rounded('Rear service back panel',(2.12,2.4,29.88,37.85),14.76,14.87,.16,'ivory' if 'ivory' in COLORS else 'white')
for i in range(8):box('Rear ventilation '+str(i),(10.22,28.1+i*.42,14.884),(21.78,28.24+i*.42,14.93),'silver')
rounded('White front center speaker plate',(12.70,15.68,19.30,23.17),1.13,1.30,.15,'silver')
for row in range(16):box('Center front ventilation '+str(row),(13.19,16.02+row*.40,1.11),(18.81,16.15+row*.40,1.15),'dark')

group='Ribbed festival lanterns'
lantern_profile=[(-4.10,1.14),(-3.84,1.84),(-3.26,2.45),(-2.54,2.82),(-1.62,3.04),(0,3.14),
    (1.62,3.04),(2.54,2.82),(3.26,2.45),(3.84,1.84),(4.10,1.14)]
def lantern_radius(y):
    for (a,ra),(b,rb) in zip(lantern_profile,lantern_profile[1:]):
        if a<=y<=b:return ra+(rb-ra)*(y-a)/(b-a)
    return 1.14
def vertical_lathe(name,cx,cy,cz,profile,material='lantern',count=48,glow=False):
    for k,((y,r),(Y,R)) in enumerate(zip(profile,profile[1:])):
        for i in range(count):
            a=i*math.tau/count;b=(i+1)*math.tau/count
            # The ring winds around the Y axis with outward radial normals.
            face(name+' %d %d'%(k,i),[(cx+r*math.cos(a),cy+y,cz+r*math.sin(a)),
                (cx+R*math.cos(a),cy+Y,cz+R*math.sin(a)),
                (cx+R*math.cos(b),cy+Y,cz+R*math.sin(b)),
                (cx+r*math.cos(b),cy+y,cz+r*math.sin(b))],material,glow=glow)
for cx in (4.25,27.75):
    cy,cz=33.65,3.80
    # A 32-sided circumference still deviates by less than .016 model units
    # from a circle. Keep all 19 physical ribs and the exact vertical profile.
    vertical_lathe('Lantern paper body '+str(cx),cx,cy,cz,lantern_profile,'lantern',32,True)
    for j in range(19):
        y=-3.82+j*.423;r=lantern_radius(y)
        # The illuminated paper ribs share the lantern's fullbright treatment.
        # Shaded ribs on an emissive body become black scanlines in dim worlds.
        vertical_lathe('Lantern raised rib %s %d'%(cx,j),cx,cy,cz,[(y-.055,r+.018),(y,r+.09),(y+.055,r+.018)],'cream',32,True)
    for low,high in ((-4.55,-4.05),(4.05,4.53)):
        vertical_lathe('Red lantern cap %s %s'%(cx,low),cx,cy,cz,[(low,1.12),(low+.08,1.23),(high-.08,1.23),(high,1.12)],'red',32)
    # Curved crest follows the lantern instead of floating on a flat sticker.
    count=12;radius=2.40
    for row in range(count):
        for col in range(count):
            x=-radius+2*radius*col/count;X=-radius+2*radius*(col+1)/count
            y=-radius+2*radius*row/count;Y=-radius+2*radius*(row+1)/count
            def pt(x,y):return (cx+x,cy+y,cz-math.sqrt(max(.01,lantern_radius(y)**2-x*x))-.106)
            face('Red curved lantern crest %s %d %d'%(cx,row,col),[pt(X,Y),pt(X,y),pt(x,y),pt(x,Y)],
                texture='lantern',uv=[(16*(1-(col+1)/count),16*(1-(row+1)/count)),(16*(1-(col+1)/count),16*(1-row/count)),
                (16*(1-col/count),16*(1-row/count)),(16*(1-col/count),16*(1-(row+1)/count))],glow=True)

group='Two-player decorated podium'
rounded('Podium red body',(.55,.80,31.45,13.73),-15.06,4.8,.24,'red')
rounded('Podium front printed face',(.90,1.18,31.10,12.96),-15.121,-15.055,.12,'white')
decal('Orange floral player podium wrap',(.93,1.21,31.07,12.93),-15.133,'front')
for x,left in ((.529,True),(31.471,False)):
    pts=[(x,13.29,4.62),(x,1.16,4.62),(x,1.16,-14.90),(x,13.29,-14.90)]
    uvs=[(0,0),(0,16),(16,16),(16,0)]
    if left:
        uvs=[(16-u,v) for u,v in uvs];pts.reverse();uvs.reverse()
    face('Decorated lower podium side '+str(left),pts,texture='podium_side',uv=uvs)
box('Podium black drum mounting top',(.58,13.58,-15.07),(31.42,13.95,4.83),'black')
box('Podium slim silver front edge',(.58,13.34,-15.19),(31.42,13.60,-14.78),'silver')
for x in (.66,30.95):box('Podium white corner rail '+str(x),(x,.88,-15.18),(x+.40,13.53,-14.92),'white')
for x in (2.38,28.36):
    box('Wheel bracket '+str(x),(x,.32,-12.11),(x+1.3,.88,-10.68),'silver')
    box('Caster foot '+str(x),(x+.12,.05,-12.2),(x+1.18,.44,-10.62),'dark')
rounded('Cream coin-door backing',(12.41,1.15,19.59,12.97),-15.182,-15.10,.23,'cream')
rounded('Black center coin door',(13.10,2.13,18.90,11.81),-15.239,-15.17,.46,'black')
rounded('Coin upper door inset',(13.38,6.71,18.62,11.50),-15.266,-15.23,.31,'dark')
rounded('Coin lower door inset',(13.38,2.45,18.62,6.31),-15.266,-15.23,.31,'dark')
rounded('Center contactless card label',(14.55,8.35,17.45,10.66),-15.285,-15.26,.12,'white')
disc('Contactless reader mark',16,9.50,.55,-15.295,-15.285,'dark',24)
ring('Contactless ring',16,9.50,.44,.34,-15.301,'white',32)
box('Coin center metal slot',(15.18,7.32,-15.292),(16.82,7.66,-15.27),'silver')
for y in (3.32,10.91):disc('Door lock '+str(y),13.95,y,.20,-15.29,-15.26,'silver',24)

# Drums are authored in their own circular local coordinates, then transformed
# into the exact tilted plane used for drumhead/rim interaction tests.
SIN,COS=math.sin(math.radians(35)),math.cos(math.radians(35))
def outward_yaw(start,center_x):
    """Splay each complete drum/stand outward around its unchanged hit center."""
    angle=math.radians(8 if center_x<16 else -8);c,s=math.cos(angle),math.sin(angle)
    for f in surfaces[start:]:
        for p in f['vertices']:
            dx,dz=p[0]-center_x,p[2]+9
            p[0]=center_x+dx*c+dz*s;p[2]=-9-dx*s+dz*c
for center_x in (8.0,24.0):
    group='Drum %d'%center_x;start=len(surfaces)
    profiles=[(.20,6.62),(.83,6.73),(2.25,6.96),(4.0,7.05),(5.72,6.83),(7.1,6.42),(8.0,5.86)]
    for k,((z,r),(Z,R)) in enumerate(zip(profiles,profiles[1:])):
        for i in range(64):
            a=i*math.tau/64;b=(i+1)*math.tau/64
            material='orange'
            face('Curved wood barrel %s %d %d'%(center_x,k,i),[(r*math.cos(a),r*math.sin(a),z),
                (r*math.cos(b),r*math.sin(b),z),(R*math.cos(b),R*math.sin(b),Z),(R*math.cos(a),R*math.sin(a),Z)],material)
    disc('Back cream drum membrane '+str(center_x),0,0,5.88,7.96,8.09,'rim',64)
    disc('Black rear barrel hoop '+str(center_x),0,0,6.02,7.70,7.84,'black',64)
    disc('Thick cream head skirt '+str(center_x),0,0,6.80,.015,.65,'rim',64)
    ring('Cream raised front rim '+str(center_x),0,0,6.80,6.10,-.055,'cream',64)
    # Slightly crowned unprinted skin; center and edge remain cream.
    for i in range(64):
        a=i*math.tau/64;b=(i+1)*math.tau/64
        face('Unprinted cream drumhead %s %d'%(center_x,i),[(0,0,-.105),(6.1*math.cos(b),6.1*math.sin(b),-.06),(6.1*math.cos(a),6.1*math.sin(a),-.06)],'head')
    for i in range(40):
        a=i*math.tau/40
        # The rear cap is buried inside the cream rim. Eight sides are ample
        # for these .085-unit studs; their count, positions and radii are unchanged.
        disc('Black rim tack %s %d'%(center_x,i),6.57*math.cos(a),6.57*math.sin(a),.085,-.064,-.044,'black',8,back=False)
    for i in range(8):
        a=i*math.tau/8
        x,y=6.53*math.cos(a),6.53*math.sin(a)
        disc('Rim silver latch %s %d'%(center_x,i),x,y,.16,-.076,-.049,'silver',10,back=False)
    # Black iron side grips on the barrel, just behind the head.
    for sx in (-1,1):
        box('Iron barrel side mount %s %s'%(center_x,sx),(sx*6.93-.10,-.64,3.45),(sx*6.93+.10,.64,4.99),'black')
        tube('Side grip %s %s'%(center_x,sx),[(sx*6.98,-.49,3.74),(sx*7.11,-.49,4.08),(sx*7.11,.49,4.08),(sx*6.98,.49,3.74)],.13,'dark',8)
    for f in surfaces[start:]:
        for p in f['vertices']:
            x,y,z=p;p[:]=[center_x+x,24+y*COS-z*SIN,-9+y*SIN+z*COS]
    outward_yaw(start,center_x)

group='Carved wooden drum cradles'
for cx in (8.0,24.0):
    start=len(surfaces)
    # Front and rear decorated saddle plates with low center and tall horns.
    outline=[(cx-6.7,14.05),(cx+6.7,14.05),(cx+6.55,14.88),(cx+5.48,15.13),
        (cx+5.77,16.14),(cx+5.15,17.35),(cx+4.50,16.91),(cx+3.57,15.49),
        (cx+2.14,14.90),(cx-2.14,14.90),(cx-3.57,15.49),(cx-4.50,16.91),
        (cx-5.15,17.35),(cx-5.77,16.14),(cx-5.48,15.13),(cx-6.55,14.88)]
    rounded('Cradle solid foot '+str(cx),(cx-6.60,13.96,cx+6.60,14.62),-10.40,-1.0,.12,'wood')
    for z in (-10.48,-2.45):
        sculpted_prism('Carved saddle crossbeam %s %s'%(cx,z),outline,z,z+.73,'wood')
        for sx in (-1,1):
            # Ornamental hook curves, raised in relief on the front-facing wood.
            px=cx+sx*5.1
            disc('Cradle spiral backing %s %s %s'%(cx,z,sx),px,15.84,.93,z-.025,z+.58,'wood',24)
            ring('Cradle scroll rim %s %s %s'%(cx,z,sx),px,15.84,.73,.57,z-.043,'wood_light',24)
            ring('Cradle scroll inner %s %s %s'%(cx,z,sx),px,15.84,.44,.29,z-.051,'gold',24)
            disc('Cradle scroll center %s %s %s'%(cx,z,sx),px,15.84,.18,z-.055,z-.028,'wood_light',12)
        disc('Cradle flower boss %s %s'%(cx,z),cx,15.05,.66,z-.065,z+.60,'wood_light',24)
        ring('Cradle flower outline %s %s'%(cx,z),cx,15.05,.49,.37,z-.078,'wood',24)
        for j in range(8):
            a=j*math.tau/8
            # Each petal's back is entirely inside the round wooden flower boss.
            disc('Cradle flower petal %s %s %d'%(cx,z,j),cx+.40*math.cos(a),15.05+.40*math.sin(a),.16,z-.08,z-.064,'gold',8,back=False)
    for sx in (-1,1):
        box('Cradle raised drum rest %s %s'%(cx,sx),(cx+sx*4.6-.55,14.95,-5.23),(cx+sx*4.6+.55,17.0,-3.31),'wood')
    outward_yaw(start,cx)

group='Tethered wooden drumsticks'
for cx in (8.0,24.0):
    rounded('Stick holder metal backing '+str(cx),(cx-1.49,8.24,cx+1.49,13.41),-15.34,-15.14,.13,'silver')
    rounded('Stick holder fabric pocket '+str(cx),(cx-1.31,5.34,cx+1.31,11.48),-15.50,-15.35,.34,'dark')
    for k,offset in enumerate((-.60,.60)):
        x=cx+offset
        tube('Wooden drumstick %s %d'%(cx,k),[(x,6.92,-15.57),(x+offset*.12,13.13,-15.40)],.22,'wood_light',12)
        tube('Black grip on drumstick %s %d'%(cx,k),[(x,7.19,-15.588),(x+offset*.04,9.52,-15.52)],.245,'black',12)
        pts=[]
        for j in range(25):
            t=j/24
            pts.append((x+math.sin(t*math.pi)*(.75 if k==0 else -.75),12.27-9.07*math.sin(t*math.pi),-15.73+.08*math.sin(t*math.pi*2)))
        tube('Hanging red tether %s %d'%(cx,k),pts,.055,'red',7)

def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
textures={key:'japanesearcades:block/taiko_'+key for key in ('materials','marquee','screen','front','instructions','side','lantern','podium_side')}
textures['particle']=textures['materials']
export_statistics={}
def write_obj(path,faces,transform):
    out=['# Classic lantern Taiko cabinet. Coordinates in blocks.','mtllib japanesearcades:models/block/taiko.mtl'];idx=1;last=None
    for f in faces:
        mat=f['texture'][1:]+('_lit' if f['glow'] else '_surface')
        if mat!=last:out.append('usemtl '+mat);last=mat
        out.extend('v '+' '.join('%.9f'%v for v in transform(p)) for p in f['vertices'])
        out.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
        out.append('f '+' '.join('%d/%d'%(idx+i,idx+i) for i in range(len(f['vertices']))));idx+=len(f['vertices'])
    # Keep the per-cabinet generator reproducible without rewriting other models.
    optimized,audit=optimize_obj('\n'.join(out)+'\n')
    assert not audit.get('skipped'),(path,audit)
    path.write_text(optimized,encoding='utf-8')
    export_statistics[path.relative_to(ASSETS).as_posix()]=audit
def wrapper(name):return {'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name,
    'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':True,
    'render_type':'minecraft:cutout_mipped_all','textures':textures}
sections={'rear_base':(0,0),'rear_console':(0,1),'rear_marquee':(0,2),'drum_base':(1,0),'drums':(1,1)}
parts={side+'_'+part:[] for side in ('primary','secondary') for part in sections}
for f in surfaces:
    poly=list(zip(f['vertices'],f['uv']))
    fragments=[poly]
    for axis,levels in ((0,[16]),(1,[16,32]),(2,[0])):
        fragments=[part for fragment in fragments for part in pieces(fragment,axis,levels)]
    for fragment in fragments:
        for q in quads(fragment):
            center=[sum(p[k] for p,uv in q)/len(q) for k in range(3)]
            col=0 if center[0]<16 else 1;row=min(2,int(center[1]//16));depth=1 if center[2]<0 else 0
            assert depth==0 or row<2,('Front geometry above 32',f['name'])
            section=('rear_base','rear_console','rear_marquee')[row] if depth==0 else ('drum_base','drums')[row]
            key=('primary_' if col==0 else 'secondary_')+section
            parts[key].append({**f,'vertices':[p for p,uv in q],'uv':[uv for p,uv in q]})
for name,faces in parts.items():
    side,section=name.split('_',1);col=0 if side=='primary' else 1;depth,row=sections[section]
    path='block/taiko_'+name
    write_obj(ASSETS/'models'/(path+'.obj'),faces,lambda p,col=col,row=row,depth=depth:[(p[0]-16*col)/16,(p[1]-16*row)/16,(p[2]+16*depth)/16])
    write_json(ASSETS/'models'/(path+'.json'),wrapper(path+'.obj'))
mtl=[]
for tex,lit in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
    mtl.extend(['newmtl '+tex+('_lit' if lit else '_surface'),'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1','map_Kd #'+tex,''])
(ASSETS/'models/block/taiko.mtl').write_text('\n'.join(mtl),encoding='utf-8')
variants={}
for direction,angle in (('north',0),('east',90),('south',180),('west',270)):
    for name in parts:
        side,section=name.split('_',1)
        variants['facing='+direction+',section='+section+',side='+side]={'model':'japanesearcades:block/taiko_'+name,**({'y':angle} if angle else {})}
write_json(ASSETS/'blockstates/taiko.json',{'variants':variants})
write_obj(ASSETS/'models/item/taiko.obj',surfaces,lambda p:[((p[0]-16)*.31+8)/16,p[1]*.31/16,(p[2]*.31+8)/16])
item=wrapper('item/taiko.obj');item.update({'ambientocclusion':False,'gui_light':'front','display':{
    'gui':{'rotation':[15,225,0],'scale':[.95,.95,.95]},'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
    'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
    'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
write_json(ASSETS/'models/item/taiko.json',item)
stats={'source_faces':len(surfaces),'authored_section_faces':{key:len(value) for key,value in parts.items()},
    'runtime_section_faces':{key:export_statistics['models/block/taiko_'+key+'.obj']['output_faces'] for key in parts},
    'item_faces':export_statistics['models/item/taiko.obj']['output_faces']}
bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
YAW=math.radians(8)
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,'statistics':stats,
    'drum_hit_geometry':{'centers':[[8,24,-9],[24,24,-9]],'elevation_degrees':35,'outward_yaw_degrees':8,
        'normals':[[-COS*math.sin(YAW),SIN,-COS*math.cos(YAW)],[COS*math.sin(YAW),SIN,-COS*math.cos(YAW)]],
        'across_axes':[[math.cos(YAW),0,-math.sin(YAW)],[math.cos(YAW),0,math.sin(YAW)]],
        'head_radius':6.1,'rim_radius':6.8}})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    assert all(-1e-8<=p[0]<=32+1e-8 and -1e-8<=p[1]<=48+1e-8 and -16<=p[2]<=16 for p in f['vertices']),(f['name'],f['vertices'])
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])

# Export editable embedded-texture Blockbench project once the parallel art
# generator has supplied its finished textures. Runtime meshes are usable first.
if all((TEX/(value.split('/')[-1]+'.png')).exists() for key,value in textures.items() if key!='particle'):
    specs=[(key,TEX/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indices={'#'+key:i for i,(key,path) in enumerate(specs)};sizes=[Image.open(path).size for key,path in specs]
    groups=defaultdict(list);elements=[]
    assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
    for f in surfaces:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'taiko/'+f['name']));index=indices[f['texture']];w,h=sizes[index];keys=['v'+str(i) for i in range(len(f['vertices']))]
        elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':index}},'visibility':True,'export':True})
        groups[f['group']].append(uid)
    texdata=[]
    for i,(key,path) in enumerate(specs):
        w,h=sizes[i];texdata.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'taiko/'+key)),'width':w,'height':h,'uv_width':w,'uv_height':h,
            'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(ART/'taiko.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':'Classic Lantern Taiko no Tatsujin',
        'model_identifier':'taiko','visible_box':[2,3,2],'resolution':{'width':256,'height':256},'elements':elements,'textures':texdata,
        'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'taiko/group/'+name)),'origin':[16,0,0],'children':children} for name,children in groups.items()]})
print('Taiko native meshes exported:',stats,'bounds:',bounds)
