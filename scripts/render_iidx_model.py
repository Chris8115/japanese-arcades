"""Render IIDX LIGHTNING's exported surfaces and preserve an editable, packed Blender scene."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/beatmania-iidx-lightning'
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
    preview = data.get('preview_textures', {}).get(key)
    texture.image = bpy.data.images.load(str(ROOT / preview if preview else TEXTURES / filename), check_existing=True)
    texture.interpolation = 'Closest'
    mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    mat.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
    if glow:
        mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = .44
    materials[identity] = mat
    return mat


def world(point):
    return (16 - point[0]) / 16, point[2] / 16, point[1] / 16


groups = {}
for face in data['meshes']:
    groups.setdefault(face['group'], []).append(face)
for name, faces in groups.items():
    vertices, polygons, uvs, mats, indices = [], [], [], [], []
    for face in faces:
        start = len(vertices)
        vertices.extend(world(point) for point in face['vertices'])
        polygons.append(list(range(start, len(vertices))))
        uvs.append(face['uv'])
        mat = material(face['texture'][1:], face['glow'])
        if mat not in mats:
            mats.append(mat)
        indices.append(mats.index(mat))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in mats:
        mesh.materials.append(mat)
    layer = mesh.uv_layers.new(name='IIDX LIGHTNING source artwork UV')
    for polygon, uv, index in zip(mesh.polygons, uvs, indices):
        polygon.material_index = index
        for loop, (u, v) in zip(polygon.loop_indices, uv):
            layer.data[loop].uv = u / 16, 1 - v / 16

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
camera_data = bpy.data.cameras.new('IIDX LIGHTNING preview camera')
camera = bpy.data.objects.new('IIDX LIGHTNING preview camera', camera_data)
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


render('beatmania-iidx-lightning.png', (4.0, -8, 4.1), (0, 0, 1.40), 3.85)
if '--single-only' not in sys.argv:
    render('beatmania-iidx-lightning-front.png', (0, -8, 2.6), (0, 0, 1.43), 3.50)
    render('beatmania-iidx-lightning-side.png', (7, -.6, 2.6), (0, 0, 1.43), 3.55)
    scene.render.resolution_x, scene.render.resolution_y = 1200, 900
    render('beatmania-iidx-lightning-controls.png', (1.7, -5, 4.6), (0, .1, 1.25), 2.65)
    render('beatmania-iidx-lightning-platform.png', (2.2, -5, 3.6), (0, -.35, .42), 2.90)
scene.render.resolution_x, scene.render.resolution_y = 900, 1200
pose((4.0, -8, 4.1), (0, 0, 1.40), 3.85)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'beatmania-iidx-lightning.blend'))
print('IIDX LIGHTNING previews and packed editable Blender scene saved.')
