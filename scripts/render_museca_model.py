"""Render the exact MÚSECA game geometry and packed UVs.

Run with Blender --background --python scripts/render_museca_model.py.
Append -- --front-only for a quick front preview or -- --detail-only for the
controls, screen and marquee. Every mode saves a packed editable .blend scene.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/museca'
TEXTURES = ROOT / 'src/main/resources/assets/funpackcustom/textures/block'
data = json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version = 0

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.cycles.samples = 12 if '--quick' in sys.argv else 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -.45
scene.world.color = (.17,.17,.17)

materials = {}


def texture_material(tex, glowing):
    key = (tex, glowing)
    if key in materials:
        return materials[key]
    material = bpy.data.materials.new(tex+('_lit' if glowing else ''))
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .52
    image = nodes.new('ShaderNodeTexImage')
    texture_file = data['textures'][tex].split('/')[-1]+'.png'
    image.image = bpy.data.images.load(str(TEXTURES/texture_file), check_existing=True)
    image.interpolation = 'Closest'
    material.node_tree.links.new(image.outputs['Color'], bsdf.inputs['Base Color'])
    material.node_tree.links.new(image.outputs['Alpha'], bsdf.inputs['Alpha'])
    if glowing:
        if tex in ('display', 'branding'):
            # Full-bright LCD/sign pixels do not acquire an extra diffuse white
            # wash from the studio lamps. This preserves the real red/black art.
            emission = nodes.new('ShaderNodeEmission')
            material.node_tree.links.new(image.outputs['Color'], emission.inputs['Color'])
            emission.inputs['Strength'].default_value = 1.0
            material.node_tree.links.new(emission.outputs[0], nodes.get('Material Output').inputs['Surface'])
        else:
            material.node_tree.links.new(image.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = .9
    materials[key] = material
    return material


face_indices = {'north':(2,1,0,3), 'east':(6,5,1,2), 'south':(7,4,5,6),
                'west':(3,0,4,7), 'up':(3,7,6,2), 'down':(4,0,1,5)}


def world(v):
    return ((8-v[0])/16, (v[2]-8)/16, v[1]/16)


# These are the same mesh faces exported to Minecraft; leave their shading flat
# so the preview cannot conceal faceting with Blender-only smoothing.
mesh_groups = {}
for face in data.get('meshes', []):
    mesh_groups.setdefault(face['group'], []).append(face)
for name, faces in mesh_groups.items():
    vertices, polygons, coordinates, group_materials, indices = [], [], [], [], []
    for face in faces:
        start = len(vertices)
        vertices.extend(world(point) for point in face['vertices'])
        polygons.append(list(range(start, len(vertices))))
        coordinates.append(face['uv'])
        mat = texture_material(face['texture'][1:], face['glow'])
        if mat not in group_materials:
            group_materials.append(mat)
        indices.append(group_materials.index(mat))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in group_materials:
        mesh.materials.append(mat)
    layer = mesh.uv_layers.new(name='Native MUSECA surface UV')
    for polygon, uv, index in zip(mesh.polygons, coordinates, indices):
        polygon.material_index = index
        for loop, (u, v) in zip(polygon.loop_indices, uv):
            layer.data[loop].uv = u / 16, 1 - v / 16


# Studio objects are separate from the exported cabinet model.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.015))
floor = bpy.context.object
floor.name = 'Preview ground'
ground = bpy.data.materials.new('Studio slate')
ground.diffuse_color = (.09,.105,.13,1)
ground.use_nodes = True
ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.09,.105,.13,1)
ground.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .75
floor.data.materials.append(ground)


def area(name, loc, power, color, size):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power
    light.color = color
    light.shape = 'DISK'
    light.size = size
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector((0,-.15,1.4))-obj.location).to_track_quat('-Z','Y').to_euler()


area('Large warm key', (-3,-4,6), 650, (1,.90,.77), 4)
area('Soft front fill', (3,-3,3), 450, (.77,.85,1), 3)
area('Top rim', (1,3,5), 800, (.83,.80,1), 3)
camera_data = bpy.data.cameras.new('Model preview camera')
camera = bpy.data.objects.new('Model preview camera', camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 3.85


def render(name, loc, target=(0,-.15,1.48), scale=3.85):
    camera.location = loc
    camera_data.ortho_scale = scale
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(ART/name)
    bpy.ops.render.render(write_still=True)


# The five-spinner deck and low pedal project toward negative world Y;
# the tilted screen and layered marquee rise behind them.
front_location = (3,-6,3.5)
front_target = (0,-.15,1.48)
if '--front-only' in sys.argv:
    render('museca-front.png', front_location, target=front_target)
else:
    if '--detail-only' not in sys.argv:
        render('museca-front.png', front_location, target=front_target)
        render('museca-back.png', (-3,6,3.65), target=front_target)
        render('museca-side.png', (6,-.1,1.48), target=(0,-.1,1.48))
    scene.render.resolution_y = 1100
    render('museca-controls.png', (2.2,-5.6,3.7), target=(0,-.55,1.18), scale=1.90)
    render('museca-screen.png', (2,-5.4,3.0), target=(0,.13,1.92), scale=1.80)
    render('museca-marquee.png', (2.5,-6,3.9), target=(0,.28,2.76), scale=1.68)

# Save the packed editable scene on the complete front view in every mode.
scene.render.resolution_y = 1500
camera_data.ortho_scale = 3.85
camera.location = front_location
camera.rotation_euler = (Vector(front_target)-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'museca.blend'))
print('Rendered exact MÚSECA game geometry and saved the packed Blender preview scene.')
