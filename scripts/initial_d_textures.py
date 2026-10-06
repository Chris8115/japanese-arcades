"""Original printed panels for the single-seat Initial D Arcade Stage 3 cab.

Drawn from shapes and lettering; no reference-photo pixels are distributed.
Geometry and its solid-colour material atlas are authored separately.
"""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'src/main/resources/assets/funpackcustom/textures/block'
WHITE, INK, GREEN, LIME, RED = '#f4f3e7', '#151b1d', '#286a49', '#a1c546', '#df3335'


def font(size, japanese=False, italic=False):
    name = 'meiryob.ttc' if japanese else ('arialbi.ttf' if italic else 'arialbd.ttf')
    return ImageFont.truetype('C:/Windows/Fonts/' + name, size)


def text(im, xy, value, size, fill=WHITE, stroke=0, outline=INK, japanese=False, italic=False):
    ImageDraw.Draw(im).text(xy, value, font=font(size, japanese, italic), anchor='mm',
                           fill=fill, stroke_width=stroke, stroke_fill=outline)


def gradient(size, top, bottom):
    from PIL import ImageColor
    im = Image.new('RGB', size)
    d = ImageDraw.Draw(im)
    a, b = ImageColor.getrgb(top), ImageColor.getrgb(bottom)
    for y in range(size[1]):
        t = y / max(1, size[1]-1)
        d.line((0, y, size[0], y), fill=tuple(round(v*(1-t)+w*t) for v, w in zip(a, b)))
    return im


