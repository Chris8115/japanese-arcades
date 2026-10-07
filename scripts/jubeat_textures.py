"""Original utility graphics for the classic blue Jubeat cabinet model."""
import math
import json
import random
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from jubeat_geometry import COLORS

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

def word(draw,xy,text,size,fill='white',bold=False):
    draw.text(xy,text,font=font(size,bold),fill=fill,anchor='mm',stroke_width=0)


def build_pad_frames():
    """A repeatable attract animation with changing positions and LED colors."""
    rng=random.Random(0x4A554245)
    palette=((47,217,244),(244,83,173),(188,223,60),
             (155,96,240),(248,176,45),(71,130,245))
    frames=[]
    for frame in range(24):
        count=rng.randint(3,6)
        lit=dict(zip(rng.sample(range(16),count),rng.sample(palette,count)))
        im=Image.new('RGB',(512,512),'#08131a');d=ImageDraw.Draw(im)
        for row in range(4):
            for col in range(4):
                x,y=col*128,row*128;i=row*4+col
                d.rectangle((x+4,y+4,x+123,y+123),fill='#263642',outline='#789399',width=3)
                d.rectangle((x+10,y+10,x+117,y+117),fill='#36464d',outline='#12212b',width=2)
                if i in lit:
                    color=lit[i]
                    dim=tuple(round(c*.64) for c in color)
                    glow=tuple(round(c+(255-c)*.62) for c in color)
                    highlight=tuple(round(c+(255-c)*.80) for c in color)
                    d.rectangle((x+18,y+18,x+109,y+109),fill=dim,outline=glow,width=3)
                    d.rectangle((x+27,y+27,x+100,y+100),fill=color,outline=highlight,width=2)
                    d.line((x+30,y+62,x+97,y+62),fill=glow,width=3)
                    d.line((x+64,y+29,x+64,y+98),fill=glow,width=3)
                else:
                    d.rectangle((x+24,y+24,x+103,y+103),outline='#60757b',width=3)
                    d.line((x+26,y+29,x+99,y+29),fill='#c0cbd0',width=4)
                d.line((x+12,y+112,x+115,y+112),fill='#a0b5bc',width=2)
        frames.append(im)
    return frames

