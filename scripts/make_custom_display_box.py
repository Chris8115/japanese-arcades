"""Generate only the Custom Display Box shell, print, and matching bitmap font.

The original six mob collectibles are deliberately not regenerated or edited.
Run: py scripts/make_custom_display_box.py

The shell contains 43 static faces, including five cutout accent masks using
tintindex 0. All navy, pale lettering, and cardboard faces stay untinted. The
item uses builtin/entity; its custom renderer must draw this shell block model.
"""
import base64
import copy
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

# Shared pure drawing/export helpers; importing does not regenerate mob assets.
from make_mob_figures import font, lettering, meshes, write

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
ART = ROOT / 'art/custom_display_box'
TEXTURE = ASSETS / 'textures/block/custom_display_box_package.png'
NAME = 'custom_display_box'
NAVY = '#182332'
PAPER = '#e9ede5'
WHITE = '#f7f7ec'
PANELS = {'front': (0, 0, 320, 448), 'back': (320, 0, 640, 448),
          'left': (640, 0, 896, 448), 'right': (0, 448, 256, 896),
          'top': (256, 448, 576, 704), 'bottom': (576, 448, 896, 704),
          'inner': (256, 704, 576, 960)}
DISPLAY = {
    'gui': {'rotation': [14,205,0], 'translation': [0,0,0], 'scale': [1,1,1]},
    'ground': {'translation': [0,2,0], 'scale': [.5,.5,.5]},
    'fixed': {'rotation': [0,180,0], 'scale': [.8,.8,.8]},
    'thirdperson_righthand': {'rotation': [75,45,0], 'translation': [0,2.5,0], 'scale': [.4,.4,.4]},
    'firstperson_righthand': {'rotation': [0,45,0], 'translation': [0,1,0], 'scale': [.55,.55,.55]}}


