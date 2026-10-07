"""Author a complete Japanese arcade as reproducible native structure NBT.

Only the Python standard library is needed. Includes full mod multiblocks,
empty inventory anchors, an operator villager, vanilla architecture and four
native painting entities. All coordinates in the layout manifest are local.
"""
import copy
import gzip
import json
import struct
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src/main/resources/data/funpackcustom/structure'
ART=ROOT/'art/japanese_arcade'
SIZE=(19,18,19)
BLOCKS={};ENTITIES=[];FIXTURES=[];DISPLAYS=[]
DIRECTIONS={'north':(0,-1),'east':(1,0),'south':(0,1),'west':(-1,0)}
CLOCKWISE={'north':'east','east':'south','south':'west','west':'north'}
OPPOSITE={'north':'south','south':'north','east':'west','west':'east'}


def byte(v):return (1,int(v))
def integer(v):return (3,int(v))
def string(v):return (8,str(v))
def floats(v):return (9,(5,list(v)))
def doubles(v):return (9,(6,list(v)))
def ints(v):return (9,(3,list(v)))
def compounds(v):return (9,(10,list(v)))


def payload(kind,value):
    if kind==1:return struct.pack('>b',value)
    if kind==3:return struct.pack('>i',value)
    if kind==5:return struct.pack('>f',value)
    if kind==6:return struct.pack('>d',value)
    if kind==8:
        b=value.encode('utf-8');return struct.pack('>H',len(b))+b
    if kind==9:
        inner,items=value
        return bytes([inner])+struct.pack('>i',len(items))+b''.join(payload(inner,item) for item in items)
    if kind==10:return b''.join(bytes([k])+payload(8,name)+payload(k,v) for name,(k,v) in value.items())+b'\0'
    raise ValueError(kind)


def write_nbt(path,size,blocks,entities):
    palette=[];indices={};entries=[]
    for pos,(name,properties,nbt) in sorted(blocks.items(),key=lambda entry:(entry[0][1],entry[0][0],entry[0][2])):
        # Native structure capture omits void cells; raw template placement does
        # not treat serialized structure_void blocks as a preserve-terrain flag.
        if name=='minecraft:structure_void':continue
        key=(name,tuple(sorted(properties.items())))
        if key not in indices:
            indices[key]=len(palette);state={'Name':string(name)}
            if properties:state['Properties']=(10,{k:string(v) for k,v in sorted(properties.items())})
            palette.append(state)
        entry={'pos':ints(pos),'state':integer(indices[key])}
        if nbt:entry['nbt']=(10,nbt)
        entries.append(entry)
    if not palette:palette=[{'Name':string('minecraft:air')}]
    data={'DataVersion':integer(3955),'size':ints(size),'palette':compounds(palette),
          'blocks':compounds(entries),'entities':compounds(entities)}
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(gzip.compress(bytes([10])+payload(8,'')+payload(10,data),mtime=0))
    return {'file':str(path.relative_to(ROOT)).replace('\\','/'),'blocks':len(entries),'palette_states':len(palette),
            'entities':len(entities),'compressed_bytes':path.stat().st_size}


def put(x,y,z,name,properties=None,nbt=None):
    assert 0<=x<SIZE[0] and 0<=y<SIZE[1] and 0<=z<SIZE[2],(x,y,z,name)
    if ':' not in name:name='minecraft:'+name
    BLOCKS[x,y,z]=(name,{k:str(v).lower() for k,v in (properties or {}).items()},nbt)


def fill(a,b,name,properties=None):
    for x in range(a[0],b[0]+1):
        for y in range(a[1],b[1]+1):
            for z in range(a[2],b[2]+1):put(x,y,z,name,properties)


def stairs(x,y,z,name,facing,half='bottom',shape='straight'):
    put(x,y,z,name,{'facing':facing,'half':half,'shape':shape,'waterlogged':False})


def slab(x,y,z,name,kind='bottom'):put(x,y,z,name,{'type':kind,'waterlogged':False})
def fence(x,y,z):put(x,y,z,'dark_oak_fence',{'north':False,'east':False,'south':False,'west':False,'waterlogged':False})
def lantern(x,y,z,hanging=False):put(x,y,z,'lantern',{'hanging':hanging,'waterlogged':False})
def log(x,y,z,wood='dark_oak',axis='y'):put(x,y,z,wood+'_log',{'axis':axis})


