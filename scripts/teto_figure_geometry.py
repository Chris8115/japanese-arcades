"""Hard-edged quarter-unit voxel Kasane Teto collectible, rebuilt from reference."""
import math
from figure_geometry import FigureGeometry

COLORS = {
    'white':'#fff0e4', 'bow_shadow':'#dcc5c0',
    'base':'#26303b', 'base_side':'#1c2430', 'base_top':'#39434b',
    'teal':'#378491', 'teal_dark':'#286473',
    'skin':'#f4c7b4', 'skin_light':'#ffdcc7', 'skin_shadow':'#dfa697', 'cheek':'#f1b8b1', 'cheek_pale':'#f7c9b9',
    'hair':'#d34870', 'hair_light':'#e65c7f', 'hair_top':'#ed708d',
    'hair_dark':'#b93560', 'hair_shadow':'#94294d', 'hair_groove':'#a42d53',
    'lash':'#653441', 'eye_red':'#cf5276', 'eye_pink':'#ee94ad', 'eye_glint':'#ffe2d8',
    'gray':'#b2a7ab', 'gray_light':'#cfbdbe', 'gray_dark':'#8d8290',
    'pink':'#ed638e', 'pink_light':'#ff91af', 'pink_dark':'#b93b68',
    'black':'#292733', 'black_light':'#3c3442', 'black_dark':'#1d202b',
    'face_base':'#edc5cc', 'face_lash':'#352936',
    'face_pupil':'#8c385c', 'face_iris':'#cf5276', 'face_sclera':'#c2b9c3',
    'face_cheek':'#e5aebe', 'face_mouth':'#dfa4b8',
}