def checker(d, box, cell, light=WHITE, dark=INK):
    x0, y0, x1, y1 = box
    for y in range(y0, y1, cell):
        for x in range(x0, x1, cell):
            d.rectangle((x,y,min(x+cell-1,x1),min(y+cell-1,y1)),
                        fill=light if ((x-x0)//cell+(y-y0)//cell)%2 else dark)


def logo(width=1040, height=350):
    """Wide cream/black title with red D3, suitable for the backlit header."""
    im = Image.new('RGBA', (width, height), (0,0,0,0))
    text(im,(width*.43,height*.29),'頭文字',round(height*.34),WHITE,
         round(height*.017),INK,True,True)
    text(im,(width*.775,height*.34),'D',round(height*.60),RED,
         round(height*.019),WHITE,False,True)
    text(im,(width*.938,height*.49),'3',round(height*.50),WHITE,
         round(height*.015),INK,False,True)
    text(im,(width*.50,height*.72),'INITIAL D',round(height*.23),WHITE,
         round(height*.009),INK,False,True)
    text(im,(width*.5,height*.945),'ARCADE STAGE Ver.3',round(height*.12),WHITE,
         round(height*.006),INK,False,True)
    return im


def paste(im, layer, xy):
    im.paste(layer, tuple(round(v) for v in xy), layer if layer.mode=='RGBA' else None)


def ae86(size=(800,440), rear=False):
    """A hand-drawn panda coupe: hatch roof, black sill, pop-ups and five-spokes."""
    im = Image.new('RGBA',(1000,580),(0,0,0,0))
    d = ImageDraw.Draw(im)
    if rear:
        # Looking over the rear bumper toward the distant road.
        d.ellipse((110,423,884,558),fill=(0,0,0,120))
        d.rounded_rectangle((141,344,237,531),20,fill='#121416')
        d.rounded_rectangle((764,344,851,531),20,fill='#121416')
        d.polygon([(153,300),(244,145),(678,123),(808,271),(869,349),(848,496),(156,501),(120,354)],fill='#e8e9df',outline=INK,width=8)
        d.polygon([(268,162),(662,145),(769,273),(199,292)],fill='#394b52',outline=INK,width=7)
        d.polygon([(294,178),(409,170),(302,275),(226,281)],fill='#91a9aa')
        d.line((193,302,783,282),fill='#1b2022',width=18)
        d.polygon([(122,352),(862,342),(852,454),(146,460)],fill='#222727')
        d.rectangle((171,365,350,398),fill='#bd2636')
        d.rectangle((649,355,817,389),fill='#bc2935')
        d.rectangle((171,400,350,417),fill='#e98749')
        d.rectangle((649,392,817,408),fill='#e98749')
        d.rectangle((402,385,589,449),fill='#e9e4cf',outline='#090e0e',width=4)
        text(im,(495,417),'13-954',34,INK)
        text(im,(501,359),'TRUENO',22,'#edeade',italic=True)
        d.polygon([(154,458),(850,451),(843,492),(162,500)],fill='#cdd2ca')
        d.line((190,482,812,473),fill='#242729',width=9)
        d.ellipse((739,479,785,508),fill='#151619',outline='#a9b2b1',width=5)
    else:
        d.ellipse((58,437,940,548),fill=(0,0,0,100))
        # Far wheels and the wedge silhouette in a three-quarter front view.
        d.ellipse((710,285,806,430),fill='#181b1d')
        d.polygon([(57,352),(156,292),(335,262),(444,127),(696,116),(809,208),(930,340),(885,426),(616,491),(104,455)],fill='#e4e7de',outline=INK,width=7)
        d.polygon([(350,265),(464,145),(673,137),(769,216)],fill='#283c42',outline=INK,width=6)
        d.polygon([(378,259),(474,158),(526,153),(468,263)],fill='#a0b5b3')
        d.line((556,140,559,240),fill=INK,width=7)
        d.polygon([(790,224),(858,283),(672,330),(599,263)],fill='#27373b',outline=INK,width=7)
        d.polygon([(57,353),(620,402),(644,450),(102,437)],fill='#1c2223')
        d.polygon([(642,402),(927,337),(887,419),(640,482)],fill='#1c2223')
        d.polygon([(85,345),(158,307),(331,293),(507,321),(607,382)],fill='#f5f5e7',outline='#545f61',width=3)
        # Distinctive raised rectangular headlamps.
        d.polygon([(126,331),(142,293),(246,302),(251,343)],fill='#e8e9dc',outline=INK,width=5)
        d.polygon([(370,352),(380,313),(487,323),(498,365)],fill='#e8e9dc',outline=INK,width=5)
        d.polygon([(131,329),(144,307),(231,315),(237,338)],fill='#fffed7',outline='#525756',width=3)
        d.polygon([(378,350),(387,326),(474,335),(486,359)],fill='#fffed7',outline='#525756',width=3)
        for x,y,rx,ry in [(266,436,70,88),(789,406,65,86)]:
            d.ellipse((x-rx,y-ry,x+rx,y+ry),fill='#121619',outline='#596368',width=4)
            d.ellipse((x-rx*.69,y-ry*.69,x+rx*.69,y+ry*.69),fill='#647276',outline='#c4d0cc',width=5)
            for angle in range(0,360,72):
                a=math.radians(angle)
                d.line((x,y,x+math.cos(a)*rx*.65,y+math.sin(a)*ry*.65),fill='#dfe3d8',width=10)
            d.ellipse((x-11,y-13,x+11,y+13),fill='#20282b')
        text(im,(461,377),'TRUENO',23,'#e6e9e0',italic=True)
        # The familiar tofu-shop door lettering is kept within the white door.
        text(im,(727,356),'藤原とうふ店',28,'#0b1418',japanese=True)
        d.rectangle((527,419,606,451),fill='#dedfcb')
        text(im,(568,435),'86',23,INK)
    return im.resize(size,Image.Resampling.LANCZOS)


def marquee():
    im=gradient((1152,512),'#d5e8bf','#1f6746');d=ImageDraw.Draw(im)
    for i in range(-5,15):
        x=i*150
        d.polygon([(x,0),(x+40,0),(x-170,512),(x-220,512)],fill='#76a951')
    d.polygon([(0,0),(1152,0),(1152,65),(0,245)],fill='#172d25')
    checker(d,(0,456,1152,504),24,WHITE,GREEN)
    title=logo(1010,340);paste(im,title,(38,95))
    text(im,(135,44),'SEGA',48,WHITE,3,'#23518b')
    text(im,(822,47),'THE LEGEND OF THE STREET',28,WHITE,italic=True)
    d.rectangle((4,4,1147,507),outline=INK,width=9)
    return im


def screen():
    im=gradient((1024,768),'#2c4662','#eec58a');d=ImageDraw.Draw(im)
    d.polygon([(0,165),(115,95),(252,197),(397,118),(495,185),(658,81),(793,182),(923,131),(1024,224),(1024,491),(0,491)],fill='#21483e')
    d.polygon([(0,278),(183,186),(330,318),(510,187),(689,263),(863,179),(1024,267),(1024,572),(0,572)],fill='#172e2e')
    # Perspective hairpin disappearing into the mountains.
    road=[(584,245),(713,251),(779,322),(684,385),(576,439),(631,506),(1024,640),(1024,768),(0,768),(321,510),(437,415),(604,342),(654,312)]
    d.polygon(road,fill='#666b6a',outline='#c8c8b2',width=8)
    d.line([(691,248),(752,319),(652,377),(502,455),(478,501),(898,729)],fill='#eac944',width=8)
    d.line([(595,251),(671,307),(635,330),(441,416),(330,510),(4,764)],fill='#d7d9c6',width=9)
    for a,b in [((540,443),(530,451)),((520,463),(504,475)),((493,489),(463,511)),((429,538),(370,582)),((316,622),(220,697))]:
        d.line((*a,*b),fill='#e6e5cf',width=9)
    # Guardrail and trees, with repeating posts giving depth.
    for i in range(11):
        x=1024-i*47;y=620-i*20
        d.line((x,y,x,y+42),fill='#b6b9ac',width=6)
    d.line([(520,402),(578,443),(1024,617)],fill='#d3d8c8',width=15)
    for x,y,s in [(52,323,90),(150,293,70),(272,266,55),(859,282,75),(957,278,104)]:
        d.rectangle((x-5,y,x+5,y+110),fill='#303023')
        for delta in (0,30,60):d.polygon([(x,y-s+delta),(x-s*.52,y+delta),(x+s*.52,y+delta)],fill='#254435')
    paste(im,ae86((375,218),True),(342,456))
    # Version-3-style high-contrast racing HUD.
    d.rounded_rectangle((12,12,426,93),12,fill='#151b26',outline='#d0dbdf',width=3)
    text(im,(58,38),'1',54,'#ffd65b',3,INK,italic=True)
    text(im,(96,48),'st',27,'#fff7c9',italic=True)
    text(im,(281,40),'AKINA / DOWNHILL',23,WHITE,italic=True)
    text(im,(276,71),'TIME  02\'36\"481',25,'#ffd87a')
    d.rounded_rectangle((802,18,1007,132),12,fill='#151b26',outline='#d0dbdf',width=3)
    text(im,(905,50),'TIME LEFT',25,WHITE)
    text(im,(906,98),'68',60,'#ffd449',2,INK,italic=True)
    d.rounded_rectangle((799,476,1008,749),16,fill='#17242c',outline='#dce4d7',width=4)
    path=[(927,499),(882,525),(940,551),(906,583),(959,615),(861,640),(897,673)]
    d.line(path,fill='#d7dfb7',width=8)
    d.ellipse((887,662,907,682),fill='#ff7048',outline=WHITE,width=3)
    text(im,(904,718),'COURSE MAP',20,WHITE)
    d.rounded_rectangle((15,627,302,749),15,fill='#192128',outline='#d3dcd8',width=3)
    text(im,(153,682),'138',78,WHITE,2,INK,italic=True)
    text(im,(243,721),'km/h',23,WHITE)
    d.rounded_rectangle((318,651,391,749),10,fill='#192128',outline='#d3dcd8',width=3)
    text(im,(354,702),'4',61,'#f3d946',2,INK)
    text(im,(566,722),'AE86  SPRINTER TRUENO',22,WHITE,2,INK,italic=True)
    return im


def side():
    im=gradient((512,1280),'#dae9c9','#1e6145');d=ImageDraw.Draw(im)
    d.polygon([(0,0),(180,0),(512,766),(512,1280),(343,1280),(0,581)],fill='#0c2522')
    for x in range(-350,1000,88):d.line((x,0,x-450,1280),fill='#71a85f',width=4)
    paste(im,logo(480,230),(8,70))
    text(im,(256,347),'AKINA SPEED STARS',26,WHITE,2,INK,italic=True)
    car=ae86((710,412)).rotate(-22,Image.Resampling.BICUBIC,expand=True)
    paste(im,car,(-137,288))
    d.polygon([(0,875),(512,729),(512,941),(0,1087)],fill=WHITE)
    text(im,(256,917),'藤原とうふ店',46,INK,japanese=True)
    text(im,(256,982),'(自家用)',26,INK,japanese=True)
    checker(d,(0,1080,512,1144),32,WHITE,GREEN)
    text(im,(256,1206),'SEGA',69,WHITE,4,'#24548b')
    d.rectangle((5,5,506,1274),outline=INK,width=10)
    return im


def seat_back():
    im=gradient((768,768),'#e6edda','#508560');d=ImageDraw.Draw(im)
    d.polygon([(0,0),(228,0),(768,563),(768,768),(589,768),(0,147)],fill='#132e27')
    for i in range(8):
        y=170+i*56;d.line((0,y,768,y-220),fill='#b8d58d',width=4)
    paste(im,logo(695,300),(25,57))
    paste(im,ae86((653,375)),(54,324))
    checker(d,(0,693,768,729),36,WHITE,GREEN)
    text(im,(386,747),'SEGA  •  INITIAL D ARCADE STAGE 3',22,WHITE)
    d.rectangle((5,5,762,762),outline=INK,width=10)
    return im


def pedestal_side():
    im=Image.new('RGB',(1280,256),WHITE);d=ImageDraw.Draw(im)
    d.polygon([(0,0),(1280,0),(1137,88),(0,88)],fill=GREEN)
    d.polygon([(939,256),(1148,73),(1280,73),(1280,256)],fill=INK)
    checker(d,(0,215,970,247),32,WHITE,GREEN)
    text(im,(467,145),'藤原とうふ店 (自家用)',69,INK,japanese=True)
    text(im,(1170,181),'D3',100,WHITE,4,RED,italic=True)
    text(im,(215,42),'INITIAL D / ARCADE STAGE3',29,WHITE,italic=True)
    d.rectangle((3,3,1276,252),outline=INK,width=7)
    return im


def details():
    im=Image.new('RGB',(1024,256),INK);d=ImageDraw.Draw(im)
    for x in (0,256,512,768):
        d.rectangle((x+8,8,x+247,247),outline='#8a9691',width=3)
    text(im,(128,90),'SEGA',65,WHITE,3,'#285897')
    text(im,(128,174),'DRIVING SIMULATOR',17,WHITE)
    d.ellipse((335,29,433,127),fill='#56b780',outline='#d5e6d5',width=7)
    text(im,(384,179),'START',37,WHITE)
    text(im,(640,93),'VIEW',48,WHITE)
    text(im,(640,175),'CHANGE',25,LIME)
    text(im,(896,72),'SHIFT',36,WHITE)
    text(im,(896,139),'−  /  +',57,LIME)
    text(im,(896,209),'SEQUENTIAL',20,WHITE)
    return im


def build_textures(destination=TEXTURES):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    outputs={}
    for name, fn in {'marquee':marquee,'screen':screen,'side':side,
                     'seat_back':seat_back,'pedestal_side':pedestal_side,'details':details}.items():
        path=destination / f'initial_d_{name}.png';fn().save(path)
        outputs[name]=path
    return outputs


if __name__=='__main__':
    for name,path in build_textures().items():print(name,path)
