"""Preview exported mob collectibles without approximating their game geometry.

Run with Python/Pillow; a background Blender worker renders the exact geometry
JSONs, then Pillow labels four contact-sheet pages. Use --mobs id,id for a subset.
Outputs live in art/mob_figures/expansion/previews; runtime assets are never edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/mob_figures'
ASSETS = ROOT / 'src/main/resources/assets'
OUT = ART / 'expansion/previews'
DETAIL_MOBS = ('creeper', 'allay', 'breeze', 'ender_dragon', 'warden', 'wither')


def options():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', type=Path, default=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'))
    parser.add_argument('--mobs', help='Comma-separated mob IDs; default is the complete collection.')
    parser.add_argument('--samples', type=int, default=12)
    parser.add_argument('--compose-only', action='store_true', help='Rebuild labels from already rendered thumbnails.')
    parser.add_argument('--blender-worker', action='store_true', help=argparse.SUPPRESS)
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    return parser.parse_args(args)


def roster(args):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from mob_figure_catalog import MOBS
    wanted = set(args.mobs.split(',')) if args.mobs else {entry[0] for entry in MOBS}
    entries = [entry for entry in MOBS if entry[0] in wanted]
    unknown = wanted - {entry[0] for entry in entries}
    if unknown:
        raise ValueError('Unknown mobs: ' + ', '.join(sorted(unknown)))
    return entries


def resource_texture(resource: str) -> Path:
    namespace, path = resource.split(':', 1)
    return ASSETS / namespace / 'textures' / (path + '.png')


def worker(args):
    import bpy
    from mathutils import Vector

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.transparent_max_bounces = 64
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.exposure = -.3
    scene.world.color = (.24, .24, .24)
    scene.render.film_transparent = True
    materials, objects = {}, {}

    def material(resource, glow, two_sided):
        key = (resource, glow, two_sided)
        if key in materials:
            return materials[key]
        path = resource_texture(resource)
        if not path.is_file():
            raise FileNotFoundError(path)
        mat = bpy.data.materials.new(resource + (' glow' if glow else ''))
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        bsdf.inputs['Roughness'].default_value = .82
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        tex.interpolation = 'Closest'
        tint = nodes.new('ShaderNodeVertexColor')
        tint.layer_name = 'Captured color'
        multiply = nodes.new('ShaderNodeMixRGB')
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1
        links.new(tex.outputs['Color'], multiply.inputs[1])
        links.new(tint.outputs['Color'], multiply.inputs[2])
        links.new(multiply.outputs[0], bsdf.inputs['Base Color'])
        alpha = nodes.new('ShaderNodeMath')
        alpha.operation = 'MULTIPLY'
        links.new(tex.outputs['Alpha'], alpha.inputs[0])
        links.new(tint.outputs['Alpha'], alpha.inputs[1])
        cutout = nodes.new('ShaderNodeMath')
        cutout.operation = 'GREATER_THAN'
        cutout.inputs[1].default_value = .1
        links.new(alpha.outputs[0], cutout.inputs[0])
        links.new(cutout.outputs[0], bsdf.inputs['Alpha'])
        geometry = nodes.new('ShaderNodeNewGeometry')
        transparent = nodes.new('ShaderNodeBsdfTransparent')
        mix = nodes.new('ShaderNodeMixShader')
        links.new(geometry.outputs['Backfacing'], mix.inputs[0])
        links.new(bsdf.outputs['BSDF'], mix.inputs[1])
        links.new(transparent.outputs['BSDF'], mix.inputs[2])
        links.new(bsdf.outputs['BSDF'] if two_sided else mix.outputs[0], nodes['Material Output'].inputs['Surface'])
        if glow:
            links.new(multiply.outputs[0], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = .45
        materials[key] = mat
        return mat

    def face_key(face):
        return (tuple(sorted(tuple(point) for point in face['vertices'])), face['texture'],
                bool(face.get('glow', False)), tuple(face.get('color', (1, 1, 1, 1))))

    def load(name):
        if name in objects:
            return objects[name]
        data = json.loads((ART / (name + '.geometry.json')).read_text(encoding='utf-8'))
        verts, polygons, uvs, face_colors, mats, indices = [], [], [], [], [], []
        duplicates = Counter(face_key(face) for face in data['meshes'])
        seen = set()
        for face in data['meshes']:
            key = face_key(face)
            if key in seen:
                continue
            seen.add(key)
            start = len(verts)
            verts.extend(((8 - point[0]) / 16, (point[2] - 8) / 16, point[1] / 16) for point in face['vertices'])
            polygons.append(list(range(start, len(verts))))
            uvs.append(face['uv'])
            color = face.get('color', (1, 1, 1, 1))
            face_colors.append(face.get('colors', [color] * len(face['vertices'])))
            texture_key = face['texture'].removeprefix('#')
            mat = material(data['textures'][texture_key], bool(face.get('glow', False)), duplicates[key] > 1)
            if mat not in mats:
                mats.append(mat)
            indices.append(mats.index(mat))
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], polygons)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        for mat in mats:
            mesh.materials.append(mat)
        uv_layer = mesh.uv_layers.new(name='Exported runtime UV')
        color_layer = mesh.color_attributes.new(name='Captured color', type='FLOAT_COLOR', domain='CORNER')
        for polygon, uv, colors, index in zip(mesh.polygons, uvs, face_colors, indices):
            polygon.material_index = index
            for loop, (u, v), color in zip(polygon.loop_indices, uv, colors):
                uv_layer.data[loop].uv = (u / 16, 1 - v / 16)
                color_layer.data[loop].color = tuple(color) if len(color) == 4 else (*color, 1)
        obj.hide_render = True
        objects[name] = obj
        return obj

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.008))
    floor = bpy.context.object
    floor.name = 'Studio floor'
    floor_mat = bpy.data.materials.new('Neutral studio floor')
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.035, .055, .075, 1)
    floor.data.materials.append(floor_mat)

    def area(name, position, power, color, size):
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.color, light.shape, light.size = power, color, 'DISK', size
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, .4)) - obj.location).to_track_quat('-Z', 'Y').to_euler()

    area('Warm key', (-3, -4, 5), 600, (1, .96, .86), 4)
    area('Cool fill', (4, -3, 4), 440, (.84, .95, 1), 4)
    area('Top rim', (1, 4, 6), 650, (1, .92, .82), 3)
    camera_data = bpy.data.cameras.new('Collection camera')
    camera = bpy.data.objects.new('Collection camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'

    def camera_view(position, target, scale):
        camera.location = position
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera_data.ortho_scale = scale

    def show(names):
        for obj in objects.values():
            obj.hide_render = True
        for name in names:
            load(name).hide_render = False

    def render(path):
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)

    entries = roster(args)
    for index, (mob, _, _) in enumerate(entries):
        name = mob + '_figure'
        show([name])
        objects[name].location = (0, 0, 0)
        scene.render.resolution_x, scene.render.resolution_y = 320, 400
        camera_view((1.2, -5, 2.25), (0, 0, .37), 1.03)
        render(OUT / 'thumbs' / (mob + '.png'))
        print(f'PREVIEW {index + 1}/{len(entries)}: {mob}', flush=True)

    for mob in DETAIL_MOBS:
        if mob not in {entry[0] for entry in entries}:
            continue
        names = ('boxed_' + mob + '_figure', mob + '_figure', mob + '_figure_box')
        show(names)
        for index, name in enumerate(names):
            objects[name].location = ((index - 1) * .94, 0, 0)
        scene.render.resolution_x, scene.render.resolution_y = 1500, 800
        camera_view((.6, -7, 3.1), (0, 0, .41), 3.02)
        render(OUT / ('detail-' + mob + '.png'))
        print(f'DETAIL: {mob}', flush=True)


def compose(args):
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, str(ROOT / 'scripts'))
    from mob_figure_catalog import MOBS, NAMES
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    font = lambda size: ImageFont.truetype(str(font_path), size) if font_path.is_file() else ImageFont.load_default(size=size)
    entries = roster(args)
    columns, rows, cell_w, cell_h, margin = 6, 4, 256, 350, 24
    page_size = columns * rows
    pages = []
    for page_number in range(math.ceil(len(entries) / page_size)):
        chunk = entries[page_number * page_size:(page_number + 1) * page_size]
        used_rows = math.ceil(len(chunk) / columns)
        sheet = Image.new('RGB', (columns * cell_w + 2 * margin, used_rows * cell_h + 2 * margin + 62), '#182332')
        draw = ImageDraw.Draw(sheet)
        draw.text((margin, margin), f'MOB COLLECTION  /  {len(entries)} VANILLA MOBS  /  PAGE {page_number + 1}',
                  fill='#e9ede5', font=font(26))
        for index, (mob, accent, _) in enumerate(chunk):
            x = margin + (index % columns) * cell_w
            y = margin + 62 + (index // columns) * cell_h
            thumb = Image.open(OUT / 'thumbs' / (mob + '.png')).convert('RGBA')
            thumb.thumbnail((240, 300), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y), thumb)
            collection_number = next(i for i, entry in enumerate(MOBS, 1) if entry[0] == mob)
            caption = f'{collection_number:02}  {NAMES[mob]}'
            label_font = font(17)
            while draw.textlength(caption, font=label_font) > cell_w - 12:
                label_font = font(label_font.size - 1)
            draw.text((x + (cell_w - draw.textlength(caption, font=label_font)) / 2, y + 313),
                      caption, fill=accent, font=label_font)
        filename = f'collection-{page_number + 1:02}.jpg'
        sheet.save(OUT / filename, quality=94)
        pages.append(filename)
    sources = {}
    for mob, _, _ in entries:
        path = ART / (mob + '_figure.geometry.json')
        sources[mob] = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / 'preview-index.json').write_text(json.dumps({
        'source': 'Exact exported runtime geometry, original texture resources and face colors',
        'count': len(entries), 'contact_sheets': pages,
        'details': [f'detail-{mob}.png' for mob in DETAIL_MOBS if mob in sources],
        'geometry_sha256': sources,
    }, indent=2) + '\n', encoding='utf-8')
    print(f'Composed {len(pages)} labeled contact sheets for {len(entries)} figures.', flush=True)


def main():
    args = options()
    (OUT / 'thumbs').mkdir(parents=True, exist_ok=True)
    if args.blender_worker:
        worker(args)
        return
    if not args.compose_only:
        command = [str(args.blender), '--background', '--python', str(Path(__file__).resolve()), '--',
                   '--blender-worker', '--samples', str(args.samples)]
        if args.mobs:
            command += ['--mobs', args.mobs]
        log_path = ROOT / 'build/verification/mob-figure-previews/render.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    compose(args)


if __name__ == '__main__':
    main()
