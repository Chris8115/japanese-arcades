"""Export ONGEKI's open portal cabinet as efficient static, native OBJ meshes.

The circular side pads are real 32-segment annuli, not stacked voxel boxes.
Authored in model units (16 per block), north/front is -Z. Artwork is prepared
separately; this exporter never resamples or repaints the original illustrations.
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
from ongeki_artwork import pack_artwork

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/ongeki'
ASSETS = ROOT / 'src/main/resources/assets/funpackcustom'
TEX = ASSETS / 'textures/block'
for path in (ART, TEX, ASSETS/'models/block', ASSETS/'models/item', ASSETS/'blockstates'):
    path.mkdir(parents=True, exist_ok=True)

COLORS = {
    'black':'#111317', 'charcoal':'#202429', 'dark':'#30363c', 'edge':'#59616a',
    'white':'#f3f1e8', 'pearl':'#daddd6', 'silver':'#aebcc1', 'bright':'#e5ebeb',
    'gold':'#ddcf80', 'gold_light':'#f1e8b8', 'cyan':'#9df8ff', 'blue':'#7495ee',
    'pink':'#ec9fdc', 'mint':'#a9f4d4', 'red':'#fb757e', 'green':'#87d99a',
}
KEYS = list(COLORS)
palette = Image.new('RGB', (256,256)); draw = ImageDraw.Draw(palette)
for i,color in enumerate(COLORS.values()):
    x,y = i%4*64,i//4*64
    draw.rectangle((x,y,x+63,y+63), fill=color)
palette.save(TEX/'ongeki_materials.png')

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

# Geometric print details stay in textures instead of hundreds of small faces.
deck = Image.new('RGB',(1024,512),'#eeeede'); d=ImageDraw.Draw(deck)
for cx in (258,766):
    for radius,color,width in ((177,'#b8c2c4',7),(156,'#d3dadd',5),(135,'#c4cdd1',3)):
        d.ellipse((cx-radius,246-radius*.72,cx+radius,246+radius*.72),outline=color,width=width)
    d.line((cx-215,354,cx-125,354),fill='#99adbc',width=7)
    d.line((cx+128,354,cx+215,354),fill='#99adbc',width=7)
for x in (30,994):
    for y in (28,482):
        d.ellipse((x-6,y-6,x+6,y+6),fill='#8c999d')
d.text((512,434),'ONGEKI',font=font(23),anchor='mm',fill='#9caaa8')
d.text((257,411),'LEFT',font=font(18),anchor='mm',fill='#97a5a4')
d.text((767,411),'RIGHT',font=font(18),anchor='mm',fill='#97a5a4')
deck.save(TEX/'ongeki_controls.png')

details=Image.new('RGB',(1024,1024),'#171c22');d=ImageDraw.Draw(details)
# Four 256px-tall strips: rear ventilation, side lettering, instruction shelf,
# and angular ivory/gold pearl trim. Each has padding safe for mipmapping.
for y in range(29,220,18):
    d.rounded_rectangle((98,y,926,y+7),radius=3,fill='#090b0e')
d.rectangle((0,256,1023,511),fill='#eeeede')
d.text((512,382),'ONGEKI',font=font(106),anchor='mm',fill='#b6beb5')
d.rectangle((0,512,1023,767),fill='#222833')
for x,label in ((35,'Aime'),(339,'RHYTHM'),(665,'LEVER + 6 KEYS')):
    d.rounded_rectangle((x,539,x+295,733),radius=9,fill='#dce6e4',outline='#abbac5',width=4)
    d.text((x+147,599),label,font=font(25,True),anchor='mm',fill='#414a50')
    for j in range(3):
        c=('#db778b','#94cda9','#8dc1e2')[j]
        d.rectangle((x+50+j*67,643,x+96+j*67,685),fill=c)
d.rectangle((0,768,1023,1023),fill='#e0e3d9')
for i in range(-4,12):
    x=i*120
    d.polygon(((x,768),(x+65,768),(x+295,1023),(x+230,1023)),fill=('#efe8ba' if i%2 else '#ccd7d9'))
    d.line((x+72,768,x+302,1023),fill='#f9f5da',width=8)
details.save(TEX/'ongeki_details.png')

pack_artwork()
SCALES={}
for key in ('display','marquee'):
    source=ART/(key+'-artwork-source.png')
    runtime=TEX/('ongeki_'+key+'.png')
    if not source.exists() or not runtime.exists():
        raise SystemExit('Prepare original ONGEKI '+key+' artwork and its packed runtime texture before export.')
    with Image.open(source) as image: sw,sh=image.size
    with Image.open(runtime) as image: tw,th=image.size
    assert sw<=tw and sh<=th
    SCALES[key]=(sw/tw,sh/th)

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

def side_ring(name,x,y,z,profile,side,segments=32,tilt_degrees=12):
    """Annular radial profile, (radius, axial depth, material, glow).

    Axis is +/-X: the circles belong on the deep sides of the white portal.
    Inside faces cant 12 degrees toward the player, as on the real cabinet.
    """
    tilt=math.radians(tilt_degrees)
    for j,(a,b) in enumerate(zip(profile,profile[1:])):
        ra,da,material,glow=a;rb,db,_,_=b
        for i in range(segments):
            ta,tb=i*math.tau/segments,(i+1)*math.tau/segments
            def point(radius,depth,t):
                # Rotate around Y so the upper pad faces inward/forward.
                px=side*depth;py=radius*math.sin(t);pz=radius*math.cos(t)
                return (x+px*math.cos(tilt)+side*pz*math.sin(tilt),y+py,
                        z-side*px*math.sin(tilt)+pz*math.cos(tilt))
            pts=[point(ra,da,ta),point(ra,da,tb),point(rb,db,tb),point(rb,db,ta)]
            if side>0:pts.reverse()
            face(name+' %d %d'%(j,i),pts,material,glow=glow)

# Broad solid lower body and modest silver toe plate.
group='Black pedestal and service panels'
box('Black bottom plinth',(-.9,.25,-.55),(16.9,1.18,16),'charcoal')
box('Silver front foot lip',(-1.25,.27,-1.12),(17.25,.81,.05),'silver')
box('Black main pedestal',(.05,1.1,.65),(15.95,17.1,15.65),'black',('down',))
box('Left pedestal edge',(-.3,1.12,.55),(.08,17.1,15.55),'charcoal')
box('Right pedestal edge',(15.92,1.12,.55),(16.3,17.1,15.55),'charcoal')
box('Front pedestal service inset',(.8,2.55,.60),(15.2,15.72,.66),'charcoal')
box('Left access door',(.98,2.76,.55),(8.88,15.5,.61),'black')
box('Right access door',(9.0,2.76,.55),(14.99,15.5,.61),'black')
box('Coin slot surround',(12.85,11.3,.44),(14.32,12.47,.58),'silver')
box('Coin insertion slit',(13.12,11.94,.42),(14.09,12.10,.45),'black')
box('Coin return dark recess',(12.85,6.88,.45),(14.35,8.16,.58),'dark')
box('Coin return tray',(12.96,6.97,.30),(14.25,7.18,.50),'silver')
for x,y in ((8.21,11.9),(14.16,4.25),(1.66,15.0)):
    box('Service latch %.2f %.2f'%(x,y),(x-.07,y-.08,.525),(x+.07,y+.08,.56),'silver')
for x in (.45,15.15):
    for z in (.8,14.6):box('Low leveling foot %.2f %.2f'%(x,z),(x-.25,0,z-.3),(x+.25,.3,z+.3),'dark')

# A genuinely separate narrow rear screen tower. The white portal is forward
# of it, with open space above and around the portrait monitor.
group='Rear portrait screen tower'
box('Rear vertical black spine',(1.45,16.98,10.8),(14.55,38.60,15.35),'black',('down',))
box('Portrait monitor sculpted bezel',(2.03,19.14,9.35),(13.97,38.38,11.05),'charcoal')
box('Portrait glossy black front frame',(2.18,19.34,9.19),(13.82,38.23,9.36),'black',('south',))
box('Screen recessed inner rim',(2.66,19.89,9.16),(13.34,37.96,9.21),'edge',('south',))
decal('Tall portrait ONGEKI display',(3.0,20.0,13.0,37.78),9.145,'display',glow=True)
box('Monitor lower wordmark bar',(2.72,19.40,9.11),(13.28,19.80,9.20),'charcoal')
decal('Monitor small instruction band',(3.06,19.47,12.94,19.73),9.098,'details',(0,8.4,16,11.7))
box('Rear inset access panel',(2.03,20.05,15.34),(13.97,36.65,15.39),'charcoal')
# One printed ventilation surface is enough; no geometry for tiny perforations.
face('Rear upper ventilation print',[(2.8,34.0,15.399),(13.2,34.0,15.399),(13.2,36.0,15.399),(2.8,36.0,15.399)],
     texture='details',uv=[(0,4),(16,4),(16,0),(0,0)])
face('Rear lower ventilation print',[(3.3,4.0,15.666),(12.7,4.0,15.666),(12.7,6.1,15.666),(3.3,6.1,15.666)],
     texture='details',uv=[(0,4),(16,4),(16,0),(0,0)])

# Console top: white sloping rectangle; SIX buttons and a central short lever.
group='Sloped white control deck'
side_prism('Deep black console housing',[(-.75,16.90),(9.40,18.45),(9.40,19.45),(-.75,18.05)],-.3,16.3,'black')
def deck_y(z):return 18.15+(z+.55)*.128
deckpoints=[(15.52,deck_y(8.96),8.96),(15.52,deck_y(-.42),-.42),
            (.48,deck_y(-.42),-.42),(.48,deck_y(8.96),8.96)]
face('Printed pearl control surface',deckpoints,texture='controls',uv=[(0,0),(0,16),(16,16),(16,0)])
box('Silver console front lip',(-.15,17.75,-.93),(16.15,18.12,-.66),'silver')
box('Glossy black console front edge',(-.30,17.30,-1.01),(16.30,17.78,-.68),'black')
for bank,xs in (('left',(2.05,3.90,5.75)),('right',(10.25,12.10,13.95))):
    for j,(x,color) in enumerate(zip(xs,('blue','green','red'))):
        z=2.0;y=deck_y(z)
        start=len(surfaces)
        box('Key surround '+bank+str(j),(x-.78,y-.12,z-.84),(x+.78,y+.10,z+.84),'edge',('down',))
        box('Key black gasket '+bank+str(j),(x-.69,y+.1,z-.73),(x+.69,y+.16,z+.73),'black',('down',))
        box('Luminous key '+bank+str(j),(x-.61,y+.16,z-.64),(x+.61,y+.29,z+.64),color,('down',))
        surfaces[-1]['glow']=True
        for f in surfaces[start:]:
            for p in f['vertices']:p[1]+=(p[2]-z)*.128
for x,color in ((2.20,'red'),(13.80,'gold')):
    y=deck_y(5.7)
    box('Small menu button '+str(x),(x-.25,y,5.40),(x+.25,y+.08,5.98),color,('down',))
box('Lever rectangular socket',(7.31,deck_y(4.7),4.2),(8.69,deck_y(4.7)+.17,5.24),'edge')
box('Lever black boot',(7.52,deck_y(4.7)+.15,4.36),(8.48,deck_y(4.7)+.40,5.1),'black')
box('Central lever metal shaft',(7.88,19.1,4.61),(8.12,20.50,4.87),'silver')
prism('Central lever black grip',[(7.68,20.1),(7.64,21.0),(7.81,21.27),(8.2,21.27),(8.37,21.0),(8.32,20.1)],4.48,5.0,'black')
face('Back console instruction shelf',[(14.0,19.43,9.08),(14.0,19.27,7.88),(2.0,19.27,7.88),(2.0,19.43,9.08)],
     texture='details',uv=[(0,8),(0,12),(16,12),(16,8)])

# The black privacy shields sit behind the hand pads, below the portrait bezel.
group='Side privacy wings and illuminated wall buttons'
wing=[(1.02,19.0),(8.85,20.1),(9.02,30.2),(7.94,30.48),(1.02,26.4)]
for side in (-1,1):
    x=.8 if side<0 else 14.78
    side_prism('Black privacy wing '+str(side),wing,x,x+.42,'black')
    # Thin pale illuminated wall keys face the player's hands, on the inside.
    xface=1.26 if side<0 else 14.74
    p=[(xface,19.75,.8),(xface,22.22,.8),(xface,22.53,2.16),(xface,19.97,2.16)]
    if side>0:p.reverse()
    face('Purple side wall button '+str(side),p,'pink',glow=True)
    side_prism('Side key black housing '+str(side),[(.61,19.41),(.61,22.5),(2.4,22.87),(2.4,19.71)],
               .75 if side<0 else 14.94,1.20 if side<0 else 15.39,'charcoal')

# Tall white side shells form a forward free-standing arch. Their broad faces
# run front-to-back; side-view circles must not become front-facing WACCA rings.
group='White portal side shells'
outline=[(-.64,17.2),(4.20,17.92),(6.70,27.4),(7.30,39.92),(6.24,44.4),
         (3.75,46.02),(.58,45.38),(-.21,42.67),(-.28,36.9),(-.64,29.3)]
for side in (-1,1):
    x0,x1=(-1.14,.18) if side<0 else (15.82,17.14)
    side_prism('Pearl portal shell '+str(side),outline,x0,x1,'white')
    # Deep charcoal insert and thin pearl outline visible between disk and deck.
    inset=[(.31,20.7),(3.55,21.18),(5.93,28.2),(6.39,39.46),(5.50,43.0),
           (3.20,44.29),(.73,43.74),(.42,36.6)]
    xi=.197 if side<0 else 15.783
    side_prism('Black portal inner insert '+str(side),inset,xi,xi+.024,'black')
    # Forward rim cap stays angular and thin, avoiding large stair-step surfaces.
    strip=[(-.672,19.00),(-.30,19.06),(-.11,42.55),(.66,45.04),(.37,45.08),(-.44,42.70)]
    side_prism('Front silver light channel '+str(side),strip,x0-.012,x1+.012,'silver')
    # LED faces point forward (-Z), where the long light bars are seen head-on.
    lx=x0+.20;rx=x1-.20
    for j,(ya,yb,col) in enumerate(((19.3,26.0,'pink'),(26.0,34.0,'mint'),(34.0,42.7,'cyan'))):
        face('Forward portal LED %s %d'%(side,j),[(rx,yb,-.69),(rx,ya,-.69),(lx,ya,-.69),(lx,yb,-.69)],col,glow=True)
    # Deliberately just one white printed panel for lettering on the lower side.
    outer=x0-.009 if side<0 else x1+.009
    pp=[(outer,20.0,.03),(outer,27.3,.03),(outer,27.3,1.09),(outer,20.0,1.09)]
    if side>0:pp.reverse()
    face('Outer ONGEKI vertical lettering '+str(side),pp,texture='details',uv=[(16,8),(0,8),(0,4),(16,4)])

# Outer faces are restrained relief rings; inward faces have three faceted
# white/silver bevels, a glowing ring and a quiet pale circular centre.
group='Circular side pads'
for side in (-1,1):
    x=.20 if side<0 else 15.8
    inward=-side
    side_ring('Inward pad '+str(side),x,32.22,2.75,
        [(3.40,0,'silver',False),(3.38,.27,'pearl',False),(3.15,.60,'white',False),
         (2.96,.72,'white',False),(2.63,.74,'cyan' if side<0 else 'mint',True),
         (2.41,.74,'white',False),(2.36,.62,'pearl',False),(.04,.62,'pearl',False)],inward,32)
    outer=-1.17 if side<0 else 17.17
    side_ring('Outer engraved ring '+str(side),outer,32.22,2.75,
        [(3.00,0,'silver',False),(2.91,.025,'white',False),(2.77,.025,'silver',False),
         (2.72,.035,'white',False),(.04,.035,'white',False)],side,32,tilt_degrees=0)

# Wide shallow brow, broad pearl canopy, a slim cyan waveform, and the separate
# hanging trapezoid marquee. Open space remains between it and the screen.
group='Sculpted canopy and suspended title marquee'
canopy=[(-1.3,43.65),(-1.47,45.52),(-.45,47.25),(3.0,47.40),(13.5,47.36),
        (16.67,46.91),(17.47,45.10),(17.30,43.65),(15.73,44.46),(.20,44.46)]
prism('Pearl faceted canopy',canopy,.30,7.16,'pearl')
frontpanel=[(-1.37,45.48),(-.42,47.10),(3.10,47.23),(13.46,47.21),(16.53,46.80),
            (17.31,45.11),(16.85,44.45),(14.10,45.43),(1.20,45.40)]
canopy_print_start=len(surfaces)
prism('Canopy white and gold face',frontpanel,.23,.31,'white',back=False)
for f in surfaces[canopy_print_start:]:
    if ' front ' in f['name']:
        f['texture']='#details'
        f['uv']=[[(p[0]+1.37)/18.68*16,12+(47.23-p[1])/2.78*4] for p in f['vertices']]
for side in (-1,1):
    pp=[(-1.28,45.50),(-.39,46.96),(1.26,46.50),(2.70,45.45),(.40,44.71)]
    if side>0:pp=[(16-x,y) for x,y in pp]
    prism('Canopy champagne angled cap '+str(side),pp,.18,.25,'gold_light',back=False)
    pp=[(-.97,45.55),(-.30,46.68),(1.33,46.15),(1.9,45.59),(.36,45.30)]
    if side>0:pp=[(16-x,y) for x,y in pp]
    prism('Canopy pale diagonal facet '+str(side),pp,.15,.20,'white',back=False)
path=[(.85,46.03),(5.2,46.14),(8.1,45.92),(11.42,46.06),(15.27,45.69)]
ribbon('Canopy dark LED recess',path,.60,.125,'black')
ribbon('Canopy cyan LED wave',path,.36,.110,'cyan',True)
box('Canopy underside transverse silver beam',(.16,43.66,2.48),(15.84,44.13,6.15),'silver')
for x in (1.16,14.84):box('Marquee hanging strut '+str(x),(x-.18,42.88,4.2),(x+.18,44.02,4.62),'silver')
marquee=[(1.05,43.95),(14.95,43.95),(13.66,40.37),(12.93,39.98),(3.07,39.98),(2.34,40.37)]
prism('Hanging trapezoid marquee white rim',marquee,4.31,4.92,'white')
inner=[(1.33,43.74),(14.67,43.74),(13.41,40.50),(12.87,40.23),(3.13,40.23),(2.59,40.50)]
prism('Hanging trapezoid dark face',inner,4.287,4.32,'charcoal',back=False)
decal('ONGEKI luminous marquee title',(2.8,40.36,13.2,43.63),4.27,'marquee',glow=True)

textures={key:'funpackcustom:block/ongeki_'+key for key in ('materials','controls','details','display','marquee')}
textures['particle']=textures['materials']

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def obj(path,faces):
    lines=['# ONGEKI efficient native cabinet, coordinates in blocks.',
           'mtllib funpackcustom:models/block/ongeki.mtl'];index=1;last=None
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
    model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'funpackcustom:models/'+name+'.obj',
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
    name='block/ongeki_'+part
    stats[part]=obj(ASSETS/'models'/(name+'.obj'),faces)
    write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
stats['item']=obj(ASSETS/'models/item/ongeki.obj',surfaces)
write_json(ASSETS/'models/item/ongeki.json',wrapper('item/ongeki',True))
mtl=[]
for key,glow in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
    mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/ongeki.mtl').write_text('\n'.join(mtl),encoding='utf-8')
write_json(ASSETS/'blockstates/ongeki.json',{'variants':{
    'facing='+direction+',part='+part:{'model':'funpackcustom:block/ongeki_'+part,**({'y':angle} if angle else {})}
    for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in split}})

bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
write_json(ART/'geometry.json',{'textures':textures,'meshes':surfaces,'bounds':bounds,
    'statistics':{'authoring_faces':len(surfaces),'optimized':stats},
    'notes':'Native static three-block portrait cabinet. Side discs face inward across portal, not straight forward. Original art packed without resampling.'})

groups=defaultdict(list);elements=[]
assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate mesh names'
texture_keys=[key for key in textures if key!='particle']
sizes={key:Image.open(TEX/('ongeki_'+key+'.png')).size for key in texture_keys}
for f in surfaces:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'ongeki/'+f['name']));key=f['texture'][1:]
    width,height=sizes[key];keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
        'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_keys.index(key)}},
        'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,key in enumerate(texture_keys):
    path=TEX/('ongeki_'+key+'.png');width,height=sizes[key]
    bbtex.append({'name':path.name,'folder':'block','namespace':'funpackcustom','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'ongeki/'+key)),'width':width,'height':height,
        'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'ongeki.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'ONGEKI','model_identifier':'ongeki','visible_box':[2,3,2],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'ongeki/group/'+name)),
                'origin':[8,0,8],'children':children} for name,children in groups.items()]})
for f in surfaces:
    assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
    a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    assert sum(v*v for v in cross)>1e-18,('Degenerate face',f['name'])
print('ONGEKI:',len(surfaces),'authoring faces; bounds',bounds)
print('Optimized native meshes:',stats)
