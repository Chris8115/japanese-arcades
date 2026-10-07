"""Build an efficient original SOUND VOLTEX NEMSYS arcade cabinet.

Four sharply tapered side fins and square speakers distinguish this cabinet
from Valkyrie. Static indexed OBJ meshes retain the native authored geometry;
print patterns and tiny perforations live in textures, not dense cuboid grids.
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
from nemsys_artwork import pack_artwork
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/sound-voltex-nemsys'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
for path in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):
    path.mkdir(parents=True,exist_ok=True)

COLORS={
    'black':'#101217','dark':'#232830','steel':'#46505f','edge':'#727f8a',
    'silver':'#b6c4ce','white':'#edf2f3','rubber':'#07090d','cream':'#e5e7df',
    'cyan':'#24dae9','cyan_light':'#a7f6fa','magenta':'#e846b9','pink':'#ffc3f0',
    'purple':'#8c66f1','blue':'#288fe0','teal':'#236e88','red':'#e84983',
}
KEYS=list(COLORS)
atlas=Image.new('RGB',(256,256));d=ImageDraw.Draw(atlas)
for i,col in enumerate(COLORS.values()):
    x,y=i%4*64,i//4*64;d.rectangle((x,y,x+63,y+63),fill=col)
atlas.save(TEX/'sound_voltex_nemsys_materials.png')
def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

# Original printed utility graphics: metallic angular circuits, logos and
# shallow speaker mesh, rather than geometry for each grille hole or LED.
deck=Image.new('RGB',(1024,512),'#1c2630');d=ImageDraw.Draw(deck)
for left in (False,True):
    for i,col in enumerate(('#8ba0ad','#bceef2','#5b8494','#dee9eb','#738790')):
        pts=[(28+i*16,28),(91+i*17,163),(210+i*16,264),(225+i*16,408),(488,484-i*13)]
        if left:pts=[(1024-x,y) for x,y in pts]
        d.line(pts,fill=col,width=7 if i%2 else 4)
for x in (100,924):
    d.ellipse((x-64,33,x+64,161),outline='#a4c8dc',width=7)
    d.ellipse((x-49,48,x+49,146),outline='#51adc5',width=4)
for j,label in enumerate(('BT-A','BT-B','BT-C','BT-D')):
    d.text((330+j*121,163),label,anchor='mm',font=font(20,True),fill='#cfdde0')
for x,label in ((398,'FX-L'),(630,'FX-R')):
    d.text((x,377),label,anchor='mm',font=font(20,True),fill='#dc9dcc')
d.text((512,459),'SOUND VOLTEX',anchor='mm',font=font(34,True),fill='#edf1f2')
d.text((512,493),'N E M S Y S',anchor='mm',font=font(14),fill='#94aebd')
for x in (31,992):
    for y in (24,489):
        d.ellipse((x-6,y-6,x+6,y+6),fill='#bac7cc');d.line((x-3,y,x+3,y),fill='#4b5866',width=2)
deck.save(TEX/'sound_voltex_nemsys_controls.png')

details=Image.new('RGB',(1024,1024),'#111721');d=ImageDraw.Draw(details)
# Upper half = 2:1 wordmark assembly. Keep exact lettering out of tiny meshes.
for mirror in (False,True):
    for i,col in enumerate(('#aabcc7','#677785','#cae5ea','#536570')):
        pts=[(0,70+i*42),(172,70+i*42),(217,121+i*42),(289,121+i*42),(332,178+i*28)]
        if mirror:pts=[(1024-x,y) for x,y in pts]
        d.line(pts,fill=col,width=5)
d.line((99,347,430,347,604,158,973,158),fill='#63d2e0',width=9)
d.line((452,371,642,371,815,196,1018,196),fill='#d774c3',width=8)
d.text((512,174),'SOUND',font=font(113,True),anchor='mm',fill='#e8eff1',stroke_width=3,stroke_fill='#05090d')
d.text((512,284),'VOLTEX',font=font(126,True),anchor='mm',fill='#e8eff1',stroke_width=3,stroke_fill='#05090d')
d.text((512,394),'EXCEED GEAR',font=font(42,True),anchor='mm',fill='#a9c2ce')
d.rectangle((0,512,511,1023),fill='#15191e')
for y in range(520,1017,9):
    for x in range(7+(y//9%2)*4,507,9):
        d.rectangle((x,y,x+2,y+2),fill='#30363e')
d.ellipse((58,570,454,966),outline='#222a33',width=11)
d.ellipse((145,657,367,879),outline='#263039',width=7)
# Bottom right = printed electronics/reader panel + vent strip.
d.rectangle((512,512,1023,1023),fill='#151c25')
d.rounded_rectangle((569,554,967,859),radius=20,outline='#778c9c',width=10)
d.rectangle((598,582,937,831),fill='#233c4d')
d.text((768,673),'e-amusement',font=font(31,True),anchor='mm',fill='#e6e5e8')
d.text((768,730),'TOUCH CARD',font=font(24),anchor='mm',fill='#91dbde')
for y in range(909,1003,15):d.line((557,y,983,y),fill='#080d11',width=6)
details.save(TEX/'sound_voltex_nemsys_details.png')

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

# Narrow black lower cabinet, separate steel toe trim and right-side service.
group='Lower black pedestal'
box('Pedestal bottom plinth',(-.22,.27,1.90),(16.22,1.24,15.36),'rubber')
box('Pedestal black cabinet',(.43,1.20,2.31),(15.57,15.06,15.18),'black',('down',))
box('Silver base front toe',(-.58,.30,1.48),(16.58,1.08,2.36),'silver')
box('Left silver base rail',(-.58,.30,2.30),(-.16,.70,15.5),'silver')
box('Right silver base rail',(16.16,.30,2.30),(16.58,.70,15.5),'silver')
box('Pedestal upper front trim',(.23,14.04,2.15),(15.77,15.17,2.36),'dark')
box('Large left service door',(5.23,2.45,2.25),(14.78,13.70,2.33),'dark')
box('Large left door inset',(5.42,2.64,2.218),(14.59,13.51,2.25),'black')
box('Right payment service door',(1.27,2.45,2.24),(5.02,13.70,2.33),'dark')
box('Upper coin service inset',(1.50,9.34,2.208),(4.77,13.46,2.24),'black')
box('Lower return service inset',(1.50,2.70,2.208),(4.77,9.04,2.24),'black')
box('Coin inlet metal trim',(2.25,11.70,2.11),(4.17,12.39,2.22),'silver')
box('Coin inlet black slit',(2.39,11.94,2.08),(4.03,12.13,2.12),'rubber')
box('Coin return inset',(2.25,4.10,2.12),(4.17,5.42,2.22),'rubber')
box('Coin return lower lip',(2.30,4.07,1.98),(4.12,4.25,2.14),'steel')
for x,y in ((1.90,8.48),(5.74,12.77),(14.12,12.77)):
    box('Small steel door lock %.2f'%x,(x-.09,y-.09,2.17),(x+.09,y+.09,2.23),'silver')
for x in (1.0,15.0):
    for z in (2.9,14.8):box('Levelling foot %.1f %.1f'%(x,z),(x-.22,0,z-.22),(x+.22,.28,z+.22),'black')

group='Black rear monitor spine'
box('Rear portrait tower',(2.40,15.00,9.84),(13.60,38.40,14.64),'black',('down',))
box('Portrait monitor surround',(2.53,19.74,7.90),(13.47,38.48,10.05),'dark')
box('Portrait black face',(2.70,19.89,7.72),(13.30,38.29,7.93),'rubber',('south',))
box('Portrait screen silver inset',(2.93,20.10,7.68),(13.07,38.08,7.75),'edge',('south',))
decal('SOUND VOLTEX portrait idle screen',(3.02,20.22,12.98,37.92),7.666,'display',glow=True)
for x in (2.79,13.21):
    for y in (20.02,24.58,29.13,33.7,38.12):
        box('Monitor bezel screw %s %s'%(x,y),(x-.038,y-.038,7.655),(x+.038,y+.038,7.697),'silver',('south',))
box('Rear service panel',(3.13,17.55,14.637),(12.87,36.61,14.69),'dark')
face('Rear upper ventilation',[(4,34.7,14.7),(12,34.7,14.7),(12,36.0,14.7),(4,36.0,14.7)],
     texture='details',uv=[(8,16),(16,16),(16,14),(8,14)])
face('Rear base ventilation',[(4.3,3.3,15.191),(11.7,3.3,15.191),(11.7,5.0,15.191),(4.3,5.0,15.191)],
     texture='details',uv=[(8,16),(16,16),(16,14),(8,14)])

# The wing faces are broad angular sheet-metal fins with thin luminous circuit
# ribbons. No dense cuboid pattern, translucent overdraw or custom renderer.
group='Four sharply tapered illuminated fins'
upper=[(-2.98,43.68),(2.41,39.62),(2.41,33.44),(.08,34.80),(-2.98,39.17)]
lower=[(2.41,29.03),(-.36,26.79),(-2.98,20.83),(-2.98,15.06),(2.41,19.19)]
for left in (False,True):
    for kind,outline in (('upper',upper),('lower',lower)):
        start=len(surfaces)
        pp=[(16-x,y) for x,y in outline] if left else outline
        prism(('Right' if left else 'Left')+' '+kind+' tapered fin',pp,5.66,6.52,'black')
        # A recessed inner bevel reproduces the manufactured layered edge.
        cx=sum(p[0] for p in pp)/len(pp);cy=sum(p[1] for p in pp)/len(pp)
        inset=[(cx+(x-cx)*.94,cy+(y-cy)*.975) for x,y in pp]
        prism(('Right' if left else 'Left')+' '+kind+' steel inner border',inset,5.635,5.67,'steel',back=False)
        inset=[(cx+(x-cx)*.86,cy+(y-cy)*.94) for x,y in pp]
        prism(('Right' if left else 'Left')+' '+kind+' black printed inset',inset,5.616,5.64,'black',back=False)
        for j in range(4):
            if kind=='upper':
                pts=[(-2.61+j*.36,42.53-j*.47),(-2.61+j*.36,39.09+j*.06),
                     (.04+j*.31,35.63+j*.31),(2.03,34.63+j*.33)]
                col=('pink','purple','magenta','pink')[j]
            else:
                pts=[(-2.59+j*.36,16.19+j*.46),(-2.59+j*.36,20.82-j*.08),
                     (.16+j*.31,25.48-j*.19),(2.03,27.12-j*.30)]
                col=('cyan_light','cyan','blue','cyan_light')[j]
            if left:pts=[(16-x,y) for x,y in pts]
            ribbon(('R' if left else 'L')+' '+kind+' circuit'+str(j),pts,.25 if j%2 else .20,5.597,col,True)
        # Lower fins lean along the monitor-to-console transition; upper fins
        # retain a nearly upright frontal presentation.
        for f in surfaces[start:]:
            for p in f['vertices']:
                p[2]+=(p[1]-33.44)*.028 if kind=='upper' else (p[1]-23.0)*.205

group='Square outward speaker pods'
for left in (False,True):
    x=-.25 if not left else 16.25
    start=len(surfaces)
    box('Square speaker rear '+str(left),(x-2.40,28.38,5.41),(x+2.40,33.28,9.12),'black')
    box('Square speaker steel edge '+str(left),(x-2.45,28.32,5.28),(x+2.45,33.34,5.49),'steel',('south',))
    box('Square speaker dark bezel '+str(left),(x-2.32,28.45,5.19),(x+2.32,33.21,5.29),'rubber',('south',))
    decal('Square speaker printed mesh '+str(left),(x-2.10,28.66,x+2.10,33.00),5.175,'details',(0,8,8,16))
    # Away from the monitor, not toward it. Large square corners remain clear.
    rotate_y_since(start,x,6.9,8 if left else -8)

group='Projecting patterned control console'
deckoutline=[(-1.88,15.02),(-1.88,16.05),(9.16,17.30),(9.16,15.78)]
side_prism('Wide black projecting deck housing',deckoutline,-1.74,17.74,'black')
def deck_y(z):return 16.13+(z+1.66)*.113
face('Printed metal control deck',[(17.40,deck_y(9.02),9.02),(17.40,deck_y(-1.62),-1.62),
                                  (-1.40,deck_y(-1.62),-1.62),(-1.40,deck_y(9.02),9.02)],
     texture='controls',uv=[(0,0),(0,16),(16,16),(16,0)])
box('Front console brushed metal lip',(-1.77,15.73,-1.96),(17.77,16.13,-1.68),'silver')
box('Front console black fascia',(-1.73,14.80,-1.92),(17.73,15.72,-1.62),'dark')
for x in (-1.53,17.21):
    side_prism('Console steel side rail '+str(x),[(-1.83,15.82),(-1.83,16.2),(9.11,17.42),(9.11,17.11)],x,x+.27,'silver')

# Standard two rotary controls, four white BT keys and two wide dark FX keys.
group='Two knobs and six raised keys'
for x in (4.33,6.78,9.22,11.67):
    z=2.15;y=deck_y(z)
    begin=len(surfaces)
    box('BT key metal frame '+str(x),(x-.99,y-.04,z-.99),(x+.99,y+.16,z+.99),'silver',('down',))
    box('BT key black gasket '+str(x),(x-.87,y+.15,z-.87),(x+.87,y+.22,z+.87),'rubber',('down',))
    box('BT ivory keycap '+str(x),(x-.76,y+.21,z-.75),(x+.76,y+.36,z+.75),'cream',('down',))
    for f in surfaces[begin:]:
        for p in f['vertices']:p[1]+=(p[2]-z)*.113
for x in (5.65,10.35):
    z=-.05;y=deck_y(z);begin=len(surfaces)
    box('FX silver frame '+str(x),(x-1.38,y-.03,z-.65),(x+1.38,y+.14,z+.65),'silver',('down',))
    box('FX luminous pink surround '+str(x),(x-1.26,y+.13,z-.55),(x+1.26,y+.21,z+.55),'magenta',('down',))
    box('FX long dark keycap '+str(x),(x-1.06,y+.20,z-.40),(x+1.06,y+.33,z+.40),'black',('down',))
    for f in surfaces[begin:]:
        for p in f['vertices']:p[1]+=(p[2]-z)*.113
for x in (1.38,14.62):
    z=4.63;y=deck_y(z)
    top_disc('Rotary control '+str(x),x,y,z,
        [(1.07,0,'black'),(1.06,.17,'silver'),(.86,.30,'silver'),(.81,.88,'edge'),(.66,1.02,'black')],20)
    box('Knob indicator '+str(x),(x-.08,y+1.025,z-.60),(x+.08,y+1.04,z-.18),'cyan',('down',))

# Shallow angled information panel below portrait glass, and a separate small
# card reader raised in the centre behind the key bank.
group='Under-screen panel and card reader'
panel=[(2.42,18.35),(13.58,18.35),(12.84,20.04),(3.16,20.04)]
prism('Under-screen trapezoid silver trim',panel,7.15,7.66,'silver')
prism('Under-screen trapezoid black label',[(2.73,18.52),(13.27,18.52),(12.65,19.83),(3.35,19.83)],7.11,7.16,'black',back=False)
decal('Under-screen SOUND VOLTEX logo',(4.33,18.60,11.67,19.76),7.093,'details',(0,0,16,8))
side_prism('Central card reader wedge',[(4.75,17.06),(4.75,17.49),(7.36,18.17),(7.36,17.31)],5.91,10.09,'silver')
def reader_y(z):return 17.49+(z-4.75)*(.68/2.61)+.025
face('Card reader tilted screen',[(9.83,reader_y(7.19),7.19),(9.83,reader_y(4.95),4.95),
                                  (6.17,reader_y(4.95),4.95),(6.17,reader_y(7.19),7.19)],
     texture='details',uv=[(8,8),(8,13.8),(16,13.8),(16,8)],glow=True)

group='Metallic SOUND VOLTEX brand marquee'
brand=[(.22,43.02),(15.78,43.02),(13.70,38.62),(2.30,38.62)]
prism('Wide upper metallic marquee shell',brand,6.15,8.02,'steel')
inner=[(.54,42.79),(15.46,42.79),(13.53,38.86),(2.47,38.86)]
prism('Upper marquee black face',inner,6.115,6.17,'black',back=False)
# Map logo across the tapered face, preserving its corner circuit decoration.
marquee_begin=len(surfaces)
prism('Upper marquee circuit artwork',[(.77,42.62),(15.23,42.62),(13.40,39.03),(2.60,39.03)],6.101,6.116,'black',back=False)
for f in surfaces[marquee_begin:]:
    if ' front ' in f['name']:
        f['texture']='#details';f['uv']=[[(15.23-p[0])/14.46*16,(42.62-p[1])/3.59*8] for p in f['vertices']]
for x,y in ((1.08,42.55),(14.92,42.55),(2.62,39.19),(13.38,39.19)):
    box('Marquee fixing %s %s'%(x,y),(x-.055,y-.055,6.07),(x+.055,y+.055,6.12),'silver',('south',))

group='Separate anime cutout topper'
header=[(.08,41.10),(15.92,41.10),(15.92,44.46),(13.58,47.43),(2.42,47.43),(.08,44.46)]
prism('Printed topper backing',header,7.79,8.22,'black')
header_start=len(surfaces)
prism('Original anime topper print',header,7.768,7.792,'black',back=False)
for f in surfaces[header_start:]:
    if ' front ' in f['name']:
        f['texture']='#marquee';su,sv=SCALES['marquee']
        f['uv']=[[(15.92-p[0])/15.84*16*su,(47.43-p[1])/6.33*16*sv] for p in f['vertices']]


textures={key:'japanesearcades:block/sound_voltex_nemsys_'+key for key in ('materials','controls','details','display','marquee')}
textures['particle']=textures['materials']

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def obj(path,faces):
    lines=['# SOUND VOLTEX NEMSYS efficient native cabinet, coordinates in blocks.',
           'mtllib japanesearcades:models/block/sound_voltex_nemsys.mtl'];index=1;last=None
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
    name='block/sound_voltex_nemsys_'+part
    stats[part]=obj(ASSETS/'models'/(name+'.obj'),faces)
    write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
stats['item']=obj(ASSETS/'models/item/sound_voltex_nemsys.obj',surfaces)
write_json(ASSETS/'models/item/sound_voltex_nemsys.json',wrapper('item/sound_voltex_nemsys',True))
mtl=[]
for key,glow in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
    mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/sound_voltex_nemsys.mtl').write_text('\n'.join(mtl),encoding='utf-8')
write_json(ASSETS/'blockstates/sound_voltex_nemsys.json',{'variants':{
    'facing='+direction+',part='+part:{'model':'japanesearcades:block/sound_voltex_nemsys_'+part,**({'y':angle} if angle else {})}
    for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in split}})

bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,
    'statistics':{'authoring_faces':len(surfaces),'optimized':stats},
    'notes':'Native static three-block portrait cabinet. Four planar tapered fins, two outward square speakers, two knobs and six keys. Original art packed without resampling.'})

groups=defaultdict(list);elements=[]
assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
texture_keys=[key for key in textures if key!='particle']
sizes={key:Image.open(TEX/('sound_voltex_nemsys_'+key+'.png')).size for key in texture_keys}
for f in surfaces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'sound_voltex_nemsys/'+f['name']));key=f['texture'][1:]
    width,height=sizes[key];keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
        'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_keys.index(key)}},
        'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,key in enumerate(texture_keys):
    path=TEX/('sound_voltex_nemsys_'+key+'.png');width,height=sizes[key]
    bbtex.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'sound_voltex_nemsys/'+key)),'width':width,'height':height,
        'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'sound-voltex-nemsys.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'SOUND VOLTEX NEMSYS','model_identifier':'sound_voltex_nemsys','visible_box':[2,3,2],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'sound_voltex_nemsys/group/'+name)),
                'origin':[8,0,8],'children':children} for name,children in groups.items()]})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])
print('SOUND VOLTEX NEMSYS:',len(surfaces),'authoring faces; bounds',bounds)
print('Optimized native meshes:',stats)
