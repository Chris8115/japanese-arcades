"""Build the wider Sound Voltex Valkyrie cabinet, native models and Blockbench file.

Coordinates are designed from the front, then mirrored for Minecraft north UVs.
The generated display/branding artwork is packed unchanged into power-of-two
textures. Technical patterns, manufactured materials and geometry are native code.
"""
from __future__ import annotations

import base64
import copy
import json
import math
import random
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from valkyrie_lower_geometry import build_lower

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/sound-voltex-valkyrie'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
ART.mkdir(parents=True,exist_ok=True)
TEXTURES.mkdir(parents=True,exist_ok=True)
MODEL.mkdir(parents=True,exist_ok=True)

PALETTE={
    'black':(18,21,27),'charcoal':(36,40,49),'steel':(75,84,101),'silver':(175,187,199),
    'white':(223,232,235),'cyan':(22,183,205),'cyan_bright':(141,245,246),'teal':(23,109,132),
    'blue':(26,104,205),'purple':(120,69,207),'magenta':(226,54,166),'pink':(251,157,213),
    'button':(240,241,227),'vent':(15,18,23),'rubber':(9,12,17),'glass':(26,59,69),
}
KEYS=list(PALETTE)
atlas=Image.new('RGB',(256,256))
rng=random.Random(606)
for i,name in enumerate(KEYS):
    tile=Image.new('RGB',(64,64),PALETTE[name]);d=ImageDraw.Draw(tile)
    for y in range(0,64,4):
        for x in range(0,64,4):
            noise=rng.choice((-2,0,0,2))
            d.rectangle((x,y,x+3,y+3),fill=tuple(max(0,min(255,c+noise)) for c in PALETTE[name]))
    if name in ('silver','steel','white','button'):
        d.line((0,0,63,0),fill=tuple(min(255,c+20) for c in PALETTE[name]),width=2)
        d.line((0,63,63,63),fill=tuple(max(0,c-22) for c in PALETTE[name]),width=2)
    if name=='vent':
        for y in range(4,62,6):
            d.line((5,y,58,y),fill=(5,7,11),width=3)
            d.line((5,y+3,58,y+3),fill=(50,54,62))
    if name=='glass':
        for x in (8,28,48):
            d.line([(x,0),(x,18),(x+8,26),(x+8,46),(x,54),(x,63)],fill=(70,133,148),width=1)
        for x,y in ((8,10),(36,34),(48,58)):
            d.rectangle((x-1,y-1,x+1,y+1),fill=(141,205,207))
    atlas.paste(tile,((i%4)*64,(i//4)*64))
atlas.save(TEXTURES/'valkyrie_materials.png')


def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('consolab.ttf' if bold else 'consola.ttf'),size)


def label(image,xy,text,size,fill,bold=False,anchor='mm'):
    mask=Image.new('1',image.size)
    ImageDraw.Draw(mask).text(xy,text,font=font(size,bold),fill=1,anchor=anchor)
    image.paste(fill,(0,0),mask)


details=Image.new('RGB',(512,256),PALETTE['black']);d=ImageDraw.Draw(details)
# A dark physical speaker cone. Concentric hard-edged bands read in Minecraft.
for radius,color in ((61,(22,26,33)),(57,(48,53,62)),(52,(13,17,24)),(46,(27,32,39)),
                     (39,(43,49,55)),(32,(30,35,42)),(23,(17,22,29)),(18,(45,51,56))):
    d.ellipse((64-radius,64-radius,64+radius,64+radius),fill=color)
for radius in (35,40,46):
    d.ellipse((64-radius,64-radius,64+radius,64+radius),outline=(56,62,65),width=1)
for n in range(24):
    angle=n*math.pi/12
    a=(64+math.cos(angle)*25,64+math.sin(angle)*25)
    b=(64+math.cos(angle)*44,64+math.sin(angle)*44)
    d.line((a,b),fill=(17,22,28))
d.ellipse((50,50,78,78),fill=(25,31,37),outline=(57,67,71))
label(details,(64,64),'SDVX',9,(100,113,119),True)
for x,y in ((22,22),(106,22),(22,106),(106,106)):
    d.rectangle((x-2,y-2,x+2,y+2),fill=(121,132,136))
    d.line((x-1,y,x+1,y),fill=(25,29,34))
# 6:1 belt nameplate, exact aspect so the lettering isn't flattened.
d.rectangle((129,1,510,62),outline=(152,169,182),width=2)
d.line([(140,4),(168,30),(140,60)],fill=(63,73,85),width=2)
d.line([(500,4),(472,30),(500,60)],fill=(63,73,85),width=2)
label(details,(320,24),'SOUND VOLTEX',18,(232,242,243),True)
label(details,(320,44),'- Valkyrie model -',16,(90,236,236),True)
for x in (147,493):
    d.rectangle((x-3,28,x+3,34),outline=(164,183,190))
    d.line((x-1,31,x+1,31),fill=(206,223,226))
# Three equal small regions: caution, serial badge, card mark.
for x in (134,262,390):
    d.rectangle((x,72,x+111,117),fill=(30,34,40),outline=(127,145,158))
d.rectangle((139,77,240,87),fill=(233,187,51))
label(details,(190,82),'CAUTION',8,(30,29,23),True)
for y in (94,100,106):
    for x in range(141,236,13): d.line((x,y,x+8,y),fill=(142,153,158))
label(details,(318,87),'VALKYRIE',11,(201,215,221),True)
for x in range(271,363,4):d.line((x,97,x,109),fill=(121,138,150),width=1+(x%3==0))
d.rectangle((397,79,438,109),fill=(154,30,68))
label(details,(418,94),'e',25,(247,226,235),True)
label(details,(470,94),'PASS',10,(115,219,230),True)
details.save(TEXTURES/'valkyrie_details.png')

# Edge-lit acrylic wing: crisp cyan-to-violet bands with inset circuit etching.
wing=Image.new('RGB',(128,384));d=ImageDraw.Draw(wing)
bands=[(110,64,190),(104,89,210),(74,128,219),(43,175,222),(32,196,215),(39,206,214),
       (24,186,204),(22,165,187)]
for y in range(384): d.line((0,y,127,y),fill=bands[min(7,y//48)])
for offset in (-26,1,28,55,82):
    points=[(offset,0),(offset+8,62),(offset+43,129),(offset+43,182),(offset+26,208),
            (offset+32,285),(offset+62,383)]
    d.line(points,fill=(137,241,239),width=3)
    d.line([(x+6,y) for x,y in points],fill=(52,145,175),width=1)
for x,y in ((18,61),(87,134),(56,208),(102,294),(45,344)):
    d.rectangle((x-2,y-2,x+2,y+2),fill=(201,255,251))
wing.save(TEXTURES/'valkyrie_wing.png')

side=Image.new('RGB',(128,512),PALETTE['black']);d=ImageDraw.Draw(side)
d.line([(10,0),(10,392),(56,490),(118,490)],fill=(221,232,236),width=4)
d.line([(24,0),(24,380),(68,478),(117,478)],fill=(88,115,135),width=2)
text_strip=Image.new('RGB',(420,68),PALETTE['black'])
label(text_strip,(210,22),'SOUND VOLTEX',38,(227,236,239),True)
label(text_strip,(210,53),'VALKYRIE MODEL',16,(94,201,216),True)
side.paste(text_strip.transpose(Image.Transpose.ROTATE_270),(40,30))
side.save(TEXTURES/'valkyrie_side.png')

source_scales={}
for key,source_name,target_name in (
        ('display','display-artwork-source.png','valkyrie_display.png'),
        ('branding','marquee-artwork-source.png','valkyrie_branding.png')):
    source=Image.open(ART/source_name).convert('RGB')
    size=tuple(1<<(n-1).bit_length() for n in source.size)
    packed=Image.new('RGB',size,PALETTE['black']);packed.paste(source,(0,0))
    packed.save(TEXTURES/target_name)
    source_scales[key]=tuple(n/p for n,p in zip(source.size,size))


def uv(name):
    i=KEYS.index(name)
    return [(i%4)*4,(i//4)*4,(i%4)*4+4,(i//4)*4+4]


elements=[]


def cube(name,start,end,material='black',*,north=None,east=None,west=None,south=None,
         up=None,down=None,rotation=None,glow=False,group='Cabinet'):
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
    elements.append(element)


def polygon(name,points,z0,z1,material,*,group='Sculpted panels',glow=False,front=None,rotation=None,step=.25):
    """Extrude an outline on a 1/4-unit grid, retaining notches and merging runs."""
    minx,maxx=min(x for x,y in points),max(x for x,y in points)
    miny,maxy=min(y for x,y in points),max(y for x,y in points)
    count=max(1,math.ceil((maxy-miny)/step));dy=(maxy-miny)/count
    rows=[];active={}
    for i in range(count):
        y=miny+(i+.5)*dy
        cross=[]
        for a,b in zip(points,points[1:]+points[:1]):
            if min(a[1],b[1])<=y<max(a[1],b[1]):
                cross.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
        cross.sort();following={}
        for j in range(0,len(cross)-1,2):
            left=max(minx,round(cross[j]/step)*step)
            right=min(maxx,round(cross[j+1]/step)*step)
            if right<=left: continue
            key=(left,right)
            if key in active:
                rect=active.pop(key);rect[3]=miny+(i+1)*dy
            else: rect=[left,right,miny+i*dy,miny+(i+1)*dy]
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


def disc(name,cx,cy,z,radius,depth,material,*,rotation=None,group='Speakers',front=None,glow=False):
    points=[(cx+radius*math.sin(n*math.pi/8),cy+radius*math.cos(n*math.pi/8)) for n in range(16)]
    polygon(name,points,z,z+depth,material,rotation=rotation,group=group,front=front,glow=glow,step=.20)


def speaker(name,cx,cy,z,radius,*,rotation=None,group='Speakers',silver=False):
    disc(name+' structural rim',cx,cy,z+.10,radius,.25,'steel',rotation=rotation,group=group)
    disc(name+' blue outer light',cx,cy,z+.055,radius*.94,.16,'blue',rotation=rotation,group=group,glow=('north',))
    disc(name+' cyan light ring',cx,cy,z,radius*.85,.14,'cyan',rotation=rotation,group=group,glow=('north',))
    disc(name+' bright inner ring',cx,cy,z-.02,radius*.78,.13,'cyan_bright',rotation=rotation,group=group,glow=('north',))
    disc(name+' black cone rim',cx,cy,z-.065,radius*.71,.17,'rubber',rotation=rotation,group=group)
    disc(name+' recessed cone',cx,cy,z-.085,radius*.63,.10,'charcoal',rotation=rotation,group=group,
         front=None if silver else ('details',[0,0,4,8]))
    disc(name+' center dome',cx,cy,z-.13,radius*.26,.10,'silver' if silver else 'black',rotation=rotation,group=group)


build_lower(cube,uv,polygon,speaker)

# The real pedestal light assembly ramps gently into the cabinet as it rises.
# A ten-degree lean is subtler than vanilla's minimum 22.5-degree element
# rotation. Closely spaced cuboid courses preserve that shallow profile, keep
# the bottom near the footwell midpoint, and retain the original artwork UVs.
ramped=[]
for element in elements:
    if element['_group'] not in ('Luminous lower V','Lower subwoofer'):
        ramped.append(element)
        continue
    assert 'rotation' not in element, element['name']
    bottom,top=element['from'][1],element['to'][1]
    courses=max(1,math.ceil((top-bottom)/.25))
    for i in range(courses):
        part=copy.deepcopy(element)
        y0=bottom+(top-bottom)*i/courses
        y1=bottom+(top-bottom)*(i+1)/courses
        shift=((y0+y1)/2-3.53)*math.tan(math.radians(10))
        part['name']+=' ramp course %02d'%i
        part['from'][1],part['to'][1]=y0,y1
        part['from'][2]+=shift
        part['to'][2]+=shift
        for direction in ('north','south','east','west'):
            u0,v0,u1,v1=element['faces'][direction]['uv']
            part['faces'][direction]['uv']=[u0,v0+(top-y1)/(top-bottom)*(v1-v0),
                                            u1,v0+(top-y0)/(top-bottom)*(v1-v0)]
        # Carry the front print/light across the tiny step ledges. Otherwise
        # their dark unlit material repeats as horizontal stripes on the glass.
        front=part['faces']['north']
        u0,v0,u1,v1=front['uv']
        for direction,v in (('up',v0),('down',v1)):
            part['faces'][direction]=copy.deepcopy(front)
            part['faces'][direction]['uv']=[u0,v,u1,v]
        ramped.append(part)
elements=ramped

# A substantial rear tower fills the space behind the display and the LED wings.
for y0,y1 in ((18,32),(32,42.1)):
    cube('Upper rear chassis '+str(y0),(2.7,y0,9.4),(13.3,y1,15.25),'black',group='Rear tower')
cube('Rear display service cover',(3.10,24.6,15.26),(12.90,40.8,15.36),'charcoal',group='Rear tower')
for y in (28,34.5):
    cube('Rear display ventilation '+str(y),(6.0,y,15.37),(9.8,y+2.2,15.46),'vent',group='Rear tower')
for x in (3.35,12.43):
    for y in (25.0,40.30):
        cube('Rear display screw '+str((x,y)),(x,y,15.37),(x+.16,y+.16,15.46),'silver',group='Rear tower')
cube('Portrait display rear case',(2.90,23.30,8.10),(13.10,40.90,10.20),'charcoal',group='Portrait display')
cube('Portrait display silver inset',(3.11,23.47,7.97),(12.89,40.74,8.23),'steel',group='Portrait display')
cube('Portrait display black bezel',(3.29,23.67,7.84),(12.71,40.57,8.09),'rubber',group='Portrait display')
cube('Exceed Gear portrait screen',(3.62,24.02,7.81),(12.38,40.20,7.89),'glass',
     north=('display',[0,0,16,16]),glow=('north',),group='Portrait display')
for x in (3.40,12.52):
    cube('Monitor thin silver seam '+str(x),(x,23.78,7.80),(x+.07,40.48,7.94),'silver',group='Portrait display')
cube('Display lower model badge',(6.0,23.39,7.77),(10.0,23.84,7.85),'black',
     north=('details',[4,0,16,4]),group='Portrait display')

# Mirrored faceted acrylic blades: a thick black carrier, silver bevel, inset
# colored panel, and applied raised traces. The white rails remain physical.
for side,mirror in (('Left',False),('Right',True)):
    def reflect(points): return [(16-x if mirror else x,y) for x,y in points]
    outer=[(-2.4,39.5),(2.75,37.52),(3.31,24.18),(-.26,26.36),(-1.62,31.15)]
    middle=[(-2.22,39.24),(2.54,37.39),(3.12,24.45),(-.08,26.50),(-1.43,31.22)]
    panel=[(-1.91,38.83),(2.22,37.15),(2.78,24.99),(.15,26.83),(-1.12,31.33)]
    polygon(side+' wing black carrier',reflect(outer),7.55,9.40,'black',group='Acrylic wings')
    polygon(side+' wing silver perimeter',reflect(middle),7.37,7.80,'silver',group='Acrylic wings')
    polygon(side+' illuminated acrylic',reflect(panel),7.28,7.49,'cyan',
            front=('wing',[16,0,0,16] if mirror else [0,0,16,16]),glow=('north',),group='Acrylic wings')
    inner=[(2.20,37.15),(2.42,37.05),(2.98,24.87),(2.75,24.76)]
    polygon(side+' long white light guide',reflect(inner),7.16,7.41,'cyan_bright',glow=('north',),group='Wing light guides')
    for i,points in enumerate((
            [(-1.70,38.31),(-1.39,38.17),(.94,29.62),(.68,29.72)],
            [(-1.16,35.37),(-.86,35.18),(.87,30.70),(.62,30.46)],
            [(.65,29.73),(.99,29.43),(1.95,25.73),(1.64,25.96)])):
        polygon(side+' raised blade etching '+str(i),reflect(points),7.15,7.37,'teal',group='Wing light guides')
    for x,y in ((-1.95,38.63),(-.94,32.26),(.48,26.54),(2.42,36.98)):
        x=16-x if mirror else x
        cube(side+' wing fixing '+str((x,y)),(x-.075,y-.075,7.16),(x+.075,y+.075,7.30),'steel',group='Wing hardware')
    # Thin rear supports connect the outer panels to the display chassis.
    x0,x1=((-1.2,3.0) if not mirror else (13.0,17.2))
    cube(side+' wing mounting strut',(x0,29.65,9.0),(x1,30.2,11.7),'charcoal',group='Rear wing supports')

# The Valkyrie's high speaker wings and broad angular crown distinguish it from
# the standard cabinet. Upper pods form asymmetrical trapezoids, not square boxes.
for side,mirror in (('Left',False),('Right',True)):
    def reflect(points):return [(16-x if mirror else x,y) for x,y in points]
    pod=[(-3.0,39.1),(-2.55,46.90),(3.25,43.55),(3.28,39.42),(-.88,37.90)]
    inset=[(-2.73,39.28),(-2.31,46.37),(2.98,43.40),(3.01,39.58),(-.83,38.17)]
    polygon(side+' upper speaker casing',reflect(pod),6.73,9.30,'black',group='Upper speakers')
    polygon(side+' upper speaker face',reflect(inset),6.58,6.83,'charcoal',group='Upper speakers')
    x=16-.08 if mirror else .08
    speaker(side+' upper speaker',x,41.57,6.40,2.16,group='Upper speakers')
    for x,y in ((-2.20,45.50),(-2.32,39.34),(2.68,42.97)):
        x=16-x if mirror else x
        cube(side+' upper speaker fastener '+str((x,y)),(x-.10,y-.10,6.46),(x+.10,y+.10,6.61),'silver',group='Upper speaker hardware')

# Layered cut corners and separate emissive light paths make the marquee a
# physical sculpted part rather than a rectangular sign stuck on the tower.
crown=[(-1.65,47.85),(2.24,47.30),(3.10,46.18),(12.90,46.18),(13.76,47.30),(17.65,47.85),
       (15.91,42.38),(13.21,41.64),(11.94,42.54),(4.06,42.54),(2.79,41.64),(.09,42.38)]
# Multiple scanline intervals preserve the lowered center between its high tips.
polygon('Marquee black cast back',crown,5.76,7.22,'black',group='Sculpted crown')
crown_face=[(x*.98+.16,(y-44.5)*.95+44.5) for x,y in crown]
polygon('Marquee silver perimeter',crown_face,5.58,5.93,'steel',group='Sculpted crown')
inner=[(-1.05,47.28),(2.02,46.89),(2.88,45.77),(13.12,45.77),(13.98,46.89),(17.05,47.28),
       (15.50,42.72),(13.22,42.11),(11.82,42.98),(4.18,42.98),(2.78,42.11),(.50,42.72)]
polygon('Marquee graphite face',inner,5.49,5.79,'black',group='Sculpted crown')
# The 3:1 source fits a 12x4 panel: all lettering falls inside the crown's
# central band. Clip only the decorative margins to the physical silhouette.
art_outline=inner[:]
for axis,bound,keep_greater in ((0,2,True),(0,14,False),(1,42.30,True),(1,46.30,False)):
    clipped=[]
    for a,b in zip(art_outline,art_outline[1:]+art_outline[:1]):
        a_inside=(a[axis]>=bound) if keep_greater else (a[axis]<=bound)
        b_inside=(b[axis]>=bound) if keep_greater else (b[axis]<=bound)
        if a_inside:clipped.append(a)
        if a_inside != b_inside:
            t=(bound-a[axis])/(b[axis]-a[axis])
            clipped.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
    art_outline=clipped
polygon('Exceed Gear marquee artwork',art_outline,5.405,5.50,'black',
        front=('branding',[0,0,16,16]),
        glow=('north',),group='Sculpted crown')
for side,mirror in (('Left',False),('Right',True)):
    def reflect(points):return [(16-x if mirror else x,y) for x,y in points]
    for i,points in enumerate((
        [(-.83,47.03),(1.89,46.63),(2.27,46.01),(.01,46.21)],
        [(-.22,46.01),(.38,44.92),(1.12,45.15),(1.87,46.10)],
        [(.96,42.92),(2.64,42.49),(3.73,43.11),(3.12,43.34)],
        [(3.64,46.27),(7.70,46.27),(7.70,46.43),(3.46,46.43)],
        [(4.06,42.87),(7.71,42.87),(7.71,42.69),(4.22,42.69)])):
        polygon(side+' crown cyan inlay '+str(i),reflect(points),5.33,5.54,'cyan',glow=('north',),group='Crown lights',step=.125)
for x in (-1.02,17.02):
    cube('Crown outer screw '+str(x),(x-.08,47.21,5.45),(x+.08,47.37,5.62),'silver',group='Crown hardware')
polygon('Marquee center diamond',[(8,42.27),(7.72,42.65),(8,43.03),(8.28,42.65)],5.31,5.56,'cyan_bright',
        glow=('north',),group='Crown lights',step=.125)

texture_paths={
    'materials':'japanesearcades:block/valkyrie_materials','details':'japanesearcades:block/valkyrie_details',
    'display':'japanesearcades:block/valkyrie_display','branding':'japanesearcades:block/valkyrie_branding',
    'wing':'japanesearcades:block/valkyrie_wing','side':'japanesearcades:block/valkyrie_side',
    'particle':'japanesearcades:block/valkyrie_materials',
}

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
    write_json(MODEL / ('sound_voltex_valkyrie_'+part+'.json'),
               {'parent':'minecraft:block/block','ambientocclusion':True,'render_type':'minecraft:cutout',
                'textures':texture_paths,'elements':parts[part]})
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'japanesearcades:block/sound_voltex_valkyrie_'+part}
        if rotation: variant['y']=rotation
        variants['facing='+facing+',part='+part]=variant
write_json(ASSETS / 'blockstates/sound_voltex_valkyrie.json', {'variants':variants})

# An explicitly scaled complete model for inventory rendering (vanilla element bounds).
item_elements=[]
for source in elements:
    e=strip_element(source)
    for key in ('from','to'):
        e[key]=[round(e[key][0]*0.35+5.2,5),round(e[key][1]*0.35,5),round(e[key][2]*0.35+5.2,5)]
    if 'rotation' in e:
        o=e['rotation']['origin'];e['rotation']['origin']=[o[0]*.35+5.2,o[1]*.35,o[2]*.35+5.2]
    item_elements.append(e)
write_json(ASSETS / 'models/item/sound_voltex_valkyrie.json',
           {'ambientocclusion':False,'gui_light':'front','textures':texture_paths,'elements':item_elements,
            'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                       'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                       'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                       'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                       'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})

artwork=TEXTURES / 'valkyrie_display.png'
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
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'japanesearcades/valkyrie/'+e['name']+'/'+str(e['from'])))
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
bbtextures=[]
for i,(identifier,path) in enumerate(texture_specs):
    texture=Image.open(path)
    bbtextures.append({'path':str(path),'name':path.name,'folder':'block','namespace':'japanesearcades',
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'valkyrie/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/japanesearcades/textures/block/'+path.name,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                       'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'sound-voltex-valkyrie.bbmodel',
           {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
            'name':'Sound Voltex Valkyrie','model_identifier':'sound_voltex_valkyrie','visible_box':[2,4,1.5],
            'resolution':{'width':256,'height':256},'elements':bb_elements,'textures':bbtextures,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'valkyrie/group/'+name)),
                         'origin':[8,0,8],'children':children} for name,children in groups.items()]})
write_json(ART/'geometry.json', {'textures':texture_paths,'elements':elements})
print('Generated',len(elements),'cuboids; section counts:',{name:len(values) for name,values in parts.items()})
print('Editable model:',ART/'sound-voltex-valkyrie.bbmodel')

# Trim unused artwork borders after all runtime and authoring exports exist.
from compact_cabinet_textures import compact_cabinet
compact_cabinet('valkyrie')
