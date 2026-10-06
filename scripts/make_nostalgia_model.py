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

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/funpackcustom'
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
marquee_source = Image.open(ART / 'marquee-artwork-source.png').convert('RGBA')
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
    for y in range(TILE):
        for x in range(TILE):
            noise = rng.choice([-2, -1, 0, 0, 1, 2])
            p[x, y] = tuple(max(0, min(255, c + noise)) for c in color)
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
        d.polygon([(32, 5), (4, 58), (60, 58)], fill=(66, 67, 75), outline=(166, 164, 169), width=1)
        d.line([(32,10),(10,55),(54,55),(32,10)], fill=(110,110,119), width=1)
        for radius in (9, 12, 16):
            d.ellipse((32-radius,38-radius,32+radius,38+radius), outline=(150,146,155), width=1)
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

# A dedicated tall side graphic keeps lettering proportionate on the narrow panel.
side_texture=Image.new('RGB',(128,512),PALETTE['ivory'])
side_draw=ImageDraw.Draw(side_texture)
side_draw.rectangle((7,7,120,504),outline=(187,153,87),width=2)
for y in range(22,495,38):
    for x in (18,110):
        side_draw.line([(x-6,y),(x,y-7),(x+6,y),(x,y+7),(x-6,y)],fill=(188,155,87),width=2)
centered(side_draw,(64,245),'NOSTALGIA',15,(77,58,44),True)
centered(side_draw,(64,272),'Op.3',19,(103,68,48),True)
for y in (190,322):
    side_draw.line([(26,y),(102,y)],fill=(186,153,87),width=2)
    side_draw.polygon([(64,y-7),(71,y),(64,y+7),(57,y)],outline=(186,153,87))
side_texture.save(TEXTURES/'nostalgia_side.png')

trim_texture=Image.new('RGB',(512,64),PALETTE['ivory'])
trim_draw=ImageDraw.Draw(trim_texture)
trim_draw.rectangle((2,2,509,61),outline=(184,151,85),width=2)
trim_draw.line([(8,8),(503,8)],fill=(241,228,201),width=2)
for center in range(42,500,86):
    ink=(194,164,106)
    trim_draw.arc((center-26,16,center+26,48),10,170,fill=ink,width=2)
    trim_draw.arc((center-18,21,center+18,43),190,350,fill=ink,width=2)
    trim_draw.line([(center-25,32),(center-8,32),(center,22),(center+8,32),(center+25,32)],fill=ink,width=2)
    for x,y in ((center-20,32),(center+20,32),(center,46)):
        trim_draw.rectangle((x-2,y-2,x+2,y+2),fill=ink)
trim_texture.save(TEXTURES/'nostalgia_marquee_trim.png')