class _Voxels:
    """Union of quarter-unit cuboids exporting only exterior square faces."""
    def __init__(self,name):
        self.name=name
        self.cells={}

    def block(self,lo,hi,color):
        a=tuple(round(v*4) for v in lo)
        b=tuple(round(v*4) for v in hi)
        assert all(abs(v*4-round(v*4))<1e-7 for v in (*lo,*hi))
        for x in range(a[0],b[0]):
            for y in range(a[1],b[1]):
                for z in range(a[2],b[2]):
                    self.cells[x,y,z]=color

    def emit(self,g):
        sides={
            'north':((0,0,-1),(3,2,1,0)), 'south':((0,0,1),(4,5,6,7)),
            'west':((-1,0,0),(0,4,7,3)), 'east':((1,0,0),(1,2,6,5)),
            'up':((0,1,0),(3,7,6,2)), 'down':((0,-1,0),(0,1,5,4)),
        }
        for (i,j,k),color in sorted(self.cells.items()):
            x,y,z=i/4,j/4,k/4
            X,Y,Z=x+.25,y+.25,z+.25
            vertices=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),
                      (x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
            for side,(offset,indices) in sides.items():
                neighbor=(i+offset[0],j+offset[1],k+offset[2])
                if neighbor not in self.cells:
                    g.face('%s voxel %d %d %d %s'%(self.name,i,j,k,side),
                           [vertices[n] for n in indices],color)


def _pixel(g,name,x,y,width,height,material,z=5.498):
    g.face(name,[(x,y+height,z),(x+width,y+height,z),
                (x+width,y,z),(x,y,z)],material)


def _paint_face(g):
    # Miku's accepted square-pixel layout, with rose irises for Teto:
    # inner iris, outer eye white, then skin at the outside of each eye.
    rows=('SSSSSSSS','SSSSSSSS','SSSSSSSS','SDDSSDDS',
          'SWPSSPWS','SWISSIWS','BSSMMSSB')
    colors={'S':'face_base','D':'face_lash','W':'face_sclera',
            'P':'face_pupil','I':'face_iris','B':'face_cheek','M':'face_mouth'}
    step=3.28/8
    for row,cells in enumerate(rows):
        for column,color in enumerate(cells):
            _pixel(g,'Teto reference face pixel %d %d'%(row,column),
                   6.36+column*step,8.5+(6-row)*step,step,step,colors[color])


def _square_curl(g,side,center,handedness):
    """A dense tapered helix sampled as occupied quarter-unit cuboids."""
    v=_Voxels('Teto '+side+' square curl')
    cz=8.25
    # A narrow pink recessed spine, with roughly one-voxel spaces between
    # the thick turns. Trigonometry only locates cubes; every edge is square.
    v.block((center-.25,8,cz-.25),(center+.25,12.25,cz+.25),'hair_groove')
    for step in range(161):
        t=step/160
        angle=handedness*math.tau*4.25*t+.35
        radius=(1-t)**.65
        x=round((center+(.90*radius+.08)*math.cos(angle))*4)/4
        z=round((cz+(.68*radius+.06)*math.sin(angle))*4)/4
        y=round((12.10-4.35*t)*4)/4
        color=('hair_light' if math.sin(angle)<-.25 else
               'hair_dark' if math.sin(angle)>.35 else 'hair')
        v.block((x-.25,y-.25,z-.25),(x+.25,y+.5,z+.25),color)
    v.block((center,7.5,cz-.25),(center+.25,8,cz),'hair_dark')
    x0,x1=(center,5.5) if center<8 else (10.5,center)
    v.block((x0,11.5,7.5),(x1,12.25,8.75),'hair_dark')
    v.block((center-.5,12,7.75),(center,12.5,8.5),'hair')
    v.block((center,12,8),(center+.5,12.5,8.75),'hair_light')
    v.emit(g)


def build():
    g=FigureGeometry(COLORS)
    g.group='Teto square display base'
    g.box('Teto base square lower block',(2.5,0,3.5),(13.5,.75,12.5),'base_side')
    g.box('Teto base square top step',(2.75,.75,3.75),(13.25,1,12.25),'base_top')
    g.box('Teto base front teal line',(2.75,.75,3.49),(13.25,.875,3.75),'teal')
    g.box('Teto base left teal line',(2.74,.75,3.75),(2.875,.875,12.25),'teal_dark')
    g.box('Teto base right teal line',(13.125,.75,3.75),(13.26,.875,12.25),'teal_dark')
    g.decal('Teto nameplate',(5,.25,11,.75),3.48,'nameplate')

    g.group='Teto voxel tall boots and thighs'
    for n,cx in enumerate((6.75,9.25)):
        v=_Voxels('Teto boot and thigh %d'%n)
        v.block((cx-.5,1,6),(cx+.5,1.25,8.75),'black_dark')
        v.block((cx-.5,1.25,6.25),(cx+.5,1.75,8.5),'black')
        v.block((cx-.5,1.75,6.75),(cx+.5,3.5,8.5),'black')
        v.block((cx-.5,3.5,6.75),(cx+.5,3.75,8.5),'pink_dark')
        v.block((cx-.25,3.75,7),(cx+.5,4.5,8.25),'skin')
        v.block((cx-.25,3.75,7),(cx+.25,4.5,7.25),'skin_light')
        v.block((cx-.25,3.5,6.75),(cx+.5,3.75,7),'pink')
        v.block((cx-.5,1.75,7),(cx-.25,3.25,8.5),'black_light')
        v.block((cx+.25,1.25,6.25),(cx+.5,1.5,6.5),'pink_dark')
        v.block((cx,2.75,6.5),(cx+.25,3.25,6.75),'pink_dark')
        v.block((cx-.25,3.25,6.5),(cx+.25,3.5,6.75),'gray')
        v.emit(g)

    g.group='Teto voxel pleated skirt and gray tunic'
    v=_Voxels('Teto stepped outfit')
    # Nested square tiers and alternating rectangular front/back pleats.
    v.block((6.25,5,6.75),(9.75,5.75,9.25),'black')
    v.block((6,4.5,6.5),(10,5,9.5),'black')
    v.block((5.75,4.25,6.5),(10.25,4.5,9.5),'pink_dark')
    for i in range(9):
        x=5.75+i*.5
        low=4.25 if i%2 else 4
        front=6.25 if i%2 else 6.5
        back=9.75 if i%2 else 9.5
        v.block((x,low,front),(x+.5,4.75,back),'black_light' if i%2 else 'black')
        v.block((x,low,front),(x+.5,low+.25,back),'pink')
    # Narrow waist, block shoulders and small split gray tunic tails.
    v.block((6.5,7.5,6.75),(9.5,8.25,9),'gray_dark')
    v.block((6.75,6.5,6.5),(9.25,7.5,8.75),'gray')
    v.block((6.5,5.75,6.5),(9.5,6.5,9),'gray')
    v.block((6.25,5.25,6.5),(9.75,5.75,9),'gray_light')
    v.block((6.25,5,6.25),(7.75,5.5,6.5),'gray_light')
    v.block((8.25,5,6.25),(9.75,5.5,6.5),'gray_light')
    v.block((6.5,5.5,6.25),(9.5,6.5,6.5),'gray')
    v.block((6.75,6.5,6.25),(9.25,7.5,6.5),'gray')
    v.block((6.75,7.5,6.5),(9.25,8,6.75),'gray_light')
    for x in (7,8.75):
        v.block((x,5.25,6.25),(x+.25,7.25,6.5),'pink_dark')
        for y in (5.5,6.25,7):
            v.block((x,y,6),(x+.25,y+.25,6.25),'pink')
    for y in (5.75,6.25,6.75,7.25):
        v.block((7.75,y,6.25),(8,y+.25,6.5),'pink_light')
    v.block((7.25,8,7.25),(8.75,8.75,8.5),'skin_shadow')
    v.block((7,7.75,6.5),(7.75,8.25,6.75),'gray_light')
    v.block((8.25,7.75,6.5),(9,8.25,6.75),'gray_light')
    v.block((7.5,7.5,6.25),(7.75,7.75,6.5),'gray_light')
    v.block((8.25,7.5,6.25),(8.5,7.75,6.5),'gray_light')
    v.block((7.75,7.75,6.25),(8.25,8,6.5),'pink_dark')
    v.block((7.75,5.5,8.75),(8,7.25,9),'pink_dark')
    v.block((7.25,7.75,9),(8.75,8,9.25),'gray_light')
    for x in (7.5,8,8.5):
        v.block((x,7.75,9),(x+.25,8,9.25),'pink_dark')
    v.emit(g)

    g.group='Teto cuboid detached sleeves'
    for sign,side in ((-1,'left'),(1,'right')):
        start=len(g.faces)
        v=_Voxels('Teto '+side+' block arm')
        v.block((-.5,-1,7),(.5,0,8.25),'skin')
        v.block((-.25,-1,6.75),(.5,0,7),'skin_light')
        v.block((-.5,-2.25,6.75),(.5,-1,8.25),'black')
        v.block((-.75,-2.75,6.5),(.75,-2.25,8.5),'black')
        v.block((-.5,-1.25,6.75),(.5,-1,8.25),'pink_dark')
        v.block((-.5,-1.25,6.5),(.5,-1,6.75),'pink')
        v.block((-.75,-2.75,6.5),(.75,-2.5,8.5),'pink')
        v.block((-.5,-3,6.75),(.5,-2.75,8.25),'skin_light')
        v.block((-.25,-2,6.5),(0,-1.5,6.75),'black_light')
        v.block((.25,-1.75,6.5),(.5,-1.5,6.75),'pink_dark')
        v.emit(g)
        angle=math.radians(sign*20)
        root=8+sign*1.75
        g.transform(start,lambda x,y,z,a=angle,r=root:
                    (r+x*math.cos(a)-y*math.sin(a),8+x*math.sin(a)+y*math.cos(a),z))

    g.group='Teto square skin head'
    v=_Voxels('Teto cuboid skin head')
    v.block((5.5,8.5,5.5),(10.5,11.5,9.75),'face_base')
    v.block((5.75,8.5,5.5),(10.25,11.25,5.75),'face_base')
    v.emit(g)

    g.group='Teto dense stepped pink voxel hair'
    v=_Voxels('Teto stepped hair cap')
    # Color tracks coherent strands; all crown transitions are little steps.
    v.block((5.25,8.75,9.5),(10.75,11.75,10.5),'hair_dark')
    v.block((5,9.25,8.75),(11,11.75,10.25),'hair')
    # Short staggered crown clumps replace the former broad roof plates.
    # A quantized height field makes only square voxel stairs, and the slow
    # lock offsets break up concentric ledges without random speckles.
    for ix in range(24):
        x=5+ix*.25
        for iz in range(21):
            z=5.25+iz*.25
            dx,dz=(x+.125-8)/3.1,(z+.125-7.875)/2.8
            dome=math.sqrt(max(0,1-dx*dx-dz*dz))
            lock=.12*math.cos((ix//2)*1.6)+.10*math.sin((iz//2)*1.8+(ix//3)*.7)
            top=min(13,round((11.15+1.65*dome+lock)*4)/4)
            color=('hair_top' if top>=12.75 and ix//2 in (3,4,7,8) else
                   'hair_light' if ix//2 in (1,3,5,8,10) else 'hair')
            v.block((x,10.75,z),(x+.25,top,z+.25),color)
    for i in range(10):
        x=5.5+i*.5
        bottom=8.5+(.25 if i in (0,3,6,9) else 0)
        depth=10.5 if i%3 else 10.75
        v.block((x,bottom,10),(x+.5,12-(.25 if i%3 else 0),depth),
                ('hair','hair_light','hair_dark')[i%3])
    lows=[9.25,9,8.75,8.5,8.75,9.25,10,10.25,
          10.5,10.25,10,9.75,9.5,9.75,10.25,10.5,
          10.5,10.25,10,9.5,9.25,8.75,9,9.25]
    for i,low in enumerate(lows):
        x=5+i*.25
        low+=.75 if 6<=i<=18 else .5
        front=4.75 if i in (3,4,10,11,12,17,18,21) else 5
        color=('hair_dark' if i<3 or i>21 else
               'hair_light' if i in (5,6,7,12,13,14,18,19) else 'hair')
        v.block((x,low,front),(x+.25,11.75,5.75),color)
    for first,last,low,high,front,color in (
            (0,3,11,11.75,5,'hair_dark'),(3,6,11.5,12.25,4.75,'hair'),
            (6,9,11.25,12,5,'hair_light'),(9,12,11.75,12.5,4.75,'hair'),
            (12,14,11.25,12.25,4.75,'hair_light'),(14,18,11.5,12.25,5,'hair'),
            (18,21,11.25,12,4.75,'hair_light'),(21,24,11,11.75,5,'hair_dark')):
        v.block((5+first*.25,low,front),(5+last*.25,high,5.75),color)
    for side,x in (('left',5),('right',10.5)):
        for j in range(12):
            z=5.75+j*.25
            bottom=8.5+(0 if j<4 else .25 if j<8 else .5)
            edge=.25 if j%4 in (1,2) else 0
            v.block((x-edge,bottom,z),(x+.5,11.5,z+.25),'hair_dark' if j<4 else 'hair')
    v.emit(g)

    g.group='Teto flat Minecraft pixel expression'
    _paint_face(g)

    g.group='Teto square stepped drill twin tails'
    _square_curl(g,'left',3.75,1)
    _square_curl(g,'right',12.25,-1)

    g.group='Teto tiny white voxel bows'
    for side,cx in (('left',5),('right',11)):
        v=_Voxels('Teto '+side+' pixel bow')
        v.block((cx-.25,12.25,7.25),(cx+.25,12.75,7.75),'bow_shadow')
        v.block((cx-.25,12.5,7),(cx+.25,12.75,7.25),'white')
        v.block((cx-.75,12.75,7.25),(cx-.25,13,7.75),'white')
        v.block((cx-.75,13,7.25),(cx-.5,13.5,7.5),'white')
        v.block((cx+.25,12.5,7.25),(cx+.75,12.75,7.75),'white')
        v.block((cx+.5,12.75,7.25),(cx+1,13,7.5),'white')
        v.block((cx,12,7.25),(cx+.25,12.5,7.5),'white')
        v.emit(g)
    narrow_groups={'Teto square skin head','Teto dense stepped pink voxel hair',
                   'Teto square stepped drill twin tails','Teto tiny white voxel bows'}
    for face in g.faces:
        if face['group'] in narrow_groups:
            face['vertices']=[[8+(x-8)*.84,y,z] for x,y,z in face['vertices']]
    return g
