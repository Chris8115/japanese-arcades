"""Export both compact GITADORA cabinets as static, per-cell OBJ meshes."""
from pathlib import Path
from collections import defaultdict
import base64,json,math,uuid
from PIL import Image
from ddr_mesh_export import pieces,quads
from obj_mesh_optimizer import optimize_obj
from gitadora_geometry import build
from gitadora_textures import generate

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/gitadora'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    ART.mkdir(parents=True,exist_ok=True)
    paths=generate()
    for kind in ('guitarfreaks','drummania'):
        ident='gitadora_'+kind
        out=ART/kind;out.mkdir(exist_ok=True)
        g,meta=build(kind)
        surfaces=g.faces
        assert len({f['name'] for f in surfaces})==len(surfaces),'Duplicate face names'
        for f in surfaces:
            assert 3<=len(f['vertices'])<=4 and len(f['vertices'])==len(f['uv']),f['name']
            assert all(math.isfinite(v) for p in f['vertices'] for v in p),f['name']
            a,b,c=f['vertices'][:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
            n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
            assert sum(x*x for x in n)>1e-16,('Zero face',f['name'])
            if len(f['vertices'])==4:assert abs(sum(n[i]*(f['vertices'][3][i]-a[i]) for i in range(3)))<1e-5,('Nonplanar',f['name'])
        used=sorted({f['texture'][1:] for f in surfaces})
        textures={key:'japanesearcades:block/gitadora_'+key for key in used}
        textures['particle']=textures['materials']
        if kind=='guitarfreaks':sections={'base':(0,0,0),'console':(0,1,0),'marquee':(0,2,0)}
        else:sections={'0':(0,0,0),'1':(1,0,0),'2':(0,0,1),'3':(1,0,1),
                       '4':(0,1,0),'5':(1,1,0),'6':(0,2,0),'7':(1,2,0),'8':(0,1,1),'9':(1,1,1)}
        parts={part:[] for part in sections}
        for face in surfaces:
            fragments=[list(zip(face['vertices'],face['uv']))]
            axes=[(1,[16,32])]+([(0,[16]),(2,[0])] if kind=='drummania' else [])
            for axis,levels in axes:fragments=[p for fragment in fragments for p in pieces(fragment,axis,levels)]
            for fragment in fragments:
                for poly in quads(fragment):
                    center=[sum(p[i] for p,uv in poly)/len(poly) for i in range(3)]
                    row=min(2,max(0,int(center[1]//16)))
                    cell=(0,row,0) if kind=='guitarfreaks' else (0 if center[0]<16 else 1,row,0 if center[2]>=0 else 1)
                    key=next((key for key,value in sections.items() if value==cell),None)
                    assert key is not None,(face['name'],cell,center)
                    parts[key].append({**face,'vertices':[p for p,uv in poly],'uv':[uv for p,uv in poly]})
        def obj(path,faces,transform):
            lines=[f'# Classic white GITADORA {kind}; static actual exported geometry.',f'mtllib japanesearcades:models/block/{ident}.mtl']
            index=1;last=None
            for f in faces:
                mat=f['texture'][1:]+('_glow' if f['glow'] else '_surface')
                if mat!=last:lines.append('usemtl '+mat);last=mat
                lines.extend('v '+' '.join('%.9f'%n for n in transform(p)) for p in f['vertices'])
                lines.extend('vt %.9f %.9f'%(u/16,1-v/16) for u,v in f['uv'])
                lines.append('f '+' '.join(f'{index+i}/{index+i}' for i in range(len(f['vertices']))));index+=len(f['vertices'])
            result,stats=optimize_obj('\n'.join(lines)+'\n')
            path.write_text(result,encoding='utf-8')
            stats['exported_faces']=sum(s.startswith('f ') for s in result.splitlines())
            stats['exported_triangles']=sum(len(s.split())-3 for s in result.splitlines() if s.startswith('f '))
            return stats
        def wrapper(name,item=False):
            model={'parent':'minecraft:block/block','loader':'neoforge:obj','model':'japanesearcades:models/'+name+'.obj',
                   'automatic_culling':False,'shade_quads':True,'flip_v':True,'emissive_ambient':True,
                   'ambientocclusion':not item,'render_type':'minecraft:cutout_mipped_all','textures':textures}
            if item:model.update({'gui_light':'front','display':{
                'gui':{'rotation':[12,225,0],'translation':[0,-5.2,0],'scale':[.34,.34,.34]},
                'ground':{'translation':[0,0,0],'scale':[.19,.19,.19]},
                'fixed':{'rotation':[0,180,0],'translation':[0,-6,0],'scale':[.33,.33,.33]},
                'thirdperson_righthand':{'rotation':[75,45,0],'scale':[.25,.25,.25]},
                'firstperson_righthand':{'rotation':[0,45,0],'translation':[0,-3,0],'scale':[.33,.33,.33]}}})
            return model
        statistics={}
        for section,faces in parts.items():
            x,row,depth=sections[section];name=f'block/{ident}_{section}'
            statistics[section]=obj(ASSETS/'models'/(name+'.obj'),faces,lambda p,x=x,row=row,depth=depth:[(p[0]-x*16)/16,(p[1]-row*16)/16,(p[2]+depth*16)/16])
            write_json(ASSETS/'models'/(name+'.json'),wrapper(name))
        shiftx,shiftz=(0,0) if kind=='guitarfreaks' else (-8,8)
        statistics['item']=obj(ASSETS/'models/item'/f'{ident}.obj',surfaces,lambda p:[(p[0]+shiftx)/16,p[1]/16,(p[2]+shiftz)/16])
        write_json(ASSETS/'models/item'/f'{ident}.json',wrapper('item/'+ident,True))
        mtl=[]
        for key,lit in sorted({(f['texture'][1:],f['glow']) for f in surfaces}):
            mtl.extend(['newmtl '+key+('_glow' if lit else '_surface'),'Ka '+('1 1 1' if lit else '0 0 0'),'Kd 1 1 1','map_Kd #'+key,''])
        (ASSETS/'models/block'/f'{ident}.mtl').write_text('\n'.join(mtl),encoding='utf-8')
        prop='part' if kind=='guitarfreaks' else 'section'
        write_json(ASSETS/'blockstates'/f'{ident}.json',{'variants':{
            f'facing={direction},{prop}={section}':{'model':f'japanesearcades:block/{ident}_{section}',**({'y':angle} if angle else {})}
            for direction,angle in (('north',0),('east',90),('south',180),('west',270)) for section in sections}})
        statistics['placed_faces']=sum(statistics[s]['exported_faces'] for s in sections)
        statistics['inventory_faces']=statistics['item']['exported_faces']
        assert statistics['placed_faces']<10000 and statistics['inventory_faces']<10000
        bounds=[[min(p[i] for f in surfaces for p in f['vertices']),max(p[i] for f in surfaces for p in f['vertices'])] for i in range(3)]
        write_json(out/'geometry.json',{**meta,'textures':textures,'meshes':surfaces,'bounds':bounds,'statistics':statistics,'sections':sections})
        sizes={key:Image.open(paths[key]).size for key in used}
        groups=defaultdict(list);elements=[]
        for f in surfaces:
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,ident+'/'+f['name']));key=f['texture'][1:];w,h=sizes[key];vertices=['v'+str(i) for i in range(len(f['vertices']))]
            elements.append({'name':f['name'],'type':'mesh','uuid':uid,'origin':[0,0,0],'rotation':[0,0,0],
                'vertices':dict(zip(vertices,f['vertices'])),'faces':{'face':{'vertices':vertices,'uv':{k:[u*w/16,v*h/16] for k,(u,v) in zip(vertices,f['uv'])},'texture':used.index(key)}},'visibility':True,'export':True})
            groups[f['group']].append(uid)
        texdata=[]
        for i,key in enumerate(used):
            path=paths[key];w,h=sizes[key];texdata.append({'name':path.name,'folder':'block','namespace':'japanesearcades','id':str(i),
                'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,ident+'/'+key)),'width':w,'height':h,'uv_width':w,'uv_height':h,
                'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),'mode':'bitmap','particle':key=='materials','render_mode':'default','visible':True})
        write_json(out/(ident+'.bbmodel'),{'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':meta['name'],
            'model_identifier':ident,'visible_box':[2,3,2],'resolution':{'width':256,'height':256},'elements':elements,'textures':texdata,
            'outliner':[{'name':name,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,ident+'/group/'+name)),'origin':[8,0,8],'children':children} for name,children in groups.items()]})
        print(ident,json.dumps({'bounds':bounds,'placed_faces':statistics['placed_faces'],'item_faces':statistics['inventory_faces']}))
    write_json(ART/'texture_audit.json',{'textures':[{'name':p.name,'size':Image.open(p).size,'bytes':p.stat().st_size,'rgba_bytes':Image.open(p).width*Image.open(p).height*4} for p in paths.values()],
        'total_base_rgba_bytes':sum(Image.open(p).width*Image.open(p).height*4 for p in paths.values()),
        'shared':'All identical printed panels/materials are shared between both cabinets; only the screen subtitles differ.',
        'provenance':'Original procedural interpretation of KONAMI OverDrive printed panels. Official cabinet photographs retained in references/ for geometry comparison.'})

if __name__=='__main__':main()
