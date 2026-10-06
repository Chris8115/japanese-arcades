"""Chrono Circle's inclined circular controls and deep speaker canopy."""
import math
from PIL import Image


def build_upper(cube, polygon, art_dir):
    cx,cy=8,26
    pivot=(cx,cy,0)
    slope=('x',22.5,pivot)
    face_uv=[.125,.125,7.875,7.875]
    outline=[(-2.40,16.60),(-1.35,15.60),(17.35,15.60),(18.40,16.60),
             (18.40,35.33),(17.38,36.40),(-1.38,36.40),(-2.40,35.33)]
    polygon('Clock panel thick charcoal backing',outline,.39,1.60,'charcoal',
            rotation=slope,group='Clock panel structure',step=.25)
    polygon('Clock panel sculpted silver perimeter',outline,.29,.50,'silver',
            rotation=slope,group='Clock panel structure',step=.25)
    inset=[(x+(0.13 if x<8 else -.13),y+(.13 if y<26 else -.13)) for x,y in outline]
    polygon('Ivory clock face with rainbow markings',inset,.16,.315,'ivory',
            front=('details',face_uv),rotation=slope,group='Printed clock face',step=.25)

    def circle_band(name,inner,outer,z0,z1,material,glow=False,texture=None,step=.25):
        rows=math.ceil(outer*2/step)
        for row in range(rows):
            y0=cy-outer+row*2*outer/rows
            y1=cy-outer+(row+1)*2*outer/rows
            ym=(y0+y1)/2-cy
            half=math.sqrt(max(0,outer*outer-ym*ym))
            hole=math.sqrt(max(0,inner*inner-ym*ym)) if abs(ym)<inner else 0
            spans=[(-half,half)] if hole==0 else [(-half,-hole),(hole,half)]
            for segment,(a,b) in enumerate(spans):
                if b-a<.015:continue
                uv=None
                if texture:
                    tex,(u0,v0,u1,v1)=texture
                    uv=(tex,[u0+(a+outer)/(outer*2)*(u1-u0),
                        v0+(cy+outer-y1)/(outer*2)*(v1-v0),
                        u0+(b+outer)/(outer*2)*(u1-u0),
                        v0+(cy+outer-y0)/(outer*2)*(v1-v0)])
                cube(name+' row '+str((row,segment)),(cx+a,y0,z0),(cx+b,y1,z1),
                     material,north=uv,rotation=slope,glow=glow,group='Circular control assembly')

    # Annular layers have disjoint radial interiors and separate front depths.
    # Shared row boundaries meet exactly, without overlaid coplanar strips.
    circle_band('Outer silver circular retaining rim',8.37,8.70,-.36,.23,'silver')
    circle_band('Outer charcoal ring shoulder',8.04,8.42,-.72,.22,'charcoal')
    circle_band('Continuous black twelve-button wheel',6.08,8.14,-.94,-.02,'black')
    circle_band('Inner polished screen retaining ring',5.91,6.17,-.37,-.18,'silver')
    circle_band('Circular screen black gasket',5.83,5.96,-.26,-.06,'rubber')
    circle_band('Round illuminated Chrono Circle LCD',0,5.84,-.105,.04,'black',
                glow=('north',),texture=('display',[0,0,16,16]),step=.20)

    def arc_points(inner,outer,center,halfangle):
        angles=[center-halfangle+2*halfangle*i/8 for i in range(9)]
        outer_points=[(cx+outer*math.cos(math.radians(a)),cy+outer*math.sin(math.radians(a))) for a in angles]
        inner_points=[(cx+inner*math.cos(math.radians(a)),cy+inner*math.sin(math.radians(a))) for a in reversed(angles)]
        return outer_points+inner_points

    for i in range(12):
        angle=90-i*30
        label='Clock button %02d '%(i+1)
        polygon(label+'separate black socket',arc_points(6.32,8.06,angle,11.10),
                -1.09,-.905,'rubber',rotation=slope,group='Twelve chrome buttons',step=.25)
        polygon(label+'raised chrome edge',arc_points(6.47,7.94,angle,9.65),
                -1.31,-1.075,'silver',rotation=slope,group='Twelve chrome buttons',step=.22)
        polygon(label+'dark lens separator',arc_points(6.58,7.84,angle,8.55),
                -1.43,-1.295,'steel',rotation=slope,group='Twelve chrome buttons',step=.22)
        polygon(label+'curved white lens',arc_points(6.70,7.73,angle,7.60),
                -1.57,-1.415,'ivory',front=('details',[12.125,8.125,15.875,11.875]),
                rotation=slope,group='Twelve chrome buttons',step=.22)

    # A shallow outer groove is physical and luminous; clock numerals and fine
    # ornamental tick marks remain on the manufactured faceplate texture.
    colors=('cyan','green','yellow','orange','pink','purple','blue','cyan')
    for i in range(24):
        angle=90-i*15
        color=colors[min(7,int(i/3))]
        polygon('Rainbow clock outer light segment %02d'%i,
                arc_points(9.17,9.26,angle,6.7),.105,.165,color,
                rotation=slope,glow=('north',),group='Rainbow clock light groove',step=.22)
    for x,y in ((-1.60,17.30),(17.50,17.30),(-1.70,34.73),(17.57,34.73),
                (1.55,16.22),(14.28,16.22),(1.50,35.77),(14.37,35.77)):
        cube('Faceplate silver fastener '+str((x,y)),(x,y,.065),(x+.13,y+.13,.17),
             'steel',rotation=slope,group='Clock face fasteners')

    # Deep rear chassis follows the actual face angle. Its stepped front stays
    # behind every sloped face; broad printed side cheeks cover the silhouette.
    for row in range(28):
        y0=16.16+row*.69
        y1=y0+.69
        front=(y1-26)*math.tan(math.radians(22.5))+1.30
        cube('Clock housing rear support course '+str(row),(-1.33,y0,front),
             (17.33,y1,14.75),'charcoal',group='Clock housing chassis')

    def side_panel(name,x0,x1,points,material,printed=False):
        lo=min(y for z,y in points);hi=max(y for z,y in points)
        zmin=min(z for z,y in points);zmax=max(z for z,y in points)
        rows=math.ceil((hi-lo)/.30)
        for row in range(rows):
            y0=lo+(hi-lo)*row/rows;y1=lo+(hi-lo)*(row+1)/rows
            ym=(y0+y1)/2;hits=[]
            for a,b in zip(points,points[1:]+points[:1]):
                if min(a[1],b[1])<=ym<max(a[1],b[1]):
                    hits.append(a[0]+(b[0]-a[0])*(ym-a[1])/(b[1]-a[1]))
            if len(hits)<2:continue
            za,zb=min(hits),max(hits)
            uv=None
            if printed:
                uv=('details',[.125+(za-zmin)/(zmax-zmin)*3.75,
                    8.125+(hi-y1)/(hi-lo)*7.75,
                    .125+(zb-zmin)/(zmax-zmin)*3.75,8.125+(hi-y0)/(hi-lo)*7.75])
            cube(name+' course '+str(row),(x0,y0,za),(x1,y1,zb),material,
                 east=uv if x0>8 else None,west=uv if x0<8 else None,
                 group='Graphic side enclosures')

    profile=[(-3.8,16.17),(-3.8,18.10),(3.62,35.25),(14.65,35.25),(14.65,16.17)]
    for side,x0,x1 in (('Left',-1.73,-1.35),('Right',17.35,17.73)):
        side_panel(side+' thick side cheek',x0,x1,profile,'ivory')
        inset_profile=[(-3.34,17.16),(-3.34,18.20),(4.07,34.58),(14.25,34.58),(14.25,17.16)]
        a,b=(x0-.07,x0-.025) if side=='Left' else (x1+.025,x1+.07)
        side_panel(side+' printed black clock-mechanism side',a,b,inset_profile,'black',True)
        a,b=(x0-.13,x0+.04) if side=='Left' else (x1-.04,x1+.13)
        cube(side+' continuous inclined orange side lamp',(a,17.50,-3.405),
             (b,35.47,-3.255),'orange',glow=True,
             rotation=('x',22.5,(8,17.50,-3.33)),group='Orange perimeter lamps')

    cube('Rear removable clock housing cover',(.1,18.7,14.78),(15.9,34.56,14.95),
         'steel',group='Rear maintenance')
    for y in (20.25,31.19):
        cube('Rear wide cooling grille '+str(y),(3.20,y,14.98),(12.80,y+1.49,15.15),
             'vent',group='Rear maintenance')
    for x in (.41,15.42):
        for y in (19.10,34.14):
            cube('Rear clock housing screw '+str((x,y)),(x,y,14.965),
                 (x+.14,y+.14,15.04),'silver',group='Rear maintenance')

    # Upper booth: rear-lit cast artwork, four box speakers, deep angular hood.
    cube('Upper poster rear enclosure',(-.5,34.7,9.66),(16.5,47.36,12.0),
         'charcoal',group='Upper character booth')
    source=Image.open(art_dir/'header-artwork-source.png')
    poster_width=12.1
    poster_height=poster_width*source.height/source.width
    cube('Upper booth pale illuminated surround',(-.05,34.95,9.52),
         (16.05,47.06,9.68),'white',glow=('north',),group='Upper character booth')
    cube('Upper character group illuminated poster',(8-poster_width/2,35.05,9.44),
         (8+poster_width/2,35.05+poster_height,9.54),'white',
         north=('header',[0,0,16,16]),glow=('north',),group='Upper character booth')
    # Base and top shelves tie the forward pillars to the back enclosure.
    cube('Upper booth bottom support sill',(-1.10,34.50,3.95),(17.10,35.03,11.90),
         'black',group='Upper booth structure')
    cube('Upper hood canopy ceiling',(-1.85,47.31,-.48),(17.85,47.85,11.94),
         'charcoal',group='Upper booth structure')
    for side,x0,x1 in (('Left',-2.11,-.92),('Right',16.92,18.11)):
        shape=[(3.72,33.95),(5.17,33.95),(5.17,40.30),(.89,44.77),
               (.89,47.83),(-.66,47.83),(-.66,44.21),(3.72,39.65)]
        side_panel(side+' angular forward hood frame',x0,x1,shape,'charcoal')
        innerx0,innerx1=(x1-.13,x1+.04) if side=='Left' else (x0-.04,x0+.13)
        cube(side+' upright orange hood light',(innerx0,35.02,3.63),
             (innerx1,39.52,3.77),'orange',glow=True,group='Orange perimeter lamps')
        cube(side+' continuous diagonal orange hood light',(innerx0+.015,39.51,3.52),
             (innerx1-.015,45.95,3.67),'orange',glow=True,
             rotation=('x',-45,(8,39.59,3.62)),group='Orange perimeter lamps')
        cube(side+' upper logo black clamp',(x0-.06,43.52,-.81),
             (x1+.06,47.91,.55),'black',group='Top logo hardware')

    for vertical,y0,y1,z in (('Lower',35.10,37.60,6.52),('Upper',44.16,46.51,4.37)):
        for side,x0,x1 in (('Left',.18,3.77),('Right',12.23,15.82)):
            cube(vertical+' '+side+' speaker box',(x0,y0,z),(x1,y1,z+2.0),
                 'black',group='Four black speaker boxes')
            polygon(vertical+' '+side+' rounded mesh face',[(x0+.10,y0+.33),
                    (x0+.33,y0+.11),(x1-.33,y0+.11),(x1-.11,y0+.34),
                    (x1-.11,y1-.35),(x1-.34,y1-.11),(x0+.34,y1-.11),(x0+.10,y1-.34)],
                    z-.055,z+.025,'black_mesh',group='Speaker grilles',step=.20)
            cube(vertical+' '+side+' speaker rear mount',(x0+.7,y0+.70,z+1.90),
                 (x1-.7,y0+1.13,9.83),'black',group='Speaker mounting brackets')

    cube('Top CHRONO CIRCLE illuminated logo board',(-1.73,43.66,-.64),
         (17.73,47.83,-.39),'black',north=('branding',[.125,.25,15.875,7.75]),
         glow=('north',),faces_only=('north',),group='Top CHRONO CIRCLE sign')
    for y in (43.62,47.83):
        cube('Clear marquee thin silver edge '+str(y),(-1.73,y,-.64),
             (17.73,y+.045,-.57),'silver',group='Top logo hardware')
    for x in (-1.35,17.21):
        for y in (44.0,47.47):
            cube('Top sign clamp fixing '+str((x,y)),(x,y,-.71),(x+.14,y+.14,-.62),
                 'silver',group='Top logo hardware')
