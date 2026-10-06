"""Native clockwork, hardware and logo prints for the Chrono Circle cabinet.

No generated art is opened or altered. Atlas regions are documented in pixels;
inset each side by 8px before mapping to the native 16-unit Minecraft UV scale.
"""
from __future__ import annotations

import colorsys
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from chunithm_textures import PALETTE as BASE_PALETTE, _label


PALETTE = {('orange' if k == 'magenta' else 'yellow' if k == 'rim_gray' else k): v
           for k,v in BASE_PALETTE.items()}
PALETTE.update(white=(229,229,218),ivory=(213,211,197),silver=(173,180,185),
               orange=(249,107,45),pink=(239,45,195),cyan=(47,211,231),
               purple=(129,64,218),blue=(43,93,229),yellow=(245,215,75),
               green=(92,215,115))
KEYS=list(PALETTE)

REGIONS={
    'clock_face':(0,0,512,512),'floor_clock':(512,0,1024,512),
    'side':(0,512,256,1024),'service_doors':(256,512,768,768),
    'chrome_button':(768,512,1024,768),'headphones':(256,768,768,896),
    'lcd':(768,768,896,896),'maker':(896,768,1024,896),
    'vents':(256,896,1024,1024),
}
BRANDING_REGIONS={'upper':(0,0,1024,256),'lower':(0,256,1024,512)}


def _font(size):
    try:
        return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size)
    except OSError:
        return ImageFont.load_default(size=size)


