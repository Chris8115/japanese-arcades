"""Export the reference-based Miku and Teto figures as native Minecraft meshes."""
import base64
import json
import uuid
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import miku_figure_geometry
import teto_figure_geometry

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/funpackcustom'
TEX=ASSETS/'textures/block'; ART=ROOT/'art/arcade_economy'
LOOT=ROOT/'src/main/resources/data/funpackcustom/loot_table/blocks'
FIGURES=[('hatsune_miku_figure','Hatsune Miku Figure','HATSUNE MIKU',miku_figure_geometry),
         ('kasane_teto_figure','Kasane Teto Figure','KASANE TETO',teto_figure_geometry)]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def textures(name,colors,plate):
    assert len(colors)<=64
    palette=Image.new('RGB',(256,256),'#171e27');draw=ImageDraw.Draw(palette)
    for i,color in enumerate(colors.values()):
        x,y=(i%8)*32,(i//8)*32;draw.rectangle((x,y,x+31,y+31),fill=color)
    palette.save(TEX/(name+'_materials.png'))
    plaque=Image.new('RGB',(384,64),'#182632');draw=ImageDraw.Draw(plaque)
    draw.rectangle((5,5,378,58),fill='#e6bd82',outline='#b08350',width=3)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',36)
    draw.text((192,33),plate,font=font,fill='#242531',anchor='mm')
    plaque.save(TEX/(name+'_nameplate.png'))
    return {'materials':'funpackcustom:block/'+name+'_materials',
            'nameplate':'funpackcustom:block/'+name+'_nameplate','particle':'funpackcustom:block/'+name+'_materials'}

def export(name,title,plate,module):
    g=module.build();paths=textures(name,module.COLORS,plate)
    if not any(f['texture']=='#nameplate' for f in g.faces):
        g.group='Engraved display nameplate'
        g.decal(title+' nameplate',(5,.25,11,.75),3.48,'nameplate')
    assert len({f['name'] for f in g.faces})==len(g.faces),name+' duplicate face names'
    for f in g.faces:
        assert 3<=len(f['vertices'])<=4 and len(f['uv'])==len(f['vertices'])
        assert all(2-1e-6<=p[0]<=14+1e-6 and 0<=p[1]<=15+1e-6 and 3-1e-6<=p[2]<=13+1e-6 for p in f['vertices']),(name,f['name'],f['vertices'])
    bounds=[[min(p[i] for f in g.faces for p in f['vertices']),max(p[i] for f in g.faces for p in f['vertices'])] for i in range(3)]
    write(ART/(name+'.geometry.json'),{'textures':paths,'meshes':g.faces,'bounds':bounds})
    lines=['# Reference-based collectible: '+title,'mtllib funpackcustom:models/block/'+name+'.mtl'];idx=1;last=None
    for f in g.faces:
        mat=f['texture'][1:]+'_surface'
        if mat!=last:lines.append('usemtl '+mat);last=mat
        lines.extend('v '+' '.join('%.9f'%(v/16) for v in p) for p in f['vertices'])
        lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
        lines.append('f '+' '.join('%d/%d'%(idx+i,idx+i) for i in range(len(f['vertices']))));idx+=len(f['vertices'])
    (ASSETS/'models/block'/(name+'.obj')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    mtl=[]
    for key in ('materials','nameplate'):mtl.extend(['newmtl '+key+'_surface','Ka 0 0 0','Kd 1 1 1','map_Kd #'+key,''])
    (ASSETS/'models/block'/(name+'.mtl')).write_text('\n'.join(mtl),encoding='utf-8')
    model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'funpackcustom:models/block/'+name+'.obj',
           'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,'ambientocclusion':True,
           'render_type':'minecraft:cutout_mipped_all','textures':paths}
    write(ASSETS/'models/block'/(name+'.json'),model)
    write(ASSETS/'blockstates'/(name+'.json'),{'variants':{'facing='+direction:{'model':'funpackcustom:block/'+name,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270))}})
    model.update({'ambientocclusion':False,'gui_light':'front','display':{
        'gui':{'rotation':[12,205,0],'translation':[0,0,0],'scale':[1.05,1.05,1.05]},
        'ground':{'translation':[0,2,0],'scale':[.5,.5,.5]},'fixed':{'rotation':[0,180,0],'scale':[.8,.8,.8]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2.5,0],'scale':[.4,.4,.4]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,1,0],'scale':[.55,.55,.55]}}})
    write(ASSETS/'models/item'/(name+'.json'),model)
    write(LOOT/(name+'.json'),{'type':'minecraft:block','pools':[{'rolls':1,'conditions':[{'condition':'minecraft:survives_explosion'}],
        'entries':[{'type':'minecraft:item','name':'funpackcustom:'+name}]}]})
    texdata=[]
    for i,key in enumerate(('materials','nameplate')):
        path=TEX/(name+'_'+key+'.png');w,h=Image.open(path).size
        texdata.append({'name':path.name,'id':str(i),'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+key)),
            'width':w,'height':h,'uv_width':w,'uv_height':h,
            'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','visible':True})
    elements=[];groups=defaultdict(list)
    for f in g.faces:
        keys=['v'+str(i) for i in range(len(f['vertices']))];index=0 if f['texture']=='#materials' else 1
        w,h=texdata[index]['width'],texdata[index]['height'];uid=str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/'+f['name']))
        elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':index}},
            'visibility':True,'export':True})
        groups[f['group']].append(uid)
    write(ART/(name+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':title,
        'resolution':{'width':256,'height':256},'elements':elements,'textures':texdata,
        'outliner':[{'name':group,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'/group/'+group)),'origin':[8,0,8],'children':ids} for group,ids in groups.items()]})
    print(name,len(g.faces),'faces',bounds)

if __name__=='__main__':
    for path in (TEX,ART,ASSETS/'models/block',ASSETS/'models/item',LOOT):path.mkdir(parents=True,exist_ok=True)
    for args in FIGURES:export(*args)
    write(ART/'art-lang.json',{'item.funpackcustom.arcade_pass':'Arcade Pass',
        **{'block.funpackcustom.'+name:title for name,title,plate,module in FIGURES}})
