"""Build DDR SuperNOVA with a tilted CRT and a standable rounded-rail stage.

Source illustrations are packed unchanged and mapped using their native aspect.
The tilted CRT cabinet and two-player stage follow the supplied red-cab
references. The connected structure has a two-by-three-block floor footprint.
"""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
from PIL import Image
from ddr_cabinet_geometry import build_cabinet
from ddr_platform_geometry import build_platform
from ddr_textures import build_textures
from wacca_surface_geometry import optimize_surfaces
from ddr_mesh_export import export_mesh_assets

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/ddr_supernova'
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
for path in (ART,TEXTURES,MODEL):path.mkdir(parents=True,exist_ok=True)
PALETTE,KEYS=build_textures(TEXTURES)

source_scales={}
for key,source_name,target_name in (
        ('display','display-artwork-source.png','ddr_supernova_display.png'),
        ('header','header-artwork-source.png','ddr_supernova_header.png')):
    source=Image.open(ART/source_name).convert('RGB')
    size=tuple(1<<(n-1).bit_length() for n in source.size)
    packed=Image.new(source.mode,size,PALETTE['black'])
    packed.paste(source,(0,0))
    packed.save(TEXTURES/target_name)
    source_scales[key]=tuple(n/p for n,p in zip(source.size,size))

