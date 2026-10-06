"""Project DIVA Future Tone's sloped display, controls and layered header."""
import math
from PIL import Image


def build_upper(cube, polygon, art_dir):
    # Coordinates are drawn from the front, then mirrored once by the exporter.
    pivot = (8, 17.2, -4.0)
    slope = ('x', 45, pivot)
    group = 'Sloped landscape monitor'
    cube('Sloped monitor black enclosure',(.75,17.35,-3.98),
         (15.25,28.67,-2.45),'black',rotation=slope,group=group)
    cube('Landscape display recessed rubber seal',(1.06,18.75,-4.105),
         (14.94,27.05,-3.87),'rubber',rotation=slope,group=group)
    source=Image.open(art_dir/'display-artwork-source.png')
    width=13.35
    height=width*source.height/source.width
    assert 7.0 < height < 8.2, 'Expected a 16:9 landscape display'
    cube('Hatsune Miku illuminated landscape display',(8-width/2,19.04,-4.19),
         (8+width/2,19.04+height,-4.065),'black',rotation=slope,
         north=('display',[0,0,16,16]),glow=('north',),group=group)
    # Thick separately sloped bezel lips keep the display genuinely inset.
    for side,x0,x1 in (('Left',.62,1.31),('Right',14.69,15.38)):
        cube(side+' monitor bevel side',(x0,18.65,-4.36),(x1,27.12,-4.07),
             'charcoal',rotation=slope,group=group)
    cube('Monitor upper black branded brow',(.63,26.87,-4.39),
         (15.37,28.68,-4.08),'black',rotation=slope,group=group)
    cube('SEGA monitor badge',(7.18,27.39,-4.425),(8.82,27.79,-4.38),
         'silver',north=('details',[.125,13.625,3.875,15.875]),rotation=slope,group=group)
    cube('Monitor lower control warning rail',(.65,17.53,-4.39),
         (15.35,18.76,-4.08),'black',rotation=slope,
         north=('details',[8.125,6.625,15.875,7.875]),group=group)
    cube('Lower screen coin slit plate',(13.40,17.76,-4.455),(13.88,18.49,-4.40),
         'silver',rotation=slope,group='Coin and price hardware')
    cube('Lower screen coin slit',(13.60,17.85,-4.48),(13.68,18.37,-4.445),
         'rubber',rotation=slope,group='Coin and price hardware')

    # The black louver and card/instruction shelf belong to the same sloped bay.
    cube('Instruction shelf black enclosure',(.58,28.67,-3.98),
         (15.42,34.06,-2.28),'black',rotation=slope,group='Instruction shelf')
    cube('Wide horizontal ventilation grille',(.60,28.78,-4.30),
         (15.40,30.70,-4.03),'vent',rotation=slope,group='Instruction shelf')
    for j in range(6):
        y=28.89+j*.28
        cube('Vent grille raised horizontal louver '+str(j),(.79,y,-4.385),
             (15.21,y+.10,-4.295),'black',rotation=slope,group='Instruction shelf')
    cube('Instruction and Aime panel metal surround',(.60,30.81,-4.18),
         (15.40,34.02,-3.97),'silver',rotation=slope,group='Instruction shelf')
    cube('Printed instructions and centered Aime reader',(.77,30.94,-4.225),
         (15.23,33.89,-4.175),'white',rotation=slope,
         north=('details',[8.125,4.125,15.875,6.375]),group='Instruction shelf')
    for x in (.92,6.19,9.69,15.0):
        for y in (31.10,33.67):
            cube('Instruction cover countersunk screw '+str((x,y)),(x,y,-4.265),
                 (x+.10,y+.10,-4.22),'steel',rotation=slope,group='Cover screws')

    # Broad printed cheeks slope toward the player. The bottom caps and tray
    # turn forward horizontally, reproducing the cabinet's curved silhouette.
    for side,x0,x1 in (('Left',-1.03,1.16),('Right',14.84,17.03)):
        cube(side+' white sloped cheek backing',(x0,17.40,-4.14),
             (x1,34.21,-3.40),'white',rotation=slope,group='Printed rainbow cheeks')
        cube(side+' rainbow and teal hexagon printed cheek',(x0+.09,17.58,-4.255),
             (x1-.09,34.06,-4.135),'white',rotation=slope,
             north=('details',[.125,.125,3.875,7.875]),
             group='Printed rainbow cheeks')
        inner0,inner1=(x1-.11,x1+.025) if side=='Left' else (x0-.025,x0+.11)
        cube(side+' continuous white-cyan inner LED',(inner0,17.50,-4.295),
             (inner1,34.10,-4.195),'white',rotation=slope,glow=True,
             group='White side illumination')
        outer0,outer1=(x0-.10,x0+.025) if side=='Left' else (x1-.025,x1+.10)
        cube(side+' cheek outer silver trim',(outer0,17.53,-4.20),
             (outer1,34.15,-3.90),'silver',rotation=slope,group='Printed rainbow cheeks')
        # Short tapered white returns form the rounded front arm ends.
        cx=(x0+x1)/2
        polygon(side+' faceted white control arm end',[(cx-1.18,16.35),
                (cx-.91,15.97),(cx+.91,15.97),(cx+1.18,16.37),
                (cx+.90,17.49),(cx-.88,17.63)],-7.82,-3.52,'white',
                group='Control arm end caps',step=.20)
        cube(side+' arm silver front corner',(cx-.64,16.22,-7.855),
             (cx+.61,16.45,-7.76),'ivory',group='Control arm end caps')
        cube(side+' white control arm rear return',(cx-.58,16.12,-3.65),
             (cx+.58,16.69,.15),'white',group='Control arm end caps')

    # Complete white control deck, with the same triangle/square/cross/circle
    # order and color as the reference. Each lens has its own raised black rim.
    cube('Black projecting control tray',(-.25,15.98,-7.76),
         (16.25,16.76,1.20),'black',group='Four button console')
    cube('Silver white control deck',(-.35,16.76,-7.60),
         (16.35,17.08,-2.64),'white',up=('details',[8.125,.125,15.875,3.875]),
         group='Four button console')
    cube('Long black front bumper',(-.17,16.00,-7.885),
         (16.17,16.54,-7.725),'rubber',group='Four button console')
    cube('Headphone jack recess',(7.48,16.56,-7.645),(8.52,16.89,-7.575),
         'rubber',group='Deck small hardware')
    cube('Headphone jack metal rim',(7.88,16.64,-7.679),(8.12,16.84,-7.639),
         'silver',group='Deck small hardware')
    cube('Headphone jack hole',(7.945,16.684,-7.695),(8.055,16.794,-7.675),
         'black',group='Deck small hardware')
    cube('Touch slider black gasket',(.68,17.09,-4.75),(15.32,17.31,-4.07),
         'black',group='Future Tone touch slider')
    cube('Touch slider silver perimeter',(.78,17.27,-4.70),(15.22,17.37,-4.10),
         'silver',group='Future Tone touch slider')
    cube('Long luminous touch slider',(.87,17.345,-4.655),(15.13,17.415,-4.155),
         'white',up=('details',[.125,12.125,7.875,13.375]),glow=True,
         group='Future Tone touch slider')

    def disc(name,cx,cz,radius,y0,y1,material,top_uv=None,glow=False):
        rows=math.ceil(2*radius/.20)
        for row in range(rows):
            z0=cz-radius+row*2*radius/rows
            z1=cz-radius+(row+1)*2*radius/rows
            half=math.sqrt(max(0,radius**2-(((z0+z1)/2)-cz)**2))
            x0,x1=cx-half,cx+half
            override=None
            if top_uv:
                u0,v0,u1,v1=top_uv
                override=('details',[u0+(x0-cx+radius)/(2*radius)*(u1-u0),
                    v0+(z0-cz+radius)/(2*radius)*(v1-v0),
                    u0+(x1-cx+radius)/(2*radius)*(u1-u0),
                    v0+(z1-cz+radius)/(2*radius)*(v1-v0)])
            cube(name+' row '+str(row),(x0,y0,z0),(x1,y1,z1),material,
                 up=override,glow=glow,group='Four luminous symbol buttons')

    for i,(x,material,symbol) in enumerate(((2.05,'green','Triangle'),(5.89,'pink','Square'),
                                           (9.73,'blue','Cross'),(13.57,'red','Circle'))):
        z=-6.14
        disc(symbol+' black circular socket',x,z,1.43,17.075,17.20,'rubber')
        disc(symbol+' raised dark button rim',x,z,1.32,17.20,17.35,'black')
        disc(symbol+' fine chrome ring',x,z,1.15,17.35,17.43,'silver')
        disc(symbol+' colored lens bevel',x,z,1.04,17.43,17.59,material,glow=True)
        disc(symbol+' illuminated printed symbol',x,z,.94,17.59,17.63,material,
             top_uv=[i*4+.125,8.125,i*4+3.875,11.875],glow=True)
    disc('Small yellow start button black socket',15.65,-5.79,.29,17.09,17.19,'black')
    disc('Small yellow start button cap',15.65,-5.79,.22,17.19,17.28,'yellow')

    # Rear housing joins the deck to the upright speaker and header tower.
    for row in range(20):
        y0=16.15+row*.69
        # Stay behind the whole upper edge of each 45-degree screen course.
        # A shallower support slope can poke through the instruction panel.
        front=max(-1.6,y0-19.41)
        cube('Sloping rear monitor support course '+str(row),(.12,y0,front),
             (15.88,y0+.69,14.78),'black',group='Rear monitor structure')
    cube('Upright logo tower black core',(1.1,29.87,8.14),(14.9,36.52,12.0),
         'black',group='Upright speaker tower')
    cube('Rear upright service panel',(1.80,18.7,14.81),(14.20,29.32,14.99),
         'charcoal',group='Rear access')
    for y in (20.4,26.4):
        cube('Rear display vent '+str(y),(4.5,y,15.01),(11.5,y+1.4,15.13),
             'vent',group='Rear access')

    # Tall white pods with double-lobed black mesh match the real speaker form.
    for side,x0,x1 in (('Left',-1.03,1.94),('Right',14.06,17.03)):
        cube(side+' tall speaker black back',(x0+.08,29.26,8.65),
             (x1-.08,38.28,11.28),'black',group='Tall twin speaker pods')
        polygon(side+' chamfered white speaker body',[(x0,29.66),(x0+.40,29.28),
                (x1-.37,29.28),(x1,29.62),(x1,37.94),(x1-.31,38.30),
                (x0+.36,38.30),(x0,37.94)],7.88,9.09,'white',
                front=('details',[4.125,.125,7.875,7.875]),group='Tall twin speaker pods',step=.25)
        cx=(x0+x1)/2
        # Each mesh lobe is actual inset hardware with a central waist.
        for j,cy in enumerate((34.67,36.30)):
            polygon(side+' black speaker lobe '+str(j),[(cx-.64,cy-.60),
                    (cx-.41,cy-.90),(cx+.39,cy-.90),(cx+.66,cy-.60),
                    (cx+.66,cy+.55),(cx+.39,cy+.84),(cx-.39,cy+.84),(cx-.64,cy+.55)],
                    7.805,7.923,'black_mesh',group='Speaker mesh',step=.20)
        for x in (x0+.24,x1-.33):
            for y in (29.87,37.74):
                cube(side+' speaker silver fixing '+str((x,y)),(x,y,7.75),
                     (x+.10,y+.10,7.86),'silver',group='Speaker fixings')
        cube(side+' speaker inner white lamp',(x1-.14 if side=='Left' else x0+.03,29.63,7.77),
             (x1-.03 if side=='Left' else x0+.14,37.97,7.85),'white',glow=True,
             group='White side illumination')

    # The center brand is a separate plaque between speakers, in front of the
    # much taller silhouette backdrop. Black standoffs and bolts give it depth.
    for x in (1.94,13.55):
        cube('Central sign black vertical standoff '+str(x),(x,30.20,7.70),
             (x+.50,38.0,8.57),'black',group='Brand plaque hardware')
    cube('Central logo metal shadow backing',(2.14,31.13,7.97),
         (13.86,36.59,8.30),'charcoal',group='Central Future Tone plaque')
    cube('Central Project DIVA Future Tone printed plaque',(2.30,31.18,7.79),
         (13.70,36.43,8.01),'white',north=('branding',[.125,.75,15.875,15.25]),
         glow=('north',),group='Central Future Tone plaque')
    cube('Brushed silver panel below central logo',(2.14,29.64,8.06),
         (13.86,31.01,8.30),'silver',group='Central Future Tone plaque')
    for x in (2.40,13.41):
        for y in (31.48,36.12):
            cube('Brand plaque silver bolt '+str((x,y)),(x-.075,y-.075,7.72),
                 (x+.075,y+.075,7.84),'silver',group='Brand plaque hardware')

    # Large sculpted printed header, small top nameplate, and stepped hexagons.
    source=Image.open(art_dir/'header-artwork-source.png')
    header_width=20.20
    header_height=header_width*source.height/source.width
    header_top=44.80
    header_bottom=header_top-header_height
    outline=[(-2.1,header_bottom+.5),(-2.1,41.21),(.5,44.80),
             (17.23,44.8),(18.1,42.99),(18.1,header_bottom+1.21),
             (16.40,header_bottom),(0,header_bottom)]
    polygon('Printed Miku silhouette rainbow header',outline,9.85,10.24,'white',
            front=('header',[0,0,16,16]),group='Miku silhouette header',step=.25)
    for x in (2.04,13.45):
        cube('Header rear mounting upright '+str(x),(x,36.35,10.31),
             (x+.46,46.28,10.71),'black',group='Header structure')
    cube('Header rear cross rail',(2.04,43.34,10.23),(13.91,43.78,10.65),
         'black',group='Header structure')
    top_outline=[(.22,44.79),(15.78,44.79),(14.5,47.25),(1.50,47.25)]
    polygon('Small top Future Tone sign backing',top_outline,9.16,9.71,'white',
            group='Top logo sign',step=.25)
    cube('Top Project DIVA Future Tone wordmark',(5.45,44.88,9.085),
         (10.55,47.228,9.20),'white',north=('branding',[.125,.75,15.875,15.25]),
         glow=('north',),group='Top logo sign')
    for j,material in enumerate(('blue','pink','yellow')):
        cube('Top sign right rainbow stripe '+str(j),(10.59,45.14+j*.33,9.10),
             (14.72-j*.14,45.37+j*.33,9.19),material,group='Top logo sign')
    cube('Top sign lower black mounting edge',(.05,44.62,9.01),
         (15.95,44.85,9.38),'black',group='Top logo sign')

    def line_xy(name,a,b,z,thickness,material):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy)
        nx,ny=-dy/length*thickness/2,dx/length*thickness/2
        polygon(name,[(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),
                     (b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)],z,z+.095,material,
                group='Raised teal hexagon outlines',step=.16)

    def hexagon(name,cx,cy,r,z,filled=False,material='cyan'):
        points=[(cx+math.cos(math.radians(a))*r,cy+math.sin(math.radians(a))*r)
                for a in range(0,360,60)]
        if filled:
            polygon(name,points,z,z+.13,material,group='Header hexagon accents',step=.20)
        else:
            for i,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
                line_xy(name+' edge '+str(i),a,b,z,.10,material)

    hexagon('Upper left open acrylic hexagon',.97,46.12,1.73,8.955)
    hexagon('Upper left overlapping acrylic hexagon',3.50,46.04,1.66,8.82)
    hexagon('Upper left teal filled hexagon',2.22,44.59,1.07,8.72,True)
    hexagon('Large upper right outlined hexagon',12.54,42.31,2.31,9.62)
    hexagon('Large right outlined hexagon',15.74,42.29,2.33,9.51)
    hexagon('Lower right outlined hexagon',14.20,39.57,2.29,9.41)
    hexagon('Small magenta header accent',17.05,43.14,1.07,9.29,True,'pink')
    hexagon('Small teal accent on magenta',17.25,42.62,.40,9.13,True)