def package_texture():
    """Top half is untinted print; bottom half is matching white accent masks."""
    base = Image.new('RGBA', (1024,1024), (0,0,0,0))
    tint = Image.new('RGBA', (1024,1024), (0,0,0,0))
    d, t = ImageDraw.Draw(base), ImageDraw.Draw(tint)
    transparent = (0,0,0,0)
    for x0,y0,x1,y1 in PANELS.values():
        d.rectangle((x0,y0,x1-1,y1-1), fill=PAPER)

    d.rectangle((0,0,319,447), fill=NAVY)
    t.rectangle((10,10,309,437), outline='white', width=3)
    d.rectangle((24,68,295,385), fill=transparent)
    d.rectangle((21,65,298,388), outline=PAPER, width=3)
    t.rectangle((24,369,295,385), fill='white')
    lettering(d,'CUSTOM COLLECTION',(160,28),23,PAPER,284)
    lettering(d,'ARCADE PRIZE  /  DISPLAY SERIES',(160,50),11,PAPER,285)
    # Leave y=0.43..1.48 model units blank for the renderer's item-name label.
    # Opaque glints with transparent surroundings avoid a translucent front slab.
    d.line([(38,126),(66,87)],fill='#dce9e7',width=3)
    d.line([(39,146),(81,87)],fill='#aebfc5',width=2)
    d.line([(276,340),(262,360)],fill='#dce9e7',width=2)

    x=320
    d.rectangle((x,0,x+319,76),fill=NAVY)
    lettering(d,'CUSTOM COLLECTION',(x+160,29),24,PAPER,290)
    lettering(d,'YOUR PERSONAL DISPLAY SERIES',(x+160,55),12,PAPER)
    t.rectangle((x+22,100,x+297,248),fill='white')
    # The circular inset and lettering remain their original ink color.
    t.ellipse((x+87,111,x+233,237),fill=transparent)
    d.ellipse((x+87,111,x+233,237),fill=NAVY)
    lettering(d,'YOU',(x+160,162),38,PAPER)
    lettering(d,'CURATE IT',(x+160,196),15,PAPER)
    lettering(d,'A COLLECTION OF YOUR OWN',(x+160,273),15,NAVY,285)
    lettering(d,'COLLECT  /  DISPLAY',(x+160,320),23,NAVY,285)
    lettering(d,'FUN PACK ARCADE',(x+118,404),13,NAVY)
    lettering(d,'CUSTOM DISPLAY SERIES',(x+118,425),10,NAVY)
    for i in range(26):
        xx=x+224+i*2
        d.rectangle((xx,391,xx+(i%3==0),427-(i%4)*2),fill=NAVY)

    for side in ('left','right'):
        x0,y0,x1,y1=PANELS[side]
        d.rectangle((x0,y0,x1-1,y1-1),fill=PAPER)
        t.rectangle((x0,y0,x1-1,y1-1),fill='white')
        for k in range(7):
            yy=y0+105+k*38
            t.line((x0+17,yy,x1-18,yy),fill=transparent,width=1)
        for text,yy,size,width in [('CUSTOM',y0+42,38,228),('COLLECTION',y0+79,24,228),
                                   ('DISPLAY',y0+219,36,220),('ARCADE PRIZE',y0+421,15,228)]:
            lettering(d,text,((x0+x1)/2,yy),size,NAVY,width)
            lettering(t,text,((x0+x1)/2,yy),size,transparent,width)
        d.rectangle((x0+15,y0+328,x1-16,y0+386),fill=NAVY)
        t.rectangle((x0+15,y0+328,x1-16,y0+386),fill=transparent)
        lettering(d,'YOUR COLLECTION',((x0+x1)/2,y0+357),23,PAPER,207)

    for side in ('top','bottom'):
        x0,y0,x1,y1=PANELS[side]
        d.rectangle((x0,y0,x1-1,y1-1),fill=NAVY)
        border=t if side=='top' else d
        border.rectangle((x0+10,y0+10,x1-11,y1-11),outline='white',width=3)
        lettering(d,'CUSTOM COLLECTION',((x0+x1)/2,y0+91),25,PAPER,290)
        lettering(d,'YOUR PERSONAL DISPLAY',((x0+x1)/2,y0+139),18,PAPER,288)
        lettering(d,'FUN PACK ARCADE',((x0+x1)/2,y0+185),13,PAPER)

    x0,y0,x1,y1=PANELS['inner']
    d.rectangle((x0,y0,x1-1,y1-1),fill='#dce2db')
    for xx in range(x0+16,x1,24):
        for yy in range(y0+12,y1,24):
            d.rectangle((xx,yy,xx+3,yy+3),fill='#c4cec7')
    d.rectangle((x0+18,y0+18,x1-19,y1-19),outline='#bfcbbf',width=5)
    lettering(d,'CUSTOM',((x0+x1)/2,y0+111),46,'#c0cdc2',275)
    lettering(d,'COLLECTION',((x0+x1)/2,y0+156),32,'#c0cdc2',275)
    # Solid texels for cardboard, navy, and particle samples.
    d.rectangle((900,0,963,63),fill=PAPER)
    d.rectangle((900,64,963,127),fill=NAVY)
    combined=Image.new('RGBA',(1024,2048))
    combined.paste(base,(0,0)); combined.paste(tint,(0,1024))
    TEXTURE.parent.mkdir(parents=True,exist_ok=True)
    combined.resize((512,1024),Image.Resampling.LANCZOS).save(TEXTURE)


def panel(name, tinted=False):
    x0,y0,x1,y1=PANELS[name]
    offset=1024 if tinted else 0
    return [x0/64,(y0+offset)/128,x1/64,(y1+offset)/128]


def face(uv, tint=False):
    result={'uv':uv,'texture':'#package'}
    if tint:result['tintindex']=0
    return result


