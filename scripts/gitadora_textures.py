"""Compact original printed panels based on the official OverDrive cabinet livery.

No photograph is pasted onto a surface. Screens are original static title-card
interpretations; all grilles, ribs, small labels and silver waves are texture detail.
"""
from pathlib import Path
import math
from PIL import Image,ImageDraw,ImageFont
from gitadora_geometry import COLORS

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'

def font(size,bold=True):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)
def text(d,xy,s,size,color='white',stroke=0,outline='black'):
    d.text(xy,s,font=font(size),fill=color,anchor='mm',stroke_width=stroke,stroke_fill=outline)

def logo(d,box,subtitle=True):
    x,y,w,h=box
    text(d,(x+w/2,y+h*.36),'GITADORA',int(w*.156),'#d5ec3d',max(2,int(w*.008)),'#172025')
    if subtitle:
        text(d,(x+w*.51,y+h*.69),'OverDrive',int(w*.124),'#fcfff5',max(2,int(w*.008)),'#172025')
        d.line((x+w*.28,y+h*.88,x+w*.74,y+h*.80),fill='#ed42a0',width=max(2,int(w*.011)))

def waves(im):
    d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((0,0,w-1,h-1),fill='#edeeeb')
    for j,(offset,col) in enumerate(((.19,'#bcc4c7'),(.23,'#e6e9e7'),(.28,'#919ca2'),(.32,'#e7ecec'))):
        upper=[(x,h*(offset+.13*math.sin(x/w*math.tau+.8))) for x in range(0,w+1,3)]
        lower=[(x,y+h*.055) for x,y in reversed(upper)]
        d.polygon(upper+lower,fill=col)
    for offset,col in ((.81,'#c0c7c9'),(.85,'#aeb9bd'),(.9,'#d4dadd')):
        line=[(x,h*(offset+.09*math.sin(x/w*math.tau-1))) for x in range(0,w+1,3)]
        d.line(line,fill=col,width=max(2,int(h*.022)))
    return d

