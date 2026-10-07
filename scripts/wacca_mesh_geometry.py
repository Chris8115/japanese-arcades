"""Continuous WACCA rim, conical touch bowl, and recessed monitor meshes.

Every circular surface is sampled on shared radial boundaries. The exact
backward shear is applied per vertex instead of quantized cuboid courses.
The original LED sheet remains a continuous projection in cabinet XY space.
"""
from collections import defaultdict
import base64
import json
import math
import uuid

from PIL import Image
from ddr_mesh_export import make_meshes, pieces, quads
from obj_mesh_optimizer import optimize_obj

CX,CY=8.0,28.2
SEGMENTS=96
LEAN=.10
LEAN_ORIGIN_Y=17.2
OUTER_RADIUS=11.0
CONE_OUTER_RADIUS,CONE_OUTER_Z=10.32,1.65
CONE_INNER_RADIUS=6.38
CONE_INNER_Z=CONE_OUTER_Z+(CONE_OUTER_RADIUS-CONE_INNER_RADIUS)*1.04
SCREEN_RADIUS,SCREEN_Z=6.18,5.82


def build_smooth_ring(palette_uv,source_scales):
    faces=[]
    half_seam=math.radians(.10)
    radial_angles=[]
    for section in range(8):
        start=section*math.tau/8
        radial_angles.extend([start-half_seam,start+half_seam]+[start+i*math.tau/SEGMENTS for i in range(1,12)])
    radial_angles.append(radial_angles[0]+math.tau)

    def add(name,group,points,material='black',texture='materials',uv=None,glow=False):
        # Author in the same front-view coordinate convention as the legacy
        # cabinet, then mirror positions and winding together. The old XY LED
        # atlas consequently keeps its cyan bottom and pink quadrant intact.
        if uv is None:
            u,v,U,V=palette_uv(material)
            uv=[(u,v),(u,V),(U,V),(U,v)][:len(points)]
        leaned=[[16-x,y,z+(y-LEAN_ORIGIN_Y)*LEAN] for x,y,z in reversed(points)]
        faces.append({'name':name,'group':group,'texture':'#'+texture,'glow':glow,
                      'vertices':leaned,'uv':[list(p) for p in reversed(uv)]})

    def point(radius,z,angle):
        return (CX+radius*math.sin(angle),CY+radius*math.cos(angle),z)

    def lathe(name,group,profile,angles=None,material='black',texture='materials',glow=False,xy_uv=None):
        # Outside->inside on the front points toward the viewer; along the
        # outer barrel a rear->front profile points radially outward.
        angles=angles or radial_angles
        for band,(a,b) in enumerate(zip(profile,profile[1:])):
            ra,za=a;rb,zb=b
            for segment,(ta,tb) in enumerate(zip(angles,angles[1:])):
                points=[point(ra,za,ta),point(ra,za,tb),point(rb,zb,tb),point(rb,zb,ta)]
                # At a closed cap's centre the repeated radial vertices become
                # one triangle; exporting a collapsed quad is unnecessary.
                if ra==0:points=[points[0],points[2],points[3]]
                elif rb==0:points=[points[0],points[1],points[2]]
                uv=[xy_uv(x,y) for x,y,z in points] if xy_uv else None
                add('%s band %02d segment %03d'%(name,band,segment),group,points,
                    material,texture,uv,glow)

    # The rim is one closed bevelled annular shell. Eight grey radial strips
    # occupy real surface area between moulded sections rather than fighting
    # with a second face laid on top of the white plastic.
    white_profile=[(CONE_OUTER_RADIUS,CONE_OUTER_Z),(CONE_OUTER_RADIUS,1.20),
                   (10.47,1.06),(10.83,1.06),(11.0,1.23),(11.0,7.52),
                   (10.82,7.72),(CONE_OUTER_RADIUS,7.72),(CONE_OUTER_RADIUS,CONE_OUTER_Z)]
    # Frontward profile ordering must be outside->inside for a north normal.
    white_profile=list(reversed(white_profile))
    for section in range(8):
        start=section*math.tau/8
        seam=[start-half_seam,start+half_seam]
        lathe('White rim moulded section seam %d'%section,'Rim panel divisions',white_profile,seam,'rim_gray')
        end=start+math.tau/8-half_seam
        arc=[start+half_seam]+[start+i*math.tau/SEGMENTS for i in range(1,12)]+[end]
        lathe('Smooth white rim section %d'%section,'Smooth white rim',white_profile,arc,'white')

    xy_led=lambda x,y:((x+3)/22*16,(39.2-y)/22*16)
    lathe('Continuous LED cone','Smooth touch bowl',
          [(CONE_OUTER_RADIUS,CONE_OUTER_Z),(CONE_INNER_RADIUS,CONE_INNER_Z)],
          material='black',texture='leds',glow=True,xy_uv=xy_led)
    # A narrow black bevel directly shares the cone edge and then the display
    # edge. Its tiny last cylindrical return is deliberate, not an open gap.
    bezel=[(CONE_INNER_RADIUS,CONE_INNER_Z),(6.30,5.77),(SCREEN_RADIUS,5.80),(SCREEN_RADIUS,SCREEN_Z)]
    lathe('Smooth display gasket','Recessed circular monitor',bezel,material='rubber')
    scale=source_scales['display']
    xy_screen=lambda x,y:((x-(CX-SCREEN_RADIUS))/(2*SCREEN_RADIUS)*16*scale[0],
                           (CY+SCREEN_RADIUS-y)/(2*SCREEN_RADIUS)*16*scale[1])
    lathe('Circular WACCA Reverse display','Recessed circular monitor',
          [(SCREEN_RADIUS,SCREEN_Z),(0,SCREEN_Z)],texture='display',glow=True,xy_uv=xy_screen)

    # A closed, softly bevelled rear enclosure replaces its former horizontal
    # strips. Its front is hidden behind the white barrel, cone, and monitor.
    lathe('Circular rear enclosure','Ring rear enclosure',
          [(0,9.12),(10.54,9.12),(10.70,8.96),(10.70,7.65)],material='black')
    metadata={'radial_segments':SEGMENTS,'shared_radial_edges':len(radial_angles)-1,'center':[CX,CY],'outer_radius':OUTER_RADIUS,
              'lean_per_y':LEAN,'lean_origin_y':LEAN_ORIGIN_Y,
              'cone_profile':[[CONE_OUTER_RADIUS,CONE_OUTER_Z],[CONE_INNER_RADIUS,CONE_INNER_Z]],
              'screen_radius':SCREEN_RADIUS,'screen_depth':SCREEN_Z,'gasket_profile':bezel,
              'rim_profile':white_profile,'panel_seams':8,'seam_half_angle_degrees':.10,
              'curve_face_count':len(faces),'texture_mapping':'Original continuous XY atlas; no pixel edits.'}
    return faces,metadata