def sign(x,y,z,lines,facing='north',color='white',wood='dark_oak'):
    text={'messages':(9,(8,[json.dumps({'text':line},ensure_ascii=False,separators=(',',':')) for line in (lines+['']*4)[:4]])),
          'color':string(color),'has_glowing_text':byte(1)}
    put(x,y,z,wood+'_wall_sign',{'facing':facing,'waterlogged':False},
        {'id':string('minecraft:sign'),'front_text':(10,text),'back_text':(10,copy.deepcopy(text)),'is_waxed':byte(1)})


def architecture():
    fill((0,0,0),(18,17,18),'air')
    # Compact paved footprint: solid foundation, recessed building floor, porch.
    fill((2,0,3),(16,0,16),'stone_bricks')
    fill((2,1,3),(16,1,16),'polished_blackstone_bricks')
    fill((3,0,0),(15,0,3),'stone_bricks')
    fill((4,1,0),(14,1,3),'smooth_stone')
    for x in range(7,12):put(x,1,0,'dirt_path')
    for x in range(3,16):
        for z in range(4,16):
            put(x,1,z,'red_terracotta' if (x+z)%2==0 else 'polished_blackstone')
    # Off-white plaster panels with dark timber posts and deep red beams.
    for y in range(2,11):
        for z in range(3,17):
            put(2,y,z,'light_gray_terracotta');put(16,y,z,'light_gray_terracotta')
        for x in range(2,17):
            put(x,y,3,'light_gray_terracotta');put(x,y,16,'light_gray_terracotta')
    for x in (2,6,12,16):
        for z in (3,16):
            for y in range(2,11):log(x,y,z)
    for x in (2,16):
        for z in (7,12):
            for y in range(2,11):log(x,y,z)
    for y in (5,6,10):
        for x in range(2,17):
            log(x,y,3,'stripped_mangrove','x');log(x,y,16,'stripped_mangrove','x')
        for z in range(3,17):
            log(2,y,z,'stripped_mangrove','z');log(16,y,z,'stripped_mangrove','z')
    # Broad open entrance. The frame is two blocks deep like the reference.
    fill((7,2,2),(11,4,3),'air')
    for x in (6,12):
        for y in range(2,6):log(x,y,2)
    fill((6,5,2),(12,5,2),'red_concrete')
    for x in (3,4,5,13,14,15):
        for y in (3,4):put(x,y,3,'red_stained_glass_pane',{'east':True,'west':True,'north':False,'south':False,'waterlogged':False})
    # Ground-floor side windows leave timber bays visible from outdoors.
    for x in (2,16):
        for z in (5,6,9,10,14,15):
            for y in (3,4):put(x,y,z,'gray_stained_glass_pane',{'north':True,'south':True,'east':False,'west':False,'waterlogged':False})
    # Upper lounge floor and central atrium opening.
    fill((3,6,4),(15,6,15),'dark_oak_planks')
    fill((7,6,7),(11,6,11),'air')
    fill((13,6,11),(14,6,14),'air')
    for x in range(3,16):
        put(x,6,2,'dark_oak_planks')
        stairs(x,6,1,'polished_blackstone_brick_stairs','north')
    for x in (3,4,5,6,7,11,12,13,14,15):fence(x,7,2)
    # Glass upper facade with doors onto the shallow balcony.
    for x in (3,4,5,6,12,13,14,15):
        for y in (7,8,9):put(x,y,3,'glass_pane',{'east':True,'west':True,'north':False,'south':False,'waterlogged':False})
    fill((7,7,3),(8,9,3),'air');fill((10,7,3),(11,9,3),'air')
    for z in (4,5,8,9,10,13,14,15):
        for y in (7,8,9):put(2,y,z,'glass_pane',{'north':True,'south':True,'east':False,'west':False,'waterlogged':False})
    for z in (4,5,6,13,14,15):
        for y in (7,8,9):put(16,y,z,'glass_pane',{'north':True,'south':True,'east':False,'west':False,'waterlogged':False})
    # Atrium guard rail, leaving the stairs' landing unobstructed.
    for z in range(7,12):fence(6,7,z);fence(12,7,z)
    for x in range(6,13):fence(x,7,6);fence(x,7,12)
    # A genuine two-wide staircase, five risers from walking Y2 to walking Y7.
    for step in range(5):
        y,z=2+step,10+step
        for x in (13,14):
            if y>2:fill((x,2,z),(x,y-1,z),'dark_oak_planks')
            stairs(x,y,z,'dark_oak_stairs','south')
            put(x,y+1,z,'air');put(x,y+2,z,'air')
    for z in (11,12,13,14):fence(15,7,z)
    # Upper ceiling and a dark hipped roof with stepped tile eaves.
    fill((2,11,3),(16,11,16),'dark_oak_planks')
    for tier in range(7):
        y=11+tier;x0,x1=1+tier,17-tier;z0,z1=2+tier,17-tier
        for x in range(x0,x1+1):
            stairs(x,y,z0,'polished_blackstone_brick_stairs','north')
            stairs(x,y,z1,'polished_blackstone_brick_stairs','south')
        for z in range(z0+1,z1):
            stairs(x0,y,z,'polished_blackstone_brick_stairs','west')
            stairs(x1,y,z,'polished_blackstone_brick_stairs','east')
        if tier==6:fill((x0,y,z0),(x1,y,z1),'polished_blackstone_bricks')
    for x,z in ((1,2),(17,2),(1,17),(17,17)):
        put(x,12,z,'polished_blackstone_brick_wall',{'up':True,'north':'none','south':'none','east':'none','west':'none','waterlogged':False})
    # Solid mounting surfaces for four large native painting signs/murals.
    fill((9,7,2),(9,11,2),'red_concrete')
    fill((7,5,2),(11,5,2),'red_concrete')
    fill((16,7,8),(16,9,10),'black_terracotta')
    fill((7,7,16),(10,9,16),'white_terracotta')


