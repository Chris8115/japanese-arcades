"""Build a one-block stackable capsule machine, using only original procedural art.

The empty poster and price plaque are filled with live item icons by the block
entity renderer.  The rotating crank is its own origin-centered baked model.
"""
import base64
import json
import math
import uuid
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/gachapon'
ASSETS = ROOT / 'src/main/resources/assets/funpackcustom'
TEX = ASSETS / 'textures/block'
for p in (ART, TEX, ASSETS/'models/block', ASSETS/'models/item', ASSETS/'blockstates'):
    p.mkdir(parents=True, exist_ok=True)

COLORS = {
    'white':'#f4f3ea', 'ivory':'#dcded8', 'edge':'#bdc7c9', 'blue':'#153eb1',
    'yellow':'#f6df26', 'chrome':'#c6cdd3', 'dark':'#252d36', 'black':'#0e141b',
    'glass':'#d2e5ed', 'reflection':'#f5fbfc', 'pink':'#ee5e99', 'mint':'#59c7b5',
    'gold':'#f4c953', 'lilac':'#b69ed9', 'poster':'#f2f4ed', 'red':'#cc3e44',
}
KEYS = list(COLORS)
atlas=Image.new('RGBA',(256,256))
d=ImageDraw.Draw(atlas)
for i,(name,color) in enumerate(COLORS.items()):
    x,y=(i%4)*64,(i//4)*64
    d.rectangle((x,y,x+63,y+63),fill=color)
atlas.save(TEX/'gachapon_materials.png')

def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)

# Decals are hand-authored utility graphics, not third-party downloaded artwork.
decals=Image.new('RGBA',(1024,1024),(242,243,235,255));dd=ImageDraw.Draw(decals)
dd.rounded_rectangle((12,10,1012,156),radius=35,fill='#1547a2')
dd.text((512,82),'CAPSULE STATION',font=font(85,True),anchor='mm',fill='#ffffff')
dd.line((64,175,960,175),fill='#b8ccd3',width=7)
dd.text((512,258),'TURN TO PLAY',font=font(70,True),anchor='mm',fill='#304660')
dd.text((512,340),'HOLD RIGHT CLICK',font=font(46,True),anchor='mm',fill='#5a6b74')
dd.rounded_rectangle((40,420,984,545),radius=18,fill='#ead43b')
dd.text((512,482),'COLLECT YOUR CAPSULE',font=font(51,True),anchor='mm',fill='#29313d')
dd.text((512,640),'PRIZES',font=font(86,True),anchor='mm',fill='#304660')
dd.text((512,780),'RETURN',font=font(62,True),anchor='mm',fill='#173fab')
dd.line((75,915,950,915),fill='#849baf',width=6)
for i in range(7):
    dd.ellipse((385+i*37,945,399+i*37,959),fill='#748795')
decals.save(TEX/'gachapon_details.png')
textures={'materials':'funpackcustom:block/gachapon_materials',
          'details':'funpackcustom:block/gachapon_details',
          'particle':'funpackcustom:block/gachapon_materials'}

surfaces=[]
group='Shell'
assembly='body'

