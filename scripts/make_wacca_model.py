"""Build a WACCA Reverse cabinet with a recessed, segmented touch bowl.

All geometry is native Java-model cuboids. Original imagegen artwork is packed
unchanged; only model UVs select it. The Blockbench file embeds the same textures.
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
from wacca_shell_geometry import build_shell
from wacca_ring_geometry import build_touch_bowl

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


def circle_points(cx,cy,r,n=192):
    return [(cx+r*math.sin(i*2*math.pi/n),cy+r*math.cos(i*2*math.pi/n)) for i in range(n)]


def annulus(name,cx,cy,outer,inner,z0,z1,material,group,step=.125):
    # Two spans on each scanline leave the center genuinely open.
    count=math.ceil(2*outer/step);dy=2*outer/count
    for i in range(count):
        y=cy-outer+(i+.5)*dy
        dx=math.sqrt(max(0,outer*outer-(y-cy)**2))
        hole=math.sqrt(max(0,inner*inner-(y-cy)**2))
        lo=cy-outer+i*dy;hi=lo+dy
        spans=[(-dx,-hole),(hole,dx)] if hole>.05 else [(-dx,dx)]
        for j,(a,b) in enumerate(spans):
            a=round(a/step)*step;b=round(b/step)*step
            if b>a:cube(name+f' course {i:02d}-{j}',(cx+a,lo,z0),(cx+b,hi,z1),material,group=group)


build_shell(cube,polygon)

# Main touch ring: the outside edge is forward, while the smaller round display
# is physically recessed behind a deep annular bank of touch-sensitive panels.
ring_start=len(elements)
cx,cy=8,28.2
polygon('Circular rear display enclosure',circle_points(cx,cy,10.70),7.65,9.12,'black',group='Ring rear enclosure')
annulus('Outer white barrel',cx,cy,10.94,10.23,1.48,7.72,'ivory','White outer ring')
annulus('Outer rim rear seam',cx,cy,11.00,10.73,1.38,2.02,'rim_gray','White outer ring')
annulus('Broad molded white rim',cx,cy,11.00,10.28,1.06,1.61,'white','White outer ring')
annulus('Inner rim silver return',cx,cy,10.34,10.17,1.23,1.69,'silver','White outer ring')

annulus('Circular screen black gasket',cx,cy,6.38,6.13,5.80,6.23,'rubber','Recessed circular monitor',step=.125)
polygon('WACCA Reverse circular display',circle_points(cx,cy,6.18),5.82,5.99,'black',
        front=('display',[0,0,16,16]),glow=('north',),group='Recessed circular monitor',step=.125)

# Eight breaks and small fixing covers in the molded white ring are physical.
for i in range(8):
    angle=i*math.pi/4
    x=cx+10.64*math.sin(angle);y=cy+10.64*math.cos(angle)
    if i%2==0:
        width,height=(.08,.67) if i in (0,4) else (.67,.08)
        cube('White rim panel seam '+str(i),(x-width/2,y-height/2,1.035),
             (x+width/2,y+height/2,1.09),'rim_gray',group='Rim panel divisions')
    else:
        seam=[(cx+r*math.sin(angle+da),cy+r*math.cos(angle+da))
              for r,da in ((10.30,-.003),(10.99,-.003),(10.99,.003),(10.30,.003))]
        polygon('Diagonal white rim seam '+str(i),seam,1.025,1.09,'rim_gray',
                group='Rim panel divisions',step=.08)

# A slight lean follows the real side profile. Short courses make the slope
# compatible with vanilla rotations and preserve the screen print continuously.
ring_elements=elements[ring_start:];elements=elements[:ring_start]
for e in ring_elements:
    bottom,top=e['from'][1],e['to'][1]
    count=max(1,math.ceil((top-bottom)/.25))
    for i in range(count):
        part=copy.deepcopy(e)
        y0=bottom+(top-bottom)*i/count;y1=bottom+(top-bottom)*(i+1)/count
        dz=((y0+y1)/2-17.2)*.10
        part['from'][1]=y0;part['to'][1]=y1
        part['from'][2]+=dz;part['to'][2]+=dz
        part['name']+=f' lean {i:02d}'
        for direction in ('north','south','east','west'):
            u0,v0,u1,v1=e['faces'][direction]['uv']
            part['faces'][direction]['uv']=[u0,v0+(top-y1)/(top-bottom)*(v1-v0),
                                            u1,v0+(top-y0)/(top-bottom)*(v1-v0)]
        # At a display/rim course boundary carry the print over the tiny ledge.
        front=part['faces']['north'];u0,v0,u1,v1=front['uv']
        for direction,v in (('up',v0),('down',v1)):
            part['faces'][direction]=copy.deepcopy(front)
            part['faces'][direction]['uv']=[u0,v,u1,v]
        elements.append(part)

# The fine bowl already includes its lean in the quantized depth. A continuous
# XY texture lets neighboring coplanar cells merge without interrupting light.
bowl_details=build_touch_bowl(cube,TEXTURES)

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
polygon('Marquee luminous ivory panel',inside,6.99,7.15,'warm_white',glow=('north',),group='Curved marquee')
# Clip quiet ivory margins with the physical arch; the letterforms retain their
# native aspect and sit above the lower center curve, without a separate poster.
logo_width=max(x for x,y in inside)-min(x for x,y in inside)
logo_height=logo_width/(3*.78)
logo_top=41.20+logo_height/2
logo_v0=(logo_top-max(y for x,y in inside))/logo_height*16
logo_v1=(logo_top-min(y for x,y in inside))/logo_height*16
polygon('WACCA Reverse marquee print',inside,6.945,7.02,'warm_white',
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
    write_json(MODEL / ('wacca_'+part+'.json'),
               {'parent':'minecraft:block/block','ambientocclusion':True,'render_type':'minecraft:cutout',
                'textures':texture_paths,'elements':parts[part]})
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'funpackcustom:block/wacca_'+part}
        if rotation: variant['y']=rotation
        variants['facing='+facing+',part='+part]=variant
write_json(ASSETS / 'blockstates/wacca.json', {'variants':variants})

# An explicitly scaled complete model for inventory rendering (vanilla element bounds).
item_elements=[]
for source in elements:
    e=strip_element(source)
    for key in ('from','to'):
        e[key]=[round(e[key][0]*0.35+5.2,5),round(e[key][1]*0.35,5),round(e[key][2]*0.35+5.2,5)]
    if 'rotation' in e:
        o=e['rotation']['origin'];e['rotation']['origin']=[o[0]*.35+5.2,o[1]*.35,o[2]*.35+5.2]
    item_elements.append(e)
write_json(ASSETS / 'models/item/wacca.json',
           {'ambientocclusion':False,'gui_light':'front','textures':texture_paths,'elements':item_elements,
            'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                       'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                       'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                       'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                       'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})

artwork=TEXTURES / 'wacca_display.png'
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
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'funpackcustom/wacca/'+e['name']+'/'+str(e['from'])))
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
    bbtextures.append({'path':str(path),'name':path.name,'folder':'block','namespace':'funpackcustom',
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'wacca/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/funpackcustom/textures/block/'+path.name,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                       'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'wacca.bbmodel',
           {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
            'name':'WACCA Reverse','model_identifier':'wacca','visible_box':[2,4,1.5],
            'resolution':{'width':256,'height':256},'elements':bb_elements,'textures':bbtextures,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'wacca/group/'+name)),
                         'origin':[8,0,8],'children':children} for name,children in groups.items()]})
write_json(ART/'geometry.json', {'textures':texture_paths,'elements':elements})
print('Generated',len(elements),'cuboids; section counts:',{name:len(values) for name,values in parts.items()})
print('Touch bowl:',bowl_details)
print('Editable model:',ART/'wacca.bbmodel')
