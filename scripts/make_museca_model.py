"""Build the MUSECA cabinet with native static meshes.

Source illustrations are packed unchanged and mapped using their native aspect.
The reclining portrait monitor, five spinners, folded marquee and prism column follow the supplied references.
"""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
from PIL import Image
from museca_shell_geometry import build_shell
from museca_upper_geometry import build_upper
from museca_textures import build_textures
from wacca_surface_geometry import optimize_surfaces
from museca_mesh_geometry import build_deck, export_museca

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/museca'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEXTURES=ASSETS/'textures/block'
MODEL=ASSETS/'models/block'
for path in (ART,TEXTURES,MODEL):path.mkdir(parents=True,exist_ok=True)
PALETTE,KEYS=build_textures(TEXTURES)

source_scales={}
for key,source_name,target_name in (
        ('display','display-artwork-source.png','museca_display.png'),
        ('marquee','marquee-artwork-source.png','museca_marquee.png')):
    source=Image.open(ART/source_name).convert('RGBA' if key=='branding' else 'RGB')
    size=tuple(1<<(n-1).bit_length() for n in source.size)
    packed=Image.new(source.mode,size,(0,0,0,0) if key=='branding' else PALETTE['black'])
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


def cube(name,start,end,material='black',*,north=None,east=None,west=None,south=None,
         up=None,down=None,rotation=None,glow=False,group='Cabinet',faces_only=None):
    assert all(b>a for a,b in zip(start,end)),(name,start,end)
    faces={side:{'uv':uv(material),'texture':'#materials'} for side in ('north','east','south','west','up','down')}
    for direction,override in (('north',north),('east',east),('west',west),('south',south),('up',up),('down',down)):
        if override:
            texture,coordinates=override
            scale=source_scales.get(texture,(1,1))
            faces[direction]={'uv':[v*scale[i%2] for i,v in enumerate(coordinates)],'texture':'#'+texture}
    element={'name':name,'from':list(start),'to':list(end),'faces':faces,'_group':group}
    if rotation:
        axis,angle,origin=rotation
        assert angle in (-45,-22.5,0,22.5,45),(name,angle)
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


build_shell(cube,polygon)
build_upper(cube,polygon,ART)
deck_meshes,deck_details=build_deck(uv)

texture_paths={
    'materials':'japanesearcades:block/museca_materials','details':'japanesearcades:block/museca_details',
    'display':'japanesearcades:block/museca_display',
    'branding':'japanesearcades:block/museca_branding','marquee':'japanesearcades:block/museca_marquee','particle':'japanesearcades:block/museca_materials',
}

# Minecraft's north-facing UVs run from +X to -X when viewed from the front.
# Mirror our front-view coordinates so the ornaments stay on the photographed right.
for e in elements:
    x0,x1=e['from'][0],e['to'][0]
    e['from'][0],e['to'][0]=16-x1,16-x0
    east=e['faces'].pop('east',None)
    west=e['faces'].pop('west',None)
    if east is not None:e['faces']['west']=east
    if west is not None:e['faces']['east']=west
    if 'rotation' in e:
        e['rotation']['origin'][0]=16-e['rotation']['origin'][0]
        if e['rotation']['axis'] in ('y','z'): e['rotation']['angle']*=-1

# Bake only the opaque exterior. Adjacent pieces do not need internal faces;
# clipped overlaps have exactly one surface owner, eliminating coplanar fights.
# Alpha-bearing cutout pieces must not occlude opaque geometry in the union.
alpha_groups=set()
marquee=[e for e in elements if e['_group'] in alpha_groups]
opaque=[e for e in elements if e['_group'] not in alpha_groups]
elements,surface_details=optimize_surfaces(opaque)
elements.extend(marquee)
surface_details['alpha_elements']=len(marquee)
surface_details['total_exported_faces']=sum(len(e['faces']) for e in elements)

export_museca(elements,deck_meshes,texture_paths,surface_details,deck_details,ROOT)

# Trim unused artwork borders after all runtime and authoring exports exist.
from compact_cabinet_textures import compact_cabinet
compact_cabinet('museca')
