"""Render and save the exact exported kiosk geometry in a Blender studio."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/arcade_kiosk'
TEX=ROOT/'src/main/resources/assets/funpackcustom/textures/block'
data=json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1350;scene.render.resolution_y=1750;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.05
scene.world.color=(.22,.22,.22)
materials={}
for key in ('materials','screen','details'):
    for glow in (False,True):
        name=key+('_glow' if glow else '_surface');mat=bpy.data.materials.new(name);mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.33
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/('arcade_kiosk_'+key+'.png')),check_existing=True)
        tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if glow:
            mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.36
        materials[name]=mat

def world(p):return ((8-p[0])/16,(p[2]-8)/16,p[1]/16)
groups={}
for f in data['meshes']:groups.setdefault(f['group'],[]).append(f)
for group,faces in groups.items():
    vertices=[];polygons=[];uvs=[];indices=[]
    for f in faces:
        start=len(vertices);vertices.extend(world(p) for p in f['vertices']);polygons.append(list(range(start,len(vertices))))
        uvs.append(f['uv']);indices.append(list(materials).index(f['texture'][1:]+('_glow' if f['glow'] else '_surface')))
    mesh=bpy.data.meshes.new(group);mesh.from_pydata(vertices,[],polygons);mesh.update()
    obj=bpy.data.objects.new(group,mesh);bpy.context.collection.objects.link(obj)
    for mat in materials.values():mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Kiosk artwork UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):layer.data[loop].uv=(u/16,1-v/16)

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('Slate floor');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.07,.09,.115,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65;floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-4,5),600,(1,.95,.91),4)
area('Cool fill',(3,-3,3),400,(.88,.93,1),3)
area('Top rim',(1,3,5),700,(.86,.94,1),3)
camdata=bpy.data.cameras.new('Kiosk camera');camera=bpy.data.objects.new('Kiosk camera',camdata)
bpy.context.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO'
def render(name,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camdata.ortho_scale=scale;scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)
render('arcade-kiosk.png',(3.4,-6,3.0),(0,0,1),2.49)
render('arcade-kiosk-front.png',(0,-6,1.40),(0,-.05,1),2.35)
camera.location=(3.4,-6,3.0);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=2.49
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'arcade_kiosk.blend'))
print('Rendered exact kiosk geometry and packed original artwork in editable Blender scene.')
