"""Render exported prize meshes directly, including editable packed studio scene."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/arcade_economy';TEX=ROOT/'src/main/resources/assets/funpackcustom/textures/block'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.65;scene.world.color=(.24,.24,.24)
materials={};objects=[]
names=('hatsune_miku_figure','kasane_teto_figure')
def material(key,glow,paths):
    filename=paths[key].split('/')[-1]+'.png'
    if (filename,glow) in materials:return materials[filename,glow]
    mat=bpy.data.materials.new(filename+('_lit' if glow else ''));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.82
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(TEX/filename),check_existing=True);tex.interpolation='Closest'
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    if glow:mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=.45
    materials[filename,glow]=mat;return mat
for name in names:
    data=json.loads((ART/(name+'.geometry.json')).read_text(encoding='utf-8'))
    verts=[];polys=[];uvs=[];mats=[];indices=[]
    for f in data['meshes']:
        start=len(verts);verts.extend(((8-p[0])/16,(p[2]-8)/16,p[1]/16) for p in f['vertices']);polys.append(list(range(start,len(verts))));uvs.append(f['uv'])
        mat=material(f['texture'][1:],f['glow'],data['textures'])
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
mat=bpy.data.materials.new('Neutral studio floor');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.035,.055,.075,1);floor.data.materials.append(mat)
def area(name,loc,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,.5))-obj.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-4,5),600,(1,.96,.86),4);area('Cool fill',(4,-3,4),440,(.84,.95,1),4);area('Top rim',(1,4,6),650,(1,.92,.82),3)
cam=bpy.data.cameras.new('Prize camera');camera=bpy.data.objects.new('Prize camera',cam);bpy.context.collection.objects.link(camera);scene.camera=camera;cam.type='ORTHO'
def render(filename,loc,target,scale):
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=scale
    scene.render.filepath=str(ART/filename);bpy.ops.render.render(write_still=True)
if '--miku-face-only' in sys.argv:
    objects[1].hide_render=True
    render('miku-face-detail.png',(0,-5,.625),(0,-.12,.625),.46)
    render('hatsune_miku_figure-front.png',(0,-5,1.45),(0,0,.46),1.16)
    sys.exit(0)
if '--teto-face-only' in sys.argv:
    objects[0].hide_render=True
    render('teto-face-detail.png',(0,-5,.67),(0,-.12,.67),.46)
    render('kasane_teto_figure-front.png',(0,-5,1.45),(0,0,.46),1.16)
    sys.exit(0)
if '--pair-only' not in sys.argv:
    for current in objects:
        if '--miku-only' in sys.argv and current.name != 'hatsune_miku_figure':continue
        if '--teto-only' in sys.argv and current.name != 'kasane_teto_figure':continue
        for obj in objects:obj.hide_render=obj!=current
        render(current.name+'.png',(1.9,-5,2.15),(0,0,.46),1.19)
        render(current.name+'-front.png',(0,-5,1.45),(0,0,.46),1.16)
        render(current.name+'-back.png',(-1.7,5,2),(0,0,.46),1.19)
        if current.name == 'hatsune_miku_figure':
            render('miku-face-detail.png',(0,-5,.625),(0,-.12,.625),.46)
        else:
            render('teto-face-detail.png',(0,-5,.67),(0,-.12,.67),.46)
for i,obj in enumerate(objects):obj.hide_render=False;obj.location.x=(i-.5)*1.0
scene.render.resolution_x=1800;scene.render.resolution_y=1050
render('arcade-prizes.png',(1.0,-8,2.7),(0,0,.46),2.12)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'arcade_prizes.blend'))
print('Arcade prize previews and packed editable Blender scene complete.')
