"""Deterministic MUSIC DIVER circuit, logo, and attract UI textures.

All artwork is drawn from geometric primitives and type; no other cabinet's
art or photographs are embedded. Physical rings and strike pads are geometry.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'
COLORS={'black':'#15141c','dark':'#272632','rubber':'#080a11','steel':'#535560',
        'silver':'#b7bac5','white':'#e9e9ef','edge':'#9396a3','pink':'#f127c2',
        'violet':'#911fee','cyan':'#41d9e8','cream':'#d2d4df','purple':'#59139b',
        'grille':'#1d1f28','blue':'#246ac0','red':'#c93652','chrome':'#dfe6e9'}

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

def logo(draw,center,size,color):
    """Angular MD monogram with the small word marks in its open right side."""
    cx,cy=center;s=size/256
    def poly(points):draw.polygon([(cx+(x-128)*s,cy+(y-128)*s) for x,y in points],fill=color)
    poly([(24,121),(43,75),(91,37),(89,96),(71,106),(72,72),(40,107)])
    poly([(99,34),(136,32),(136,119),(116,119),(116,58),(99,71)])
    poly([(76,144),(97,144),(97,219),(76,205)])
    poly([(108,144),(163,144),(193,169),(156,202),(110,215),(110,193),(151,183),(166,170),(151,163),(108,163)])
    draw.text((cx+48*s,cy-8*s),'USIC',font=font(max(8,round(23*s)),True),anchor='mm',fill=color)
    draw.text((cx+91*s,cy+51*s),'IVER',font=font(max(8,round(23*s)),True),anchor='mm',fill=color)

def generate():
    TEX.mkdir(parents=True,exist_ok=True)
    atlas=Image.new('RGB',(256,256));d=ImageDraw.Draw(atlas)
    for i,color in enumerate(COLORS.values()):
        x,y=i%4*64,i//4*64;d.rectangle((x,y,x+63,y+63),fill=color)
    atlas.save(TEX/'music_diver_materials.png')

    circuit=Image.new('RGB',(1024,1024),'#ec288e');d=ImageDraw.Draw(circuit)
    for row in range(16):
        for col in range(10):
            x=col*104+(row%2)*39;y=row*67
            d.line([(x,y+8),(x+65,y+8),(x+80,y+23),(x+80,y+48),(x+18,y+48)],fill='#ff98d9',width=5)
            d.line([(x+8,y+15),(x+8,y+34),(x+50,y+34)],fill='#ffd0ed',width=3)
            for xx in (x+24,x+38,x+51):d.rectangle((xx,y+15,xx+4,y+24),fill='#ffabd9')
    d.text((512,120),'MUSIC DIVER',anchor='mm',font=font(88,True),fill='#fff1fa')
    d.text((512,887),'DIVE INTO THE MUSIC',anchor='mm',font=font(45,True),fill='#ffc5ee')
    circuit.save(TEX/'music_diver_circuit.png')

    # One radial luminous circuit image maps continuously over the four
    # separate acrylic marquee windows; its centre is a separate logo disc.
    marquee=Image.new('RGB',(1024,1024),'#6711b9');d=ImageDraw.Draw(marquee)
    for r in (236,247,270,297,320,348,369,399,430,449,468,486):
        d.ellipse((512-r,512-r,512+r,512+r),outline='#e640fb' if r%2 else '#b627ed',width=5 if r%2 else 9)
    for i in range(160):
        a=math.tau*i/160;r1=300 if i%3 else 326;r2=358 if i%3 else 394
        c,s=math.cos(a),math.sin(a)
        d.line((512+c*r1,512+s*r1,512+c*r2,512+s*r2),fill='#da46f0',width=4)
        if i%4==0:d.line((512+c*419,512+s*419,512+c*475,512+s*475),fill='#fa75ff',width=6)
    for i in range(32):
        a=math.tau*i/32;d.arc((44,44,980,980),math.degrees(a),math.degrees(a)+7,fill='#ff8aff',width=8)
    marquee.save(TEX/'music_diver_marquee.png')
    center=Image.new('RGB',(512,512),'#e122ea');d=ImageDraw.Draw(center)
    d.ellipse((12,12,500,500),outline='#34e7ed',width=13)
    logo(d,(256,228),393,'#a137d5')
    # Full words stay legible on the six-model-unit physical centre disc;
    # the larger angular monogram remains visible behind them.
    d.text((256,206),'MUSIC',font=font(78,True),anchor='mm',fill='#353276',stroke_width=1)
    d.text((256,296),'DIVER',font=font(78,True),anchor='mm',fill='#353276',stroke_width=1)
    d.text((256,453),'TAITO',font=font(20,True),anchor='mm',fill='#684d9e')
    center.save(TEX/'music_diver_logo.png')

    screen=Image.new('RGB',(1024,1024),'#0b1024');d=ImageDraw.Draw(screen)
    for y in range(0,1024,32):d.line((0,y,1024,y),fill='#131a32',width=1)
    for x in range(0,1024,32):d.line((x,0,x,1024),fill='#131a32',width=1)
    for radius in (360,376,425,438):d.ellipse((512-radius,512-radius,512+radius,512+radius),outline='#6389c0' if radius%2 else '#352d65',width=3)
    for a in (45,135,225,315):
        aa=math.radians(a);d.line((512,512,512+500*math.cos(aa),512+500*math.sin(aa)),fill='#265d7d',width=2)
    for i in range(38):
        a=math.tau*i/38;r=426
        d.line((512+math.cos(a)*r,512+math.sin(a)*r,512+math.cos(a)*(r+15),512+math.sin(a)*(r+15)),fill='#3fd7e1',width=2)
    logo(d,(512,342),376,'#35e7ec')
    for i in range(4):
        cy=590+i*56;x=320+i*21
        d.polygon([(x,cy),(x+265,cy),(x+243,cy+33),(x-22,cy+33)],fill=('#692684','#113b69','#484591','#253c6e')[i])
        d.line((x,cy,x+265,cy),fill='#e747d8',width=4)
    d.text((512,596),'DIVE INTO THE MUSIC!',anchor='mm',font=font(27,True),fill='#f8d4fb')
    d.text((512,812),'TOUCH TO START',anchor='mm',font=font(30,True),fill='#a7bff5')
    screen.save(TEX/'music_diver_display.png')

    status=Image.new('RGB',(1024,256),'#101225');d=ImageDraw.Draw(status)
    d.rectangle((4,4,1019,251),outline='#da54ee',width=5)
    d.text((38,36),'MUSIC DIVER',font=font(41,True),fill='#a7e7ff')
    d.text((954,47),'STAGE 01',anchor='ra',font=font(36,True),fill='#d082e5')
    for y in (110,157,204):
        d.rectangle((25,y,522,y+26),outline='#5ca0f2',width=3)
        d.rectangle((35,y+8,392+(y%20)*4,y+18),fill='#542f80')
    d.text((769,146),'DIVE!',anchor='mm',font=font(64,True),fill='#f348d1')
    d.text((776,212),'RHYTHM  /  ACTION',anchor='mm',font=font(20),fill='#84cbe6')
    status.save(TEX/'music_diver_status.png')

    # Black triangle side print is physically a triangle; the rectangular
    # lettering texture is mapped along its steep diagonal axis.
    side=Image.new('RGB',(256,1024),'#12131a');d=ImageDraw.Draw(side)
    label=Image.new('RGB',(1000,170),'#12131a');ld=ImageDraw.Draw(label)
    ld.text((500,85),'MUSIC DIVER',anchor='mm',font=font(122,True),fill='#e8e9f1')
    side.paste(label.rotate(90,expand=True),(43,12))
    side.save(TEX/'music_diver_side.png')

    details=Image.new('RGB',(1024,1024),'#202129');d=ImageDraw.Draw(details)
    for y in range(4,508,8):
        for x in range(4+(y//8%2)*4,508,8):d.ellipse((x,y,x+2,y+2),fill='#474753')
    d.ellipse((94,94,418,418),outline='#2d2e37',width=14)
    d.ellipse((211,211,301,301),outline='#262735',width=10)
    d.rectangle((512,0,1023,511),fill='#090e19')
    for y in (77,444):d.line((527,y,1007,y),fill='#b1a5c0',width=5)
    d.line([(541,371),(629,121),(737,382),(553,239),(731,240)],fill='#ccd1d9',width=9)
    d.rectangle((778,189,995,343),fill='#2dd5e9',outline='#6873aa',width=10)
    d.text((886,236),'NESiCA',anchor='mm',font=font(26,True),fill='#135282')
    d.text((886,293),'TOUCH',anchor='mm',font=font(21),fill='#126598')
    d.rectangle((0,512,511,1023),fill='#dcdee5')
    for y in range(563,966,27):d.line((48,y,465,y),fill='#858894',width=8)
    d.rectangle((512,512,1023,1023),fill='#f0edf0')
    d.rectangle((559,563,976,648),fill='#bf376c')
    d.text((768,605),'MUSIC DIVER',anchor='mm',font=font(33,True),fill='#fff1f7')
    for y in (709,744,779,814,849,884):d.line((572,y,963,y),fill='#767886',width=4)
    details.save(TEX/'music_diver_details.png')
    return COLORS

if __name__=='__main__':generate()
