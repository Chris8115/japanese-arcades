"""Render all mob collectibles directly from their exported runtime geometry."""
import json
import sys
from collections import Counter
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/mob_figures';TEX=ROOT/'src/main/resources/assets/funpackcustom/textures/block'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
scene.cycles.transparent_max_bounces=64
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.3;scene.world.color=(.24,.24,.24)
materials={};objects=[]
mobs=('creeper','zombie','skeleton','enderman','slime','axolotl')
names=tuple(name for mob in mobs for name in ('boxed_'+mob+'_figure',mob+'_figure',mob+'_figure_box'))
def material(key,glow,paths,two_sided=False):
    filename=paths[key].split('/')[-1]+'.png'
    if (filename,glow,two_sided) in materials:return materials[filename,glow,two_sided]
    mat=bpy.data.materials.new(filename+('_lit' if glow else ''));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.82
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/filename),check_existing=True);tex.interpolation='Closest'
    mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    # Minecraft culls the reverse of each quad. Match that for the separate
    # front/back faces used by thin package windows and axolotl gills.
    geometry=mat.node_tree.nodes.new('ShaderNodeNewGeometry')
    transparent=mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    mix=mat.node_tree.nodes.new('ShaderNodeMixShader')
    mat.node_tree.links.new(geometry.outputs['Backfacing'],mix.inputs[0])
    mat.node_tree.links.new(bsdf.outputs['BSDF'],mix.inputs[1])
    mat.node_tree.links.new(transparent.outputs['BSDF'],mix.inputs[2])
    mat.node_tree.links.new(bsdf.outputs['BSDF'] if two_sided else mix.outputs[0],mat.node_tree.nodes['Material Output'].inputs['Surface'])
    if glow:mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.45
    materials[filename,glow,two_sided]=mat;return mat
for name in names:
    data=json.loads((ART/(name+'.geometry.json')).read_text(encoding='utf-8'))
    verts=[];polys=[];uvs=[];mats=[];indices=[]
    # Opposite zero-thickness quads must become a single two-sided studio face;
    # coincident transparent rays otherwise hide the gills or render them black.
    face_key=lambda f: (tuple(sorted(tuple(p) for p in f['vertices'])),f['texture'])
    duplicates=Counter(face_key(f) for f in data['meshes']);seen=set()
    for f in data['meshes']:
        key=face_key(f)
        if key in seen:continue
        seen.add(key)
        start=len(verts);verts.extend(((8-p[0])/16,(p[2]-8)/16,p[1]/16) for p in f['vertices']);polys.append(list(range(start,len(verts))));uvs.append(f['uv'])
        mat=material(f['texture'][1:],f['glow'],data['textures'],duplicates[key]>1)
        if mat not in mats:mats.append(mat)
        indices.append(mats.index(mat))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],polys);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);objects.append(obj)
    for mat in mats:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Original printed art UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):layer.data[loop].uv=(u/16,1-v/16)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('Neutral studio floor');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.035,.055,.075,1);floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-4,5),600,(1,.96,.86),4);area('Cool fill',(4,-3,4),440,(.84,.95,1),4);area('Top rim',(1,4,6),650,(1,.92,.82),3)
cam=bpy.data.cameras.new('Prize camera');camera=bpy.data.objects.new('Prize camera',cam);bpy.context.collection.objects.link(camera);scene.camera=camera;cam.type='ORTHO'
def render(filename,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=scale
    scene.render.filepath=str(ART/filename);bpy.ops.render.render(write_still=True)

# Six matching pairs: filled packaging behind its separate loose figure.
def collection_layout():
    for i,obj in enumerate(objects):
        mob,form=divmod(i,3)
        obj.hide_render=form==2
        obj.location=((mob-2.5)*.83, .36 if form==0 else -.46, 0)
collection_layout()
scene.render.resolution_x=1800;scene.render.resolution_y=950
render('mob-collection.png',(1.15,-9,4.4),(0,0,.40),5.25)
for i,obj in enumerate(objects):
    obj.hide_render=i>=3
    obj.location=((i-1)*.92,0,0)
scene.render.resolution_x=1400;scene.render.resolution_y=850
render('boxed-loose-empty.png',(1.0,-7,3.0),(0,0,.42),2.93)
collection_layout()
scene.render.resolution_x=1800;scene.render.resolution_y=950
camera.location=(1.15,-9,4.4);camera.rotation_euler=(Vector((0,0,.40))-camera.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=5.25
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'mob_collection.blend'))
print('Mob figure previews and packed editable Blender scene complete.')
