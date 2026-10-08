"""Printed utility panels for the Sunny Park widescreen cabinet.

Fine speaker perforations, decals, and screw heads remain texture detail.
Generated illustration is preserved separately; runtime copies are atlas-sized.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from popn_music_geometry import COLORS

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/popn_music'
TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

def text(d,xy,label,size,fill,bold=True,outline=None):
    d.text(xy,label,font=font(size,bold),fill=fill,anchor='mm',stroke_width=max(1,size//24) if outline else 0,stroke_fill=outline)

def popkun(d,cx,cy,r,color):
    d.ellipse((cx-r*1.2,cy-r*1.2,cx+r*1.2,cy+r*1.2),fill='#ffd237',outline='#ec7853',width=max(2,int(r*.035)))
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#f6eed1')
    d.ellipse((cx-r*.88,cy-r*.88,cx+r*.88,cy+r*.88),fill=color,outline='white',width=max(2,int(r*.055)))
    for x in (cx-r*.33,cx+r*.33):
        d.ellipse((x-r*.16,cy-r*.65,x+r*.16,cy-r*.19),fill='#fffce2')
        d.ellipse((x-r*.07,cy-r*.52,x+r*.07,cy-r*.27),fill='#242c3b')
    d.rectangle((cx-r*.83,cy-r*.05,cx+r*.83,cy+r*.13),fill='#f6eed1')
    d.line((cx-r*.66,cy+r*.025,cx+r*.66,cy+r*.025),fill='#969ba0',width=max(1,int(r*.018)))
    d.arc((cx-r*.66,cy-r*.10,cx+r*.66,cy+r*.59),0,180,fill='#b53322',width=max(1,int(r*.07)))

def generate():
    TEX.mkdir(parents=True,exist_ok=True); result={}
    def save(key,im):
        path=TEX/('popn_music_'+key+'.png');im.save(path);result[key]=path
    im=Image.new('RGB',(256,256));d=ImageDraw.Draw(im)
    for i,color in enumerate(COLORS.values()):
        x,y=(i%4)*64,(i//4)*64;d.rectangle((x,y,x+63,y+63),fill=color)
    save('materials',im)

    # Keep the complete illustration, including the title and both mascots.
    source=Image.open(ART/'sunny-park-artwork-source.png').convert('RGB')
    save('marquee',source.resize((1024,512),Image.Resampling.LANCZOS))
    screen=Image.new('RGB',(1024,576),'#37c1ed')
    screen.paste(source.resize((1024,512),Image.Resampling.LANCZOS),(0,0))
    d=ImageDraw.Draw(screen)
    d.rectangle((0,512,1024,576),fill='#d3f78c')
    text(d,(512,537),'PRESS THE RED BUTTON',27,'#dc3427',outline='white')
    text(d,(90,559),'KONAMI',12,'#2b7453')
    text(d,(920,559),'CREDIT  0',12,'#2b7453')
    save('screen',screen)

    console=Image.new('RGB',(1024,512),'#f7f6e7');d=ImageDraw.Draw(console)
    for color,inset in (('#12b9da',0),('#ffcc23',16),('#f15c25',30)):
        d.rounded_rectangle((inset,inset,1023-inset,511-inset),radius=110-inset,outline=color,width=9)
    for i,col in enumerate(('#42b6c5','#8dd975','#ffee76')):
        d.arc((65+i*20,140+i*14,980-i*20,700-i*14),180,355,fill=col,width=9)
    # Small printed instructions stay behind the nine physical raised keys.
    text(d,(690,40),'9 BUTTONS · LET’S ENJOY MUSIC!',17,'#df6216')
    text(d,(512,474),"pop'n music",37,'#f7fbe5',outline='#e64121')
    for x,y,r,color in ((68,78,27,'#ffde28'),(949,381,23,'#3ac7ed'),(136,421,16,'#73c547')):
        d.ellipse((x-r,y-r,x+r,y+r),fill=color)
    save('console',console)

    edge=Image.new('RGB',(1024,128),'#f5f2e7');d=ImageDraw.Draw(edge)
    d.polygon(((0,6),(770,6),(1024,68),(1024,110),(230,110),(0,53)),fill='#f69623')
    d.polygon(((0,74),(230,121),(820,121),(1024,95),(1024,126),(0,126)),fill='#52c6df')
    text(d,(512,64),"pop'n music",66,'white',outline='#dd4928')
    save('console_edge',edge)

    bezel=Image.new('RGB',(1024,1024),'#ffcd3e');d=ImageDraw.Draw(bezel)
    d.polygon(((0,0),(196,0),(400,1024),(0,1024)),fill='#88d4e1')
    d.polygon(((0,340),(140,180),(160,630),(0,760)),fill='#b2e3e5')
    d.polygon(((0,770),(260,800),(530,1024),(0,1024)),fill='#d6eae2')
    for x,y in ((50,113),(940,88),(968,847),(165,945)):
        d.ellipse((x-29,y-29,x+29,y+29),fill='#fff4a5')
        for dx,dy in ((-33,0),(33,0),(0,-33),(0,33)):
            d.ellipse((x+dx-17,y+dy-17,x+dx+17,y+dy+17),fill='#fffce7')
    for x,y,col in ((916,93,'#f3862e'),(983,121,'#48b9dd')):
        d.ellipse((x-31,y-31,x+31,y+31),fill=col,outline='white',width=4)
    text(d,(530,55),"pop'n music",38,'#fffde0',outline='#ee9731')
    d.rounded_rectangle((448,889,933,982),radius=17,fill='#ffad30',outline='#fff4a4',width=5)
    text(d,(690,916),'LET’S ENJOY MUSIC!',22,'#e16929')
    for i,col in enumerate(('#fcf9ec','#fbdc28','#23c874','#1692e8','#ee3a48','#1692e8','#23c874','#fbdc28','#fcf9ec')):
        x=510+i*44;d.ellipse((x,941,x+26,967),fill=col,outline='#725c44',width=2)
    save('bezel',bezel)

    side=Image.new('RGB',(512,1024),'#f6f6ed');d=ImageDraw.Draw(side)
    d.polygon(((0,0),(512,0),(512,1024),(400,1024),(0,330)),fill='#13bde2')
    for cy,col,mark in ((210,'#f4c323','♪'),(450,'#7ccb40','M'),(815,'#0874c5','♪'),(980,'#ef382b','♪')):
        d.ellipse((282,cy-74,444,cy+88),fill=col,outline='white',width=9)
        text(d,(363,cy+3),mark,78,'white')
    # Manufacture-style bold side lettering, against broad cyan and white fields.
    text(d,(214,603),"pop'n",83,'#ffbc18',outline='#b64c1c')
    text(d,(205,688),'music',83,'#ffbc18',outline='#b64c1c')
    text(d,(130,821),'LET’S',31,'#238a7f')
    text(d,(131,862),'ENJOY MUSIC',21,'#238a7f')
    save('side',side)

    front=Image.new('RGB',(512,512),'#f0f1ee');d=ImageDraw.Draw(front)
    d.rounded_rectangle((9,9,502,502),radius=6,outline='#d4d9d5',width=2)
    popkun(d,292,266,101,'#ff4d27')
    d.ellipse((175,204,227,249),fill='#7bc4dd',outline='white',width=3)
    text(d,(201,226),"pop'n",13,'#437779')
    for x in (25,487):
        for y in (25,487):
            d.ellipse((x-3,y-3,x+3,y+3),fill='#9caaa9')
            d.line((x-2,y,x+2,y),fill='#edf1ee',width=1)
    save('front',front)

    speaker=Image.new('RGB',(256,256),'#1a2023');d=ImageDraw.Draw(speaker)
    for r,color in ((123,'#393d3e'),(118,'#0b1013'),(107,'#313538'),(81,'#22282b'),(39,'#151b20')):
        d.ellipse((128-r,128-r,128+r,128+r),fill=color)
    for y in range(7,250,6):
        for x in range(7+(3 if y%12 else 0),250,6):
            if (x-128)**2+(y-128)**2<113**2:
                d.ellipse((x,y,x+2,y+2),fill='#080d11')
    d.arc((23,23,233,233),202,320,fill='#555c5d',width=3)
    save('speaker',speaker)

    rainbow=Image.new('RGB',(512,32));d=ImageDraw.Draw(rainbow)
    for i,color in enumerate(('#f3ece3','#f9d32c','#66d851','#ee363d','#2e99e4','#ac51d7','#ffe89d','#62d1e3','#f1eae0')):
        x0=round(i*512/9);x1=round((i+1)*512/9)
        d.rectangle((x0,0,x1,31),fill=color)
        d.line((x0,0,x0,31),fill='#faf6f0',width=2)
        d.rectangle((x0+5,4,x1-5,9),fill='#fff8e2')
    save('rainbow',rainbow)

    details=Image.new('RGB',(1024,1024),'#eef1ed');d=ImageDraw.Draw(details)
    # TL: speaker-center edition plate; TR: reader face.
    details.paste(source.resize((512,512),Image.Resampling.LANCZOS),(0,0))
    d.rounded_rectangle((521,9,1014,502),radius=20,fill='#1c242a',outline='#aebbc0',width=8)
    d.rounded_rectangle((550,35,985,218),radius=12,fill='#f1ebe3',outline='#7c8788',width=5)
    text(d,(768,90),'e-amusement',36,'#d83d4f')
    text(d,(768,147),'PASS',35,'#536477')
    for row in range(3):
        for col in range(3):
            x,y=594+col*94,255+row*67
            d.rounded_rectangle((x,y,x+69,y+49),radius=6,fill='#7b8a93',outline='#d0dadf',width=2)
            text(d,(x+34,y+24),str(row*3+col+1),23,'#fffde7')
    # BL: black/red semicircular decorative tweeter panel.
    d.rectangle((0,512,511,1023),fill='#252231')
    for r in range(60,260,24):
        d.arc((256-r,790-r,256+r,790+r),185,355,fill='#d35b9b' if r%48 else '#8267b9',width=8)
    for x in range(12,512,15):d.line((x,590,x,969),fill='#473645',width=2)
    text(d,(256,895),"pop'n music",39,'#f3d6ed')
    # BR: narrow coin panel, real machine has its own black service fascia.
    d.rectangle((512,512,1023,1023),fill='#343b3b')
    d.rectangle((663,550,878,691),fill='#879797')
    d.rectangle((693,574,849,665),fill='#f46729')
    d.rectangle((744,587,799,650),fill='#1d282c')
    d.rectangle((692,758,848,855),fill='#aeb6b7')
    d.rectangle((719,784,822,832),fill='#141b21')
    d.ellipse((757,928,790,961),fill='#dce1df')
    d.line((773,934,773,955),fill='#293238',width=3)
    for x in (535,1000):
        for y in (532,1004):d.ellipse((x-4,y-4,x+4,y+4),fill='#b4c0c0')
    save('details',details)
    return result
