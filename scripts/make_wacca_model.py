"""Build WACCA with a smooth recessed cone, bevelled rim, and curved marquee.

The retained pedestal faces and continuous curved surfaces share native OBJ
exports. Original artwork and LED pixels remain unchanged; only geometry and
UV interpolation select them. The Blockbench file embeds the same textures.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from wacca_shell_geometry import build_shell
from wacca_ring_geometry import _write_led_atlas
from wacca_mesh_geometry import build_smooth_ring, smooth_polygon, export_wacca
from wacca_surface_geometry import optimize_surfaces

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/wacca'
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
ART.mkdir(parents=True,exist_ok=True)
TEXTURES.mkdir(parents=True,exist_ok=True)
MODEL.mkdir(parents=True,exist_ok=True)

PALETTE={
    'black':(16,18,25),'charcoal':(31,32,42),'white':(230,233,229),'ivory':(213,217,212),
    'silver':(167,178,187),'steel':(78,88,99),'rubber':(8,10,17),'vent':(20,23,30),
    'magenta':(191,28,166),'pink':(242,91,220),'cyan':(58,208,233),'purple':(109,41,213),
    'blue':(37,43,169),'rim_gray':(191,199,200),'warm_white':(244,238,204),'black_mesh':(25,28,35),
}
KEYS=list(PALETTE)
atlas=Image.new('RGB',(256,256))
rng=random.Random(710)
for i,name in enumerate(KEYS):
    tile=Image.new('RGB',(64,64),PALETTE[name]);d=ImageDraw.Draw(tile)
    for y in range(0,64,4):
        for x in range(0,64,4):
            n=rng.choice((-2,0,0,2))
            d.rectangle((x,y,x+3,y+3),fill=tuple(max(0,min(255,c+n)) for c in PALETTE[name]))
    if name=='ivory':
        for y in range(0,72,12):
            for x in range(-6,70,12):
                xx=x+(6 if (y//12)%2 else 0)
                d.polygon([(xx,y),(xx+6,y+12),(xx+12,y)],fill=(204,210,207))
                d.polygon([(xx,y),(xx-6,y+12),(xx+6,y+12)],fill=(219,223,218))
    if name in ('vent','black_mesh'):
        for y in range(4,64,7):
            for x in range(3,64,8):
                if name=='black_mesh':
                    d.polygon([(x,y),(x+3,y+5),(x+6,y)],fill=(5,8,14),outline=(46,51,57))
                else:d.rectangle((x,y,x+5,y+2),fill=(4,6,11))
    atlas.paste(tile,((i%4)*64,(i//4)*64))
atlas.save(TEXTURES/'wacca_materials.png')


def label(image,xy,text,size,fill,bold=False,anchor='mm'):
    font=ImageFont.truetype('C:/Windows/Fonts/'+('consolab.ttf' if bold else 'consola.ttf'),size)
    mask=Image.new('1',image.size)
    ImageDraw.Draw(mask).text(xy,text,font=font,fill=1,anchor=anchor)
    image.paste(fill,(0,0),mask)


# Wide printed panel below the ring; its layout matches the modeled reader,
# headphone socket, and coin slot. No piano keys or rotary controls on WACCA.
details=Image.new('RGB',(512,256),PALETTE['black']);d=ImageDraw.Draw(details)
for y in range(0,96,16):
    for x in range(-8,530,16):
        xx=x+(8 if (y//16)%2 else 0)
        d.polygon([(xx,y),(xx+8,y+16),(xx+16,y)],fill=(48,49,60))
d.line([(6,6),(506,6),(506,90),(6,90),(6,6)],fill=(241,78,217),width=3)
d.rounded_rectangle((20,14,78,81),radius=9,fill=(226,222,226),outline=(167,137,165),width=2)
label(details,(49,40),'Aime',17,(149,57,116),True)
label(details,(49,57),'CARD',10,(106,92,110))
label(details,(149,30),'MARVELOUS!',15,(226,149,62),True)
label(details,(156,63),'TOUCH THE MUSIC',10,(197,194,204))
for x in range(95,198,13):d.polygon([(x,44),(x+7,49),(x,54)],fill=(224,76,204))
d.rectangle((238,25,291,77),outline=(222,85,207),width=3)
label(details,(264,33),'AUDIO',9,(235,217,236),True)
label(details,(353,45),'WACCA',27,(238,128,227),True)
label(details,(353,65),'REVERSE',11,(163,155,201),True)
d.rectangle((424,12,494,29),fill=(212,179,91))
label(details,(459,20),'INSERT COIN',8,(28,28,35),True)
label(details,(457,77),'1 PLAY 100',9,(220,220,223),True)
for x in (88,100,112):d.rectangle((x,78,x+8,85),fill=(190,180,190))
# Small upper speaker grille and restrained rear labels.
for y in range(104,192,4):
    for x in range(3,92,4):d.rectangle((x,y,x+1,y+1),fill=(78,80,88))
label(details,(215,132),'WACCA',28,(188,191,200),True)
label(details,(215,164),'REVERSE',18,(204,87,178),True)
d.rectangle((332,110,494,171),fill=(196,200,200))
label(details,(413,126),'SERVICE / POWER',13,(39,43,51),True)
for x in range(345,484,4):d.line((x,145,x,161),fill=(33,35,43),width=1+x%3)
details.save(TEXTURES/'wacca_details.png')

source_scales={}
for key,source_name,target_name in (
        ('display','display-artwork-source.png','wacca_display.png'),
        ('branding','marquee-artwork-source.png','wacca_branding.png')):
    source=Image.open(ART/source_name).convert('RGB')
    size=tuple(1<<(n-1).bit_length() for n in source.size)
    packed=Image.new('RGB',size,PALETTE['black']);packed.paste(source,(0,0))
    packed.save(TEXTURES/target_name)
    source_scales[key]=tuple(n/p for n,p in zip(source.size,size))


def uv(name):
    i=KEYS.index(name)
    # Eight native pixels keep sampling inside this 64px material tile through
    # mip level 4. Exact tile/sprite boundaries can pick up neighboring colours.
    inset=.5
    return [(i%4)*4+inset,(i//4)*4+inset,(i%4)*4+4-inset,(i//4)*4+4-inset]


elements=[]
header_meshes=[]


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
    if group=='Curved marquee':
        assert rotation is None, 'The header retains its original upright plane'
        header_meshes.extend(smooth_polygon(name,points,z0,z1,material,group,front,glow,uv,source_scales))
        return
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
# Regenerate the exact same deterministic atlas; no artwork is changed.
_write_led_atlas(TEXTURES)
smooth_meshes,smooth_details=build_smooth_ring(uv,source_scales)

# Raised curved marquee behind the bowl. Dark upright speakers flank the sign,
# as in the reference, rather than adding large exposed circular speaker pods.
header=[(-1.55,38.10),(-1.30,42.76),(1.25,43.95),(4.55,44.70),(8,44.96),
        (11.45,44.70),(14.75,43.95),(17.30,42.76),(17.55,38.10),(15.95,37.34),
        (13.8,38.20),(11.12,39.18),(8,39.58),(4.88,39.18),(2.20,38.20),(.05,37.34)]
header=[(x,y-.8 if i==0 or i>=8 else y) for i,(x,y) in enumerate(header)]
polygon('Curved marquee black shell',header,7.20,9.23,'black',group='Curved marquee')
printed=[(-.56,41.70),(1.52,43.43),(4.63,44.17),(8,44.40),(11.37,44.17),
         (14.48,43.43),(16.56,41.70),(15.74,38.31),(13.47,39.12),(10.91,39.87),
         (8,40.13),(5.09,39.87),(2.53,39.12),(.26,38.31)]
printed=[(x,y-.8 if i>=7 else y) for i,(x,y) in enumerate(printed)]
polygon('Marquee silver edging',printed,7.07,7.38,'silver',group='Curved marquee')
inside=[((x-8)*.97+8,(y-41.3)*.96+41.3) for x,y in printed]
# Clip quiet ivory margins with the physical arch; the letterforms retain their
# native aspect and sit above the lower center curve, without a separate poster.
logo_width=max(x for x,y in inside)-min(x for x,y in inside)
logo_height=logo_width/(3*.78)
logo_top=41.20+logo_height/2
logo_v0=(logo_top-max(y for x,y in inside))/logo_height*16
logo_v1=(logo_top-min(y for x,y in inside))/logo_height*16
polygon('WACCA Reverse marquee print',inside,6.945,7.15,'warm_white',
        front=('branding',[1.76,logo_v0,14.24,logo_v1]),
        glow=('north',),group='Curved marquee')
for side,x0,x1 in (('Left',-1.24,.06),('Right',15.94,17.24)):
    cube(side+' marquee speaker inset',(x0,38.17,6.96),(x1,41.10,7.28),'rubber',group='Upper speakers')
    cube(side+' marquee speaker grille',(x0+.09,38.32,6.91),(x1-.09,40.91,7.04),'vent',
         north=('details',[0,6.5,3,12]),group='Upper speakers')
    for y in (38.40,40.77):
        cube(side+' header screw '+str(y),(x0+.13,y,6.87),(x0+.25,y+.12,6.97),'silver',group='Header fasteners')

texture_paths={
    'materials':'funpackcustom:block/wacca_materials','details':'funpackcustom:block/wacca_details',
    'leds':'funpackcustom:block/wacca_leds','display':'funpackcustom:block/wacca_display',
    'branding':'funpackcustom:block/wacca_branding','particle':'funpackcustom:block/wacca_materials',
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

# Bake only the opaque exterior. Adjacent pieces do not need internal faces;
# clipped overlaps have exactly one surface owner, eliminating coplanar fights.
elements,surface_details=optimize_surfaces(elements)

export_wacca(elements,smooth_meshes+header_meshes,texture_paths,surface_details,smooth_details,ROOT)
