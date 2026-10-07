"""Render the actual baked Gachapon meshes, plus sample live inventory overlays.

Sample Minecraft icons are read from the local cached game jar for the preview
only. They are kept under ignored build/ and are not packed into the .blend or
bundled with the mod. The saved Blender scene contains original machine assets.
"""
import json
import math
import sys
import zipfile
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/gachapon'
TEX=ROOT/'src/main/resources/assets/japanesearcades/textures/block'
BUILD=ROOT/'build/gachapon-preview';BUILD.mkdir(parents=True,exist_ok=True)
data=json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=40
scene.cycles.use_denoising=True
scene.render.resolution_x=1450;scene.render.resolution_y=1450;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.2
scene.world.color=(.22,.22,.22)
materials={};sample_images=[];sample_materials=[];sample_meshes=[];sample_objects=[]

def material(name,path,sample=False):
    if name in materials:return materials[name]
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.39
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
    tex.interpolation='Closest'
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
    if sample:sample_images.append(tex.image);sample_materials.append(mat)
    materials[name]=mat
    return mat

def world(p,offset=(0,0,0)):
    return ((8-p[0])/16+offset[0],(p[2]-8)/16+offset[1],p[1]/16+offset[2])

def model(name,faces,offset=(0,0,0)):
    vertices=[];polys=[];uvs=[];indices=[]
    for f in faces:
        start=len(vertices);vertices.extend(world(p,offset) for p in f['vertices'])
        polys.append(list(range(start,len(vertices))));uvs.append(f['uv']);indices.append(0 if f['texture']=='#materials' else 1)
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],polys);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    for tex in ('materials','details'):mesh.materials.append(material('Machine '+tex,TEX/('gachapon_'+tex+'.png')))
    uv_layer=mesh.uv_layers.new(name='Machine UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):uv_layer.data[loop].uv=(u/16,1-v/16)
    return obj

jar=Path.home()/'.gradle/caches/neoformruntime/artifacts/minecraft_1.21.1_client.jar'
items=['diamond','emerald','ender_pearl','nether_star','golden_apple','iron_ingot','amethyst_shard','heart_of_the_sea','totem_of_undying']
if not jar.exists():raise FileNotFoundError('The local Minecraft client jar is required for sample inventory icons: '+str(jar))
with zipfile.ZipFile(jar) as z:
    for item in items:
        p=BUILD/(item+'.png');p.write_bytes(z.read('assets/minecraft/textures/item/'+item+'.png'))

def sample_plane(name,points,path,offset):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([world(p,offset) for p in points],[],[[0,1,2,3]]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mat=material('Preview inventory '+path.stem,path,True);mesh.materials.append(mat)
    uv_layer=mesh.uv_layers.new(name='Live icon UV')
    for loop,uv in zip(mesh.polygons[0].loop_indices,[(0,1),(0,0),(1,0),(1,1)]):uv_layer.data[loop].uv=uv
    sample_meshes.append(mesh);sample_objects.append(obj)
    return obj

def sample_inventory(offset):
    created=[]
    for i,item in enumerate(items):
        x=[11.9,8,4.1][i%3];y=[13.72,11.75,9.78][i//3];r=.775;z=1.48
        created.append(sample_plane('Sample reward '+item,[(x+r,y+r,z),(x+r,y-r,z),(x-r,y-r,z),(x-r,y+r,z)],BUILD/(item+'.png'),offset))
    x,y,z=11.73,7,.935;r=.43
    created.append(sample_plane('Sample emerald price',[(x+r,y+r,z),(x+r,y-r,z),(x-r,y-r,z),(x-r,y+r,z)],BUILD/'emerald.png',offset))
    # Blender's 3D text is an annotation of the client-rendered amount label.
    curve=bpy.data.curves.new('Live price amount','FONT');curve.body='2 ×';curve.size=.050;curve.align_x='CENTER';curve.align_y='CENTER'
    obj=bpy.data.objects.new('Sample live price amount',curve);bpy.context.collection.objects.link(obj)
    obj.location=world((13.66,7,.932),offset);obj.rotation_euler=(math.pi/2,0,0)
    mat=bpy.data.materials.get('White preview lettering')
    if not mat:
        mat=bpy.data.materials.new('White preview lettering');mat.diffuse_color=(1,1,1,1)
    curve.materials.append(mat);created.append(obj);sample_objects.append(obj)
    return created

single=model('Single stackable Gachapon',data['meshes'])
capsule=model('Openable capsule item',data['capsule_meshes'])
capsule.hide_render=True;capsule.hide_viewport=True
single_samples=sample_inventory((0,0,0))
stacked=[];stacked_samples=[]
for x in (-.5,.5):
    for y in (0,1):
        offset=(x,0,y)
        stacked.append(model('Stacked Gachapon %.1f %.1f'%(x,y),data['meshes'],offset))
        stacked_samples.extend(sample_inventory(offset))
for obj in stacked+stacked_samples:obj.hide_render=True;obj.hide_viewport=True

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006));floor=bpy.context.object;floor.name='Studio floor'
ground=bpy.data.materials.new('Studio slate');ground.use_nodes=True
ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.085,.105,.13,1)
ground.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.75;floor.data.materials.append(ground)

def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,.6))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-4,5),500,(1,.95,.86),4)
area('Soft fill',(3,-3,3),400,(.85,.91,1),3)
area('Top rim',(1,3,5),700,(.91,.93,1),3)
camdata=bpy.data.cameras.new('Gachapon preview camera');camera=bpy.data.objects.new('Gachapon preview camera',camdata)
bpy.context.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO'

def render(name,loc,target,scale):
    camera.location=loc;camdata.ortho_scale=scale
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)

render('gachapon-single.png',(2.8,-5,2.7),(0,0,.5),1.66)
if '--single-only' not in sys.argv:
    render('gachapon-front.png',(0,-5,.9),(0,-.08,.5),1.38)
    for obj in [single]+single_samples:obj.hide_render=True;obj.hide_viewport=True
    for obj in stacked+stacked_samples:obj.hide_render=False;obj.hide_viewport=False
    render('gachapon-stacked.png',(3.8,-6,3.3),(0,0,1),3.05)
    for obj in [single]+single_samples:obj.hide_render=False;obj.hide_viewport=False
    for obj in stacked+stacked_samples:obj.hide_render=True;obj.hide_viewport=True
    for obj in [single]+single_samples:obj.hide_render=True
    capsule.hide_render=False
    render('gachapon-capsule.png',(2.3,-5,2.1),(0,0,.5),.97)
    capsule.hide_render=True
    for obj in [single]+single_samples:obj.hide_render=False

# The authoring scene intentionally excludes third-party sample item textures.
for obj in sample_objects:
    if obj.name in bpy.data.objects:bpy.data.objects.remove(obj,do_unlink=True)
for mesh in sample_meshes:
    if mesh.name in bpy.data.meshes:bpy.data.meshes.remove(mesh)
for mat in sample_materials:
    if mat.name in bpy.data.materials:bpy.data.materials.remove(mat)
for image in sample_images:
    if image.name in bpy.data.images:bpy.data.images.remove(image)
camera.location=(2.8,-5,2.7);camdata.ortho_scale=1.66
camera.rotation_euler=(Vector((0,0,.5))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'gachapon.blend'))
print('Rendered exact one-block model and live-inventory sample overlays; saved original-assets-only Blender file.')
