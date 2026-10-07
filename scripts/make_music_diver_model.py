"""Export MUSIC DIVER as a static three-block NeoForge OBJ cabinet.

The lower play circle, four strike pads, retaining brackets, rectangular
status screen and trim all share a single 42-degree sloping deck plane.
The upright topper is a separate layered four-sector acrylic assembly.
"""
from __future__ import annotations
import base64
from collections import defaultdict
import json
import math
from pathlib import Path
import uuid
from PIL import Image
from ddr_mesh_export import pieces,quads
from obj_mesh_optimizer import optimize_obj
from music_diver_textures import generate
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/music-diver'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
for path in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):
    path.mkdir(parents=True,exist_ok=True)
COLORS=generate()
KEYS=list(COLORS)

surfaces=[]
group='Cabinet'

def tile(material):
    i=KEYS.index(material);u=i%4*4;v=i//4*4
    return [(u+1,v+1),(u+1,v+3),(u+3,v+3),(u+3,v+1)]

def face(name,points,material='white',texture='materials',uv=None,glow=False):
    coordinates=uv or tile(material)[:len(points)]
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

def disc(name,cx,cy,z,r,texture,segments=40,glow=False):
    def uv(x,y):return [8-(x-cx)/r*8,8-(y-cy)/r*8]
    for i in range(segments):
        a,b=math.tau*i/segments,math.tau*(i+1)/segments
        points=[(cx,cy,z),(cx+r*math.cos(b),cy+r*math.sin(b),z),(cx+r*math.cos(a),cy+r*math.sin(a),z)]
        face(name+' '+str(i),points,texture=texture,uv=[uv(x,y) for x,y,z in points],glow=glow)

def annular_sector(name,cx,cy,inner,outer,a0,a1,z0,z1,material='black',steps=10,
                   front_texture=None,glow=False,uv_radius=None,back=True):
    """A real thick curved panel, with a single faceted convex quad per step."""
    for i in range(steps):
        a=math.radians(a0+(a1-a0)*i/steps);b=math.radians(a0+(a1-a0)*(i+1)/steps)
        point=lambda r,t,z:(cx+r*math.cos(t),cy+r*math.sin(t),z)
        front=[point(inner,a,z0),point(inner,b,z0),point(outer,b,z0),point(outer,a,z0)]
        if front_texture:
            rr=uv_radius or outer
            uv=[[8-(p[0]-cx)/rr*8,8-(p[1]-cy)/rr*8] for p in front]
            face(name+' front '+str(i),front,texture=front_texture,uv=uv,glow=glow)
        else:face(name+' front '+str(i),front,material,glow=glow)
        if z0!=z1:
            face(name+' outer '+str(i),[point(outer,a,z0),point(outer,b,z0),point(outer,b,z1),point(outer,a,z1)],material)
            face(name+' inner '+str(i),[point(inner,b,z0),point(inner,a,z0),point(inner,a,z1),point(inner,b,z1)],material)
            if back:face(name+' back '+str(i),list(reversed([point(inner,a,z1),point(inner,b,z1),point(outer,b,z1),point(outer,a,z1)])),material)
    for angle,reverse in ((a0,False),(a1,True)):
        if z0==z1:continue
        t=math.radians(angle);pts=[(cx+inner*math.cos(t),cy+inner*math.sin(t),z0),(cx+outer*math.cos(t),cy+outer*math.sin(t),z0),
                                (cx+outer*math.cos(t),cy+outer*math.sin(t),z1),(cx+inner*math.cos(t),cy+inner*math.sin(t),z1)]
        face(name+' end '+str(angle),list(reversed(pts)) if reverse else pts,material)

# Exact shared deck transform. Local X,Y is the rectangular inclined plane;
# local negative Z is outward toward the player's eyes, never into the body.
DECK_ANGLE=math.radians(42)
def deck_point(x,y,z):
    return [8+x,22.05+y*math.sin(DECK_ANGLE)-z*math.cos(DECK_ANGLE),
            5.4+y*math.cos(DECK_ANGLE)+z*math.sin(DECK_ANGLE)]
def deck_since(start):
    for f in surfaces[start:]:f['vertices']=[deck_point(*p) for p in f['vertices']]
