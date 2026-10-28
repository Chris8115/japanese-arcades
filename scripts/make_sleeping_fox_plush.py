"""Build the editable sleeping fox plush reward source with Blender's mesh tools.

Run: blender --background --python scripts/make_sleeping_fox_plush.py
Only the FOX_PLUSH mesh collection is saved. Run export_sleeping_fox_plush.py
afterward to regenerate the integrated reward's static Minecraft resources.
One Blender unit is one block; front is -Y, up is +Z. Native pixel detail uses UVs.
"""
from pathlib import Path
import bpy
import json
import math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "art/sleeping_fox_plush"


def material(name, hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # Hex swatches describe display/sRGB colors; shader inputs are linear.
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*linear, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*linear, 1)
    shader.inputs["Roughness"].default_value = .94
    shader.inputs["Specular IOR Level"].default_value = .16
    return mat


def move_to_collection(obj):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def finish_mesh(obj, name, mat, bevel=0, segments=2):
    obj.name = name
    move_to_collection(obj)
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if bevel:
        modifier = obj.modifiers.new("Sewn cushion edge - applied geometry", "BEVEL")
        modifier.width = bevel
        modifier.segments = segments
        modifier.affect = 'EDGES'
        modifier.limit_method = 'ANGLE'
        modifier.angle_limit = math.radians(25)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    for face in obj.data.polygons:
        face.use_smooth = False
    obj["part"] = name
    obj["construction"] = "Applied low-poly mesh; flat normals; no subdivision"
    obj.select_set(False)
    return obj


def cushion(name, center, dimensions, mat, bevel=.04, segments=2, rotation=None):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish_mesh(obj, name, mat, bevel, segments)
    if rotation:
        obj.rotation_euler = rotation
    return obj


def mesh(name, verts, faces, mat, bevel=0, segments=2):
    bpy.ops.object.select_all(action='DESELECT')
    data = bpy.data.meshes.new(name + "_mesh")
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    finish_mesh(obj, name, mat, bevel, segments)
    return obj


def stroke(name, a, b, radius, mat, sides=6):
    a, b = Vector(a), Vector(b)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=(b-a).length,
                                      end_fill_type='NGON', location=(a+b)/2)
    obj = bpy.context.object
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return finish_mesh(obj, name, mat)


def front_patch(name, xz, front_y, thickness, mat, bevel=.01):
    verts = [(x, front_y, z) for x, z in xz] + [(x, front_y+thickness, z) for x, z in xz]
    n = len(xz)
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    return mesh(name, verts, faces, mat, bevel)


