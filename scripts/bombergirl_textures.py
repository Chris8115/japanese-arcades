"""Reproducible Bombergirl artwork preparation from preserved official sources.

No AI approximation of the character artwork. The exact Konami Rainbow key art
is resized uniformly and surrounded by inexpensive original utility graphics.
Every runtime image is aligned to 16 pixels for four atlas mip levels.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from bombergirl_geometry import COLORS
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/bombergirl';TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'

def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),n)
def text(d,xy,label,size,color,outline=None):d.text(xy,label,font=font(size,True),fill=color,anchor='mm',stroke_width=1 if outline else 0,stroke_fill=outline)

def generate():
    TEX.mkdir(parents=True,exist_ok=True);paths={}
    def save(k,im):
        assert im.width%16==im.height%16==0
        p=TEX/('bombergirl_'+k+'.png');im.save(p,optimize=True);paths[k]=p
    im=Image.new('RGB',(64,64));d=ImageDraw.Draw(im)
    for i,c in enumerate(COLORS.values()):
        x,y=i%4*16,i//4*16;d.rectangle((x,y,x+15,y+15),fill=c)
    save('materials',im)
    art=Image.open(ART/'references/official-title.png').convert('RGBA')
    topper=Image.new('RGBA',(768,544));fit=ImageOps.contain(art,(768,544),Image.Resampling.LANCZOS);topper.alpha_composite(fit,((768-fit.width)//2,(544-fit.height)//2));save('topper',topper)
    back=Image.new('RGBA',topper.size,'#e5e5e3');back.putalpha(ImageOps.mirror(topper.getchannel('A')));save('topper_back',back)
    # The logo is copied from the official high-resolution transparent key art.
    logo=art.crop((233,561,776,674))
    marquee=Image.new('RGB',(768,160),'#f1f2ed');m=ImageOps.contain(logo,(728,152),Image.Resampling.LANCZOS);marquee.paste(m,((768-m.width)//2,(160-m.height)//2),m)
    d=ImageDraw.Draw(marquee)
    for x in (34,734):
        for y in (15,145):d.ellipse((x-2,y-2,x+2,y+2),fill='#555c61')
    save('marquee',marquee)
    # Portrait attract-mode composition preserves every character and logo.
    screen=Image.new('RGB',(384,704),'#eefbfd');d=ImageDraw.Draw(screen)
    for j in range(704):
        c=(int(239-42*j/704),int(250-7*j/704),int(253-1*j/704));d.line((0,j,384,j),fill=c)
    for i,c in enumerate(('#59eee4','#ffe36a','#ed6aa8','#a7a0ef')):
        d.arc((-150+i*21,-50+i*21,550-i*21,650-i*21),0,360,fill=c,width=7)
    # Attract screens feature a large character portrait, rather than another
    # miniature copy of the topper. Keep the original illustration's aspect.
    portrait=art.crop((305,132,693,579))
    m=ImageOps.contain(portrait,(384,435),Image.Resampling.LANCZOS);screen.paste(m,((384-m.width)//2,48),m)
    text(d,(192,37),'KONAMI',17,'#bf1837')
    d.polygon([(30,482),(354,482),(368,502),(354,525),(30,525),(16,502)],fill='#191b29')
    text(d,(192,503),'TOUCH TO START',27,'#fff56e')
    for i,(s,c) in enumerate([('4 vs 4  TEAM BATTLE','#ed2e74'),('BOMB • SKILL • VICTORY','#33aec4')]):
        yy=544+i*59;d.rounded_rectangle((26,yy-20,358,yy+23),radius=6,fill='white',outline=c,width=3);text(d,(192,yy),s,19,c)
    d.rectangle((0,665,384,704),fill='#181d25');text(d,(79,683),'CREDIT  0',14,'white');text(d,(288,683),'e-amusement',14,'white');save('screen',screen)
    # Front service hardware is printed, avoiding dozens of tiny screw meshes.
    im=Image.new('RGB',(256,256),'#e6e9e8');d=ImageDraw.Draw(im)
    d.rectangle((4,4,251,251),outline='#adb7bb',width=2)
    for x,y in ((15,15),(241,15),(15,241),(241,241)):
        d.ellipse((x-2,y-2,x+2,y+2),fill='#737f83');d.line((x-1,y,x+1,y),fill='#e7e9e9')
    for y in (44,129):
        d.rectangle((217,y,235,y+21),fill='#8b979e');d.rectangle((222,y+4,230,y+15),fill='#222a30')
    text(d,(63,22),'KONAMI',9,'#c73245');save('front',im)
    im=Image.new('RGB',(256,256),'#c9cfd0');d=ImageDraw.Draw(im)
    for y in range(24,129,8):d.rounded_rectangle((28,y,228,y+3),radius=1,fill='#3c464c')
    d.rectangle((79,169,182,201),fill='#e9eceb');text(d,(130,181),'KONAMI',9,'#3d474c');text(d,(128,193),'BOMBERGIRL',7,'#3d474c')
    d.rectangle((33,214,63,235),fill='#2f373c');d.rectangle((39,220,56,228),fill='#11191b');save('rear',im)
    im=Image.new('RGB',(256,512),'#171c21');d=ImageDraw.Draw(im)
    d.polygon([(0,0),(256,0),(256,57),(55,362),(0,394)],fill='#e2e7e8')
    d.polygon([(205,80),(224,62),(43,349),(24,361)],fill='#929da6')
    m=ImageOps.contain(logo,(228,60),Image.Resampling.LANCZOS);im.paste(m,(14,415),m);save('side',im)
    # The large top print has contrasting white rails and a dark wristrest.
    im=Image.new('RGB',(512,384),'#161b22');d=ImageDraw.Draw(im)
    d.polygon([(0,0),(512,0),(512,384),(423,384),(385,347),(127,347),(88,384),(0,384)],fill='#dfe4e8')
    d.polygon([(41,0),(471,0),(489,338),(452,360),(411,326),(107,326),(61,360),(23,338)],fill='#1b232b')
    for x in (16,497):
        for y in (20,105,219,332):d.ellipse((x-2,y-2,x+2,y+2),fill='#6a747e')
    for i in range(20):
        d.line((102+i*12,346,86+i*12,370),fill='#252e36',width=2)
    text(d,(255,373),'BOMBERGIRL',17,'#eef6f7');save('deck',im)
    # Main lower LCD: concentric attract-state target and a subtle character.
    im=Image.new('RGB',(512,320),'#ffe9ad');d=ImageDraw.Draw(im)
    for j in range(320):d.line((0,j,512,j),fill=(255,228-int(j*.1),156-int(j*.1)))
    for r in (70,89,96,111,129,151,181):
        d.arc((256-r,160-r,256+r,160+r),15,335,fill='#fffce9' if r%2 else '#f8b957',width=6 if r>100 else 3)
    for a in range(0,360,30):
        r=145;rr=157;t=math.radians(a);d.line((256+r*math.cos(t),160+r*math.sin(t),256+rr*math.cos(t),160+rr*math.sin(t)),fill='#fffbe5',width=3)
    text(d,(256,155),'TOUCH',30,'#fffceb');text(d,(256,186),'TO START',18,'#fffceb');save('touch',im)
    # Utility atlas: reader, coin information, screws and caution notices.
    im=Image.new('RGB',(256,256),'#20252d');d=ImageDraw.Draw(im)
    d.rounded_rectangle((4,4,123,123),radius=8,fill='#eaeeee',outline='#8999a8',width=3)
    d.rounded_rectangle((27,28,102,77),radius=6,outline='#d32a4e',width=3);text(d,(64,47),'e-amusement',10,'#cc315a');text(d,(64,65),'PASS',11,'#31415a');text(d,(64,97),'TOUCH HERE',9,'#395365')
    d.rectangle((136,6,248,42),fill='#e2e6e7');text(d,(192,19),'1 PLAY',10,'#232a33');text(d,(192,33),'100 YEN',10,'#232a33')
    d.rectangle((135,81,246,117),fill='#478c38');text(d,(192,98),'PASELI',13,'white')
    save('details',im)
    im=Image.new('RGB',(256,256),'#252a2f');d=ImageDraw.Draw(im)
    for r in (122,113,102,91):d.ellipse((128-r,128-r,128+r,128+r),outline='#dfe5e7',width=2)
    for a in range(0,360,6):
        t=math.radians(a);d.line((128+94*math.cos(t),128+94*math.sin(t),128+105*math.cos(t),128+105*math.sin(t)),fill='#eeeeed',width=2)
    text(d,(128,23),'PUSH',20,'#f1f1ef');text(d,(128,232),'PUSH',20,'#f1f1ef');save('button',im)
    im=Image.new('RGB',(128,128),'#242b2e');d=ImageDraw.Draw(im)
    for y in range(2,128,4):
        for x in range(2+(y%8)//2,128,4):d.rectangle((x,y,x+1,y+1),fill='#080e12')
    save('speaker',im)
    im=Image.new('RGB',(256,512),'#e9eef0');d=ImageDraw.Draw(im)
    d.line((5,42,61,102,195,102,251,42),fill='#aab8c4',width=5)
    text(d,(125,27),'KONAMI',10,'#b9243b')
    for x in (13,243):
        for y in (130,486):d.ellipse((x-2,y-2,x+2,y+2),fill='#657886')
    d.rectangle((216,48,236,67),fill='#d7bf6c');text(d,(226,58),'1',9,'#384148');save('bezel',im)
    im=Image.new('RGB',(32,256));d=ImageDraw.Draw(im)
    stops=[(0,(47,234,218)),(.32,(161,245,217)),(.50,(255,238,146)),(.66,(255,158,141)),(1,(229,92,244))]
    for y in range(256):
        t=y/255
        for (a,A),(b,B) in zip(stops,stops[1:]):
            if a<=t<=b:
                f=(t-a)/(b-a);c=tuple(round(A[i]*(1-f)+B[i]*f) for i in range(3));d.line((0,y,32,y),fill=c);break
    save('lights',im)
    return paths