def _materials():
    image=Image.new('RGB',(256,256))
    d=ImageDraw.Draw(image)
    rng=random.Random(611)
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
        if name=='black_mesh':
            for y in range(3,61,5):
                for x in range(3+(y//5%2)*2,61,5):
                    d.rectangle((ox+x,oy+y,ox+x+1,oy+y+1),fill=(4,7,12))
    return image


def _point(cx,cy,r,a):
    a=math.radians(a)
    return (round(cx+r*math.cos(a)),round(cy+r*math.sin(a)))


def _rainbow(a,brightness=1):
    color=colorsys.hsv_to_rgb((.20-a/360)%1,.72,brightness)
    return tuple(round(v*255) for v in color)


def _rainbow_arc(d,center,radius,width,start=0,end=360,brightness=.96):
    cx,cy=center
    for a in range(start,end,2):
        d.line((_point(cx,cy,radius,a),_point(cx,cy,radius,a+2)),
               fill=_rainbow(a,brightness),width=width)


def _ornament(d,x,y,scale=1,color=(131,137,128)):
    # Angular clockwork corner stamp engraved on the actual white cabinet.
    points=[(x,y),(x+25*scale,y),(x+25*scale,y+18*scale),
            (x+8*scale,y+18*scale),(x+8*scale,y+41*scale),
            (x+35*scale,y+41*scale)]
    d.line(points,fill=color,width=max(1,round(2*scale)))
    d.ellipse((x+23*scale,y+29*scale,x+46*scale,y+52*scale),outline=color,
              width=max(1,round(2*scale)))
    d.line((x+35*scale,y+29*scale,x+35*scale,y+41*scale),fill=color,
           width=max(1,round(2*scale)))


def _plate_border(d,size=512):
    edge=(141,145,135)
    points=[(14,34),(32,14),(size-32,14),(size-14,34),
            (size-14,size-34),(size-32,size-14),(32,size-14),(14,size-34),(14,34)]
    d.line(points,fill=edge,width=2)
    for x,y in ((29,39),(size-30,39),(29,size-39),(size-30,size-39)):
        d.ellipse((x-4,y-4,x+4,y+4),fill=(162,167,158),outline=(113,120,114))
        d.line((x-2,y,x+2,y),fill=(237,239,223),width=1)


def _clock_plate(floor=False):
    image=Image.new('RGB',(512,512),PALETTE['white'])
    d=ImageDraw.Draw(image)
    _plate_border(d)
    if not floor:
        # Controller geometry hides the central field. Artwork therefore stays
        # in a narrow outside band, matching the prominent clock-face surround.
        for r in (215,226,235):
            _rainbow_arc(d,(256,256),r,3)
        for i in range(60):
            a=-90+i*6
            r0=203 if i%5 else 197
            d.line((_point(256,256,r0,a),_point(256,256,213,a)),
                   fill=_rainbow(a),width=2 if i%5 else 3)
        for i in range(12):
            a=-75+i*30
            p=[_point(256,256,227,a-11),_point(256,256,227,a-3),
               _point(256,256,234,a),_point(256,256,227,a+3),
               _point(256,256,227,a+11)]
            d.line(p,fill=_rainbow(a),width=3)
        for x,y,a in ((74,67,-135),(438,67,-45),(74,445,135),(438,445,45)):
            # Stylized spear/clock-hand motifs are thin engraved color lines.
            c=_rainbow(a)
            d.polygon(((x,y),(x-19,y+26),(x+20,y-9)),outline=c,width=2)
            for dx,dy in ((-22,-11),(21,26)):
                d.line((x+dx-6,y+dy-5,x+dx,y+dy+5,x+dx+6,y+dy-5),fill=c,width=2)
        d.rectangle((222,14,290,38),fill=PALETTE['white'])
        _label(image,(256,25),'XII',26,_rainbow(-90),True)
        d.rectangle((228,472,284,497),fill=PALETTE['white'])
        _label(image,(256,483),'VI',27,_rainbow(90),True)
        _label(image,(256,504),'CHRONO CIRCLE',9,(147,153,138))
    else:
        for x,y in ((26,30),(435,30),(26,430),(435,430)):
            _ornament(d,x,y,.85)
        d.ellipse((58,58,454,454),outline=(171,163,157),width=2)
        # Printed perimeter teeth, inner rainbow and central concentric emblem.
        for i in range(32):
            a=i*360/32
            p=[_point(256,256,203,a),_point(256,256,216,a),
               _point(256,256,216,a+5),_point(256,256,204,a+5),
               _point(256,256,204,a+11.25)]
            d.line(p,fill=(214,127,207),width=3)
        for r,w in ((186,6),(177,2),(157,3),(145,2)):
            _rainbow_arc(d,(256,256),r,w)
        nums=('XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI')
        for i,num in enumerate(nums):
            a=-90+i*30
            _label(image,_point(256,256,167,a),num,18,_rainbow(a),True)
        for i in range(60):
            a=-90+i*6
            d.line((_point(256,256,134,a),_point(256,256,142,a)),
                   fill=(149,155,143),width=1 if i%5 else 2)
        for r,w in ((91,3),(83,2),(64,5),(49,2),(24,6)):
            d.ellipse((256-r,256-r,256+r,256+r),outline=(137,142,132),width=w)
        d.polygon(((256,169),(248,219),(256,230),(264,219)),fill=(142,145,133))
        d.polygon(((318,271),(277,255),(267,263),(277,271)),fill=(142,145,133))
        _label(image,(256,365),'CHRONO',18,(143,148,132),True)
        _label(image,(256,385),'CIRCLE',16,(143,148,132),True)
    return image


def _side():
    image=Image.new('RGB',(256,512),(27,29,35))
    d=ImageDraw.Draw(image)
    for poly in (((22,0),(47,0),(70,177),(50,337),(23,482),(9,482),(27,320),(44,176)),
                 ((224,0),(239,0),(246,195),(209,311),(236,493),(214,493),(188,309),(222,195))):
        d.polygon(poly,fill=(208,87,42))
    for r in (75,62,19):
        d.ellipse((129-r,203-r,129+r,203+r),outline=(118,127,129),width=3)
    for a in range(0,360,30):
        d.line((_point(129,203,47,a),_point(129,203,60,a)),fill=(115,126,130),width=2)
    for a in (25,157,265):
        d.line((_point(129,203,19,a),_point(129,203,97,a)),fill=(114,121,125),width=3)
        x,y=_point(129,203,98,a)
        d.ellipse((x-5,y-5,x+5,y+5),outline=(129,137,137),width=2)
    d.line((130,298,148,331,147,459),fill=(102,111,118),width=2)
    _label(image,(128,403),'CHRONO',20,(133,141,141),True)
    _label(image,(128,430),'CIRCLE',18,(133,141,141),True)
    return image


def _details():
    image=Image.new('RGB',(1024,1024),PALETTE['white'])
    image.paste(_clock_plate(),(0,0))
    image.paste(_clock_plate(True),(512,0))
    image.paste(_side(),(0,512))
    d=ImageDraw.Draw(image)
    # Two very clean, nearly unprinted white service door panels.
    for x0,x1 in ((256,510),(514,768)):
        d.rectangle((x0+8,522,x1-8,758),fill=(219,219,204),outline=(150,154,144),width=2)
        d.line((x0+15,530,x1-16,530),fill=(234,235,220),width=2)
        _ornament(d,x0+18,700,.90)
        for x,y in ((x0+15,534),(x1-16,534),(x0+15,746),(x1-16,746)):
            d.ellipse((x-3,y-3,x+3,y+3),fill=(133,143,135))
        x=x0+125
        d.ellipse((x-9,547,x+9,562),fill=(170,179,172),outline=(118,127,121))
    d.rectangle((739,644,754,670),fill=(193,199,190),outline=(167,176,166))
    # Blank polished silver controller key face. Its curved housing is geometry.
    d.rectangle((768,512,1023,767),fill=(153,166,176))
    for y in range(520,760):
        value=174+round(60*max(0,1-abs(y-592)/118))
        d.line((777,y,1015,y),fill=(value,min(255,value+4),min(255,value+8)))
    d.line((789,534,1000,534),fill=(252,253,244),width=7)
    d.line((789,744,1000,744),fill=(76,91,103),width=5)
    # Metallic headphone and tiny RGB status strip.
    d.rectangle((256,768,767,895),fill=(195,189,181))
    d.line((264,780,758,780),fill=(232,228,211),width=2)
    d.line((264,883,758,883),fill=(131,134,127),width=2)
    d.arc((482,789,543,844),180,360,fill=(102,110,111),width=5)
    d.rectangle((480,817,489,838),fill=(102,110,111))
    d.rectangle((536,817,545,838),fill=(102,110,111))
    _label(image,(512,860),'HEADPHONE',16,(102,110,111),True)
    for x,c in ((310,PALETTE['green']),(338,PALETTE['pink']),(364,PALETTE['cyan'])):
        d.ellipse((x-4,820,x+4,828),fill=c)
    for x in (625,643):
        d.ellipse((x-4,820,x+4,828),fill=(36,88,237))
    # Service card reader, not an artificial character thumbnail.
    d.rectangle((768,768,895,895),fill=(37,72,90))
    d.rectangle((777,778,886,885),outline=(57,184,238),width=6)
    d.rectangle((784,788,879,875),fill=(14,26,41))
    _label(image,(832,810),'CARD',15,(236,164,78),True)
    _label(image,(832,834),'TOUCH TO PLAY',9,(188,217,226),True)
    _label(image,(832,858),'A.M.PASS',10,(158,190,204))
    d.rectangle((896,768,1023,895),fill=(221,222,207))
    _label(image,(960,795),'ANDAMIRO',13,(117,135,135),True)
    _label(image,(960,820),'CHRONO',12,(134,144,135),True)
    _label(image,(960,839),'CIRCLE',12,(134,144,135),True)
    _label(image,(960,871),'SERVICE',9,(133,144,131))
    d.rectangle((256,896,1023,1023),fill=(188,190,177))
    for y in range(905,1016,5):
        for x in range(265+(y//5%2)*2,1015,5):
            d.rectangle((x,y,x+1,y+1),fill=(94,108,107))
    return image


def _wordmark(image,y,ink,background):
    d=ImageDraw.Draw(image)
    d.rectangle((0,y,1023,y+255),fill=background)
    font=_font(98)
    letters='CHRONO'
    widths=[d.textlength(c,font=font) for c in letters]
    total=sum(widths)+len(letters)*4
    x=(1024-total)/2
    for index,(letter,w) in enumerate(zip(letters,widths)):
        if index==3:
            d.ellipse((x+4,y+35,x+w-2,y+115),outline=ink,width=5)
            d.ellipse((x+13,y+44,x+w-11,y+106),outline=ink,width=3)
            d.ellipse((x+21,y+53,x+w-19,y+97),outline=ink,width=3)
        else:
            d.text((x,y+23),letter,font=font,fill=ink)
        x+=w+4
    left=(1024-total)/2
    d.polygon(((59,y+83),(left+12,y+73),(left+12,y+87)),fill=ink)
    d.polygon(((965,y+83),(1024-left-12,y+73),(1024-left-12,y+87)),fill=ink)
    d.text((512,y+182),'CIRCLE',font=_font(86),fill=ink,anchor='mm')


def _branding():
    # The top wordmark is printed on clear acrylic: only its white lettering
    # writes pixels. The lower service sign remains an opaque ivory plate.
    image=Image.new('RGBA',(1024,512),(0,0,0,0))
    _wordmark(image,0,(243,244,233,255),(0,0,0,0))
    _wordmark(image,256,(139,144,133),(221,220,204))
    d=ImageDraw.Draw(image)
    d.rectangle((7,263,1016,504),outline=(164,168,155),width=2)
    for x,y in ((17,273),(1006,273),(17,495),(1006,495)):
        d.ellipse((x-3,y-3,x+3,y+3),fill=(145,153,141))
    # Native cutout rendering uses hard alpha, including the font edge pixels.
    image.putalpha(image.getchannel('A').point(lambda a:255 if a>=128 else 0))
    # A four-pixel charcoal print edge keeps the clear sign readable where its
    # white lettering overlaps the pale poster behind it. Include every part
    # of the native mark: letter shapes, concentric O and extended clock points.
    upper=image.crop((0,0,1024,256))
    expanded=upper.getchannel('A').filter(ImageFilter.MaxFilter(9))
    edged=Image.new('RGBA',upper.size,(0,0,0,0))
    edged.paste((32,37,42,255),(0,0),expanded)
    edged.alpha_composite(upper)
    image.paste(edged,(0,0))
    return image


def build_textures(textures):
    """Write materials256², details1024² and dual branding1024x512."""
    textures=Path(textures)
    textures.mkdir(parents=True,exist_ok=True)
    _materials().save(textures/'chrono_circle_materials.png')
    _details().save(textures/'chrono_circle_details.png')
    _branding().save(textures/'chrono_circle_branding.png')
    return dict(PALETTE),list(KEYS)
