"""Classic original blue Jubeat: native cabinet, sixteen raised pads and cube."""
import math
from initial_d_geometry import Geometry

COLORS = {
    'black':'#101820','charcoal':'#222c38','edge':'#475765','rubber':'#080d13',
    'silver':'#bac8ce','silver_dark':'#758996','light':'#eef5f4','blue':'#0877bf',
    'blue_dark':'#073365','cyan':'#46d4ff','blue_light':'#71b6d8','glass':'#bfd9df',
    'glass_side':'#66828d','lime':'#c0d649','gold':'#c2aa63','red':'#a33741',
}
SLOPE_Y = math.sin(math.radians(35))
SLOPE_Z = math.cos(math.radians(35))
PAD_ORIGIN = (0,19.5,1.0)
CUBE_CENTER = (8,36,10.45)
CUBE_PITCH = -12
CUBE_SCALE = 9/9.8
NECK_ANGLE = 58
NECK_ORIGIN = (0,PAD_ORIGIN[1]+10*SLOPE_Y,PAD_ORIGIN[2]+10*SLOPE_Z)
NECK_LENGTH = 3.0


def deck_point(x,y,z=0):
    return (x,PAD_ORIGIN[1]+y*SLOPE_Y-z*SLOPE_Z,PAD_ORIGIN[2]+y*SLOPE_Z+z*SLOPE_Y)


def neck_point(x,y,z=0):
    sy,sz=math.sin(math.radians(NECK_ANGLE)),math.cos(math.radians(NECK_ANGLE))
    return (x,NECK_ORIGIN[1]+y*sy-z*sz,NECK_ORIGIN[2]+y*sz+z*sy)


def bevel(g,name,rect,front,back,rim,side='edge',top='silver'):
    """Four crisp bevel faces and a recessed middle, with no soft corners."""
    x,y,X,Y=rect
    g.box(name+' body',(x,y,back),(X,Y,back+.12),side)
    outer=[(x,y,back),(X,y,back),(X,Y,back),(x,Y,back)]
    inner=[(x+rim,y+rim,front),(X-rim,y+rim,front),
           (X-rim,Y-rim,front),(x+rim,Y-rim,front)]
    for i in range(4):
        j=(i+1)%4
        g.face(name+' bevel '+str(i),[outer[i],inner[i],inner[j],outer[j]],top)
    return x+rim,y+rim,X-rim,Y-rim