def tile(material):
    i=KEYS.index(material);u=(i%4)*4;v=(i//4)*4
    return [(u+1,v+1),(u+1,v+3),(u+3,v+3),(u+3,v+1)]

def face(name,points,material='white',texture='materials',uv=None):
    if uv is None: uv=tile(material)[:len(points)]
    surfaces.append({'name':name,'group':group,'assembly':assembly,'texture':'#'+texture,
                     'glow':False,'vertices':[list(p) for p in points],'uv':uv})

def box(name,lo,hi,material='white'):
    x,y,z=lo;X,Y,Z=hi
    v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for side,ids in {'north':(3,2,1,0),'south':(4,5,6,7),'west':(0,4,7,3),
                     'east':(1,2,6,5),'up':(3,7,6,2),'down':(0,1,5,4)}.items():
        face(name+' '+side,[v[i] for i in ids],material)

def roundrect(x0,y0,x1,y1,r,segments=5):
    r=min(r,(x1-x0)/2,(y1-y0)/2)
    points=[]
    for cx,cy,start in ((x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)):
        for i in range(segments+1):
            a=math.radians(start+i*90/segments)
            point=(cx+r*math.cos(a),cy+r*math.sin(a))
            if not points or math.dist(point,points[-1])>1e-10:points.append(point)
    if math.dist(points[0],points[-1])<1e-10:points.pop()
    return points

def prism(name,outline,z0,z1,material='white',front=True,back=True):
    cx=sum(p[0] for p in outline)/len(outline);cy=sum(p[1] for p in outline)/len(outline)
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        if front: face(name+' front '+str(i),[(cx,cy,z0),(*q,z0),(*p,z0)],material)
        if back: face(name+' back '+str(i),[(cx,cy,z1),(*p,z1),(*q,z1)],material)
        face(name+' edge '+str(i),[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material)

def rounded(name,rect,z0,z1,r=.25,material='white'):
    prism(name,roundrect(*rect,r),z0,z1,material)

def circle(cx,cy,r,count=48):
    return [(cx+r*math.cos(i*math.tau/count),cy+r*math.sin(i*math.tau/count)) for i in range(count)]

def disc(name,cx,cy,r,z0,z1,material='white',count=48):
    prism(name,circle(cx,cy,r,count),z0,z1,material)

def ring(name,cx,cy,outer,inner,z,material='white',count=64):
    a=circle(cx,cy,outer,count);b=circle(cx,cy,inner,count)
    for i in range(count):
        j=(i+1)%count
        face(name+' '+str(i),[(*a[i],z),(*b[i],z),(*b[j],z),(*a[j],z)],material)

def arc(name,cx,cy,r0,r1,z,start,end,material='yellow'):
    count=max(3,int(abs(end-start)/7))
    for i in range(count):
        a=math.radians(start+(end-start)*i/count);b=math.radians(start+(end-start)*(i+1)/count)
        face(name+str(i),[(cx+r1*math.cos(a),cy+r1*math.sin(a),z),
                          (cx+r0*math.cos(a),cy+r0*math.sin(a),z),
                          (cx+r0*math.cos(b),cy+r0*math.sin(b),z),
                          (cx+r1*math.cos(b),cy+r1*math.sin(b),z)],material)

def decal(name,rect,z,region):
    x0,y0,x1,y1=rect;u0,v0,u1,v1=region
    # +X is the viewer's left for a north-facing machine.
    face(name,[(x1,y1,z),(x1,y0,z),(x0,y0,z),(x0,y1,z)],texture='details',
         uv=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)])

