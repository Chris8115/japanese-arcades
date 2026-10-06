"""Kasane Teto collectible with a compact head and chunky cubic pink hair."""
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
    """Union of equal cubes, with quarter-unit defaults for the outfit."""
    def __init__(self,name,step=.25,origin=(0,0,0)):
        self.name=name
        self.step=step
        self.origin=origin
        self.cells={}

    def block(self,lo,hi,color):
        a=tuple(round((v-o)/self.step) for v,o in zip(lo,self.origin))
        b=tuple(round((v-o)/self.step) for v,o in zip(hi,self.origin))
        assert all(abs(v-(o+i*self.step))<1e-7
                   for bounds,indices in ((lo,a),(hi,b))
                   for v,o,i in zip(bounds,self.origin,indices))
        self.grid_block(a,b,color)

    def grid_block(self,lo,hi,color):
        for x in range(lo[0],hi[0]):
            for y in range(lo[1],hi[1]):
                for z in range(lo[2],hi[2]):
                    self.cells[x,y,z]=color

    def emit(self,g):
        sides={
            'north':((0,0,-1),(3,2,1,0)), 'south':((0,0,1),(4,5,6,7)),
            'west':((-1,0,0),(0,4,7,3)), 'east':((1,0,0),(1,2,6,5)),
            'up':((0,1,0),(3,7,6,2)), 'down':((0,-1,0),(0,1,5,4)),
        }
        for (i,j,k),color in sorted(self.cells.items()):
            x,y,z=(o+n*self.step for o,n in zip(self.origin,(i,j,k)))
            X,Y,Z=x+self.step,y+self.step,z+self.step
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


def _crown(g):
    # Same 12-cube width and eight-cube height as Miku. Teto's neck and
    # accepted face sit half a unit higher; the hair follows that placement.
    v=_Voxels('Teto compact hair cap',.375,(5.75,8.75,4.75))
    block=v.grid_block
    block((0,5,2),(12,7,13),'hair')
    block((2,7,3),(5,8,11),'hair_light')
    block((5,7,4),(7,8,12),'hair')
    block((7,7,5),(10,8,11),'hair_light')
    block((3,7,4),(5,8,7),'hair_top')
    block((6,7,7),(8,8,11),'hair')
    # Broad, stepped fringe locks frame the existing square pixel eyes.
    block((0,1,2),(2,7,5),'hair_dark')
    block((1,0,1),(2,7,4),'hair')
    block((2,4,0),(3,7,4),'hair_light')
    block((3,4,0),(5,7,4),'hair')
    block((5,3,0),(6,7,4),'hair')
    block((6,4,0),(7,7,4),'hair_light')
    block((7,5,1),(9,7,4),'hair_light')
    block((9,4,1),(10,7,4),'hair')
    block((10,0,1),(11,7,4),'hair')
    block((11,1,2),(12,7,4),'hair_dark')
    # Connected side and rear clumps cover the nape without tiny stripes.
    block((0,1,4),(2,7,10),'hair_dark')
    block((10,1,4),(12,7,10),'hair_dark')
    block((1,-1,11),(11,7,13),'hair_dark')
    block((0,2,10),(3,7,14),'hair')
    block((3,0,11),(6,7,14),'hair')
    block((6,1,11),(9,7,14),'hair_light')
    block((9,2,10),(12,7,14),'hair')
    v.emit(g)


def _square_curl(g,side,center,handedness):
    """Three short stepped turns made from full-sized .375-unit cubes."""
    v=_Voxels('Teto '+side+' square curl',.375,(center-.1875,7.625,7.8125))
    v.grid_block((0,0,0),(1,11,1),'hair_groove')
    for step in range(145):
        t=step/144
        angle=handedness*math.tau*3*t+.35
        radius=(1-t)**.65
        x=round(2.5*radius*math.cos(angle))
        z=round(2*radius*math.sin(angle))
        y=round(9*(1-t))
        color=('hair_light' if math.sin(angle)<-.25 else
               'hair_dark' if math.sin(angle)>.35 else 'hair')
        v.grid_block((x,y,z),(x+1,y+2,z+1),color)
    # A compact root joins the curl to the cap beneath its white bow.
    v.grid_block((-1,9,-1),(2,11,2),'hair')
    v.grid_block((1 if center<8 else -3,9,-1),
                 (4 if center<8 else 0,11,2),'hair_dark')
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
    g.box('Teto compact square head',(6.36,8.5,5.5),(9.64,11.372,9.26),'face_base')

    g.group='Teto dense stepped pink voxel hair'
    _crown(g)

    g.group='Teto flat Minecraft pixel expression'
    _paint_face(g)

    g.group='Teto square stepped drill twin tails'
    _square_curl(g,'left',4.625,1)
    _square_curl(g,'right',11.375,-1)

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
    # Lower the bows onto the shortened curl roots, preserving square blocks.
    for face in g.faces:
        if face['group']=='Teto tiny white voxel bows':
            face['vertices']=[[x,y-1,z] for x,y,z in face['vertices']]
    return g
