"""Manufactured maimai DX prints, faithful to the coral/yellow official model.

Generated LCD artwork is kept separate and never modified here. The native
floor graphic accounts for the model's 38.4 x 13 floor mat aspect ratio.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from chunithm_textures import PALETTE as BASE_PALETTE, _label


PALETTE={('coral' if k=='magenta' else 'yellow' if k=='purple' else k):v
         for k,v in BASE_PALETTE.items()}
PALETTE.update(coral=(233,62,61),pink=(227,101,173),cyan=(63,183,214),
               yellow=(242,239,92),blue=(57,127,205),green=(95,196,139),
               white=(236,236,226),ivory=(218,223,216))
KEYS=list(PALETTE)
REGIONS={
    'floor_mat':(0,0,1024,512),'upper_bezel':(0,512,512,768),
    'side_badge':(512,512,768,768),'embossed_dx':(0,768,512,1024),
    'speaker':(512,768,768,1024),'camera':(768,512,1024,640),
    'aime_instructions':(768,640,1024,768),'reader':(768,768,1024,896),
    'coin':(768,896,1024,1024),
}


def _font(size,japanese=False,rounded=False):
    name='meiryob.ttc' if japanese else 'arlrdbd.ttf' if rounded else 'arialbd.ttf'
    try:
        return ImageFont.truetype(str(Path('C:/Windows/Fonts')/name),size)
    except OSError:
        return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size)


def _materials():
    image=Image.new('RGB',(256,256))
    d=ImageDraw.Draw(image)
    rng=random.Random(802)
    for i,name in enumerate(KEYS):
        ox,oy=i%4*64,i//4*64
        for y in range(0,64,4):
            for x in range(0,64,4):
                v=rng.choice((-2,0,0,2))
                c=tuple(max(0,min(255,n+v)) for n in PALETTE[name])
                d.rectangle((ox+x,oy+y,ox+x+3,oy+y+3),fill=c)
        if name=='vent':
            for y in range(5,60,7):
                for x in range(4,60,10):
                    d.rectangle((ox+x,oy+y,ox+x+6,oy+y+2),fill=(4,7,12))
        elif name=='black_mesh':
            for y in range(3,61,5):
                for x in range(3+(y//5%2)*2,61,5):
                    d.rectangle((ox+x,oy+y,ox+x+1,oy+y+1),fill=(3,6,11))
    return image


def _star(d,x,y,r,fill):
    points=[]
    for i in range(10):
        a=math.radians(-90+i*36)
        radius=r if i%2==0 else r*.44
        points.append((round(x+math.cos(a)*radius),round(y+math.sin(a)*radius)))
    d.polygon(points,fill=fill)


def _cloud(d,x,y,w,h,color=(246,248,237)):
    d.rectangle((x,y+h*.45,x+w,y+h),fill=color)
    for px,py,r in ((x+w*.18,y+h*.50,h*.31),(x+w*.42,y+h*.30,h*.45),
                    (x+w*.69,y+h*.43,h*.39),(x+w*.88,y+h*.57,h*.28)):
        d.ellipse((px-r,py-r,px+r,py+r),fill=color)


def _brand():
    image=Image.new('RGBA',(1024,512),(0,0,0,0))
    d=ImageDraw.Draw(image)
    colors=[(242,197,56),(32,184,197),(236,80,91),(69,152,216),(226,92,162),(120,199,69)]
    text='maimai'
    font=_font(188,rounded=True)
    widths=[d.textlength(c,font=font) for c in text]
    x=(1024-sum(widths)-25)/2
    for c,w,color in zip(text,widths,colors):
        # Thin dark outer print, generous white border, colored rounded glyph.
        d.text((x,19),c,font=font,fill=color,stroke_width=14,stroke_fill=(43,57,62))
        d.text((x,19),c,font=font,fill=color,stroke_width=9,stroke_fill=(248,249,237))
        x+=w+5
    font=_font(114,japanese=True)
    text='でらっくす'
    widths=[d.textlength(c,font=font) for c in text]
    x=102
    for c,w,color in zip(text,widths,[colors[2],colors[0],colors[1],colors[4],colors[5]]):
        d.text((x,243),c,font=font,fill=color,stroke_width=13,stroke_fill=(43,57,62))
        d.text((x,243),c,font=font,fill=color,stroke_width=8,stroke_fill=(248,249,237))
        x+=w+2
    d.text((802,362),'DX',font=_font(73,rounded=True),anchor='mm',fill=(242,204,54),
           stroke_width=10,stroke_fill=(43,57,62))
    d.text((802,362),'DX',font=_font(73,rounded=True),anchor='mm',fill=(242,204,54),
           stroke_width=5,stroke_fill=(248,249,237))
    _star(d,901,339,25,(246,208,65))
    image.putalpha(image.getchannel('A').point(lambda a:255 if a>=128 else 0))
    return image


def _mat(brand):
    image=Image.new('RGB',(1024,512),(216,61,61))
    d=ImageDraw.Draw(image)
    # The official mat has a broad rainbow across its red field.
    colors=[(234,82,70),(239,160,54),(244,218,54),(118,184,78),
            (61,166,184),(76,116,176)]
    for i,color in enumerate(colors):
        inset=i*57
        d.ellipse((31+inset,-247+inset,993-inset,710-inset),fill=color)
    _cloud(d,52,239,187,97)
    _cloud(d,802,239,172,97)
    for x,y,r in ((125,80,15),(891,66,16),(170,425,14),(859,416,12)):
        _star(d,x,y,r,(246,239,175))
    # Counteract the floor's ~1.48 horizontal physical stretch, while keeping
    # the reusable sign/logo texture at its natural proportions.
    label=brand.resize((571,420),Image.Resampling.NEAREST)
    image.paste(label,(227,35),label)
    d.rectangle((835,460,985,493),fill=(182,40,46),outline=(240,159,150),width=1)
    _label(image,(910,476),'maimai DX',17,(246,231,211),True)
    d.line((7,504,1016,504),fill=(91,37,44),width=3)
    return image


def _upper_bezel():
    image=Image.new('RGB',(512,256),(223,82,74))
    d=ImageDraw.Draw(image)
    # Rainbow trim around the rectangular upper display; center is hidden byLCD.
    colors=[(231,149,65),(239,221,77),(108,191,116),(66,176,195),(83,125,191)]
    for i,c in enumerate(colors):
        d.rounded_rectangle((25+i*5,21+i*5,487-i*5,235-i*5),radius=20,outline=c,width=5)
    d.rectangle((53,52,459,205),fill=(114,192,215))
    for y in range(43,214,17):
        d.line((8,y,17,y),fill=(238,201,167),width=3)
        d.line((495,y,504,y),fill=(238,201,167),width=3)
    _cloud(d,16,195,51,37)
    _cloud(d,443,195,51,37)
    return image


def _hand_badge():
    image=Image.new('RGB',(256,256),(230,102,79))
    d=ImageDraw.Draw(image)
    d.ellipse((10,10,245,245),fill=(243,230,81),outline=(35,40,42),width=7)
    d.ellipse((26,26,229,229),fill=(244,245,232),outline=(237,203,65),width=3)
    # Simple raised-hand symbol used on the real cabinet's outer round badge.
    c=(49,66,65)
    d.rounded_rectangle((78,104,171,192),radius=28,fill=c)
    for x,y,w in ((77,68,22),(101,49,23),(127,57,22),(150,78,22)):
        d.rounded_rectangle((x,y,x+w,143),radius=10,fill=c)
    d.polygon(((81,129),(53,109),(44,116),(60,157),(92,181)),fill=c)
    d.ellipse((57,205,63,211),fill=c)
    _label(image,(131,214),'TOUCH!',16,c,True)
    return image


def _dx():
    # This is raised white lettering on the shell, not a rectangular sticker.
    # Fill D's normal font counter, then cut the reference's five-point star.
    mask=Image.new('1',(512,256))
    d=ImageDraw.Draw(mask)
    d.text((256,123),'DX',font=_font(176),anchor='mm',fill=1)
    ImageDraw.floodfill(mask,(193,123),1)
    _star(d,193,122,29,0)
    image=Image.new('RGBA',(512,256),(0,0,0,0))
    # A subtle pale bevel keeps the embossed mark legible without coloring it.
    shadow=Image.new('RGBA',image.size,(0,0,0,0))
    shadow.paste((207,214,207,255),(0,0),mask)
    image.alpha_composite(shadow,(3,3))
    highlight=Image.new('RGBA',image.size,(0,0,0,0))
    highlight.paste((245,245,235,255),(0,0),mask)
    image.alpha_composite(highlight,(-1,-1))
    image.paste((223,228,221,255),(0,0),mask)
    return image


def _speaker():
    image=Image.new('RGB',(256,256),(15,17,22))
    d=ImageDraw.Draw(image)
    d.ellipse((18,18,237,237),fill=(24,28,32),outline=(4,6,12),width=7)
    d.ellipse((39,39,216,216),outline=(41,47,48),width=2)
    for y in range(30,227,5):
        for x in range(29+(y//5%2)*2,228,5):
            if (x-128)**2+(y-128)**2<95**2:
                d.rectangle((x,y,x+1,y+1),fill=(6,9,13))
    d.ellipse((95,95,160,160),fill=(16,21,27),outline=(36,42,46),width=2)
    return image


def _details(brand):
    image=Image.new('RGBA',(1024,1024),(*PALETTE['white'],255))
    image.paste(_mat(brand),(0,0))
    image.paste(_upper_bezel(),(0,512))
    image.paste(_hand_badge(),(512,512))
    image.paste(_dx(),(0,768))
    image.paste(_speaker(),(512,768))
    d=ImageDraw.Draw(image)
    # Camera section: powder-coated oval housing, lens, small pilot lamp.
    d.rounded_rectangle((786,524,1006,628),radius=28,fill=(225,230,220),outline=(164,177,173),width=2)
    d.ellipse((853,535,931,613),fill=(9,20,28),outline=(90,108,113),width=5)
    d.ellipse((869,550,915,598),fill=(25,53,65),outline=(77,109,122),width=2)
    d.ellipse((879,556,894,568),fill=(126,185,189))
    d.ellipse((960,556,972,568),fill=(126,172,82))
    # Aime + instruction card follows the narrow shared center column.
    d.rectangle((781,649,1010,759),fill=(230,232,223),outline=(166,179,173),width=1)
    d.rectangle((789,658,897,750),fill=(41,48,53))
    d.rounded_rectangle((800,673,886,728),radius=12,fill=(205,60,107))
    _label(image,(843,699),'aime',22,(248,234,224),True)
    _label(image,(950,670),'HOW TO PLAY',10,(57,100,116),True)
    for y in (691,710,730):
        d.rectangle((912,y,929,y+11),fill=(145,192,135))
        d.line((935,y+2,996,y+2),fill=(99,121,118),width=2)
        d.line((935,y+8,983,y+8),fill=(148,164,153),width=1)
    # Reader face: black vertical service section with a green-blue statusLCD.
    d.rectangle((781,779,1010,884),fill=(25,30,36),outline=(117,133,130),width=2)
    d.rectangle((798,791,932,869),fill=(108,182,163),outline=(184,220,199),width=2)
    _label(image,(865,814),'TOUCH',16,(22,73,77),True)
    _label(image,(865,842),'YOUR CARD',13,(31,93,93),True)
    d.rectangle((951,795,992,827),fill=(186,203,171))
    d.rectangle((951,843,992,866),fill=(211,199,84))
    # Dark vertical coin slot and small embossed maker labels.
    d.rectangle((779,908,1013,1012),fill=(222,227,217),outline=(170,183,173),width=1)
    d.rectangle((794,919,851,997),fill=(44,49,55),outline=(114,128,125),width=2)
    d.rectangle((815,927,827,987),fill=(4,9,14))
    _label(image,(932,935),'SEGA',22,(117,148,155),True)
    _label(image,(932,966),'100 YEN',15,(92,113,109),True)
    _label(image,(932,991),'maimai DX',10,(130,153,144))
    return image


def build_textures(textures):
    """Write materials256², details1024² and transparent branding1024x512."""
    textures=Path(textures)
    textures.mkdir(parents=True,exist_ok=True)
    brand=_brand()
    _materials().save(textures/'maimai_materials.png')
    _details(brand).save(textures/'maimai_details.png')
    brand.save(textures/'maimai_branding.png')
    return dict(PALETTE),list(KEYS)
