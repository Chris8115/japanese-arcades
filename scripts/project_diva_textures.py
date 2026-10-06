"""Native manufactured prints for Project DIVA Arcade Future Tone.

The generated character and header artwork is separate and never modified here.
All atlas coordinates refer to pixels. Inset regions by 8px when assigning UVs.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from chunithm_textures import PALETTE as BASE_PALETTE
from chunithm_textures import _label


PALETTE = {('red' if k == 'magenta' else 'yellow' if k == 'purple' else k): v
           for k, v in BASE_PALETTE.items()}
PALETTE.update(red=(236, 78, 98), pink=(224, 123, 225), cyan=(35, 184, 185),
               yellow=(237, 198, 64), blue=(65, 123, 234), green=(150, 218, 98))
KEYS = list(PALETTE)

# Pixels in the 1024-square details texture. All are opaque.
REGIONS = {
    'rail': (0, 0, 256, 512), 'speaker': (256, 0, 512, 512),
    'deck': (512, 0, 1024, 256), 'instructions': (512, 256, 1024, 416),
    'warning_strip': (512, 416, 1024, 512),
    'triangle': (0, 512, 256, 768), 'square': (256, 512, 512, 768),
    'cross': (512, 512, 768, 768), 'circle': (768, 512, 1024, 768),
    'slider': (0, 768, 512, 864), 'maker': (0, 864, 256, 1024),
    'aime': (256, 864, 512, 1024), 'coin': (512, 768, 768, 1024),
    'service': (768, 768, 1024, 1024),
}


def _font(size, bold=True, italic=False, japanese=False):
    filename = ('meiryob.ttc' if japanese else
                'arialbi.ttf' if italic else 'arialbd.ttf' if bold else 'arial.ttf')
    try:
        return ImageFont.truetype(str(Path('C:/Windows/Fonts') / filename), size)
    except OSError:
        return ImageFont.load_default(size=size)


def _hex(draw, xy, r, fill=None, outline=None, width=2):
    x, y = xy
    pts = [(round(x + r * math.cos(math.radians(a))),
            round(y + r * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
    draw.polygon(pts, fill=fill)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=width, joint='curve')


def _materials():
    image = Image.new('RGB', (256, 256))
    d = ImageDraw.Draw(image)
    rng = random.Random(904)
    for i, name in enumerate(KEYS):
        ox, oy = i % 4 * 64, i // 4 * 64
        for y in range(0, 64, 4):
            for x in range(0, 64, 4):
                v = rng.choice((-2, 0, 0, 2))
                c = tuple(max(0, min(255, n + v)) for n in PALETTE[name])
                d.rectangle((ox+x, oy+y, ox+x+3, oy+y+3), fill=c)
        if name == 'vent':
            for y in range(5, 60, 8):
                for x in range(4, 60, 12):
                    d.rectangle((ox+x, oy+y, ox+x+8, oy+y+2), fill=(4, 7, 12))
        elif name == 'black_mesh':
            for y in range(3, 61, 5):
                for x in range(3+(y//5%2)*2, 61, 5):
                    d.rectangle((ox+x, oy+y, ox+x+1, oy+y+1), fill=(4, 7, 12))
    return image


def _rail():
    image = Image.new('RGB', (256, 512), (232, 236, 230))
    d = ImageDraw.Draw(image)
    # Long printed side strips; the top half stays mostly white with a teal hex.
    _hex(d, (127, 76), 48, fill=(45, 185, 172))
    _hex(d, (128, 76), 57, outline=(184, 203, 197), width=2)
    d.polygon(((76, 47), (86, 47), (78, 59), (69, 59)), fill=(232, 236, 230))
    _label(image, (128, 151), 'Project DIVA', 12, (128, 165, 161))
    for x in (57, 104, 152, 199):
        _hex(d, (x, 179), 13, outline=(143, 159, 151), width=2)
    d.line((35, 204, 220, 204), fill=(159, 196, 186), width=2)
    colors = [(39,70,117),(209,223,222),(104,83,133),(231,235,221),
              (97,169,177),(49,113,157),(139,199,190),(247,232,169),
              (223,95,131),(227,155,91),(226,64,89),(248,194,71),
              (208,225,213),(65,130,188),(59,102,169),(230,224,227)]
    y = 243
    for i in range(32):
        h = (5, 9, 4, 7, 11)[i % 5]
        c = colors[i % len(colors)]
        d.polygon(((0,y),(256,y+12),(256,y+h+12),(0,y+h)), fill=c)
        # Broken rectangular pixels in the printed rainbow, not random texture noise.
        if i % 3 == 0:
            d.rectangle((28+i%6*31,y+2,43+i%6*31,y+h+3), fill=(229,234,226))
        y += h+1
    for x,y,r in ((97,323,38),(158,402,38),(108,468,32)):
        _hex(d, (x,y), r, outline=(213,228,208), width=3)
    return image


def _speaker():
    image = Image.new('RGB', (256, 512), (222, 229, 224))
    d = ImageDraw.Draw(image)
    d.polygon(((0,0),(47,0),(47,360),(18,392),(0,392)), fill=(37,177,163))
    d.polygon(((206,0),(255,0),(255,512),(231,491)), fill=(192,205,202))
    for y in (282,293,311):
        d.arc((-10,y-100,336,y+86), 24, 168, fill=(34,178,174), width=4)
    # Two connected rounded speaker apertures form the characteristic figure eight.
    for box in ((74,45,184,168),(74,155,184,278)):
        d.rounded_rectangle(box, radius=52, fill=(10,18,22), outline=(102,130,130), width=2)
    d.rectangle((95,127,163,191), fill=(10,18,22))
    for y in range(50, 276, 5):
        for x in range(79+(y//5%2)*2, 181, 5):
            if image.getpixel((x,y)) == (10,18,22):
                d.point((x,y), fill=(66,83,80))
    _label(image, (129,390), 'Project DIVA', 17, (91,156,151))
    _label(image, (129,415), 'A R C A D E', 15, (102,164,157))
    _hex(d, (130,455), 16, fill=(166,186,178))
    for x in (67,101,170,202):
        _hex(d, (x,479), 7, outline=(151,172,164))
    for x in (23,230):
        for y in (29,348,489):
            d.ellipse((x-3,y-3,x+3,y+3), fill=(88,105,104))
            d.line((x-2,y,x+2,y), fill=(210,219,214))
    return image


def _deck():
    image = Image.new('RGB', (512, 256), (219,233,229))
    d = ImageDraw.Draw(image)
    d.polygon(((40,0),(207,0),(80,256),(0,256),(0,146)), fill=(199,220,216))
    d.polygon(((290,0),(444,0),(308,256),(168,256)), fill=(163,205,199))
    for xy,r in (((128,145),67),((270,70),58),((399,167),66)):
        _hex(d, xy, r, outline=(215,239,233), width=3)
    for x in (60,177,294,411):
        d.ellipse((x-43,68,x+43,210), outline=(241,245,238), width=2)
    _label(image, (251,238), 'HEADPHONE', 13, (62,94,93))
    _label(image, (468,235), 'SEGA', 10, (89,114,111), True)
    return image


def _button(symbol, color):
    image = Image.new('RGB', (256,256), color)
    d = ImageDraw.Draw(image)
    # The physical disc is modeled; this atlas gives its translucent colored cap
    # and the correct large, unmistakable controller symbol.
    d.ellipse((17,17,238,238), outline=(247,250,239), width=4)
    d.ellipse((27,27,228,228), outline=tuple(min(255,c+26) for c in color), width=2)
    shadow = tuple(max(0,c-70) for c in color)
    if symbol == 'triangle':
        p = [(128,58),(60,181),(196,181),(128,58)]
        d.line(p, fill=shadow, width=21, joint='curve')
        d.line(p, fill=(242,255,239), width=11, joint='curve')
    elif symbol == 'square':
        d.rectangle((64,64,192,192), outline=shadow, width=19)
        d.rectangle((72,72,184,184), outline=(255,239,254), width=10)
    elif symbol == 'cross':
        for p in ((70,69,185,186),(185,69,70,186)):
            d.line(p, fill=shadow, width=23)
            d.line(p, fill=(232,254,255), width=12)
    else:
        d.ellipse((64,64,192,192), outline=shadow, width=20)
        d.ellipse((71,71,185,185), outline=(255,244,239), width=10)
    return image


def _instruction_sheet():
    image = Image.new('RGB',(512,160),(189,205,197))
    d = ImageDraw.Draw(image)
    for bounds in ((8,8,207,150),(218,8,301,150),(312,8,503,150)):
        d.rectangle(bounds, fill=(225,230,211), outline=(135,153,149), width=2)
    _label(image,(104,22),'HOW TO PLAY',12,(29,99,123),True)
    _label(image,(407,22),'TOUCH SLIDER',12,(29,99,123),True)
    for i,c in enumerate((PALETTE['green'], PALETTE['pink'],PALETTE['blue'],PALETTE['red'])):
        x=43+i*41
        d.ellipse((x-11,34,x+11,56),fill=c,outline=(50,71,73),width=2)
    for x,y,w in ((20,65,174),(321,43,168),(321,112,167),(20,131,172)):
        d.rectangle((x,y,x+w,y+5),fill=(42,69,83))
        for n in range(3):
            d.line((x,y+10+n*5,x+w-10-(n%2)*22,y+10+n*5),fill=(98,115,113),width=1)
    for x,y,w,h in ((23,85,73,35),(112,85,79,35),(328,72,62,31),(414,72,67,31)):
        d.rectangle((x,y,x+w,y+h),fill=(33,57,78),outline=(97,120,119),width=2)
        # Native instructional diagram of note lanes, not substitute artwork.
        for n in range(5):
            xx=x+8+n*(w-14)//5
            d.line((xx,y+5,xx+10,y+h-5),fill=(53,193,189),width=2)
    d.rectangle((222,12,297,148),fill=(34,35,39))
    d.rounded_rectangle((230,73,289,125),radius=9,fill=(239,229,218))
    d.rounded_rectangle((234,80,285,116),radius=8,fill=(199,61,104))
    _label(image,(260,97),'aime',19,(251,239,227),True)
    _label(image,(260,139),'TOUCH',8,(195,206,194),True)
    d.polygon(((234,26),(246,20),(254,38),(243,42)),fill=(211,62,98))
    d.polygon(((269,26),(282,20),(290,38),(278,42)),fill=(210,219,210))
    return image


def _details():
    image = Image.new('RGB',(1024,1024),PALETTE['black'])
    image.paste(_rail(),(0,0))
    image.paste(_speaker(),(256,0))
    image.paste(_deck(),(512,0))
    image.paste(_instruction_sheet(),(512,256))
    for i,(name,color) in enumerate((('triangle','green'),('square','pink'),('cross','blue'),('circle','red'))):
        image.paste(_button(name,PALETTE[color]),(i*256,512))
    d=ImageDraw.Draw(image)
    # Below-monitor caution/coin instruction strip.
    d.rectangle((520,424,1015,503),fill=(24,29,36))
    d.rectangle((529,434,682,490),fill=(225,227,205))
    d.rectangle((529,434,682,447),fill=(236,209,91))
    _label(image,(607,441),'CAUTION',10,(55,60,53),True)
    for y in range(455,485,6):
        d.line((537,y,670-(y%3)*14,y),fill=(92,104,89),width=1)
    d.rectangle((704,435,858,488),fill=(63,153,157))
    _label(image,(781,459),'TOUCH & SLIDE',12,(232,242,222),True)
    d.rectangle((905,434,1002,489),fill=(235,213,89))
    _label(image,(954,451),'1 PLAY',12,(33,48,46),True)
    _label(image,(954,475),'100 YEN',13,(33,48,46),True)
    # Long white/pale pink touch-slider face with tiny ticks and end arrows.
    d.rectangle((0,768,511,863),fill=(219,213,231))
    d.rectangle((8,776,503,855),outline=(249,248,239),width=3)
    d.line((25,785,486,785),fill=(255,255,246),width=4)
    for x in range(46,477,12):
        d.line((x,797,x,803 if x%24 else 810),fill=(244,240,244),width=1)
    for pts in (((39,810),(22,819),(39,829)),((473,810),(490,819),(473,829))):
        d.line(pts,fill=(252,251,243),width=5)
    _label(image,(256,835),'TOUCH SLIDER',15,(249,244,245),True)
    d.rectangle((0,864,255,1023),fill=(30,42,48))
    _label(image,(128,924),'SEGA',46,(222,233,224),True)
    _label(image,(128,984),'Project DIVA ARCADE',13,(155,184,178))
    d.rectangle((256,864,511,1023),fill=(226,225,210))
    d.rounded_rectangle((278,885,489,996),radius=20,fill=(194,58,103))
    _label(image,(384,937),'aime',53,(249,239,218),True)
    _label(image,(384,977),'TOUCH YOUR CARD',12,(249,239,218),True)
    d.rectangle((512,768,767,1023),fill=(202,211,203))
    d.rectangle((530,786,749,1005),fill=(40,48,53),outline=(137,153,145),width=3)
    d.rectangle((610,810,668,905),fill=(196,201,188))
    d.rectangle((630,819,644,896),fill=(11,19,23))
    _label(image,(640,944),'INSERT COIN',19,(222,230,210),True)
    _label(image,(640,976),'100 YEN',18,(222,230,210),True)
    d.rectangle((768,768,1023,1023),fill=(214,222,211))
    _label(image,(896,799),'SEGA',26,(42,101,124),True)
    _label(image,(896,832),'SERVICE PANEL',18,(70,87,84),True)
    _label(image,(896,865),'Project DIVA',17,(67,101,105))
    _label(image,(896,893),'Arcade Future Tone',14,(67,101,105))
    for y in range(923,991,8):
        d.line((789,y,998-(y%3)*13,y),fill=(115,133,120),width=1)
    return image


def _outlined_text(image,xy,text,size,fill,stroke,width=3,italic=False,japanese=False):
    d=ImageDraw.Draw(image)
    d.text(xy,text,font=_font(size,italic=italic,japanese=japanese),anchor='mm',
           fill=fill,stroke_fill=stroke,stroke_width=width)


def _branding():
    """Native layered lettering and printed stripes; logical crop is 2.172:1."""
    image=Image.new('RGB',(1024,512),(221,235,226))
    d=ImageDraw.Draw(image)
    for i,c in enumerate(((238,239,213),(199,222,217),(178,212,212),(219,231,211))):
        x=i*115-175
        d.polygon(((x,24),(x+58,24),(x+278,488),(x+220,488)),fill=c)
    for x,y,r in ((934,80,89),(113,369,94),(914,408,109)):
        _hex(d,(x,y),r,outline=(196,220,210),width=3)
    # Small Japanese Hatsune Miku lockup above the large Project DIVA title.
    _outlined_text(image,(146,74),'初音ミク',37,(87,192,215),(34,108,141),2,japanese=True)
    _outlined_text(image,(922,65),'SEGA',25,(34,126,168),(226,241,231),1)
    _outlined_text(image,(502,164),'Project DIVA',101,(243,252,241),(33,95,105),9)
    _outlined_text(image,(502,164),'Project DIVA',101,(231,249,239),(65,171,184),4)
    d.line((88,228,910,228),fill=(228,224,108),width=4)
    d.line((89,238,793,238),fill=(93,178,186),width=3)
    _outlined_text(image,(686,243),'PROJECT DIVA ARCADE',17,(233,248,237),(29,109,157),3)
    # The real italic Arcade wordmark carries a yellow-green face and dark outline.
    _outlined_text(image,(507,331),'Arcade',118,(195,228,107),(39,76,96),11,italic=True)
    _outlined_text(image,(507,331),'Arcade',118,(202,236,128),(40,157,180),5,italic=True)
    # Musical note/arrow emblem beside Arcade, built from manufacturer-style shapes.
    d.polygon(((885,283),(930,307),(893,361),(872,348),(899,311),(875,301)),
              fill=(223,224,107),outline=(31,106,137))
    d.line(((885,283),(930,307),(893,361),(872,348)),fill=(34,100,128),width=5)
    _outlined_text(image,(544,434),'Future Tone',58,(219,83,139),(241,244,228),7,italic=True)
    _outlined_text(image,(544,434),'Future Tone',58,(221,88,143),(60,142,155),2,italic=True)
    return image


def build_textures(textures):
    """Write materials256², details1024², branding1024x512; return palette."""
    textures=Path(textures)
    textures.mkdir(parents=True,exist_ok=True)
    _materials().save(textures/'project_diva_materials.png')
    _details().save(textures/'project_diva_details.png')
    _branding().save(textures/'project_diva_branding.png')
    return dict(PALETTE),list(KEYS)
