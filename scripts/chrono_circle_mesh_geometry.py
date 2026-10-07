"""Chrono Circle's radial controls and native static mesh export.

The old clock was a union of hundreds of scanline cuboids. Shared radial
boundaries retain the original radii, layer depths and 22.5-degree inclination
without their internal faces or tiny stair-step walls. Artwork pixels and
projected UVs are unchanged.
"""
import math


def build_controls(palette_uv, source_scales):
    faces=[]
    cx,cy=8.,26.
    segments=96
    cosine,sine=math.cos(math.pi/8),math.sin(math.pi/8)

    def point(r,z,a):
        return (cx+r*math.sin(a),cy+r*math.cos(a),z)

    def add(name,group,points,material='black',texture='materials',coords=None,glow=False):
        if coords is None:
            u,v,U,V=palette_uv(material)
            coords=[(u,v),(u,V),(U,V),(U,v)][:len(points)]
        # Match the original generator's shared X rotation and global X mirror.
        def transform(p):
            x,y,z=p
            return [16-x,cy+(y-cy)*cosine-z*sine,(y-cy)*sine+z*cosine]
        faces.append({'name':name,'group':group,'texture':'#'+texture,'glow':glow,
                      'vertices':[transform(p) for p in reversed(points)],
                      'uv':[list(p) for p in reversed(coords)]})

    angles=[i*math.tau/segments for i in range(segments+1)]

    def band(name,ra,za,rb,zb,material,group='Circular control assembly',
             arc=None,texture=None,mapping=None,glow=False):
        aa=angles if arc is None else arc
        for i,(a,b) in enumerate(zip(aa,aa[1:])):
            points=[point(ra,za,a),point(ra,za,b),point(rb,zb,b),point(rb,zb,a)]
            if rb==0:points=points[:3]
            coords=[mapping(x,y) for x,y,z in points] if mapping else None
            add(name+' segment %03d'%i,group,points,material,texture or 'materials',coords,glow)

    # One exterior profile replaces overlapping annular solids. All transitions
    # use the exposed boundary of the former union, including the deep black
    # button shoulder and the recessed display's silver gasket.
    profile=[(8.70,.16),(8.70,-.36),(8.42,-.36),(8.42,-.72),
             (8.14,-.72),(8.14,-.94),(6.08,-.94),(6.08,-.37),
             (5.91,-.37),(5.91,-.26),(5.83,-.26),(5.83,-.105)]
    materials=['silver','silver','charcoal','charcoal','black','black','black',
               'silver','silver','rubber','rubber']
    for i,((ra,za),(rb,zb),material) in enumerate(zip(profile,profile[1:],materials)):
        band('Continuous circular layer %02d'%i,ra,za,rb,zb,material)
    su,sv=source_scales['display']
    mapping=lambda x,y:((x-(cx-5.84))/(2*5.84)*16*su,(cy+5.84-y)/(2*5.84)*16*sv)
    band('Round illuminated Chrono Circle LCD',5.83,-.105,0,-.105,'black',
         texture='display',mapping=mapping,glow=True)

    def sector(name,inner,outer,center,halfangle,z0,z1,material,group,subdivisions=4,front=None,glow=False):
        # Angle uses the original button layout: XII at +Y and clockwise order.
        arc=[math.radians(90-center-halfangle+2*halfangle*i/subdivisions)
             for i in range(subdivisions+1)]
        mapping=None;texture=None
        if front:
            texture,(u,v,U,V)=front
            old_angles=[math.radians(90-center-halfangle+2*halfangle*i/8) for i in range(9)]
            old_points=[point(r,z0,a) for r in (inner,outer) for a in old_angles]
            xmin,xmax=min(p[0] for p in old_points),max(p[0] for p in old_points)
            ymin,ymax=min(p[1] for p in old_points),max(p[1] for p in old_points)
            mapping=lambda x,y:(u+(x-xmin)/(xmax-xmin)*(U-u),v+(ymax-y)/(ymax-ymin)*(V-v))
        band(name+' face',outer,z0,inner,z0,material,group,arc,texture,mapping,glow)
        band(name+' outer return',outer,z1,outer,z0,material,group,arc)
        band(name+' inner return',inner,z0,inner,z1,material,group,arc)
        a,b=arc[0],arc[-1]
        add(name+' first end',group,[point(outer,z1,a),point(outer,z0,a),
                                    point(inner,z0,a),point(inner,z1,a)],material)
        add(name+' last end',group,[point(outer,z0,b),point(outer,z1,b),
                                   point(inner,z1,b),point(inner,z0,b)],material)
        # Rear caps are fully buried in the supporting wheel/layer.

    for i in range(12):
        angle=90-i*30;label='Clock button %02d '%(i+1)
        args={'center':angle,'group':'Twelve chrome buttons'}
        sector(label+'separate black socket',6.32,8.06,halfangle=11.10,z0=-1.09,z1=-.94,material='rubber',**args)
        sector(label+'raised chrome edge',6.47,7.94,halfangle=9.65,z0=-1.31,z1=-1.09,material='silver',**args)
        sector(label+'dark lens separator',6.58,7.84,halfangle=8.55,z0=-1.43,z1=-1.31,material='steel',**args)
        sector(label+'curved white lens',6.70,7.73,halfangle=7.60,z0=-1.57,z1=-1.43,material='ivory',
               front=('details',[12.125,8.125,15.875,11.875]),**args)

    colors=('cyan','green','yellow','orange','pink','purple','blue','cyan')
    for i in range(24):
        sector('Rainbow clock outer light segment %02d'%i,9.17,9.26,90-i*15,6.7,.105,.16,
               colors[min(7,int(i/3))],'Rainbow clock light groove',subdivisions=2,glow=True)
    metadata={'radial_segments':segments,'button_segments':4,'light_arc_segments':2,
              'center':[cx,cy],'inclination_degrees':22.5,'exterior_profile':profile,
              'curve_faces':len(faces),'screen_uv_radius':5.84,
              'screen_visible_radius':5.83,'button_count':12,
              'texture_mapping':'Original projected artwork; unchanged source and runtime PNG pixels.'}
    return faces,metadata


