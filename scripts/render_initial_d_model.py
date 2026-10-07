"""Render the actual seven-section source geometry and a one-block-adjacent pair."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/initial_d';TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'
data=json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=36;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.25
scene.world.color=(.19,.19,.19)
materials={}
def material(key,glow):
    name=(key,glow)
    if name in materials:return materials[name]
    mat=bpy.data.materials.new(key+('_lit' if glow else ''));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.40
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/(data['textures'][key].split('/')[-1]+'.png')),check_existing=True)
    tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
    if glow:
        mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.44
    materials[name]=mat;return mat
def world(p):return ((8-p[0])/16,p[2]/16,p[1]/16)
groups={};objects=[]
for f in data['meshes']:groups.setdefault(f['group'],[]).append(f)
for name,faces in groups.items():
    vertices=[];polys=[];uvs=[];mats=[];indices=[]
    for f in faces:
        start=len(vertices);vertices.extend(world(p) for p in f['vertices']);polys.append(list(range(start,len(vertices))));uvs.append(f['uv'])
        mat=material(f['texture'][1:],f['glow'])
        if mat not in mats:mats.append(mat)
        indices.append(mats.index(mat))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],polys);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);objects.append(obj)
    for mat in mats:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Initial D source artwork UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):layer.data[loop].uv=(u/16,1-v/16)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('Slate studio floor');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.07,.09,.11,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.76;floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,-.4,1.4))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-4,-5,6),750,(1,.93,.83),4)
area('Cool fill',(4,-4,4),540,(.84,.91,1),4)
area('Top rim',(1,4,6),850,(1,.92,.79),3)
camdata=bpy.data.cameras.new('Initial D preview camera');camera=bpy.data.objects.new('Initial D preview camera',camdata)
bpy.context.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO'
def point(loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale
def render(name,loc,target,scale):
    point(loc,target,scale);scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)
render('initial-d.png',(4.8,-7,4.2),(0,-.40,1.21),3.85)
if '--single-only' not in sys.argv:
    render('initial-d-front.png',(0,-8,3.35),(0,-.40,1.21),3.50)
    render('initial-d-seat.png',(4.1,1.8,3.9),(0,-1.05,.94),2.9)
    paired=[]
    for obj in objects:
        copy=obj.copy();copy.data=obj.data;bpy.context.collection.objects.link(copy);copy.location.x=1;paired.append(copy)
    render('initial-d-paired.png',(4.8,-7,4.2),(.5,-.40,1.21),4.1)
    for obj in paired:bpy.data.objects.remove(obj,do_unlink=True)
point((4.8,-7,4.2),(0,-.40,1.21),3.85)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'initial_d.blend'))
print('Initial D previews and packed native-geometry Blender scene saved.')
