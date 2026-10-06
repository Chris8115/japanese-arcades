"""Native red-cab DDR SuperNOVA hardware prints and stage panel materials.

The two generated illustrations live in art/ddr_supernova and are never edited
here. Details use a 1024-square atlas (64 pixels per model UV unit); all region
contracts have an eight-pixel inset to prevent neighbouring texture bleed.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from chunithm_textures import PALETTE as BASE_PALETTE, _label


PALETTE = {('red' if k == 'magenta' else 'yellow' if k == 'purple' else k): v
           for k, v in BASE_PALETTE.items()}
PALETTE.update(black=(15, 16, 19), charcoal=(32, 32, 35), white=(232, 233, 231),
               ivory=(205, 208, 207), silver=(189, 196, 199), steel=(93, 101, 108),
               red=(196, 22, 38), pink=(203, 32, 111), cyan=(34, 186, 211),
               yellow=(242, 175, 32), blue=(34, 64, 179), rim_gray=(157, 166, 172),
               green=(83, 188, 87), black_mesh=(28, 29, 31))
KEYS = list(PALETTE)
REGIONS = {
    'arrow_up': (0, 0, 256, 256), 'arrow_down': (256, 0, 512, 256),
    'arrow_left': (512, 0, 768, 256), 'arrow_right': (768, 0, 1024, 256),
    'plain_steel': (0, 256, 256, 512), 'center_diamond': (256, 256, 512, 512),
    'speaker': (512, 256, 768, 512), 'tweeter': (768, 256, 1024, 512),
    'stay_cool': (0, 512, 512, 640), 'foot_badge': (512, 512, 640, 640),
    'coin_slot': (640, 512, 768, 640), 'manufacturer': (768, 512, 1024, 640),
    'controls': (0, 640, 1024, 768), 'red_case': (0, 768, 512, 1024),
    'service': (512, 768, 768, 1024), 'warning': (768, 768, 1024, 1024),
}
UV_REGIONS = {name: [(x0 + 8) / 64, (y0 + 8) / 64,
                     (x1 - 8) / 64, (y1 - 8) / 64]
              for name, (x0, y0, x1, y1) in REGIONS.items()}


def _font(size, italic=False):
    return ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf' if italic else
                              'C:/Windows/Fonts/arialbd.ttf', size)


def _materials():
    image = Image.new('RGB', (256, 256))
    d = ImageDraw.Draw(image)
    rng = random.Random(2006)
    for i, name in enumerate(KEYS):
        ox, oy = i % 4 * 64, i // 4 * 64
        for y in range(0, 64, 4):
            for x in range(0, 64, 4):
                v = rng.choice((-2, 0, 0, 2))
                color = tuple(max(0, min(255, n + v)) for n in PALETTE[name])
                d.rectangle((ox+x, oy+y, ox+x+3, oy+y+3), fill=color)
        if name == 'vent':
            for y in range(4, 63, 6):
                d.line((ox+4, oy+y, ox+59, oy+y), fill=(5, 7, 10), width=2)
        if name == 'black_mesh':
            for y in range(3, 62, 5):
                for x in range(3 + (y//5 % 2)*2, 62, 5):
                    d.rectangle((ox+x, oy+y, ox+x+1, oy+y+1), fill=(4, 5, 7))
    return image


def _screw(d, x, y, r=5):
    d.ellipse((x-r-1, y-r-1, x+r+1, y+r+1), fill=(57, 62, 64))
    d.ellipse((x-r, y-r, x+r, y+r), fill=(190, 199, 201))
    d.line((x-r+2, y, x+r-2, y), fill=(49, 55, 58), width=2)
    d.line((x, y-r+2, x, y+r-2), fill=(71, 77, 80), width=1)


def _steel(size=(256, 256), dark=False, screws=True):
    image = Image.new('RGB', size)
    d = ImageDraw.Draw(image)
    rng = random.Random(45)
    for y in range(size[1]):
        v = rng.choice((-3, -1, 0, 1, 2))
        base = (58, 61, 65) if dark else (177, 185, 188)
        d.line((0, y, size[0], y), fill=tuple(n+v for n in base))
    d.rectangle((8, 8, size[0]-9, size[1]-9), outline=(89, 97, 100), width=2)
    d.rectangle((11, 11, size[0]-12, size[1]-12), outline=(213, 219, 220) if not dark else (82, 85, 88), width=1)
    if screws:
        for x in (20, size[0]-21):
            for y in (20, size[1]-21):
                _screw(d, x, y)
    return image


def _arrow(direction, blue=False):
    image = Image.new('RGB', (256, 256), (173, 183, 185))
    d = ImageDraw.Draw(image)
    base = (28, 65, 176) if blue else (189, 27, 98)
    for y in range(9, 248):
        lift = round(18 * (1 - abs(y-127) / 127))
        d.line((9, y, 247, y), fill=tuple(min(255, n+lift) for n in base))
    # DDR's coloured arrows are printed on square acrylic with dark rounded
    # corner panels; no additional translucent geometry is needed on the pad.
    d.pieslice((-74, -74, 74, 74), 0, 90, fill=(39, 40, 47))
    d.pieslice((182, -74, 330, 74), 90, 180, fill=(39, 40, 47))
    d.pieslice((-74, 182, 74, 330), 270, 360, fill=(39, 40, 47))
    d.pieslice((182, 182, 330, 330), 180, 270, fill=(39, 40, 47))
    d.rectangle((9, 9, 247, 247), outline=(229, 229, 231), width=3)
    points = [(128, 47), (211, 126), (165, 126), (165, 203), (91, 203), (91, 126), (45, 126)]
    angle = {'up': 0, 'right': 90, 'down': 180, 'left': 270}[direction]
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    points = [(round(128+(x-128)*ca-(y-128)*sa), round(128+(x-128)*sa+(y-128)*ca)) for x, y in points]
    d.line(points + points[:1], fill=(84, 181, 246) if blue else (245, 130, 186), width=12, joint='curve')
    d.line(points + points[:1], fill=(244, 240, 246), width=6, joint='curve')
    _label(image, (128, 20), 'Dance Dance Revolution', 10, (220, 225, 238), True)
    _label(image, (128, 237), 'Dance Dance Revolution', 10, (220, 225, 238), True)
    for x in (19, 237):
        for y in (19, 237):
            _screw(d, x, y, 4)
    return image


def _center():
    image = _steel(dark=True)
    d = ImageDraw.Draw(image)
    for y in range(39, 236, 24):
        for x in range(33 + (y//24 % 2)*12, 235, 24):
            d.polygon(((x-5,y-3),(x+3,y-8),(x+6,y-6),(x-2,y)), fill=(88, 92, 96))
            d.line((x-5,y-2,x+4,y-7), fill=(26, 30, 33), width=1)
    # Corner screws remain visible over the embossed anti-slip diamond tread.
    for x in (20,235):
        for y in (20,235):
            _screw(d,x,y)
    return image


def _speaker(tweeter=False):
    image = Image.new('RGB', (256,256), (24,25,28))
    d = ImageDraw.Draw(image)
    for r,c in ((121,(112,118,122)),(116,(49,52,56)),(108,(14,16,18)),(102,(52,55,57)),(97,(30,32,35))):
        d.ellipse((128-r,128-r,128+r,128+r),fill=c)
    if tweeter:
        d.ellipse((65,65,191,191),fill=(17,19,22),outline=(64,68,72),width=6)
        d.ellipse((79,79,177,177),fill=(33,35,37))
        d.arc((81,81,175,175),192,287,fill=(77,81,85),width=3)
    else:
        for y in range(29,228,5):
            for x in range(29+(y//5 % 2)*2,228,5):
                if (x-128)**2+(y-128)**2 < 94**2:
                    d.rectangle((x,y,x+1,y+1),fill=(6,7,9))
    return image


def _stay_cool():
    image = Image.new('RGB',(512,128),(14,16,23))
    d = ImageDraw.Draw(image)
    d.polygon(((10,10),(153,10),(171,21),(342,21),(360,10),(502,10),(502,83),(461,118),(51,118),(10,83)),outline=(89,200,89),width=4)
    d.text((256,66),'Stay Cool!',font=_font(61,True),anchor='mm',fill=(212,54,139),stroke_width=2,stroke_fill=(248,175,218))
    _label(image,(256,35),'This is a great song!',11,(202,210,212))
    for x,c in ((213,(54,127,193)),(243,(198,54,139)),(273,(54,127,193))):
        d.polygon(((x,103),(x+24,103),(x+31,112),(x-6,112)),fill=c)
    return image


def _foot_badge():
    image=Image.new('RGB',(128,128),(32,84,47))
    d=ImageDraw.Draw(image)
    d.rectangle((10,10,118,118),outline=(158,232,148),width=4)
    # Small manufacturer foot-pad pictogram, not character illustration.
    for x,y in ((44,47),(84,79)):
        d.rounded_rectangle((x-10,y-21,x+10,y+17),radius=8,fill=(170,237,145))
        d.rectangle((x-9,y+7,x+9,y+11),fill=(32,84,47))
    return image


def _coin():
    image=_steel((128,128))
    d=ImageDraw.Draw(image)
    d.rectangle((29,21,100,102),fill=(60,64,67),outline=(215,222,223),width=3)
    d.rectangle((47,29,58,78),fill=(8,10,12),outline=(133,139,141),width=2)
    d.rectangle((72,55,91,81),fill=(22,24,27),outline=(154,161,163),width=2)
    _label(image,(64,105),'100',14,(20,23,25),True)
    return image


def _manufacturer():
    image=_steel((256,128))
    d=ImageDraw.Draw(image)
    d.rectangle((20,25,237,79),fill=(178,23,41))
    d.text((128,53),'KONAMI',font=_font(32),anchor='mm',fill=(246,241,233))
    _label(image,(128,101),'DanceDanceRevolution',13,(37,41,44),True)
    return image


def _red_case():
    image=Image.new('RGB',(512,256),(115,8,19))
    d=ImageDraw.Draw(image)
    for y in range(256):
        d.line((0,y,512,y),fill=(119+int(40*math.sin(y/256*math.pi)),8,21))
    for x in range(-128,641,32):
        d.line((x,0,x+128,256),fill=(173,30,46),width=1)
    for y in range(0,256,24):
        d.line((0,y,512,y),fill=(164,25,40),width=1)
    d.ellipse((130,-48,382,304),outline=(206,45,49),width=3)
    for x,tx in ((92,'1P'),(418,'2P')):
        d.text((x,116),tx,font=_font(53,True),anchor='mm',fill=(181,42,49))
    return image


def _controls():
    image=Image.new('RGB',(1024,128),(41,20,25))
    d=ImageDraw.Draw(image)
    d.line((10,20,1013,20),fill=(212,69,51),width=4)
    d.line((10,108,1013,108),fill=(135,27,39),width=3)
    for center in (263,759):
        for x,direction in ((center-83,-1),(center+83,1)):
            d.polygon(((x+direction*18,65),(x-direction*12,45),(x-direction*12,85)),fill=(226,178,48),outline=(68,49,29),width=3)
        d.rounded_rectangle((center-33,45,center+33,84),radius=5,fill=(28,161,144),outline=(178,231,194),width=3)
        _label(image,(center,65),'START',14,(227,250,233),True)
        _label(image,(center,100),'SELECT  /  START',13,(227,208,179),True)
    _label(image,(512,47),'DanceDanceRevolution',17,(208,186,169),True)
    _label(image,(512,74),'SuperNOVA',21,(219,59,57),True)
    return image


def _service():
    image=Image.new('RGB',(256,256),(21,23,27))
    d=ImageDraw.Draw(image)
    d.rectangle((15,15,241,241),outline=(60,65,68),width=2)
    d.rectangle((71,37,185,89),fill=(45,48,49),outline=(128,136,140),width=3)
    d.rectangle((93,48,160,64),fill=(4,7,8))
    _label(image,(128,106),'COIN',16,(179,184,178),True)
    d.rectangle((54,139,200,217),outline=(45,51,56),width=3)
    _screw(d,185,178,7)
    _label(image,(108,238),'KONAMI',13,(95,104,109),True)
    return image


def _warning():
    image=_steel()
    d=ImageDraw.Draw(image)
    d.rectangle((20,26,236,227),fill=(215,218,211),outline=(61,65,68),width=2)
    d.rectangle((22,28,234,72),fill=(239,186,35))
    _label(image,(128,50),'! CAUTION',25,(27,29,26),True)
    for y,line in ((98,'WATCH YOUR STEP'),(122,'PLAY SAFELY'),(151,'DO NOT JUMP'),(179,'KEEP CLEAR')):
        _label(image,(128,y),line,17,(40,45,44),True)
    _label(image,(128,209),'KONAMI',14,(76,79,72),True)
    return image


def _details():
    image=Image.new('RGB',(1024,1024),(17,20,24))
    tiles={'arrow_up':_arrow('up'),'arrow_down':_arrow('down'),
           'arrow_left':_arrow('left',True),'arrow_right':_arrow('right',True),
           'plain_steel':_steel(),'center_diamond':_center(),
           'speaker':_speaker(),'tweeter':_speaker(True),
           'stay_cool':_stay_cool(),'foot_badge':_foot_badge(),
           'coin_slot':_coin(),'manufacturer':_manufacturer(),
           'controls':_controls(),'red_case':_red_case(),
           'service':_service(),'warning':_warning()}
    for name,tile in tiles.items():
        x0,y0,x1,y1=REGIONS[name]
        assert tile.size == (x1-x0,y1-y0), name
        image.paste(tile,(x0,y0))
    return image


def build_textures(textures: Path):
    textures=Path(textures)
    textures.mkdir(parents=True,exist_ok=True)
    _materials().save(textures/'ddr_supernova_materials.png')
    _details().save(textures/'ddr_supernova_details.png')
    return dict(PALETTE),list(KEYS)


if __name__ == '__main__':
    import sys
    build_textures(Path(sys.argv[1]) if len(sys.argv)>1 else
                   Path(__file__).resolve().parents[1]/'build/verification/ddr-textures')
