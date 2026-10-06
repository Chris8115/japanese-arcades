"""Original compact arcade prizes and utility-card artwork; native OBJ export."""
import base64
import json
import math
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from initial_d_geometry import Geometry

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
TEX=ASSETS/'textures/block';ITEMTEX=ASSETS/'textures/item';ART=ROOT/'art/arcade_economy'
for path in (TEX,ITEMTEX,ART,ASSETS/'models/block',ASSETS/'models/item',ROOT/'src/main/resources/data/funpackcustom/loot_table/blocks'):path.mkdir(parents=True,exist_ok=True)
COLORS={'white':'#fff6e4','teal':'#31b4b3','teal_dark':'#247b89','pink':'#f46ca6',
        'navy':'#172a43','dark':'#263b51','gold':'#d8a039','lightgold':'#ffdc78',
        'silver':'#a5c2cf','cyan':'#86eeee','blue':'#476fc2','purple':'#9d77c7',
        'cream':'#ffe9bf','black':'#131e2a','orange':'#ef9558','red':'#dc4f73'}
palette=Image.new('RGB',(256,256));draw=ImageDraw.Draw(palette)
for i,color in enumerate(COLORS.values()):draw.rectangle(((i%4)*64,(i//4)*64,(i%4+1)*64-1,(i//4+1)*64-1),fill=color)
palette.save(TEX/'arcade_prize_materials.png')

def font(size):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size)
def label(im,xy,text,size,fill,anchor='mm'):
    ImageDraw.Draw(im).text(xy,text,font=font(size),fill=fill,anchor=anchor)
def star(cx,cy,r,inner=.45,n=5):
    return [(cx+math.cos(-math.pi/2+i*math.pi/n)*r*(1 if i%2==0 else inner),cy+math.sin(-math.pi/2+i*math.pi/n)*r*(1 if i%2==0 else inner)) for i in range(n*2)]

# A single-original-screen miniature cabinet: a simple star rhythm scene.
im=Image.new('RGB',(512,384),COLORS['navy']);d=ImageDraw.Draw(im)
for x in range(-384,512,96):d.polygon([(x,384),(x+40,384),(x+320,0),(x+280,0)],fill='#223d57')
for r,color in ((145,'#345870'),(112,COLORS['teal']),(102,COLORS['navy'])):d.ellipse((256-r,195-r,256+r,195+r),fill=color)
d.polygon(star(256,195,79),fill=COLORS['lightgold']);d.ellipse((218,179,232,193),fill=COLORS['navy']);d.ellipse((280,179,294,193),fill=COLORS['navy'])
d.arc((238,191,274,221),0,180,fill=COLORS['navy'],width=6)
for x,y,c in ((66,128,'pink'),(441,190,'cyan'),(116,288,'lightgold'),(368,301,'pink')):d.ellipse((x-15,y-15,x+15,y+15),fill=COLORS[c])
label(im,(256,31),'PERFECT!',36,COLORS['white']);label(im,(256,348),'ARCADE STAR',24,COLORS['cyan']);im.save(TEX/'arcade_prize_mini_screen.png')
im=Image.new('RGB',(768,160),COLORS['navy']);d=ImageDraw.Draw(im)
d.rectangle((0,0,768,12),fill=COLORS['cyan']);d.rectangle((0,148,768,160),fill=COLORS['pink']);d.polygon(star(70,80,43),fill=COLORS['lightgold'])
label(im,(429,83),'ARCADE STAR',68,COLORS['white']);im.save(TEX/'arcade_prize_mini_marquee.png')

im=Image.new('RGB',(640,768),COLORS['navy']);d=ImageDraw.Draw(im)
d.polygon([(0,0),(640,0),(640,118),(0,350)],fill=COLORS['teal']);d.polygon([(0,635),(640,395),(640,768),(0,768)],fill=COLORS['pink'])
for x,y in ((54,364),(573,325),(79,585),(577,621)):d.polygon(star(x,y,22),fill=COLORS['lightgold'])
label(im,(320,76),'ARCADE',89,COLORS['white']);label(im,(320,158),'CLUB',87,COLORS['white'])
for r,c in ((164,'white'),(147,'teal'),(120,'navy')):d.ellipse((320-r,397-r,320+r,397+r),fill=COLORS[c])
d.polygon(star(320,397,102),fill=COLORS['lightgold']);d.ellipse((279,375,293,391),fill=COLORS['navy']);d.ellipse((347,375,361,391),fill=COLORS['navy'])
d.arc((300,390,340,423),0,180,fill=COLORS['navy'],width=7)
label(im,(320,649),'PLAY TOGETHER',44,COLORS['white']);label(im,(320,707),'GOOD GAMES. GOOD FRIENDS.',22,COLORS['navy']);im.save(TEX/'arcade_prize_poster.png')
im=Image.new('RGB',(512,96),COLORS['navy']);label(im,(256,48),'RHYTHM STAR',48,COLORS['lightgold']);im.save(TEX/'arcade_prize_trophy_label.png')

# Contactless pass silhouette: original white/teal/magenta design, no real issuer logo.
im=Image.new('RGBA',(1024,640),(0,0,0,0));d=ImageDraw.Draw(im)
d.rounded_rectangle((14,14,1010,626),58,fill=COLORS['white'],outline=COLORS['silver'],width=12)
d.rounded_rectangle((34,34,990,606),42,outline='#dde7e2',width=4)
d.polygon([(36,59),(973,59),(987,114),(36,342)],fill=COLORS['teal'])
d.polygon([(600,605),(989,387),(989,568),(959,605)],fill=COLORS['pink'])
d.polygon(star(121,123,49),fill=COLORS['white']);label(im,(226,122),'ARCADE',57,COLORS['white'],'lm')
label(im,(89,377),'ARCADE PASS',94,COLORS['navy'],'lm');label(im,(93,457),'PLAY  /  COLLECT  /  REDEEM',27,COLORS['teal_dark'],'lm')
label(im,(91,556),'MEMBER CARD',23,COLORS['navy'],'lm')
for radius in (30,51,72):d.arc((849-radius,270-radius,849+radius,270+radius),-58,58,fill=COLORS['teal_dark'],width=10)
d.ellipse((844,263,858,277),fill=COLORS['teal_dark'])
im.save(ART/'arcade-pass.png')
icon=Image.new('RGBA',(512,512),(0,0,0,0));small=im.resize((496,310),Image.Resampling.LANCZOS);icon.alpha_composite(small,(8,101));icon.save(ITEMTEX/'arcade_pass.png')
(ASSETS/'models/item/arcade_pass.json').write_text(json.dumps({'parent':'minecraft:item/generated','textures':{'layer0':'funpackcustom:item/arcade_pass'}},indent=2)+'\n')

def ellipsoid(g,name,center,radii,mat,segments=16,rings=8):
    cx,cy,cz=center;rx,ry,rz=radii
    def pt(i,j):
        a=i*math.tau/segments;b=-math.pi/2+j*math.pi/rings
        return (cx+rx*math.cos(b)*math.cos(a),cy+ry*math.sin(b),cz+rz*math.cos(b)*math.sin(a))
    for j in range(rings):
        for i in range(segments):
            points=[pt(i,j),pt(i,j+1),pt(i+1,j+1),pt(i+1,j)]
            if j==0:points=points[:3]
            if j==rings-1:points=[points[0],points[1],points[3]]
            g.face(name+' %d %d'%(i,j),points,mat)

def model():return Geometry(COLORS)
models={}
g=model();g.group='Soft teal arcade cat'
ellipsoid(g,'Pear shaped plush body',(8,4.8,8.6),(3.5,4.6,2.9),'teal')
ellipsoid(g,'Cream sewn tummy',(8,4.35,5.85),(2.17,2.87,.45),'cream')
for x in (5.12,10.88):ellipsoid(g,'Plush seated paw '+str(x),(x,1.47,5.65),(2.05,1.40,1.86),'teal_dark')
for x in (4.0,12.0):ellipsoid(g,'Soft little arm '+str(x),(x,5.14,7.90),(1.08,2.04,1.28),'teal')
ellipsoid(g,'Rounded cat head',(8,9.69,7.73),(4.83,3.01,3.05),'teal')
for x in (4.02,11.98):
    g.prism('Pointed soft ear '+str(x),[(x-1.44,11.20),(x+1.44,11.20),(x,13.92)],6.45,8.29,'teal_dark')
    g.prism('Pink inside ear '+str(x),[(x-.88,11.73),(x+.88,11.73),(x,13.43)],6.425,6.455,'pink')
ellipsoid(g,'Cream oval muzzle',(8,9.17,4.91),(3.28,1.97,.31),'cream')
for x in (6.22,9.78):
    g.disc('Black bead eye '+str(x),x,9.76,.29,4.57,4.70,'navy',16)
    g.disc('Eye sparkle '+str(x),x+.065,9.845,.079,4.545,4.575,'white',12)
for x in (5.44,10.56):g.disc('Pink cheek '+str(x),x,8.80,.32,4.592,4.66,'pink',16)
g.prism('Small heart nose',[(7.61,9.2),(8,8.89),(8.39,9.2)],4.557,4.65,'pink')
g.tube('Left embroidered smile',[(8,8.96,4.55),(7.91,8.59,4.57),(7.51,8.49,4.60)],.058,'navy',6)
g.tube('Right embroidered smile',[(8,8.96,4.55),(8.09,8.59,4.57),(8.49,8.49,4.60)],.058,'navy',6)
g.rounded('Magenta collar',(5.48,6.32,10.52,6.80),5.77,7.0,.15,'pink')
points=[(x,5.99-(y-5.99)) for x,y in star(8,5.99,.70)]
g.prism('Gold collectible star tag',points,5.42,5.61,'lightgold')
g.tube('Curled plush tail',[(11.0,2.0,10.35),(12.70,2.63,10.40),(13.23,3.70,9.69),(12.94,4.48,9.35)],.48,'teal_dark',10)
models['arcade_cat_plush']=g

g=model();g.group='Rhythm star trophy'
g.rounded('Navy beveled trophy foot',(4.0,.05,12.0,1.55),4.6,11.4,.28,'navy')
g.rounded('Gold stepped foot',(4.51,1.55,11.49,2.12),5.12,10.88,.22,'gold')
g.rounded('Gold upright trophy stem',(7.33,2.10,8.67,7.50),7.02,8.48,.18,'gold')
for x,left in ((6.05,True),(9.95,False)):
    g.prism('Award ribbon '+str(left),[(x-.72,3.75),(x,4.36),(x+.72,3.75),(x+.64,8.14),(x-.64,8.14)],7.34,7.62,'pink' if left else 'teal')
points=[(x,9.50-(y-9.50)) for x,y in star(8,9.50,4.38)]
g.prism('Raised five point gold star',points,6.48,8.41,'gold')
points=[(x,9.50-(y-9.50)) for x,y in star(8,9.50,3.89)]
g.prism('Polished gold star face',points,6.39,6.49,'lightgold')
g.disc('Teal enamel medal',8,9.43,1.28,6.29,6.405,'teal_dark',24)
start=len(g.faces)
g.disc('Musical note dot',7.69,8.95,.36,6.26,6.30,'white',16)
g.box('Musical note stem',(7.93,8.95,6.25),(8.15,10.23,6.29),'white')
g.prism('Musical note flag',[(8.1,9.83),(8.74,9.61),(8.74,10.04),(8.1,10.30)],6.25,6.29,'white')
# Viewer-left is positive model X on the north face. Mirror the printed note,
# preserving outward winding, so its stem remains on the viewer-right.
g.transform(start,lambda x,y,z:(16-x,y,z))
for f in g.faces[start:]:f['vertices'].reverse();f['uv'].reverse()
g.decal('Rhythm Star engraved plaque',(4.48,.35,11.52,1.19),4.579,'trophy_label')
models['rhythm_star_trophy']=g

g=model();g.group='Tiny decorative arcade cabinet'
g.yz_shell('Miniature navy shell',3.66,12.34,[(.05,5.35),(4.72,5.35),(5.75,3.74),(7.28,4.0),(8.31,5.39),(11.70,6.47),(12.1,5.80),(13.92,5.8),(13.92,11.55),(.05,11.55)],'navy')
g.box('Mini arcade silver foot',(3.55,.05,5.23),(12.45,.50,11.61),'silver')
for x in (3.51,12.37):
    g.yz_shell('Magenta side trim '+str(x),x,x+.12,[(.54,5.29),(4.78,5.29),(5.74,3.65),(7.31,3.92),(8.34,5.3),(11.74,6.38),(12.1,5.70),(13.93,5.70),(13.93,6.01),(12.2,6.01),(11.84,6.68),(8.2,5.64),(7.12,4.25),(5.86,3.99),(4.97,5.58),(.54,5.58)],'pink')
start=len(g.faces)
g.rounded('Mini black screen bezel',(4.14,8.12,11.86,11.82),5.22,5.41,.14,'black')
g.decal('Tiny star game screen',(4.48,8.43,11.52,11.56),5.201,'mini_screen',True)
g.transform(start,lambda x,y,z:(x,y,z+(y-8.12)*.318))
g.rounded('Mini lit marquee surround',(3.99,12.32,12.01,13.69),5.691,5.89,.10,'cyan')
g.decal('Arcade Star marquee',(4.15,12.48,11.85,13.53),5.678,'mini_marquee',True)
g.yz_shell('Miniature cyan control deck',3.91,12.09,[(6.54,3.71),(7.33,4.03),(7.97,5.0),(7.75,5.25),(6.41,4.01)],'teal')
g.tube('Tiny joystick shaft',[(6.25,7.25,4.47),(6.25,8.57,4.35)],.11,'silver',8)
ellipsoid(g,'Pink joystick ball',(6.25,8.58,4.35),(.40,.39,.4),'pink',12,6)
for x,z in ((9.20,4.18),(10.42,4.62)):
    start=len(g.faces);g.disc('Mini action button '+str(x),x,-z,.39,-7.61,-7.42,'lightgold',12)
    g.transform(start,lambda X,Z,Y:(X,-Y,-Z))
g.rounded('Mini lower panel',(4.26,.98,11.74,4.67),5.305,5.43,.14,'teal_dark')
points=[(x,3.01-(y-3.01)) for x,y in star(8,3.01,1.4)]
g.prism('Tiny lower star emblem',points,5.265,5.33,'lightgold')
for x in (3.645,12.355):
    for y in (2.1,4.1,6.1):
        pts=[(x,y,8.06),(x,y+.63,7.57),(x,y+2.11,10.15),(x,y+1.48,10.64)]
        if x<8:pts.reverse()
        g.face('Mini side lightning '+str(x)+' '+str(y),pts,'teal' if y!=4.1 else 'pink')
models['mini_arcade_cabinet']=g

g=model();g.group='Arcade poster display stand'
g.rounded('Weighted navy plaque base',(2.15,.05,13.85,1.0),3.68,12.32,.36,'navy')
g.box('Poster silver upright',(7.34,1.0,7.19),(8.66,3.08,8.81),'silver')
g.rounded('White acrylic display frame',(2.83,2.18,13.17,13.96),7.00,8.36,.26,'white')
g.rounded('Teal inset print border',(3.14,2.52,12.86,13.64),6.972,7.02,.13,'teal')
g.decal('Original arcade club poster',(3.43,2.83,12.57,13.32),6.958,'poster')
g.rounded('Plaque rear charcoal panel',(3.22,2.66,12.78,13.5),8.35,8.40,.15,'navy')
for x in (3.12,12.88):
    for y in (2.48,13.65):g.disc('Acrylic screw %s %s'%(x,y),x,y,.075,6.959,7.016,'silver',12)
models['arcade_poster']=g

texture_paths={name:'funpackcustom:block/arcade_prize_'+name for name in ('materials','mini_screen','mini_marquee','poster','trophy_label')}
texture_paths['particle']=texture_paths['materials']
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def export(name,g):
    assert len({f['name'] for f in g.faces})==len(g.faces),name
    for f in g.faces:
        assert 3<=len(f['vertices'])<=4 and len(f['uv'])==len(f['vertices'])
        assert all(2<=p[0]<=14 and 0<=p[1]<=14 and 3<=p[2]<=13 for p in f['vertices']),(name,f['name'],f['vertices'])
    bounds=[[min(p[i] for f in g.faces for p in f['vertices']),max(p[i] for f in g.faces for p in f['vertices'])] for i in range(3)]
    write(ART/(name+'.geometry.json'),{'textures':texture_paths,'meshes':g.faces,'bounds':bounds})
    lines=['# Original arcade collectible: '+name,'mtllib funpackcustom:models/block/arcade_prizes.mtl'];idx=1;last=None
    for f in g.faces:
        mat=f['texture'][1:]+('_lit' if f['glow'] else '_surface')
        if mat!=last:lines.append('usemtl '+mat);last=mat
        lines.extend('v '+' '.join('%.9f'%(v/16) for v in p) for p in f['vertices'])
        lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
        lines.append('f '+' '.join('%d/%d'%(idx+i,idx+i) for i in range(len(f['vertices']))));idx+=len(f['vertices'])
    (ASSETS/'models/block'/(name+'.obj')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'funpackcustom:models/block/'+name+'.obj',
           'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':True,
           'render_type':'minecraft:cutout_mipped_all','textures':texture_paths}
    write(ASSETS/'models/block'/(name+'.json'),model)
    write(ASSETS/'blockstates'/(name+'.json'),{'variants':{'facing='+direction:{'model':'funpackcustom:block/'+name,**({'y':angle} if angle else {})} for direction,angle in (('north',0),('east',90),('south',180),('west',270))}})
    model.update({'ambientocclusion':False,'gui_light':'front','display':{'gui':{'rotation':[15,225,0],'translation':[0,1,0],'scale':[1.05,1.05,1.05]},
        'ground':{'translation':[0,2,0],'scale':[.5,.5,.5]},'fixed':{'rotation':[0,180,0],'scale':[.8,.8,.8]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.4,.4,.4]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,1,0],'scale':[.55,.55,.55]}}})
    write(ASSETS/'models/item'/(name+'.json'),model)
    write(ROOT/'src/main/resources/data/funpackcustom/loot_table/blocks'/(name+'.json'),{'type':'minecraft:block','pools':[{'rolls':1,'conditions':[{'condition':'minecraft:survives_explosion'}],'entries':[{'type':'minecraft:item','name':'funpackcustom:'+name}]}]})
    specs=[(key,TEX/(value.split('/')[-1]+'.png')) for key,value in texture_paths.items() if key!='particle'];texids={'#'+key:i for i,(key,path) in enumerate(specs)}
    textures=[]
    for i,(key,path) in enumerate(specs):
        w,h=Image.open(path).size;textures.append({'name':path.name,'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'arcade_prizes/'+key)),
            'width':w,'height':h,'uv_width':w,'uv_height':h,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','visible':True})
    elements=[]
    for f in g.faces:
        keys=['v'+str(i) for i in range(len(f['vertices']))];index=texids[f['texture']];w,h=textures[index]['width'],textures[index]['height']
        elements.append({'name':f['name'],'type':'mesh','uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+f['name'])),'origin':[0,0,0],'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':index}},'visibility':True,'export':True})
    write(ART/(name+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':name,'resolution':{'width':256,'height':256},'elements':elements,'textures':textures,'outliner':[e['uuid'] for e in elements]})
    print(name,len(g.faces),'faces',bounds)

mtl=[]
for key,lit in sorted({(f['texture'][1:],f['glow']) for g in models.values() for f in g.faces}):mtl.extend(['newmtl '+key+('_lit' if lit else '_surface'),'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1','map_Kd #'+key,''])
(ASSETS/'models/block/arcade_prizes.mtl').write_text('\n'.join(mtl),encoding='utf-8')
for name,g in models.items():export(name,g)
write(ART/'art-lang.json',{'item.funpackcustom.arcade_pass':'Arcade Pass','block.funpackcustom.arcade_cat_plush':'Arcade Cat Plush',
    'block.funpackcustom.rhythm_star_trophy':'Rhythm Star Trophy','block.funpackcustom.mini_arcade_cabinet':'Mini Arcade Cabinet','block.funpackcustom.arcade_poster':'Arcade Poster Stand'})
