"""Reproducible static models for all Minecraft 1.21.1 mob collectibles.

Run with Python/Pillow. Vanilla entity PNGs are copied byte-for-byte from the
local 1.21.1 client JAR (or retained existing copies); no entity renderer runs.
Every box, miniature and empty package is a normal cutout block model.
"""
import argparse
import base64
import copy
import hashlib
import json
import uuid
import zipfile
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from mob_figure_catalog import MOBS

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
TEX = ASSETS / 'textures/block'
ART = ROOT / 'art/mob_figures'
LOOT = ROOT / 'src/main/resources/data/japanesearcades/loot_table/blocks'
LEGACY_MOBS = ('creeper', 'zombie', 'skeleton', 'enderman', 'slime', 'axolotl')
PANELS = {'front': (0, 0, 320, 448), 'back': (320, 0, 640, 448),
          'left': (640, 0, 896, 448), 'right': (0, 448, 256, 896),
          'top': (256, 448, 576, 704), 'bottom': (576, 448, 896, 704),
          'inner': (256, 704, 576, 960), 'plaque': (576, 704, 896, 768)}
SWATCHES = {'navy': '#182332', 'paper': '#e9ede5', 'gold': '#dbbd79',
            'pink': '#df7d9d', 'white': '#f7f7ec', 'bone': '#adaaa0',
            'black': '#252531', 'green': '#6baf46'}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def font(size, bold=True):
    candidates = [Path('C:/Windows/Fonts') / ('arialbd.ttf' if bold else 'arial.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def lettering(draw, text, xy, size, fill, max_width=None, anchor='mm'):
    f = font(size)
    while max_width and draw.textbbox((0, 0), text, font=f)[2] > max_width:
        size -= 1
        f = font(size)
    draw.text(xy, text, font=f, fill=fill, anchor=anchor)


def make_package(mob, accent, number, biome):
    """Print dieline-like artwork; the central front panel is truly transparent."""
    title = mob.replace('_', ' ').upper()
    im = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    navy, paper, gold = SWATCHES['navy'], SWATCHES['paper'], SWATCHES['gold']
    for key, (x0, y0, x1, y1) in PANELS.items():
        d.rectangle((x0, y0, x1-1, y1-1), fill=paper)
    # Front: generous transparent window, a slim printed frame, readable labels.
    d.rectangle((0, 0, 319, 447), fill=navy)
    d.rectangle((10, 10, 309, 437), outline=accent, width=3)
    d.rectangle((24, 68, 295, 385), fill=(0, 0, 0, 0))
    d.rectangle((21, 65, 298, 388), outline=paper, width=3)
    d.rectangle((24, 369, 295, 385), fill=accent)
    lettering(d, 'MOB COLLECTION', (139, 28), 22, paper, 248)
    lettering(d, 'ARCADE PRIZE  /  SERIES 01', (139, 49), 10, accent)
    d.rectangle((267, 15, 302, 52), fill=accent)
    lettering(d, f'{number:02}', (285, 35), 23, navy)
    lettering(d, title, (160, 409), 32, paper, 270)
    lettering(d, 'MINIATURE DISPLAY FIGURE', (160, 432), 10, accent)
    # Small opaque glints imply the clear packaging film without a translucent
    # full-sheet overdraw layer or obscuring the actual 3D collectible.
    d.line([(38, 126), (66, 87)], fill='#dce9e7', width=3)
    d.line([(39, 146), (81, 87)], fill='#aebfc5', width=2)
    d.line([(276, 340), (262, 360)], fill='#dce9e7', width=2)
    # Back print is an intentionally complete package rather than a blank cube.
    x = 320
    d.rectangle((x, 0, x+319, 447), fill=paper)
    d.rectangle((x, 0, x+319, 76), fill=navy)
    lettering(d, 'MOB COLLECTION', (x+160, 29), 25, paper)
    lettering(d, f'NO. {number:02}  /  {title}', (x+160, 55), 14, accent, 294)
    d.rectangle((x+22, 100, x+297, 248), fill=accent)
    lettering(d, f'{number:02}', (x+160, 172), 126, navy)
    lettering(d, biome, (x+160, 273), 17, navy)
    lettering(d, f'COLLECT ALL {len(MOBS)}', (x+160, 312), 20, navy)
    for i in range(6):
        badge = ((number-1)//6)*6+i+1
        if badge > len(MOBS):
            continue
        xx = x+27+i*46
        d.rectangle((xx, 335, xx+35, 370), fill=navy if badge == number else '#bac3bd')
        lettering(d, f'{badge:02}', (xx+18, 353), 17, paper)
    lettering(d, 'FUN PACK ARCADE', (x+118, 404), 13, navy)
    lettering(d, 'DISPLAY SERIES 01', (x+118, 425), 10, navy)
    for i in range(26):
        xx=x+224+i*2
        d.rectangle((xx, 391, xx+(i%3 == 0), 427-(i%4)*2), fill=navy)
    # Both narrow side panels read correctly when the package is turned.
    for side in ('left', 'right'):
        x0, y0, x1, y1 = PANELS[side]
        d.rectangle((x0, y0, x1-1, y1-1), fill=accent)
        for k in range(7):
            yy=y0+105+k*38
            d.line((x0+17, yy, x1-18, yy), fill=paper, width=1)
        lettering(d, 'MOB', ((x0+x1)/2, y0+42), 44, navy)
        lettering(d, 'COLLECTION', ((x0+x1)/2, y0+79), 24, navy)
        lettering(d, f'{number:02}', ((x0+x1)/2, y0+220), 132, navy)
        d.rectangle((x0+15, y0+328, x1-16, y0+386), fill=navy)
        lettering(d, title, ((x0+x1)/2, y0+357), 30, paper, 206)
        lettering(d, 'ARCADE PRIZE', ((x0+x1)/2, y0+421), 15, navy)
    for side in ('top', 'bottom'):
        x0, y0, x1, y1 = PANELS[side]
        d.rectangle((x0, y0, x1-1, y1-1), fill=navy)
        d.rectangle((x0+10, y0+10, x1-11, y1-11), outline=accent, width=3)
        lettering(d, 'MOB COLLECTION', ((x0+x1)/2, y0+91), 26, paper, 290)
        lettering(d, f'{number:02}  /  {title}', ((x0+x1)/2, y0+137), 23, accent, 290)
        lettering(d, 'FUN PACK ARCADE', ((x0+x1)/2, y0+185), 13, paper)
    x0, y0, x1, y1 = PANELS['inner']
    d.rectangle((x0, y0, x1-1, y1-1), fill='#dce2db')
    for xx in range(x0+16, x1, 24):
        for yy in range(y0+12, y1, 24):
            d.rectangle((xx, yy, xx+3, yy+3), fill='#c4cec7')
    d.rectangle((x0+18, y0+18, x1-19, y1-19), outline=accent, width=5)
    lettering(d, f'{number:02}', ((x0+x1)/2, (y0+y1)/2), 118, '#c0cdc2')
    x0, y0, x1, y1 = PANELS['plaque']
    d.rectangle((x0, y0, x1-1, y1-1), fill=navy)
    d.rectangle((x0+3, y0+3, x1-4, y1-4), outline=accent, width=3)
    lettering(d, f'{number:02}  {title}', ((x0+x1)/2, (y0+y1)/2), 37, paper, 292)
    for i, color in enumerate([*SWATCHES.values(), accent]):
        d.rectangle((900, i*48, 963, i*48+47), fill=color)
    # Two-by-two supersampling keeps printed type legible at modest VRAM cost.
    im.resize((512, 512), Image.Resampling.LANCZOS).save(TEX/(mob+'_figure_package.png'))


def panel(key):
    return [v/64 for v in PANELS[key]]


def solid(key):
    i = list(SWATCHES).index(key) if key in SWATCHES else 8
    return [14.25, (i*48+16)/64, 14.75, (i*48+32)/64]


def uv_net(offset, size, texture_size):
    u, v = offset
    w, h, d = size
    px = {'north': [u+d, v+d, u+d+w, v+d+h],
          'east': [u, v+d, u+d, v+d+h],
          'south': [u+d+w+d, v+d, u+d+w+d+w, v+d+h],
          'west': [u+d+w, v+d, u+d+w+d, v+d+h],
          'up': [u+d, v, u+d+w, v+d],
          'down': [u+d+w, v+d, u+d+w+w, v]}
    return {side: [a*16/texture_size[i%2] for i,a in enumerate(rect)] for side,rect in px.items()}


class Geometry:
    def __init__(self, mob):
        self.mob = mob
        self.elements = []
        self.texture_size = Image.open(TEX/(mob+'_figure_skin.png')).size if mob in LEGACY_MOBS else (64, 64)

    def cube(self, name, start, end, material='skin', uv=None, colors=None):
        faces = {}
        for side in ('north', 'south', 'east', 'west', 'up', 'down'):
            sideuv = uv[side] if isinstance(uv, dict) else (uv or solid(material))
            faces[side] = {'uv': sideuv, 'texture': '#'+('package' if material in SWATCHES or material == 'accent' else material)}
        if colors:
            faces.update(colors)
        self.elements.append({'name': name, 'from': list(start), 'to': list(end), 'faces': faces})

    def skin(self, name, start, end, offset, size):
        self.cube(name, start, end, uv=uv_net(offset, size, self.texture_size))

    def plane(self, name, start, end, side, texture, uv):
        self.elements.append({'name':name, 'from':list(start), 'to':list(end),
                              'faces': {side: {'uv':uv, 'texture':'#'+texture}}})

    def base(self):
        self.cube('Display plinth', (4.4, 0, 4.4), (11.6, .46, 11.6), 'navy')
        self.cube('Accent plinth rim', (4.5, .46, 4.5), (11.5, .64, 11.5), 'accent')
        self.cube('Dark inset top', (4.7, .64, 4.7), (11.3, .73, 11.3), 'navy')
        self.plane('Printed collection nameplate', (5.05, .06, 4.395), (10.95, .4, 4.395), 'north', 'package', panel('plaque'))


def figure(mob):
    g = Geometry(mob)
    g.base()
    if mob == 'creeper':
        # Exact 8x8x8 head, 8x12x4 torso and four 4x6x4 feet proportions.
        s = .38
        def c(name, a, b, offset, dims):
            g.skin(name, (8+a[0]*s, .73+a[1]*s, 8+a[2]*s), (8+b[0]*s, .73+b[1]*s, 8+b[2]*s), offset, dims)
        c('Creeper head', (-4,18,-4),(4,26,4),(0,0),(8,8,8))
        c('Creeper torso', (-4,6,-2),(4,18,2),(16,16),(8,12,4))
        for x in (-4,0):
            for z in (-6,2):
                c('Creeper foot '+str((x,z)),(x,0,z),(x+4,6,z+4),(0,16),(4,6,4))
    elif mob in ('zombie', 'skeleton'):
        s=.305
        g.skin(mob+' head', (8-4*s,.73+24*s,8-4*s),(8+4*s,.73+32*s,8+4*s),(0,0),(8,8,8))
        g.skin(mob+' torso',(8-4*s,.73+12*s,8-2*s),(8+4*s,.73+24*s,8+2*s),(16,16),(8,12,4))
        leg_width=4 if mob=='zombie' else 2
        arm_width=4 if mob=='zombie' else 2
        for side in (-1,1):
            cx=8+side*2*s
            g.skin(mob+' leg '+str(side),(cx-leg_width*s/2,.73,8-leg_width*s/2),
                   (cx+leg_width*s/2,.73+12*s,8+leg_width*s/2),(0,16),(leg_width,12,leg_width))
            cx=8+side*(4+arm_width/2)*s
            if mob=='zombie':
                # Raised arms are baked cuboids: no animation, ticking or entity.
                uv=uv_net((40,16),(4,12,4),g.texture_size)
                g.cube('Zombie reaching arm '+str(side),(cx-2*s,.73+20*s,4.22),
                       (cx+2*s,.73+24*s,4.22+12*s),uv={
                           'north':uv['down'],'south':uv['up'],'up':uv['north'],
                           'down':uv['south'],'east':uv['east'],'west':uv['west']})
            else:
                g.skin('Skeleton arm bone '+str(side),(cx-s,.73+12*s,8-s),
                       (cx+s,.73+24*s,8+s),(40,16),(2,12,2))
        if mob=='skeleton':
            # A compact bow gives the collectible a distinct silhouette.
            for yy,xx in ((2.2,5.65),(3.25,5.3),(4.3,5.1),(5.35,5.3),(6.4,5.65)):
                g.cube('Bow wood '+str(yy),(xx,yy,6.65),(xx+.25,yy+1.08,6.9),'gold')
            g.cube('Bow string',(5.89,2.25,6.71),(5.95,7.4,6.78),'paper')
    elif mob=='enderman':
        s=.21
        g.skin('Enderman head',(8-4*s,.73+38*s,8-4*s),(8+4*s,.73+46*s,8+4*s),(0,0),(8,8,8))
        g.skin('Enderman torso',(8-4*s,.73+27*s,8-2*s),(8+4*s,.73+39*s,8+2*s),(32,16),(8,12,4))
        for side in (-1,1):
            cx=8+side*2*s
            g.skin('Enderman long leg '+str(side),(cx-s,.73,8-s),(cx+s,.73+30*s,8+s),(56,0),(2,30,2))
            cx=8+side*5*s
            g.skin('Enderman long arm '+str(side),(cx-s,.73+9*s,8-s),(cx+s,.73+39*s,8+s),(56,0),(2,30,2))
        g.plane('Purple Enderman eyes',(8-4*s,.73+38*s,8-4*s-.005),(8+4*s,.73+46*s,8-4*s-.005),
                'north','eyes',[2,4,4,8])
    elif mob=='slime':
        # An opaque vinyl shell uses the inner slime skin; raised dark eyes and
        # mouth retain the actual mob silhouette without overlapping glass cubes.
        g.skin('Slime vinyl body',(5, .73,5),(11,6.73,11),(0,16),(6,6,6))
        for index,x in enumerate((5.7,9.0)):
            g.skin('Slime eye '+str(index),(x,4.4,4.92),(x+1.25,5.65,5.12),(32,index*4),(2,2,2))
        g.skin('Slime mouth',(7.95,3.45,4.92),(8.65,4.15,5.12),(32,8),(1,1,1))
        g.cube('Slime top shine',(5.65,6.733,5.6),(6.8,6.746,6.1),'paper')
        g.cube('Slime top shine small',(7.0,6.733,5.6),(7.45,6.746,6.1),'paper')
    elif mob=='axolotl':
        # Low swimming pose, broad head, four feet and three feathered gill fans.
        g.skin('Axolotl head',(5.9,2.4,4.35),(10.1,5.025,6.975),(0,1),(8,5,5))
        g.skin('Axolotl body',(6.35,2.15,6.975),(9.65,3.8,10.95),(0,11),(8,4,10))
        def fin(name,a,b,rect,axis='z'):
            uv=[v/4 for v in rect]
            sides=('north','south') if axis=='z' else ('east','west')
            for side in sides:
                g.plane(name+' '+side,a,b,side,'skin',uv)
        fin('Top gills',(5.9,5.025,6.45),(10.1,6.6,6.45),(3,37,11,40))
        fin('Left gills',(4.325,2.4,6.45),(5.9,6.075,6.45),(0,40,3,47))
        fin('Right gills',(10.1,2.4,6.45),(11.675,6.075,6.45),(11,40,14,47))
        for side in (-1,1):
            x0,x1=(5.25,6.65) if side<0 else (9.35,10.75)
            for z in (7.25,10.2):
                fin('Axolotl foot '+str((side,z)),(x0,.74,z),(x1,2.85,z),(2,13,5,18))
        fin('Axolotl tail',(8,1.9,10.2),(8,4.525,11.6),(2,31,14,36),'x')
    return g


def packaging(mob):
    g=Geometry(mob)
    # The printed front is one cutout face, not a six-sided transparent cube.
    g.plane('Printed frame and window glints',(3,0,4),(13,14,4),'north','package',panel('front'))
    g.plane('Inside printed front frame',(3,0,4.015),(13,14,4.015),'south','package',panel('front'))
    g.cube('Cardboard back',(3,0,11.7),(13,14,12),'paper',colors={
        'south':{'uv':panel('back'),'texture':'#package'},
        'north':{'uv':panel('inner'),'texture':'#package'}})
    g.cube('Cardboard left wall',(3,0,4.02),(3.3,14,11.7),'paper',colors={
        'west':{'uv':panel('left'),'texture':'#package'}})
    g.cube('Cardboard right wall',(12.7,0,4.02),(13,14,11.7),'paper',colors={
        'east':{'uv':panel('right'),'texture':'#package'}})
    g.cube('Top lid',(3.3,13.7,4.02),(12.7,14,11.7),'paper',colors={
        'up':{'uv':panel('top'),'texture':'#package'}})
    g.cube('Bottom lid',(3.3,0,4.02),(12.7,.3,11.7),'paper',colors={
        'down':{'uv':panel('bottom'),'texture':'#package'}})
    g.cube('Retained inner cardboard tray',(3.4,.3,4.3),(12.6,.59,11.65),'paper')
    return g


def meshes(elements):
    result=[]
    for element in elements:
        x0,y0,z0=element['from']; x1,y1,z1=element['to']
        # Order is outward-facing and matches vanilla block face UV direction.
        vertices={
            'north':[(x1,y1,z0),(x1,y0,z0),(x0,y0,z0),(x0,y1,z0)],
            'south':[(x0,y1,z1),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1)],
            'east':[(x1,y1,z1),(x1,y0,z1),(x1,y0,z0),(x1,y1,z0)],
            'west':[(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)],
            'up':[(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],
            'down':[(x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)]}
        for side,face in element['faces'].items():
            u0,v0,u1,v1=face['uv']
            result.append({'name':element['name']+' '+side,'group':element['name'],
                'texture':face['texture'],'vertices':vertices[side],
                'uv':[[u0,v0],[u0,v1],[u1,v1],[u1,v0]],'glow':False})
    return result


def export(name, mob, g, boxed=False):
    textures={'skin':'japanesearcades:block/'+mob+'_figure_skin',
              'package':'japanesearcades:block/'+mob+'_figure_package',
              'particle':'japanesearcades:block/'+mob+'_figure_skin'}
    if mob=='enderman':textures['eyes']='japanesearcades:block/enderman_figure_eyes'
    model={'parent':'minecraft:block/block','render_type':'minecraft:cutout',
           'ambientocclusion':True,'textures':textures,'elements':g.elements}
    write(ASSETS/'models/block'/(name+'.json'),model)
    write(ASSETS/'models/item'/(name+'.json'),{'parent':'japanesearcades:block/'+name,'gui_light':'front',
        'display':{'gui':{'rotation':[14,205,0],'translation':[0,0,0], 'scale':[1,1,1] if boxed else [1.12,1.12,1.12]},
        'ground':{'translation':[0,2,0],'scale':[.5,.5,.5]},
        'fixed':{'rotation':[0,180,0],'scale':[.8,.8,.8]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.4,.4,.4]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,1,0],'scale':[.55,.55,.55]}}})
    write(ASSETS/'blockstates'/(name+'.json'),{'variants':{
        'facing='+direction:{'model':'japanesearcades:block/'+name,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270))}})
    write(LOOT/(name+'.json'),{'type':'minecraft:block','pools':[{'rolls':1,
        'conditions':[{'condition':'minecraft:survives_explosion'}],
        'entries':[{'type':'minecraft:item','name':'japanesearcades:'+name}]}]})
    faces=meshes(g.elements)
    bounds=[[min(p[i] for f in faces for p in f['vertices']),max(p[i] for f in faces for p in f['vertices'])] for i in range(3)]
    assert len(faces)<400,(name,len(faces))
    limits=((3,13),(0,14),(4,12)) if boxed else ((4,12),(0,11.5),(4,12))
    assert all(a>=lo-1e-6 and b<=hi+1e-6 for (a,b),(lo,hi) in zip(bounds,limits)),(name,bounds)
    write(ART/(name+'.geometry.json'),{'textures':textures,'meshes':faces,'bounds':bounds,'face_count':len(faces)})
    texdata=[]
    indices={}
    for key,path in textures.items():
        if key=='particle':continue
        indices[key]=len(texdata)
        filename=TEX/(path.split('/')[-1]+'.png')
        width,height=Image.open(filename).size
        texdata.append({'name':filename.name,'id':str(len(texdata)),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+key)),'width':width,'height':height,
            'uv_width':width,'uv_height':height,
            'source':'data:image/png;base64,'+base64.b64encode(filename.read_bytes()).decode(),
            'mode':'bitmap','visible':True})
    elements=[]
    for element in g.elements:
        out=copy.deepcopy(element)
        out['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+element['name']))
        out.update({'type':'cube','origin':[8,0,8],'rotation':[0,0,0],'rescale':False,'box_uv':False})
        for face in out['faces'].values():
            idx=indices[face['texture'][1:]]; t=texdata[idx]
            face['uv']=[v*(t['width'] if i%2==0 else t['height'])/16 for i,v in enumerate(face['uv'])]
            face['texture']=idx
        elements.append(out)
    write(ART/(name+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},
        'name':name,'resolution':{'width':512,'height':512},'elements':elements,
        'textures':texdata,'outliner':[e['uuid'] for e in elements]})
    print(f'{name}: {len(g.elements)} elements, {len(faces)} faces, bounds={bounds}')
    return {'model':name,'elements':len(g.elements),'placed_faces':len(faces),
            'inventory_faces':len(faces),'bounds':bounds}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--minecraft-jar',type=Path,default=Path.home()/'.gradle/caches/neoformruntime/artifacts/minecraft_1.21.1_client.jar')
    args=parser.parse_args()
    for path in (TEX,ART,ASSETS/'models/block',ASSETS/'models/item',LOOT):path.mkdir(parents=True,exist_ok=True)
    sources=[]
    archive=zipfile.ZipFile(args.minecraft_jar) if args.minecraft_jar.exists() else None
    for number,(mob,accent,biome) in enumerate(MOBS,1):
        make_package(mob,accent,number,biome)
        if mob not in LEGACY_MOBS:
            continue
        basename='axolotl_lucy' if mob=='axolotl' else mob
        source='assets/minecraft/textures/entity/'+mob+'/'+basename+'.png'
        dest=TEX/(mob+'_figure_skin.png')
        if archive:dest.write_bytes(archive.read(source))
        if not dest.exists():raise FileNotFoundError('Supply --minecraft-jar to copy '+source)
        sources.append({'file':str(dest.relative_to(ROOT)).replace('\\','/'),'source':source,
                        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        if mob=='enderman':
            dest=TEX/'enderman_figure_eyes.png'
            if archive:dest.write_bytes(archive.read('assets/minecraft/textures/entity/enderman/enderman_eyes.png'))
            if not dest.exists():raise FileNotFoundError('Missing copied Enderman eyes texture')
    if archive:archive.close()
    audit=[]
    for mob,accent,biome in MOBS:
        if mob not in LEGACY_MOBS:
            from mob_figure_meshes import export_captured_mob
            audit.extend(export_captured_mob(mob, sys.modules[__name__]))
            continue
        loose=figure(mob)
        audit.append(export(mob+'_figure',mob,loose))
        empty=packaging(mob)
        audit.append(export(mob+'_figure_box',mob,empty,True))
        full=packaging(mob)
        for element in loose.elements:
            e=copy.deepcopy(element)
            e['from'][1]+=.6;e['to'][1]+=.6
            full.elements.append(e)
        audit.append(export('boxed_'+mob+'_figure',mob,full,True))
    write(ART/'model-audit.json',{'format':'static baked block models (legacy cuboids and captured vanilla meshes)','source_minecraft_version':'1.21.1',
        'render_type':'minecraft:cutout','textures_copied_without_modification':sources,'models':audit})


if __name__=='__main__':main()