def uv(name):
    i=KEYS.index(name)
    # Eight native pixels keep sampling inside this 64px material tile through
    # mip level 4. Exact tile/sprite boundaries can pick up neighboring colours.
    inset=.5
    return [(i%4)*4+inset,(i//4)*4+inset,(i%4)*4+4-inset,(i//4)*4+4-inset]


elements=[]
raw_meshes=[]
assembly="cabinet"


def cube(name,start,end,material='black',*,north=None,east=None,west=None,south=None,
         up=None,down=None,rotation=None,glow=False,group='Cabinet',faces_only=None):
    assert all(b>a for a,b in zip(start,end)),(name,start,end)
    faces={side:{'uv':uv(material),'texture':'#materials'} for side in ('north','east','south','west','up','down')}
    for direction,override in (('north',north),('east',east),('west',west),('south',south),('up',up),('down',down)):
        if override:
            texture,coordinates=override
            scale=source_scales.get(texture,(1,1))
            faces[direction]={'uv':[v*scale[i%2] for i,v in enumerate(coordinates)],'texture':'#'+texture}
    element={'name':name,'from':list(start),'to':list(end),'faces':faces,'_group':group,'_assembly':assembly}
    if rotation:
        axis,angle,origin=rotation
        assert -180 <= angle <= 180,(name,angle)
        element['rotation']={'axis':axis,'angle':angle,'origin':list(origin),'rescale':False}
    if glow:
        for side,face in faces.items():
            if glow is True or side in glow:
                face['neoforge_data']={'block_light':15,'sky_light':15,'ambient_occlusion':False}
    if faces_only:
        element['faces']={side:face for side,face in faces.items() if side in faces_only}
    elements.append(element)


def polygon(name,points,z0,z1,material,*,group='Sculpted panels',glow=False,front=None,rotation=None,step=.25):
    minx,maxx=min(x for x,y in points),max(x for x,y in points)
    miny,maxy=min(y for x,y in points),max(y for x,y in points)
    count=max(1,math.ceil((maxy-miny)/step));dy=(maxy-miny)/count
    rows=[];active={}
    for i in range(count):
        y=miny+(i+.5)*dy;cross=[]
        for a,b in zip(points,points[1:]+points[:1]):
            if min(a[1],b[1])<=y<max(a[1],b[1]):
                cross.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
        cross.sort();following={}
        for j in range(0,len(cross)-1,2):
            left=max(minx,round(cross[j]/step)*step)
            right=min(maxx,round(cross[j+1]/step)*step)
            if right<=left:continue
            key=(left,right)
            if key in active:
                rect=active.pop(key);rect[3]=miny+(i+1)*dy
            else:rect=[left,right,miny+i*dy,miny+(i+1)*dy]
            following[key]=rect
        rows.extend(active.values());active=following
    rows.extend(active.values())
    for i,(left,right,bottom,top) in enumerate(rows):
        override=None
        if front:
            tex,(u0,v0,u1,v1)=front
            override=(tex,[u0+(left-minx)/(maxx-minx)*(u1-u0),v0+(maxy-top)/(maxy-miny)*(v1-v0),
                           u0+(right-minx)/(maxx-minx)*(u1-u0),v0+(maxy-bottom)/(maxy-miny)*(v1-v0)])
        cube(name+' segment %02d'%i,(left,bottom,z0),(right,top,z1),material,
             north=override,rotation=rotation,glow=glow,group=group)


def mesh(name,vertices,faces,material,*,group='Cabinet',glow=False,uv=None,texture='materials'):
    tile=globals()['uv'](material)
    for i,indices in enumerate(faces):
        default=[(tile[0],tile[1]),(tile[0],tile[3]),(tile[2],tile[3]),(tile[2],tile[1])]
        raw_meshes.append({'name':name+' face '+str(i),'group':group,'assembly':assembly,
                           'texture':'#'+texture,'glow':glow,
                           'vertices':[list(vertices[j]) for j in indices],
                           'uv':uv[i] if uv is not None else default[:len(indices)]})


build_cabinet(cube,polygon,mesh,ART)
# A real red cabinet is narrower than its two-player stage. Its console has a
# tall surround and a 4:3 CRT; the near-square marquee matches the references.
cabinet_width=.78
for e in elements:
    for point in (e['from'],e['to']):
        point[0]=16+(point[0]-16)*cabinet_width
    if 'rotation' in e:
        e['rotation']['origin'][0]=16+(e['rotation']['origin'][0]-16)*cabinet_width
    if e['name'] in ('Deep black CRT aperture','Inner beveled CRT lip','Luminous four-to-three CRT picture'):
        for point in (e['from'],e['to']):
            point[1]=26.1+(point[1]-26.1)*cabinet_width
for face in raw_meshes:
    for point in face['vertices']:
        point[0]=16+(point[0]-16)*cabinet_width
assembly='stage'
build_platform(cube,polygon,mesh)

texture_paths={
    'materials':'funpackcustom:block/ddr_supernova_materials','details':'funpackcustom:block/ddr_supernova_details',
    'display':'funpackcustom:block/ddr_supernova_display',
    'header':'funpackcustom:block/ddr_supernova_header','particle':'funpackcustom:block/ddr_supernova_materials',
}

# Minecraft's north-facing UVs run from +X to -X when viewed from the front.
# Mirror our front-view coordinates so the ornaments stay on the photographed right.
for e in elements:
    x0,x1=e['from'][0],e['to'][0]
    e['from'][0],e['to'][0]=32-x1,32-x0
    east=e['faces'].pop('east',None)
    west=e['faces'].pop('west',None)
    if east is not None:e['faces']['west']=east
    if west is not None:e['faces']['east']=west
    if 'rotation' in e:
        e['rotation']['origin'][0]=32-e['rotation']['origin'][0]
        if e['rotation']['axis'] in ('y','z'): e['rotation']['angle']*=-1

# Bake only the opaque exterior. Adjacent pieces do not need internal faces;
# clipped overlaps have exactly one surface owner, eliminating coplanar fights.
# Alpha-bearing cutout pieces must not occlude opaque geometry in the union.
alpha_groups=set()
marquee=[e for e in elements if e['_group'] in alpha_groups]
opaque=[e for e in elements if e['_group'] not in alpha_groups]
aligned=[e for e in opaque if 'rotation' not in e]
rotated_groups={}
for element in opaque:
    if 'rotation' in element:
        key=json.dumps(element['rotation'],sort_keys=True)
        local=copy.deepcopy(element)
        del local['rotation']
        rotated_groups.setdefault(key,[]).append(local)
elements,surface_details=optimize_surfaces(aligned)
# Pieces sharing one rotation also share a local coordinate system. Resolve
# their opaque union before rotating it so layered surfaces have one exterior.
surface_details['rotation_groups']=[]
for key,group in rotated_groups.items():
    exterior,details=optimize_surfaces(group)
    rotation=json.loads(key)
    for element in exterior:
        element['rotation']=copy.deepcopy(rotation)
    elements.extend(exterior)
    surface_details['rotation_groups'].append({'rotation':rotation,**details})
elements.extend(marquee)
surface_details['alpha_elements']=len(marquee)
surface_details['total_exported_faces']=sum(len(e['faces']) for e in elements)

# NeoForge's bundled OBJ loader preserves the CRT tilt and rounded rail tubes.
export_mesh_assets(elements, raw_meshes, texture_paths, surface_details, ROOT)