def radial_box(name,r0,r1,width,angle,z0,z1,material):
    start=len(surfaces);box(name,(r0,-width/2,z0),(r1,width/2,z1),material)
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    for f in surfaces[start:]:
        for p in f['vertices']:p[0],p[1]=p[0]*c-p[1]*s,p[0]*s+p[1]*c

group='White wedge cabinet and casters'
box('Black recessed cabinet foot',(.43,.55,.37),(15.57,1.33,15.55),'rubber')
# Each small wheel is an eight-sided cylinder in its side plane.
for x in (1.24,14.76):
    for z in (1.20,14.55):
        start=len(surfaces)
        prism('Caster %.2f %.2f'%(x,z),[(.48*math.cos(i*math.tau/8),.48*math.sin(i*math.tau/8)) for i in range(8)],-.22,.22,'steel')
        for f in surfaces[start:]:f['vertices']=[[x+p[2],.5+p[1],z+p[0]] for p in reversed(f['vertices'])];f['uv'].reverse()
        box('Caster bracket %.2f %.2f'%(x,z),(x-.35,.67,z-.53),(x+.35,1.16,z+.53),'silver')
body_profile=[(.02,1.15),(15.75,1.15),(15.75,30.73),(-.42,16.17)]
side_prism('Solid white continuous wedge body',body_profile,.20,15.80,'white')
box('Rear structural mast',(1.04,25.80,15.20),(14.96,36.60,15.55),'white')
box('Rear service door',(3.44,6.23,15.767),(12.56,22.84,15.807),'cream',('north',))
box('Rear door handle',(11.37,13.60,15.80),(11.67,15.40,15.93),'steel')
for y in (3.48,23.64):
    face('Rear cooling grille '+str(y),[(5.2,y,15.81),(10.8,y,15.81),(10.8,y+1.35,15.81),(5.2,y+1.35,15.81)],
         texture='details',uv=[(0,16),(8,16),(8,8),(0,8)])

group='Triangular black side graphics'
for right in (False,True):
    x=15.819 if right else .181
    # The side print is bounded by the actual wedge, leaving a broad white
    # triangle towards the back and the diagonal MUSIC DIVER wordmark.
    points=[(x,2.1,1.05),(x,3.0,7.34),(x,27.98,14.80),(x,16.3,1.20)]
    face('Black wedge side graphic '+str(right),list(reversed(points)) if right else points,'black')
    # Local rectangle axis follows the rising rearward diagonal of the side.
    z0,y0=3.84,3.66;z1,y1=12.96,26.00;dz,dy=z1-z0,y1-y0;length=math.hypot(dz,dy)
    nz,ny=-dy/length*1.23,dz/length*1.23
    xx=x+(.025 if right else -.025)
    pp=[(xx,y0+ny,z0+nz),(xx,y0-ny,z0-nz),(xx,y1-ny,z1-nz),(xx,y1+ny,z1+nz)]
    # Mirrored physical sides keep readable words from both viewpoints.
    coords=[(0,16),(16,16),(16,0),(0,0)]
    face('Diagonal MUSIC DIVER side wordmark '+str(right),list(reversed(pp)) if right else pp,texture='side',
         uv=list(reversed(coords)) if right else coords)
    pp=[(x,6.0,12.65),(x,6.0,14.76),(x,8.5,14.76),(x,8.5,12.65)]
    face('Side service vent '+str(right),list(reversed(pp)) if right else pp,texture='details',
         uv=[(0,8),(8,8),(8,16),(0,16)] if right else [(0,16),(8,16),(8,8),(0,8)])

group='Front doors reader and stick holster'
front_start=len(surfaces)
box('White front service fascia',(.40,1.50,-.46),(15.60,14.88,.20),'white')
for x0,x1,y0,y1 in ((1.00,9.22,2.05,13.66),(10.08,14.70,2.05,7.10),(10.08,14.70,8.03,13.66)):
    box('Door fine shadow %.2f %.2f'%(x0,y0),(x0,y0,-.489),(x1,y1,-.450),'edge',('south',))
    box('Door white inset %.2f %.2f'%(x0,y0),(x0+.10,y0+.10,-.515),(x1-.10,y1-.10,-.487),'white',('south',))
    box('Door silver lock %.2f %.2f'%(x0,y0),(x0+.69,y1-.95,-.595),(x0+.93,y1-.55,-.51),'steel')
