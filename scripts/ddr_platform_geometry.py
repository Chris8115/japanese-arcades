"""DDR SuperNOVA's two-player steel stage and rounded red safety rails.

The gameplay panels share one level top at Y2.4. Tubes are actual round meshes,
with closed ends and continuous shoulders, rather than stacks of block arcs.
Source X coordinates are drawn from the front and mirrored by the exporter.
"""
import math


def build_platform(cube, polygon, mesh):
    """Build the low stage using the cabinet generator's cube/mesh callbacks."""
    def convex(name, vertices, faces, material, group):
        # Orient convex hardware and folded plates consistently outwards.
        center=[sum(p[k] for p in vertices)/len(vertices) for k in range(3)]
        oriented=[]
        for face in faces:
            a,b,c=[vertices[i] for i in face[:3]]
            u=[b[k]-a[k] for k in range(3)]
            v=[c[k]-a[k] for k in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            middle=[sum(vertices[i][k] for i in face)/len(face) for k in range(3)]
            oriented.append(face if sum(n[k]*(middle[k]-center[k]) for k in range(3))>0 else list(reversed(face)))
        mesh(name,vertices,oriented,material,group=group)

    def plate(name, points, y0, y1, material, group):
        n=len(points)
        vertices=[[x,y0,z] for x,z in points]+[[x,y1,z] for x,z in points]
        faces=[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
        faces += [[0,i,i+1] for i in range(1,n-1)]
        faces += [[n,n+i,n+i+1] for i in range(1,n-1)]
        convex(name,vertices,faces,material,group)

    def cylinder(name,cx,cz,y0,y1,radius,material,group,sides=8):
        points=[(cx+radius*math.cos(i*math.tau/sides),
                 cz+radius*math.sin(i*math.tau/sides)) for i in range(sides)]
        plate(name,points,y0,y1,material,group)

    outline=[(-2.94,-28.72),(-1.66,-30.0),(33.66,-30.0),
             (34.94,-28.72),(34.94,-3.05),(-2.94,-3.05)]
    plate('Continuous low steel stage frame',outline,.36,2.31,'steel','Low steel dance platform')
    under=[(-2.80,-28.68),(-1.57,-29.87),(33.57,-29.87),
           (34.80,-28.68),(34.80,-3.17),(-2.80,-3.17)]
    plate('Stage recessed rubber underside',under,.16,.49,'rubber','Low steel dance platform')
    cube('Narrow black seam joining the two player stages',(15.94,2.307,-29.93),
         (16.06,2.348,-3.12),'black',group='Stage center joining hardware')
    for x0,x1 in ((15.58,15.91),(16.09,16.42)):
        cube('Steel center seam trim '+str(x0),(x0,2.306,-29.91),
             (x1,2.375,-3.13),'silver',group='Stage center joining hardware')

    # Each station is a genuine 3x3 panel arrangement, with four arrows around
    # a dark center plate and four screwed plain steel corner panels.
    # Up-face UVs reverse both axes so the arrows read from the player's side
    # after the source X mirror; the up arrow points toward the cabinet (+Z).
    arrow_uv={
        'up':[.125,.125,3.875,3.875],
        'down':[4.125,.125,7.875,3.875],
        'left':[8.125,.125,11.875,3.875],
        'right':[12.125,.125,15.875,3.875],
    }
    def top_uv(uv):return [uv[2],uv[3],uv[0],uv[1]]
    for player,cx in enumerate((7.1,24.9),1):
        for row,z in enumerate((-8.5,-14.0,-19.5)):
            for col,x in enumerate((cx-5.4,cx,cx+5.4)):
                label='Player %d panel %d-%d '%(player,row,col)
                arrow={(0,1):'up',(2,1):'down',(1,0):'left',(1,2):'right'}.get((row,col))
                cube(label+'recessed black panel joint',(x-2.68,2.265,z-2.68),
                     (x+2.68,2.355,z+2.68),'rubber',group='Eighteen screwed dance panels')
                if arrow:
                    cube(label+'screwed steel arrow surround',(x-2.635,2.349,z-2.635),
                         (x+2.635,2.377,z+2.635),'silver',group='Eight arrow pressure pads')
                    cube(label+'black arrow lens gasket',(x-2.535,2.371,z-2.535),
                         (x+2.535,2.392,z+2.535),'black',group='Eight arrow pressure pads')
                    cube(label+arrow+' illuminated arrow lens',(x-2.49,2.385,z-2.49),
                         (x+2.49,2.400,z+2.49),'pink' if arrow in ('up','down') else 'blue',
                         up=('details',top_uv(arrow_uv[arrow])),glow=('up',),
                         group='Eight arrow pressure pads')
                else:
                    uv=[4.125,4.125,7.875,7.875] if (row,col)==(1,1) else [.125,4.125,3.875,7.875]
                    cube(label+('dark center diamond plate' if (row,col)==(1,1) else 'brushed corner plate'),
                         (x-2.625,2.349,z-2.625),(x+2.625,2.400,z+2.625),
                         'charcoal' if (row,col)==(1,1) else 'silver',
                         up=('details',top_uv(uv)),group='Eighteen screwed dance panels')

        # Broad brushed strip behind the lower arrow holds the handrail feet.
        cube('Player %d rear standing strip'%player,(cx-8.73,2.304,-29.88),
             (cx+8.73,2.365,-22.33),'silver',group='Rear rail mounting strips')
        cube('Player %d rear strip inner black seam'%player,(cx-8.68,2.361,-22.45),
             (cx+8.68,2.380,-22.34),'charcoal',group='Rear rail mounting strips')
        cube('Player %d Stay Cool front fascia'%player,(cx-3.73,.55,-30.075),
             (cx+3.73,2.235,-29.975),'black',
             north=('details',[.125,8.125,7.875,9.875]),group='Printed stage fascia')

    # The outer player-facing corners have short beveled metal entry plates.
    for side,x0,x1 in (('Left',-1.36,2.83),('Right',29.17,33.36)):
        vertices=[[x0,.17,-32.0],[x1,.17,-32.0],[x1,.17,-29.70],[x0,.17,-29.70],
                  [x0,.28,-32.0],[x1,.28,-32.0],[x1,2.365,-29.70],[x0,2.365,-29.70]]
        convex(side+' small folded entry ramp',vertices,
               [[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]],
               'silver','Two small outer entry ramps')
    for side,x,angle in (('Left',-2.30,45),('Right',34.30,-45)):
        cube(side+' green foot symbol on chamfered stage corner',(x-.51,.81,-29.45),
             (x+.51,1.83,-29.36),'black',
             north=('details',[8.125,8.125,9.875,9.875]),
             rotation=('y',angle,(x,1.32,-29.405)),group='Printed stage fascia')

    # Recessed carry sockets and the central mechanical joining plate.
    for side,x0,x1 in (('Left',-2.989,-2.92),('Right',34.92,34.989)):
        for z in (-24.7,-10.2):
            cube(side+' stage side carry recess '+str(z),(x0,.78,z-.91),
                 (x1,1.52,z+.91),'rubber',group='Stage transport hardware')
    cube('Central black stage coupling plate',(14.65,.50,-30.09),
         (17.35,1.73,-29.95),'black',group='Stage center joining hardware')
    for x in (14.89,17.00):
        for y in (.70,1.40):
            cube('Stage coupling chrome fixing '+str((x,y)),(x,y,-30.12),
                 (x+.12,y+.12,-30.065),'silver',group='Stage fasteners')

    # Frame screws remain flush with the standing surface. The dense screws
    # around individual glass panels are already printed in the panel atlas.
    screws=[]
    for x in (-2.35,15.74,16.26,34.35):
        for z in (-28.9,-25.6,-22.7,-17.0,-11.6,-5.15):screws.append((x,z))
    for x in (-.10,4.85,9.35,14.2,17.8,22.65,27.15,32.1):
        screws.extend(((x,-3.70),(x,-29.26)))
    for i,(x,z) in enumerate(screws):
        cube('Flush frame screw %02d'%i,(x-.055,2.344,z-.055),
             (x+.055,2.394,z+.055),'rim_gray',group='Stage fasteners')
        cube('Flush frame screw slot %02d'%i,(x-.031,2.388,z-.012),
             (x+.031,2.397,z+.012),'black',group='Stage fasteners')

    def rail(player,cx):
        z=-27.5;radius=.40;bend=1.60;shoulder_y=18.50;top_y=20.10
        bend_steps=5
        # Centerline with tangent vectors, shared across red and black pieces.
        path=[(cx-5.8,2.48,0.,1.,False),
              (cx-5.8,17.70,0.,1.,False),
              (cx-5.8,shoulder_y,0.,1.,True)]
        for i in range(1,bend_steps+1):
            a=math.pi-i*(math.pi/2)/bend_steps
            path.append((cx-4.2+bend*math.cos(a),shoulder_y+bend*math.sin(a),
                         math.sin(a),-math.cos(a),True))
        path.append((cx+4.2,top_y,1.,0.,True))
        for i in range(1,bend_steps+1):
            a=math.pi/2-i*(math.pi/2)/bend_steps
            path.append((cx+4.2+bend*math.cos(a),shoulder_y+bend*math.sin(a),
                         math.sin(a),-math.cos(a),True))
        path.extend(((cx+5.8,17.70,0.,-1.,True),(cx+5.8,2.48,0.,-1.,False)))
        vertices=[];sides=8
        for x,y,tx,ty,black in path:
            for j in range(sides):
                theta=math.tau*j/sides
                vertices.append([x+radius*math.sin(theta)*ty,
                                 y-radius*math.sin(theta)*tx,
                                 z+radius*math.cos(theta)])
        red=[];grip=[]
        for i in range(len(path)-1):
            # The grip starts above the long straight red posts, and wraps
            # both rounded shoulders and the continuous horizontal top bar.
            target=grip if 1<=i<len(path)-2 else red
            for j in range(sides):
                k=(j+1)%sides
                target.append([i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j])
        for ring,reverse in ((0,True),(len(path)-1,False)):
            center=len(vertices);vertices.append([path[ring][0],path[ring][1],z])
            for j in range(sides):
                face=[center,ring*sides+j,ring*sides+(j+1)%sides]
                red.append(list(reversed(face)) if reverse else face)
        mesh('Player %d smooth red tubular handrail posts'%player,vertices,red,'red',
             group='Four red tubular rail posts')
        mesh('Player %d continuous black rounded hand grip'%player,vertices,grip,'rubber',
             group='Two rounded black U grips')
        for side,x in (('left',cx-5.8),('right',cx+5.8)):
            cylinder('Player %d %s rail mounting flange'%(player,side),x,z,2.32,2.63,.72,
                     'silver','Four bolted rail sockets')
            cylinder('Player %d %s rail socket collar'%(player,side),x,z,2.60,2.81,.485,
                     'steel','Four bolted rail sockets')
            for a in (45,135,225,315):
                theta=math.radians(a)
                bx=x+.59*math.cos(theta);bz=z+.59*math.sin(theta)
                cylinder('Player %d %s flange bolt %d'%(player,side,a),bx,bz,2.622,2.703,.096,
                         'rim_gray','Rail flange bolts',sides=6)

    for player,cx in enumerate((7.1,24.9),1):rail(player,cx)
