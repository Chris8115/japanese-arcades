"""Build the cabinet's Minecraft JSON models and editable Blockbench project.

Geometry and the material sheet are deterministic. The separate artwork sheet is
the original imagegen output; this script does not crop or edit that image.
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

from nostalgia_cabinet_geometry import build_cabinet
from nostalgia_console_geometry import build_console
from nostalgia_marquee_geometry import build_marquee
from nostalgia_surface_art import build_surface_art

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
ART = ROOT / 'art/nostalgia-op3'
TEXTURES = ASSETS / 'textures/block'
MODEL = ASSETS / 'models/block'
ART.mkdir(parents=True, exist_ok=True)
TEXTURES.mkdir(parents=True, exist_ok=True)
MODEL.mkdir(parents=True, exist_ok=True)

# Texture packing only: put the original pixels into a power-of-two canvas.
# The generated source remains untouched, with no crop, resampling, or repainting.
artwork_source = ART / 'artwork-source.png'
if not artwork_source.exists():
    raise SystemExit('Missing original artwork: '+str(artwork_source))
source_art = Image.open(artwork_source)
assert source_art.width == source_art.height, 'The source uses a square 2x2 layout'
art_size = 1 << (source_art.width-1).bit_length()
packed_art = Image.new('RGB', (art_size,art_size), (16,16,24))
packed_art.paste(source_art, (0,0))
packed_art.save(TEXTURES / 'nostalgia_artwork.png')
ART_UV_SCALE = source_art.width / art_size

# Preserve the generated cutout alpha when packing the marquee sprite atlas.
marquee_source = Image.open(ART / 'marquee-artwork-v2.png').convert('RGBA')
assert marquee_source.getextrema()[3][0] == 0, 'Marquee sprites need a transparent background'
marquee_size = tuple(1 << (n-1).bit_length() for n in marquee_source.size)
marquee_atlas = Image.new('RGBA', marquee_size, (0,0,0,0))
marquee_atlas.paste(marquee_source, (0,0))
marquee_atlas.save(TEXTURES / 'nostalgia_marquee.png')
MARQUEE_UV_SCALE = tuple(n/p for n,p in zip(marquee_source.size,marquee_size))

TILE = 64
PALETTE = {
    'black': (23, 24, 30), 'ivory': (228, 218, 197), 'gold': (174, 134, 63),
    'silver': (136, 143, 161), 'white_key': (247, 236, 209), 'black_key': (29, 24, 30),
    'teal': (88, 203, 219), 'pink': (211, 136, 174), 'lavender': (156, 147, 217),
    'blue': (139, 189, 224), 'speaker': (230, 221, 198), 'triangle': (25, 26, 33),
    'rhythm': (41, 30, 69), 'vent': (26, 28, 33), 'red_key': (201, 68, 91),
    'label': (243, 225, 193),
}
KEYS = list(PALETTE)
ATLAS = Image.new('RGB', (TILE * 4, TILE * 4))
rng = random.Random(303)

def font(size: int, serif: bool = False):
    file = Path('C:/Windows/Fonts/georgia.ttf' if serif else 'C:/Windows/Fonts/consola.ttf')
    return ImageFont.truetype(str(file), size)

def centered(draw, xy, text, size, fill, serif=False):
    draw.text(xy, text, font=font(size, serif), fill=fill, anchor='mm')

def tile_image(name):
    color = PALETTE[name]
    im = Image.new('RGB', (TILE, TILE), color)
    p = im.load()
    for y in range(0,TILE,4):
        for x in range(0,TILE,4):
            noise = rng.choice([-3, -2, 0, 0, 2, 3])
            for dy in range(4):
                for dx in range(4):
                    p[x+dx, y+dy] = tuple(max(0, min(255, c + noise)) for c in color)
    d = ImageDraw.Draw(im)
    if name == 'ivory':
        for _ in range(18):
            x, y = rng.randrange(64), rng.randrange(64)
            d.line([(x-2, y), (x, y-2), (x+2, y), (x, y+2), (x-2, y)], fill=(204, 183, 132))
    elif name in ('silver', 'gold', 'white_key'):
        for x in range(64):
            delta = int(14 * math.cos(x / 64 * math.pi))
            d.line([(x, 0), (x, 63)], fill=tuple(max(0, min(255, c + delta)) for c in color))
        d.line([(0, 0), (63, 0)], fill=tuple(min(255, c+25) for c in color))
        d.line([(0, 63), (63, 63)], fill=tuple(max(0, c-25) for c in color))
    elif name == 'speaker':
        d.ellipse((3, 3, 60, 60), fill=(154, 153, 150), outline=(191, 182, 151), width=2)
        for y in range(8, 57, 3):
            for x in range(8, 57, 3):
                if (x-31.5)**2 + (y-31.5)**2 < 24**2:
                    d.rectangle((x, y, x+1, y+1), fill=(43, 44, 47))
        for x, y in ((3,3), (59,3), (3,59), (59,59)):
            d.rectangle((x, y, x+1, y+1), fill=(82, 86, 92))
    elif name == 'triangle':
        d.polygon([(32, 5), (4, 58), (60, 58)], fill=(38,40,46), outline=(147,144,139), width=1)
        d.line([(32,10),(10,55),(54,55),(32,10)], fill=(90,91,96), width=1)
        for radius in (9, 11, 15, 17):
            d.ellipse((32-radius,38-radius,32+radius,38+radius), outline=(115,113,119), width=1)
        for n in range(24):
            angle=n*math.pi/12
            x,y=round(32+19*math.cos(angle)),round(38+19*math.sin(angle))
            if y<55 and abs(x-32)<(y-5)*.51:
                d.point((x,y),fill=(193,183,165))
        for x,y in ((27,23),(37,23),(19,45),(46,46),(32,52),(24,50),(39,51)):
            d.polygon([(x,y-1),(x-1,y+1),(x+1,y+1)],fill=(144,139,143))
        for x,y in ((32,14),(14,51),(50,51)):
            d.rectangle((x-1,y-1,x+1,y+1), fill=(175,171,179))
    elif name == 'rhythm':
        for y in range(64):
            glow = max(0, 1 - abs(y - 26) / 30)
            d.line([(0,y),(63,y)], fill=(int(29+39*glow),int(28+18*glow),int(59+50*glow)))
        d.line([(2,0),(13,61),(50,61),(61,0)], fill=(167,148,209))
        for n in range(1,5):
            d.line([(12+n*8,0),(13+n*7,61)], fill=(78,75,115))
        for y in (13,27,40,53):
            d.line([(6,y),(57,y)], fill=(97,83,133))
        for x,y in ((20,39),(43,46),(34,33),(27,55),(45,18)):
            d.rectangle((x-5,y,x+4,y+2), fill=(169,224,244))
            d.line([(x-4,y),(x+3,y)], fill=(240,249,246))
        centered(d,(32,11),'280',10,(239,219,255),True)
        centered(d,(32,25),'A',12,(238,201,110),True)
        d.arc((21,15,43,36),10,170,fill=(215,176,92),width=1)
        d.arc((21,15,43,36),190,350,fill=(215,176,92),width=1)
        for x in (22,42):
            d.rectangle((x-2,57,x+2,63), fill=(100,233,231))
            d.rectangle((x-1,59,x+1,63), fill=(225,255,244))
    elif name == 'vent':
        for y in range(5,60,4):
            d.line([(6,y),(57,y)], fill=(7,9,13), width=2)
            d.line([(6,y+2),(57,y+2)], fill=(47,48,55))
    elif name == 'red_key':
        d.rectangle((2,2,61,61),outline=(229,126,139),width=2)
        d.line([(3,3),(60,3)],fill=(245,162,168),width=2)
        d.line([(3,60),(60,60)],fill=(149,42,65),width=2)
    elif name == 'label':
        d.rectangle((4,4,59,59),outline=(173,78,52),width=4)
        d.rectangle((10,10,53,53),outline=(218,174,106),width=2)
        centered(d,(32,33),'1',44,(53,40,35))
    return im

for i, name in enumerate(KEYS):
    ATLAS.paste(tile_image(name), ((i % 4)*TILE, (i//4)*TILE))
ATLAS.save(TEXTURES / 'nostalgia_materials.png')

# Native printed surfaces share a restrained pixel palette.
build_surface_art(TEXTURES, PALETTE, font)

def uv(name):
    i = KEYS.index(name)
    return [(i%4)*4, (i//4)*4, (i%4)*4+4, (i//4)*4+4]

elements = []

def cube(name, start, end, material='black', *, north=None, east=None, west=None,
         south=None, up=None, down=None,
         rotation=None, glow=False, group='Cabinet'):
    faces = {direction: {'uv': uv(material), 'texture': '#materials'}
             for direction in ('north','east','south','west','up','down')}
    for direction, override in (('north',north),('east',east),('west',west),
                                ('south',south),('up',up),('down',down)):
        if override:
            texture, tex_uv = override
            coordinates = [v*ART_UV_SCALE for v in tex_uv] if texture == 'artwork' else tex_uv
            if texture == 'marquee':
                coordinates = [v*MARQUEE_UV_SCALE[i%2] for i,v in enumerate(tex_uv)]
            faces[direction] = {'uv': coordinates, 'texture': '#' + texture}
    element = {'name':name, 'from':list(start), 'to':list(end), 'faces':faces}
    if rotation:
        axis, angle, origin = rotation
        element['rotation'] = {'axis':axis, 'angle':angle, 'origin':list(origin), 'rescale':False}
    if glow:
        if glow is True: element['shade'] = False
        for direction,face in faces.items():
            if glow is True or direction in glow:
                face['neoforge_data'] = {'block_light':15, 'sky_light':15, 'ambient_occlusion':False}
    element['_group'] = group
    elements.append(element)

def cutout_sprite(name, cell, start, end, material, *, rotation=None, glow=False,
                  printed=True, relief=0, group='Marquee rosettes'):
    """Extrude the sprite's alpha silhouette as stepped, textured model cuboids.

    This reads the source alpha for geometry only. The original pixels and alpha
    are packed unchanged; each front face selects its own region using UVs.
    """
    col,row=cell
    sw,sh=marquee_source.size
    cx0,cx1=round(col*sw/3),round((col+1)*sw/3)
    cy0,cy1=round(row*sh/2),round((row+1)*sh/2)
    sprite_alpha=marquee_source.getchannel('A').crop((cx0,cy0,cx1,cy1))
    bbox=sprite_alpha.point(lambda alpha: 255 if alpha >= 128 else 0).getbbox()
    assert bbox, 'Missing marquee sprite '+name
    px0,py0,px1,py1=bbox
    cols=20
    rows=max(12,round(cols*(py1-py0)/(px1-px0)*(end[0]-start[0])/(end[1]-start[1])))
    mask=[]
    for iy in range(rows):
        active=[]
        for ix in range(cols):
            box=(round(px0+(px1-px0)*ix/cols),round(py0+(py1-py0)*iy/rows),
                 round(px0+(px1-px0)*(ix+1)/cols),round(py0+(py1-py0)*(iy+1)/rows))
            region=sprite_alpha.crop(box)
            histogram=region.histogram()
            opaque=sum(histogram[128:])
            radius=math.hypot((ix+.5)/cols*2-1,(iy+.5)/rows*2-1)
            depth_level=2 if radius<.30 else 1 if radius<.78 else 0
            active.append((depth_level if relief else 0) if opaque >= region.width*region.height*.35 else -1)
        mask.append(active)
    # Greedy rectangles retain stepped silhouettes/UVs, while avoiding six faces
    # for every pixel row inside a solid book page or flower petal.
    for iy in range(rows):
        ix=0
        while ix<cols:
            if mask[iy][ix]<0:
                ix+=1
                continue
            first=ix
            depth_level=mask[iy][ix]
            while ix<cols and mask[iy][ix]==depth_level: ix+=1
            bottom=iy+1
            while bottom<rows and all(mask[bottom][x]==depth_level for x in range(first,ix)):
                bottom+=1
            for y in range(iy,bottom):
                for x in range(first,ix): mask[y][x]=-1
            x0=start[0]+(end[0]-start[0])*first/cols
            x1=start[0]+(end[0]-start[0])*ix/cols
            y0=end[1]-(end[1]-start[1])*bottom/rows
            y1=end[1]-(end[1]-start[1])*iy/rows
            u0=(cx0+px0+(px1-px0)*first/cols)/sw*16
            u1=(cx0+px0+(px1-px0)*ix/cols)/sw*16
            v0=(cy0+py0+(py1-py0)*iy/rows)/sh*16
            v1=(cy0+py0+(py1-py0)*bottom/rows)/sh*16
            front=start[2]-relief*depth_level/2
            cube(name+' row %02d run %02d'%(iy,first),(x0,y0,front),(x1,y1,end[2]),
                 material,north=('marquee',[u0,v0,u1,v1]) if printed else None,
                 rotation=rotation,glow=glow,group=group)

build_cabinet(cube, uv)
build_console(cube, uv)

build_marquee(cube, cutout_sprite)

texture_paths = {'materials':'japanesearcades:block/nostalgia_materials',
                 'artwork':'japanesearcades:block/nostalgia_artwork',
                 'marquee':'japanesearcades:block/nostalgia_marquee',
                 'trim':'japanesearcades:block/nostalgia_trim_v2',
                 'rhythm':'japanesearcades:block/nostalgia_rhythm',
                 'controls':'japanesearcades:block/nostalgia_controls',
                 'side':'japanesearcades:block/nostalgia_side_v2',
                 'particle':'japanesearcades:block/nostalgia_materials'}

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
    write_json(MODEL / ('nostalgia_op3_'+part+'.json'),
               {'parent':'minecraft:block/block','ambientocclusion':True,'render_type':'minecraft:cutout',
                'textures':texture_paths,'elements':parts[part]})
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'japanesearcades:block/nostalgia_op3_'+part}
        if rotation: variant['y']=rotation
        variants['facing='+facing+',part='+part]=variant
write_json(ASSETS / 'blockstates/nostalgia_op3.json', {'variants':variants})

# An explicitly scaled complete model for inventory rendering (vanilla element bounds).
item_elements=[]
for source in elements:
    e=strip_element(source)
    for key in ('from','to'):
        e[key]=[round(e[key][0]*0.35+5.2,5),round(e[key][1]*0.35,5),round(e[key][2]*0.35+5.2,5)]
    if 'rotation' in e:
        o=e['rotation']['origin'];e['rotation']['origin']=[o[0]*.35+5.2,o[1]*.35,o[2]*.35+5.2]
    item_elements.append(e)
write_json(ASSETS / 'models/item/nostalgia_op3.json',
           {'ambientocclusion':False,'gui_light':'front','textures':texture_paths,'elements':item_elements,
            'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                       'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                       'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                       'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                       'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})

artwork=TEXTURES / 'nostalgia_artwork.png'
if not artwork.exists():
    raise SystemExit('Missing original artwork sheet: '+str(artwork))
im=Image.open(artwork)
assert im.width == im.height and im.width & (im.width-1) == 0, 'Artwork must be a square power-of-two sheet'

# Blockbench's free format preserves the complete cabinet and named groups.
texture_specs = [(key,TEXTURES/(value.split('/')[-1]+'.png')) for key,value in texture_paths.items() if key!='particle']
texture_indices = {'#'+key:i for i,(key,path) in enumerate(texture_specs)}
texture_sizes = [Image.open(path).size for key,path in texture_specs]
bb_elements=[]
groups={}
for source in elements:
    e=strip_element(source)
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'japanesearcades/nostalgia/'+e['name']+'/'+str(e['from'])))
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
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'nostalgia/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/japanesearcades/textures/block/'+path.name,
                       'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                       'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'nostalgia-op3.bbmodel',
           {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
            'name':'Nostalgia Op.3','model_identifier':'nostalgia_op3','visible_box':[2,4,1.5],
            'resolution':{'width':256,'height':256},'elements':bb_elements,'textures':bbtextures,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'nostalgia/group/'+name)),
                         'origin':[8,0,8],'children':children} for name,children in groups.items()]})
write_json(ART/'geometry.json', {'textures':texture_paths,'elements':elements})
print('Generated',len(elements),'cuboids; section counts:',{name:len(values) for name,values in parts.items()})
print('Editable model:',ART/'nostalgia-op3.bbmodel')
