"""Groove Coaster's portrait monitor, illuminated console wings and boosters."""
import math
from PIL import Image


def build_upper(cube, polygon, art_dir):
    # The monitor stands on its own rear column, above and behind the controls.
    source=Image.open(art_dir/'display-artwork-source.png')
    width=14.1
    height=width*source.height/source.width
    bottom=19.4
    cube('Tall portrait monitor black case',(-.60,18.88,9.34),(16.60,45.40,15.10),
         'black',group='Portrait monitor')
    cube('Portrait monitor inset metal bezel',(.12,19.08,9.17),(15.88,44.93,9.48),
         'steel',group='Portrait monitor')
    cube('Portrait screen rubber gasket',(.43,19.20,9.045),(15.57,44.68,9.29),
         'rubber',group='Portrait monitor')
    cube('Groove Coaster gameplay display',(.95,bottom,8.935),(15.05,bottom+height,9.13),
         'black',north=('display',[0,0,16,16]),glow=('north',),group='Portrait monitor')
    cube('Monitor lower beveled ledge',(-.37,18.72,8.96),(16.37,19.03,10.10),
         'charcoal',group='Portrait monitor')
    cube('Screen lower identification label',(6.30,18.94,8.875),(9.7,19.18,9.13),
         'silver',north=('details',[8.25,.25,15.75,3.75]),group='Monitor labels')
    for x in (-.38,16.19):
        for y in (19.55,32.15,44.25):
            cube('Monitor front screw '+str((x,y)),(x,y,9.255),(x+.15,y+.15,9.40),
                 'steel',group='Monitor fasteners')
    for side,x0,x1 in (('Left',-.72,-.50),('Right',16.50,16.72)):
        cube(side+' vertical monitor side return',(x0,19.40,10.33),(x1,44.88,14.81),
             'charcoal',group='Monitor side covers')
        for y in (21.3,40.5):
            cube(side+' monitor side screw '+str(y),(x0-.025,y,13.67),(x1+.025,y+.15,13.82),
                 'steel',group='Monitor fasteners')

    # The classic smoked header is a shallow luminous sign, not a large poster.
    header=[(-1.72,45.28),(-1.72,47.27),(-1.10,47.94),(16.97,47.94),
            (17.72,47.34),(17.72,45.34),(17.10,44.93),(-1.07,44.93)]
    polygon('Classic clipped header dark shell',header,8.22,11.33,'charcoal',
            group='Classic marquee',step=.25)
    face=[(-1.32,45.34),(-1.32,47.29),(-.88,47.68),(16.90,47.68),
          (17.32,47.29),(17.32,45.34),(16.90,45.13),(-.88,45.13)]
    polygon('Groove Coaster luminous dot matrix header',face,8.09,8.30,'purple',
            front=('branding',[.125,.5,11.875,7.5]),glow=('north',),
            group='Classic marquee',step=.25)
    cube('Marquee lower silver support',(-1.20,44.69,8.49),(17.20,44.94,11.84),
         'steel',group='Classic marquee')
    for side,x0,x1 in (('Left',-1.65,-.56),('Right',16.56,17.65)):
        cube(side+' rear header mounting leg',(x0,43.65,14.95),(x1,46.52,16.72),
             'black',group='Marquee brackets')
        cube(side+' header mounting shoulder',(x0,46.38,10.68),(x1,47.37,16.69),
             'black',group='Marquee brackets')
        cube(side+' clipped header end cap',(x0-.04,45.47,8.04),(x1+.04,47.18,8.43),
             'black',group='Classic marquee')
        for y in (45.78,46.88):
            cube(side+' header screw '+str(y),(x0+.34,y,7.99),(x0+.48,y+.14,8.16),
                 'silver',group='Monitor fasteners')

    # A thin shared top surface connects the two freestanding booster pods.
    # Its printed acrylic is two-sided cutout, so the footwell is visible below.
    cube('Booster deck rear structural crossbar',(-3.50,18.90,-.30),(19.50,19.24,1.72),
         'charcoal',group='Controller bridge')
    cube('Front deck narrow clear trim',(-3.45,19.07,-8.48),(19.45,19.31,-8.21),
         'cyan',glow=('north','up'),group='Controller edge lights')
    cube('Clear circuit-printed booster deck',(-3.47,19.29,-8.24),(19.47,19.38,1.70),
         'blue',up=('lights',[8.25,4.25,15.75,7.75]),down=('lights',[8.25,4.25,15.75,7.75]),
         glow=('up','down'),faces_only=('up','down'),group='Clear controller acrylic')
    cube('Center headphone pod',(6.55,18.28,-8.00),(9.45,19.65,-6.73),
         'steel',group='Headphone panel')
    cube('Headphone socket printed face',(6.71,18.40,-8.08),(9.29,19.53,-7.94),
         'black',north=('details',[4.25,.25,7.75,3.75]),group='Headphone panel')
    for x in (6.79,9.05):
        for y in (18.50,19.33):
            cube('Headphone panel silver fixing '+str((x,y)),(x,y,-8.11),(x+.12,y+.12,-8.01),
                 'silver',group='Controller fasteners')

    def drum(name,cx,cz,radius,y0,y1,material,*,lit=False,step=.25):
        # Horizontal X/Z circle built as merged runs, rather than overlapping
        # rotated spokes. The opaque surface clipper removes internal faces.
        count=math.ceil(radius*2/step)
        rows=[];active={}
        for row in range(count):
            z0=cz-radius+row*2*radius/count
            z1=cz-radius+(row+1)*2*radius/count
            dz=(z0+z1)/2-cz
            span=math.sqrt(max(0,radius*radius-dz*dz))
            lo=round((cx-span)/step)*step
            hi=round((cx+span)/step)*step
            if hi<=lo:continue
            key=(lo,hi)
            if key in active:
                rect=active.pop(key);rect[3]=z1
            else:rect=[lo,hi,z0,z1]
            rows.extend(active.values());active={key:rect}
        rows.extend(active.values())
        for i,(x0,x1,z0,z1) in enumerate(rows):
            overrides={}
            if lit:
                ux0=8.25+(x0-cx+radius)/(radius*2)*7.5
                ux1=8.25+(x1-cx+radius)/(radius*2)*7.5
                uz0=8.25+(z0-cz+radius)/(radius*2)*7.5
                uz1=8.25+(z1-cz+radius)/(radius*2)*7.5
                overrides=dict(north=('lights',[ux0,.25,ux1,3.75]),
                               south=('lights',[ux1,.25,ux0,3.75]),
                               east=('lights',[uz0,.25,uz1,3.75]),
                               west=('lights',[uz1,.25,uz0,3.75]),glow=True)
            cube(name+' course %02d'%i,(x0,y0,z0),(x1,y1,z1),material,
                 group='Twin boosters',**overrides)

    for side,x in (('Left',2.6),('Right',13.4)):
        # Tapered black pedestal, broad opal lamp, black control ring and button.
        for index,(r,y0,y1) in enumerate(((1.62,17.56,17.92),(1.91,17.92,18.21),
                                          (2.22,18.21,18.51),(2.50,18.51,18.75))):
            drum(side+' booster tapered support '+str(index),x,-5.0,r,y0,y1,'black',step=.3)
        drum(side+' booster lower dark bezel',x,-5.0,2.96,18.72,18.96,'rubber')
        drum(side+' opal luminous booster drum',x,-5.0,3.03,18.97,20.48,'cyan',lit=True)
        drum(side+' clear booster top rim',x,-5.0,3.12,20.49,20.64,'purple',lit=True)
        drum(side+' booster black sloped collar lower',x,-5.0,2.39,20.66,20.90,'black')
        drum(side+' booster black sloped collar upper',x,-5.0,1.93,20.90,21.23,'charcoal')
        drum(side+' booster fine silver ring',x,-5.0,1.66,21.24,21.36,'silver')
        drum(side+' booster raised black button surround',x,-5.0,1.55,21.36,21.91,'rubber')
        drum(side+' booster top button',x,-5.0,1.23,21.92,22.13,'silver')
        drum(side+' booster opal button cap',x,-5.0,1.01,22.14,22.21,'white')
        for dx,dz in ((-2.55,0),(2.55,0),(0,-2.55),(0,2.55)):
            cube(side+' booster top flange screw '+str((dx,dz)),
                 (x+dx-.09,20.65,-5+dz-.09),(x+dx+.09,20.72,-5+dz+.09),
                 'steel',group='Controller fasteners')

    # Sweeping illuminated acrylic panels wrap each outer controller pedestal.
    # A blue core carries long nested white circuit rails, with bright edge trim.
    profile=[(-8.6,2.13),(-8.80,17.83),(-8.36,19.86),(-6.86,21.05),
             (-3.78,21.28),(.45,20.18),(3.88,15.05),(6.10,9.84),(3.42,2.13)]
    for side,x0,x1 in (('Left',-4.12,-3.68),('Right',19.68,20.12)):
        count=math.ceil((21.28-2.13)/.3)
        for row in range(count):
            y0=2.13+row*(21.28-2.13)/count
            y1=2.13+(row+1)*(21.28-2.13)/count
            y=(y0+y1)/2;cross=[]
            for a,b in zip(profile,profile[1:]+profile[:1]):
                if min(a[1],b[1])<=y<max(a[1],b[1]):
                    cross.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
            if len(cross)<2:continue
            z0,z1=min(cross),max(cross)
            u0=.25+(z0+9.2)/15.4*7.5
            u1=.25+(z1+9.2)/15.4*7.5
            v0=.25+(21.5-y1)/19.5*15.5
            v1=.25+(21.5-y0)/19.5*15.5
            cube(side+' luminous acrylic side course %02d'%row,(x0,y0,z0),(x1,y1,z1),
                 'blue',east=('lights',[u0,v0,u1,v1]),west=('lights',[u1,v0,u0,v1]),
                 glow=('east','west'),group='Illuminated side wings')
            for edge,z in (('front',z0),('back',z1-.17)):
                cube(side+' acrylic '+edge+' light course %02d'%row,
                     (x0-.035,y0,z),(x1+.035,y1,z+.17),'purple',
                     glow=True,group='Acrylic edge lighting')
        # The top shoulders connect the side sheet to the clear control surface.
        cube(side+' controller curved shoulder',(x0-.02,19.34,-7.28),(x1+.02,20.97,-2.49),
             'purple',glow=('east','west','up'),group='Acrylic shoulder')
        for y,z in ((3.06,-7.90),(3.10,2.28),(14.15,3.30)):
            cube(side+' acrylic panel fixing '+str((y,z)),(x0-.065,y,z),(x1+.065,y+.16,z+.16),
                 'silver',group='Controller fasteners')

    cube('Monitor rear gasket',(.27,21.02,15.12),(15.73,44.58,15.25),
         'rubber',group='Rear monitor service panel')
    cube('Monitor rear service cover',(.49,21.23,15.27),(15.51,44.37,15.39),
         'charcoal',group='Rear monitor service panel')
    for y in (23.0,38.0):
        cube('Rear monitor cooling vent '+str(y),(4.88,y,15.42),(11.12,y+2.07,15.52),
             'vent',group='Rear monitor service panel')
    for x in (.86,14.96):
        for y in (21.59,43.8):
            cube('Rear monitor cover screw '+str((x,y)),(x,y,15.43),(x+.15,y+.15,15.58),
                 'steel',group='Monitor fasteners')