def generate():
    TEX.mkdir(parents=True,exist_ok=True);paths={}
    def save(key,im):
        path=TEX/f'gitadora_{key}.png';im.save(path,optimize=True);paths[key]=path
    im=Image.new('RGB',(128,128));d=ImageDraw.Draw(im)
    for i,c in enumerate(COLORS.values()):d.rectangle(((i%4)*32,(i//4)*32,(i%4)*32+31,(i//4)*32+31),fill=c)
    save('materials',im)
    im=Image.new('RGB',(512,256));d=waves(im)
    d.rectangle((5,5,506,250),outline='#bcc0c1',width=4)
    text(d,(54,21),'KONAMI',17,'#c72c40')
    logo(d,(25,56,462,164),False)
    text(d,(256,230),'GuitarFreaks  &  DrumMania',18,'#526164')
    save('marquee',im)
    for kind,label in (('guitarfreaks','GuitarFreaks'),('drummania','DrumMania')):
        im=Image.new('RGB',(512,288));pix=im.load()
        for y in range(288):
            for x in range(512):
                glow=max(0,1-math.hypot((x-245)/330,(y-145)/235))
                pix[x,y]=(int(188+50*glow),int(29+43*glow),int(91+67*glow))
        d=ImageDraw.Draw(im)
        for i in range(11):
            x=i*55-110
            d.polygon(((x,288),(x+18,288),(x+250,0),(x+231,0)),fill='#e9559f')
        for x,y,r in ((70,68,36),(421,113,52),(339,257,32)):
            d.ellipse((x-r,y-r,x+r,y+r),outline='#f7b2d2',width=2)
            for angle in range(0,360,30):
                a=math.radians(angle);d.line((x+(r-8)*math.cos(a),y+(r-8)*math.sin(a),x+(r+8)*math.cos(a),y+(r+8)*math.sin(a)),fill='#f7b2d2',width=3)
        text(d,(53,18),'KONAMI',18,'#ffffff')
        text(d,(470,18),'BEMANI',12,'#ffffff')
        logo(d,(40,49,430,150))
        text(d,(256,214),label,26,'#ffffff',1,'#861049')
        text(d,(256,248),'LET’S START A SESSION!',16,'#fffdc5')
        d.rectangle((0,270,512,288),fill='#9c1749')
        text(d,(75,278),'e-amusement',10,'#fff8e1');text(d,(442,278),'CREDIT  0',11,'#fff8e1')
        save('screen_'+kind,im)
    im=Image.new('RGB',(256,256));waves(im);save('front',im)
    im=Image.new('RGB',(128,512));d=waves(im)
    d.rectangle((7,75,120,251),fill='#282d31')
    text(d,(64,145),'GITADORA',18,'#d7e748');text(d,(64,174),'OverDrive',17,'#ffffff')
    save('side',im)
    im=Image.new('RGB',(512,96));d=waves(im)
    d.line((0,9,511,9),fill='#c7cfd2',width=3);d.line((0,88,511,88),fill='#acb7bc',width=3)
    save('bridge',im)
    im=Image.new('RGB',(256,32),'#edefeb');d=ImageDraw.Draw(im);text(d,(128,16),'GITADORA',22,'#303a41');save('title',im)
    im=Image.new('RGB',(128,128),'#0c1115');d=ImageDraw.Draw(im)
    for r,c in ((61,'#484d50'),(58,'#121619'),(45,'#232a2e'),(22,'#181e22')):d.ellipse((64-r,64-r,64+r,64+r),fill=c)
    for y in range(3,126,4):
        for x in range(3+(2 if y%8 else 0),126,4):
            if (x-64)**2+(y-64)**2<57**2:d.rectangle((x,y,x+1,y+1),fill='#060b0f')
    save('speaker',im)
    im=Image.new('RGB',(128,128),'#42454a');d=ImageDraw.Draw(im)
    for r in (57,54,51):d.ellipse((64-r,64-r,64+r,64+r),outline='#51565b',width=1)
    for y in range(5,126,4):
        for x in range(5,126,4):d.point((x,y),fill='#3c4044')
    text(d,(64,64),'KONAMI',10,'#61676b');save('pad',im)
    im=Image.new('RGB',(128,256),'#141a20');d=ImageDraw.Draw(im)
    d.rectangle((6,6,121,249),outline='#69767e',width=2)
    d.rectangle((43,37,88,72),fill='#b9c3c8');d.rectangle((48,43,83,49),fill='#1b2429')
    text(d,(65,85),'INSERT COIN',11,'#dce3e4')
    d.rectangle((42,113,87,149),fill='#969ea4');d.rectangle((46,117,83,144),fill='#29343b')
    for y in (16,238):
        for x in (17,110):d.ellipse((x-2,y-2,x+2,y+2),fill='#939ea5')
    d.ellipse((59,191,71,203),fill='#a7b1b7');d.line((65,194,65,200),fill='#26323c',width=2)
    save('service',im)
    im=Image.new('RGB',(256,256),'#222a31');d=ImageDraw.Draw(im)
    d.rounded_rectangle((17,15,237,128),radius=6,fill='#dbe2df',outline='#8c999e',width=5)
    text(d,(128,45),'e-amusement',23,'#c54e62');text(d,(128,82),'PASS',25,'#4e5b63')
    d.rectangle((63,104,193,114),fill='#1b232b')
    for j in range(3):
        for i in range(3):
            x,y=162+i*24,149+j*24;d.rectangle((x,y,x+18,y+17),fill='#ccd1cf');text(d,(x+9,y+8),str(j*3+i+1),10,'#27313a')
    text(d,(75,152),'SELECT',13,'#ffffff');text(d,(75,176),'DECIDE',13,'#ffffff')
    text(d,(128,237),'PASELI ACCEPTED',12,'#aaddc2');save('reader',im)
    im=Image.new('RGB',(128,256),'#dce1df');d=ImageDraw.Draw(im)
    for y in range(19,128,7):d.rectangle((15,y,112,y+3),fill='#4b565d')
    d.rectangle((15,164,111,233),fill='#abb5b7');text(d,(64,180),'KONAMI',14,'#38454d');text(d,(64,201),'GITADORA',11,'#38454d');text(d,(64,221),'AC 100 V',10,'#38454d');save('rear',im)
    im=Image.new('RGB',(64,128),'#242b30');d=ImageDraw.Draw(im)
    d.rectangle((3,3,60,124),outline='#aeb9bc',width=4)
    for y in range(13,119,11):d.line((10,y,54,y),fill='#7d8b91',width=4)
    text(d,(32,108),'K',13,'#d4dcdd');save('pedal',im)
    return paths
