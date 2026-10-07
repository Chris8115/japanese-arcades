"""The red first-generation DDR SuperNOVA cabinet above its separate stage."""
import math
from PIL import Image


def build_cabinet(cube, polygon, mesh, art_dir):
    cube('Low black cabinet plinth',(-.55,.35,.45),(32.55,1.35,15.45),'black',group='Cabinet lower shell')
    cube('Broad red dual speaker enclosure',(-.30,1.15,.82),(32.30,17.40,15.15),'red',group='Cabinet lower shell')
    for side,x0,x1,face in (('Left',-.34,-.28,'west'),('Right',32.28,32.34,'east')):
        cube(side+' red wireframe side artwork',(x0,2.02,1.58),(x1,16.48,14.43),'red',
             **{face:('details',[.125,12.125,7.875,15.875])},group='Cabinet lower shell')
    cube('Black recessed service front',(.03,1.55,.43),(31.97,16.98,1.00),'black',group='Cabinet lower shell')
    cube('Speaker cabinet black horizontal shelf',(-.64,17.22,.19),(32.64,17.74,15.43),'charcoal',group='Cabinet lower shell')
    for name,x in (('Left',-.40),('Right',32.18)):
        cube(name+' polished outer upright',(x,1.0,.34),(x+.22,17.30,1.02),'silver',group='Cabinet chrome trim')
    cube('Lower cabinet chrome sill',(-.37,1.02,.30),(32.40,1.28,.68),'silver',group='Cabinet chrome trim')
    cube('Top shelf polished edge',(-.66,17.28,.14),(32.66,17.51,.27),'steel',group='Cabinet chrome trim')

    def disc(name,cx,cy,r,z0,z1,material,texture=None,glow=False):
        # Real circular rims and lenses match the rounded stage rails. Keep
        # the front UV radial so printed speaker mesh remains undistorted.
        # Large woofers keep a smooth 32-sided outline. Smaller fittings occupy
        # far fewer screen pixels; their original radii and depths do not need
        # the same subdivision count as the large speaker surrounds.
        count=32 if r>3 else 12 if r<.3 else 24
        # The cabinet is .78 as wide as the initial construction grid. Apply
        # the same factor vertically here so its exported fittings stay round.
        ry=r*.78
        ring=[(cx+r*math.cos(i*math.tau/count),cy+ry*math.sin(i*math.tau/count)) for i in range(count)]
        vertices=[(x,y,z0) for x,y in ring]+[(x,y,z1) for x,y in ring]+[(cx,cy,z0),(cx,cy,z1)]
        shell=[[i,(i+1)%count,(i+1)%count+count,i+count] for i in range(count)]
        shell += [[2*count+1,i+count,(i+1)%count+count] for i in range(count)]
        mesh(name+' rim',vertices,shell,material,group='Cabinet speakers and lamps')
        front=[[2*count,(i+1)%count,i] for i in range(count)]
        options={}
        if texture:
            key,(u0,v0,u1,v1)=texture
            options={'texture':key,'uv':[[[u0+(vertices[j][0]-cx+r)/(2*r)*(u1-u0),
                                         v0+(cy+ry-vertices[j][1])/(2*ry)*(v1-v0)] for j in face] for face in front]}
        mesh(name+' face',vertices,front,material,glow=glow,group='Cabinet speakers and lamps',**options)

    for side,cx in (('Left',5.75),('Right',26.25)):
        cube(side+' silver speaker panel',(cx-4.72,1.62,.26),(cx+4.72,16.75,.50),'steel',
             north=('details',[.125,4.125,3.875,7.875]),group='Cabinet speaker panels')
        cube(side+' clear-panel lower edging',(cx-4.72,1.65,.18),(cx+4.72,1.80,.30),'silver',group='Cabinet chrome trim')
        for dx in (-4.75,4.60):
            cube(side+' clear-panel vertical channel '+str(dx),(cx+dx,1.63,.15),
                 (cx+dx+.15,16.78,.40),'silver',group='Cabinet chrome trim')
        disc(side+' large woofer chrome surround',cx,6.42,4.20,-.05,.31,'silver')
        disc(side+' large woofer black suspension',cx,6.42,3.93,-.15,-.02,'rubber')
        disc(side+' large woofer raised mesh',cx,6.42,3.69,-.23,-.12,'black_mesh',
             texture=('details',[8.125,4.125,11.875,7.875]))
        disc(side+' upper tweeter chrome surround',cx,13.19,1.76,-.06,.31,'silver')
        disc(side+' upper tweeter mesh',cx,13.19,1.51,-.16,-.02,'black_mesh',
             texture=('details',[12.125,4.125,15.875,7.875]))
        for dx in (-4.35,4.23):
            for y in (2.12,16.18):
                cube(side+' speaker panel screw '+str((dx,y)),(cx+dx,y,.10),
                     (cx+dx+.12,y+.12,.20),'charcoal',group='Cabinet fasteners')

    # The narrow black column between the two chrome speaker panels contains
    # distinct coin plates, returns, keyed doors and the wired stage connection.
    cube('Central lower black coin column',(11.03,1.44,.16),(20.97,17.0,.51),'rubber',group='Cabinet service hardware')
    for x in (11.08,20.77):
        cube('Coin column brushed upright '+str(x),(x,1.44,.09),(x+.15,17.05,.22),'steel',group='Cabinet service hardware')
    cube('Tall recessed coin service door',(11.70,5.00,.05),(20.30,16.25,.20),'charcoal',group='Cabinet service hardware')
    for cx in (13.73,18.27):
        cube('Coin slot silver plate '+str(cx),(cx-.67,12.00,-.03),(cx+.67,14.50,.075),'steel',group='Cabinet service hardware')
        cube('Coin slot dark vertical mouth '+str(cx),(cx-.10,13.20,-.075),(cx+.10,14.16,-.022),'black',group='Cabinet service hardware')
        cube('Coin return square button '+str(cx),(cx-.45,12.22,-.092),(cx+.45,12.83,-.012),'ivory',group='Cabinet service hardware')
        cube('Coin return catch '+str(cx),(cx-.55,8.76,-.08),(cx+.55,9.65,.07),'black',group='Cabinet service hardware')
        cube('Coin return flap '+str(cx),(cx-.43,8.93,-.11),(cx+.43,9.43,-.067),'steel',group='Cabinet service hardware')
    cube('Lower keyed cashbox door',(11.70,1.90,.06),(20.30,4.78,.22),'charcoal',group='Cabinet service hardware')
    cube('Small service safety label',(12.65,5.22,-.04),(19.35,6.51,.075),'ivory',
         north=('details',[12.125,12.125,15.875,15.875]),group='Cabinet service hardware')
    disc('Cashbox circular lock',16,3.06,.22,-.03,.12,'silver')
    cube('Cabinet stage cable recessed connector',(15.23,1.60,-.04),(16.77,3.00,.26),'black',group='Cabinet stage cable')

    # All CRT parts use one common pivot, giving the entire console the real
    # cabinet's backward lean while keeping the square screen aperture true.
    tilt=('x',11.5,(16,17.4,.15))
    cube('Deep CRT monitor pod',(4.66,17.4,.15),(27.34,34.0,10.2),'black',rotation=tilt,group='Cabinet tilted CRT')
    for side,x0,x1 in (('Left',4.48,4.70),('Right',27.30,27.52)):
        cube(side+' red CRT side panel',(x0,17.6,.03),(x1,33.9,10.0),'red',rotation=tilt,group='Cabinet tilted CRT')
    cube('Red printed CRT front surround',(4.82,17.50,-.04),(27.18,33.87,.20),'red',
         north=('details',[.125,12.125,7.875,15.875]),rotation=tilt,group='Cabinet tilted CRT')
    for x in (4.61,27.15):
        cube('Chrome CRT outer side rail '+str(x),(x,17.35,-.13),(x+.24,34.00,.30),
             'silver',rotation=tilt,group='Cabinet tilted CRT')
    cube('Chrome CRT upper edging',(4.64,33.73,-.15),(27.38,33.98,.31),'steel',rotation=tilt,group='Cabinet tilted CRT')
    cube('Deep black CRT aperture',(7.11,19.36,-.26),(24.89,32.90,-.015),'rubber',rotation=tilt,group='Cabinet tilted CRT')
    cube('Inner beveled CRT lip',(7.48,19.64,-.33),(24.52,32.59,-.245),'charcoal',rotation=tilt,group='Cabinet tilted CRT')
    cube('Luminous four-to-three CRT picture',(7.90,20.02,-.375),(24.10,32.17,-.321),'black',
         north=('display',[0,0,16,16]),glow=('north',),rotation=tilt,group='Cabinet tilted CRT')
    cube('Konami maker strip below CRT',(13.20,18.78,-.285),(18.80,19.50,-.21),'red',
         north=('details',[12.44,8.39,15.70,9.20]),rotation=tilt,group='Cabinet tilted CRT')
    cube('Red wireframe two player apron',(4.78,16.08,-.04),(27.22,17.55,.20),'red',
         north=('details',[.125,13.15,7.875,14.52]),rotation=tilt,group='Cabinet tilted CRT')
    cube('Two player printed control strip',(5.12,17.65,-.25),(26.88,18.65,-.075),'black',
         north=('details',[.125,10.125,15.875,11.875]),rotation=tilt,group='Cabinet tilted CRT')
    # Two green confirm buttons and four yellow selection arrows on the shelf.
    for player,cx in ((1,10.10),(2,21.90)):
        cube(str(player)+'P black control group',(cx-3.15,17.81,-.37),(cx+3.15,18.48,-.11),
             'black',rotation=tilt,group='Cabinet tilted CRT')
        cube(str(player)+'P green rectangular start',(cx-.64,17.90,-.45),(cx+.64,18.36,-.34),
             'green',rotation=tilt,glow=('north',),group='Cabinet tilted CRT')
        for side,x,direction in (('left',cx-2.03,-1),('right',cx+2.03,1)):
            polygon(str(player)+'P yellow '+side+' select',[(x-direction*.30,17.85),
                (x+direction*.37,18.13),(x-direction*.30,18.41)],-.44,-.35,'yellow',
                rotation=tilt,group='Cabinet tilted CRT',step=.11)

    # The large suspended marquee has a chrome frame and paired lamp/speaker
    # wings. Its shallow depth keeps the characteristic opening above the CRT.
    for x in (8.25,22.55):
        cube('Marquee support post '+str(x),(x,31.00,7.12),(x+1.20,35.05,8.82),'black',group='Cabinet marquee supports')
    cube('Red rectangular SuperNOVA marquee',(4.75,34.30,6.35),(27.25,47.93,9.85),'red',group='Cabinet marquee')
    cube('Black marquee inner gasket',(5.50,34.55,6.14),(26.50,47.66,6.42),'black',group='Cabinet marquee')
    with Image.open(art_dir/'header-artwork-source.png') as artwork:
        half_width=12.8*artwork.width/artwork.height/.78/2
    cube('Backlit SuperNOVA marquee artwork',(16-half_width,34.70,6.055),(16+half_width,47.50,6.18),'white',
         north=('header',[0,0,16,16]),glow=('north',),group='Cabinet marquee')
    for x in (4.69,27.03):
        cube('Marquee chrome vertical surround '+str(x),(x,34.18,5.97),(x+.28,48.0,6.62),'silver',group='Cabinet marquee frame')
    for y in (34.18,47.72):
        cube('Marquee chrome horizontal surround '+str(y),(4.71,y,5.96),(27.33,y+.28,6.63),'silver',group='Cabinet marquee frame')
    for side,cx in (('Left',1.90),('Right',30.10)):
        cube(side+' red three-section lamp wing',(cx-2.04,36.02,6.75),(cx+2.04,45.99,10.62),'red',group='Cabinet marquee wings')
        cube(side+' black horizontal upper speaker',(cx-2.31,39.00,6.18),(cx+2.31,42.69,7.05),'black',group='Cabinet marquee wings')
        cube(side+' perforated speaker inset',(cx-2.03,39.28,6.07),(cx+2.03,42.41,6.24),'black_mesh',group='Cabinet marquee wings')
        for label,y,color in (('red top',44.43,'pink'),('amber bottom',37.35,'yellow')):
            cube(side+' '+label+' lamp black socket',(cx-1.52,y-1.32,6.26),
                 (cx+1.52,y+1.32,6.85),'black',group='Cabinet marquee wings')
            disc(side+' '+label+' chrome lamp rim',cx,y,1.02,6.10,6.32,'steel')
            disc(side+' '+label+' glowing round lens',cx,y,.80,6.015,6.16,color,glow=True)
            disc(side+' '+label+' bright lens center',cx,y,.53,5.985,6.03,'white' if color=='pink' else 'ivory',glow=True)
    for x in (5.04,26.93):
        for y in (34.59,47.43):
            cube('Marquee frame fixing '+str((x,y)),(x,y,5.91),(x+.13,y+.13,6.04),'charcoal',group='Cabinet fasteners')

    # Rear access panels, cooling slots and the red-painted outer side walls.
    cube('Back cabinet service panel',(.73,2.07,15.15),(31.27,16.56,15.32),'charcoal',group='Cabinet rear service')
    for cx in (7.20,24.80):
        cube('Rear cabinet cooling panel '+str(cx),(cx-3.65,11.18,15.31),(cx+3.65,14.84,15.40),'vent',group='Cabinet rear service')
        for y in (11.57,12.27,12.97,13.67,14.37):
            cube('Rear horizontal vent '+str((cx,y)),(cx-3.28,y,15.38),(cx+3.28,y+.15,15.45),'black',group='Cabinet rear service')
    cube('Rear mains inlet',(14.70,3.02,15.29),(17.30,4.57,15.48),'black',group='Cabinet rear service')
    for x in (1.18,30.82):
        for z in (2.4,13.75):
            cube('Cabinet levelling-foot stem '+str((x,z)),(x-.13,.11,z-.13),(x+.13,.46,z+.13),'steel',group='Cabinet feet')
            cube('Cabinet levelling-foot pad '+str((x,z)),(x-.37,.06,z-.37),(x+.37,.18,z+.37),'rubber',group='Cabinet feet')

    # A short corrugated umbilical joins the screen cabinet to the metal stage.
    slope=math.degrees(math.atan2(.77,3.31))
    length=math.hypot(.77,3.31)
    cube('Flexible stage cable core',(15.82,1.735,-1.605-length/2),(16.18,2.095,-1.605+length/2),
         'rubber',rotation=('x',-slope,(16,1.915,-1.605)),group='Cabinet stage cable')
    for i in range(19):
        t=i/18;z=.05-3.31*t;y=2.30-.77*t
        cube('Stage connection cable rib '+str(i),(15.75,y-.20,z-.07),(16.25,y+.20,z+.07),
             'charcoal' if i%2 else 'rubber',group='Cabinet stage cable')