def furnishing():
    # Small lounge booths and tables around the atrium, never on the stair route.
    for z in (6,7,9,10):stairs(3,7,z,'dark_oak_stairs','east')
    for x in (5,6,7,8,9,10,11):stairs(x,7,14,'dark_oak_stairs','north')
    for z in (5,6,7):stairs(14,7,z,'dark_oak_stairs','west')
    for x,z in ((4,7),(4,10),(7,13),(10,13),(13,6)):
        fence(x,7,z);put(x,8,z,'oak_pressure_plate',{'powered':False})
    fill((3,7,15),(4,8,15),'bookshelf')
    put(3,9,15,'potted_azalea_bush');put(4,9,15,'potted_cherry_sapling')
    # A chest avoids introducing a competing fisherman job-site POI.
    put(15,2,13,'chest',{'facing':'north','type':'single','waterlogged':False},{'id':string('minecraft:chest'),
        'Items':compounds([{'Slot':byte(0),'id':string('minecraft:paper'),'count':integer(8)},
                           {'Slot':byte(1),'id':string('minecraft:bread'),'count':integer(3)}])})
    put(15,4,13,'dark_oak_planks')
    sign(15,4,12,['備品','SUPPLIES','',''],facing='north')
    # A tucked-away lounge daybed gives the resident a reachable resting place.
    for z,part in ((8,'foot'),(9,'head')):
        put(14,7,z,'red_bed',{'facing':'south','part':part,'occupied':False},
            {'id':string('minecraft:bed')})
    # Paper lantern rhythm, plus a pair above the open atrium.
    for x,z in ((5,5),(11,5),(5,10),(11,12),(9,15)):
        lantern(x,5,z,True)
    for x,z in ((4,5),(14,5),(4,13),(14,14)):
        lantern(x,10,z,True)
    for x,z in ((8,8),(10,10)):
        put(x,10,z,'chain',{'axis':'y','waterlogged':False});lantern(x,9,z,True)
    for x,z in ((3,2),(15,2),(1,10),(17,13)):
        put(x,9,z,'shroomlight')
        slab(x,10,z,'red_nether_brick_slab')
        lantern(x,8,z,True)
    for x,z in ((5,0),(13,0)):
        put(x,2,z,'stone_brick_wall',{'up':True,'north':'none','south':'none','east':'none','west':'none','waterlogged':False})
        lantern(x,3,z)
    # Entrance sakura planters, trimmed low enough to keep the facade visible.
    for cx in (2,16):
        for x in range(cx-1,cx+2):
            for z in range(0,3):put(x,1,z,'stone_bricks')
        put(cx,1,1,'dirt')
        for y in range(2,5):log(cx,y,1,'cherry')
        for y,radius in ((4,1),(5,2),(6,1)):
            for dx in range(-radius,radius+1):
                for dz in range(-radius,radius+1):
                    x,z=cx+dx,1+dz
                    if 0<=x<19 and 0<=z<19 and abs(dx)+abs(dz)<=radius+1 and (dx or dz or y>=5):
                        put(x,y,z,'cherry_leaves',{'distance':1,'persistent':True,'waterlogged':False})
    for x,z in ((1,5),(17,5),(1,14),(17,14)):
        put(x,1,z,'stone_bricks');put(x,2,z,'potted_flowering_azalea_bush')
    sign(6,4,1,['遊ぶ','PLAY','集める','COLLECT'],facing='north')
    sign(12,4,1,['くつろぐ','RELAX','2F LOUNGE','↑'],facing='north')
    put(12,4,5,'dark_oak_planks')
    sign(12,4,4,['ARCADE DESK','PASS / PRIZES','STAFF','WELCOME'],facing='north')
    for y in range(2,7):log(12,y,11)
    sign(12,4,10,['2F LOUNGE','↑ STAIRS','',''],facing='north')
    sign(6,9,15,['ゲームセンター','ARCADE LOUNGE','TAKE A BREAK',''],facing='north')


