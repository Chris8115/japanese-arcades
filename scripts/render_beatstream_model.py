"""Render the actual Minecraft cuboids and UVs with Blender, without redesigning them."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

bpy.context.preferences.filepaths.save_version = 0

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/beatstream'
TEXTURES = ROOT / 'src/main/resources/assets/funpackcustom/textures/block'
data = json.loads((ART/'geometry.json').read_text(encoding='utf-8'))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 825
scene.render.resolution_y = 1125
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -.45
scene.world.color = (.17,.17,.17)

materials = {}

def texture_material(tex, glowing):
    key=(tex,glowing)
    if key in materials: return materials[key]
    material=bpy.data.materials.new(tex+('_lit' if glowing else ''))
    material.use_nodes=True
    nodes=material.node_tree.nodes
    bsdf=nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=.52
    image=nodes.new('ShaderNodeTexImage')
    texture_file=data['textures'][tex].split('/')[-1]+'.png'
    image.image=bpy.data.images.load(str(TEXTURES/texture_file),check_existing=True)
    image.interpolation='Closest'
    material.node_tree.links.new(image.outputs['Color'],bsdf.inputs['Base Color'])
    material.node_tree.links.new(image.outputs['Alpha'],bsdf.inputs['Alpha'])
    if glowing:
        material.node_tree.links.new(image.outputs['Color'],bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value=.78 if tex=='screens' else .60
    materials[key]=material
    return material

face_indices={'north':(2,1,0,3),'east':(6,5,1,2),'south':(7,4,5,6),
              'west':(3,0,4,7),'up':(3,7,6,2),'down':(4,0,1,5)}

def world(v): return ((8-v[0])/16,(v[2]-8)/16,v[1]/16)

for e in data['elements']:
    a,b=e['from'],e['to']
    verts=[[a[0],a[1],a[2]],[b[0],a[1],a[2]],[b[0],b[1],a[2]],[a[0],b[1],a[2]],
           [a[0],a[1],b[2]],[b[0],a[1],b[2]],[b[0],b[1],b[2]],[a[0],b[1],b[2]]]
    if 'rotation' in e:
        r=e['rotation'];o=r['origin'];angle=math.radians(r['angle']);c,s=math.cos(angle),math.sin(angle)
        axis=r['axis']
        for i,v in enumerate(verts):
            x,y,z=[v[j]-o[j] for j in range(3)]
            if axis=='x': n=[x,y*c-z*s,y*s+z*c]
            elif axis=='y': n=[x*c+z*s,y,-x*s+z*c]
            else: n=[x*c-y*s,x*s+y*c,z]
            verts[i]=[n[j]+o[j] for j in range(3)]
    mesh=bpy.data.meshes.new(e['name'])
    names=list(face_indices)
    mesh.from_pydata([world(v) for v in verts],[],[face_indices[name] for name in names])
    mesh.update()
    obj=bpy.data.objects.new(e['name'],mesh)
    bpy.context.collection.objects.link(obj)
    uv_layer=mesh.uv_layers.new(name='Cabinet UV')
    for poly,direction in zip(mesh.polygons,names):
        face=e['faces'][direction]
        tex=face['texture'][1:]
        mat=texture_material(tex,'neoforge_data' in face)
        if mat.name not in obj.data.materials: obj.data.materials.append(mat)
        poly.material_index=list(obj.data.materials).index(mat)
        u0,v0,u1,v1=[v/16 for v in face['uv']]
        uvs=[(u0,1-v0),(u0,1-v1),(u1,1-v1),(u1,1-v0)]
        for loop,tex_uv in zip(poly.loop_indices,uvs): uv_layer.data[loop].uv=tex_uv

for face in data.get('meshes',[]):
    mesh=bpy.data.meshes.new(face['name'])
    mesh.from_pydata([world(p) for p in face['vertices']],[],[list(range(len(face['vertices'])))])
    mesh.update()
    obj=bpy.data.objects.new(face['name'],mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(texture_material(face['texture'][1:],face['glow']))
    uv_layer=mesh.uv_layers.new(name='Cabinet UV')
    for loop,(u,v) in zip(mesh.polygons[0].loop_indices,face['uv']):
        uv_layer.data[loop].uv=(u/16,1-v/16)

# Restrained studio environment, separate from the exported game geometry.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015))
floor=bpy.context.object;floor.name='Preview ground'
ground=bpy.data.materials.new('Studio slate');ground.diffuse_color=(.09,.105,.13,1)
ground.use_nodes=True
ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.09,.105,.13,1)
ground.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.75
floor.data.materials.append(ground)

def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,1.4))-obj.location).to_track_quat('-Z','Y').to_euler()

area('Large warm key',(-3,-4,6),650,(1,.90,.77),4)
area('Soft front fill',(3,-3,3),450,(.77,.85,1),3)
area('Top rim',(1,3,5),800,(.83,.80,1),3)
camera_data=bpy.data.cameras.new('Model preview camera')
camera=bpy.data.objects.new('Model preview camera',camera_data)
bpy.context.collection.objects.link(camera);scene.camera=camera
camera_data.type='ORTHO';camera_data.ortho_scale=3.67

def render(name,loc,target=(0,.02,1.46),scale=3.67):
    camera.location=loc
    camera_data.ortho_scale=scale
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ART/name)
    bpy.ops.render.render(write_still=True)

if '--detail-only' not in sys.argv:
    render('beatstream.png',(3,-6,3.35))
    render('beatstream-front.png',(0,-6,2.8))
    render('beatstream-side.png',(6,.02,1.46))
    if '--preview-only' in sys.argv:
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(ART/'beatstream.blend'))
        raise SystemExit(0)
    render('beatstream-back.png',(-3,6,3.6))
    scene.render.resolution_y=825
    render('beatstream-controls.png',(2,-5,3.4),target=(0,-.17,1.52),scale=1.65)
scene.render.resolution_y=825
render('beatstream-marquee.png',(2.5,-6,3.65),target=(0,.05,2.64),scale=1.60)
scene.render.resolution_y=1125
camera_data.ortho_scale=3.67
camera.location=(3,-6,3.35)
camera.rotation_euler=(Vector((0,.02,1.46))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'beatstream.blend'))
print('Rendered exact game geometry and saved the Blender preview scene.')
