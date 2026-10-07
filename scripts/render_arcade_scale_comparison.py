"""Render Groove Coaster beside Chunithm at their exact shared 1/16 scale.

Run with Blender --background --python scripts/render_arcade_scale_comparison.py.
Reads each cabinet's current exported geometry and packed textures; no cabinet
is resized or given a different camera. Only horizontal placement is changed.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'src/main/resources/assets/japanesearcades/textures/block'
OUTPUT = ROOT / 'art/groove_coaster/groove-coaster-chunithm-scale.png'
MODEL_TO_WORLD = 1 / 16
FACE_INDICES = {
    'north': (2, 1, 0, 3), 'east': (6, 5, 1, 2), 'south': (7, 4, 5, 6),
    'west': (3, 0, 4, 7), 'up': (3, 7, 6, 2), 'down': (4, 0, 1, 5),
}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1800
scene.render.resolution_y = 1350
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -.35
scene.world.color = (.17, .17, .17)
materials = {}


def texture_material(cabinet, data, tex, glowing):
    key = (cabinet, tex, glowing)
    if key in materials:
        return materials[key]
    material = bpy.data.materials.new('_'.join((cabinet, tex, 'lit' if glowing else 'plain')))
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .52
    texture = nodes.new('ShaderNodeTexImage')
    filename = data['textures'][tex].split('/')[-1] + '.png'
    texture.image = bpy.data.images.load(str(TEXTURES / filename), check_existing=True)
    texture.interpolation = 'Closest'
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    material.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
    if glowing:
        material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.1 if tex in ('display', 'branding') else .9
    materials[key] = material
    return material


def transformed_vertices(element):
    a, b = element['from'], element['to']
    verts = [[a[0], a[1], a[2]], [b[0], a[1], a[2]],
             [b[0], b[1], a[2]], [a[0], b[1], a[2]],
             [a[0], a[1], b[2]], [b[0], a[1], b[2]],
             [b[0], b[1], b[2]], [a[0], b[1], b[2]]]
    rotation = element.get('rotation')
    if rotation:
        origin = rotation['origin']
        angle = math.radians(rotation['angle'])
        c, s = math.cos(angle), math.sin(angle)
        for i, v in enumerate(verts):
            x, y, z = [v[j] - origin[j] for j in range(3)]
            axis = rotation['axis']
            if rotation.get('rescale'):
                factor = 1 / math.cos(angle)
                x, y, z = (x if axis == 'x' else x * factor,
                           y if axis == 'y' else y * factor,
                           z if axis == 'z' else z * factor)
            if axis == 'x':
                p = [x, y * c - z * s, y * s + z * c]
            elif axis == 'y':
                p = [x * c + z * s, y, -x * s + z * c]
            else:
                p = [x * c - y * s, x * s + y * c, z]
            verts[i] = [p[j] + origin[j] for j in range(3)]
    return verts


def build_cabinet(cabinet, horizontal_offset):
    data = json.loads((ROOT / 'art' / cabinet / 'geometry.json').read_text(encoding='utf-8'))
    vertices, faces, face_data = [], [], []
    bounds_min, bounds_max = [math.inf] * 3, [-math.inf] * 3
    for element in data['elements']:
        transformed = transformed_vertices(element)
        for point in transformed:
            for axis in range(3):
                bounds_min[axis] = min(bounds_min[axis], point[axis])
                bounds_max[axis] = max(bounds_max[axis], point[axis])
        start = len(vertices)
        # Exactly the same coordinate conversion and model scale for both.
        vertices.extend(((8 - v[0]) * MODEL_TO_WORLD + horizontal_offset,
                         (v[2] - 8) * MODEL_TO_WORLD,
                         v[1] * MODEL_TO_WORLD) for v in transformed)
        for direction, indices in FACE_INDICES.items():
            if direction not in element['faces']:
                continue
            face = element['faces'][direction]
            if not face.get('texture'):
                continue
            faces.append(tuple(start + index for index in indices))
            face_data.append(face)
    # A single mesh per cabinet preserves every face while avoiding thousands
    # of Blender scene objects. Neither geometry nor UVs are simplified.
    mesh = bpy.data.meshes.new(cabinet + '_exact_export')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(cabinet, mesh)
    bpy.context.collection.objects.link(obj)
    uv_layer = mesh.uv_layers.new(name='Exported cabinet UV')
    material_slots = {}
    for poly, face in zip(mesh.polygons, face_data):
        tex = face['texture'][1:]
        mat = texture_material(cabinet, data, tex, 'neoforge_data' in face)
        if mat.name not in material_slots:
            material_slots[mat.name] = len(mesh.materials)
            mesh.materials.append(mat)
        poly.material_index = material_slots[mat.name]
        u0, v0, u1, v1 = [value / 16 for value in face['uv']]
        uvs = [(u0, 1 - v0), (u0, 1 - v1), (u1, 1 - v1), (u1, 1 - v0)]
        turns = face.get('rotation', 0) // 90
        uvs = uvs[turns:] + uvs[:turns]
        for loop, tex_uv in zip(poly.loop_indices, uvs):
            uv_layer.data[loop].uv = tex_uv
    return {
        'model_to_world_scale': MODEL_TO_WORLD,
        'elements': len(data['elements']), 'faces': len(faces),
        'width_blocks': (bounds_max[0] - bounds_min[0]) * MODEL_TO_WORLD,
        'depth_blocks': (bounds_max[2] - bounds_min[2]) * MODEL_TO_WORLD,
        'height_blocks': (bounds_max[1] - bounds_min[1]) * MODEL_TO_WORLD,
    }


offsets = {'groove_coaster': -1.15, 'chunithm': 1.10}
measurements = {name: build_cabinet(name, x) for name, x in offsets.items()}


def plain_material(name, color, roughness=.75):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return material


bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.015))
bpy.context.object.name = 'Shared studio ground'
bpy.context.object.data.materials.append(plain_material('Studio slate', (.073, .088, .111)))
label_material = plain_material('Floor label ivory', (.72, .79, .87))
dimension_material = plain_material('Floor label muted', (.38, .48, .60))


def floor_label(body, x, y, size, material):
    curve = bpy.data.curves.new(body, 'FONT')
    curve.body = body
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = size
    obj = bpy.data.objects.new('Floor label ' + body, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, -.012)
    obj.data.materials.append(material)


for name, title in (('groove_coaster', 'GROOVE COASTER'), ('chunithm', 'CHUNITHM')):
    m = measurements[name]
    floor_label(title, offsets[name], -1.44, .145, label_material)
    dimensions = f"{m['width_blocks']:.2f} W  x  {m['depth_blocks']:.2f} D  x  {m['height_blocks']:.2f} H blocks"
    floor_label(dimensions, offsets[name], -1.61, .061, dimension_material)


def area(name, location, power, color, size):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power
    light.color = color
    light.shape = 'DISK'
    light.size = size
    obj = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, -.15, 1.4)) - obj.location).to_track_quat('-Z', 'Y').to_euler()


area('Large warm key', (-4, -5, 7), 1050, (1, .90, .80), 5)
area('Soft front fill', (5, -4, 4), 700, (.77, .86, 1), 4)
area('Shared top rim', (1, 3, 6), 1000, (.85, .82, 1), 4)
camera_data = bpy.data.cameras.new('Shared scale comparison camera')
camera = bpy.data.objects.new('Shared scale comparison camera', camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 5.75
camera.location = (6.5, -12.5, 6.0)
camera.rotation_euler = (Vector((0, -.28, 1.38)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(OUTPUT)
bpy.ops.render.render(write_still=True)

report = ROOT / 'build/verification/arcade-scale-comparison.json'
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(measurements, indent=2), encoding='utf-8')
print('SAME-SCALE CABINET MEASUREMENTS ' + json.dumps(measurements))
print('Rendered comparison: ' + str(OUTPUT))
