"""Export the editable original-blue Jubeat model and three native block parts."""
import base64
import json
import math
import uuid
from collections import defaultdict
from pathlib import Path
from PIL import Image
from ddr_mesh_export import pieces,quads
from jubeat_geometry import build
from jubeat_textures import build_textures

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/jubeat';ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
TEX=ASSETS/'textures/block'
GLASS_TEXTURES={'#cube','#cube_top','#glass_overlay'}

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    for p in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):
        p.mkdir(parents=True,exist_ok=True)
    texture_files=build_textures(TEX)
    textures={key:'japanesearcades:block/jubeat_'+key for key in texture_files}
    textures['particle']=textures['materials']
    g,metadata=build()
    assert len({f['name'] for f in g.faces})==len(g.faces),'Duplicate face name'
    for f in g.faces:
        assert len(f['vertices'])==len(f['uv']) and 3<=len(f['vertices'])<=4,f['name']
        assert all(0<=p[0]<=16 and 0<=p[1]<=48 and 0<=p[2]<=16 for p in f['vertices']),(f['name'],f['vertices'])
        a,b,c=f['vertices'][:3]
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        assert sum(n*n for n in cross)>1e-15,('Degenerate face',f['name'])
    part_names=('base','console','marquee');parts={name:[] for name in part_names}
    for f in g.faces:
        for fragment in pieces(list(zip(f['vertices'],f['uv'])),1,[16,32]):
            for q in quads(fragment):
                row=min(2,int(sum(p[1] for p,uv in q)/len(q)//16))
                parts[part_names[row]].append({**f,'vertices':[p for p,uv in q],'uv':[uv for p,uv in q]})
    def obj(path,faces,transform):
        lines=['# Classic blue Jubeat. Native block mesh; units are blocks.','mtllib japanesearcades:models/block/jubeat.mtl']
        index=1;last=None
        for f in faces:
            mat=f['texture'][1:]+('_lit' if f['glow'] else '_surface')
            if mat!=last:lines.append('usemtl '+mat);last=mat
            lines.extend('v '+' '.join('%.9f'%v for v in transform(p)) for p in f['vertices'])
            lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
            lines.append('f '+' '.join('%d/%d'%(index+i,index+i) for i in range(len(f['vertices']))))
            index+=len(f['vertices'])
        path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def wrapper(path,render_type='minecraft:cutout_mipped_all'):
        return {'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+path,
                'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
                'ambientocclusion':True,'render_type':render_type,'textures':textures}
    def layered_model(path,faces,transform):
        # Opaque frames/interiors render first; genuine fractional-alpha panes
        # are a separate native translucent pass for both blocks and items.
        solid=[f for f in faces if f['texture'] not in GLASS_TEXTURES]
        glass=[f for f in faces if f['texture'] in GLASS_TEXTURES]
        obj(ASSETS/'models'/(path+'.obj'),solid,transform)
        obj(ASSETS/'models'/(path+'_glass.obj'),glass,transform)
        return {'parent':'minecraft:block/block','loader':'neoforge:composite',
                'ambientocclusion':True,'textures':textures,
                'children':{'solid':wrapper(path+'.obj'),
                            'glass':wrapper(path+'_glass.obj','minecraft:translucent')},
                'item_render_order':['solid','glass']}
    for row,name in enumerate(part_names):
        path='block/jubeat_'+name
        model=layered_model(path,parts[name],lambda p,row=row:[p[0]/16,(p[1]-row*16)/16,p[2]/16])
        write_json(ASSETS/'models'/(path+'.json'),model)
    mtl=[]
    for key,lit in sorted({(f['texture'][1:],f['glow']) for f in g.faces}):
        mtl.extend(['newmtl '+key+('_lit' if lit else '_surface'),'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1','map_Kd #'+key,''])
    (ASSETS/'models/block/jubeat.mtl').write_text('\n'.join(mtl),encoding='utf-8')
    write_json(ASSETS/'blockstates/jubeat.json',{'variants':{
        'facing='+direction+',part='+part:{'model':'japanesearcades:block/jubeat_'+part,**({'y':angle} if angle else {})}
        for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for part in part_names}})
    item=layered_model('item/jubeat',g.faces,lambda p:[((p[0]-8)*.36+8)/16,p[1]*.36/16,((p[2]-8)*.36+8)/16])
    item.update({'ambientocclusion':False,'gui_light':'front','display':{
        'gui':{'rotation':[15,225,0],'scale':[.96,.96,.96]},
        'ground':{'translation':[0,2,0],'scale':[.65,.65,.65]},
        'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
        'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,3,0],'scale':[.5,.5,.5]},
        'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,2,0],'scale':[.55,.55,.55]}}})
    write_json(ASSETS/'models/item/jubeat.json',item)
    loot=ROOT/'src/main/resources/data/japanesearcades/loot_table/blocks/jubeat.json'
    loot.parent.mkdir(parents=True,exist_ok=True)
    write_json(loot,{'type':'minecraft:block','pools':[{'rolls':1,
        'conditions':[{'condition':'minecraft:survives_explosion'}],
        'entries':[{'type':'minecraft:item','name':'japanesearcades:jubeat','conditions':[{
            'condition':'minecraft:block_state_property','block':'japanesearcades:jubeat','properties':{'part':'base'}}]}]}]})
    bounds=[[min(p[i] for f in g.faces for p in f['vertices']),max(p[i] for f in g.faces for p in f['vertices'])] for i in range(3)]
    stats={'source_faces':len(g.faces),'runtime_section_faces':{k:len(v) for k,v in parts.items()},
           'translucent_faces':sum(f['texture'] in GLASS_TEXTURES for f in g.faces)}
    write_json(ART/'geometry.json',{'textures':textures,'meshes':g.faces,'bounds':bounds,'statistics':stats,**metadata})
    # Blockbench displays a single square frame; the runtime atlas uses the
    # matching vertical animation strip and its .mcmeta timing.
    specs=[(key,ART/'jubeat-pads-preview.png' if key=='pads' else path)
           for key,path in texture_files.items()]
    indices={'#'+key:i for i,(key,path) in enumerate(specs)}
    sizes=[Image.open(path).size for key,path in specs];elements=[];groups=defaultdict(list)
    for f in g.faces:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'jubeat/'+f['name']));idx=indices[f['texture']];w,h=sizes[idx]
        keys=['v'+str(i) for i in range(len(f['vertices']))]
        elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
            'vertices':dict(zip(keys,f['vertices'])),'faces':{'face':{'vertices':keys,
            'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(keys,f['uv'])},'texture':idx}},'visibility':True,'export':True})
        groups[f['group']].append(uid)
    texdata=[]
    for i,(key,path) in enumerate(specs):
        w,h=sizes[i];texdata.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'jubeat/'+key)),'width':w,'height':h,'uv_width':w,'uv_height':h,
            'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','particle':i==0,'render_mode':'default','visible':True})
    write_json(ART/'jubeat.bbmodel',{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},
        'name':'Jubeat Original Blue Cabinet','model_identifier':'jubeat','visible_box':[1,3,1],
        'resolution':{'width':256,'height':256},'elements':elements,'textures':texdata,
        'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'jubeat/group/'+name)),
                    'origin':[8,0,8],'children':children} for name,children in groups.items()]})
    print('Jubeat exported',stats,'bounds',bounds)

if __name__=='__main__':main()