def smooth_polygon(name,outline,z0,z1,material,group,front,glow,palette_uv,source_scales):
    """Exact flat header outlines and print mapping, without scanline ledges."""
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    outline=list(outline)
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))
    if area<0:outline.reverse()
    ids=list(range(len(outline)));triangles=[]
    while len(ids)>3:
        for j,index in enumerate(ids):
            prev,nxt=ids[j-1],ids[(j+1)%len(ids)];a,b,c=outline[prev],outline[index],outline[nxt]
            if cross(a,b,c)<=1e-10:continue
            if any(cross(a,b,outline[k])>=-1e-10 and cross(b,c,outline[k])>=-1e-10 and cross(c,a,outline[k])>=-1e-10
                   for k in ids if k not in (prev,index,nxt)):continue
            triangles.append((prev,index,nxt));ids.pop(j);break
        else:raise AssertionError(('Invalid header polygon',name))
    triangles.append(tuple(ids));result=[]
    u,v,U,V=palette_uv(material)
    minx,maxx=min(x for x,y in outline),max(x for x,y in outline)
    miny,maxy=min(y for x,y in outline),max(y for x,y in outline)
    def add(suffix,points,is_front=False):
        texture='materials';coords=[(u,v),(u,V),(U,V),(U,v)][:len(points)]
        if is_front and front:
            texture,region=front;u0,v0,u1,v1=region;su,sv=source_scales.get(texture,(1,1))
            coords=[((u0+(x-minx)/(maxx-minx)*(u1-u0))*su,(v0+(maxy-y)/(maxy-miny)*(v1-v0))*sv) for x,y,z in points]
        result.append({'name':name+suffix,'group':group,'texture':'#'+texture,
                       'glow':bool(is_front and (glow is True or glow and 'north' in glow)),
                       'vertices':[[16-x,y,z] for x,y,z in reversed(points)],'uv':[list(p) for p in reversed(coords)]})
    for i,triangle in enumerate(triangles):
        add(' smooth front %d'%i,[(*outline[k],z0) for k in reversed(triangle)],True)
        add(' smooth back %d'%i,[(*outline[k],z1) for k in triangle])
    for i,a in enumerate(outline):
        b=outline[(i+1)%len(outline)]
        add(' smooth edge %d'%i,[(*a,z0),(*b,z0),(*b,z1),(*a,z1)])
    return result