def sphere(name,center,r,top='glass',bottom='pink',segments=20,rings=10):
    cx,cy,cz=center
    for j in range(rings):
        a=-math.pi/2+math.pi*j/rings;b=-math.pi/2+math.pi*(j+1)/rings
        for i in range(segments):
            t=i*math.tau/segments;u=(i+1)*math.tau/segments
            def pt(lat,lon):return (cx+r*math.cos(lat)*math.cos(lon),cy+r*math.sin(lat),cz+r*math.cos(lat)*math.sin(lon))
            pts=[pt(a,t),pt(b,t),pt(b,u),pt(a,u)]
            if j==0:pts=pts[1:]
            elif j==rings-1:pts=[pts[0],pts[1],pts[3]]
            face(name+' %d %d'%(j,i),pts,top if j>=rings//2 else bottom)

# Every physical surface lies inside one block, with flush mating planes at Y0/16.
rounded('Continuous white rear casing',(.3,.0,15.7,15.70),3.45,15.65,.52,'white')
rounded('Flat stackable foot',(.22,0,15.78,.65),.9,15.72,.22,'ivory')
rounded('Thin base rim',(.22,.52,15.78,.77),.75,15.72,.12,'white')
rounded('Stacking cap',(.22,15.45,15.78,16),.78,15.72,.20,'white')
decal('Capsule station top badge',(4.72,15.53,11.28,15.96),.768,(0,.10,16,2.47))
rounded('Cap fine inset seam',(.34,15.39,15.66,15.45),1.05,15.51,.12,'edge')
rounded('Lower molded control shell',(.4,.64,15.6,8.55),1.08,4.0,.75,'white')

group='Glass chamber'
# Concave chamber corners, thin molded perimeter, clear center; render icons in
# front of the pale internal poster rather than behind a sorting-prone glass quad.
rounded('Chamber back wall',(.73,8.04,15.27,15.43),3.22,3.5,.50,'ivory')
rounded('Poster tray', (2.06,8.83,13.94,15.12),1.63,2.98,.22,'edge')
rounded('Blank live prize poster',(2.25,9.05,13.75,14.95),1.60,1.64,.18,'poster')
for x in (1.00,15.00):
    box('Thin clear side stile '+str(x),(x-.12,8.84,1.33),(x+.12,15.43,3.24),'glass')
    box('White glass edge highlight '+str(x),(x-.105,10.15,1.29),(x-.065,15.30,1.35),'reflection')
box('Clear top flange',(1.0,15.19,1.27),(15.0,15.39,3.26),'glass')
box('White top highlight',(1.08,15.34,1.23),(14.92,15.39,1.32),'reflection')
# Rounded bottom front of the chamber, mirrored sides and a low clear lip.
for cx,start in ((2.4,180),(13.6,270)):
    for i in range(9):
        a=math.radians(start+i*10);b=math.radians(start+(i+1)*10)
        face('Glass lower curved corner %s %s'%(cx,i),[(cx+1.40*math.cos(a),9.43+1.40*math.sin(a),1.32),
             (cx+1.22*math.cos(a),9.43+1.22*math.sin(a),1.32),
             (cx+1.22*math.cos(b),9.43+1.22*math.sin(b),1.32),
             (cx+1.40*math.cos(b),9.43+1.40*math.sin(b),1.32)],'glass')
box('Clear bottom lip',(2.4,8.04,1.32),(13.6,8.23,3.20),'glass')
box('Molded capsule hopper',(2.23,8.07,2.30),(13.77,8.41,3.43),'ivory')
for i,(x,col) in enumerate(((2.0,'pink'),(5.2,'gold'),(10.7,'mint'),(14.1,'lilac'))):
    sphere('Visible stock capsule '+str(i),(x,8.61,2.64),.61,'glass',col,16,8)
for x in (1.1,14.9):
    disc('Glass fixing screw '+str(x),x,15.05,.105,1.20,1.32,'chrome',16)

group='Operator controls'
rounded('Blank blue price plaque',(11.05,6.45,15.05,7.66),.99,1.10,.38,'blue')
disc('Dial blue outer surround',8.2,5.0,2.13,.86,1.15,'blue')
ring('Yellow outer dial band',8.2,5,1.99,1.91,.844,'yellow')
ring('Fine white inner dial band',8.2,5,1.73,1.69,.839,'white')
arc('Turning direction upper',8.2,5,1.79,1.86,.832,48,138)
arc('Turning direction lower',8.2,5,1.79,1.86,.832,226,308)
for i,(x,y) in enumerate(((6.58,5.88),(9.82,4.11))):
    face('Dial yellow arrow '+str(i),[(x-.18,y+.20,.82),(x+.21,y,.82),(x-.18,y-.20,.82)],'yellow')
for angle in (157,166,175,337,346,355):
    a=math.radians(angle);disc('Dial marker '+str(angle),8.2+1.83*math.cos(a),5+1.83*math.sin(a),.065,.823,.845,'yellow',12)

disc('Coin entry outer rim',3.65,6.78,.74,.81,1.11,'chrome')
disc('Coin entry white inset',3.65,6.78,.61,.775,.83,'ivory')
rounded('Coin insertion slot',(3.54,6.27,3.76,7.29),.758,.80,.08,'dark')
rounded('Return instruction blue label',(1.10,5.37,2.28,6.91),.975,1.09,.32,'blue')
arc('Return arrow',1.71,5.98,.25,.33,.96,20,300,'yellow')
face('Return arrow head',[(1.9,5.68,.95),(1.57,5.69,.95),(1.77,5.94,.95)],'yellow')
disc('Coin return push button',3.2,5.57,.22,.67,1.04,'ivory',24)
disc('Operator keyed lock rim',3.29,4.19,.48,.81,1.10,'chrome',32)
disc('Operator lock face',3.29,4.19,.33,.785,.85,'ivory',24)
box('Keyhole slit',(3.24,3.99,.768),(3.34,4.39,.79),'dark')
decal('Small control direction caption',(10.95,4.80,14.97,5.50),1.062,(0,3.05,16,5.83))

group='Collection tray'
# A recessed circular mouth with a true hollow tunnel and shaped catch apron.
cx,cy=10.62,2.27
disc('Outlet dark recess',cx,cy,1.26,1.018,1.10,'black')
ring('Outlet smooth white rolled rim',cx,cy,1.45,1.28,.92,'ivory')
ring('Outlet thin reflective rim',cx,cy,1.29,1.21,.905,'chrome')
disc('Outlet inside bottom shade',cx,cy-.36,.77,.975,1.01,'dark',32)
# Apron cross-section in Y/Z, expanded to left/right without obstructing mouth.
profile=[(.71,.29),(.74,1.22),(1.59,1.34),(1.17,.63)]
for x0,x1,name in ((8.68,12.67,'Capsule catch apron'),(2.56,5.62,'Coin return apron')):
    for i,(y,z) in enumerate(profile):
        Y,Z=profile[(i+1)%len(profile)]
        face(name+' slope '+str(i),[(x0,y,z),(x1,y,z),(x1,Y,Z),(x0,Y,Z)],'white' if i!=1 else 'ivory')
    for x,rev in ((x0,False),(x1,True)):
        points=[(x,y,z) for y,z in profile]
        face(name+' side '+str(x),points[::-1] if rev else points,'white')
rounded('Coin return recess',(3.02,1.45,4.67,2.91),1.021,1.10,.22,'edge')
rounded('Coin return dark inner pocket',(3.24,1.60,4.45,2.70),1.005,1.023,.15,'ivory')
box('Coin return back shade',(3.39,2.18,.994),(4.28,2.58,1.025),'edge')
decal('Collection yellow instruction',(7.82,.83,14.90,1.18),.302,(0,6.55,16,8.56))

group='Rear and side detailing'
rounded('Rear removable access door',(1.05,1.04,14.95,14.92),15.64,15.72,.36,'ivory')
for y in (1.48,14.48):
    for x in (1.62,14.38):
        # rear screw heads may be seen in paired back view
        box('Rear screw %s %s'%(x,y),(x-.10,y-.10,15.72),(x+.10,y+.10,15.78),'chrome')
for i in range(8):
    box('Rear cooling slots '+str(i),(5.18+i*.72,2.30,15.724),(5.50+i*.72,4.14,15.76),'edge')
# Thin top bearing surface joins vertically stacked copies without feet or gaps.
for x in (.70,15.16):
    box('Side case join '+str(x),(x,1.10,8.0),(x+.05,14.96,8.045),'ivory')

body=list(surfaces)
surfaces=[];assembly='crank';group='Turning crank'
disc('Crank seated white disc',0,0,1.64,-.32,.0,'ivory')
disc('Crank front cap',0,0,1.50,-.44,-.31,'white')
# A broad rounded molded grip, giving the real white butterfly/crank silhouette.
rounded('Molded horizontal turning handle',(-1.40,-.31,1.40,.31),-.89,-.41,.25,'white')
box('Handle lower bevel',(-1.14,-.30,-.87),(1.14,-.23,-.41),'ivory')
face('Yellow handle pointer',[(.70,.17,-.904),(1.08,.0,-.904),(.70,-.17,-.904)],'yellow')
crank=list(surfaces)
combined=body+[{**f,'vertices':[[x+8.2,y+5,z+1] for x,y,z in f['vertices']]} for f in crank]

surfaces=[];assembly='capsule';group='Capsule item'
sphere('Openable capsule',(8,8,8),5.2,'glass','pink',32,16)
# Narrow equatorial rim in horizontal XZ plane.
for i in range(32):
    a=math.tau*i/32;b=math.tau*(i+1)/32
    face('Capsule seam '+str(i),[(8+5.24*math.cos(a),7.85,8+5.24*math.sin(a)),
         (8+5.24*math.cos(a),8.15,8+5.24*math.sin(a)),
         (8+5.24*math.cos(b),8.15,8+5.24*math.sin(b)),
         (8+5.24*math.cos(b),7.85,8+5.24*math.sin(b))],'white')
capsule=list(surfaces)

def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def obj(path,faces):
    lines=['# Original stackable Gachapon model; one coordinate unit is one block.',
           'mtllib funpackcustom:models/block/gachapon.mtl'];index=1;material=None
    for f in faces:
        mat=f['texture'][1:]+'_surface'
        if mat!=material:lines.append('usemtl '+mat);material=mat
        lines.extend('v '+' '.join('%.8f'%(v/16) for v in p) for p in f['vertices'])
        lines.extend('vt %.8f %.8f'%(u/16,1-v/16) for u,v in f['uv'])
        lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
        index+=len(f['vertices'])
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def wrapper(model,item=False):
    model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'funpackcustom:models/'+model,
           'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
           'ambientocclusion':not item,'render_type':'minecraft:cutout_mipped_all','textures':textures}
    if item:model.update({'gui_light':'front','display':{
        'gui':{'rotation':[15,225,0],'scale':[.8,.8,.8]},
        'ground':{'translation':[0,2,0],'scale':[.5,.5,.5]},
        'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.38,.38,.38]},
        'firstperson_righthand':{'rotation':[0,45,0],'scale':[.55,.55,.55]}}})
    return model