def shell():
    elements=[]
    def cube(name,a,b,printed=None):
        faces={side:face([14.25,.125,14.75,.375]) for side in ('north','south','east','west','up','down')}
        for side,part in (printed or {}).items():faces[side]=face(panel(part))
        elements.append({'name':name,'from':list(a),'to':list(b),'faces':faces})
    def plane(name,a,b,side,part,tint=False):
        elements.append({'name':name,'from':list(a),'to':list(b),
                         'faces':{side:face(panel(part,tint),tint)}})

    plane('Printed front frame and glints',(3,0,4.008),(13,14,4.008),'north','front')
    plane('Inside printed front frame',(3,0,4.022),(13,14,4.022),'south','front')
    cube('Cardboard back',(3.005,0,11.7),(12.995,13.995,11.995),{'south':'back','north':'inner'})
    cube('Cardboard left wall',(3.005,0,4.03),(3.3,13.995,11.7),{'west':'left'})
    cube('Cardboard right wall',(12.7,0,4.03),(12.995,13.995,11.7),{'east':'right'})
    cube('Top lid',(3.3,13.7,4.03),(12.7,13.995,11.7),{'up':'top'})
    cube('Bottom lid',(3.3,0,4.03),(12.7,.3,11.7),{'down':'bottom'})
    cube('Retained inner cardboard tray',(3.4,.3,4.3),(12.6,.59,11.65))
    plane('Tintable front border and accent',(3,0,4),(13,14,4),'north','front',True)
    plane('Tintable back accent',(3.005,0,12),(12.995,13.995,12),'south','back',True)
    plane('Tintable left side',(3,0,4.03),(3,13.995,11.7),'west','left',True)
    plane('Tintable right side',(13,0,4.03),(13,13.995,11.7),'east','right',True)
    plane('Tintable lid border',(3.3,14,4.03),(12.7,14,11.7),'up','top',True)
    return elements


def bitmap_font():
    """Arial Bold bitmap glyphs, with the vanilla font covering other Unicode."""
    atlas=Image.new('RGBA',(512,480),(0,0,0,0))
    draw=ImageDraw.Draw(atlas)
    glyphfont=font(30)
    codepoints=list(range(32,128))+list(range(160,256))
    rows=[]
    for row in range(12):
        chars=[]
        for col in range(16):
            cp=codepoints[row*16+col]
            # Space advance comes from the explicit provider, not empty pixels.
            char='\0' if cp in (32,127,160) else chr(cp)
            chars.append(char)
            if char!='\0':
                draw.text((col*32+1,row*40+30),char,font=glyphfont,fill='white',anchor='ls')
        rows.append(''.join(chars))
    path=ASSETS/'textures/font/custom_display_box.png'
    path.parent.mkdir(parents=True,exist_ok=True)
    atlas.save(path)
    write(ASSETS/'font/custom_display_box.json',{'providers':[
        {'type':'space','advances':{' ':3.25,'\u00a0':3.25}},
        {'type':'bitmap','file':'japanesearcades:font/custom_display_box.png','height':10,'ascent':8,'chars':rows},
        {'type':'reference','id':'minecraft:default'}]})


