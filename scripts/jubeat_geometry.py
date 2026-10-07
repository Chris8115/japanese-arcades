"""Classic original blue Jubeat: native cabinet, sixteen raised pads and cube."""
import math
from initial_d_geometry import Geometry
from ddr_mesh_export import pieces,quads

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
LOWER_CUBE_CENTER = (8,3.9,7.1)
LOWER_CUBE_SIZE = 9.2
LOWER_CUBE_PITCH = 25
LOWER_CUBE_PLINTH = .86
SPEAKER_CENTERS = ((2.05,28.8,11.75),(13.95,28.8,11.75))
SPEAKER_PITCH = 10
NECK_ANGLE = 35
NECK_ORIGIN = (0,PAD_ORIGIN[1]+10*SLOPE_Y,PAD_ORIGIN[2]+10*SLOPE_Z)
NECK_LENGTH = 3.0


def deck_point(x,y,z=0):
    return (x,PAD_ORIGIN[1]+y*SLOPE_Y-z*SLOPE_Z,PAD_ORIGIN[2]+y*SLOPE_Z+z*SLOPE_Y)


def neck_point(x,y,z=0):
    sy,sz=math.sin(math.radians(NECK_ANGLE)),math.cos(math.radians(NECK_ANGLE))
    return (x,NECK_ORIGIN[1]+y*sy-z*sz,NECK_ORIGIN[2]+y*sz+z*sy)


def pitched_point(point,center,angle):
    x,y,z=point;c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    return (center[0]+x,center[1]+y*c-z*s,center[2]+y*s+z*c)


def face_bounds(faces):
    return [[min(p[i] for f in faces for p in f['vertices']),
             max(p[i] for f in faces for p in f['vertices'])] for i in range(3)]


def embed_below_plinth(g,start,height):
    """Clip only the hidden portion of a rigid cube below its opaque plinth."""
    visible=[]
    for face in g.faces[start:]:
        if all(p[1]>=height-1e-9 for p in face['vertices']):
            visible.append(face);continue
        for fragment in pieces(list(zip(face['vertices'],face['uv'])),1,[height]):
            if sum(p[1] for p,uv in fragment)/len(fragment)<height-1e-9:continue
            for i,fragment_quad in enumerate(quads(fragment)):
                visible.append({**face,'name':face['name']+' plinth cut '+str(i),
                                'vertices':[p for p,uv in fragment_quad],
                                'uv':[uv for p,uv in fragment_quad]})
    g.faces[start:]=visible


def pane_vertices(side,half,plane):
    """Outward-wound square pane; half is span, plane is distance to center."""
    a,d=half,plane
    return {
        'front':[(a,a,-d),(a,-a,-d),(-a,-a,-d),(-a,a,-d)],
        'rear':[(-a,a,d),(-a,-a,d),(a,-a,d),(a,a,d)],
        'left':[(-d,a,-a),(-d,-a,-a),(-d,-a,a),(-d,a,a)],
        'right':[(d,a,a),(d,-a,a),(d,-a,-a),(d,a,-a)],
        'top':[(-a,d,-a),(-a,d,a),(a,d,a),(a,d,-a)],
        'bottom':[(-a,-d,a),(-a,-d,-a),(a,-d,-a),(a,-d,a)],
    }[side]