box('Coin acceptor white bezel',(11.57,9.03,-.66),(14.10,13.30,-.51),'cream')
box('Coin acceptor black face',(12.10,9.35,-.699),(13.70,13.01,-.651),'black',('south',))
box('Coin narrow slot',(12.46,11.85,-.723),(13.24,12.03,-.692),'rubber')
box('Coin small yellow label',(12.58,11.12,-.726),(13.10,11.38,-.70),'cream',('south',))
box('Instruction console dark body',(1.90,13.60,-1.35),(12.08,16.22,-.44),'black')
decal('Front control and NESiCA cyan display',(2.09,13.76,11.91,16.08),-1.372,'details',(8,0,16,8),glow=False)
# Crop the same printed reader pixels onto the luminous face, preserving their
# registration with the surrounding instruction panel after its front mirror.
decal('Cyan reader luminous inset',
      (2.09+(778-512)/512*9.82,16.08-343/512*2.32,
       2.09+(995-512)/512*9.82,16.08-189/512*2.32),
      -1.39,'details',(778/64,189/64,995/64,343/64),glow=True)
box('Front left long stick holster black outer',(-.72,5.06,-2.19),(1.78,16.35,-.66),'black')
box('Stick holster brushed silver front',(-.53,5.20,-2.225),(1.49,15.51,-2.192),'silver',('south',))
box('Stick holster left chrome edge',(-.72,5.12,-2.27),(-.55,15.78,-2.18),'steel')
box('Stick holster right black edge',(1.47,5.12,-2.27),(1.75,15.78,-2.18),'rubber')
box('Stick holster open dark recess',(-.55,15.52,-2.13),(1.57,16.38,-.72),'rubber')
for i,x in enumerate((.06,.85)):
    box('Held drumstick shaft '+str(i),(x-.105,15.89,-1.51),(x+.105,18.03,-1.30),'silver')
    box('Held drumstick grip '+str(i),(x-.14,15.79,-1.57),(x+.14,16.91,-1.25),'black')
    box('Held drumstick pink tip '+str(i),(x-.15,18.00,-1.57),(x+.15,18.41,-1.25),'pink')
for f in surfaces[front_start:]:
    f['vertices']=[[16-x,y,z] for x,y,z in reversed(f['vertices'])]
    f['uv'].reverse()
    # Mirror manufactured front parts, while keeping their printed UI text
    # upright and readable in the same native front-view convention.
    if f['texture']=='#details':
        lo=min(u for u,v in f['uv']);hi=max(u for u,v in f['uv'])
        f['uv']=[[lo+hi-u,v] for u,v in f['uv']]

group='Continuous forty-two degree illuminated deck'
start=len(surfaces)
outline=[(-8.88,-8.53),(-9.14,-7.84),(-8.71,9.08),(-7.80,12.64),(7.80,12.64),(8.71,9.08),(9.14,-7.84),(8.88,-8.53)]
prism('Thick black sloping deck tray',outline,-.10,.60,'black')
inner=[(x*.98,y*.992) for x,y in outline]
before=len(surfaces);prism('Pink printed acrylic deck surround',inner,-.18,-.105,'pink',back=False)
for f in surfaces[before:]:
    if ' front ' in f['name']:
        f['texture']='#circuit';f['uv']=[[(9.15-p[0])/18.3*16,(12.7-p[1])/21.3*16] for p in f['vertices']]
for side in (-1,1):
    path=[(side*8.70,-8.06),(side*8.91,-7.66),(side*8.48,8.90),(side*7.57,12.25)]
    ribbon('Hot pink outer deck lamp '+str(side),path,.20,-.24,'pink',True)
    ribbon('Fine cyan white deck lamp '+str(side),[(x-side*.21,y) for x,y in path],.055,-.255,'cream',True)
for x in (-8.4,8.4):
    for y in (-7.6,7.0):box('Deck acrylic retaining screw %.1f %.1f'%(x,y),(x-.095,y-.095,-.29),(x+.095,y+.095,-.18),'silver')
deck_since(start)