def read_indexed_png(data):
    """Read the unchanged native 4-bit palette PNG using only Python's stdlib."""
    import struct, zlib
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    offset, compressed, palette, alpha = 8, b'', [], b''
    while offset < len(data):
        n = struct.unpack('>I', data[offset:offset+4])[0]
        kind, payload = data[offset+4:offset+8], data[offset+8:offset+8+n]
        if kind == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', payload)
            assert depth == 4 and color == 3 and interlace == 0
        elif kind == b'PLTE':
            palette = [tuple(payload[i:i+3]) for i in range(0, len(payload), 3)]
        elif kind == b'tRNS': alpha = payload
        elif kind == b'IDAT': compressed += payload
        offset += n+12
    raw = zlib.decompress(compressed)
    stride, rows, previous, at = (width+1)//2, [], [0]*((width+1)//2), 0
    for y in range(height):
        filt = raw[at]; at += 1
        row = list(raw[at:at+stride]); at += stride
        for i in range(stride):
            left, up, corner = row[i-1] if i else 0, previous[i], previous[i-1] if i else 0
            if filt == 1: pred = left
            elif filt == 2: pred = up
            elif filt == 3: pred = (left+up)//2
            elif filt == 4:
                base = left+up-corner
                distances = [abs(base-left), abs(base-up), abs(base-corner)]
                pred = [left, up, corner][distances.index(min(distances))]
            else:
                assert filt == 0
                pred = 0
            row[i] = (row[i]+pred)&255
        pixels = []
        for x in range(width):
            index = (row[x//2] >> (4 if x%2 == 0 else 0)) & 15
            pixels.append((*palette[index], alpha[index] if index < len(alpha) else 255))
        rows.append(pixels)
        previous = row
    return rows


def pixel_box(name, center, pixel_size, texture_origin, dimensions=None, rotation=(0, 0, 0), bevel=.003):
    """Six UV-mapped faces preserve vanilla pixel detail without per-pixel geometry."""
    w, h, d = pixel_size
    sx, sy, sz = dimensions or (w*.10, d*.10, h*.10)
    u, v = texture_origin
    vertices, vertex_ids, faces, charts = [], {}, [], []
    def vertex(co):
        key = tuple(round(x, 8) for x in co)
        if key not in vertex_ids:
            vertex_ids[key] = len(vertices); vertices.append(key)
        return vertex_ids[key]
    def face_grid(origin, horizontal, downward, columns, rows, uv):
        origin, horizontal, downward = Vector(origin), Vector(horizontal), Vector(downward)
        assert all(skin[uv[1]+r][uv[0]+c][3] == 255 for r in range(rows) for c in range(columns))
        faces.append(tuple(vertex(x) for x in (origin, origin+downward,
                                               origin+horizontal+downward, origin+horizontal)))
        charts.append([(uv[0]/64, 1-uv[1]/64), (uv[0]/64, 1-(uv[1]+rows)/64),
                       ((uv[0]+columns)/64, 1-(uv[1]+rows)/64), ((uv[0]+columns)/64, 1-uv[1]/64)])
    # Source charts follow vanilla CubeListBuilder's 6-face box unwrap.
    face_grid((-sx/2,-sy/2,sz/2), (sx,0,0), (0,0,-sz), w,h,(u+d,v+d))
    face_grid((sx/2,sy/2,sz/2), (-sx,0,0), (0,0,-sz), w,h,(u+d+w+d,v+d))
    face_grid((sx/2,-sy/2,sz/2), (0,sy,0), (0,0,-sz), d,h,(u,v+d))
    face_grid((-sx/2,sy/2,sz/2), (0,-sy,0), (0,0,-sz), d,h,(u+d+w,v+d))
    face_grid((-sx/2,sy/2,sz/2), (sx,0,0), (0,-sy,0), w,d,(u+d,v))
    face_grid((-sx/2,-sy/2,-sz/2), (sx,0,0), (0,sy,0), w,d,(u+d+w,v))
    obj = mesh(name, vertices, faces, skin_material)
    uv_layer = obj.data.uv_layers.new(name='Vanilla fox UV')
    for face, chart in zip(obj.data.polygons, charts):
        for loop, uv in zip(face.loop_indices, chart):
            uv_layer.data[loop].uv = uv
    if bevel:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        modifier = obj.modifiers.new('Tiny sewn edge - applied', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = 'ANGLE'
        modifier.angle_limit = math.radians(25)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.select_set(False)
    obj.location = center
    obj.rotation_euler = rotation
    obj['reference_dimensions_pixels'] = str(pixel_size)
    obj['pixel_markings'] = 'Native sleeping fox pixels on six UV-mapped faces; no pixel geometry or overlays'
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)
collection = bpy.data.collections.new('FOX_PLUSH')
bpy.context.scene.collection.children.link(collection)
OUT.mkdir(parents=True, exist_ok=True)
skin_path = OUT / 'model.fox_sleep.png'
# Keep the native source file byte-for-byte; exact pixels populate the UV atlas.
if not skin_path.exists():
    import zipfile
    jar = Path.home()/'.gradle/caches/neoformruntime/artifacts/minecraft_1.21.1_client.jar'
    with zipfile.ZipFile(jar) as archive:
        skin_path.write_bytes(archive.read('assets/minecraft/textures/entity/fox/fox_sleep.png'))
skin = read_indexed_png(skin_path.read_bytes())
colors = sorted({p[:3] for row in skin for p in row if p[3] == 255})
swatches = {color: material('Vanilla fox cloth '+''.join('%02X'%c for c in color), ''.join('%02X'%c for c in color)) for color in colors}
orange = swatches[(204,105,32)]
dark = swatches[(6,4,14)]
cream = swatches[(231,217,211)]
tag_ink = material('Muted red woven tag ink', 'B44E3B')

# A compact, mip-aligned atlas: untouched native pixels in the upper-left,
# nearest opaque padding elsewhere, and four solid 16x16 swatches at the bottom.
# This writes exact known pixel data; it does not resample or redraw the skin.
import struct, zlib
opaque = [(x,y,p) for y,row in enumerate(skin) for x,p in enumerate(row) if p[3] == 255]
atlas = []
for y in range(64):
    row = []
    for x in range(64):
        if y >= 48:
            color = [(204,105,32), (6,4,14), (231,217,211), (180,78,59)][x//16]
            row.append((*color,255))
        elif x < 48 and y < 32 and skin[y][x][3] == 255:
            row.append(skin[y][x])
        else:
            row.append(min(opaque, key=lambda p:(p[0]-x)**2+(p[1]-min(y,31))**2)[2])
    atlas.append(row)
def chunk(kind, data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
texture_path = OUT/'model.texture.png'
texture_path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',64,64,8,6,0,0,0))+
                        chunk(b'IDAT',zlib.compress(b''.join(b'\x00'+bytes(c for p in row for c in p) for row in atlas),9))+chunk(b'IEND',b''))
skin_material = material('Vanilla fox UV cloth', 'FFFFFF')
texture = skin_material.node_tree.nodes.new('ShaderNodeTexImage')
texture.image = bpy.data.images.load(str(texture_path))
texture.image.pack()
texture.interpolation = 'Closest'
skin_material.node_tree.links.new(texture.outputs['Color'], skin_material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Vanilla proportions: 8x6x6 head, 2x2x1 ears, 4x2x3 muzzle.
# The sleeping fox rests its snout at the rectangular cream tail tip.
head_center = (-.43, -.13, .51)
pixel_box('01 vanilla-proportioned sleeping head', head_center, (8,6,6), (1,5))
pixel_box('02 protruding cuboid cream muzzle and nose', (-.43,-.58,.31), (4,2,3), (6,18), bevel=.0025)
pixel_box('03 left small square ear', (-.73,-.28,.91), (2,2,1), (8,1), bevel=.002)
pixel_box('04 right small square ear', (-.13,-.28,.91), (2,2,1), (15,1), bevel=.002)

# A longer sideways cuboid body. This is a new sleeping toy pose, not an enlarged
# mounted figure. The single-segment chamfer is only 3mm on a block-scale model.
pixel_box('05 long sleeping cuboid body', (.13,.26,.33), (6,11,6), (24,15),
          dimensions=(.63,.63,1.20), rotation=(math.pi/2,0,-math.pi/2))

# Angular folded tail: one long rectangular vanilla-style tail across the front
# and a short square-root section along the flank. Faces meet rather than overlap.
tail = pixel_box('06 rectangular tail with vanilla cream tip', (.005,-.49,.15), (4,9,5), (30,0),
                dimensions=(.38,.30,1.45), rotation=(math.pi/2,0,math.pi/2), bevel=.002)
cushion('07 square tail root fold', (.64,-.08,.15), (.34,.44,.30), orange, .002, 1)

# Tiny tucked cuboid feet, as plush cues; no extended animal legs or articulated joints.
cushion('08 tucked dark front paw', (.015,-.21,.21), (.17,.23,.13), dark, .003, 1)
cushion('09 tucked dark rear paw', (.40,.51,.07), (.18,.17,.14), dark, .003, 1)

# Small cloth label is the only extra embellishment beyond the vanilla fox forms.
label = cushion('10 small woven prize tag', (.741,.28,.31), (.105,.085,.008), cream, .001, 1,
                (0,math.radians(-12),0))
for i in range(2):
    stripe = cushion('11 prize tag stitch '+str(i), (0,0,0), (.036,.007,.002), tag_ink, 0)
    stripe.matrix_world = label.matrix_world @ __import__('mathutils').Matrix.Translation((.008,-.015+i*.025,.005))

# Ensure winding is outward and all delivered objects contain their actual final geometry.
# Tiny chamfers can meet a pixel-grid corner at duplicate coordinates. Weld only
# coincident vertices and remove collapsed edges before triangulation/export.
import bmesh
for obj in collection.objects:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-8)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
bpy.ops.object.select_all(action='DESELECT')
for obj in collection.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = tail
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

corners = [obj.matrix_world @ Vector(v) for obj in collection.objects for v in obj.bound_box]
min_z = min(v.z for v in corners)
for obj in collection.objects:
    obj.location.z -= min_z
    for face in obj.data.polygons:
        face.use_smooth = False
bpy.context.view_layer.update()
corners = [obj.matrix_world @ Vector(v) for obj in collection.objects for v in obj.bound_box]
low = [min(v[i] for v in corners) for i in range(3)]
high = [max(v[i] for v in corners) for i in range(3)]
parts = []
for obj in collection.objects:
    obj.data.calc_loop_triangles()
    parts.append({"name": obj.name, "vertices": len(obj.data.vertices),
                  "faces": len(obj.data.polygons), "triangles": len(obj.data.loop_triangles)})
faces = sum(p["faces"] for p in parts)
triangles = sum(p["triangles"] for p in parts)
assert faces < 2500, f"Prototype budget exceeded: {faces} faces"
assert not any(obj.modifiers for obj in collection.objects)
assert not any(obj.type != 'MESH' for obj in collection.objects)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene["prototype_only"] = False
scene["front_axis"] = "-Y"
scene["intended_use"] = "Editable optimized source for the integrated oversized sleeping fox arcade plush reward"
for workspace in bpy.data.workspaces:
    for screen in workspace.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.type = 'MATERIAL'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "model.blend"))
bpy.ops.export_scene.gltf(filepath=str(OUT / "model.glb"), export_format='GLB',
                          use_selection=True, export_materials='EXPORT',
                          export_normals=True, export_texcoords=True,
                          export_animations=False, export_cameras=False, export_lights=False)
bpy.ops.wm.obj_export(filepath=str(OUT / "model.obj"), export_selected_objects=True,
                      forward_axis='NEGATIVE_Y', up_axis='Z', export_materials=True,
                      apply_modifiers=True)
manifest = {
    "name": "Minecraft-style Sleeping Fox Plush", "status": "optimized source model for the integrated sleeping_fox_plush arcade reward",
    "generator": "scripts/make_sleeping_fox_plush.py", "blender_version": bpy.app.version_string,
    "collection": "FOX_PLUSH", "units": "1 Blender unit = 1 Minecraft block",
    "axes": {"blender_and_obj": "X width, -Y front, Z up", "glb": "X width, +Z front, +Y up (standard glTF conversion)"},
    "bounds": {"minimum": low, "maximum": high, "dimensions": [high[i]-low[i] for i in range(3)]},
    "faces": faces, "triangles": triangles, "vertices": sum(p["vertices"] for p in parts),
    "mesh_objects": len(parts),
    "material_count": len({obj.data.materials[face.material_index] for obj in collection.objects for face in obj.data.polygons}),
    "authoring_material_count": len(bpy.data.materials),
    "geometry": "Vanilla-proportioned cuboids with tiny one-segment cloth bevels; rectangular folded tail; flat normals; no subdivision",
    "textures": "Exact native 48x32 sleeping-fox pixels mapped onto cuboid faces in a 64x64 atlas, packed in Blender/GLB. Unchanged source retained as model.fox_sleep.png.",
    "optimization": "Replaced per-pixel material geometry with UV-mapped flat faces; approved cuboid bounds and tiny edge bevels retained.",
    "reference": {"game": "Minecraft Java 1.21.1", "geometry": "FoxModel.createBodyLayer", "skin": "assets/minecraft/textures/entity/fox/fox_sleep.png", "head_pixels": [8,6,6], "ears_pixels": [2,2,1], "muzzle_pixels": [4,2,3], "pose_note": "Cuboid sleeping toy reinterpretation; compressed rectangular tail and two tucked plush paws, not a literal vanilla pose export."},
    "grounded": abs(low[2]) < .00001, "parts": parts,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding='utf-8')
print("FOX PLUSH READY " + json.dumps({key: manifest[key] for key in ('faces', 'triangles', 'mesh_objects', 'bounds')}))