def add_machine(name,x,y,z,facing,kind='standard'):
    identifier='funpackcustom:'+name;dx,dz=DIRECTIONS[facing];ax,az=DIRECTIONS[CLOCKWISE[facing]]
    expected=[]
    if kind=='standard':
        for height,part in enumerate(('base','console','marquee')):
            p=(x,y+height,z);props={'facing':facing,'part':part,'has_record':False}
            put(*p,identifier,props,{'id':string('funpackcustom:nostalgia_jukebox')} if height==0 else None)
            expected.append({'pos':p,'properties':{k:str(v).lower() for k,v in props.items()}})
    elif kind=='taiko':
        sections=[('rear_base',0,0),('rear_console',0,1),('rear_marquee',0,2),('drum_base',1,0),('drums',1,1)]
        for side,side_name in enumerate(('primary','secondary')):
            for section,depth,height in sections:
                p=(x+ax*side+dx*depth,y+height,z+az*side+dz*depth)
                props={'facing':facing,'side':side_name,'section':section,'part':('base','console','marquee')[height],'has_record':False}
                put(*p,identifier,props,{'id':string('funpackcustom:nostalgia_jukebox')} if side==0 and section=='rear_base' else None)
                expected.append({'pos':p,'properties':{k:str(v).lower() for k,v in props.items()}})
    elif kind=='claw':
        for part in range(18):
            p=(x+ax*(part%3)-dx*((part//3)%2),y+part//6,z+az*(part%3)-dz*((part//3)%2))
            props={'facing':facing,'part':part}
            put(*p,identifier,props,{'id':string('funpackcustom:claw_machine')} if part==0 else None)
            expected.append({'pos':p,'properties':{k:str(v).lower() for k,v in props.items()}})
    elif kind=='gachapon':
        props={'facing':facing};put(x,y,z,identifier,props,{'id':string('funpackcustom:gachapon')})
        expected.append({'pos':(x,y,z),'properties':props})
    elif kind=='kiosk':
        for height,half in enumerate(('lower','upper')):
            p=(x,y+height,z);props={'facing':facing,'half':half};put(*p,identifier,props)
            expected.append({'pos':p,'properties':props})
    FIXTURES.append({'id':identifier,'kind':kind,'anchor':[x,y,z],'facing':facing,'parts':expected,
                     'stock':'empty','record':'none'})


def machines():
    add_machine('jubeat',3,2,6,'east')
    add_machine('wacca',3,2,9,'east')
    add_machine('chunithm',3,2,12,'east')
    add_machine('taiko',7,2,14,'north','taiko')
    add_machine('project_diva',11,2,14,'north')
    add_machine('nostalgia_op3',15,2,8,'west')
    add_machine('arcade_kiosk',12,2,5,'west','kiosk')
    # Prize displays have no ownership lock or operator inventory to configure.
    fill((14,2,5),(15,2,7),'polished_blackstone_bricks')
    for mob,z in (('creeper',5),('axolotl',6),('enderman',7)):
        identifier='funpackcustom:boxed_'+mob+'_figure'
        put(14,3,z,identifier,{'facing':'west'})
        DISPLAYS.append({'id':identifier,'position':[14,3,z],'facing':'west'})
        put(15,3,z,'dark_oak_trapdoor',{'facing':'east','half':'bottom','open':True,'powered':False,'waterlogged':False})
    put(5,2,5,'polished_blackstone_bricks')
    put(5,3,5,'funpackcustom:boxed_zombie_figure',{'facing':'east'})
    DISPLAYS.append({'id':'funpackcustom:boxed_zombie_figure','position':[5,3,5],'facing':'east'})


PAINTINGS=[
    {'variant':'funpackcustom:arcade_vertical_sign','size':[1,5],'anchor':[9,9,1],'facing':'north','backing':[[9,7,2],[9,11,2]]},
    {'variant':'funpackcustom:arcade_game_center','size':[5,1],'anchor':[9,5,1],'facing':'north','backing':[[7,5,2],[11,5,2]]},
    {'variant':'funpackcustom:arcade_invader','size':[3,3],'anchor':[17,8,9],'facing':'east','backing':[[16,7,8],[16,9,10]]},
    {'variant':'funpackcustom:arcade_fuji','size':[4,3],'anchor':[8,8,17],'facing':'south','backing':[[7,7,16],[10,9,16]]}]


def entities():
    # Anchor-center positions intentionally stay inside the same block under
    # template rotation; Painting.moveTo then recalculates the display bounds.
    for painting in PAINTINGS:
        x,y,z=painting['anchor'];facing={'south':0,'west':1,'north':2,'east':3}[painting['facing']]
        tag={'id':string('minecraft:painting'),'variant':string(painting['variant']),
             'facing':byte(facing),'TileX':integer(x),'TileY':integer(y),'TileZ':integer(z),
             'Invulnerable':byte(0),'Motion':doubles((0,0,0)),'Rotation':floats((facing*90,0))}
        ENTITIES.append({'pos':doubles((x+.5,y+.5,z+.5)),'blockPos':ints((x,y,z)),'nbt':(10,tag)})
    pos=(11.5,2.,5.5)
    ENTITIES.append({'pos':doubles(pos),'blockPos':ints((11,2,5)),
        'nbt':(10,{'id':string('minecraft:villager'),'PersistenceRequired':byte(1),'Age':integer(0),
            'VillagerData':(10,{'type':string('minecraft:plains'),'profession':string('minecraft:none'),'level':integer(1)}),
            'Motion':doubles((0,0,0)),'Rotation':floats((90,0))})})


def preserve_surrounding_terrain():
    # Clearing rooms must not excavate the unbuilt perimeter at ground level.
    for x in range(SIZE[0]):
        for y in (0,1):
            for z in range(SIZE[2]):
                if BLOCKS[x,y,z][0]=='minecraft:air':put(x,y,z,'structure_void')


def validate():
    occupied=set()
    for fixture in FIXTURES:
        for part in fixture['parts']:
            p=tuple(part['pos']);assert p not in occupied,('Overlapping machine',p)
            occupied.add(p);name,props,nbt=BLOCKS[p]
            assert name==fixture['id'] and props==part['properties'],(fixture,p,name,props)
            if p[1]==2:
                floor=BLOCKS[p[0],1,p[2]][0]
                assert floor!='minecraft:air',('Unsupported machine',p)
    for x in (13,14):
        for step in range(5):
            y,z=2+step,10+step
            assert BLOCKS[x,y,z][0]=='minecraft:dark_oak_stairs'
            assert BLOCKS[x,y+1,z][0]=='minecraft:air' and BLOCKS[x,y+2,z][0]=='minecraft:air',('Blocked staircase',x,y,z)
    for x in range(7,12):
        for y in (2,3):assert BLOCKS[x,y,3][0]=='minecraft:air',('Blocked entry',x,y)
    assert BLOCKS[11,2,5][0]=='minecraft:air' and BLOCKS[11,3,5][0]=='minecraft:air','Operator spawn blocked'
    for p in PAINTINGS:
        a,b=p['backing']
        dx,dz=DIRECTIONS[p['facing']]
        for x in range(a[0],b[0]+1):
            for y in range(a[1],b[1]+1):
                for z in range(a[2],b[2]+1):
                    assert BLOCKS[x,y,z][0]!='minecraft:air',('Missing mural support',p)
                    assert BLOCKS[x+dx,y,z+dz][0]=='minecraft:air',('Obstructed mural',p['variant'],(x+dx,y,z+dz))


def map_svg():
    colors={'minecraft:air':'#faf4e6','minecraft:dark_oak_fence':'#735236','minecraft:dark_oak_stairs':'#ad7842',
            'minecraft:dark_oak_log':'#302721','minecraft:light_gray_terracotta':'#c9b7a4',
            'minecraft:glass_pane':'#8fced4','minecraft:red_stained_glass_pane':'#bd6868'}
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1020" height="660" viewBox="0 0 1020 660">',
        '<rect width="1020" height="660" fill="#eee5d5"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#27282b}.title{font-size:23px;font-weight:bold}.small{font-size:12px}</style>',
        '<text x="35" y="36" class="title">Japanese arcade — authored floor plans</text>']
    for ox,y,label in ((35,2,'1F / ARCADE + SERVICE DESK'),(535,7,'2F / LOUNGE + OPEN ATRIUM')):
        parts.append(f'<text x="{ox}" y="70" font-size="17" font-weight="bold">{label}</text>')
        for x in range(19):
            for z in range(19):
                name=BLOCKS[x,y,z][0]
                color='#c64245' if name.startswith('funpackcustom:') else colors.get(name,'#706864')
                if y==7 and 7<=x<=11 and 7<=z<=11:color='#343845'
                parts.append(f'<rect x="{ox+x*24}" y="{90+z*24}" width="23" height="23" fill="{color}"/>')
        parts.append(f'<text x="{ox+210}" y="578" class="small">NORTH / ENTRANCE ↑</text>')
    for index,fixture in enumerate(FIXTURES,1):
        x,y,z=fixture['anchor'];label='K' if fixture['kind']=='kiosk' else str(index)
        parts.append(f'<text x="{35+x*24+12}" y="{90+z*24+17}" text-anchor="middle" fill="white" font-size="14" font-weight="bold">{label}</text>')
    parts.append('<text x="35" y="618" class="small">1 Jubeat · 2 WACCA · 3 Chunithm · 4 Taiko · 5 Project DIVA · 6 Nostalgia · K Kiosk · Four prize displays</text>')
    parts.append('<text x="35" y="641" class="small">Red: machine cells. Brown: stairs / seating. Dark center: open atrium. Upper stair landing is at the rear right.</text></svg>')
    (ART/'floor-plans.svg').write_text('\n'.join(parts),encoding='utf-8')


def main():
    BLOCKS.clear();ENTITIES.clear();FIXTURES.clear();DISPLAYS.clear();ART.mkdir(parents=True,exist_ok=True)
    architecture();furnishing();machines();entities();preserve_surrounding_terrain();validate()
    standalone=write_nbt(OUT/'arcade/japanese_arcade.nbt',SIZE,BLOCKS,ENTITIES)
    village=copy.deepcopy(BLOCKS)
    connector={'name':string('minecraft:building_entrance'),'target':string('minecraft:building_entrance'),
        'pool':string('minecraft:empty'),'final_state':string('minecraft:dirt_path'),'joint':string('aligned')}
    village[9,1,0]=('minecraft:jigsaw',{'orientation':'north_up'}, {'id':string('minecraft:jigsaw'),**connector})
    village_info=write_nbt(OUT/'arcade/japanese_arcade_village.nbt',SIZE,village,ENTITIES)
    # Integrated Villages roads attach through walking air, one block above
    # their surface, whereas vanilla's building connector occupies the path.
    integrated=copy.deepcopy(BLOCKS)
    integrated_connector={'name':string('integrated_villages:house'),'target':string('integrated_villages:house'),
        'pool':string('minecraft:empty'),'final_state':string('minecraft:air'),'joint':string('aligned')}
    integrated[9,2,0]=('minecraft:jigsaw',{'orientation':'north_up'},
        {'id':string('minecraft:jigsaw'),**integrated_connector})
    integrated_info=write_nbt(OUT/'arcade/japanese_arcade_integrated_village.nbt',SIZE,integrated,ENTITIES)
    fixture=write_nbt(OUT/'arcade_test.nbt',(32,24,32),{},[])
    road={(x,y,z):('minecraft:air',{},None) for x in range(5) for y in range(3) for z in range(3)}
    for x in range(5):road[x,1,1]=('minecraft:dirt_path',{},None)
    test_connector={**connector,'pool':string('funpackcustom:arcade/village')}
    road[2,1,0]=('minecraft:jigsaw',{'orientation':'north_up'},{'id':string('minecraft:jigsaw'),**test_connector})
    road_info=write_nbt(OUT/'arcade/test_road.nbt',(5,3,3),road,[])
    manifest={'size':list(SIZE),'front':'north','main_building_bounds':[[2,0,3],[16,11,16]],
        'ground_floor_solid_y':1,'ground_floor_walk_y':2,'upper_floor_solid_y':6,'upper_floor_walk_y':7,
        'entrance':{'clear_x':[7,11],'z':3,'walk_y':2,'height':3},
        'village_connector':{'position':[9,1,0],'orientation':'north_up','name':'minecraft:building_entrance',
            'target':'minecraft:building_entrance','pool':'minecraft:empty','final_state':'minecraft:dirt_path','joint':'aligned'},
        'integrated_village_connector':{'position':[9,2,0],'orientation':'north_up','name':'integrated_villages:house',
            'target':'integrated_villages:house','pool':'minecraft:empty','final_state':'minecraft:air','joint':'aligned'},
        'fixtures':FIXTURES,'machine_count':6,'jukebox_anchors':6,'prize_displays':DISPLAYS,'operator_spawn':[11.5,2,5.5],
        'operator_profession':'unemployed adult; acquires funpackcustom:arcade_operator from the reachable kiosk',
        'staircase':{'width_x':[13,14],'steps':[[13,2+i,10+i] for i in range(5)],'upper_landing':[13,7,15]},
        'atrium_opening':{'x':[7,11],'z':[7,11],'floor_y':6},'paintings':PAINTINGS,
        'inventory_policy':'Six jukebox cabinets start without discs. No claw/gachapon operator inventories. Service chest contains 8 paper and 3 bread only; four static boxed figures decorate display plinths.',
        'resident_bed':{'foot':[14,7,8],'head':[14,7,9],'facing':'south'},
        'rotation_verification':'Place all native rotations around template origin; transform each fixturepart and facing together. No fixed world-space job-site NBT.',
        'outputs':[standalone,village_info,integrated_info,fixture,road_info],
        'terrain_preservation':'Unbuilt perimeter cells at Y0/Y1 are omitted from serialized NBT; explicit air clears rooms and roof space above.',
        'solid_block_counts':dict(sorted(Counter(v[0] for v in BLOCKS.values() if v[0] not in ('minecraft:air','minecraft:structure_void')).items()))}
    (ART/'layout.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    map_svg()
    print(json.dumps({'size':SIZE,'fixtures':len(FIXTURES),'machines':6,'paintings':4,
        'entities':len(ENTITIES),'outputs':manifest['outputs']},indent=2))


if __name__=='__main__':main()
