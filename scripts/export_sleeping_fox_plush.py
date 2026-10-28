"""Export the approved sleeping fox into four static Minecraft block cells.

Run with Blender: blender --background --python scripts/export_sleeping_fox_plush.py
Reads model.blend without changing it. Exact UV colors, tiny chamfers, and silhouette
are preserved; fully hidden faces are discarded and cell boundaries are clipped.
"""
from pathlib import Path
import bpy
import hashlib
import json
import math
import shutil
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/sleeping_fox_plush'
ASSETS = ROOT/'src/main/resources/assets/japanesearcades'
MODEL = ASSETS/'models'
NAME = 'sleeping_fox_plush'
EPS = 1e-8


def area(points):
    return sum((points[i]-points[0]).cross(points[i+1]-points[0]).length/2
               for i in range(1,len(points)-1))


def clean(poly):
    result = []
    for point, uv in poly:
        if not result or (point-result[-1][0]).length > EPS:
            result.append((point,uv))
    if len(result)>1 and (result[0][0]-result[-1][0]).length < EPS:
        result.pop()
    changed = True
    while changed and len(result)>3:
        changed = False
        for i in range(len(result)):
            a,b,c = result[i-1][0],result[i][0],result[(i+1)%len(result)][0]
            if (b-a).cross(c-b).length < 1e-10:
                result.pop(i); changed=True; break
    if len(result)<3 or area([p for p,u in result]) < 1e-12:
        return []
    return result


def clip(poly, axis, value, keep_above):
    out = []
    if not poly:
        return out
    for prev,curr in zip(poly[-1:]+poly[:-1],poly):
        a,b = prev[0][axis]-value,curr[0][axis]-value
        inside_a,inside_b = (a>=-EPS,b>=-EPS) if keep_above else (a<=EPS,b<=EPS)
        if inside_a != inside_b:
            t = a/(a-b)
            point = prev[0].lerp(curr[0],t)
            point[axis] = value
            out.append((point,prev[1].lerp(curr[1],t)))
        if inside_b:
            out.append(curr)
    return clean(out)


def split(poly):
    """Fan into convex quads/triangles; NeoForge OBJ faces must have <=4 corners."""
    if len(poly)<=4:
        return [poly]
    out=[]
    for i in range(1,len(poly)-1,2):
        out.append([poly[0]]+poly[i:min(i+3,len(poly))])
    return out


def clip_plane(poly, normal, origin, keep_inside):
    """Clip an arbitrary plane, retaining affine UVs at every new corner."""
    out=[]
    if not poly:
        return out
    for prev,curr in zip(poly[-1:]+poly[:-1],poly):
        a,b=normal.dot(prev[0]-origin),normal.dot(curr[0]-origin)
        ia,ib=(a>=-EPS,b>=-EPS) if keep_inside else (a<=EPS,b<=EPS)
        if ia!=ib:
            t=a/(a-b)
            out.append((prev[0].lerp(curr[0],t),prev[1].lerp(curr[1],t)))
        if ib:
            out.append(curr)
    return clean(out)


def subtract_contact(poly, cutter):
    """Subtract only the covered part of an opposite-facing coplanar contact."""
    normal=(cutter[1][0]-cutter[0][0]).cross(cutter[2][0]-cutter[0][0]).normalized()
    inside=poly
    outside=[]
    for a,b in zip(cutter,cutter[1:]+cutter[:1]):
        inward=normal.cross(b[0]-a[0]).normalized()
        remainder=clip_plane(inside,inward,a[0],False)
        if remainder:
            outside.append(remainder)
        inside=clip_plane(inside,inward,a[0],True)
        if not inside:
            return [poly],0
    overlap=area([p for p,u in inside])
    return (outside,overlap) if overlap>1e-10 else ([poly],0)


