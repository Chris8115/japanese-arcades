"""Small native mesh helpers and seven-cell OBJ export for Initial D."""
import base64
import json
import math
import uuid
from collections import defaultdict

from PIL import Image
from ddr_mesh_export import pieces, quads

class Geometry:
    def __init__(self,colors):self.colors=list(colors);self.faces=[];self.group='Cabinet'
    def face(self,name,points,material='white',texture='materials',uv=None,glow=False):
        if uv is None:
            index=self.colors.index(material);u=(index%4)*4;v=(index//4)*4
            uv=[(u+1,v+1),(u+1,v+3),(u+3,v+3),(u+3,v+1)][:len(points)]
        self.faces.append({'name':name,'group':self.group,'vertices':[list(p) for p in points],
            'texture':'#'+texture,'uv':uv,'glow':glow})
    def box(self,name,lo,hi,material='white'):
        x,y,z=lo;X,Y,Z=hi;v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
        for side,ids in {'north':(3,2,1,0),'south':(4,5,6,7),'west':(0,4,7,3),
            'east':(1,2,6,5),'up':(3,7,6,2),'down':(0,1,5,4)}.items():self.face(name+' '+side,[v[i] for i in ids],material)
    def prism(self,name,outline,z0,z1,material='white',front=True,back=True):
        cx=sum(p[0] for p in outline)/len(outline);cy=sum(p[1] for p in outline)/len(outline)
        for i,p in enumerate(outline):
            q=outline[(i+1)%len(outline)]
            if front:self.face(name+' front '+str(i),[(cx,cy,z0),(*q,z0),(*p,z0)],material)
            if back:self.face(name+' back '+str(i),[(cx,cy,z1),(*p,z1),(*q,z1)],material)
            self.face(name+' edge '+str(i),[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material)
    def roundrect(self,x0,y0,x1,y1,r,n=5):
        r=min(r,(x1-x0)/2,(y1-y0)/2);out=[]
        for cx,cy,start in ((x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)):
            for i in range(n+1):
                a=math.radians(start+i*90/n);p=(cx+r*math.cos(a),cy+r*math.sin(a))
                if not out or math.dist(p,out[-1])>1e-8:out.append(p)
        if math.dist(out[0],out[-1])<1e-8:out.pop()
        return out
    def rounded(self,name,rect,z0,z1,r=.2,material='white'):
        self.prism(name,self.roundrect(*rect,r),z0,z1,material)
    def disc(self,name,x,y,r,z0,z1,material='silver',count=24):
        self.prism(name,[(x+r*math.cos(i*math.tau/count),y+r*math.sin(i*math.tau/count)) for i in range(count)],z0,z1,material)
    def decal(self,name,rect,z,texture,glow=False):
        x,y,X,Y=rect;self.face(name,[(X,Y,z),(X,y,z),(x,y,z),(x,Y,z)],texture=texture,uv=[(0,0),(0,16),(16,16),(16,0)],glow=glow)
    def tube(self,name,points,radius,material='black',segments=8):
        for k,(a,b) in enumerate(zip(points,points[1:])):
            vec=[b[i]-a[i] for i in range(3)];size=math.sqrt(sum(v*v for v in vec));n=[v/size for v in vec]
            ref=(0,1,0) if abs(n[1])<.9 else (1,0,0)
            u=[n[1]*ref[2]-n[2]*ref[1],n[2]*ref[0]-n[0]*ref[2],n[0]*ref[1]-n[1]*ref[0]]
            size=math.sqrt(sum(v*v for v in u));u=[v/size for v in u]
            v=[n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0]]
            def pt(c,t):return [c[i]+radius*(u[i]*math.cos(t)+v[i]*math.sin(t)) for i in range(3)]
            for j in range(segments):
                t=j*math.tau/segments;s=(j+1)*math.tau/segments
                self.face(name+' %d %d'%(k,j),[pt(a,t),pt(a,s),pt(b,s),pt(b,t)],material)
    def torus(self,name,cx,cy,cz,radius,tube,material='black',segments=40,rings=8):
        def pt(a,b):return (cx+(radius+tube*math.cos(b))*math.cos(a),cy+(radius+tube*math.cos(b))*math.sin(a),cz+tube*math.sin(b))
        for i in range(segments):
            a=i*math.tau/segments;A=(i+1)*math.tau/segments
            for j in range(rings):
                b=j*math.tau/rings;B=(j+1)*math.tau/rings
                self.face(name+' %d %d'%(i,j),[pt(a,b),pt(A,b),pt(A,B),pt(a,B)],material)
    def yz_shell(self,name,x0,x1,profile,material='white'):
        cy=sum(p[0] for p in profile)/len(profile);cz=sum(p[1] for p in profile)/len(profile)
        for i,(y,z) in enumerate(profile):
            Y,Z=profile[(i+1)%len(profile)]
            self.face(name+' left '+str(i),[(x0,cy,cz),(x0,Y,Z),(x0,y,z)],material)
            self.face(name+' right '+str(i),[(x1,cy,cz),(x1,y,z),(x1,Y,Z)],material)
            self.face(name+' surface '+str(i),[(x0,y,z),(x0,Y,Z),(x1,Y,Z),(x1,y,z)],material)
    def transform(self,start,fn):
        for f in self.faces[start:]:f['vertices']=[list(fn(*p)) for p in f['vertices']]

def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def export(root,g,textures,metadata):
    art=root/'art/initial_d';assets=root/'src/main/resources/assets/japanesearcades';tex=assets/'textures/block'
    sections={'cabinet_base':(0,0),'cabinet_console':(0,1),'cabinet_marquee':(0,2),
        'footwell':(1,0),'controls':(1,1),'seat_base':(2,0),'seat_back':(2,1)}
    parts={key:[] for key in sections}
    for f in g.faces:
        fragments=[list(zip(f['vertices'],f['uv']))]
        for axis,levels in ((1,[16,32]),(2,[-16,0])):fragments=[p for f0 in fragments for p in pieces(f0,axis,levels)]
        for fragment in fragments:
            for q in quads(fragment):
                y=sum(p[1] for p,uv in q)/len(q);z=sum(p[2] for p,uv in q)/len(q)
                row=min(2,int(y//16));depth=0 if z>=0 else 1 if z>=-16 else 2
                assert depth==0 or row<2,('Unknown front upper section',f['name'])
                key=('cabinet_base','cabinet_console','cabinet_marquee')[row] if depth==0 else ('footwell','controls')[row] if depth==1 else ('seat_base','seat_back')[row]
                parts[key].append({**f,'vertices':[p for p,uv in q],'uv':[uv for p,uv in q]})
    def obj(path,faces,transform):
        lines=['# Original single Initial D cabinet. Coordinates in blocks.','mtllib japanesearcades:models/block/initial_d.mtl'];idx=1;last=None
        for f in faces:
            mat=f['texture'][1:]+('_lit' if f['glow'] else '_surface')
            if mat!=last:lines.append('usemtl '+mat);last=mat
            lines.extend('v '+' '.join('%.9f'%v for v in transform(p)) for p in f['vertices'])
            lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
            lines.append('f '+' '.join('%d/%d'%(idx+i,idx+i) for i in range(len(f['vertices']))));idx+=len(f['vertices'])
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def wrapper(name):return {'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name,
        'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':True,
        'render_type':'minecraft:cutout_mipped_all','textures':textures}
    for name,faces in parts.items():
        depth,row=sections[name];path='block/initial_d_'+name
        obj(assets/'models'/(path+'.obj'),faces,lambda p,depth=depth,row=row:[p[0]/16,(p[1]-16*row)/16,(p[2]+16*depth)/16])
        write_json(assets/'models'/(path+'.json'),wrapper(path+'.obj'))
    mtl=[]
    for key,lit in sorted({(f['texture'][1:],f['glow']) for f in g.faces}):
        mtl.extend(['newmtl '+key+('_lit' if lit else '_surface'),'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1','map_Kd #'+key,''])
    (assets/'models/block/initial_d.mtl').write_text('\n'.join(mtl),encoding='utf-8')
    write_json(assets/'blockstates/initial_d.json',{'variants':{
        'facing='+direction+',section='+section:{'model':'japanesearcades:block/initial_d_'+section,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for section in sections}})
    obj(assets/'models/item/initial_d.obj',g.faces,lambda p:[((p[0]-8)*.35+8)/16,p[1]*.35/16,((p[2]+8)*.35+8)/16])
    item=wrapper('item/initial_d.obj');item.update({'ambientocclusion':False,'gui_light':'front','display':{
        'gui':{'rotation':[15,225,0],'scale':[.96,.96,.96]},'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
        'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
    write_json(assets/'models/item/initial_d.json',item)
    bounds=[[min(p[i] for f in g.faces for p in f['vertices']),max(p[i] for f in g.faces for p in f['vertices'])] for i in range(3)]
    stats={'source_faces':len(g.faces),'runtime_section_faces':{k:len(v) for k,v in parts.items()}}
    write_json(art/'geometry.json',{'textures':textures,'meshes':g.faces,'bounds':bounds,'statistics':stats,**metadata})
    specs=[(key,tex/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indices={'#'+key:i for i,(key,path) in enumerate(specs)};sizes=[Image.open(path).size for key,path in specs]
    groups=defaultdict(list);elements=[]
    assert len({f['name'] for f in g.faces})==len(g.faces),'Duplicate authoring name'
    for f in g.faces:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'initial_d/'+f['name']));index=indices[f['texture']];w,h=sizes[index];keys=['v'+str(i) for i in range(len(f['vertices']))]
        elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':index}},'visibility':True,'export':True})
        groups[f['group']].append(uid)
    texdata=[]
    for i,(key,path) in enumerate(specs):
        w,h=sizes[i];texdata.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'initial_d/'+key)),'width':w,'height':h,'uv_width':w,'uv_height':h,
            'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(art/'initial_d.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':'Initial D Stage 3 Single Cabinet',
        'model_identifier':'initial_d','visible_box':[1,3,3],'resolution':{'width':256,'height':256},'elements':elements,'textures':texdata,
        'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'initial_d/group/'+name)),'origin':[8,0,0],'children':children} for name,children in groups.items()]})
    for f in g.faces:
        assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
        assert all(.25-1e-8<=p[0]<=15.75+1e-8 and 0<=p[1]<=48 and -31.7<=p[2]<=15.7 for p in f['vertices']),(f['name'],f['vertices'])
    print('Initial D exported',stats,'bounds',bounds)
