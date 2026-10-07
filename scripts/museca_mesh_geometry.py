"""MUSECA's planar controller shelf and shared-slope spinner surfaces.

All deck/control vertices use one affine height function. The native OBJ loader
therefore receives real planes, not scanline cubes approximating a shallow tilt.
The retained cabinet geometry and original texture pixels are unchanged.
"""
import math
from collections import defaultdict
import base64
import json
import uuid
from PIL import Image
from ddr_mesh_export import make_meshes, pieces, quads
from obj_mesh_optimizer import optimize_obj
from wacca_surface_geometry import optimize_surfaces

DECK_SLOPE=.145
DECK_OUTLINE=[(-1.55,3.45),(17.55,3.45),(18.6,-4.90),
              (16.30,-7.50),(-.30,-7.50),(-2.6,-4.90)]
SPINNER_CENTERS=[(2.50,.42),(8,.42),(13.50,.42),(5.15,-4.02),(10.85,-4.02)]


def deck_y(z):
    return 18.07+(z+7.50)*DECK_SLOPE


def build_deck(palette_uv):
    faces=[]

    def add(name,group,points,material='black',texture='materials',coords=None,glow=False):
        if coords is None:
            u,v,U,V=palette_uv(material)
            coords=[(u,v),(u,V),(U,V),(U,v)][:len(points)]
        # Author X as seen from the front, mirror positions and winding once.
        faces.append({'name':name,'group':group,'texture':'#'+texture,'glow':glow,
                      'vertices':[[16-x,deck_y(z)+h,z] for x,h,z in reversed(points)],
                      'uv':[list(p) for p in reversed(coords)]})

    def level(outline,h):return [(x,h,z) for x,z in outline]
    def connect(name,lower,upper,material,group):
        for i,(a,b) in enumerate(zip(lower,lower[1:]+lower[:1])):
            # The footprint is clockwise in XZ and faces upward as an XYZ cap.
            add(name+' side %d'%i,group,[a,b,upper[(i+1)%len(upper)],upper[i]],material)

    # A continuous closed shell: black underside, six sidewalls and six narrow
    # white bevels. The entire printed top is just two coplanar convex quads.
    group='Five-spinner deck'
    lower=level(DECK_OUTLINE,-.87)
    seam=level(DECK_OUTLINE,-.17)
    edge=level(DECK_OUTLINE,-.035)
    # A uniform inset keeps every matching edge parallel, so each bevel is a
    # true quad plane rather than a subtly twisted four-vertex surface.
    top_outline=[(x+(8-x)*.005,z+(-2-z)*.005) for x,z in DECK_OUTLINE]
    top=level(top_outline,0)
    connect('Planar deck black undertray',lower,seam,'black',group)
    connect('Planar deck white perimeter',seam,edge,'white',group)
    connect('Planar deck shallow white bevel',edge,top,'white',group)
    for i,indices in enumerate(((0,1,2,3),(0,3,4,5))):
        add('Planar deck sealed underside %d'%i,group,[lower[k] for k in reversed(indices)])
        points=[top[k] for k in indices]
        # Same continuous printed projection as the original up faces after
        # their global X mirror. No image resampling or replacement artwork.
        coords=[(8.25+(18.6-x)/21.2*7.5,.25+(z+7.50)/10.95*7.5) for x,h,z in points]
        add('Planar deck printed top %d'%i,group,points,'white','details',coords)

    def box(name,x0,x1,z0,z1,h0,h1,material,group):
        # Sloped tops and bottoms remain parallel to the controller plate.
        lo=[(x0,h0,z0),(x0,h0,z1),(x1,h0,z1),(x1,h0,z0)]
        hi=[(x0,h1,z0),(x0,h1,z1),(x1,h1,z1),(x1,h1,z0)]
        connect(name,lo,hi,material,group)
        add(name+' bottom',group,list(reversed(lo)),material)
        add(name+' top',group,hi,material)

    # One concealed support replaces four stair courses. Its bottom meets the
    # chassis top without duplicate coplanar sidewalls; the top follows the deck.
    support_outline=[(0,1.65),(16,1.65),(16,3.85),(0,3.85)]
    support_outline.reverse()
    lo=[(x,17.84-deck_y(z),z) for x,z in support_outline]
    hi=level(support_outline,-.19)
    connect('Rear deck concealed planar support',lo,hi,'black','Deck support')
    add('Rear deck concealed support underside','Deck support',list(reversed(lo)))
    add('Rear deck concealed support top','Deck support',hi)

    # Function button and screw heads now share the slope rather than hovering
    # on horizontal cubes over successive deck steps.
    h0=19.67-deck_y((2.44+3.19)/2)
    box('Center small rear function button',7.47,8.53,2.44,3.19,h0,h0+.22,'charcoal','Deck hardware')
    h0=19.89-deck_y((2.56+3.05)/2)
    box('Rear function button silver cap',7.60,8.40,2.56,3.05,h0,h0+.14,'silver','Deck hardware')
    for x,z in ((-1.,-4.9),(17.,-4.9),(.9,-6.93),(15.1,-6.93),(.1,2.9),(15.9,2.9)):
        box('Deck countersunk screw '+str((x,z)),x-.075,x+.075,z-.075,z+.075,0,.055,'steel','Deck hardware')

    # Twenty-four sides keep these small controllers round at playing distance
    # without spending extra faces on their repeated body and hub rings.
    segments=24
    angles=[i*math.tau/segments for i in range(segments+1)]

    def spindle(name,cx,cz,profile,materials,group='Five luminous spinners'):
        def p(r,h,a):return (cx+r*math.cos(a),h,cz+r*math.sin(a))
        for band,((ra,ha),(rb,hb),(mat,lit)) in enumerate(zip(profile,profile[1:],materials)):
            for i,(a,b) in enumerate(zip(angles,angles[1:])):
                points=[p(ra,ha,a),p(ra,ha,b),p(rb,hb,b),p(rb,hb,a)]
                # In XZ, inside-to-outside gives the underside; the exterior
                # profile goes out along the bottom and back in across the top.
                if ra==0:points=[points[0],points[2],points[3]]
                elif rb==0:points=points[:3]
                add(name+' band %02d segment %02d'%(band,i),group,list(reversed(points)),mat,glow=lit)

    # Exact manufactured radii, tier heights and white lighting from the
    # original source, now expressed as a continuous closed radial profile.
    profile=[(0,0),(1.96,0),(1.96,.16),(1.91,.16),(1.91,.35),
             (1.76,.35),(1.76,.71),(1.56,.71),(1.56,.88),
             (1.36,.88),(1.36,.98),(0,.98)]
    materials=[('steel',False),('steel',False),('steel',False),('ivory',False),
               ('ivory',False),('white',True),('white',True),('white',True),
               ('white',True),('ivory',False),('ivory',False)]
    local_inlays=[]
    def inlay_cube(name,start,end,material):
        local_inlays.append({'name':name,'from':start,'to':end,'_group':'Spinner center inlays',
          'faces':{side:{'uv':palette_uv(material),'texture':'#materials'}
                   for side in ('north','east','south','west','up','down')}})
    for i,(x,z) in enumerate(SPINNER_CENTERS,1):
        stem='Spinner %d '%i
        spindle(stem+'continuous tiered body',x,z,profile,materials)
        spindle(stem+'center medallion',x,z,[(0,.98),(.60,.98),(.60,1.015),(0,1.015)],
                [('rim_gray',False)]*3)
        for k,(dx,dz,w,d) in enumerate(((-.4,-.055,.80,.11),(-.055,-.4,.11,.80))):
            inlay_cube(stem+'inlaid center line '+str(k),[x+dx,1.017,z+dz],
                       [x+dx+w,1.035,z+dz+d],'steel')
        for k in range(5):
            o=-.35+k*.15
            inlay_cube(stem+'diagonal emblem A '+str(k),[x+o-.055,1.016,z+o-.055],
                       [x+o+.055,1.036,z+o+.055],'white')
            inlay_cube(stem+'diagonal emblem B '+str(k),[x-o-.055,1.016,z+o-.055],
                       [x-o+.055,1.036,z+o+.055],'white')
    # Resolve the symbol's intersecting bars locally before applying the same
    # affine tilt to every vertex; there are no coplanar crossed overlays.
    inlays,_=optimize_surfaces(local_inlays)
    for f in make_meshes([{**e,'_assembly':'cabinet'} for e in inlays]):
        add(f['name'],f['group'],f['vertices'],texture=f['texture'][1:],coords=f['uv'])
    metadata={'deck_slope':DECK_SLOPE,'deck_intercept':deck_y(0),
              'deck_outline':DECK_OUTLINE,'deck_top_outline':top_outline,'deck_top_faces':2,
              'deck_shell_faces':22,'deck_height_function':'y=18.07+0.145*(z+7.50)',
              'spinner_centers_authoring_xz':SPINNER_CENTERS,'spinner_segments':segments,
              'spinner_exterior_profile':profile,'control_faces':len(faces),
              'texture_mapping':'Original top artwork projection with global X mirror; all PNG pixels unchanged.'}
    return faces,metadata


