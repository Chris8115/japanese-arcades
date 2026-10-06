"""Render exported prize meshes directly, including editable packed studio scene."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/arcade_economy';TEX=ROOT/'src/main/resources/assets/funpackcustom/textures/block'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.25;scene.world.color=(.24,.24,.24)
materials={};objects=[]
names=('arcade_cat_plush','rhythm_star_trophy','mini_arcade_cabinet','arcade_poster')
def material(key,glow):
    if (key,glow) in materials:return materials[key,glow]
    mat=bpy.data.materials.new(key+('_lit' if glow else ''));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.48
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/('arcade_prize_'+key+'.png')),check_existing=True);tex.interpolation='Closest'
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    if glow:mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.45
    materials[key,glow]=mat;return mat
for name in names:
    data=json.loads((ART/(name+'.geometry.json')).read_text(encoding='utf-8'))
    verts=[];polys=[];uvs=[];mats=[];indices=[]
    for f in data['meshes']:
        start=len(verts);verts.extend(((8-p[0])/16,(p[2]-8)/16,p[1]/16) for p in f['vertices']);polys.append(list(range(start,len(verts))));uvs.append(f['uv'])
        mat=material(f['texture'][1:],f['glow'])
        if mat not in mats:mats.append(mat)
        indices.append(mats.index(mat))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],polys);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);objects.append(obj)
    for mat in mats:mesh.materials.append(mat)
    layer=mesh.uv_layers.new(name='Original printed art UV')
    for poly,uv,index in zip(mesh.polygons,uvs,indices):
        poly.material_index=index
        for loop,(u,v) in zip(poly.loop_indices,uv):layer.data[loop].uv=(u/16,1-v/16)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object;floor.name='Studio floor'
mat=bpy.data.materials.new('Neutral studio floor');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.09,.125,.15,1);floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-4,5),600,(1,.96,.86),4);area('Cool fill',(4,-3,4),440,(.84,.95,1),4);area('Top rim',(1,4,6),650,(1,.92,.82),3)
cam=bpy.data.cameras.new('Prize camera');camera=bpy.data.objects.new('Prize camera',cam);bpy.context.collection.objects.link(camera);scene.camera=camera;cam.type='ORTHO'
def render(filename,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=scale
    scene.render.filepath=str(ART/filename);bpy.ops.render.render(write_still=True)
for current in objects:
    for obj in objects:obj.hide_render=obj!=current
    render(current.name+'.png',(2.1,-5,2.55),(0,0,.45),1.20)
for i,obj in enumerate(objects):obj.hide_render=False;obj.location.x=(i-1.5)*1.12
scene.render.resolution_x=2000;scene.render.resolution_y=700
render('arcade-prizes.png',(1.6,-10,4.0),(0,0,.43),4.65)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'arcade_prizes.blend'))
print('Arcade prize previews and packed editable Blender scene complete.')