def write_obj(path, polys, offset):
    lines=['# Generated from the approved sleeping fox; static, flat-shaded geometry.',
           'mtllib japanesearcades:models/block/sleeping_fox_plush.mtl',
           'o sleeping_fox_plush','s off','usemtl fox_cloth']
    positions,uvs,pmap,tmap,face_lines=[],[],{},{},[]
    for poly in polys:
        refs=[]
        for point,uv in poly:
            p=tuple(round(point[i]-offset[i],9) for i in range(3))
            t=tuple(round(v,9) for v in uv)
            if p not in pmap:
                pmap[p]=len(positions)+1; positions.append(p)
            if t not in tmap:
                tmap[t]=len(uvs)+1; uvs.append(t)
            refs.append(f'{pmap[p]}/{tmap[t]}')
        face_lines.append('f '+' '.join(refs))
    lines += ['v '+' '.join(f'{n:.9f}' for n in p) for p in positions]
    lines += ['vt '+' '.join(f'{n:.9f}' for n in p) for p in uvs]
    lines += face_lines
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'faces':len(polys),'triangles':sum(len(p)-2 for p in polys),
            'vertices':len(positions),'bounds':{'minimum':[min(p[i] for p in positions) for i in range(3)],
                                              'maximum':[max(p[i] for p in positions) for i in range(3)]},
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def model_json(obj_path, ao=True):
    return {'parent':'minecraft:block/block','loader':'neoforge:obj',
            'model':'japanesearcades:models/'+obj_path,
            'automatic_culling':False,'shade_quads':True,'flip_v':True,
            'emissive_ambient':True,'ambientocclusion':ao,'render_type':'minecraft:solid',
            'textures':{'materials':'japanesearcades:block/'+NAME,
                        'particle':'japanesearcades:block/'+NAME}}


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


bpy.ops.wm.open_mainfile(filepath=str(ART/'model.blend'))
objects=sorted(bpy.data.collections['FOX_PLUSH'].objects,key=lambda o:o.name)
assert all(o.type=='MESH' and not o.modifiers for o in objects)
bpy.context.view_layer.update()
planes={}
for obj in objects:
    normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
    planes[obj]=[(normal_matrix @ face.normal, obj.matrix_world @ obj.data.vertices[face.vertices[0]].co)
                 for face in obj.data.polygons]
source_faces=sum(len(o.data.polygons) for o in objects)
full=[]
removed=[]
solid_uvs={(204,105,32):(.125,.125),(6,4,14):(.375,.125),
           (231,217,211):(.625,.125),(180,78,59):(.875,.125)}
for obj in objects:
    uv_layer=obj.data.uv_layers.active
    for face in obj.data.polygons:
        points=[obj.matrix_world @ obj.data.vertices[obj.data.loops[i].vertex_index].co for i in face.loop_indices]
        # These objects are convex cuboids. A face is hidden only if all its
        # vertices lie within another solid AND its outward side enters that
        # solid. This also removes buried contact faces at coplanar joins (ear
        # bottoms, muzzle rear), without deleting exposed coincident surfaces.
        outward=(obj.matrix_world.to_3x3().inverted().transposed() @ face.normal).normalized()
        beyond=sum(points,Vector())/len(points)+outward*1e-5
        if any(other!=obj and all(all(normal.dot(point-origin)<=1e-6 for normal,origin in plane)
                                 for point in points)
               and all(normal.dot(beyond-origin)<-1e-7 for normal,origin in plane)
               for other,plane in planes.items()):
            removed.append({'part':obj.name,'face':face.index}); continue
        mat=obj.data.materials[face.material_index]
        textured=any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes)
        if textured:
            coords=[Vector(uv_layer.data[i].uv) for i in face.loop_indices]
        else:
            rgb=tuple(round(255*(12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055)) for c in mat.diffuse_color[:3])
            coords=[Vector(solid_uvs[rgb]) for _ in points]
        # Swapping Y/Z reverses handedness: reverse vertex order once so the
        # exported triangle cross products still point outside the fox.
        poly=[(Vector((p.x+1.01,p.z,p.y+1.0675)),uv) for p,uv in zip(points,coords)]
        poly.reverse()
        full.extend(split(clean(poly)))

# Beveled pieces can meet on a plane without one whole face being enclosed.
# Remove their shared interior patches exactly, rather than offsetting surfaces
# or leaving competing coplanar faces. Same-facing exterior faces are untouched.
contacts=[]
contact_clipped=[]
for index,face in enumerate(full):
    normal=(face[1][0]-face[0][0]).cross(face[2][0]-face[0][0]).normalized()
    fragments=[face]
    for other_index,cutter in enumerate(full):
        other_normal=(cutter[1][0]-cutter[0][0]).cross(cutter[2][0]-cutter[0][0]).normalized()
        if normal.dot(other_normal)>-.99999 or max(abs(normal.dot(p-face[0][0])) for p,u in cutter)>1e-6:
            continue
        next_fragments=[]
        for fragment in fragments:
            pieces,overlap=subtract_contact(fragment,cutter)
            if overlap:
                contacts.append({'source_face':index,'contact_face':other_index,'removed_area':overlap})
            next_fragments.extend(pieces)
        fragments=next_fragments
    contact_clipped.extend(piece for fragment in fragments for piece in split(fragment))
