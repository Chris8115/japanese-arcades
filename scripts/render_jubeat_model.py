"""Studio views of the actual native Jubeat source meshes and packed .blend."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/jubeat'
TEX=ROOT/'src/main/resources/assets/funpackcustom/textures/block'
data=json.loads((ART/'geometry.json').read_text(encoding='utf-8'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=36;scene.cycles.use_denoising=True
scene.render.resolution_x=1300;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
scene.world.color=(.20,.20,.20)
materials={}
for f in data['meshes']:
    key=f['texture'][1:];lit=f['glow'];name=(key,lit)
    if name in materials:continue
    mat=bpy.data.materials.new(key+('_lit' if lit else ''));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.33
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(TEX/(data['textures'][key].split('/')[-1]+'.png')),check_existing=True)
    tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    if lit:
        bsdf.inputs['Roughness'].default_value=.8
        bsdf.inputs['Specular IOR Level'].default_value=.05
        mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.36
    materials[name]=mat
def world(p):return ((8-p[0])/16,(p[2]-8)/16,p[1]/16)
groups={}
for f in data['meshes']:groups.setdefault(f['group'],[]).append(f)
for group,faces in groups.items():
    vertices=[];polygons=[];uvs=[];indices=[]
    for f in faces:
        start=len(vertices);vertices.extend(world(p) for p in f['vertices']);polygons.append(list(range(start,len(vertices))))
        uvs.append(f['uv']);indices.append(list(materials).index((f['texture'][1:],f['glow'])))
    mesh=bpy.data.meshes.new(group);mesh.from_pydata(vertices,[],polygons);mesh.update()
    obj=bpy.data.objects.new(group,mesh);bpy.context.collection.objects.link(obj)
    for mat in materials.values():mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Jubeat artwork UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):layer.data[loop].uv=(u/16,1-v/16)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('Slate floor');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.065,.075,.09,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.62;floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Large warm key',(-3,-4,5),650,(1,.95,.9),4)
area('Cool front fill',(3,-3,3),520,(.80,.90,1),3)
area('Upper rim',(1,3,5),740,(.77,.90,1),3)
camdata=bpy.data.cameras.new('Jubeat camera');camera=bpy.data.objects.new('Jubeat camera',camdata)
bpy.context.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO'
def render(name,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camdata.ortho_scale=scale;scene.render.filepath=str(ART/name);bpy.ops.render.render(write_still=True)
if '--remaining-only' not in sys.argv:
    render('jubeat.png',(3.5,-6,3.3),(0,0,1.23),2.95)
    render('jubeat-side.png',(6,0,1.3),(0,0,1.3),2.95)
if '--preview-only' not in sys.argv:
    render('jubeat-front.png',(0,-6,2.55),(0,0,1.23),2.85)
    render('jubeat-back.png',(-3.5,6,3.2),(0,0,1.23),2.95)
    scene.render.resolution_x=1500;scene.render.resolution_y=1200
    render('jubeat-controls.png',(1.1,-4,4.4),(0,-.06,1.45),1.32)
camera.location=(3.5,-6,3.3);camera.rotation_euler=(Vector((0,0,1.23))-camera.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=2.95
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'jubeat.blend'))
print('Jubeat mesh renders and packed editable Blender scene complete.')