def hollow_glass_cube(g,name,size,frame,outer_texture,top_texture,inner_texture,
                      inner_size,inset,inner_sides=('front','left','right','rear')):
    """Real hollow edge frame with glass and small recessed independent displays."""
    h=size/2;glass_plane=h-frame*.25;glass_half=h-frame*.45
    inner_plane=glass_plane-inset;ih=inner_size/2
    for x in (-h,h-frame):
        for z in (-h,h-frame):
            g.box(name+' corner rail %.2f %.2f'%(x,z),(x,-h,z),(x+frame,h,z+frame),'black')
    for y in (-h,h-frame):
        for z in (-h,h-frame):
            g.box(name+' horizontal rail %.2f %.2f'%(y,z),(-h,y,z),(h,y+frame,z+frame),'black')
        for x in (-h,h-frame):
            g.box(name+' depth rail %.2f %.2f'%(x,y),(x,y,-h+frame),(x+frame,y+frame,h-frame),'black')
    for side in ('front','rear','left','right','top','bottom'):
        tex=top_texture if side=='top' else outer_texture
        uv=[(0,0),(0,16),(16,16),(16,0)]
        if side=='top':uv=[(16,16),(16,0),(0,0),(0,16)]
        g.face(name+' exterior glass '+side,pane_vertices(side,glass_half,glass_plane),
               texture=tex,uv=uv,glow=False)
    for side in inner_sides:
        a=ih+.07;d=inner_plane
        lo,hi={
            'front':((-a,-a,-d+.012),(a,a,-d+.12)),
            'rear':((-a,-a,d-.12),(a,a,d-.012)),
            'left':((-d+.012,-a,-a),(-d+.12,a,a)),
            'right':((d-.12,-a,-a),(d-.012,a,a)),
        }[side]
        g.box(name+' recessed display backing '+side,lo,hi,'charcoal')
        tex=inner_texture[side] if isinstance(inner_texture,dict) else inner_texture
        g.face(name+' recessed illuminated artwork '+side,pane_vertices(side,ih,inner_plane),
               texture=tex,uv=[(0,0),(0,16),(16,16),(16,0)],glow=True)
    # Visible interior rails provide depth through the clear fields, without
    # filling the cabinet with an opaque cube behind its exterior glass.
    rail=h-.53
    for x in (-rail,rail):
        for z in (-rail,rail):
            g.box(name+' internal silver upright %.2f %.2f'%(x,z),
                  (x-.04,-h+.25,z-.04),(x+.04,h-.25,z+.04),'silver_dark')
    for z in (-rail,rail):
        g.box(name+' inner bottom bearer '+str(z),(-rail,-h+.32,z-.06),
              (rail,-h+.43,z+.06),'edge')


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
    front_profile=[(.86,10.6),(9.8,10.6),(10.6,6.25),(11.4,6.65),
                   (24.75,9.05),(26.95,12.05),(29.3,12.05)]
    profile=front_profile+[(29.3,14.9),(.86,14.9)]
    # Convex vertical bands preserve the deliberate recessed outline without
    # a centroid fan spanning across the concave ledge below the control cube.
    for i,((y,z),(Y,Z)) in enumerate(zip(front_profile,front_profile[1:])):
        g.yz_shell('Continuous rear chassis band '+str(i),3.9,12.1,
                   [(y,z),(Y,Z),(Y,14.9),(y,14.9)],'black')
    g.box('Rear lower service housing',(4.3,1.0,12.40),(11.7,15.8,14.88),'charcoal')
    for row in range(9):
        g.box('Rear horizontal vent '+str(row),(5.0,3.1+row*.30,14.902),(11.0,3.20+row*.30,14.94),'rubber')
    g.box('Rear black upper backbone',(5.2,16,12.1),(10.8,30.0,14.88),'black')
    for row in range(6):
        g.box('Upper rear cooling slot '+str(row),(6.25,22.0+row*.3,14.905),(9.75,22.11+row*.3,14.94),'edge')
    g.box('Rear power socket frame',(8.2,1.4,14.91),(9.95,2.6,14.98),'rubber')
    g.box('Rear power socket',(8.55,1.8,14.975),(9.55,2.1,15.01),'silver_dark')

    g.group='Lower tilted hollow glass display cube'
    start=len(g.faces)
    hollow_glass_cube(g,'Lower glass cube',LOWER_CUBE_SIZE,.28,'glass_overlay','glass_overlay',
                      {'front':'plaque','left':'plaque_side','right':'plaque_side'},7.40,.52,
                      ('front','left','right'))
    g.transform(start,lambda x,y,z:pitched_point((x,y,z),LOWER_CUBE_CENTER,LOWER_CUBE_PITCH))
    lower_glass_unclipped_bounds=face_bounds(g.faces[start:])
    embed_below_plinth(g,start,LOWER_CUBE_PLINTH)
    lower_glass_bounds=face_bounds(g.faces[start:])
    h=LOWER_CUBE_SIZE/2
    lower_glass_corners=[pitched_point((0,y,z),LOWER_CUBE_CENTER,LOWER_CUBE_PITCH)
                         for y,z in ((h,-h),(h,h),(-h,h),(-h,-h))]

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
    speaker_specs=[]
    for side,center in zip(('left','right'),SPEAKER_CENTERS):
        start=len(g.faces)
        g.box(side+' dark speaker enclosure',(-1.6,-1.6,-1.5),(1.6,1.6,1.5),'black')
        inner=bevel(g,side+' speaker brushed bevel',(-1.6,-1.6,1.6,1.6),-1.61,-1.49,.19,'charcoal','silver')
        g.decal(side+' perforated black speaker grille',inner,-1.622,'speaker')
        for xx in (-1.46,1.46):
            for yy in (-1.46,1.46):g.disc(side+' speaker screw %.2f %.2f'%(xx,yy),xx,yy,.055,-1.638,-1.58,'edge',12)
        g.transform(start,lambda x,y,z,center=center:pitched_point((x,y,z),center,SPEAKER_PITCH))
        speaker_specs.append({'side':side,'center':center,'housing_size':[3.2,3.2,3.0],
                              'pitch_degrees':SPEAKER_PITCH,'bounds':face_bounds(g.faces[start:])})
    g.box('Upper panel mounting block',(3.8,26.85,12.45),(12.2,28.75,13.75),'black')
    panel=bevel(g,'Separate silver utility panel',(3.72,27.00,12.28,28.65),11.60,11.81,.18,'silver_dark','silver')
    g.decal('Indicator bar above play grid',(3.98,27.23,12.02,28.42),11.581,'labels')

    g.group='Black framed blue illuminated cube topper'
    g.box('Cube rear neck',(6.4,29.1,10.5),(9.6,32.2,13.0),'black')
    start=len(g.faces)
    hollow_glass_cube(g,'Upper glass cube',9,.32,'cube','cube_top','cube_inner',5.70,.65)
    g.transform(start,lambda x,y,z:pitched_point((x,y,z),CUBE_CENTER,CUBE_PITCH))
    cube_bounds=face_bounds(g.faces[start:])

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
              'lower_glass_cube':{'center':LOWER_CUBE_CENTER,'size':[LOWER_CUBE_SIZE]*3,
                                  'pitch_degrees':LOWER_CUBE_PITCH,'bounds':lower_glass_bounds,
                                  'unclipped_bounds':lower_glass_unclipped_bounds,
                                  'embedded_in_plinth':True,'clip_below_y':LOWER_CUBE_PLINTH,
                                  'side_corners_yz':[[p[1],p[2]] for p in lower_glass_corners],
                                  'glass_texture':'glass_overlay','art_texture':'plaque',
                                  'side_art_texture':'plaque_side',
                                  'glass_to_art_gap':.52,'art_size':7.40},
              'rear_lower_support':{'bounds':[[3.9,12.1],[.86,29.3],[6.25,14.9]],
                                    'front_profile_yz':front_profile,'profile_yz':profile},
              'display_neck':{'origin':NECK_ORIGIN,'slope_degrees':NECK_ANGLE,
                              'width':9.8,'height':NECK_LENGTH},
              'upper_panel_bounds':[[3.72,12.28],[27.00,28.65],[11.581,11.93]],
              'speakers':speaker_specs,
              'cube':{'center':CUBE_CENTER,'size':[9,9,9],'pitch_degrees':CUBE_PITCH,'bounds':cube_bounds,
                      'glass_to_art_gap':.65,'inner_art_size':5.70,'hollow':True},
              'maximum_height':cube_bounds[1][1]}
    return g,metadata