def build_textures(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    result={}
    def save(name,im):
        path=destination/('jubeat_'+name+'.png');im.save(path);result[name]=path
    im=Image.new('RGB',(256,256));d=ImageDraw.Draw(im)
    for i,color in enumerate(COLORS.values()):
        x,y=(i%4)*64,(i//4)*64;d.rectangle((x,y,x+63,y+63),fill=color)
    save('materials',im)

    # A separate illuminated panel sits inside the glass cube. Keep the
    # outer printed circuitry transparent so the frame and recess are visible.
    im=Image.new('RGB',(768,768));px=im.load()
    for y in range(768):
        for x in range(768):
            halo=max(0,1-math.hypot((x-290)/670,(y-440)/750))
            streak=max(0,1-abs(x+y*.48-445)/260)
            px[x,y]=(int(8+10*halo),int(34+50*halo+14*streak),int(44+67*halo+24*streak))
    d=ImageDraw.Draw(im)
    word(d,(384,463),'jubeat',151,'#e4f8f4')
    d.line((133,550,639,550),fill='#b9e4df',width=3)
    word(d,(384,590),'TOUCH THE MUSIC',24,'#abd6d5')
    save('cube_inner',im)

    im=Image.new('RGBA',(768,768),(169,223,225,9));d=ImageDraw.Draw(im)
    # White/cyan printing floats on the outer glazing; unprinted areas show
    # the inset graphics and internal frame through real fractional alpha.
    for row in range(5):
        for col in range(5):
            x=32+col*155;y=25+row*154
            d.rectangle((x,y,x+112,y+112),outline=(179,239,237,155 if (row+col)%3 else 215),width=5)
            d.rectangle((x+13,y+13,x+93,y+93),outline=(153,219,224,76),width=2)
    for x in (96,302,533,694):d.line((x,0,x+60,768),fill=(181,226,231,58),width=2)
    d.polygon(((0,0),(70,0),(470,768),(428,768)),fill=(220,248,250,12))
    d.line((9,760,9,9,760,9),fill=(223,251,249,116),width=4)
    d.line((17,750,17,17,750,17),fill=(147,215,224,37),width=2)
    save('cube',im)
    top=im.copy();dt=ImageDraw.Draw(top)
    dt.line((0,0,768,768),fill=(198,242,237,65),width=3)
    save('cube_top',top)

    im=Image.new('RGBA',(512,512),(173,220,226,8));d=ImageDraw.Draw(im)
    d.polygon(((0,0),(45,0),(296,512),(273,512)),fill=(230,250,252,11))
    d.line((5,506,5,5,506,5),fill=(230,253,254,112),width=3)
    d.line((505,14,505,505,14,505),fill=(126,204,222,62),width=2)
    save('glass_overlay',im)

    im=Image.new('RGB',(768,768),'#043871');d=ImageDraw.Draw(im)
    for y in range(9,768,12):
        for x in range(9,768,12):
            radius=math.hypot(x-384,y-384)
            c=int(145+70*min(1,radius/450))
            d.ellipse((x-2,y-2,x+2,y+2),fill=(20,c,255))
    for i in range(10):d.rectangle((i*3,i*3,767-i*3,767-i*3),outline=(20,120+i*9,245),width=2)
    d.ellipse((128,125,640,637),fill='#073348',outline='#0ca1d7',width=8)
    word(d,(384,354),'jubeat',130,'#43dcff')
    word(d,(384,457),'FEEL THE BEAT',29,'#60d8f5')
    d.line((160,421,608,421),fill='#42c7e7',width=4)
    save('plaque',im)

    # The lower housing's side windows have a luminous plain logo panel,
    # distinct from the circular graphic behind its front glass.
    im=Image.new('RGB',(512,512));px=im.load()
    for y in range(512):
        for x in range(512):
            halo=max(0,1-math.hypot((x-256)/345,(y-256)/345))
            px[x,y]=(int(28+94*halo),int(89+88*halo),int(111+85*halo))
    d=ImageDraw.Draw(im)
    for y in range(8,512,8):
        for x in range(8,512,8):
            if min(x,y,511-x,511-y)<75:
                d.rectangle((x,y,x+1,y+1),fill='#bfedf0')
    for inset in (4,12,24):d.rectangle((inset,inset,511-inset,511-inset),outline='#a4dce4',width=2)
    word(d,(256,283),'jubeat',105,'#e4fbf8')
    d.line((85,347,427,347),fill='#d3eff1',width=3)
    word(d,(256,375),'TOUCH THE MUSIC',19,'#c8eaf0')
    save('plaque_side',im)

    frames=build_pad_frames()
    im=Image.new('RGB',(512,512*len(frames)))
    for index,frame in enumerate(frames):im.paste(frame,(0,index*512))
    save('pads',im)
    result['pads'].with_suffix('.png.mcmeta').write_text(json.dumps({
        'animation':{'width':512,'height':512,'frametime':6,'interpolate':False}
    },indent=2)+'\n',encoding='utf-8')
    preview=Path(__file__).resolve().parents[1]/'art/jubeat/jubeat-pads-preview.png'
    preview.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(preview)
    im=Image.new('RGB',(1024,128),'#091b37');d=ImageDraw.Draw(im)
    for x in range(0,1024,45):d.line((x,0,x+95,128),fill='#124d77',width=3)
    # The separate silver panel sits ahead of this narrow blue deck strip.
    # Keep it decorative so no lettering is clipped by that physical panel.
    for x in range(16,1024,128):
        d.rectangle((x,23,x+70,93),outline='#2072a0',width=3)
    d.line((0,112,1024,112),fill='#4296bb',width=3)
    save('status',im)

    im=Image.new('RGB',(768,320),'#063567');d=ImageDraw.Draw(im)
    for row in range(3):
        for col in range(8):
            x,y=12+col*103,12+row*104
            d.rectangle((x,y,x+75,y+75),outline='#198abf',width=3)
    for x in range(-100,768,106):d.line((x,0,x+160,320),fill='#1371a5',width=3)
    word(d,(384,159),'jubeat',132,'#efffff')
    d.line((137,235,631,235),fill='#69d8f0',width=3)
    word(d,(384,274),'TOUCH THE MUSIC',21,'#a4e4f4')
    save('neck',im)

    im=Image.new('RGB',(512,512),'#151e26');d=ImageDraw.Draw(im)
    for row in range(4):
        for col in range(4):
            x,y=25+col*120,25+row*120
            d.rectangle((x,y,x+98,y+98),fill='#b7bfc0',outline='#657780',width=5)
            d.rectangle((x+9,y+9,x+89,y+89),outline='#e0e3db',width=2)
    save('side',im)

    im=Image.new('RGB',(512,512),'#13191d');d=ImageDraw.Draw(im)
    for radius,col in ((208,'#253037'),(192,'#111820'),(161,'#202a30'),(128,'#192229'),(94,'#29343a'),(72,'#121a22')):
        d.ellipse((256-radius,256-radius,256+radius,256+radius),fill=col)
    for y in range(12,512,13):
        for x in range(12+(6 if (y//13)%2 else 0),512,13):d.ellipse((x,y,x+5,y+5),fill='#071018')
    d.rectangle((4,4,507,507),outline='#3a494f',width=5)
    save('speaker',im)

    im=Image.new('RGB',(1024,128),'#aab7bb');d=ImageDraw.Draw(im)
    d.rectangle((20,22,265,109),fill='#303b46')
    for i in range(5):d.rectangle((32+i*44,41,65+i*44,67),fill='#267780' if i!=3 else '#7b2228')
    word(d,(455,64),'CARD / COIN',44,'#142330',True)
    word(d,(822,48),'jubeat',59,'#142330')
    word(d,(822,99),'TOUCH & PLAY',18,'#142330')
    save('labels',im)
    im=Image.new('RGB',(256,256),'#127bc0');d=ImageDraw.Draw(im)
    d.rounded_rectangle((12,12,244,244),radius=17,outline='#d3f5ff',width=9)
    d.rounded_rectangle((42,71,164,165),radius=9,outline='#e8ffff',width=7)
    d.line((56,94,150,94),fill='#e8ffff',width=7)
    for r in (24,39,54):d.arc((166-r,128-r,166+r,128+r),-56,56,fill='#e8ffff',width=5)
    word(d,(128,213),'CARD',30,'white',True)
    save('card',im)
    return result