for name,faces,item in (('block/gachapon',body,False),('block/gachapon_crank',crank,False),
                         ('item/gachapon',combined,True),('item/gachapon_capsule',capsule,True)):
    obj(ASSETS/'models'/(name+'.obj'),faces)
    write_json(ASSETS/'models'/(name+'.json'),wrapper(name+'.obj',item))
(ASSETS/'models/block/gachapon.mtl').write_text('newmtl materials_surface\nKa 0 0 0\nKd 1 1 1\nmap_Kd #materials\n\nnewmtl details_surface\nKa 0 0 0\nKd 1 1 1\nmap_Kd #details\n',encoding='utf-8')
write_json(ASSETS/'blockstates/gachapon.json',{'variants':{
    'facing='+f:{'model':'funpackcustom:block/gachapon',**({'y':r} if r else {})}
    for f,r in (('north',0),('east',90),('south',180),('west',270))}})
write_json(ART/'geometry.json',{'textures':textures,'meshes':combined,'capsule_meshes':capsule,
    'anchors':{'dial':[8.2,5,1],'price':[13.05,7,.94],
       'prize_x':[11.9,8,4.1],'prize_y':[13.72,11.75,9.78],'prize_z':1.48,'prize_size':1.55},
    'statistics':{'body_faces':len(body),'crank_faces':len(crank),'capsule_faces':len(capsule)},
    'notes':'1x1x1 block; live item icons and amount text are drawn by the block entity renderer.'})