def export_museca(elements,curves,textures,surface_statistics,smooth_statistics,root):
    """Convert retained legacy faces exactly, add curves, and export native OBJ."""
    art=root/'art/museca';assets=root/'src/main/resources/assets/japanesearcades'
    model=assets/'models/block';item=assets/'models/item'
    model.mkdir(parents=True,exist_ok=True);item.mkdir(parents=True,exist_ok=True)
    meshes=make_meshes([{**e,'_assembly':'cabinet'} for e in elements])+curves

    def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    def write_obj(path,faces):
        lines=['# Smooth MUSECA cabinet; positions are in Minecraft block units.',
               'mtllib japanesearcades:models/block/museca.mtl'];index=1;last=None
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
        stats[name]=write_obj(model/('museca_'+name+'.obj'),faces)
        write_json(model/('museca_'+name+'.json'),wrapper('block/museca_'+name))
    item_faces=[{**f,'vertices':[[x*.35+5.2,y*.35,z*.35+5.2] for x,y,z in f['vertices']]} for f in meshes]
    stats['item']=write_obj(item/'museca.obj',item_faces)
    item_model=wrapper('item/museca');item_model.update({'ambientocclusion':False,'gui_light':'front',
        'display':{'gui':{'rotation':[15,225,0],'translation':[0,0,0],'scale':[.95,.95,.95]},
                   'ground':{'translation':[0,2,0],'scale':[.6,.6,.6]},
                   'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
                   'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
                   'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.5,.5,.5]}}})
    write_json(item/'museca.json',item_model)
    mtl=[]
    for key,glow in sorted({(f['texture'][1:],f['glow']) for f in meshes}):
        mtl.extend(['newmtl '+key+('_glow' if glow else '_surface'),'Ka '+('1 1 1' if glow else '0 0 0'),
                    'Kd 1 1 1','map_Kd #'+key,''])
    (model/'museca.mtl').write_text('\n'.join(mtl),encoding='utf-8')
    write_json(assets/'blockstates/museca.json',{'variants':{
        'facing='+direction+',part='+part:{'model':'japanesearcades:block/museca_'+part,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in parts}})

    textures_list=[(key,assets/'textures/block'/(value.split('/')[-1]+'.png')) for key,value in textures.items() if key!='particle']
    indexes={'#'+key:i for i,(key,path) in enumerate(textures_list)}
    sizes=[Image.open(path).size for key,path in textures_list]
    bb=[];groups=defaultdict(list)
    for mesh_index,f in enumerate(meshes):
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'museca/smooth/'+str(mesh_index)+'/'+f['name']));ti=indexes[f['texture']];width,height=sizes[ti]
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
                           'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'museca/'+key)),'width':width,'height':height,
                           'uv_width':width,'uv_height':height,'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                           'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(art/'museca.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'MUSECA','model_identifier':'museca','visible_box':[2,4,1.5],'resolution':{'width':256,'height':256},
        'elements':bb,'textures':bbtextures,'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'museca/group/'+name)),
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
    print('MUSECA smooth mesh:',len(meshes),'source faces; bounds',bounds)
    print('Planar controls:',smooth_statistics)
    print('Optimized native meshes:',stats)