def export(elements):
    textures={'package':'japanesearcades:block/custom_display_box_package',
              'particle':'japanesearcades:block/custom_display_box_package'}
    write(ASSETS/'models/block/custom_display_box.json',{'parent':'minecraft:block/block',
        'render_type':'minecraft:cutout','ambientocclusion':True,'textures':textures,'elements':elements})
    write(ASSETS/'models/item/custom_display_box.json',{'parent':'minecraft:builtin/entity',
        'gui_light':'front','textures':{'particle':textures['particle']},'display':DISPLAY})
    write(ASSETS/'blockstates/custom_display_box.json',{'variants':{
        'facing='+direction:{'model':'japanesearcades:block/custom_display_box',**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270))}})
    write(ROOT/'src/main/resources/data/japanesearcades/loot_table/blocks/custom_display_box.json',{
        'type':'minecraft:block','pools':[{'rolls':1,
            'conditions':[{'condition':'minecraft:survives_explosion'}],
            'entries':[{'type':'minecraft:item','name':'japanesearcades:custom_display_box',
                'functions':[{'function':'minecraft:copy_components','source':'block_entity',
                    'include':['japanesearcades:display_box']}]}]}]})
    faces=meshes(elements)
    by_name={e['name']:e for e in elements}
    for f in faces:
        f['tintindex']=next(iter(by_name[f['group']]['faces'].values())).get('tintindex',-1)
    bounds=[[min(p[i] for f in faces for p in f['vertices']),max(p[i] for f in faces for p in f['vertices'])] for i in range(3)]
    assert len(faces)==43 and bounds==[[3,13],[0,14],[4,12]],(len(faces),bounds)
    assert all(0<=v<=16 for e in elements for f in e['faces'].values() for v in f['uv'])
    write(ART/'custom_display_box.geometry.json',{'textures':textures,'meshes':faces,
        'bounds':bounds,'face_count':len(faces),'preview_tint':'#79c9bb'})
    bb_elements=[]
    for element in elements:
        e=copy.deepcopy(element)
        e.update({'type':'cube','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/'+e['name'])),
            'origin':[8,0,8],'rotation':[0,0,0],'rescale':False,'box_uv':False})
        for f in e['faces'].values():
            f['uv']=[v*(512 if i%2==0 else 1024)/16 for i,v in enumerate(f['uv'])]
            f['texture']=0
        bb_elements.append(e)
    write(ART/'custom_display_box.bbmodel',{'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},
        'name':'Custom Display Box','resolution':{'width':512,'height':1024},'elements':bb_elements,
        'textures':[{'name':TEXTURE.name,'id':'0','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/package')),
            'width':512,'height':1024,'uv_width':512,'uv_height':1024,
            'source':'data:image/png;base64,'+base64.b64encode(TEXTURE.read_bytes()).decode(),
            'mode':'bitmap','visible':True}],
        'outliner':[e['uuid'] for e in bb_elements]})
    write(ART/'design.json',{
        'shell_faces':43,'shell_elements':13,'shell_bounds_model_units':bounds,
        'tinted_faces':5,'tintindex':0,'tint_policy':'Only white accent-mask quads receive the contained-item color; print and cardboard remain untinted.',
        'texture':'japanesearcades:block/custom_display_box_package',
        'texture_size':[512,1024],
        'texture_layout':'Untinted atlas in top half, matching white alpha accent masks in bottom half.',
        'dynamic_label':{'font':'japanesearcades:custom_display_box','color':'#f7f7ec',
            'region_model_units':{'x':[3.85,12.15],'y':[.43,1.48],'z':3.985},
            'center_model_units':[8,.955,3.985],
            'center_block_units':[.5,.0596875,.2490625],
            'recommended_max_width_block_units':.51875,
            'recommended_max_height_block_units':.065625,
            'transform':'Apply the block facing rotation about block center. In north-local coordinates, text screen-right points toward negative X; text screen-down points toward negative Y. Place the text plane at z=3.985/16, in front of the untinted navy footer. Center the measured line and scale it to fit the region.',
            'overflow':'Scale to fit; preserve Component text and use the minecraft:default font fallback for remaining Unicode.'},
        'contents':{'interior_model_units':{'x':[3.5,12.5],'y':[1.9,11.9],'z':[4.15,11.6]},
            'suggested_center_model_units':[8,6.7,8],
            'suggested_max_extent_model_units':[8,9.6,7.1],
            'note':'Fit the complete transformed item or mob miniature bounds inside the window; the cardboard tray top is y=0.59.'},
        'item_model':'minecraft:builtin/entity; custom item renderer draws this shell block model and the stored contents.',
        'copied_loot_component':'japanesearcades:display_box'})
    print('custom_display_box: 13 elements, 43 shell faces, 5 tinted masks; bounds='+str(bounds))


def main():
    ART.mkdir(parents=True,exist_ok=True)
    package_texture()
    bitmap_font()
    export(shell())


if __name__=='__main__':main()
