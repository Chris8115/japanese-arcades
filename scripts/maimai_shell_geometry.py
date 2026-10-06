"""maimai DX's twin sculpted white faces, service column and low shared base.

Source coordinates are drawn from the front around X16. The printed mat is a
thin rubber sheet; it is not a raised platform. Upper screens, circular controls
and the coral visor are supplied by the separate upper-geometry module.
"""
import math


def build_shell(cube, polygon):
    # A shared deep dark chassis ties the two white stations together. Wide
    # surfaces are split into the six native placement cells by the exporter.
    cube('Twin cabinet continuous dark rear chassis',(-2.44,5.25,1.045),
         (34.44,43.48,15.18),'black',group='Shared twin chassis')
    cube('Twin cabinet shared black base pan',(-3.02,.44,-.28),
         (35.02,5.37,15.20),'black',group='Shared black plinth')
    cube('Shared plinth upper charcoal lip',(-3.05,5.05,-.89),
         (35.05,5.80,15.23),'charcoal',group='Shared black plinth')
    cube('Shared plinth dark forward fascia',(-2.97,1.02,-.535),
         (34.97,5.14,-.21),'black',group='Shared black plinth')
    cube('Shared plinth silver bottom edge',(-2.87,.47,-.332),
         (34.87,.62,-.17),'steel',group='Shared black plinth')
    for side,x0,x1 in (('Left',-3.10,-2.83),('Right',34.83,35.10)):
        cube(side+' plinth folded side lip',(x0,.76,-.46),(x1,5.57,15.28),
             'charcoal',group='Shared black plinth')

    # Slightly faceted top/front return on the real low speaker plinth.
    for row in range(5):
        y0=4.86+row*.16
        front=-.56-row*.075
        cube('Plinth forward top bevel course %02d'%row,
             (-2.93,y0,front),(34.93,y0+.16,.25),'charcoal',
             group='Shared black plinth')

    left_outline=[(-2.50,10.35),(-2.50,39.65),(-2.26,40.74),
                  (-1.57,41.65),(14.45,41.65),(15.00,40.90),
                  (15.00,8.02),(14.37,6.80),(13.61,5.90),
                  (.13,5.90),(-1.08,6.55),(-1.97,8.00)]

    def facade(name, points):
        low,high=min(y for x,y in points),max(y for x,y in points)
        count=math.ceil((high-low)/.25)
        angle=math.radians(22.5)
        bend_top=low+.99/math.tan(angle)
        levels=sorted(set([low+(high-low)*i/count for i in range(count+1)]+[bend_top]))
        strips=[]
        for row,(y0,y1) in enumerate(zip(levels,levels[1:])):
            ym=(y0+y1)/2
            cross=[]
            for a,b in zip(points,points[1:]+points[:1]):
                if min(a[1],b[1])<=ym<max(a[1],b[1]):
                    cross.append(a[0]+(b[0]-a[0])*(ym-a[1])/(b[1]-a[1]))
            if len(cross)!=2:continue
            x0,x1=min(cross),max(cross)
            # The broad lower bend is a continuous native 22.5-degree skin.
            # Its stepped backing is inset and entirely behind that plane;
            # exposed horizontal ledges would read as louvers in game.
            if y0<bend_top:
                local0=low+(y0-low)/math.cos(angle)
                local1=low+(y1-low)/math.cos(angle)
                edge_inset=.012 if abs(y1-bend_top)<1e-8 else 0
                cube(name+' smooth lower molded skin course %02d'%row,
                     (x0+edge_inset,local0,.99),(x1-edge_inset,local1,1.09),'white',
                     rotation=('x',-22.5,(16,low,.99)),
                     group='Twin smooth lower facade skins')
                front=.99-(y0-low)*math.tan(angle)+.102
                x0+=.06;x1-=.06
            else:front=0
            key=(round(x0,6),round(x1,6),front)
            if strips and strips[-1][0]==key:
                strips[-1][2]=y1
            else:strips.append([key,y0,y1])
        for row,(key,y0,y1) in enumerate(strips):
            x0,x1,front=key
            cube(name+' molded white shell course %02d'%row,
                 (x0,y0,front),(x1,y1,1.12),'white',group='Twin sculpted white facades')

    facade('Left',left_outline)
    facade('Right',[(32-x,y) for x,y in reversed(left_outline)])
    for side,cx in (('Left',6.40),('Right',25.60)):
        # A pale embossed print provides the star-cut D and angular X without
        # turning the reference's subtle molding into bold painted lettering.
        cube(side+' pale molded DX insignia',(cx-4.50,10.73,-.024),
             (cx+4.50,15.085,.042),'white',
             north=('details',[.125,12.125,7.875,15.875]),
             faces_only=('north',),group='Pale DX front molding')
        # The small black teardrop below each ring is the headphone hardware.
        cube(side+' headphone outlet white mounting boss',(cx-.50,17.23,-.12),
             (cx+.50,18.57,.24),'ivory',group='Under-ring headphone outlets')
        polygon(side+' headphone outlet black rounded face',
                [(cx-.41,18.45),(cx+.41,18.45),(cx+.42,17.71),
                 (cx+.25,17.36),(cx-.25,17.36),(cx-.42,17.71)],
                -.43,-.082,'black',group='Under-ring headphone outlets',step=.13)
        cube(side+' headphone jack chrome rim',(cx-.13,17.65,-.48),
             (cx+.13,17.88,-.411),'steel',group='Under-ring headphone outlets')
        cube(side+' headphone jack dark bore',(cx-.055,17.70,-.509),
             (cx+.055,17.83,-.469),'rubber',group='Under-ring headphone outlets')
        # A low woofer in each half of the black base is visible in the product
        # reference. Its grille is dark and restrained, with no invented LEDs.
        radius=1.26
        for row in range(11):
            y0=3.12-radius+2*radius*row/11
            y1=3.12-radius+2*radius*(row+1)/11
            half=math.sqrt(max(0,radius**2-(((y0+y1)/2)-3.12)**2))
            u0=8.125+(radius-half)/(2*radius)*3.75
            u1=8.125+(radius+half)/(2*radius)*3.75
            v0=12.125+(3.12+radius-y1)/(2*radius)*3.75
            v1=12.125+(3.12+radius-y0)/(2*radius)*3.75
            cube(side+' low plinth speaker row %02d'%row,(cx-half,y0,-.576),
                 (cx+half,y1,-.52),'black_mesh',north=('details',[u0,v0,u1,v1]),
                 group='Two low plinth woofers')
        for x in (cx-5.90,cx+5.90):
            cube(side+' lower facade fixing '+str(x),(x,6.07,.837),
                 (x+.10,6.18,1.051),'steel',group='Cabinet fasteners')

    # A narrow common column carries all central player-service hardware.
    cube('Central service-column dark structural gasket',(14.88,5.76,.13),
         (17.12,42.52,1.23),'rubber',group='Shared central service column')
    cube('Central service-column ivory face',(15.03,8.25,-.17),
         (16.97,42.35,.20),'ivory',group='Shared central service column')
    for row in range(10):
        y0=5.82+row*.25;y1=y0+.25
        front=.86-row*.103
        cube('Central column curved lower foot course %02d'%row,
             (15.04,y0,front),(16.96,y1,1.21),'ivory',group='Shared central service column')
    cube('Central column fine left aluminum seam',(14.982,8.27,-.151),
         (15.043,42.35,.25),'silver',group='Shared central service column')
    cube('Central column fine right aluminum seam',(16.957,8.27,-.151),
         (17.018,42.35,.25),'silver',group='Shared central service column')

    # The camera is a small projecting white housing with a real stepped lens.
    cube('Central player camera ivory housing',(15.14,39.96,-.694),
         (16.86,41.40,-.145),'white',group='Shared player camera')
    cube('Central player camera upper bevel',(15.27,41.39,-.54),
         (16.73,41.57,-.14),'ivory',group='Shared player camera')
    for layer,radius,z0,z1,material in (
            ('black lens surround',.48,-.755,-.674,'black'),
            ('silver lens ring',.37,-.815,-.741,'silver'),
            ('dark optical glass',.285,-.848,-.800,'rubber')):
        for row in range(9):
            y0=40.69-radius+2*radius*row/9
            y1=40.69-radius+2*radius*(row+1)/9
            half=math.sqrt(max(0,radius**2-(((y0+y1)/2)-40.69)**2))
            cube('Camera '+layer+' row %02d'%row,(16-half,y0,z0),
                 (16+half,y1,z1),material,group='Shared player camera')
    cube('Camera small blue optical glint',(15.874,40.745,-.869),
         (16.006,40.843,-.838),'cyan',group='Shared player camera')
    cube('Camera status lamp',(16.49,40.26,-.728),
         (16.60,40.37,-.678),'green',group='Shared player camera')

    # Player selection, Aime reader, the small lower payment screen and coin
    # return are separate pieces on the column rather than a single flat print.
    cube('Central player-information silver plate',(15.21,30.00,-.214),
         (16.79,35.86,-.145),'silver',group='Central instructions and Aime reader')
    cube('Central compact how-to-play instruction label',(15.35,32.12,-.233),
         (16.65,33.24,-.201),'ivory',
         north=('details',[14.1875,10.21875,15.6875,11.51171875]),
         group='Central instructions and Aime reader')
    cube('Central small SEGA maker label',(15.40,30.35,-.235),
         (16.60,30.86,-.201),'ivory',
         north=('details',[13.9375,14.46875,15.1875,15.0]),
         group='Central instructions and Aime reader')
    cube('Central Aime reader black housing',(15.28,24.97,-.338),
         (16.72,28.73,-.149),'black',group='Central instructions and Aime reader')
    cube('Central Aime reader ivory face',(15.46,25.23,-.385),
         (16.54,28.42,-.315),'white',group='Central instructions and Aime reader')
    cube('Central Aime reader pink logo',(15.48,26.39,-.402),
         (16.52,27.055,-.373),'pink',
         north=('details',[12.5,10.515625,13.84375,11.375]),
         group='Central instructions and Aime reader')
    for side,x0,x1,material in (('1P',15.28,15.84,'blue'),('2P',16.16,16.72,'coral')):
        polygon(side+' triangular selection key',[(x0,29.27),(x1,29.27),
                ((x0+x1)/2,28.89)],-.284,-.15,material,
                group='Central instructions and Aime reader',step=.095)
    cube('Central narrow yellow confirmation button',(15.64,24.15,-.298),
         (16.36,24.64,-.15),'yellow',group='Central instructions and Aime reader')
    cube('Central lower reader service door outline',(15.19,11.33,-.224),
         (16.81,19.74,-.148),'steel',group='Central lower payment hardware')
    cube('Central lower reader service door ivory face',(15.29,11.46,-.253),
         (16.71,19.61,-.212),'ivory',group='Central lower payment hardware')
    cube('Central compact payment reader black housing',(15.18,15.94,-.552),
         (16.82,17.69,-.242),'black',group='Central lower payment hardware')
    cube('Central compact payment reader blue bezel',(15.30,16.09,-.595),
         (16.70,17.55,-.523),'blue',group='Central lower payment hardware')
    cube('Central compact payment reader display',(15.425,16.50,-.632),
         (16.575,17.17,-.579),'charcoal',
         north=('details',[12.46875,12.359375,14.5625,13.578125]),
         group='Central lower payment hardware')
    cube('Central coin return black recess',(15.59,13.39,-.318),
         (16.41,15.05,-.242),'rubber',group='Central lower payment hardware')
    cube('Central coin acceptor vertical plate',(15.65,14.02,-.341),
         (16.35,14.98,-.309),'steel',
         north=('details',[12.40625,14.359375,13.296875,15.578125]),
         group='Central lower payment hardware')
    cube('Central coin return silver lower flap',(15.70,13.49,-.345),
         (16.30,13.89,-.303),'steel',group='Central lower payment hardware')
    cube('Central lower service-door chrome lock',(15.85,18.31,-.321),
         (16.15,18.63,-.241),'silver',group='Central lower payment hardware')
    cube('Central service-door narrow keyway',(15.978,18.39,-.343),
         (16.022,18.56,-.310),'rubber',group='Central lower payment hardware')
    for y in (9.39,11.78,20.02,23.51,29.74,35.48,38.81,41.94):
        for x in (15.19,16.69):
            cube('Central column countersunk screw '+str((x,y)),(x,y,-.221),
                 (x+.11,y+.11,-.15),'steel',group='Cabinet fasteners')

    # Two generous rear service panels, vents and side grips make the cabinet
    # coherent when approached from behind or placed free-standing in a room.
    for side,cx in (('Left',6.40),('Right',25.60)):
        cube(side+' rear service gasket',(cx-7.52,6.78,15.165),
             (cx+7.52,40.17,15.292),'rubber',group='Twin rear access panels')
        cube(side+' rear charcoal access door',(cx-7.30,7.01,15.273),
             (cx+7.30,39.94,15.371),'charcoal',group='Twin rear access panels')
        for y in (10.13,33.09):
            cube(side+' rear cooling mesh '+str(y),(cx-3.29,y,15.354),
                 (cx+3.29,y+2.31,15.438),'vent',group='Rear cooling')
            for row in range(4):
                cube(side+' rear cooling louver '+str((y,row)),(cx-3.12,y+.25+row*.47,15.423),
                     (cx+3.12,y+.40+row*.47,15.477),'black',group='Rear cooling')
        for x in (cx-6.96,cx+6.96):
            for y in (7.36,23.62,39.48):
                cube(side+' rear service screw '+str((x,y)),(x,y,15.359),
                     (x+.14,y+.14,15.407),'silver',group='Cabinet fasteners')
    cube('Rear shared mains input plate',(15.20,7.79,15.165),
         (16.80,9.44,15.286),'steel',group='Shared rear hardware')
    cube('Rear shared mains socket',(15.49,8.16,15.269),
         (16.51,8.75,15.389),'rubber',group='Shared rear hardware')
    cube('Rear central identification plate',(15.20,13.20,15.166),
         (16.80,14.07,15.245),'ivory',group='Shared rear hardware')
    for side,x0,x1 in (('Left',-2.542,-2.417),('Right',34.417,34.542)):
        for y in (12.12,29.85):
            cube(side+' recessed side transport grip '+str(y),(x0,y,11.31),
                 (x1,y+.85,13.66),'rubber',group='Side transport hardware')
            a,b=(x0-.028,x0+.016) if side=='Left' else (x1-.016,x1+.028)
            cube(side+' side grip lower folded edge '+str(y),(a,y+.02,11.47),
                 (b,y+.22,13.49),'steel',group='Side transport hardware')

    for x in (-1.22,16.0,33.22):
        for z in (1.68,14.10):
            cube('Cabinet levelling-foot stem '+str((x,z)),(x-.14,.21,z-.14),
                 (x+.14,.75,z+.14),'steel',group='Base feet')
            cube('Cabinet levelling-foot broad pad '+str((x,z)),(x-.40,.08,z-.43),
                 (x+.40,.25,z+.43),'rubber',group='Base feet')

    # Floor mat: thin rubber backing with a printed top facing the player.
    # Reverse both up-face UV axes to compensate for the global X mirror.
    cube('Thin maimai floor mat rubber sheet',(-3.20,.12,-13.00),
         (35.20,.215,.10),'rubber',group='Thin printed floor mat')
    cube('Rainbow maimai DX floor mat printed surface',(-3.08,.203,-12.89),
         (35.08,.254,.01),'coral',up=('details',[15.875,7.875,.125,.125]),
         group='Thin printed floor mat')
