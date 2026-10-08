"""Render the exact runtime mesh, save an editable articulated Blender source."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/mech_suit'
data=json.loads((ROOT/'src/main/resources/assets/japanesearcades/meshes/mech_suit.json').read_text())
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1000
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.world.color=(.16,.18,.22)
materials={}

def material(color,glow):
    key=color,glow
    if key in materials:return materials[key]
    mat=bpy.data.materials.new(f'{color:06x}'+('_light' if glow else ''))
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    def linear(channel):
        value=channel/255
        return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    rgb=tuple(linear((color>>n)&255) for n in (16,8,0))
    bsdf.inputs['Base Color'].default_value=(*rgb,1)
    bsdf.inputs['Roughness'].default_value=.35
    if color in (0xC5992E,0xF1CF61,0x525965,0xBFC6C4):bsdf.inputs['Metallic'].default_value=.55
    if glow:
        bsdf.inputs['Emission Color'].default_value=(*rgb,1)
        bsdf.inputs['Emission Strength'].default_value=.6
    materials[key]=mat
    return mat

def world(p):return (p[0],p[2],p[1])

objects={}
for part in data['parts']:
    verts=[];faces=[];normals=[];mats=[];indices=[]
    for color,glow,raw in part['faces']:
        # Coordinate axis exchange reverses winding, so flip polygons once.
        ids=[]
        count=3 if raw[12:18]==raw[18:24] else 4
        for i in range(count):
            ids.append(len(verts));verts.append(world(raw[i*6:i*6+3]));normals.append(world(raw[i*6+3:i*6+6]))
        faces.append(list(reversed(ids)))
        mat=material(color,glow)
        if mat not in mats:mats.append(mat)
        indices.append(mats.index(mat))
    mesh=bpy.data.meshes.new(part['name'])
    mesh.from_pydata(verts,[],faces);mesh.update()
    mesh.normals_split_custom_set_from_vertices(normals)
    obj=bpy.data.objects.new(part['name'],mesh)
    bpy.context.collection.objects.link(obj)
    for mat in mats:mesh.materials.append(mat)
    for poly,index in zip(mesh.polygons,indices):poly.material_index=index;poly.use_smooth=True
    obj['pivot_blocks']=part['pivot'];obj['parent_part']=part['parent']
    pivot=Vector(world(part['pivot']))
    for vertex in mesh.vertices:vertex.co-=pivot
    obj.location=pivot
    objects[part['name']]=obj

bpy.context.view_layer.update()
for part in data['parts']:
    if not part['parent']:continue
    obj=objects[part['name']];parent=objects[part['parent']]
    obj.parent=parent
    obj.matrix_parent_inverse=parent.matrix_world.inverted()
bpy.context.view_layer.update()

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.007))
floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('blue gray floor');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.045,.061,.082,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
floor.data.materials.append(mat)

def area(name,pos,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector((0,0,2.8))-obj.location).to_track_quat('-Z','Y').to_euler()
area('warm key',(-5,-7,9),1900,(1,.95,.85),6)
area('cool fill',(5,-3,6),1500,(.76,.88,1),5)
area('top rim',(1,5,9),2400,(.93,.95,1),4)
camera_data=bpy.data.cameras.new('Mech preview')
camera=bpy.data.objects.new('Mech preview',camera_data);bpy.context.collection.objects.link(camera);scene.camera=camera
camera_data.type='ORTHO'

def render(name,pos,target,scale):
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.ortho_scale=scale
    scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)
render('mech_suit.png',(8,-14,7),(0,0,2.45),6.35)
if '--single-only' not in sys.argv:
    render('mech_suit-front.png',(0,-14,4.2),(0,0,2.50),6.15)
    render('mech_suit-back.png',(-7,13,6),(0,0,2.5),6.2)
    render('mech_suit-head.png',(2.5,-7,5.5),(0,-.04,4.12),2.15)
camera.location=(8,-14,7)
camera.rotation_euler=(Vector((0,0,2.45))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.ortho_scale=6.35
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'mech_suit.blend'))
print('Saved exact runtime mesh preview and editable mesh scene.')
