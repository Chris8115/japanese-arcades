"""Single-play 2x2x2 UFO CATCHER-inspired compact crane cabinet.

Eight chunk-baked sections contain only the stationary case. The item and
editable preview include the same parked three-arm rig as the runtime profile.
Dimensions and prize/gantry coordinates are shared with ClawMachineLayout.
"""
from pathlib import Path
from collections import defaultdict
import base64
import hashlib
import json
import math
import uuid
from PIL import Image,ImageDraw,ImageFont
from initial_d_geometry import Geometry
from popn_music_geometry import _face,_surface
from bombergirl_geometry import plate,lathe
from ddr_mesh_export import pieces,quads
from obj_mesh_optimizer import optimize_obj

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/compact_claw_machine'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
ID='compact_claw_machine'
GRID_COLUMNS=4
PAD_WIDTH=5.6
COLORS={'white':'#f2f4f3','silver':'#bdcbd2','black':'#14232d','dark':'#354955',
 'cyan':'#b3f2ef','orange':'#f5c877','yellow':'#fff0b6','red':'#eb6598',
 'blue':'#4392b8','green':'#8bd8b4','cream':'#fff9eb','glass':'#dbf8ff',
 'pink':'#efa6cb','chrome':'#e2eaec','charcoal':'#657781','gray':'#94a4ac'}
PROFILE={'dimensions':[32,32,32],'part_formula':'x+2*z+4*y','grid_columns':GRID_COLUMNS,'grid_rows':3,
 'prize_centers':[[26-20*c/(GRID_COLUMNS-1),13.5,25-8*r] for r in range(3) for c in range(GRID_COLUMNS)],
 'floor_y':11,'pad_top_y':11.18,'pad_width':PAD_WIDTH,'prize_max_uniform_envelope':[4.6,4.6,3.4],
 'prize_bottom_y':11.2,'claw_home_basis_y':23,'claw_lowered_basis_y':13.5,'claw_scale':.85,
 'rail_y':28.1,'cable_top_y':27.7,'chute_home':[26,23,3.6],
 'chute_aperture':[22.5,2,29.5,5.5],'payout':[26,5,-4],
 'price_icon':[11.2,8.65,.20],'price_count':[16.5,8.65,.20]}

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def textures():
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',n)
    result={}
    def save(k,im):
        p=TEX/(ID+'_'+k+'.png');im.save(p,optimize=True);result[k]=p
    im=Image.new('RGB',(64,64));d=ImageDraw.Draw(im)
    for i,c in enumerate(COLORS.values()):
        x,y=i%4*16,i//4*16;d.rectangle((x,y,x+15,y+15),fill=c)
    save('materials',im)
    im=Image.new('RGB',(512,96),'#fff9fd');d=ImageDraw.Draw(im)
    for x in range(-50,560,85):d.polygon([(x,0),(x+54,0),(x+127,96),(x+73,96)],fill='#fae7f2')
    d.text((256,40),'UFO CATCHER',font=font(54),anchor='mm',fill='#c73685',stroke_width=2,stroke_fill='white')
    d.text((256,79),'C O M P A C T',font=font(17),anchor='mm',fill='#57788c')
    d.text((39,83),'SEGA',font=font(13),anchor='mm',fill='#1786aa');save('sign',im)
    im=Image.new('RGB',(256,128),'#ecabd0');d=ImageDraw.Draw(im)
    d.rounded_rectangle((6,6,249,121),radius=8,outline='#fff5fd',width=3)
    d.text((128,65),'PRIZE OUT',font=font(34),anchor='mm',fill='#ffffff');save('prize_out',im)
    im=Image.new('RGB',(256,128),'#204d61');d=ImageDraw.Draw(im)
    d.rounded_rectangle((4,4,251,123),radius=8,outline='#a2efed',width=2)
    d.text((128,42),'MOVE  •  DROP',font=font(21),anchor='mm',fill='#f4fcff')
    d.text((128,90),'GOOD LUCK!',font=font(25),anchor='mm',fill='#f6b5d6');save('controls',im)
    im=Image.new('RGB',(256,256),'#e7eeef');d=ImageDraw.Draw(im)
    d.rounded_rectangle((3,3,252,253),radius=7,outline='#a1b0b7',width=2)
    d.text((126,26),'UFO CATCHER',font=font(17),anchor='mm',fill='#9a6a8c')
    for x,y in ((18,17),(237,17),(18,238),(237,238)):
        d.ellipse((x-2,y-2,x+2,y+2),fill='#8a9da6');d.line((x-1,y,x+1,y),fill='white')
    d.rounded_rectangle((186,118,218,160),radius=4,fill='#a6b9c2');d.ellipse((194,129,210,145),fill='#d6e3e9');d.line((202,131,202,143),fill='#405464',width=2)
    d.rectangle((162,53,218,85),fill='#bdcbd0');d.rectangle((174,63,206,69),fill='#233d4b')
    for yy in range(193,219,5):d.line((67,yy,146,yy),fill='#9baab0',width=2)
    save('service',im)
    im=Image.new('RGB',(256,256),'#e7edee');d=ImageDraw.Draw(im)
    d.rectangle((4,4,251,251),outline='#bcc9cf',width=2)
    for y in range(24,149,8):d.rounded_rectangle((36,y,220,y+3),radius=1,fill='#86959d')
    d.rectangle((90,189,208,230),fill='#f9faf8');d.text((148,202),'SEGA',font=font(13),anchor='mm',fill='#3282a2');d.text((148,219),'UFO CATCHER',font=font(10),anchor='mm',fill='#637983')
    d.rectangle((27,200,54,229),fill='#566b77');d.rectangle((33,211,48,216),fill='#132c3c');save('rear',im)
    im=Image.new('RGB',(256,128),'#f3e4ee');d=ImageDraw.Draw(im)
    d.polygon([(0,78),(256,7),(256,33),(0,104)],fill='#e8bbd5')
    d.text((128,52),'UFO CATCHER',font=font(25),anchor='mm',fill='#c24b8d',stroke_width=1,stroke_fill='white')
    d.text((128,86),'COMPACT',font=font(15),anchor='mm',fill='#4d859e');save('side',im)
    im=Image.new('RGBA',(128,128),(0,0,0,0));d=ImageDraw.Draw(im)
    # Sparse edge reflections use alpha cutout rather than tinted solid glass.
    d.line((2,4,2,123),fill=(207,249,253,190),width=1)
    d.line((125,4,125,123),fill=(236,255,255,150),width=1)
    d.line((5,2,122,2),fill=(224,252,254,175),width=1)
    d.line((10,28,18,20),fill=(231,254,255,210),width=1)
    d.line((12,34,24,22),fill=(231,254,255,210),width=1);save('glass',im)
    return result