def uv(name):
    i = KEYS.index(name)
    return [(i%4)*4, (i//4)*4, (i%4)*4+4, (i//4)*4+4]

elements = []

def cube(name, start, end, material='black', *, north=None, east=None, west=None,
         rotation=None, glow=False, group='Cabinet'):
    faces = {direction: {'uv': uv(material), 'texture': '#materials'}
             for direction in ('north','east','south','west','up','down')}
    for direction, override in (('north',north),('east',east),('west',west)):
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
                face['neoforge_data'] = {'block_light':15, 'sky_light':15}
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
    cols=24
    rows=max(12,round(cols*(py1-py0)/(px1-px0)*(end[0]-start[0])/(end[1]-start[1])))
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
            active.append(depth_level if opaque >= region.width*region.height*.35 else -1)
        ix=0
        while ix<cols:
            if active[ix]<0:
                ix+=1
                continue
            first=ix
            depth_level=active[ix] if relief else 0
            while ix<cols and active[ix]>=0 and (not relief or active[ix]==depth_level): ix+=1
            x0=start[0]+(end[0]-start[0])*first/cols
            x1=start[0]+(end[0]-start[0])*ix/cols
            y0=end[1]-(end[1]-start[1])*(iy+1)/rows
            y1=end[1]-(end[1]-start[1])*iy/rows
            u0=(cx0+px0+(px1-px0)*first/cols)/sw*16
            u1=(cx0+px0+(px1-px0)*ix/cols)/sw*16
            v0=(cy0+py0+(py1-py0)*iy/rows)/sh*16
            v1=(cy0+py0+(py1-py0)*(iy+1)/rows)/sh*16
            front=start[2]-relief*depth_level/2
            cube(name+' row %02d run %02d'%(iy,first),(x0,y0,front),(x1,y1,end[2]),
                 material,north=('marquee',[u0,v0,u1,v1]) if printed else None,
                 rotation=rotation,glow=glow,group=group)

# Three stacked body segments keep the world model within vanilla JSON bounds.
for y0,y1,label in ((1.4,16,'Base'),(16,32,'Console'),(32,39.4,'Display')):
    cube(label+' back shell',(1.2,y0,8.8),(14.8,y1,15.1), group='Back cabinet')
cube('Left footwell wall',(1.2,1.4,4.3),(2.1,16,9.0),group='Recessed footwell')
cube('Right footwell wall',(13.9,1.4,4.3),(14.8,16,9.0),group='Recessed footwell')
cube('Footwell floor',(2.1,1.45,4.5),(13.9,2.15,9.1),'black_key',group='Recessed footwell')
cube('Inset service door',(3.0,9.8,8.60),(13.5,15.8,8.87),group='Recessed footwell')
cube('Footwell top return',(2.0,15.4,4.3),(14.0,16,9.0),group='Recessed footwell')
cube('Kick panel',(0.8,0.7,3.8),(15.2,2,15.1),'silver',group='Lower cabinet')
for x in (1.7,13.7):
    for z in (4.7,13.5):
        cube('Cabinet foot',(x,0,z),(x+0.8,0.9,z+0.8),'black_key',group='Lower cabinet')
# A stepped triangular plate leans back into the open footwell. The artwork's
# continuous UVs are clipped to each strip, so this is real inset geometry.
triangle_tilt=('x',22.5,(8,3.15,5.4))
for i in range(14):
    y0=3.15+i*6.5/14
    y1=3.15+(i+1)*6.5/14
    half=3.7*(1-i/14)
    u0,u1=32-half/3.7*28,32+half/3.7*28
    v0,v1=58-(i+1)/14*53,58-i/14*53
    triangle_uv=[12+u0/16,8+v0/16,12+u1/16,8+v1/16]
    cube('Recessed triangle strip %02d'%i,(8-half,y0,5.4),(8+half,y1,5.62),
         'silver',north=('materials',triangle_uv),rotation=triangle_tilt,group='Recessed footwell')
cube('Inset door split',(9.9,10,8.53),(10.0,15.2,8.72),'black_key',group='Recessed footwell')
cube('Inset door lock',(12.5,10.8,8.5),(12.8,11.5,8.68),'silver',group='Recessed footwell')
for side,x in (('left',1.25),('right',14.25)):
    cube(side+' lower ornamental border',(x,2.1,4.05),(x+0.5,15.9,4.22),'silver',group='Lower cabinet')
    for i in range(12):
        y=2.6+i*1.05
        cube(side+' diamond '+str(i),(x-0.06,y,3.97),(x+0.34,y+0.4,4.07),
             'ivory' if i%3 else 'lavender',rotation=('z',45,(x+0.14,y+0.2,4.02)),group='Lower cabinet')
for side,x in (('left',1.10),('right',14.78)):
    cube(side+' side vent',(x,4.5,10.2),(x+0.12,11.5,14.2),east=('materials',uv('vent')),
         west=('materials',uv('vent')),group='Back cabinet')
    cube(side+' ivory side panel',(x,17.0,10.1),(x+0.14,37.9,14.9),'ivory',
         east=('side',[0,0,16,16]),west=('side',[0,0,16,16]),group='Back cabinet')

# Keyboard and slanted touchscreen. The panel leans back 22.5 degrees.
cube('Console support',(0.7,16,3.3),(15.3,18.4,14.8),group='Keyboard')
# The real cabinet has a solid enclosure behind the inclined monitor. Horizontal
# courses fill its wedge back to the rear shell; their small front steps sit
# inside the thick monitor backing and are hidden by its continuous sloped face.
housing_bottom, housing_top = 18.4, 26.3
housing_courses = 24
for i in range(housing_courses):
    y0 = housing_bottom + (housing_top-housing_bottom)*i/housing_courses
    y1 = housing_bottom + (housing_top-housing_bottom)*(i+1)/housing_courses
    front = 2.8 + math.tan(math.radians(22.5))*(y0-19.1) + 0.72/math.cos(math.radians(22.5))
    cube('Solid touchscreen housing course %02d'%i,(1.2,y0,front),(14.8,y1,8.95),
         group='Touchscreen enclosure')
cube('Keyboard shelf',(0.3,17.8,0),(15.7,18.5,9.1),'ivory',group='Keyboard')
cube('Front keyboard trim',(0.3,17.65,-0.02),(15.7,18.08,0.22),'gold',group='Keyboard')
cube('Keyboard light strip',(0.75,18.36,0.17),(15.25,18.5,0.35),'teal',glow=True,group='Keyboard')
for x in (0.3,15.05):
    cube('Keyboard cheek',(x,18.25,0.1),(x+0.65,18.95,4.5),'ivory',group='Keyboard')
white_count = 24
key_width = 13.7/white_count
for i in range(white_count):
    x=1.15+i*key_width
    cube('White piano key %02d'%i,(x,18.51,0.65),(x+key_width-0.035,18.89,3.75),'white_key',group='Piano keys')
    if i%7 not in (2,6) and i<white_count-1:
        cube('Black piano key %02d'%i,(x+key_width-0.20,18.89,2.04),
             (x+key_width+0.15,19.20,3.75),'black_key',group='Piano keys')
tilt = ('x',22.5,(8,19.1,2.8))
cube('Angled screen backing',(0.8,19.1,2.8),(15.2,26.8,3.7),'ivory',rotation=tilt,group='Touchscreen')
cube('Angled dark bezel',(1.45,19.5,2.7),(14.55,26.35,2.83),'black_key',rotation=tilt,group='Touchscreen')
cube('Rhythm screen',(1.78,19.79,2.66),(14.22,26.04,2.71),
     north=('materials',uv('rhythm')),rotation=tilt,glow=True,group='Touchscreen')
for x in (0.9,14.65):
    cube('Gold touchscreen rail',(x,19.16,2.6),(x+0.42,26.75,2.79),'gold',rotation=tilt,group='Touchscreen')
    cube('Illuminated touchscreen rail',(x+0.12,19.5,2.56),(x+0.24,26.4,2.63),'white_key',
         rotation=tilt,glow=True,group='Touchscreen')

# The central fascia leans back into the upper monitor. Each speaker wing also
# toes inward: its outer edge projects forward. Thin horizontal courses preserve
# the vertical lean while their Y rotation supplies the inward-facing normal,
# using vanilla cuboids' single-axis rotation and the concept's stepped style.
speaker_tilt=('x',22.5,(8,26.0,6.45))
cube('Slanted central speaker fascia',(4.10,26.0,6.45),(11.90,29.8,9.2),'ivory',
     rotation=speaker_tilt,group='Speakers and sign')
lean_sin,lean_cos=math.sin(math.radians(22.5)),math.cos(math.radians(22.5))
def speaker_courses(name,x0,x1,y0,y1,offset,depth,hinge,angle,material,count):
    tile=uv(material)
    for i in range(count):
        low=y0+(y1-y0)*i/count
        high=y0+(y1-y0)*(i+1)/count
        z=6.45+((low+high)/2-26)*lean_sin+offset*lean_cos
        bottom=26+(low-26)*lean_cos-offset*lean_sin
        top=26+(high-26)*lean_cos-offset*lean_sin
        tex_uv=[tile[0],tile[1]+(y1-high)/(y1-y0)*(tile[3]-tile[1]),
                tile[2],tile[1]+(y1-low)/(y1-y0)*(tile[3]-tile[1])]
        cube(name+' course %02d'%i,(x0,bottom,z),(x1,top,z+depth),'ivory',
             north=('materials',tex_uv),rotation=('y',angle,(hinge,26,z)),group='Speakers and sign')
for side,x0,x1,hinge,angle in (('Left',.75,4.40,4.20,-22.5),('Right',11.60,15.25,11.80,22.5)):
    speaker_courses(side+' inward speaker housing',x0,x1,26.0,29.8,0,1.35,hinge,angle,'ivory',32)
    speaker_courses(side+' inward speaker grille',x0+.20,x1-.20,26.30,29.50,-.18,.18,hinge,angle,'speaker',24)
    for y in (26.14,29.55):
        speaker_courses(side+' speaker raised rim '+str(y),x0+.13,x1-.13,y,y+.13,-.23,.24,
                        hinge,angle,'white_key',1)
cube('Gold title surround',(4.34,26.49,6.22),(11.66,29.23,6.55),'gold',
     rotation=speaker_tilt,group='Speakers and sign')
cube('Nostalgia title plaque',(4.53,26.65,6.16),(11.47,29.07,6.27),'black_key',
     north=('artwork',[8,0,16,8]),rotation=speaker_tilt,glow=True,group='Speakers and sign')

# Upper screen, ivory trim, and gold edge decoration.
cube('Upper screen housing',(0.75,29.5,7.85),(15.25,39.45,9.50),'ivory',group='Upper monitor')
cube('Upper screen gold bevel',(1.19,29.78,7.72),(14.81,39.00,7.93),'gold',group='Upper monitor')
cube('Upper screen dark border',(1.43,30.05,7.65),(14.57,38.73,7.80),'black_key',group='Upper monitor')
cube('Nostalgia Op.3 screen',(1.68,30.29,7.59),(14.32,38.49,7.70),'black_key',
     north=('artwork',[0,0,8,8]),glow=True,group='Upper monitor')
for x in (1.56,14.38):
    cube('Upper screen light edge '+str(x),(x,30.22,7.54),(x+.055,38.56,7.60),
         'lavender',glow=True,group='Upper monitor lights')
cube('Upper screen lower light edge',(1.56,30.19,7.53),(14.435,30.25,7.60),
     'blue',glow=True,group='Upper monitor lights')
cube('Ivory marquee ledge',(0.55,39.20,7.30),(15.45,39.85,10.35),'ivory',group='Marquee')
cube('Marquee gold ribbon',(0.70,39.63,7.18),(15.30,39.83,7.37),'gold',group='Marquee')
cube('Ornate cascading marquee fascia',(.30,38.98,6.25),(15.8,40.25,7.53),'ivory',
     north=('trim',[0,0,16,16]),group='Marquee fascia')
cube('Marquee fascia upper gold edge',(.30,40.15,6.17),(15.8,40.31,6.32),'gold',group='Marquee fascia')
cube('Cabinet number badge',(.57,39.10,6.10),(1.56,40.15,6.29),'ivory',
     north=('materials',uv('label')),group='Marquee fascia')
for x in (0.94,14.83):
    for y in (29.75,39.02):
        cube('Monitor frame rivet',(x,y,7.72),(x+0.21,y+0.21,7.86),'silver',group='Upper monitor')

# Separate stepped book pages form an open book, with the taller cat page on
# the right. Their printed fronts follow the new reference-inspired artwork.
for x in (6.8,8.5):
    cube('Book mounting bracket '+str(x),(x,39.65,8.90),(x+0.50,41.05,9.55),
         'gold',group='Book marquee')
# Thick stepped gold covers, ivory page stacks, and the printed front leaf form
# three separate depth layers on each half of the open book.
for name,cell,x0,x1,top,angle,hinge in (
        ('Left music',(0,1),1.25,7.95,45.7,22.5,7.95),
        ('Right cat',(1,1),7.90,14.85,47.3,-22.5,7.90)):
    rotation=('y',angle,(hinge,40.55,8.8))
    cutout_sprite(name+' gold cover',cell,(x0-.12,40.40,9.08),(x1+.12,top+.15,9.88),
                  'gold',rotation=rotation,printed=False,group='Book covers')
    cutout_sprite(name+' ivory page stack',cell,(x0-.04,40.48,8.94),(x1+.04,top+.05,9.48),
                  'white_key',rotation=rotation,printed=False,group='Book page layers')
cutout_sprite('Left music page',(0,1),(1.25,40.55,8.8),(7.95,45.7,9.3),'gold',
              rotation=('y',22.5,(7.95,40.55,8.8)),group='Book marquee')
cutout_sprite('Right cat page',(1,1),(7.90,40.55,8.8),(14.85,47.3,9.3),'gold',
              rotation=('y',-22.5,(7.90,40.55,8.8)),group='Book marquee')
cube('Book center spine',(7.72,40.6,8.65),(8.12,45.1,9.1),'gold',group='Book marquee')
for y in (41.15,42.25,43.35,44.45):
    cube('Raised book spine band '+str(y),(7.62,y,8.52),(8.22,y+.20,9.24),
         'gold',group='Book marquee')
for i in range(11):
    x=0.90+i*1.28
    y=38.15+0.32*i
    rotation=('z',-22.5,(8,40.4,8))
    height=2.65+(0,.35,.65,.15,.45,.85,.20,.60,.30,.70,.40)[i]
    front=(6.70,6.55,6.74)[i%3]
    cube('Marquee white piano key '+str(i),(x,y,front),(x+1.12,y+height,8.80),
         'white_key',rotation=rotation,group='Piano marquee')
    cube('Marquee key colored heel '+str(i),(x,y,front-.10),(x+1.12,y+0.60,front+.10),
         ('blue','lavender','pink')[i%3],rotation=rotation,group='Piano marquee')
    if i%7 not in (2,6):
        cube('Marquee red key '+str(i),(x+0.76,y+1.02,front-.28),(x+1.20,y+height+.18,front+.15),
             'red_key',rotation=rotation,group='Piano marquee')
    if i in (1,4,8):
        cube('Marquee key light '+str(i),(x+.12,y+.64,front-.12),(x+.99,y+.78,front-.04),
             'teal',rotation=rotation,glow=('north',),group='Piano marquee')
for i,(x,y,material) in enumerate(((0.35,40.05,'blue'),(5.75,39.45,'lavender'),(11.65,38.70,'pink'))):
    rotation=('z',-22.5,(x+1.875,y+1.925,6.3))
    cutout_sprite('Rosette colored backing '+str(i),(i,0),(x-.13,y-.13,6.19),(x+3.88,y+3.98,7.32),
                  material,rotation=rotation,printed=False,group='Rosette back layers')
    cutout_sprite('Floral rosette '+str(i),(i,0),(x,y,5.95),(x+3.75,y+3.85,6.72),
                  'ivory',rotation=rotation,glow=('north',),relief=.46)
# Smaller flower cutouts spill down the monitor edge, as in the concept.
for name,cell,x,y,width,material in (
        ('Pink',(2,0),14.25,34.8,2.40,'pink'),
        ('Lavender',(1,0),14.40,32.2,2.10,'lavender'),
        ('Blue',(0,0),14.45,30.3,1.65,'blue')):
    cutout_sprite(name+' monitor flower backing',cell,(x-.08,y-.08,7.47),(x+width+.08,y+width+.13,7.90),
                  material,printed=False,group='Monitor flowers')
    cutout_sprite(name+' monitor flower',cell,(x,y,7.23),(x+width,y+width+.05,7.57),
                  'ivory',glow=('north',),relief=.24,group='Monitor flowers')

texture_paths = {'materials':'funpackcustom:block/nostalgia_materials',
                 'artwork':'funpackcustom:block/nostalgia_artwork',
                 'marquee':'funpackcustom:block/nostalgia_marquee',
                 'trim':'funpackcustom:block/nostalgia_marquee_trim',
                 'side':'funpackcustom:block/nostalgia_side',
                 'particle':'funpackcustom:block/nostalgia_materials'}

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
               {'parent':'minecraft:block/block','ambientocclusion':False,'render_type':'minecraft:cutout',
                'textures':texture_paths,'elements':parts[part]})
variants={}
for facing,rotation in (('north',0),('east',90),('south',180),('west',270)):
    for part in part_names:
        variant={'model':'funpackcustom:block/nostalgia_op3_'+part}
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
bb_elements=[]
groups={}
for source in elements:
    e=strip_element(source)
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'funpackcustom/nostalgia/'+e['name']+'/'+str(e['from'])))
    rot=e.get('rotation')
    rotation=[0,0,0]
    origin=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
    if rot:
        rotation['xyz'.index(rot['axis'])]=rot['angle'];origin=rot['origin']
    bbfaces={}
    for direction,face in e['faces'].items():
        index={'#materials':0,'#artwork':1,'#side':2,'#marquee':3,'#trim':4}[face['texture']]
        width,height=((256,256),(im.width,im.height),(128,512),marquee_size,(512,64))[index]
        bbfaces[direction]={'uv':[v*(width if i%2==0 else height)/16 for i,v in enumerate(face['uv'])], 'texture':index}
    bb_elements.append({'name':e['name'],'type':'cube','uuid':uid,'from':e['from'],'to':e['to'],
                        'origin':origin,'rotation':rotation,'faces':bbfaces,'box_uv':False,
                        'color':1,'rescale':False,'autouv':0,'visibility':True,'export':True,
                        'shade':e.get('shade',True)})
    groups.setdefault(source['_group'],[]).append(uid)
bbtextures=[]
for i,(path,identifier) in enumerate(((TEXTURES/'nostalgia_materials.png','materials'),(artwork,'artwork'),
                                     (TEXTURES/'nostalgia_side.png','side'),
                                     (TEXTURES/'nostalgia_marquee.png','marquee'),
                                     (TEXTURES/'nostalgia_marquee_trim.png','trim'))):
    texture=Image.open(path)
    bbtextures.append({'path':str(path),'name':path.name,'folder':'block','namespace':'funpackcustom',
                       'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'nostalgia/'+identifier)),
                       'width':texture.width,'height':texture.height,'uv_width':texture.width,'uv_height':texture.height,
                       'relative_path':'../../src/main/resources/assets/funpackcustom/textures/block/'+path.name,
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
