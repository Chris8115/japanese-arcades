"""Render Bombergirl's shipped OBJ and preserve a packed, editable Blender scene."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/bombergirl'
TEXTURES = ROOT / 'src/main/resources/assets/japanesearcades/textures/block'
data = json.loads((ART / 'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -.25
scene.world.color = (.19, .19, .19)
materials = {}


def material(key, glow):
    identity = key, glow
    if identity in materials:
        return materials[identity]
    mat = bpy.data.materials.new(key + ('_lit' if glow else ''))
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .40
    texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
    filename = data['textures'][key].split('/')[-1] + '.png'
    texture.image = bpy.data.images.load(str(TEXTURES / filename), check_existing=True)
    texture.interpolation = 'Closest'
    mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
    if glow:
        mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = .44
    materials[identity] = mat
    return mat


def world(point):
    return (8 - point[0]) / 16, (point[2] - 8) / 16, point[1] / 16


# Render the final optimized shipped OBJ, not a parallel authoring mesh.
# This catches exporter winding, partition, and UV mistakes before native QA.
positions=[];uvs=[];groups={};current=None
objpath=ROOT/'src/main/resources/assets/japanesearcades/models/item/bombergirl.obj'
for line in objpath.read_text().splitlines():
    parts=line.split()
    if not parts:continue
    if parts[0]=='v':positions.append(tuple(float(n)*16 for n in parts[1:4]))
    elif parts[0]=='vt':uvs.append(tuple(float(n) for n in parts[1:3]))
    elif parts[0]=='usemtl':current=parts[1]
    elif parts[0]=='f':
        refs=[r.split('/') for r in parts[1:]]
        groups.setdefault(current,[]).append(([(positions[int(r[0])-1]) for r in refs],[(uvs[int(r[1])-1]) for r in refs]))
for name,faces in groups.items():
    vertices=[];polygons=[];face_uvs=[]
    for points,face_uv in faces:
        start=len(vertices);vertices.extend(world(p) for p in points)
        polygons.append(list(range(start,len(vertices))));face_uvs.append(face_uv)
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],polygons);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    key=name.rsplit('_',1)[0];glow=name.endswith('_glow')
    mesh.materials.append(material(key,glow))
    layer=mesh.uv_layers.new(name='Shipped OBJ UVs')
    for polygon,coords in zip(mesh.polygons,face_uvs):
        for loop,uv in zip(polygon.loop_indices,coords):layer.data[loop].uv=uv

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.012))
floor = bpy.context.object
floor.name = 'Preview floor'
mat = bpy.data.materials.new('Slate studio floor')
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.07, .09, .115, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .76
floor.data.materials.append(mat)


def area(name, location, power, color, size):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.color, light.shape, light.size = power, color, 'DISK', size
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 1.5)) - obj.location).to_track_quat('-Z', 'Y').to_euler()


area('Warm key', (-4, -5, 6), 750, (1, .93, .83), 4)
area('Cool fill', (4, -4, 4), 540, (.84, .91, 1), 4)
area('Top rim', (1, 4, 6), 850, (1, .92, .79), 3)
camera_data = bpy.data.cameras.new('Bombergirl preview camera')
camera = bpy.data.objects.new('Bombergirl preview camera', camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'


def pose(location, target, scale):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.ortho_scale = scale


def render(name, location, target, scale):
    pose(location, target, scale)
    scene.render.filepath = str(ART / name)
    bpy.ops.render.render(write_still=True)


render('bombergirl.png', (4.0, -8, 3.7), (0, 0, 1.48), 3.45)
if '--single-only' not in sys.argv:
    render('bombergirl-front.png', (0, -8, 2.3), (0, 0, 1.48), 3.25)
    render('bombergirl-side.png', (7, -.6, 2.6), (0, 0, 1.48), 3.25)
    scene.render.resolution_x, scene.render.resolution_y = 1200, 900
    render('bombergirl-controls.png', (1.6, -4.6, 3.6), (0, -.12, 1.12), 1.60)
scene.render.resolution_x, scene.render.resolution_y = 900, 1200
pose((4.0, -8, 3.7), (0, 0, 1.48), 3.45)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'bombergirl.blend'))
print('Bombergirl previews and packed editable Blender scene saved.')