def build():
    g=Geometry(COLORS)
    g.group='Broad silver feet and black pedestal'
    g.box('Low black footprint',(1.1,0,.95),(14.9,.25,14.85),'rubber')
    g.box('Silver full length sole',(0.55,.25,.55),(15.45,.67,15.15),'silver_dark')
    g.box('Foot plate black upper',(1.0,.67,.8),(15.0,.86,14.85),'black')
    for i,x in enumerate((.6,14.68)):
        g.box('Raised silver foot rail '+str(i),(x,.65,2.15),(x+.72,.99,14.70),'silver')
        for j,z in enumerate((2.6,13.9)):
            g.box('Foot rail bolt %d %d'%(i,j),(x+.22,1,z),(x+.47,1.025,z+.25),'edge')
    profile=[(.85,8.6),(12.6,8.6),(15.85,13.22),(.85,13.22)]
    g.yz_shell('Black support pedestal beneath control cube',3.3,12.7,profile,'black')
    g.box('Rear lower service housing',(3.75,1.0,11.0),(12.25,15.8,13.3),'charcoal')
    for row in range(9):
        g.box('Rear horizontal vent '+str(row),(5.0,3.1+row*.30,13.302),(11.0,3.20+row*.30,13.34),'rubber')
    g.box('Rear black upper backbone',(5.2,16,12.1),(10.8,30.0,13.3),'black')
    for row in range(6):
        g.box('Upper rear cooling slot '+str(row),(6.25,22.0+row*.3,13.305),(9.75,22.11+row*.3,13.34),'edge')
    g.box('Rear power socket frame',(8.7,1.4,13.31),(10.85,2.6,13.38),'rubber')
    g.box('Rear power socket',(9.15,1.8,13.375),(10.45,2.1,13.41),'silver_dark')

    g.group='Blue luminous lower plaque'
    start=len(g.faces)
    panel=bevel(g,'Lower square lamp black surround',(2.8,0,13.2,11.4),-.08,.45,.43,'black','edge')
    g.decal('Blue dot matrix lower jubeat plaque',panel,-.09,'plaque',True)
    for x in (3.05,12.95):
        for y in (.28,11.12):g.disc('Lower plaque screw %.2f %.2f'%(x,y),x,y,.065,-.10,-.04,'silver_dark',12)
    c,s=math.cos(math.radians(35)),math.sin(math.radians(35))
    g.transform(start,lambda x,y,z:(x,1.55+y*c-z*s,1.4+y*s+z*c))
    # Two triangular braces connect the forward lamp to the pedestal.
    for x in (3.10,12.65):
        g.yz_shell('Lower lamp rear brace '+str(x),x,x+.25,
                   [(1.0,1.8),(10.50,8.10),(11.15,8.95),(1.0,9.1)],'charcoal')

    g.group='Rigid tilted lower control cube'
    start=len(g.faces)
    # One real10-unit cube: top, front and printed side faces all inherit
    # the same orthonormal rotation. There are no tapered side cheeks.
    g.box('True cubic lower control housing',(3,0,0),(13,10,10),'charcoal')
    for x,left in ((2.982,True),(13.018,False)):
        points=[(x,9.4,.6),(x,.6,.6),(x,.6,9.4),(x,9.4,9.4)]
        uv=[(0,0),(0,16),(16,16),(16,0)]
        if not left:points.reverse();uv.reverse()
        g.face('Side four by four tile motif '+str(left),points,texture='side',uv=uv)
    g.transform(start,deck_point)
    lower_cube_corners=[deck_point(3,y,z) for y,z in ((0,0),(10,0),(10,10),(0,10))]

    g.group='Square pads on control cube top face'
    start=len(g.faces)
    g.box('Control deck black slab',(3,0,-.015),(13,10,.10),'rubber')
    g.box('Control deck thin metal underlip',(3.12,.12,-.07),(12.88,9.88,-.01),'silver_dark')
    g.box('Deep pad matrix black bed',(3.32,.50,-.13),(12.68,9.50,-.065),'black')
    # This is a physical 4 by 4 array, not a single screen texture.
    pads=[]
    width=2.05;pitch=2.18;bottom=.705
    for row in range(4):
        for col in range(4):
            i=row*4+col;x=3.705+col*pitch;y=bottom+row*pitch
            bounds=(x,y,x+width,y+width)
            interior=bevel(g,'Raised transparent pad %02d'%i,bounds,-.37,-.16,.13,'glass_side','glass')
            xx,yy,XX,YY=interior
            u0,v0=(col*4+.10),(3-row)*4+.10
            u1,v1=u0+3.8,v0+3.8
            g.face('Illuminated square pad face %02d'%i,[(XX,YY,-.379),(XX,yy,-.379),(xx,yy,-.379),(xx,YY,-.379)],
                   texture='pads',uv=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)],glow=True)
            # Two short bright catchlights sell the clear acrylic cap.
            g.box('Pad acrylic highlight %02d'%i,(x+.16,y+width-.15,-.39),(x+.76,y+width-.11,-.376),'light')
            corners=[deck_point(xx,yy,-.379),deck_point(XX,yy,-.379),deck_point(XX,YY,-.379),deck_point(xx,YY,-.379)]
            pads.append({'index':i,'row':row,'column':col,
                         'center':deck_point(x+width/2,y+width/2,-.379),
                         'face_corners':corners,'local_rectangle':list(bounds)})
    for x in (3.26,12.74):
        for y in (.27,9.73):g.disc('Deck bolt %.2f %.2f'%(x,y),x,y,.075,-.083,-.03,'silver',12)
    g.transform(start,deck_point)

    g.group='Distinct sloped blue display neck'
    start=len(g.faces)
    g.box('Sloped display neck black body',(3.1,0,0),(12.9,NECK_LENGTH,.46),'black')
    inner=bevel(g,'Sloped neck display raised border',(3.22,.05,12.78,NECK_LENGTH-.07),-.11,.02,.28,'blue_dark','edge')
    g.decal('Blue illuminated rectangular display neck',inner,-.123,'neck',True)
    for x in (3.36,12.64):
        for y in (.20,NECK_LENGTH-.24):g.disc('Display neck screw %.2f %.2f'%(x,y),x,y,.06,-.132,-.075,'silver_dark',12)
    g.transform(start,neck_point)

    g.group='Metal coin and card service fascia'
    start=len(g.faces)
    g.box('Black service sloped face',(2.15,0,-.04),(13.85,5.15,.15),'black')
    g.box('Service metal coin strip',(2.90,3.58,-.12),(13.10,4.95,-.035),'silver')
    g.box('Card reader black surround',(3.35,3.86,-.20),(6.60,4.64,-.115),'rubber')
    g.box('Card reader silver slot',(3.55,4.23,-.23),(6.37,4.40,-.195),'silver_dark')
    g.box('Card opening black line',(3.72,4.28,-.243),(6.24,4.35,-.219),'rubber')
    g.box('Coin entry upper black surround',(7.0,3.92,-.205),(9.85,4.67,-.12),'edge')
    g.box('Coin vertical opening',(8.15,4.05,-.225),(8.37,4.56,-.195),'rubber')
    g.box('Service tiny instructions panel',(10.2,3.87,-.15),(12.72,4.67,-.125),'light')
    g.decal('Service coin return caption',(10.30,4.04,12.60,4.50),-.156,'labels')
    g.box('Operator dark service door',(3.55,.35,-.09),(9.80,3.45,-.035),'rubber')
    g.box('Coin return silver frame',(4.05,.68,-.16),(6.1,1.86,-.09),'silver_dark')
    g.box('Coin return recessed pocket',(4.28,.87,-.175),(5.91,1.70,-.155),'black')
    g.box('Coin return lower lip',(4.28,.77,-.29),(5.91,.93,-.14),'edge')
    g.box('Operator lock plate',(7.98,1.66,-.16),(8.94,2.57,-.09),'edge')
    g.disc('Operator barrel lock',8.46,2.10,.22,-.195,-.155,'silver',16)
    g.box('Lock key slit',(8.42,1.97,-.209),(8.50,2.23,-.191),'black')
    g.box('Blue contactless card label',(11.08,.90,-.12),(12.40,2.30,-.05),'blue')
    g.decal('Contactless identifier',(11.19,1.02,12.29,2.18),-.131,'card')
    # The service fascia occupies the adjacent cube face (local Y=0).
    # Its outward normal is exactly perpendicular to the pad top normal.
    g.transform(start,lambda x,y,z:deck_point(8+(x-8)*.84,z-.04,9.4-y*1.65))

    g.group='Separate silver square speakers'
    g.box('Speaker support bridge',(1.1,27.8,11.65),(14.9,29.3,13.4),'black')
    start=len(g.faces)
    for side,x in (('left',.65),('right',12.70)):
        g.box(side+' silver speaker enclosure',(x,26.7,7.8),(x+2.65,29.45,10.75),'silver_dark')
        inner=bevel(g,side+' speaker brushed bevel',(x,26.7,x+2.65,29.45),7.70,7.82,.19,'silver_dark','silver')
        g.decal(side+' perforated black speaker grille',inner,7.692,'speaker')
        for xx in (x+.14,x+2.50):
            for yy in (26.84,29.30):g.disc(side+' speaker screw %.2f %.2f'%(xx,yy),xx,yy,.055,7.685,7.73,'edge',12)
    g.transform(start,lambda x,y,z:(x,y+.7,z+2.4))
    g.box('Upper panel mounting block',(3.8,27.65,11.8),(12.2,29.55,13.1),'black')
    panel=bevel(g,'Separate silver utility panel',(3.45,27.80,12.55,29.45),10.95,11.16,.18,'silver_dark','silver')
    g.decal('Indicator bar above play grid',(3.72,28.03,12.28,29.22),10.931,'labels')

    g.group='Black framed blue illuminated cube topper'
    g.box('Cube rear neck',(6.4,29.1,10.5),(9.6,32.2,13.0),'black')
    start=len(g.faces)
    lo=(3.1,29.8,5.1);hi=(12.9,39.6,14.9);thick=.39
    # Flat luminous inset panes provide a blue acrylic appearance. The full
    # cube frame is modeled in3D, including its rear and top surfaces.
    g.box('Cube blue inner block',(3.42,30.12,5.42),(12.58,39.28,14.58),'blue_dark')
    g.decal('Blue cube front jubeat grid',(3.49,30.19,12.51,39.21),5.405,'cube',True)
    g.face('Blue cube rear jubeat grid',[(3.49,39.21,14.595),(3.49,30.19,14.595),(12.51,30.19,14.595),(12.51,39.21,14.595)],
           texture='cube',uv=[(0,0),(0,16),(16,16),(16,0)],glow=True)
    for x,left in ((3.405,True),(12.595,False)):
        near,far=(5.49,14.51) if left else (14.51,5.49)
        pts=[(x,39.21,near),(x,30.19,near),(x,30.19,far),(x,39.21,far)]
        uv=[(0,0),(0,16),(16,16),(16,0)]
        g.face('Blue cube side jubeat grid '+str(left),pts,texture='cube',uv=uv,glow=True)
    g.face('Blue cube upper grid',[(3.49,39.295,5.49),(3.49,39.295,14.51),(12.51,39.295,14.51),(12.51,39.295,5.49)],
           texture='cube_top',uv=[(16,16),(16,0),(0,0),(0,16)],glow=True)
    for x in (lo[0],hi[0]-thick):
        for z in (lo[2],hi[2]-thick):g.box('Cube corner upright %.2f %.2f'%(x,z),(x,lo[1],z),(x+thick,hi[1],z+thick),'black')
    for y in (lo[1],hi[1]-thick):
        for z in (lo[2],hi[2]-thick):g.box('Cube horizontal frame %.2f %.2f'%(y,z),(lo[0],y,z),(hi[0],y+thick,z+thick),'black')
        for x in (lo[0],hi[0]-thick):g.box('Cube side frame %.2f %.2f'%(x,y),(x,y,lo[2]+thick),(x+thick,y+thick,hi[2]-thick),'black')
    for x in (3.58,12.42):
        g.box('Cube inset cyan edge '+str(x),(x,30.3,5.388),(x+.045,38.99,5.41),'blue_light')
    c,s=math.cos(math.radians(CUBE_PITCH)),math.sin(math.radians(CUBE_PITCH))
    g.transform(start,lambda x,y,z:(8+(x-8)*CUBE_SCALE,
                                    CUBE_CENTER[1]+((y-34.7)*c-(z-10)*s)*CUBE_SCALE,
                                    CUBE_CENTER[2]+((y-34.7)*s+(z-10)*c)*CUBE_SCALE))
    cube_bounds=[[min(p[i] for f in g.faces[start:] for p in f['vertices']),
                  max(p[i] for f in g.faces[start:] for p in f['vertices'])] for i in range(3)]

    metadata={'machine':'Original blue Jubeat single cabinet','front':'north (-Z)',
              'block_units':16,'pad_count':16,'pads':pads,
              'pad_plane':{'origin':PAD_ORIGIN,'up_axis':(0,SLOPE_Y,SLOPE_Z),
                           'outward_normal':(0,SLOPE_Z,-SLOPE_Y),'slope_degrees':math.degrees(math.atan2(SLOPE_Y,SLOPE_Z))},
              'cabinet_profile_yz':profile,
              'lower_control_cube':{'x_bounds':[3,13],'size':[10,10,10],
                                    'top_front_origin':PAD_ORIGIN,
                                    'up_back_axis':(0,SLOPE_Y,SLOPE_Z),
                                    'into_volume_axis':(0,-SLOPE_Z,SLOPE_Y),
                                    'side_corners_yz':[[p[1],p[2]] for p in lower_cube_corners]},
              'lower_plaque_recline_degrees':35,
              'display_neck':{'origin':NECK_ORIGIN,'slope_degrees':NECK_ANGLE,
                              'width':9.8,'height':NECK_LENGTH},
              'upper_panel_bounds':[[3.45,12.55],[27.80,29.45],[10.931,11.28]],
              'cube':{'center':CUBE_CENTER,'pitch_degrees':CUBE_PITCH,'bounds':cube_bounds},
              'maximum_height':cube_bounds[1][1]}
    return g,metadata
