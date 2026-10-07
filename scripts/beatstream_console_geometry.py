"""BeatStream display deck copied from the Nostalgia shell, with native cuboids."""
import math


def build_console(cube, uv):
    cube('Console rear support',(.8,16,3.25),(15.2,18.42,14.8),group='Touchscreen enclosure')
    for i in range(28):
        y0=17.65+8.65*i/28
        y1=17.65+8.65*(i+1)/28
        front=2.8+math.tan(math.radians(22.5))*(y0-19.1)+.72/math.cos(math.radians(22.5))
        cube('Touchscreen solid backing %02d'%i,(1.2,y0,front),(14.8,y1,9.05),group='Touchscreen enclosure')
    cube('Control deck black undertray',(.4,17.1,.85),(15.6,18.34,5.8),group='White control strip')
    for i in range(3):
        inset=(3-i)*.30
        z=i*.30
        cube('Clipped deck underside %d'%i,(.4+inset,17.22,z),(15.6-inset,18.32,z+.31),group='White control strip')
        cube('Clipped white deck %d'%i,(.25+inset,18.12,z),(15.75-inset,18.53,z+.31),'ivory',group='White control strip')
    cube('Flat white front strip',(.25,18.12,.9),(15.75,18.53,2.08),'ivory',group='White control strip')
    cube('White front folded edge',(1.16,17.93,.005),(14.84,18.26,.2),'ivory',group='White control strip')
    cube('Silver front seam',(1.16,17.94,.001),(14.84,18.02,.07),'silver',group='White control strip')
    cube('Printed instruction strip',(1.18,18.531,.12),(14.82,18.565,.72),'ivory',up=('controls',[16,16,0,0]),group='White control strip')
    for x in (.53,15.28):
        cube('Front strip fixing '+str(x),(x,18.532,.97),(x+.14,18.563,1.11),'silver',group='White control strip')
    cube('Coin slot surround',(13.48,18.565,.2),(14.19,18.63,.7),'silver',group='White control strip')
    cube('Coin slot dark opening',(13.77,18.63,.27),(13.89,18.657,.61),'black_key',group='White control strip')

    # Shift the whole lower end forward into the former keyboard opening. The
    # display and its surround share a22.5-degree slope and a narrow plain lip.
    tilt=('x',22.5,(8,19.1,2.8))
    cube('Inclined touchscreen black casing',(.70,18.22,2.53),(15.30,26.85,3.40),'black',rotation=tilt,group='Touchscreen')
    cube('Inclined white touchscreen frame',(.80,18.27,2.39),(15.20,26.80,2.75),'ivory',rotation=tilt,group='Touchscreen')
    cube('Touchscreen black gasket',(1.24,18.56,2.31),(14.76,26.43,2.41),'black_key',rotation=tilt,group='Touchscreen')
    cube('BeatStream lower touch display',(1.46,18.78,2.27),(14.54,26.20,2.32),'black_key',north=('screens',[8,0,16,16]),rotation=tilt,glow=('north',),group='Touchscreen')
    for x in (.91,14.77):
        cube('Touchscreen silver rail '+str(x),(x,18.35,2.27),(x+.24,26.69,2.44),'silver',rotation=tilt,group='Touchscreen trim')
        for y in (18.42,26.43):
            cube('Touchscreen screw '+str((x,y)),(x+.06,y,2.21),(x+.18,y+.14,2.28),'black_key',rotation=tilt,group='Touchscreen hardware')

    # The outer surround changes from white to black on the horizontal line
    # through the inward speaker tips. The white portion belongs to the lower
    # touchscreen; the black portion continues down from the upper monitor.
    seam_y=19.1+(27.73492062465493-19.1+(2.39-2.8)*math.sin(math.radians(22.5)))/math.cos(math.radians(22.5))
    for side,x0,x1 in (('Left',.80,1.24),('Right',14.76,15.20)):
        cube(side+' white lower speaker shoulder',
             (x0,26.50,2.39),(x1,seam_y,3.68),'ivory',rotation=tilt,group='Touchscreen trim')
        cube(side+' black upper speaker shoulder',
             (x0,seam_y,2.39),(x1,30.80,3.68),'black',rotation=tilt,group='Touchscreen trim')

    cube('Speaker fascia rear support',(1,25.9,7.75),(15,29.83,10),group='Speaker enclosure')
    # The broad white bridge and black upper transition use two simple planar
    # meshes, meeting exactly at the unchanged inward speaker-tip line. They
    # replace the former recessed valley and tiny shelf, without a center plaque.

    cube('Upper display black chassis',(.80,29.5,8.10),(15.20,39.45,10.30),group='Upper monitor')
    cube('Upper display black surround',(.68,29.5,7.84),(15.32,39.45,8.35),'black',group='Upper monitor')
    cube('Upper display silver inner bevel',(1.18,30.12,7.72),(14.82,38.50,7.93),'silver',group='Upper monitor')
    cube('Upper display black gasket',(1.40,30.31,7.64),(14.60,38.31,7.80),'black_key',group='Upper monitor')
    cube('BeatStream upper attract display',(1.65,30.55,7.59),(14.35,38.08,7.69),'black_key',north=('screens',[0,0,8,16]),glow=('north',),group='Upper monitor')
    cube('Upper frame diagonal crown',(.91,38.57,7.79),(15.09,39.25,7.85),'black',north=('trim',[0,0,16,16]),group='Upper monitor trim')
    cube('Upper frame diagonal lower band',(.97,29.68,7.78),(15.03,30.04,7.85),'black',north=('trim',[0,0,16,16]),group='Upper monitor trim')
    for x in (.90,14.91):
        for y in (29.77,34.8,39.10):
            cube('Upper monitor fixing '+str((x,y)),(x,y,7.73),(x+.16,y+.16,7.83),'silver',group='Upper monitor hardware')
    cube('Black marquee mounting ledge',(.55,39.2,7.3),(15.45,39.85,10.35),'black',group='Marquee fascia')
    cube('Patterned marquee fascia',(.3,38.98,6.25),(15.8,40.25,7.53),'black',north=('trim',[0,0,16,16]),group='Marquee fascia')
    cube('Marquee fascia silver edge',(.3,40.15,6.17),(15.8,40.31,6.32),'silver',group='Marquee fascia')


def build_marquee(cube, cutout_sprite):
    for x in (3.3,12.1):
        cube('Topper rear mounting post '+str(x),(x,39.4,8.12),(x+.6,43.3,8.48),'black',group='Diecut topper')
    cutout_sprite('BeatStream illustrated diecut topper',(.5,40.15,7.66),(15.5,47.65,7.97),'black_key',group='Diecut topper')
