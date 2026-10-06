"""Chrono Circle's angular lower housing and illuminated player platform.

The front has opposing slopes: the doors lean forward toward the clock panel,
while the lower CHRONO CIRCLE sign leans back into the narrow waist. The wide
floor platform is part of the cabinet, with clipped corners and a thin orange rim.
"""
import math


def build_shell(cube, polygon):
    """Build the connected lower cabinet, broad footplate and service hardware."""
    def floor_polygon(name, points, y0, y1, material, glow=False):
        # X/Z polygons are sliced into joined strips, merging straight runs.
        zmin,zmax=min(p[1] for p in points),max(p[1] for p in points)
        rows=max(1,math.ceil((zmax-zmin)/.22))
        strips=[]
        for row in range(rows):
            za=zmin+(zmax-zmin)*row/rows
            zb=zmin+(zmax-zmin)*(row+1)/rows
            z=(za+zb)/2
            cross=[]
            for a,b in zip(points,points[1:]+points[:1]):
                if min(a[1],b[1]) <= z < max(a[1],b[1]):
                    cross.append(a[0]+(b[0]-a[0])*(z-a[1])/(b[1]-a[1]))
            cross.sort()
            if len(cross)!=2:continue
            xa,xb=cross
            if strips and abs(strips[-1][0]-xa)<1e-8 and abs(strips[-1][1]-xb)<1e-8:
                strips[-1][3]=zb
            else:strips.append([xa,xb,za,zb])
        for i,(xa,xb,za,zb) in enumerate(strips):
            cube(name+' course %02d'%i,(xa,y0,za),(xb,y1,zb),material,
                 glow=glow,group='Clipped player platform')

    outer=[(-.60,-14.70),(16.60,-14.70),(18.0,-13.30),
           (18.0,-2.38),(17.12,-1.50),(-1.12,-1.50),
           (-2.0,-2.38),(-2.0,-13.30)]
    underside=[(-.53,-14.57),(16.53,-14.57),(17.86,-13.24),
               (17.86,-2.47),(17.03,-1.64),(-1.03,-1.64),
               (-1.86,-2.47),(-1.86,-13.24)]
    inner=[(-.40,-14.20),(16.40,-14.20),(17.48,-13.12),
           (17.48,-2.60),(16.86,-1.98),(-.86,-1.98),
           (-1.48,-2.60),(-1.48,-13.12)]
    floor_polygon('Platform black structural underside',underside,.12,.53,'rubber')
    floor_polygon('Platform continuous luminous orange perimeter',outer,.46,.65,'orange',glow=True)
    floor_polygon('Platform brushed silver outer bevel',outer,.65,1.08,'silver')
    floor_polygon('Platform inset ivory standing surface',inner,1.02,1.32,'ivory')
    # Enlarge the central clock artwork onto a broad14x11.5 canvas. Cropping
    # the source's plain corner margins makes the clock occupy the platform.
    # Its slight oval follows the broad reference floor, while the luminous
    # ring stays fully ahead of the calf and inside the silver perimeter.
    floor_left,floor_width,floor_depth=1.0,14.0,11.5
    floor_center_z=-9.665
    canvas_front=floor_center_z-floor_depth/2
    crop_min,crop_max=37.5,474.5
    crop_span=crop_max-crop_min

    def floor_uv(x0,x1,z0,z1):
        return [(512+crop_min+(x1-floor_left)/floor_width*crop_span)/64,
                (crop_max-(z0-canvas_front)/floor_depth*crop_span)/64,
                (512+crop_min+(x0-floor_left)/floor_width*crop_span)/64,
                (crop_max-(z1-canvas_front)/floor_depth*crop_span)/64]

    cube('Player platform printed clock diagram',(floor_left,1.072,-14.64),
         (floor_left+floor_width,1.352,-3.915),'ivory',
         # Java's up face, after the exporter's global X mirror, needs both
         # axes reversed so XII and the wordmark face a player at the front.
         up=('details',floor_uv(floor_left,floor_left+floor_width,-14.64,-3.915)),
         group='Floor clock decoration')
    # The printed outer rainbow has its own narrow, raised luminous diffuser.
    # Use saturated material colors, rather than sampling tiny atlas arcs with
    # white pixels around them, so this physical light stays vivid at distance.
    # Match the atlas's radius186 and six-pixel stroke at the enlarged mapping.
    inner_x,outer_x=183*floor_width/crop_span,189*floor_width/crop_span
    inner_z,outer_z=183*floor_depth/crop_span,189*floor_depth/crop_span
    light_hues={'orange':.051,'yellow':.137,'green':.365,'cyan':.518,
                'blue':.622,'purple':.737,'pink':.871}
    rows=math.ceil(outer_z*2/.20)
    for row in range(rows):
        z0=floor_center_z-outer_z+row*2*outer_z/rows
        z1=floor_center_z-outer_z+(row+1)*2*outer_z/rows
        dz=(z0+z1)/2-floor_center_z
        outer=outer_x*math.sqrt(max(0,1-(dz/outer_z)**2))
        inner=inner_x*math.sqrt(max(0,1-(dz/inner_z)**2)) if abs(dz)<inner_z else 0
        spans=[(-outer,outer)] if inner==0 else [(-outer,-inner),(inner,outer)]
        for segment,(a,b) in enumerate(spans):
            if b-a<.001:continue
            x0,x1=8+a,8+b
            angle=math.atan2(-dz/floor_depth,((a+b)/2)/floor_width)
            hue=(.20-angle/(2*math.pi))%1
            material=min(light_hues,key=lambda key:
                         min(abs(hue-light_hues[key]),1-abs(hue-light_hues[key])))
            cube('Floor clock luminous rainbow rim '+str((row,segment)),
                 (x0,1.339,z0),(x1,1.410,z1),material,glow=True,
                 group='Floor clock decoration')
    for x in (-1.26,17.26):
        cube('Platform long inner border '+str(x),(x-.035,1.317,-12.72),
             (x+.035,1.349,-3.07),'steel',group='Platform fittings')
    cube('Platform near silver inner border',(.12,1.318,-13.99),
         (15.88,1.349,-13.92),'steel',group='Platform fittings')
    for x,z in ((-.27,-13.78),(16.27,-13.78),(-1.13,-3.11),(17.13,-3.11)):
        cube('Platform countersunk fixing '+str((x,z)),(x-.065,1.314,z-.065),
             (x+.065,1.368,z+.065),'silver',group='Platform fittings')
    # Thin mechanical corner motifs echo the clock's printed white/silver frame.
    for side,x0,x1 in (('Left',.0,1.83),('Right',14.17,16.0)):
        for z in (-13.48,-3.91):
            cube(side+' platform corner horizontal mark '+str(z),
                 (x0,1.314,z),(x1,1.354,z+.065),'steel',group='Platform fittings')
            x=x0 if side=='Left' else x1-.065
            cube(side+' platform corner short return '+str(z),
                 (x,1.314,z),(x+.065,1.354,z+.73),'steel',group='Platform fittings')

    def front_at(y):
        if y<2.20:return -4.65
        if y<=8.25:return -4.65+(y-2.20)*math.tan(math.radians(22.5))
        return -2.144-(y-8.25)*math.tan(math.radians(22.5))

    # Joined courses reproduce the side silhouette without a large rectangular
    # lower block filling the reference cabinet's narrow waist.
    for row in range(35):
        y0=1.26+row*(16.20-1.26)/35
        y1=1.26+(row+1)*(16.20-1.26)/35
        front=front_at((y0+y1)/2)
        cube('White sculpted lower housing course %02d'%row,
             (-.50,y0,front),(16.50,y1,15.10),'white',group='Sculpted lower cabinet')
    cube('Base rear dark bottom seam',(-.31,.97,10.67),(16.31,1.40,15.17),
         'rubber',group='Sculpted lower cabinet')
    cube('Lower cabinet white platform collar',(-.50,1.14,-4.58),
         (16.50,1.94,-1.45),'white',group='Sculpted lower cabinet')

    # Broad smooth door skins sit on the stepped structural support. Both use
    # one shared native22.5-degree transform, so the printed ornament and frame
    # stay continuous instead of being broken by individual horizontal courses.
    door_bottom,door_top=8.63,14.94
    door_pivot=(8,door_bottom,front_at(door_bottom))
    door_slope=('x',-22.5,door_pivot)
    cosine,sine=math.cos(math.radians(22.5)),math.sin(math.radians(22.5))

    def sloped_door(name,x0,x1,bottom,top,offset,back,material,uv=None):
        z0=door_pivot[2]-offset*cosine
        y0=door_bottom+(bottom-door_bottom+sine*offset*cosine)/cosine
        y1=y0+(top-bottom)/cosine
        cube(name,(x0,y0,z0),(x1,y1,door_pivot[2]+back),material,
             north=('details',uv) if uv else None,rotation=door_slope,group='Upper service doors')

    sloped_door('Upper double-door continuous dark surround',.02,15.98,8.52,15.07,
                .15,.13,'rubber')
    for side,x0,x1 in (('Left',.31,7.88),('Right',8.12,15.69)):
        u0=4.125+(x0-.31)/(15.69-.31)*7.75
        u1=4.125+(x1-.31)/(15.69-.31)*7.75
        sloped_door(side+' smooth ivory service door',x0,x1,door_bottom,door_top,
                    .225,-.095,'ivory',[u0,8.125,u1,11.875])

    # The side strips follow the face, rather than becoming unrelated vertical
    # bars. Short silver lips anchor the orange diffuser in the white enclosure.
    for side,x0,x1 in (('Left',-.59,-.45),('Right',16.45,16.59)):
        for row in range(17):
            y0=8.56+row*.445;y1=y0+.445;front=front_at((y0+y1)/2)
            cube(side+' lower side LED steel channel %02d'%row,
                 (x0-.04,y0,front-.115),(x1+.04,y1,front+.23),
                 'steel',group='Lower cabinet illumination')
            cube(side+' lower side orange diffuser %02d'%row,
                 (x0,y0+.025,front-.166),(x1,y1-.025,front-.08),
                 'orange',glow=True,group='Lower cabinet illumination')

    # The shallow shelf and headphone fascia project just ahead of the clock's
    # bottom edge. Keep the small headphone print at its own native proportion.
    cube('Headphone fascia dark structural backing',(-.69,15.13,-5.51),
         (16.69,16.18,-4.63),'black',group='Headphone shelf')
    cube('Headphone fascia brushed light metal face',(-.44,15.23,-5.563),
         (16.44,16.10,-5.49),'silver',group='Headphone shelf')
    cube('Headphone fascia central printed plate',(6.10,15.25,-5.591),
         (9.90,16.09,-5.55),'silver',
         north=('details',[4.125,12.125,11.875,13.875]),group='Headphone shelf')
    cube('Headphone fascia upper orange illuminated edge',(-.40,16.10,-5.59),
         (16.40,16.20,-5.45),'orange',glow=True,group='Headphone shelf')
    cube('Physical headphone socket chrome seat',(7.86,15.53,-5.638),
         (8.14,15.72,-5.578),'steel',group='Headphone shelf')
    cube('Physical headphone socket dark opening',(7.945,15.555,-5.666),
         (8.055,15.675,-5.627),'rubber',group='Headphone shelf')
    for i,material in enumerate(('green','orange','cyan')):
        x=1.27+i*.21
        cube('Headphone fascia small status lamp '+str(i),(x,15.63,-5.603),
             (x+.09,15.72,-5.55),material,glow=True,group='Headphone shelf')
    for x in (-.22,16.09):
        cube('Headphone fascia countersunk screw '+str(x),(x,15.42,-5.607),
             (x+.11,15.53,-5.55),'steel',group='Cabinet fasteners')

    # A fine intake separates the two opposed slopes at the narrow waist.
    cube('Waist grille silver folded surround',(.05,7.39,-2.95),
         (15.95,8.61,-1.79),'silver',group='Waist ventilation')
    cube('Waist broad fine black intake mesh',(.32,7.57,-3.008),
         (15.68,8.44,-2.92),'vent',group='Waist ventilation')
    cube('Waist intake upper dark shadow',(.15,8.47,-2.974),
         (15.85,8.61,-2.78),'rubber',group='Waist ventilation')
    for x in (.43,15.48):
        cube('Waist grille fastener '+str(x),(x,7.72,-3.054),
             (x+.12,7.85,-2.987),'steel',group='Cabinet fasteners')

    # The broad branded calf leans back by 22.5 degrees, matching the reference
    # bend beneath the grille. Its back intersects the stepped white support.
    calf_rotation=('x',22.5,(8,2.72,-4.525))
    cube('Lower calf bevel silver surround',(.14,2.72,-4.625),
         (15.86,7.18,-4.30),'silver',rotation=calf_rotation,group='Lower CHRONO CIRCLE sign')
    cube('Lower calf white CHRONO CIRCLE sign',(.36,2.91,-4.667),
         (15.64,6.99,-4.604),'ivory',rotation=calf_rotation,group='Lower CHRONO CIRCLE sign')
    cube('Lower calf printed CHRONO CIRCLE wordmark',(1.70,3.43,-4.693),
         (14.30,6.43,-4.654),'ivory',rotation=calf_rotation,
         north=('branding',[.125,8.25,15.875,15.75]),group='Lower CHRONO CIRCLE sign')
    for x in (.55,15.32):
        for y in (3.10,6.68):
            cube('Calf sign countersunk fixing '+str((x,y)),(x,y,-4.706),
                 (x+.13,y+.13,-4.654),'steel',rotation=calf_rotation,group='Cabinet fasteners')
    cube('Calf lower white folded kick strip',(-.34,1.67,-4.81),
         (16.34,2.77,-4.48),'white',group='Lower CHRONO CIRCLE sign')

    # Small handles/locks and the right-hand service reader are mounted on the
    # same forward rake as the door. The reader's cyan border is restrained.
    def door_rotation(y,x):
        return ('x',-22.5,(x,y,front_at(y)-.29))

    for x in (3.93,12.07):
        y=14.25;z=front_at(y)-.29;rot=door_rotation(y,x)
        cube('Upper door round lock square seat '+str(x),(x-.19,y-.16,z-.09),
             (x+.19,y+.16,z+.17),'silver',rotation=rot,group='Door locks and reader')
        cube('Upper door lock inset cylinder '+str(x),(x-.12,y-.10,z-.115),
             (x+.12,y+.10,z-.078),'steel',rotation=rot,group='Door locks and reader')
        cube('Upper door lock keyway '+str(x),(x-.021,y-.079,z-.132),
             (x+.021,y+.079,z-.106),'rubber',rotation=rot,group='Door locks and reader')
    x,y=13.55,11.70;z=front_at(y)-.31;rot=door_rotation(y,x)
    cube('Right door compact service reader mounting', (x-1.13,y-.67,z-.16),
         (x+1.13,y+.73,z+.19),'black',rotation=rot,group='Door locks and reader')
    cube('Right door service reader cyan edge', (x-.96,y-.52,z-.205),
         (x+.96,y+.58,z-.11),'cyan',rotation=rot,glow=True,group='Door locks and reader')
    cube('Right door service reader black bezel', (x-.84,y-.44,z-.247),
         (x+.84,y+.50,z-.19),'rubber',rotation=rot,group='Door locks and reader')
    cube('Right door service reader small LCD', (x-.66,y-.29,z-.278),
         (x+.66,y+.37,z-.236),'steel',rotation=rot,
         north=('details',[12.125,12.125,13.875,13.875]),group='Door locks and reader')
    for x in (.49,7.56,8.31,15.38):
        for y in (9.04,14.49):
            z=front_at(y)-.269
            cube('Service door fixing '+str((x,y)),(x,y,z-.022),
                 (x+.12,y+.12,z+.07),'steel',group='Cabinet fasteners')

    # Rear mechanical details and feet complete the model from all directions.
    cube('Rear cabinet access gasket',(.20,2.23,15.08),
         (15.80,14.97,15.22),'rubber',group='Rear cabinet access')
    cube('Rear cabinet white service cover',(.40,2.44,15.19),
         (15.60,14.75,15.30),'ivory',group='Rear cabinet access')
    for y in (3.48,11.52):
        cube('Rear cooling opening '+str(y),(4.42,y,15.282),
             (11.58,y+1.82,15.365),'vent',group='Rear ventilation')
        for row in range(4):
            cube('Rear vent shallow louver '+str((y,row)),(4.56,y+.18+row*.40,15.35),
                 (11.44,y+.29+row*.40,15.406),'steel',group='Rear ventilation')
    cube('Rear low power inlet plate',(12.27,3.19,15.281),
         (14.34,4.68,15.384),'steel',group='Rear cabinet access')
    cube('Rear inset mains power socket',(12.67,3.57,15.367),
         (13.96,4.15,15.481),'rubber',group='Rear cabinet access')
    for x in (.74,15.10):
        for y in (2.82,14.33):
            cube('Rear access captive screw '+str((x,y)),(x,y,15.28),
                 (x+.14,y+.14,15.348),'steel',group='Cabinet fasteners')
    for x in (.45,15.55):
        for z in (1.38,14.08):
            cube('Levelling foot steel stem '+str((x,z)),(x-.15,.43,z-.15),
                 (x+.15,1.52,z+.15),'steel',group='Cabinet feet')
            cube('Levelling foot broad pad '+str((x,z)),(x-.41,.13,z-.43),
                 (x+.41,.48,z+.43),'silver',group='Cabinet feet')
    for x in (1.69,14.31):
        cube('Rear transport castor steel fork '+str(x),(x-.39,.73,13.25),
             (x+.39,1.34,14.58),'steel',group='Cabinet feet')
        cube('Rear transport castor '+str(x),(x-.31,.14,13.38),
             (x+.31,.90,14.46),'rubber',group='Cabinet feet')