group='Inclined circular play screen and four strike pads'
start=len(surfaces)
front_ring('Round console black lower shell',0,0,0,[(9.02,-.26,'black',False),(8.94,-.45,'pink',True),
    (8.76,-.65,'violet',True),(8.54,-.69,'black',False),(7.08,-.69,'black',False)],48)
disc('Circular gameplay screen',0,0,-.73,7.06,'display',48,True)
front_ring('Fine blue glass perimeter',0,0,0,[(7.13,-.742,'cyan',True),(7.03,-.748,'black',False)],48)
for sector,center in enumerate((0,90,180,270)):
    a0,a1=center-37.5,center+37.5
    annular_sector('Strike pad %d black housing'%sector,0,0,7.01,8.89,a0,a1,-1.27,-.50,'black',12)
    annular_sector('Strike pad %d charcoal top'%sector,0,0,7.24,8.70,a0+1,a1-1,-1.291,-1.272,'dark',12,back=False)
    # Three short concentric turquoise grooves at both ends of each pad.
    for end,(lo,hi) in enumerate(((a0+5,a0+21),(a1-21,a1-5))):
        for groove,r in enumerate((7.64,7.94,8.24)):
            annular_sector('Strike pad %d cyan groove %d %d'%(sector,end,groove),0,0,r,r+.064,lo,hi,-1.319,-1.319,'cyan',4,glow=True,back=False)
    radial_box('Strike pad %d subtle outer ridge'%sector,8.77,8.91,.43,center,-1.27,-.54,'rubber')
for i,a in enumerate((45,135,225,315)):
    radial_box('Diagonal ring joining bracket %d'%i,6.90,8.95,.89,a,-1.34,-.72,'silver')
    radial_box('Bracket %d inset rose strip'%i,7.22,8.69,.47,a,-1.354,-1.342,'cream')
    radial_box('Bracket %d retaining screw'%i,8.18,8.31,.15,a,-1.376,-1.355,'steel')
deck_since(start)

group='Rectangular status display on shared deck slope'
start=len(surfaces)
box('Status display black raised housing',(-7.32,8.72,-.46),(7.32,12.06,-.14),'black')
decal('Uphill rectangular gameplay status screen',(-6.98,8.96,6.98,11.79),-.482,'status',glow=True)
for x in (-7.19,7.19):box('Status bezel silver corner '+str(x),(x-.08,8.84,-.50),(x+.08,11.98,-.46),'steel')
deck_since(start)

group='Upright round marquee gear backing'
topper_start=len(surfaces)
CX,CY=8,37.72
gear=[]
for i in range(64):
    angle=math.tau*i/64;r=10.08 if i%4 in (1,2) else 9.44
    gear.append((CX+r*math.cos(angle),CY+r*math.sin(angle)))
before=len(surfaces);prism('Pink angular circuit gear backing',gear,14.28,15.04,'pink')
for f in surfaces[before:]:
    if ' front ' in f['name'] or ' back ' in f['name']:
        f['texture']='#circuit';f['uv']=[[(18.1-p[0])/20.2*16,(47.83-p[1])/20.2*16] for p in f['vertices']]
        if ' back ' in f['name']:
            f['uv']=[[16-u,v] for u,v in f['uv']]
front_ring('Topper deep continuous round rim',CX,CY,0,[(9.37,14.31,'black',False),(9.43,11.05,'black',False),
    (9.21,10.75,'steel',False),(8.98,10.58,'black',False)],48)

group='Four separated luminous marquee circuit windows'
for sector,center in enumerate((0,90,180,270)):
    a0,a1=center-38,center+38
    annular_sector('Marquee sector %d dark frame'%sector,CX,CY,3.38,9.10,a0,a1,10.53,13.30,'black',12)
    annular_sector('Marquee sector %d raised acrylic'%sector,CX,CY,3.70,8.83,a0+1.7,a1-1.7,10.493,10.52,'purple',12,
                   front_texture='marquee',glow=True,uv_radius=9.05,back=False)
    annular_sector('Marquee sector %d magenta rim'%sector,CX,CY,8.80,8.89,a0+2,a1-2,10.473,10.473,'violet',12,glow=True,back=False)
