"""Native BeatStream grille and manufactured trim surfaces, no photo edits."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    'black':(20,22,27), 'ivory':(233,236,238), 'gold':(152,161,170),
    'silver':(157,168,178), 'white_key':(248,251,253), 'black_key':(11,13,17),
    'teal':(25,224,240), 'pink':(241,26,162), 'lavender':(161,153,225),
    'blue':(51,178,238), 'speaker':(18,27,33), 'triangle':(15,28,36),
    'rhythm':(25,28,34), 'vent':(21,24,29), 'red_key':(222,46,92),
    'label':(237,241,244),
}


def build_surface_art(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    atlas=Image.new('RGB',(256,256))
    for i,(name,color) in enumerate(PALETTE.items()):
        tile=Image.new('RGB',(64,64),color)
        d=ImageDraw.Draw(tile)
        if name in ('silver','gold'):
            for x in range(64):
                shift=round(11*math.cos(x/63*math.pi))
                d.line((x,0,x,63),fill=tuple(max(0,min(255,c+shift)) for c in color))
        elif name=='vent':
            for y in range(5,61,4):
                d.line((5,y,58,y),fill=(5,7,9),width=2)
                d.line((5,y+2,58,y+2),fill=(42,47,51))
        atlas.paste(tile,((i%4)*64,(i//4)*64))
    atlas.save(directory/'beatstream_materials.png')

    # Triangular acrylic frame around an actual dark perforated speaker. A full
    # texture is split over native geometry strips, retaining continuous motifs.
    im=Image.new('RGB',(512,512),(15,20,26));d=ImageDraw.Draw(im)
    outer=[(9,8),(499,256),(9,504)]
    d.polygon(outer,fill=(180,199,204))
    d.polygon([(27,35),(460,256),(27,477)],fill=(28,194,211))
    d.polygon([(44,66),(411,256),(44,446)],fill=(159,249,250))
    d.polygon([(59,91),(374,256),(59,421)],fill=(36,95,105))
    d.polygon([(67,105),(348,256),(67,407)],fill=(12,24,29))
    for y in range(112,404,9):
        for x in range(75,346,9):
            if x < 348-abs(y-256)*1.82:
                d.ellipse((x,y,x+3,y+3),fill=(49,65,72))
    for x,y in ((23,34),(455,256),(23,478)):
        d.ellipse((x-4,y-4,x+4,y+4),fill=(66,84,92))
    im.save(directory/'beatstream_speaker.png')

    # Same symmetric53/64-high triangular artwork footprint and UV selection as
    # Nostalgia's centered lower geometry, recolored to cyan illuminated acrylic.
    im=Image.new('RGB',(512,512),(10,27,35));d=ImageDraw.Draw(im)
    d.polygon([(256,40),(32,464),(480,464)],fill=(10,38,50))
    for points,color,width in (([(256,44),(37,460),(475,460)],(115,255,249),4),
                               ([(256,70),(57,448),(455,448)],(19,155,182),4),
                               ([(256,86),(71,439),(441,439)],(62,215,232),2)):
        d.line(points+points[:1],fill=color,width=width)
    cx,cy=256,304
    for radius,width,color in ((123,3,(17,108,139)),(111,3,(66,219,230)),(88,2,(143,250,245)),(76,3,(39,198,218))):
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline=color,width=width)
    for n in range(36):
        a=n*math.tau/36
        x,y=round(cx+129*math.cos(a)),round(cy+129*math.sin(a))
        if abs(x-256)<(y-40)*.50:
            d.rectangle((x-2,y-2,x+2,y+2),fill=(80,220,232))
    for y in range(72,449,28):
        for x in range(55,458,29):
            if abs(x-256)<(y-40)*.48-12 and (x-cx)**2+(y-cy)**2>138**2:
                d.polygon([(x,y),(x+6,y+9),(x-6,y+9)],outline=(89,212,224))
    im.save(directory/'beatstream_triangle.png')

    # Diagonal fractured print is the cabinet's own applied trim. The materials
    # retain black fields rather than Nostalgia's ivory/gold ornamental bands.
    for name,size in (('trim',(512,64)),('side',(128,512))):
        im=Image.new('RGB',size,(21,23,28));d=ImageDraw.Draw(im)
        w,h=size
        for k in range(-h,w+h,20):
            d.line((k,0,k-h,h),fill=(73,78,85),width=5)
            d.line((k+8,0,k+8-h,h),fill=(44,49,57),width=3)
        for y in range(0,h,36):
            for x in range(0,w,48):
                if (x//48+y//36)%3==0:
                    d.polygon([(x,y),(x+33,y),(x+16,y+20)],fill=(20,22,27))
        if name=='side':
            d.rectangle((4,4,w-5,h-5),outline=(99,109,118),width=2)
            for y,color in ((54,(17,221,231)),(103,(242,45,156)),(152,(199,238,34))):
                d.polygon([(35,y),(95,y+28),(35,y+56)],outline=color,width=3)
        else:
            d.line((0,h-2,w,h-2),fill=(102,114,126),width=2)
        im.save(directory/('beatstream_'+name+'.png'))
    im=Image.new('RGB',(512,64),(232,236,238));d=ImageDraw.Draw(im)
    for x,color in ((14,(28,191,214)),(40,(233,26,151)),(66,(143,201,21))):
        d.polygon([(x,18),(x+16,32),(x,46)],fill=color)
    ft=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
    d.text((256,31),'TOUCH THE SCREEN TO PLAY',font=ft,anchor='mm',fill=(58,65,72))
    d.line((6,58,506,58),fill=(139,149,159),width=2)
    im.save(directory/'beatstream_controls.png')