from collections import defaultdict
import base64
import json
import uuid
from PIL import Image
from ddr_mesh_export import make_meshes, pieces, quads
from obj_mesh_optimizer import optimize_obj


def export_chrono(elements,curves,textures,surface_statistics,smooth_statistics,root):
    """Convert retained legacy faces exactly, add curves, and export native OBJ."""
    art=root/'art/chrono_circle';assets=root/'src/main/resources/assets/japanesearcades'
    model=assets/'models/block';item=assets/'models/item'
    model.mkdir(parents=True,exist_ok=True);item.mkdir(parents=True,exist_ok=True)
    meshes=make_meshes([{**e,'_assembly':'cabinet'} for e in elements])+curves

    def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    def write_obj(path,faces):
        lines=['# Smooth Chrono Circle cabinet; positions are in Minecraft block units.',
               'mtllib japanesearcades:models/block/chrono_circle.mtl'];index=1;last=None
        for f in faces:
            mat=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
            if mat!=last:lines.append('usemtl '+mat);last=mat
            lines.extend('v '+' '.join('%.9f'%(v/16) for v in p) for p in f['vertices'])
            lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
            lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
            index+=len(f['vertices'])
        result,stats=optimize_obj('\n'.join(lines)+'\n');path.write_text(result,encoding='utf-8');return stats

    def wrapper(name):
        return {'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name+'.obj',
                'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
                'ambientocclusion':True,'render_type':'minecraft:cutout_mipped_all','textures':textures}

    parts={'base':[],'console':[],'marquee':[]}
    for f in meshes:
        for piece in pieces(list(zip(f['vertices'],f['uv'])),1,[16,32]):
            for poly in quads(piece):
                row=min(2,max(0,int(sum(p[0][1] for p in poly)/len(poly)//16)))
                parts[tuple(parts)[row]].append({**f,'vertices':[[p[0],p[1]-row*16,p[2]] for p,uv in poly],
                                               'uv':[uv for p,uv in poly]})
    stats={}
    for name,faces in parts.items():
        stats[name]=write_obj(model/('chrono_circle_'+name+'.obj'),faces)
        write_json(model/('chrono_circle_'+name+'.json'),wrapper('block/chrono_circle_'+name))
    item_faces=[{**f,'vertices':[[x*.35+5.2,y*.35,z*.35+5.2] for x,y,z in f['vertices']]} for f in meshes]
    stats['item']=write_obj(item/'chrono_circle.obj',item_faces)
    item_model=wrapper('item/chrono_circle');item_model.update({'ambientocclusion':False,'gui_light':'front',
        'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                   'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                   'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                   'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                   'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
    write_json(item/'chrono_circle.json',item_model)
    mtl=[]
    for key,glow in sorted({(f['texture'][1:],f['glow']) for f in meshes}):
        mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                    'Kd 1 1 1','map_Kd #'+key,''])
    (model/'chrono_circle.mtl').write_text('\n'.join(mtl),encoding='utf-8')
    write_json(assets/'blockstates/chrono_circle.json',{'variants':{
        'facing='+direction+',part='+part:{'model':'japanesearcades:block/chrono_circle_'+part,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in parts}})

    textures_list=[(key,assets/'textures/block'/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indexes={'#'+key:i for i,(key,path) in enumerate(textures_list)}
    sizes=[Image.open(path).size for key,path in textures_list]
    bb=[];groups=defaultdict(list)
    for mesh_index,f in enumerate(meshes):
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'chrono_circle/smooth/'+str(mesh_index)+'/'+f['name']));ti=indexes[f['texture']];width,height=sizes[ti]
        keys=['v'+str(i) for i in range(len(f['vertices']))]
        bb.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
                   'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
                   'uv':{k:[u*width/16,v*height/16] for k,(u,v) in zip(keys,f['uv'])},'texture':ti}},
                   'visibility':True,'export':True})
        groups[f['group']].append(uid)
    bbtextures=[]
    for i,(key,path) in enumerate(textures_list):
        width,height=sizes[i]
        bbtextures.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
                           'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'chrono_circle/'+key)),'width':width,'height':height,
                           'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                           'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(art/'chrono_circle.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'Chrono Circle','model_identifier':'chrono_circle','visible_box':[2,4,1.5],'resolution':{'width':256,'height':256},
        'elements':bb,'textures':bbtextures,'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'chrono_circle/group/'+name)),
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
    print('Chrono Circle smooth mesh:',len(meshes),'source faces; bounds',bounds)
    print('Smooth ring:',smooth_statistics)
    print('Optimized native meshes:',stats)