def export_wacca(elements,curves,textures,surface_statistics,smooth_statistics,root):
    """Convert retained legacy faces exactly, add curves, and export native OBJ."""
    art=root/'art/wacca';assets=root/'src/main/resources/assets/funpackcustom'
    model=assets/'models/block';item=assets/'models/item'
    model.mkdir(parents=True,exist_ok=True);item.mkdir(parents=True,exist_ok=True)
    meshes=make_meshes([{**e,'_assembly':'cabinet'} for e in elements])+curves

    def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    def write_obj(path,faces):
        lines=['# Smooth WACCA cabinet; positions are in Minecraft block units.',
               'mtllib funpackcustom:models/block/wacca.mtl'];index=1;last=None
        for f in faces:
            mat=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
            if mat!=last:lines.append('usemtl '+mat);last=mat
            lines.extend('v '+' '.join('%.9f'%(v/16) for v in p) for p in f['vertices'])
            lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
            lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
            index+=len(f['vertices'])
        result,stats=optimize_obj('\n'.join(lines)+'\n');path.write_text(result,encoding='utf-8');return stats

    def wrapper(name):
        return {'parent':'minecraft:block/block','loader':'neoforge:obj','model':'funpackcustom:models/'+name+'.obj',
                'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
                'ambientocclusion':True,'render_type':'minecraft:solid','textures':textures}

    parts={'base':[],'console':[],'marquee':[]}
    for f in meshes:
        for piece in pieces(list(zip(f['vertices'],f['uv'])),1,[16,32]):
            for poly in quads(piece):
                row=min(2,max(0,int(sum(p[0][1] for p in poly)/len(poly)//16)))
                parts[tuple(parts)[row]].append({**f,'vertices':[[p[0],p[1]-row*16,p[2]] for p,uv in poly],
                                               'uv':[uv for p,uv in poly]})
    stats={}
    for name,faces in parts.items():
        stats[name]=write_obj(model/('wacca_'+name+'.obj'),faces)
        write_json(model/('wacca_'+name+'.json'),wrapper('block/wacca_'+name))
    item_faces=[{**f,'vertices':[[x*.35+5.2,y*.35,z*.35+5.2] for x,y,z in f['vertices']]} for f in meshes]
    stats['item']=write_obj(item/'wacca.obj',item_faces)
    item_model=wrapper('item/wacca');item_model.update({'ambientocclusion':False,'gui_light':'front',
        'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                   'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                   'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                   'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                   'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
    write_json(item/'wacca.json',item_model)
    mtl=[]
    for key,glow in sorted({(f['texture'][1:],f['glow']) for f in meshes}):
        mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                    'Kd 1 1 1','map_Kd #'+key,''])
    (model/'wacca.mtl').write_text('\n'.join(mtl),encoding='utf-8')
    write_json(assets/'blockstates/wacca.json',{'variants':{
        'facing='+direction+',part='+part:{'model':'funpackcustom:block/wacca_'+part,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in parts}})

    textures_list=[(key,assets/'textures/block'/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indexes={'#'+key:i for i,(key,path) in enumerate(textures_list)}
    sizes=[Image.open(path).size for key,path in textures_list]
    bb=[];groups=defaultdict(list)
    for f in meshes:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'wacca/smooth/'+f['name']));ti=indexes[f['texture']];width,height=sizes[ti]
        keys=['v'+str(i) for i in range(len(f['vertices']))]
        bb.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
                   'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
                   'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':ti}},
                   'visibility':True,'export':True})
        groups[f['group']].append(uid)
    bbtextures=[]
    for i,(key,path) in enumerate(textures_list):
        width,height=sizes[i]
        bbtextures.append({'name':path.name,'folder':'block','namespace':'funpackcustom','id':str(i),
                           'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'wacca/'+key)),'width':width,'height':height,
                           'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                           'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(art/'wacca.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'WACCA Reverse','model_identifier':'wacca','visible_box':[2,4,1.5],'resolution':{'width':256,'height':256},
        'elements':bb,'textures':bbtextures,'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'wacca/group/'+name)),
            'origin':[8,0,8],'children':children} for name,children in groups.items()]})
    bounds=[[min(p[i] for f in meshes for p in f['vertices']),max(p[i] for f in meshes for p in f['vertices'])] for i in range(3)]
    write_json(art/'geometry.json',{'textures':textures,'meshes':meshes,'legacy_elements':elements,
        'surface_optimization':surface_statistics,'smooth_geometry':smooth_statistics,
        'statistics':{'authoring_faces':len(meshes),'optimized':stats},'bounds':bounds})
    for f in meshes:
        assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
        a,b,c=f['vertices'][:3];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        assert sum(x*x for x in n)>1e-18,('Degenerate face',f['name'])
    print('WACCA smooth mesh:',len(meshes),'source faces; bounds',bounds)
    print('Smooth ring:',smooth_statistics)
    print('Optimized native meshes:',stats)
