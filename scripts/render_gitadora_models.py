"""Render the actual shipped GITADORA inventory OBJ meshes; save packed Blender files."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
ART=ROOT/'art/gitadora'
bpy.context.preferences.filepaths.save_version=0

def render_model(kind):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ident='gitadora_'+kind;out=ART/kind
    data=json.loads((out/'geometry.json').read_text())
    objtext=(ASSETS/'models/item'/f'{ident}.obj').read_text()
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
    scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.12
    scene.world=bpy.data.worlds.new('Studio world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.20,.24,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.38
    verts=[];texcoords=[];groups={};material_name=None
    for line in objtext.splitlines():
        fields=line.split()
        if not fields:continue
        if fields[0]=='v':
            x,y,z=map(float,fields[1:]);verts.append((.5-x,z-.5,y))
        elif fields[0]=='vt':texcoords.append(tuple(map(float,fields[1:])))
        elif fields[0]=='usemtl':material_name=fields[1]
        elif fields[0]=='f':
            face=[];uv=[]
            for field in fields[1:]:
                indices=field.split('/');face.append(verts[int(indices[0])-1]);uv.append(texcoords[int(indices[1])-1])
            groups.setdefault(material_name,[]).append((face,uv))
    collection=bpy.data.collections.new('GITADORA_'+kind.upper());scene.collection.children.link(collection)
    for name,faces in groups.items():
        glow=name.endswith('_glow');key=name[:-5] if glow else name[:-8]
        mat=bpy.data.materials.new(name);mat.use_nodes=True
        bsdf=mat.node_tree.nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=.5
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSETS/'textures/block'/f'gitadora_{key}.png'));tex.interpolation='Closest'
        mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if glow:
            mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.42
        points=[];polys=[]
        for vertices,uv in faces:
            first=len(points);points.extend(vertices);polys.append(list(range(first,len(points))))
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],polys);mesh.update();mesh.materials.append(mat)
        obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj)
        layer=mesh.uv_layers.new(name='Runtime OBJ UV')
        for poly,(_,uv) in zip(mesh.polygons,faces):
            for loop,value in zip(poly.loop_indices,uv):layer.data[loop].uv=value
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));floor=bpy.context.object;floor.name='Preview floor'
    mat=bpy.data.materials.new('Slate');mat.diffuse_color=(.10,.12,.15,1);floor.data.materials.append(mat)
    def area(name,location,power,color,size):
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
        o=bpy.data.objects.new(name,light);scene.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Warm key',(-4,-5,6),800,(1,.93,.86),4)
    area('Cool fill',(4,-4,4),650,(.83,.91,1),4)
    area('Top rim',(1,4,6),950,(1,.95,.88),3)
    camera_data=bpy.data.cameras.new('Camera');camera=bpy.data.objects.new('Camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO'
    def shot(name,location,target,scale):
        camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=scale
        scene.render.filepath=str(out/name)
        if '--save-only' not in sys.argv:bpy.ops.render.render(write_still=True)
    shot(ident+'.png',(4,-8,4.2),(0,0,1.46),3.85 if kind=='drummania' else 3.45)
    if '--single-only' not in sys.argv:
        shot(ident+'-front.png',(0,-9,2.9),(0,0,1.46),3.55 if kind=='drummania' else 3.35)
        if kind=='drummania':
            scene.render.resolution_x=1200;scene.render.resolution_y=900
            shot(ident+'-controls.png',(2.8,-5,4.5),(0,-.22,1.2),2.7)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/(ident+'.blend')))
    print('RENDERED '+ident)

kinds=[k for k in ('guitarfreaks','drummania') if k in sys.argv] or ['guitarfreaks','drummania']
for kind in kinds:render_model(kind)