groups=defaultdict(list);elements=[]
assert len({f['name'] for f in combined})==len(combined),'Duplicate authoring mesh names'
for f in combined:
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'gachapon/'+f['name']))
    texture_index=0 if f['texture']=='#materials' else 1;size=256 if texture_index==0 else 1024
    keys=['v'+str(i) for i in range(len(f['vertices']))]
    elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
        'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
          'uv':{k:[u*size/16,v*size/16] for k,(u,v) in zip(keys,f['uv'])},'texture':texture_index}},
        'visibility':True,'export':True})
    groups[f['group']].append(uid)
bbtex=[]
for i,(key,size) in enumerate((('materials',256),('details',1024))):
    p=TEX/('gachapon_'+key+'.png')
    bbtex.append({'name':p.name,'folder':'block','namespace':'funpackcustom','id':str(i),
        'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'gachapon/'+key)),'width':size,'height':size,
        'uv_width':size,'uv_height':size,'source':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode(),
        'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
write_json(ART/'gachapon.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
    'name':'Stackable Gachapon','model_identifier':'gachapon','visible_box':[1,1,1],
    'resolution':{'width':256,'height':256},'elements':elements,'textures':bbtex,
    'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'gachapon/group/'+name)),
       'origin':[8,0,8],'children':children} for name,children in groups.items()]})
for f in combined:
    assert len(f['vertices']) in (3,4),f['name']
    assert len(f['vertices'])==len(f['uv']),f['name']
    assert all(-.001<=v<=16.001 for p in f['vertices'] for v in p),(f['name'],f['vertices'])
    if f['name'].startswith(('Dial yellow arrow','Yellow handle pointer','Return arrow head')):
        a,b,c=f['vertices'][:3]
        normal_z=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        assert normal_z<0,('Front decal points away from north-facing viewer',f['name'])
print('Exported body/crank/capsule faces:',len(body),len(crank),len(capsule))