def shell_box(g,name,lo,hi,mat='white',faces=None):
    start=len(g.faces);g.box(name,lo,hi,mat)
    if faces is not None:g.faces[start:]=[f for f in g.faces[start:] if f['name'].rsplit(' ',1)[1] in faces]

def rod(g,name,a,b,r,mat):
    direction=[b[i]-a[i] for i in range(3)];n=math.sqrt(sum(v*v for v in direction));direction=[v/n for v in direction]
    ref=(0,1,0) if abs(direction[1])<.9 else (1,0,0)
    u=[direction[1]*ref[2]-direction[2]*ref[1],direction[2]*ref[0]-direction[0]*ref[2],direction[0]*ref[1]-direction[1]*ref[0]]
    n=math.sqrt(sum(v*v for v in u));u=[v/n for v in u]
    v=[direction[1]*u[2]-direction[2]*u[1],direction[2]*u[0]-direction[0]*u[2],direction[0]*u[1]-direction[1]*u[0]]
    vs=[[p[i]+r*(du*u[i]+dv*v[i]) for i in range(3)] for p in (a,b) for du,dv in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    for j,ids in enumerate([(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]):
        g.face(name+str(j),[vs[i] for i in ids],mat)

def geometry():
    g=Geometry(COLORS)
    g.group='Low white pedestal and adjustable feet'
    for x in (2.3,29.7):
        for z in (3,29):
            lathe(g,f'Rubber adjustable foot{x}-{z}',x,z,[(.68,0),(.68,.44),(.42,.55),(.25,.55),(.25,1.08)],['black','black','silver','silver'],12)
    shell_box(g,'Inset base plinth',(.95,.68,1.8),(31.05,1.4,30.6),'gray',faces=('north','south','east','west','down'))
    shell_box(g,'Main lower shell',(.60,1.35,1.68),(31.4,10.45,31.2),'white',faces=('east','west','south','down'))
    # The front is built around an actual 8x6 prize opening, never a black decal.
    shell_box(g,'Front bottom sill',(.6,1.35,.62),(31.4,2.4,1.80),'white',faces=('north','up','down','east','west'))
    shell_box(g,'Front right service fascia',(.6,2.4,.62),(21,10.45,1.8),'white',faces=('north','up','down','east','west'))
    shell_box(g,'Prize chute outer jamb',(30,2.4,.62),(31.4,10.45,1.8),'white',faces=('north','up','down','east','west'))
    shell_box(g,'Prize chute lintel',(21,8.4,.62),(30,10.45,1.8),'white',faces=('north','up','down','east','west'))
    # Enclosed chute cavity: back, bottom and inward-facing walls prevent seeing
    # through the hollow shell. Start walls behind jambs to preserve clear seams.
    shell_box(g,'Chute back',(21,2.4,6.28),(30,10.9,6.52),'dark',faces=('north',))
    shell_box(g,'Chute bottom',(21,2.39,.65),(30,2.63,6.52),'silver',faces=('up',))
    shell_box(g,'Chute inner left',(20.78,2.4,1.8),(21,10.9,6.52),'silver',faces=('east',))
    shell_box(g,'Chute inner right',(30,2.4,1.8),(30.22,10.9,6.52),'silver',faces=('west',))
    for name,lo,hi in [('left',(21,10.55,.7),(22.5,10.86,6.52)),('right',(29.5,10.55,.7),(30,10.86,6.52)),('front',(22.5,10.55,.7),(29.5,10.86,2)),('rear',(22.5,10.55,5.5),(29.5,10.86,6.52))]:
        shell_box(g,'Chute ceiling '+name,lo,hi,'silver',faces=('down',))
    for x in (20.58,30.0):shell_box(g,'Pink chute side '+str(x),(x,2.48,.42),(x+.42,8.40,.69),'pink',faces=('north','east','west'))
    shell_box(g,'Pink chute lintel',(20.58,8.40,.42),(30.42,8.90,.69),'pink',faces=('north','up','down'))
    shell_box(g,'Pink chute lower lip',(20.58,2.02,.42),(30.42,2.48,.69),'pink',faces=('north','up','down'))
    # Low partial flap leaves an unmistakable open receiving bay above it.
    plate(g,'Prize out partial flap',[(21.2,2.65),(29.8,2.65),(29.8,4.2),(21.2,4.2)],.38,.55,'pink',texture='prize_out')
    _surface(g,'Printed service access door',[(19.55,7.02,.596),(19.55,2.12,.596),(7.15,2.12,.596),(7.15,7.02,.596)],'service')
    _surface(g,'Rear vent and service label',[(5.4,9.6,31.214),(5.4,2.1,31.214),(26.6,2.1,31.214),(26.6,9.6,31.214)],'rear',normal=(0,0,1))
    for x,out in ((.588,-1),(31.412,1)):
        a,b=(3.0,28.8) if out<0 else (28.8,3.0)
        _surface(g,'Side branding'+str(x),[(x,9.4,a),(x,6.1,a),(x,6.1,b),(x,9.4,b)],'side',normal=(out,0,0))

    g.group='Prize bed with separate drop opening'
    # Floor strips meet edge-to-edge around the exact X22.5..29.5/Z2..5.5 hole.
    for name,lo,hi in [('rear',(.58,10.44,5.5),(31.42,11,31.22)),('front left',(.58,10.44,1.85),(22.5,11,5.5)),('front right',(29.5,10.44,1.85),(31.42,11,5.5)),('front lip',(22.5,10.44,1.85),(29.5,11,2))]:
        shell_box(g,'Prize floor '+name,lo,hi,'white',faces=('up','down','north','east','west','south'))
    # U-rim does not overlap its rear crossbar or the front stock pads.
    for x in (22.5,29.25):shell_box(g,'Hole rim'+str(x),(x,10.95,2.05),(x+.25,11.12,5.25),'silver')
    shell_box(g,'Hole rear rim',(22.5,10.95,5.25),(29.5,11.12,5.5),'silver')
    for slot,(x,y,z) in enumerate(PROFILE['prize_centers']):
        shell_box(g,f'Prize pad rim{slot}',(x-PAD_WIDTH/2,11,z-3.1),(x+PAD_WIDTH/2,11.13,z+3.1),'pink',faces=('up','north','south','east','west'))
        shell_box(g,f'Prize pad top{slot}',(x-PAD_WIDTH/2+.22,11.13,z-2.88),(x+PAD_WIDTH/2-.22,11.18,z+2.88),'cream',faces=('up','north','south','east','west'))

    g.group='Clear glass chamber and pastel uprights'
    for x in (.7,30.15):
        for z in (1.75,29.95):
            shell_box(g,'White corner post'+str((x,z)),(x,10.6,z),(x+1.15,28.85,z+1.05),'white',faces=('north','south','east','west'))
            shell_box(g,'Pink post front'+str((x,z)),(x+.17,11.2,z-.14),(x+.98,28.66,z+.02),'pink',faces=('north','east','west'))
            for i in (0,1):
                # Two long printed light catches, not a separate mesh per LED.
                _face(g,'Lit corner strip'+str((x,z,i)),[(x+.25+i*.56,28.3,z-.155),(x+.25+i*.56,11.6,z-.155),(x+.31+i*.56,11.6,z-.155),(x+.31+i*.56,28.3,z-.155)],'cream',normal=(0,0,-1),glow=True)
    # These glass planes are mostly empty alpha. Each side is a separate outward
    # face; there are no tinted opaque walls obscuring the live prize collection.
    def glass(name,corners,normal):
        _surface(g,name+' outer',corners,'glass',normal=normal)
        pts=[(x+normal[0]*-.012,y+normal[1]*-.012,z+normal[2]*-.012) for x,y,z in reversed(corners)]
        _surface(g,name+' inner',pts,'glass',normal=tuple(-v for v in normal))
    glass('Front clear glass',[(30.12,28.43,1.745),(30.12,11.22,1.745),(1.88,11.22,1.745),(1.88,28.43,1.745)],(0,0,-1))
    glass('Rear clear glass',[(1.88,28.43,31.018),(1.88,11.22,31.018),(30.12,11.22,31.018),(30.12,28.43,31.018)],(0,0,1))
    for x,out in ((1.36,-1),(30.64,1)):
        za,zb=(2.85,29.9) if out<0 else (29.9,2.85)
        glass('Side glass'+str(x),[(x,28.43,za),(x,11.22,za),(x,11.22,zb),(x,28.43,zb)],(out,0,0))
    for y in (16,22.0,27.7):shell_box(g,'Rear acrylic display rail'+str(y),(1.9,y,30.42),(30.1,y+.13,30.65),'silver',faces=('north','up','down'))
    shell_box(g,'Lower front pink belt',(.65,10.75,1.42),(31.35,11.23,1.80),'pink',faces=('north','up','down'))

    g.group='Rounded pink canopy and fixed gantry'
    # Shallow radius along all four canopy corners preserves the compact family
    # silhouette with a few clean planes; raised cap carries no pixel geometry.
    plate(g,'White roof case',g.roundrect(.40,29.0,31.60,31.88,1.2,n=5),.83,31.22,'white')
    plate(g,'Curved pink front canopy',g.roundrect(.26,28.36,31.74,31.98,1.25,n=6),.48,.83,'pink')
    plate(g,'White title lens',g.roundrect(1.7,28.88,30.3,31.36,.8,n=4),.455,.475,'white',texture='sign',glow=True)
    shell_box(g,'Pink side roof belt',(.39,30.6,1.1),(31.61,31.4,31.25),'pink',faces=('west','east','south'))
    shell_box(g,'White raised crown',(1.2,31.85,1.45),(30.8,31.97,30.65),'white',faces=('up','east','west','south'))
    for x in (3,28.5):shell_box(g,'Fixed longitudinal rail'+str(x),(x,28.47,2.4),(x+.50,28.77,29.1),'dark')
    for z in (5.1,28):shell_box(g,'Static ceiling tie'+str(z),(3.05,28.68,z),(28.95,28.84,z+.36),'silver')
    # Control deck has a chamfered plan outline and completely distinct LCD.
    g.group='Single-player joystick and drop controls'
    outline=[(5.2,.20),(20.3,.20),(21.0,.88),(21.0,4.40),(5.2,4.40),(4.65,3.85),(4.65,.88)]
    cy=11.35
    for i,(x,z) in enumerate(outline):
        X,Z=outline[(i+1)%len(outline)]
        _face(g,f'Control deck top{i}',[(12.8,cy,2.3),(x,cy,z),(X,cy,Z)],'white',normal=(0,1,0))
        _face(g,f'Control deck edge{i}',[(x,10.3,z),(X,10.3,Z),(X,cy,Z),(x,cy,z)],'silver',normal=(x-12.8,0,z-2.3))
        _face(g,f'Control deck bottom{i}',[(12.8,10.3,2.3),(X,10.3,Z),(x,10.3,z)],'white',normal=(0,-1,0))
    shell_box(g,'Payment plate border',(7.5,7.5,.27),(20,10.0,.47),'pink',faces=('north','up','down','east','west'))
    shell_box(g,'Payment plate',(7.70,7.70,.23),(19.8,9.80,.26),'cyan',faces=('north',))
    # Viewer-left joystick, viewer-right pink drop button, small instruction LCD.
    lathe(g,'Joystick flange',17.65,.86,[(.72,11.355),(.72,11.47),(.50,11.61),(.20,11.70)],['dark','black','silver'],20)
    lathe(g,'Joystick shaft',17.65,.86,[(.18,11.65),(.18,12.72)],['silver'],12)
    lathe(g,'Pink joystick ball',17.65,.86,[(0,12.55),(.38,12.62),(.63,12.89),(.65,13.19),(.44,13.51),(0,13.66)],['pink'],20)
    lathe(g,'Drop button socket',7.15,.86,[(.72,11.36),(.72,11.57),(.64,11.69)],['silver','dark'],24)
    lathe(g,'Pink drop button',7.15,.86,[(.62,11.64),(.62,11.80),(.53,11.96),(.24,12.07),(0,12.1)],['red'],24)
    shell_box(g,'Instruction LCD black rim',(10.0,11.35,.25),(15.3,11.48,1.58),'black',faces=('up','north','south','east','west'))
    _surface(g,'Instruction LCD',[(15.08,11.495,1.44),(15.08,11.495,.39),(10.22,11.495,.39),(10.22,11.495,1.44)],'controls',normal=(0,1,0),glow=True)
    static=g.faces[:]

    g.faces=[];g.group='Parked runtime rig (item only)'
    x,y,z=26,23,3.6;s=.85
    g.box('Moving cross rail',(3,28.1,z-.32*s),(29,28.1+.45*s,z+.32*s),'silver')
    g.box('Moving trolley',(x-2*s,28.1-1.2*s,z-1.25*s),(x+2*s,28.1+.65*s,z+1.25*s),'dark')
    g.box('Trolley pastel face',(x-1.7*s,28.1-.95*s,z-1.35*s),(x+1.7*s,28.1,z-1.23*s),'cyan')
    g.box('Hanging cable',(x-.10*s,y+3.45*s,z-.10*s),(x+.10*s,27.7,z+.10*s),'black')
    g.box('Claw chrome palm',(x-1.45*s,y+2*s,z-1.45*s),(x+1.45*s,y+3.5*s,z+1.45*s),'silver')
    g.box('Claw pink ring',(x-1.5*s,y+2.6*s,z-1.5*s),(x+1.5*s,y+2.95*s,z+1.5*s),'pink')
    for finger in range(3):
        a=math.radians(90+120*finger);dx,dz=math.cos(a),math.sin(a)
        p=lambda r,h:(x+dx*r*s,y+h*s,z+dz*r*s)
        rod(g,f'Finger{finger} upper',p(.95,2.1),p(3.1,.45),.19*s,'silver')
        rod(g,f'Finger{finger} lower',p(3.1,.45),p(2.9,-1.3),.19*s,'silver')
        rod(g,f'Finger{finger} grip',p(2.9,-1.3),p(2.45,-1.45),.25*s,'black')
    return static,g.faces

def export():
    for p in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):p.mkdir(parents=True,exist_ok=True)
    paths=textures();tex={k:'japanesearcades:block/'+ID+'_'+k for k in paths};tex['particle']=tex['materials']
    static,rig=geometry();allfaces=static+rig
    assert len({f['name'] for f in allfaces})==len(allfaces)
    for f in allfaces:
        assert 3<=len(f['vertices'])<=4 and all(math.isfinite(v) for p in f['vertices'] for v in p)
        assert all(-1e-8<=v<=16+1e-8 for p in f['uv'] for v in p),(f['name'],f['uv'])
    parts={i:[] for i in range(8)}
    for f in static:
        fragments=[list(zip(f['vertices'],f['uv']))]
        for axis in range(3):fragments=[p for poly in fragments for p in pieces(poly,axis,[16])]
        for fragment in fragments:
            for q in quads(fragment):
                center=[sum(p[i] for p,u in q)/len(q) for i in range(3)]
                ix,iy,iz=[min(1,max(0,int(c//16))) for c in center];part=ix+2*iz+4*iy
                parts[part].append({**f,'vertices':[[p[0]-ix*16,p[1]-iy*16,p[2]-iz*16] for p,u in q],'uv':[u for p,u in q]})
    def obj(path,faces,transform):
        lines=['# Compact UFO-style claw machine; static plus optional parked rig.','mtllib japanesearcades:models/block/'+ID+'.mtl'];idx=1;last=None
        for f in faces:
            mat=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
            if last!=mat:lines.append('usemtl '+mat);last=mat
            lines.extend('v '+' '.join('%.9f'%v for v in transform(p)) for p in f['vertices'])
            lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
            lines.append('f '+' '.join(f'{idx+i}/{idx+i}' for i in range(len(f['vertices']))));idx+=len(f['vertices'])
        result,stats=optimize_obj('\n'.join(lines)+'\n');path.write_text(result,encoding='utf-8')
        stats['faces']=sum(l.startswith('f ') for l in result.splitlines());stats['sha256']=hashlib.sha256(result.encode()).hexdigest();return stats
    def wrapper(name,item=False):
        out={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name+'.obj','automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':not item,'render_type':'minecraft:cutout_mipped_all','textures':tex}
        if item:out.update({'gui_light':'front','display':{'gui':{'rotation':[15,225,0],'scale':[.86,.86,.86]},'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},'fixed':{'rotation':[0,180,0],'scale':[.9,.9,.9]},'thirdperson_righthand':{'rotation':[75,45,0],'scale':[.45,.45,.45]}}})
        return out
    stats={}
    for part,faces in parts.items():
        name='block/'+ID+'_'+str(part);stats[str(part)]=obj(ASSETS/'models'/(name+'.obj'),faces,lambda p:[v/16 for v in p]);write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
    stats['item']=obj(ASSETS/'models/item'/(ID+'.obj'),allfaces,lambda p:[(p[0]*.43+1.12)/16,(p[1]*.43+.5)/16,(p[2]*.43+1.12)/16])
    write_json(ASSETS/'models/item'/(ID+'.json'),wrapper('item/'+ID,True))
    lines=[]
    for k,glow in sorted({(f['texture'][1:],f['glow']) for f in allfaces}):lines.extend(['newmtl '+k+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),'Kd 1 1 1','map_Kd #'+k,''])
    (ASSETS/'models/block'/(ID+'.mtl')).write_text('\n'.join(lines))
    write_json(ASSETS/'blockstates'/(ID+'.json'),{'variants':{'facing='+d+',part='+str(p):{'model':'japanesearcades:block/'+ID+'_'+str(p),**({'y':a} if a else {})}for d,a in [('north',0),('east',90),('south',180),('west',270)]for p in parts}})
    stats['placed_static_faces']=sum(stats[str(i)]['faces'] for i in parts);stats['moving_hardware_faces']=len(rig);stats['placed_plus_hardware_faces']=stats['placed_static_faces']+len(rig)
    stats['active_selection_faces']=24
    stats['active_cabinet_only_faces']=stats['placed_plus_hardware_faces']+24
    write_json(ART/'geometry.json',{'textures':tex,'meshes':static,'preview_meshes':rig,'metadata':PROFILE,'statistics':stats})
    # Independent editable free-mesh source contains an explicitly separate rig.
    keys=list(paths);groups=defaultdict(list);elements=[]
    for f in allfaces:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,ID+'/'+f['name']));key=f['texture'][1:];w,h=Image.open(paths[key]).size;vs=['v'+str(i) for i in range(len(f['vertices']))]
        elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],'vertices':dict(zip(vs,f['vertices'])),'faces':{'face':{'vertices':vs,'texture':keys.index(key),'uv':{n:[u*w/16,v*h/16] for n,(u,v) in zip(vs,f['uv'])}}},'visibility':True,'export':True});groups[f['group']].append(uid)
    ts=[]
    for k,p in paths.items():
        w,h=Image.open(p).size;ts.append({'name':p.name,'id':str(keys.index(k)),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,ID+'/texture/'+k)),'width':w,'height':h,'uv_width':w,'uv_height':h,'mode':'bitmap','source':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode(),'particle':k=='materials'})
    write_json(ART/(ID+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':'Compact UFO-style Claw Machine','model_identifier':ID,'resolution':{'width':256,'height':256},'elements':elements,'textures':ts,'outliner':[{'name':k,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,ID+'/group/'+k)),'origin':[16,0,16],'children':v}for k,v in groups.items()]})
    audit={'profile':PROFILE,'counts':stats,'textures':{p.name:{'size':list(Image.open(p).size),'png_bytes':p.stat().st_size}for p in paths.values()}}
    audit['texture_pixels']=sum(v['size'][0]*v['size'][1] for v in audit['textures'].values());audit['estimated_texture_bytes_with_four_mips']=sum(4*sum((v['size'][0]>>i)*(v['size'][1]>>i) for i in range(5)) for v in audit['textures'].values())
    assert all(0<n<=512 and n%16==0 for v in audit['textures'].values() for n in v['size'])
    for i,a in enumerate(PROFILE['prize_centers']):
        for b in PROFILE['prize_centers'][i+1:]:assert abs(a[0]-b[0])>=4.6 or abs(a[2]-b[2])>=4.6
        assert 1.85<a[0]-2.3<a[0]+2.3<30.15 and 1.8<a[2]-2.3<a[2]+2.3<29.95
        assert a[2]-3.1>PROFILE['chute_aperture'][3] or a[0]+3.2<PROFILE['chute_aperture'][0]
    assert stats['placed_static_faces']<2000 and stats['placed_plus_hardware_faces']<10000
    audit['checks']=['All twelve 4.6 x 4.6 x 3.4 prize envelopes separated','Every floor pad clears front chute','Final static face count below 2000','Complete geometry plus moving hardware below 10000','All textures <=512 and mip16 aligned']
    from compact_cabinet_textures import CABINETS,compact_cabinet
    CABINETS[ID]=(ID,Path(__file__).name,[ID+'_'+k for k in paths if k!='materials'])
    write_json(ART/'texture_compaction.json',compact_cabinet(ID))
    write_json(ART/'runtime_audit.json',audit)
    print(json.dumps({'static_faces':stats['placed_static_faces'],'rig_faces':len(rig),'item_faces':stats['item']['faces'],'pixels':audit['texture_pixels']},indent=2))

if __name__=='__main__':export()
