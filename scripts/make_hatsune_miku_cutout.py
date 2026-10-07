"""Bake an immutable RGBA print into a lightweight two-block cardboard cutout.

The source PNG is copied byte-for-byte. Its alpha is sampled only to construct
the coarse cardboard silhouette, never to repaint or rewrite the artwork.
Rotation follows standing signs: 0 south, 4 west, 8 north, 12 east.
"""
import argparse
import base64
import copy
import hashlib
import json
import math
import random
import uuid
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
ART=ROOT/'art/hatsune_miku_cutout'
NAME='hatsune_miku_cutout'
Z_BACK,Z_FRONT=7.68,8.32
TEXTURES={'print':'funpackcustom:block/'+NAME+'_print',
          'cardboard':'funpackcustom:block/'+NAME+'_cardboard',
          'particle':'funpackcustom:block/'+NAME+'_cardboard'}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


class Geometry:
    def __init__(self):self.faces=[]

    def face(self,name,vertices,texture='cardboard',uv=None,group='Cardboard'):
        if uv is None:uv=[[.5,.5],[.5,7.5],[7.5,7.5],[7.5,.5]][:len(vertices)]
        self.faces.append({'name':name,'group':group,'vertices':[list(p) for p in vertices],
                           'texture':'#'+texture,'uv':uv,'glow':False})

    def box(self,name,a,b,group='Folded rear support'):
        x0,y0,z0=a;x1,y1,z1=b
        sides={
            'front':[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
            'back':[(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
            'left':[(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
            'right':[(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],
            'top':[(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0)],
            'bottom':[(x0,y0,z1),(x0,y0,z0),(x1,y0,z0),(x1,y0,z1)]}
        for side,points in sides.items():self.face(name+' '+side,points,group=group)


def cardboard_texture():
    """New procedural kraft material; no source artwork pixels are changed."""
    rng=random.Random(12039)
    im=Image.new('RGB',(256,256),'#ac8556')
    px=im.load()
    for y in range(128):
        for x in range(128):
            n=rng.randrange(-5,6)
            px[x,y]=(max(0,185+n),max(0,149+n),max(0,103+n))
    d=ImageDraw.Draw(im)
    for x in range(128,256):
        d.line((x,0,x,127),fill=('#8e653e' if x%8<2 else '#c09b65'))
    d.rectangle((0,128,127,255),fill='#a47c4e')
    d.rectangle((128,128,255,255),fill='#765537')
    path=ASSETS/'textures/block'/(NAME+'_cardboard.png')
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path)


def rectangles(mask):
    """Greedy disjoint rectangles cover the back without tiny coplanar cubes."""
    rows,cols=len(mask),len(mask[0]); remaining=[row[:] for row in mask]
    output=[]
    for y in range(rows):
        for x in range(cols):
            if not remaining[y][x]:continue
            x1=x+1
            while x1<cols and remaining[y][x1]:x1+=1
            y1=y+1
            while y1<rows and all(remaining[y1][xx] for xx in range(x,x1)):y1+=1
            for yy in range(y,y1):
                for xx in range(x,x1):remaining[yy][xx]=False
            output.append((x,y,x1,y1))
    return output


def boundary_runs(mask):
    """Merge adjacent collinear outline segments into one extruded edge quad."""
    rows,cols=len(mask),len(mask[0]); runs=defaultdict(list)
    for y in range(rows):
        for x in range(cols):
            if not mask[y][x]:continue
            if x==0 or not mask[y][x-1]:runs[('left',x)].append(y)
            if x==cols-1 or not mask[y][x+1]:runs[('right',x+1)].append(y)
            if y==0 or not mask[y-1][x]:runs[('top',y)].append(x)
            if y==rows-1 or not mask[y+1][x]:runs[('bottom',y+1)].append(x)
    result=[]
    for (side,fixed),values in sorted(runs.items()):
        start=last=values[0]
        for value in values[1:]:
            if value==last+1:last=value
            else:result.append((side,fixed,start,last+1));start=last=value
        result.append((side,fixed,start,last+1))
    return result


def silhouette(source,grid_width):
    im=Image.open(source).convert('RGBA')
    alpha=im.getchannel('A')
    cutoff=alpha.point(lambda a:255 if a>=128 else 0)
    bbox=cutoff.getbbox()
    if bbox is None:raise ValueError('The print PNG has no opaque artwork')
    if cutoff.getextrema()==(255,255):raise ValueError('The print requires a transparent silhouette, not a rectangular opaque background')
    left,top,right,bottom=bbox
    art_w,art_h=right-left,bottom-top
    scale=min(15.2/art_w,29.4/art_h)
    width,height=art_w*scale,art_h*scale
    x0=8-width/2;y0=1.0;y1=y0+height
    rows=max(2,round(grid_width*art_h/art_w))
    sampled=cutoff.crop(bbox).resize((grid_width,rows),Image.Resampling.BOX)
    mask=[[sampled.getpixel((x,y))>=96 for x in range(grid_width)] for y in range(rows)]
    def xx(x):return x0+x/grid_width*width
    def yy(y):return y1-y/rows*height
    g=Geometry()
    # Full-resolution artwork appears exactly once. Its alpha retains detail
    # finer than the intentionally economical physical cardboard perimeter.
    u0,v0,u1,v1=left/im.width*16,top/im.height*16,right/im.width*16,bottom/im.height*16
    g.face('Original printed silhouette',[(x0,y0,Z_FRONT),(x0+width,y0,Z_FRONT),
        (x0+width,y1,Z_FRONT),(x0,y1,Z_FRONT)],'print',
        [[u0,v1],[u1,v1],[u1,v0],[u0,v0]],'Immutable front print')
    rects=rectangles(mask)
    for index,(a,b,c,d) in enumerate(rects):
        g.face('Kraft back '+str(index),[(xx(c),yy(d),Z_BACK),(xx(a),yy(d),Z_BACK),
            (xx(a),yy(b),Z_BACK),(xx(c),yy(b),Z_BACK)],
            uv=[[c/grid_width*8,d/rows*8],[a/grid_width*8,d/rows*8],
                [a/grid_width*8,b/rows*8],[c/grid_width*8,b/rows*8]],group='Kraft silhouette back')
    edges=boundary_runs(mask)
    for index,(side,fixed,a,b) in enumerate(edges):
        if side=='left':
            vertices=[(xx(fixed),yy(b),Z_FRONT),(xx(fixed),yy(a),Z_FRONT),
                      (xx(fixed),yy(a),Z_BACK),(xx(fixed),yy(b),Z_BACK)]
        elif side=='right':
            vertices=[(xx(fixed),yy(b),Z_BACK),(xx(fixed),yy(a),Z_BACK),
                      (xx(fixed),yy(a),Z_FRONT),(xx(fixed),yy(b),Z_FRONT)]
        elif side=='top':
            vertices=[(xx(a),yy(fixed),Z_BACK),(xx(a),yy(fixed),Z_FRONT),
                      (xx(b),yy(fixed),Z_FRONT),(xx(b),yy(fixed),Z_BACK)]
        else:
            vertices=[(xx(a),yy(fixed),Z_FRONT),(xx(a),yy(fixed),Z_BACK),
                      (xx(b),yy(fixed),Z_BACK),(xx(b),yy(fixed),Z_FRONT)]
        g.face('Corrugated edge '+str(index),vertices,uv=[[8.25,.25],[8.25,7.75],
                [15.75,7.75],[15.75,.25]],group='Die-cut cardboard edges')
    return g,{'source_size':[im.width,im.height],'alpha_bbox_pixels':list(bbox),
        'grid':[grid_width,rows],'back_rectangles':len(rects),'outline_edge_quads':len(edges),
        'art_width_model_units':width,'art_height_model_units':height,
        'top_model_units':y1,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}


def support(g):
    g.box('Low cardboard display foot',(3.6,0,4.8),(12.4,.42,11.2),'Cardboard foot')
    g.box('Front folded tab',(5.65,.42,7.72),(10.35,1.03,8.5),'Cardboard foot')
    g.box('Rear folded tab',(5.8,.42,4.8),(10.2,.74,6.2))
    # A narrow, slanted, closed cardboard strut behind the character.
    a,b,c,d=(6.7,.74,4.96),(9.3,.74,4.96),(9.3,14.0,7.5),(6.7,14.0,7.5)
    e,f,h,i=(6.7,.74,5.16),(9.3,.74,5.16),(9.3,14.0,7.7),(6.7,14.0,7.7)
    for name,points in [('back',[a,d,c,b]),('front',[e,f,h,i]),('left',[a,e,i,d]),
                        ('right',[b,c,h,f]),('top',[d,i,h,c]),('bottom',[a,b,f,e])]:
        g.face('Folded easel '+name,points,group='Folded rear support')
    g.box('Scored upper hinge',(6.5,13.72,7.42),(9.5,14.12,7.7))


def clip_face(face,bound,keep_above):
    points=list(zip(face['vertices'],face['uv']));result=[]
    def inside(p):return p[1]>=bound-1e-9 if keep_above else p[1]<=bound+1e-9
    for index,(current,uv) in enumerate(points):
        previous,prev_uv=points[index-1]
        old,new=inside(previous),inside(current)
        if old!=new:
            amount=(bound-previous[1])/(current[1]-previous[1])
            p=[previous[i]+amount*(current[i]-previous[i]) for i in range(3)]
            q=[prev_uv[i]+amount*(uv[i]-prev_uv[i]) for i in range(2)]
            result.append((p,q))
        if new:result.append((current,uv))
    if len(result)<3:return None
    # Exclude boundary-only degenerate polygons.
    a,b,c=[p for p,uv in result[:3]]
    ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
    cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
    if sum(v*v for v in cross)<1e-14:return None
    assert len(result)<=4,(face['name'],len(result))
    out=copy.deepcopy(face)
    out['vertices']=[list(p) for p,uv in result];out['uv']=[list(uv) for p,uv in result]
    return out


def sliced(faces,half):
    output=[]
    for face in faces:
        result=clip_face(face,16,half=='upper')
        if result:
            if half=='upper':
                for point in result['vertices']:point[1]-=16
            output.append(result)
    return output


def rotated(faces,rotation):
    theta=math.pi*rotation/8;c,s=math.cos(theta),math.sin(theta)
    output=copy.deepcopy(faces)
    for face in output:
        for point in face['vertices']:
            x,z=point[0]-8,point[2]-8
            point[0]=8+c*x-s*z;point[2]=8+s*x+c*z
    return output


def bounds(faces):
    return [[round(min(p[i] for f in faces for p in f['vertices']),8),
             round(max(p[i] for f in faces for p in f['vertices']),8)] for i in range(3)]


def obj(name,faces):
    lines=['# Static Minecraft-style Miku cardboard display','mtllib funpackcustom:models/block/'+NAME+'.mtl']
    index=1;previous=None
    for face in faces:
        material=face['texture'][1:]+'_surface'
        if material!=previous:lines.append('usemtl '+material);previous=material
        lines.extend('v '+' '.join(f'{v/16:.9f}' for v in point) for point in face['vertices'])
        lines.extend(f'vt {u/16:.9f} {1-v/16:.9f}' for u,v in face['uv'])
        lines.append('f '+' '.join(f'{index+i}/{index+i}' for i in range(len(face['vertices']))))
        index+=len(face['vertices'])
    path=ASSETS/'models/block'/(name+'.obj')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    model={'parent':'minecraft:block/block','loader':'neoforge:obj',
        'model':'funpackcustom:models/block/'+name+'.obj','automatic_culling':False,
        'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':True,
        'render_type':'minecraft:cutout_mipped_all','textures':TEXTURES}
    write(ASSETS/'models/block'/(name+'.json'),model)
    return model


def editable(faces):
    textures=[];indices={}
    for key in ('print','cardboard'):
        path=ASSETS/'textures/block'/(NAME+'_'+key+'.png');w,h=Image.open(path).size
        indices[key]=len(textures)
        textures.append({'name':path.name,'id':str(len(textures)),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/'+key)),
            'width':w,'height':h,'uv_width':w,'uv_height':h,
            'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
            'mode':'bitmap','visible':True})
    elements=[];groups=defaultdict(list)
    for face in faces:
        keys=['v'+str(i) for i in range(len(face['vertices']))]
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/'+face['name']))
        index=indices[face['texture'][1:]];w,h=textures[index]['width'],textures[index]['height']
        elements.append({'name':face['name'],'type':'mesh','uuid':uid,'origin':[8,0,8],
            'rotation':[0,0,0],'vertices':dict(zip(keys,face['vertices'])),
            'faces':{'face':{'vertices':keys,'uv':{key:[u*w/16,v*h/16]
                for key,(u,v) in zip(keys,face['uv'])},'texture':index}},'visibility':True,'export':True})
        groups[face['group']].append(uid)
    write(ART/(NAME+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'Hatsune Miku Cardboard Cutout','resolution':{'width':256,'height':256},
        'elements':elements,'textures':textures,'outliner':[{'name':group,
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/group/'+group)),
            'origin':[8,0,8],'children':children} for group,children in groups.items()]})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ART/'miku-cutout-print.png')
    parser.add_argument('--grid-width',type=int,default=48)
    args=parser.parse_args()
    if not args.source.exists():raise FileNotFoundError('Waiting for immutable source artwork: '+str(args.source))
    if not 16<=args.grid_width<=128:raise ValueError('--grid-width must be16..128')
    ART.mkdir(parents=True,exist_ok=True)
    g,analysis=silhouette(args.source,args.grid_width)
    support(g)
    lower,upper=sliced(g.faces,'lower'),sliced(g.faces,'upper')
    placed_faces=len(lower)+len(upper)
    assert placed_faces<1000,('Reduce --grid-width: complete placed face budget',placed_faces)
    assert len({f['name'] for f in g.faces})==len(g.faces)
    assert all(0<=u<=16 for f in g.faces for uv in f['uv'] for u in uv)
    texture=ASSETS/'textures/block'/(NAME+'_print.png')
    texture.parent.mkdir(parents=True,exist_ok=True);texture.write_bytes(args.source.read_bytes())
    cardboard_texture()
    model_dir=ASSETS/'models/block';model_dir.mkdir(parents=True,exist_ok=True)
    mtl=[]
    for key in ('print','cardboard'):
        mtl.extend(['newmtl '+key+'_surface','Ka 0 0 0','Kd 1 1 1','map_Kd #'+key,''])
    (model_dir/(NAME+'.mtl')).write_text('\n'.join(mtl),encoding='utf-8')
    whole=obj(NAME,g.faces)
    center_above_block=analysis['top_model_units']/2-8
    whole.update({'ambientocclusion':False,'gui_light':'front','display':{
        'gui':{'rotation':[8,-15,0],'translation':[0,-center_above_block*.56*math.cos(math.radians(8)),0],'scale':[.56,.56,.56]},
        'ground':{'translation':[0,2,0],'scale':[.4,.4,.4]},
        'fixed':{'translation':[0,-center_above_block*.5,0],'scale':[.5,.5,.5]},
        'thirdperson_righthand':{'rotation':[0,0,0],'translation':[0,1,0],'scale':[.35,.35,.35]},
        'firstperson_righthand':{'rotation':[0,-20,0],'translation':[0,-1,0],'scale':[.42,.42,.42]}}})
    write(ASSETS/'models/item'/(NAME+'.json'),whole)
    variants={};audit=[]
    for rotation in range(16):
        for half,faces in (('lower',lower),('upper',upper)):
            name=f'{NAME}_{half}_{rotation:02}'
            turned=rotated(faces,rotation);box=bounds(turned)
            assert 0<=box[0][0] and box[0][1]<=16 and 0<=box[2][0] and box[2][1]<=16,(name,box)
            assert 0<=box[1][0] and box[1][1]<=16,(name,box)
            obj(name,turned)
            variants[f'half={half},rotation={rotation}']={'model':'funpackcustom:block/'+name}
            audit.append({'model':name,'faces':len(turned),'bounds':box})
    write(ASSETS/'blockstates'/(NAME+'.json'),{'variants':variants})
    write(ROOT/'src/main/resources/data/funpackcustom/loot_table/blocks'/(NAME+'.json'),{
        'type':'minecraft:block','pools':[{'rolls':1,'conditions':[
            {'condition':'minecraft:block_state_property','block':'funpackcustom:'+NAME,'properties':{'half':'lower'}},
            {'condition':'minecraft:survives_explosion'}],
            'entries':[{'type':'minecraft:item','name':'funpackcustom:'+NAME}]}]})
    write(ART/(NAME+'.geometry.json'),{'textures':TEXTURES,'meshes':g.faces,
        'bounds':bounds(g.faces),'face_count':len(g.faces)})
    editable(g.faces)
    write(ART/'model-audit.json',{'format':'static NeoForge OBJ baked meshes','source':analysis,
        'rotation_contract':'0=south,4=west,8=north,12=east;22.5degrees per segment',
        'inventory_faces':len(g.faces),'complete_placed_faces':placed_faces,
        'placed_lower_faces':len(lower),'placed_upper_faces':len(upper),'whole_bounds':bounds(g.faces),
        'front_thickness_model_units':Z_FRONT-Z_BACK,'render_type':'minecraft:cutout_mipped_all',
        'block_entity_renderer':False,'ticking':False,'placed_models':audit})
    print(f'{NAME}: inventory={len(g.faces)} faces, complete placed={placed_faces} faces '
          f'({len(lower)} lower + {len(upper)} upper), bounds={bounds(g.faces)}')
    print('Artwork copied unchanged; SHA256='+analysis['source_sha256'])


if __name__=='__main__':main()
