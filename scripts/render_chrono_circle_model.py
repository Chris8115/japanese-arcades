"""Render the exact Chrono Circle game geometry and packed UVs.

Run with Blender --background --python scripts/render_chrono_circle_model.py.
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
ART = ROOT / 'art/chrono_circle'
TEXTURES = ROOT / 'src/main/resources/assets/japanesearcades/textures/block'
data = json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version = 0

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
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
        # Full-bright game faces retain their texture colors under any light.
        # Preserve cutout alpha on the clear, illuminated marquee lettering.
        emission = nodes.new('ShaderNodeEmission')
        material.node_tree.links.new(image.outputs['Color'], emission.inputs['Color'])
        emission.inputs['Strength'].default_value = 1.0
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        mix = nodes.new('ShaderNodeMixShader')
        material.node_tree.links.new(image.outputs['Alpha'], mix.inputs[0])
        material.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
        material.node_tree.links.new(emission.outputs[0], mix.inputs[2])
        material.node_tree.links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])
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
    layer = mesh.uv_layers.new(name='Native Chrono Circle surface UV')
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


# The clock controls and broad floor platform project toward negative world Y;
# the reclined circular display and character hood rise behind them.
front_location = (3,-6,3.5)
front_target = (0,-.15,1.48)
if '--front-only' in sys.argv:
    render('chrono_circle-front.png', front_location, target=front_target)
else:
    if '--detail-only' not in sys.argv:
        render('chrono_circle-front.png', front_location, target=front_target)
        render('chrono_circle-back.png', (-3,6,3.65), target=front_target)
        render('chrono_circle-side.png', (6,-.1,1.48), target=(0,-.1,1.48))
    scene.render.resolution_y = 1100
    render('chrono_circle-controls.png', (2.2,-5.6,3.7), target=(0,-.52,1.50), scale=1.70)
    render('chrono_circle-screen.png', (2,-5.4,3.0), target=(0,-.30,1.63), scale=1.65)
    render('chrono_circle-marquee.png', (2.5,-6,3.9), target=(0,.2,2.49), scale=1.70)

# Save the packed editable scene on the complete front view in every mode.
scene.render.resolution_y = 1500
camera_data.ortho_scale = 3.85
camera.location = front_location
camera.rotation_euler = (Vector(front_target)-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'chrono_circle.blend'))
print('Rendered exact Chrono Circle game geometry and saved the packed Blender preview scene.')