full=contact_clipped

(MODEL/'block'/f'{NAME}.mtl').write_text('newmtl fox_cloth\nKa 0 0 0\nKd 1 1 1\nmap_Kd #materials\n',encoding='utf-8')
shutil.copyfile(ART/'model.texture.png',ASSETS/'textures/block'/f'{NAME}.png')
parts={}
world_area=sum(area([p for p,u in f]) for f in full)
clipped_area=0
for part,(cx,cz) in enumerate(((0,0),(1,0),(0,1),(1,1))):
    polys=[]
    for face in full:
        # Assign an original face precisely on a partition plane to one cell,
        # avoiding duplicate surfaces without creating hidden closing caps.
        if any(all(abs(p[axis]-1)<EPS for p,u in face) and cell==0 for axis,cell in ((0,cx),(2,cz))):
            continue
        clipped=face
        for axis,low in ((0,cx),(2,cz)):
            clipped=clip(clipped,axis,low,True)
            clipped=clip(clipped,axis,low+1,False)
        if clipped:
            polys.extend(split(clipped))
    clipped_area+=sum(area([p for p,u in f]) for f in polys)
    parts[str(part)]=write_obj(MODEL/'block'/f'{NAME}_part{part}.obj',polys,(cx,0,cz))
    write_json(MODEL/'block'/f'{NAME}_part{part}.json',model_json(f'block/{NAME}_part{part}.obj'))
assert abs(world_area-clipped_area)<1e-7,(world_area,clipped_area)

item_stats=write_obj(MODEL/'item'/f'{NAME}.obj',full,(.5,0,.5))
item=model_json(f'item/{NAME}.obj',False)
item['gui_light']='side'
item['display']={
    'gui':{'rotation':[25,225,0],'translation':[0,0,0],'scale':[.55,.55,.55]},
    'ground':{'translation':[0,3,0],'scale':[.35,.35,.35]},
    'fixed':{'rotation':[0,180,0],'scale':[.5,.5,.5]},
    'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.38,.38,.38]},
    'thirdperson_lefthand':{'rotation':[75,225,0],'translation':[0,2.5,0],'scale':[.38,.38,.38]},
    'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,1,0],'scale':[.48,.48,.48]},
    'firstperson_lefthand':{'rotation':[0,225,0],'translation':[0,1,0],'scale':[.48,.48,.48]}}
write_json(MODEL/'item'/f'{NAME}.json',item)
variants={}
for direction,rotation in [('north',0),('east',90),('south',180),('west',270)]:
    for part in range(4):
        variant={'model':f'japanesearcades:block/{NAME}_part{part}'}
        if rotation:
            variant['y']=rotation
        variants[f'facing={direction},part={part}']=variant
write_json(ASSETS/'blockstates'/f'{NAME}.json',{'variants':variants})

audit={'source':'art/sleeping_fox_plush/model.blend','source_sha256':hashlib.sha256((ART/'model.blend').read_bytes()).hexdigest(),
       'generator':'scripts/export_sleeping_fox_plush.py','source_faces':source_faces,
       'prior_pixel_geometry_faces':1262,'removed_fully_enclosed_faces':len(removed),'removed_faces':removed,
       'internal_contact_patches_removed':contacts,
       'item':item_stats,'parts':parts,'complete_placed_faces':sum(p['faces'] for p in parts.values()),
       'complete_placed_triangles':sum(p['triangles'] for p in parts.values()),
       'uv_texture':{'path':'textures/block/sleeping_fox_plush.png','width':64,'height':64,'rgba_bytes':16384,'mip_levels':4},
       'geometry':{'static_chunk_model':True,'block_entity':False,'animated':False,'no_partition_caps':True,
                   'front':'north (-Z)','part_offsets_north':[[0,0],[1,0],[0,1],[1,1]],
                   'transform':'Minecraft=(BlenderX+1.01, BlenderZ, BlenderY+1.0675)',
                   'source_surface_area':world_area,'clipped_surface_area':clipped_area},
       'note':'Counts are final OBJ faces, not performance measurements. Native client verification is separate.'}
assert audit['complete_placed_faces']<350
assert item_stats['faces']<300
write_json(ART/'runtime_audit.json',audit)
print('RUNTIME FOX READY '+json.dumps({k:audit[k] for k in ['source_faces','removed_fully_enclosed_faces','complete_placed_faces','complete_placed_triangles']}))
