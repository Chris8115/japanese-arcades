"""Studio previews of the standalone fox prototype, using its actual geometry.

Run with Blender in background mode. Pass --hero-only after -- for a fast review.
No Minecraft assets are generated or modified by this script.
"""
from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/sleeping_fox_plush"
PREVIEW_PREFIX = "sleeping_fox_minecraft"
bpy.ops.wm.open_mainfile(filepath=str(ART / "model.blend"))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.threads_mode = "FIXED"
scene.render.threads = 8
scene.render.resolution_x = 1440
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.film_transparent = False

collection = bpy.data.collections["FOX_PLUSH"]
points = [obj.matrix_world @ Vector(corner)
          for obj in collection.all_objects if obj.type == "MESH"
          for corner in obj.bound_box]
lower = Vector(tuple(min(p[i] for p in points) for i in range(3)))
upper = Vector(tuple(max(p[i] for p in points) for i in range(3)))
center = (lower + upper) * .5

world = bpy.data.worlds.new("Fox preview studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.7, .74, .8, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .35
scene.world = world

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, lower.z - .008))
floor = bpy.context.object
floor.name = "Preview floor (not part of model)"
mat = bpy.data.materials.new("Neutral studio floor")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.25, .28, .29, 1)
mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
floor.data.materials.append(mat)


def area(name, position, power, color, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.color = color
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (center - obj.location).to_track_quat("-Z", "Y").to_euler()


area("Softbox key", (-3, -4, 5), 430, (1, .92, .82), 4)
area("Softbox fill", (4, -2, 3), 210, (.86, .93, 1), 3)
area("Softbox rim", (1, 4, 5), 500, (1, .95, .87), 3)

camera_data = bpy.data.cameras.new("Fox preview")
camera = bpy.data.objects.new("Fox preview", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"
camera_data.lens = 50


def render(name, direction, padding=1.22):
    camera.location = center + Vector(direction)
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    inverse = camera.matrix_world.inverted()
    local = [inverse @ point for point in points]
    width = max(p.x for p in local) - min(p.x for p in local)
    height = max(p.y for p in local) - min(p.y for p in local)
    aspect = scene.render.resolution_x / scene.render.resolution_y
    camera_data.ortho_scale = max(width, height * aspect) * padding
    scene.render.filepath = str(ART / name)
    bpy.ops.render.render(write_still=True)


render(f"{PREVIEW_PREFIX}_preview.png", (3.2, -6, 3.0))
if "--hero-only" not in sys.argv:
    render(f"{PREVIEW_PREFIX}_front.png", (0, -6, .85))
    render(f"{PREVIEW_PREFIX}_back.png", (-3.2, 6, 2.8))
    render(f"{PREVIEW_PREFIX}_top.png", (0, -.01, 6))
print("Saved previews of the actual standalone fox mesh; source model unchanged.")
