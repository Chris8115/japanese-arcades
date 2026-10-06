"""Reference-led control deck, canted speakers and monitor, in vanilla cuboids."""
import math


def build_console(cube, uv):
    # The black enclosure meets the continuous sloping face. No open space behind
    # the touch panel, and the control shelf has the clipped corners of the real unit.
    cube('Console rear support',(.8,16,3.25),(15.2,18.42,14.8),group='Touchscreen enclosure')
    for i in range(24):
        y0=18.4+7.9*i/24
        y1=18.4+7.9*(i+1)/24
        front=2.8+math.tan(math.radians(22.5))*(y0-19.1)+.72/math.cos(math.radians(22.5))
        cube('Touchscreen solid wedge %02d'%i,(1.2,y0,front),(14.8,y1,9.05),group='Touchscreen enclosure')
    cube('Keyboard black undertray',(.40,17.10,.85),(15.60,18.34,5.8),group='Keyboard deck')
    for i in range(3):
        inset=(3-i)*.30
        z=i*.30
        cube('Clipped deck underside %d'%i,(.40+inset,17.22,z),(15.60-inset,18.32,z+.31),group='Keyboard deck')
        cube('Clipped ivory deck %d'%i,(.25+inset,18.12,z),(15.75-inset,18.53,z+.31),'ivory',group='Keyboard deck')
    cube('Ivory control deck',(.25,18.12,.9),(15.75,18.53,5.3),'ivory',group='Keyboard deck')
    cube('Keyboard front folded edge',(1.16,17.93,-.035),(14.84,18.26,.20),'ivory',
         north=('trim',[0,0,16,16]),group='Keyboard deck')
    cube('Thin champagne front seam',(1.16,17.94,-.058),(14.84,18.02,.07),'gold',group='Keyboard deck')
    cube('Printed instruction and title strip',(1.18,18.531,.09),(14.82,18.565,.80),'ivory',
         up=('controls',[16,16,0,0]),group='Keyboard deck')
    cube('Keybed dark recess',(1.08,18.53,.90),(14.92,18.62,3.86),'black_key',group='Piano keys')
    count=28
    width=13.5/count
    for i in range(count):
        x=1.25+i*width
        cube('Piano ivory key %02d'%i,(x,18.62,1.00),(x+width-.035,18.91,3.78),'white_key',group='Piano keys')
        # The accent only occupies the back of the playing surface.
        if i%7 not in (2,6) and i<count-1:
            cube('Piano black accent %02d'%i,(x+width-.17,18.92,2.50),
                 (x+width+.12,19.07,3.75),'black_key',group='Piano keys')
    cube('Keybed warm light line',(1.25,18.56,.85),(14.75,18.67,.98),'white_key',glow=('north','up'),group='Keyboard lights')
    for x in (.36,14.96):
        cube('Stepped keyboard cheek '+str(x),(x,18.52,.90),(x+.68,18.84,4.40),'ivory',group='Keyboard deck')
        cube('Cheek gold seam '+str(x),(x+.11,18.842,1.25),(x+.17,18.861,4.12),'gold',group='Keyboard deck')
        for z in (1.11,4.03):
            cube('Keyboard fixing '+str((x,z)),(x+.27,18.846,z),(x+.42,18.88,z+.15),'silver',group='Keyboard hardware')
    cube('Coin slot surround',(13.48,18.565,.18),(14.19,18.63,.70),'silver',group='Keyboard hardware')
    cube('Coin slot dark opening',(13.77,18.63,.27),(13.89,18.657,.61),'black_key',group='Keyboard hardware')

    tilt=('x',22.5,(8,19.1,2.8))
    cube('Inclined monitor black casing',(.70,19.05,2.92),(15.30,26.85,3.80),'black',rotation=tilt,group='Touchscreen')
    cube('Inclined ivory monitor frame',(.80,19.10,2.78),(15.20,26.80,3.16),'ivory',rotation=tilt,group='Touchscreen')
    cube('Touchscreen black gasket',(1.35,19.48,2.70),(14.65,26.38,2.80),'black_key',rotation=tilt,group='Touchscreen')
    cube('Detailed rhythm screen',(1.66,19.77,2.66),(14.34,26.09,2.71),
         north=('rhythm',[0,0,16,16]),rotation=tilt,glow=('north',),group='Touchscreen')
    for x in (.91,14.67):
        cube('Touchscreen champagne rail '+str(x),(x,19.20,2.61),(x+.34,26.69,2.78),'gold',rotation=tilt,group='Touchscreen trim')
        cube('Touchscreen light diffuser '+str(x),(x+.10,19.42,2.56),(x+.20,26.47,2.64),'white_key',rotation=tilt,glow=('north',),group='Touchscreen trim')
        for y in (19.25,26.43):
            cube('Touchscreen screw '+str((x,y)),(x+.09,y,2.55),(x+.22,y+.16,2.62),'silver',rotation=tilt,group='Touchscreen hardware')

    # Individual outward-projecting wings face the listener; narrow courses
    # combine the two angles within the vanilla single-axis rotation format.
    speaker_tilt=('x',22.5,(8,26.0,6.45))
    cube('Speaker fascia rear support',(1.0,25.9,7.75),(15.0,29.83,10.0),group='Speaker enclosure')
    cube('Canted central ivory fascia',(4.1,26.0,6.45),(11.9,29.8,8.95),'ivory',rotation=speaker_tilt,group='Speakers and sign')
    sin,cos=math.sin(math.radians(22.5)),math.cos(math.radians(22.5))

    def courses(name,x0,x1,y0,y1,offset,depth,hinge,angle,material,count):
        tile=uv(material)
        for i in range(count):
            low=y0+(y1-y0)*i/count
            high=y0+(y1-y0)*(i+1)/count
            z=6.45+((low+high)/2-26)*sin+offset*cos
            bottom=26+(low-26)*cos-offset*sin
            top=26+(high-26)*cos-offset*sin
            tex_uv=[tile[0],tile[1]+(y1-high)/(y1-y0)*4,tile[2],tile[1]+(y1-low)/(y1-y0)*4]
            cube(name+' course %02d'%i,(x0,bottom,z),(x1,top,z+depth),'ivory',
                 north=('materials',tex_uv),rotation=('y',angle,(hinge,26,z)),group='Angled speaker wings')
    for side,x0,x1,hinge,angle in (('Left',.75,4.4,4.2,-22.5),('Right',11.6,15.25,11.8,22.5)):
        courses(side+' housing',x0,x1,26.0,29.8,0,1.35,hinge,angle,'ivory',20)
        courses(side+' inset round grille',x0+.20,x1-.20,26.3,29.5,-.13,.13,hinge,angle,'speaker',20)
        for y in (26.10,29.58):
            courses(side+' folded edge '+str(y),x0+.13,x1-.13,y,y+.10,-.20,.19,hinge,angle,'white_key',1)
    # The actual title is a shaped applied plaque, not a wide rectangular screen.
    for i,(inset,y0,y1) in enumerate(((.48,26.42,26.68),(.17,26.68,27.02),(0,27.02,28.60),(.17,28.60,28.93),(.48,28.93,29.22))):
        cube('Plaque shaped gold edge %d'%i,(4.34+inset,y0,6.19),(11.66-inset,y1,6.54),'gold',rotation=speaker_tilt,group='Nostalgia plaque')
        left,right=4.49+inset,11.51-inset
        # The source plaque occupies a square atlas cell. Select its central
        # horizontal band instead of squeezing the full square into this wide
        # fascia: the title becomes taller while retaining the side curls.
        v_top,v_bottom=1.6,6.4
        tex=[8+(left-4.49)/7.02*8,v_top+(29.22-y1)/2.80*(v_bottom-v_top),
             8+(right-4.49)/7.02*8,v_top+(29.22-y0)/2.80*(v_bottom-v_top)]
        cube('Plaque printed relief %d'%i,(left,y0+.015,6.15),(right,y1-.015,6.24),'black_key',
             north=('artwork',tex),rotation=speaker_tilt,glow=('north',),group='Nostalgia plaque')

    cube('Upper display black chassis',(.80,29.5,8.10),(15.20,39.45,10.30),group='Upper monitor')
    cube('Upper ivory display surround',(.68,29.5,7.84),(15.32,39.45,8.35),'ivory',group='Upper monitor')
    cube('Upper display inner gold bevel',(1.18,30.12,7.72),(14.82,38.50,7.93),'gold',group='Upper monitor')
    cube('Upper display black gasket',(1.40,30.31,7.64),(14.60,38.31,7.80),'black_key',group='Upper monitor')
    cube('Nostalgia Op.3 illuminated screen',(1.65,30.55,7.59),(14.35,38.08,7.69),'black_key',
         north=('artwork',[0,0,8,8]),glow=('north',),group='Upper monitor')
    # Matching printed ornament bands with small mechanical fasteners, restrained
    # enough to read as cream sheet metal from normal Minecraft viewing distance.
    cube('Upper frame printed crown',(.91,38.57,7.79),(15.09,39.25,7.85),'ivory',north=('trim',[0,0,16,16]),group='Upper monitor trim')
    cube('Upper frame printed lower band',(.97,29.68,7.78),(15.03,30.04,7.85),'ivory',north=('trim',[0,0,16,16]),group='Upper monitor trim')
    for x in (.90,14.91):
        for y in (29.77,34.8,39.10):
            cube('Upper monitor fixing '+str((x,y)),(x,y,7.73),(x+.16,y+.16,7.83),'silver',group='Upper monitor hardware')
    for x in (1.57,14.38):
        cube('Display light seam '+str(x),(x,30.46,7.54),(x+.05,38.18,7.61),'lavender',glow=('north',),group='Upper monitor lights')
    cube('Upper screen lower light seam',(1.57,30.45,7.55),(14.43,30.50,7.61),'blue',glow=('north',),group='Upper monitor lights')
    cube('Ivory marquee mounting ledge',(.55,39.2,7.30),(15.45,39.85,10.35),'ivory',group='Marquee fascia')
    cube('Ornate cascading marquee fascia',(.30,38.98,6.25),(15.80,40.25,7.53),'ivory',north=('trim',[0,0,16,16]),group='Marquee fascia')
    cube('Marquee fascia champagne edge',(.30,40.15,6.17),(15.80,40.31,6.32),'gold',group='Marquee fascia')
    cube('Cabinet number badge',(.57,39.1,6.1),(1.56,40.15,6.29),'ivory',north=('materials',uv('label')),group='Marquee fascia')
