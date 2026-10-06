"""Reference-inspired printed artwork for the classic lantern Taiko cabinet.

All artwork is drawn here from shapes and type; reference photographs are not
sampled or copied into the runtime assets. Native dimensions preserve mipmaps.
The separate geometry generator owns the hardware/material atlas.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'src/main/resources/assets/funpackcustom/textures/block'
INK = '#542e29'
CREAM = '#fff4d4'
RED = '#ed4734'
BLUE = '#38b6c4'
GOLD = '#ffc643'


def font(size, japanese=False):
    candidates = (['C:/Windows/Fonts/meiryob.ttc', 'C:/Windows/Fonts/YuGothB.ttc']
                  if japanese else ['C:/Windows/Fonts/arialbd.ttf'])
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError('Taiko artwork requires a bold Japanese font (Meiryo or Yu Gothic).')


def text(image, xy, value, size, fill=INK, outline=None, stroke=0, japanese=False):
    ImageDraw.Draw(image).text(xy, value, font=font(size, japanese), anchor='mm',
                              fill=fill, stroke_fill=outline, stroke_width=stroke)


def flower(draw, x, y, radius, fill='#f9bec6', edge=INK, width=5):
    for angle in (-90, -18, 54, 126, 198):
        a = math.radians(angle)
        px, py = x + radius * .58 * math.cos(a), y + radius * .58 * math.sin(a)
        pr = radius * .54
        draw.ellipse((px-pr, py-pr, px+pr, py+pr), fill=fill, outline=edge, width=width)
    draw.ellipse((x-radius*.51, y-radius*.51, x+radius*.51, y+radius*.51), fill=fill)
    for angle in range(0, 360, 72):
        a = math.radians(angle)
        ex, ey = x+radius*.4*math.cos(a), y+radius*.4*math.sin(a)
        draw.line((x, y, ex, ey), fill=edge, width=max(1,width//2))
        draw.ellipse((ex-3,ey-3,ex+3,ey+3),fill=edge)
    draw.ellipse((x-4,y-4,x+4,y+4),fill=edge)


def mascot(size, blue=False, wave=False):
    """A cheerful drum character, with a round face and visible barrel side."""
    scale = size / 300
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    def box(values): return tuple(round(v*scale) for v in values)
    def ellipse(values, fill, edge=INK, width=4):
        d.ellipse(box(values), fill=fill, outline=edge, width=max(1,round(width*scale)))
    body, face = (RED, BLUE) if blue else (BLUE, RED)
    # Stubby feet and outstretched mitten hands sit behind the drum shell.
    ellipse((78,239,124,276), CREAM)
    ellipse((170,242,219,277), CREAM)
    ellipse((15,141,74,207), CREAM)
    ellipse((235,87 if wave else 144,286,156 if wave else 207), CREAM)
    ellipse((54,62,268,264), body)
    d.arc(box((105,74,268,253)), -75, 78, fill='#fdf7dc', width=max(2,round(9*scale)))
    ellipse((37,41,239,254), CREAM, width=6)
    ellipse((51,55,225,240), face, width=3)
    # Happy open mouth, dark oval eyes and two tiny pale reflections.
    ellipse((92,102,111,135), '#241e1c', '#241e1c', 1)
    ellipse((161,99,180,132), '#241e1c', '#241e1c', 1)
    d.pieslice(box((90,124,183,215)), 0, 180, fill='#5a2427', outline=INK, width=max(1,round(3*scale)))
    d.pieslice(box((107,156,172,209)), 0, 180, fill='#f69b9b')
    d.line(box((88,168,93,165)), fill=INK, width=max(1,round(3*scale)))
    d.line(box((181,165,187,162)), fill=INK, width=max(1,round(3*scale)))
    return image


def paste_mascot(image, center, size, blue=False, angle=0, wave=False):
    figure = mascot(size, blue, wave)
    if angle:
        figure = figure.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    image.paste(figure, (round(center[0]-figure.width/2), round(center[1]-figure.height/2)), figure)


def crest(size=256):
    """Three comma-shaped tomoe in one red disc, matching the lantern emblem."""
    s = 4
    image = Image.new('RGBA', (size*s,size*s), (0,0,0,0))
    d = ImageDraw.Draw(image)
    c, r = size*s/2, size*s*.44
    d.ellipse((c-r,c-r,c+r,c+r),fill='#dc2730')
    # Transparent separators reveal the ribbed cream lantern under the crest.
    for degrees in (0,120,240):
        pts=[]
        for i in range(90):
            t=i/89
            angle=math.radians(degrees+10+132*t)
            distance=r*t
            pts.append((c+distance*math.cos(angle),c+distance*math.sin(angle)))
        d.line(pts,fill=(0,0,0,0),width=round(size*s*.070),joint='curve')
    return image.resize((size,size),Image.Resampling.LANCZOS)


def _marquee():
    image=Image.new('RGB',(1536,416),'#ffdc72');d=ImageDraw.Draw(image)
    # Golden rays and pink festival clouds frame the central Japanese lockup.
    for i in range(16):
        a=math.radians(i*22.5)
        b=a+.12
        d.polygon(((768,195),(768+1700*math.cos(a),195+1700*math.sin(a)),
                   (768+1700*math.cos(b),195+1700*math.sin(b))),fill='#fff0a5')
    for x,y,r in ((20,25,125),(170,44,115),(1460,22,140),(1320,83,100)):
        d.ellipse((x-r,y-r,x+r,y+r),fill='#f8aab8',outline=CREAM,width=12)
    for x in range(-25,1550,73):
        d.arc((x,340,x+110,434),180,360,fill='#ef9b4a',width=7)
    for x,y,r in ((354,93,28),(1191,285,27),(127,344,28),(1410,352,32),(1212,57,22)):
        flower(d,x,y,r,'#fff3d2',width=3)
    paste_mascot(image,(188,243),352,False,-13,True)
    paste_mascot(image,(1360,240),344,True,13,True)
    text(image,(779,59),'namco',39,'#c5252b')
    text(image,(782,159),'太鼓の達人',132,'#ec3e30',INK,13,True)
    text(image,(782,154),'太鼓の達人',132,'#ed4434',CREAM,6,True)
    text(image,(790,287),'12',124,'#fff174','#712c26',9)
    text(image,(514,312),'ドン！',58,'#219cab',CREAM,5,True)
    text(image,(1038,312),'カッ！',58,'#d64e37',CREAM,5,True)
    text(image,(789,380),'TAIKO NO TATSUJIN',25,INK)
    d.rectangle((4,4,1531,411),outline='#fff6cc',width=8)
    return image


def _screen():
    image=Image.new('RGB',(960,768),'#73d1e1');d=ImageDraw.Draw(image)
    for y in range(342,768):
        t=(y-342)/426
        d.line((0,y,960,y),fill=(round(242+9*t),round(161-85*t),round(126-39*t)))
    # Two high-contrast gameplay elements keep this readable at cabinet scale.
    d.rectangle((0,0,959,85),fill='#fff1bb')
    d.rectangle((0,0,190,85),fill='#ed5644')
    text(image,(94,43),'1P',48,CREAM,INK,2)
    text(image,(580,44),'おまつりタイム',39,INK,japanese=True)
    d.rounded_rectangle((19,91,940,125),radius=9,fill='#573847')
    for x in range(27,808,22):d.rectangle((x,98,x+17,119),fill='#ffd94b')
    text(image,(869,108),'魂',31,CREAM,japanese=True)
    d.rectangle((0,136,959,333),fill='#f3d895')
    d.rectangle((0,146,959,324),fill='#392f43')
    d.rectangle((196,156,959,313),fill='#545367')
    d.line((192,152,192,319),fill='#f2ce6d',width=5)
    for x in (132,):
        d.ellipse((x-63,172,x+63,298),outline='#fff8d6',width=9)
        d.ellipse((x-47,188,x+47,282),outline='#ac9e81',width=5)
    for x,blue in ((380,False),(495,False),(612,True),(733,False),(851,True)):
        d.ellipse((x-38,197,x+38,273),fill=BLUE if blue else RED,outline=CREAM,width=5)
        d.ellipse((x-15,223,x-9,233),fill=INK);d.ellipse((x+9,223,x+15,233),fill=INK)
        d.arc((x-13,232,x+13,253),0,180,fill=INK,width=3)
    text(image,(132,355),'良',36,'#fff3aa','#914937',3,True)
    # Festival tower, striped stage skirt, and hanging paper lanterns.
    d.rectangle((350,435,610,660),fill='#fff0cd',outline=INK,width=7)
    for x in range(360,610,50):d.rectangle((x,453,x+24,654),fill='#e74c45')
    d.polygon(((317,444),(365,391),(596,391),(646,444)),fill='#e7473d',outline=INK)
    d.line((317,445,646,445),fill='#6c3032',width=8)
    d.rectangle((417,466,545,548),fill='#f6c457',outline=INK,width=5)
    text(image,(481,507),'祭',58,'#bd3b35',japanese=True)
    d.rectangle((300,654,662,684),fill='#83384b')
    d.rectangle((284,684,680,709),fill='#f0c453')
    # The strings sag into the scene, providing familiar festival ambience.
    for left,right in ((-50,350),(615,1010)):
        d.arc((left,230,right,455),0,180,fill=INK,width=4)
        for i in range(7):
            x=left+35+i*(right-left-65)/6;y=345+37*math.sin(i*math.pi/6)
            d.line((x,y-9,x,y+8),fill=INK,width=2)
            d.rounded_rectangle((x-15,y,x+15,y+44),radius=12,fill='#fff4c4',outline='#b53a32',width=3)
    paste_mascot(image,(179,575),326,False,-10,True)
    paste_mascot(image,(782,577),326,True,10,True)
    for x,y,r in ((57,485,23),(897,483,27),(335,601,15),(652,605,16)):
        flower(d,x,y,r,'#ffebbf',width=3)
    d.rectangle((0,724,959,767),fill='#402d40')
    text(image,(144,746),'012450',28,CREAM)
    text(image,(480,746),'太鼓の達人',24,CREAM,japanese=True)
    text(image,(826,746),'CREDIT  0',22,CREAM)
    return image


def lattice(d,size):
    w,h=size
    for y in range(-40,h+60,45):
        for x in range(-40,w+60,52):
            d.line(((x,y),(x+26,y+15),(x+52,y),(x+52,y+30),(x+26,y+45),(x,y+30),(x,y)),fill='#ffe2a2',width=2)
            d.line(((x+26,y+15),(x+26,y+45)),fill='#ffe2a2',width=2)


def _front():
    image=Image.new('RGB',(1200,448),'#f4b737');d=ImageDraw.Draw(image)
    lattice(d,image.size)
    for x,y,r in ((91,106,107),(349,184,122),(831,96,116),(1082,271,137)):
        flower(d,x,y,r,'#ef7a27',width=7)
        d.ellipse((x-r*.5,y-r*.5,x+r*.5,y+r*.5),fill='#ef7a27')
        d.ellipse((x-r*.47,y-r*.47,x+r*.47,y+r*.47),outline=CREAM,width=9)
        d.ellipse((x-r*.31,y-r*.31,x+r*.31,y+r*.31),outline=CREAM,width=5)
        d.arc((x-19,y-6,x+19,y+22),0,180,fill=CREAM,width=6)
        for ex in (x-13,x+13):d.ellipse((ex-4,y-12,ex+4,y-3),fill=CREAM)
    for x,y,r in ((294,54,38),(77,317,44),(400,359,47),(977,61,41),(760,348,46),(1122,92,34)):
        flower(d,x,y,r,'#f9d2cd',width=4)
    # Flowing festival cloth stays graphic rather than becoming photo noise.
    for x in (-70,250,830,1140):
        d.polygon(((x,440),(x+115,180),(x+152,190),(x+83,440)),fill=CREAM,outline=INK)
        d.line((x+19,438,x+130,188),fill='#c74733',width=5)
    d.rectangle((463,0,737,447),fill=CREAM)
    for x in range(0,1200,42):
        if not 443<x<735:d.rectangle((x,413,x+40,447),fill=('#b4d8d0' if (x//42)%2 else '#fff0ce'))
    d.rectangle((0,0,1199,10),fill='#cc4635')
    return image


def _side():
    image=Image.new('RGB',(512,1536),'#fff1d1');d=ImageDraw.Draw(image)
    d.rectangle((8,8,503,1527),outline='#d84a32',width=16)
    d.rectangle((21,523,490,1514),fill='#f4b93f');lattice(d,image.size)
    # The upper white crest panel is unpatterned, as on the classic cabinet.
    d.rectangle((21,21,490,522),fill='#fff1d1')
    emblem=crest(326);image.paste(emblem,(93,76),emblem)
    text(image,(256,446),'太鼓の達人',62,'#de4733',japanese=True)
    for x,y,r in ((102,618,91),(407,780,110),(104,1107,107),(393,1375,122)):
        flower(d,x,y,r,'#ee7a2c',width=7)
    paste_mascot(image,(252,849),423,False,-13,True)
    paste_mascot(image,(249,1220),422,True,12,True)
    for x,y,r in ((414,555,40),(89,918,35),(426,1068,40),(108,1430,41)):
        flower(d,x,y,r,'#ffd9d1',width=4)
    return image


def _instructions():
    image=Image.new('RGB',(1024,112),'#fff2d5');d=ImageDraw.Draw(image)
    labels=('まんなかをたたく','ふちをたたく','リズムにあわせて','みんなでドンドン！')
    for i,label in enumerate(labels):
        x=i*256
        d.rectangle((x+3,3,x+252,108),outline='#da9676',width=2)
        color=RED if i%2==0 else BLUE
        d.ellipse((x+15,24,x+78,87),fill=CREAM,outline=INK,width=3)
        d.ellipse((x+24,33,x+69,78),fill=color,outline=INK,width=2)
        text(image,(x+165,44),label,17,INK,japanese=True)
        text(image,(x+165,78),'ドン！' if i%2==0 else 'カッ！',24,color,japanese=True)
    return image


def _podium_side():
    """Printed festival wrap for the forward drum podium's broad side wall."""
    image=Image.new('RGB',(1024,640),'#f4b737');d=ImageDraw.Draw(image)
    lattice(d,image.size)
    for x,y,r in ((105,94,139),(931,112,142),(701,485,181),(50,646,162)):
        flower(d,x,y,r,'#ed7929',width=8)
    for x,y,r in ((397,65,44),(881,357,53),(69,358,43),(475,615,57),(966,649,42)):
        flower(d,x,y,r,'#f9d2cd',width=5)
    # White fabric bands echo the flowing cloth on the front factory wrap.
    for x in (-153,301,805):
        d.polygon(((x,704),(x+242,109),(x+309,140),(x+118,704)),fill=CREAM,outline=INK)
        d.line((x+28,704,x+268,119),fill='#cc4936',width=8)
    d.ellipse((675,45,925,295),fill=CREAM,outline=INK,width=7)
    d.ellipse((691,61,909,279),outline='#e9792c',width=5)
    text(image,(802,169),'祭',143,'#d84832',japanese=True)
    paste_mascot(image,(330,347),550,False,-14,True)
    paste_mascot(image,(806,465),315,True,13,True)
    d.rectangle((0,0,1023,15),fill='#c64435')
    for x in range(0,1024,52):
        d.rectangle((x,602,x+51,639),fill='#b4d8d0' if (x//52)%2 else CREAM)
    d.rectangle((0,0,1023,639),outline='#a23b30',width=8)
    return image


def build_textures(textures=TEXTURES):
    """Write each full-face print; geometry owns materials and UV placement."""
    textures=Path(textures);textures.mkdir(parents=True,exist_ok=True)
    panels={'marquee':_marquee(),'screen':_screen(),'front':_front(),
            'side':_side(),'instructions':_instructions(),'lantern':crest(),
            'podium_side':_podium_side()}
    paths={}
    for name,image in panels.items():
        path=textures/f'taiko_{name}.png';image.save(path);paths[name]=path
    return paths


if __name__ == '__main__':
    for name,path in build_textures().items():
        with Image.open(path) as image:print(f'{name}: {image.width}x{image.height} {path}')
