"""Render the actual exported Taiko mesh and save an editable Blender scene."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/taiko';TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--single-only',action='store_true')
parser.add_argument('--samples',type=int,default=40)
parser.add_argument('--resolution-percent',type=int,default=100)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert args.samples>0 and 1<=args.resolution_percent<=100
data=json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=args.samples;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1750;scene.render.resolution_percentage=args.resolution_percent
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.40
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
def world(p):return ((16-p[0])/16,p[2]/16,p[1]/16)
groups={}
for f in data['meshes']:groups.setdefault(f['group'],[]).append(f)
for name,faces in groups.items():
    vertices=[];polys=[];uvs=[];mats=[];indices=[]
    for f in faces:
        start=len(vertices);vertices.extend(world(p) for p in f['vertices']);polys.append(list(range(start,len(vertices))));uvs.append(f['uv'])
        mat=material(f['texture'][1:],f['glow'])
        if mat not in mats:mats.append(mat)
        indices.append(mats.index(mat))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],polys);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    for mat in mats:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Taiko source artwork UV')
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
    obj.rotation_euler=(Vector((0,0,1.5))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-4,-5,6),750,(1,.93,.83),4)
area('Cool fill',(4,-4,4),540,(.84,.91,1),4)
area('Top rim',(1,4,6),850,(1,.92,.79),3)
camdata=bpy.data.cameras.new('Taiko preview camera');camera=bpy.data.objects.new('Taiko preview camera',camdata)
bpy.context.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO'
def render(name,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale
    scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)
render('taiko.png',(4.7,-8,4.9),(0,-.10,1.46),3.86)
if not args.single_only:
    render('taiko-front.png',(0,-8,3.0),(0,-.10,1.5),3.6)
    render('taiko-drums.png',(2.6,-5,3.9),(0,-.38,1.35),2.8)
camera.location=(4.7,-8,4.9);camera.rotation_euler=(Vector((0,-.10,1.46))-camera.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=3.86
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'taiko.blend'))
print('Taiko previews and packed native-geometry Blender scene saved.')