for i,a in enumerate((45,135,225,315)):
    before=len(surfaces)
    radial_box('Topper diagonal black spoke '+str(i),3.10,9.31,1.53,a,10.49,13.55,'black')
    radial_box('Topper diagonal silver locking strut '+str(i),3.83,8.58,.98,a,10.447,10.48,'silver')
    for f in surfaces[before:]:
        for p in f['vertices']:p[0]+=CX;p[1]+=CY
front_ring('Central logo thick black collar',CX,CY,0,[(3.55,10.68,'black',False),(3.42,10.26,'steel',False),
    (3.29,10.18,'pink',True),(3.11,10.16,'black',False)],48)
disc('Round MUSIC DIVER logo',CX,CY,10.143,3.105,'logo',48,True)
# Keep the upright circle behind the inclined status screen. The compact
# moulded topper depth does not require a second block behind the cabinet.
for f in surfaces[topper_start:]:
    for p in f['vertices']:p[2]=14.1+(p[2]-10.143)*(1.9/(15.04-10.143))

group='Paired marquee speakers'
speakers_start=len(surfaces)
for right in (False,True):
    x=16.09 if right else -.09
    box('Black speaker body '+str(right),(x-1.86,28.31,10.48),(x+1.86,33.04,13.24),'black')
    box('Speaker rim '+str(right),(x-1.72,28.47,10.38),(x+1.72,32.89,10.49),'dark')
    decal('Speaker mesh grille '+str(right),(x-1.56,28.66,x+1.56,32.71),10.356,'details',(0,0,8,8))
for f in surfaces[speakers_start:]:
    for p in f['vertices']:p[2]+=2.7


textures={key:'japanesearcades:block/music_diver_'+key for key in ('materials','circuit','marquee','logo','display','status','side','details')}
textures['particle']=textures['materials']

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def obj(path,faces):
    lines=['# MUSIC DIVER efficient native cabinet, coordinates in blocks.',
           'mtllib japanesearcades:models/block/music_diver.mtl'];index=1;last=None
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

split={'base':[],'console':[],'marquee':[]}
for f in surfaces:
    for part in pieces(list(zip(f['vertices'],f['uv'])),1,[16,32]):
        for poly in quads(part):
            row=min(2,max(0,int(sum(p[0][1] for p in poly)/len(poly)//16)))
            split[tuple(split)[row]].append({**f,'vertices':[[p[0],p[1]-row*16,p[2]] for p,uv in poly],
                                           'uv':[uv for p,uv in poly]})
stats={}
for part,faces in split.items():
    name='block/music_diver_'+part
    stats[part]=obj(ASSETS/'models'/(name+'.obj'),faces)
    write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
stats['item']=obj(ASSETS/'models/item/music_diver.obj',surfaces)
write_json(ASSETS/'models/item/music_diver.json',wrapper('item/music_diver',True))
mtl=[]
for key,glow in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
    mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/music_diver.mtl').write_text('\n'.join(mtl),encoding='utf-8')
write_json(ASSETS/'blockstates/music_diver.json',{'variants':{
    'facing='+direction+',part='+part:{'model':'japanesearcades:block/music_diver_'+part,**({'y':angle} if angle else {})}
    for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in split}})

bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,
    'statistics':{'authoring_faces':len(surfaces),'optimized':stats},
    'notes':'Native static three-block MUSIC DIVER wedge cabinet. Lower controls all share a 42-degree sloping plane; separate upright four-sector luminous topper. Deterministic procedural circuit artwork.'})

groups=defaultdict(list);elements=[]
assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
texture_keys=[key for key in textures if key!='particle']
sizes={key:Image.open(TEX/('music_diver_'+key+'.png')).size for key in texture_keys}
for f in surfaces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'music_diver/'+f['name']));key=f['texture'][1:]
    width,height=sizes[key];keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
        'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_keys.index(key)}},
        'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,key in enumerate(texture_keys):
    path=TEX/('music_diver_'+key+'.png');width,height=sizes[key]
    bbtex.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'music_diver/'+key)),'width':width,'height':height,
        'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'music-diver.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'MUSIC DIVER','model_identifier':'music_diver','visible_box':[2,3,2],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'music_diver/group/'+name)),
                'origin':[8,0,8],'children':children} for name,children in groups.items()]})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])
print('MUSIC DIVER:',len(surfaces),'authoring faces; bounds',bounds)
print('Optimized native meshes:',stats)
