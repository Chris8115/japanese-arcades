"""MÚSECA's tapered illuminated prism chamber, lower cabinet and foot pedal."""
import math


def build_shell(cube, polygon):
    """Emit a genuinely recessed cabinet and seven separate wireframe prisms."""
    # The solid service cabinet sits behind the inset illumination chamber.
    cube('Lower cabinet continuous rear chassis', (0, 1.72, -.35),
         (16, 17.84, 14.98), 'black', group='Lower black cabinet')
    cube('Lower cabinet broad bottom plinth', (-.55, 1.20, -6.88),
         (16.55, 2.78, 15.10), 'black', group='Lower black cabinet')
    cube('Lower plinth front folded lip', (-.53, 1.22, -7.00),
         (16.53, 1.62, -6.81), 'charcoal', group='Lower black cabinet')
    cube('Lower chamber bottom black ledge', (5.94, 2.73, -6.63),
         (10.06, 3.06, -3.67), 'charcoal', group='Prism chamber structure')
    for side, x0, x1 in (('Left', -.02, 3.16), ('Right', 12.84, 16.02)):
        cube(side+' outer front structural pillar', (x0, 2.69, -6.55),
             (x1, 17.75, .04), 'black', group='Lower black cabinet')
        skin0,skin1=(x0-.11,x0+.08) if side=='Left' else (x1-.08,x1+.11)
        cube(side+' lower cabinet side skin', (skin0, 2.31, -.03),
             (skin1, 17.78, 14.99),
             'black', group='Lower black cabinet')
        cube(side+' front pillar upper shoulder', (x0-.12, 16.78, -6.79),
             (x1+.12, 17.83, 4.08), 'charcoal', group='Lower black cabinet')

    bottom, top = 3.02, 16.76

    def chamber(y):
        fraction=(y-bottom)/(top-bottom)
        return 1.50+2.85*fraction, -6.40+2.70*fraction

    # Folded side reveals taper toward the bottom. They have substantial depth,
    # while the chamber back sits another 2.5 units behind its front opening.
    # Adjacent courses are joined by the main opaque exterior-surface pass.
    count=28
    for row in range(count):
        y0=bottom+(top-bottom)*row/count
        y1=bottom+(top-bottom)*(row+1)/count
        half,front=chamber((y0+y1)/2)
        left,right=8-half,8+half
        cube('Prism chamber dark rear course %02d'%row,
             (3.10,y0,front+2.53),(12.90,y1,.06),
             'charcoal',group='Prism chamber structure')
        cube('Left sculpted tapered reveal %02d'%row,
             (3.04,y0,front-.23),(left,y1,.03),
             'black',group='Prism chamber structure')
        cube('Right sculpted tapered reveal %02d'%row,
             (right,y0,front-.23),(12.96,y1,.03),
             'black',group='Prism chamber structure')
        # Thin dark-metal edges catch light without covering the clear recess.
        cube('Left prism opening metal edge %02d'%row,
             (left-.13,y0,front-.28),(left+.02,y1,front-.07),
             'steel',group='Prism opening edges')
        cube('Right prism opening metal edge %02d'%row,
             (right-.02,y0,front-.28),(right+.13,y1,front-.07),
             'steel',group='Prism opening edges')

    cube('Prism chamber upper shadow rail', (3.55,16.77,-3.98),
         (12.45,17.78,-.04),'rubber',group='Prism chamber structure')

    def horizontal_wire(name, a, b, y, material, thickness=.09):
        """A connected thin luminous edge in X/Z, with real horizontal depth."""
        distance=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
        steps=1 if min(abs(b[0]-a[0]),abs(b[1]-a[1]))<1e-8 else max(1,math.ceil(distance/.34))
        for index in range(steps):
            p=[a[j]+(b[j]-a[j])*index/steps for j in range(2)]
            q=[a[j]+(b[j]-a[j])*(index+1)/steps for j in range(2)]
            cube(name+' segment %02d'%index,
                 (min(p[0],q[0])-thickness/2,y-thickness/2,min(p[1],q[1])-thickness/2),
                 (max(p[0],q[0])+thickness/2,y+thickness/2,max(p[1],q[1])+thickness/2),
                 material,glow=True,group='Illuminated triangular prisms')

    for tier in range(7):
        y0=3.41+tier*1.82
        y1=y0+1.44
        half,front=chamber(y0)
        width=2*half-.78
        depth=1.40+.06*tier
        zfront=front+.35
        # Alternate the triangular section orientation, creating the staggered
        # zigzag seen through the real cabinet's tapered transparent chamber.
        if tier%2:
            vertices=[(8-width/2,zfront),(8+width/2,zfront),(8,zfront+depth)]
        else:
            vertices=[(8,zfront),(8-width/2,zfront+depth),(8+width/2,zfront+depth)]
        material=('amber' if tier<4 else 'pink' if tier%2 else 'magenta')
        for level,y in (('lower',y0),('upper',y1)):
            for edge,(a,b) in enumerate(zip(vertices,vertices[1:]+vertices[:1])):
                horizontal_wire('Prism %02d %s triangle edge %d'%(tier,level,edge),a,b,y,material)
        for index,(x,z) in enumerate(vertices):
            cube('Prism %02d upright luminous edge %d'%(tier,index),
                 (x-.045,y0,z-.045),(x+.045,y1,z+.045),material,
                 glow=True,group='Illuminated triangular prisms')
        # Tiny physical clips anchor the luminous acrylic inside the chamber.
        for x,z in vertices:
            cube('Prism %02d lower steel clip %.3f'%(tier,x),
                 (x-.08,y0-.08,z-.07),(x+.08,y0-.045,z+.07),
                 'steel',group='Prism mounting clips')

    # Real right-hand service hardware sits beside, rather than over, the prism.
    cube('Right front service-panel gasket', (13.03,3.16,-6.633),
         (15.83,15.65,-6.543),'rubber',group='Right service panel')
    cube('Right front service-panel metal face', (13.16,3.28,-6.684),
         (15.70,15.52,-6.626),'charcoal',group='Right service panel')
    cube('Right lower cashbox door outline', (13.30,3.63,-6.728),
         (15.55,8.70,-6.673),'rim_gray',group='Right service panel')
    cube('Right lower cashbox door', (13.41,3.74,-6.761),
         (15.44,8.57,-6.714),'black',group='Right service panel')
    cube('Cashbox lock mounting plate', (13.70,5.32,-6.827),
         (14.24,5.92,-6.749),'silver',group='Right service hardware')
    cube('Cashbox narrow lock keyway', (13.93,5.45,-6.871),
         (14.01,5.78,-6.819),'rubber',group='Right service hardware')
    cube('Right compact service-display housing', (13.22,9.42,-6.957),
         (15.59,12.34,-6.675),'charcoal',group='Right service hardware')
    cube('Right compact service-display bezel', (13.41,9.72,-7.012),
         (15.41,12.06,-6.947),'steel',group='Right service hardware')
    cube('Right compact service display', (13.60,9.95,-7.041),
         (15.22,11.83,-7.000),'black',north=('details',[4.25,12.25,7.75,15.75]),
         glow=('north',),group='Right service hardware')
    cube('Right coin slit surround', (13.81,13.07,-6.762),
         (15.12,14.79,-6.675),'steel',group='Right service hardware')
    cube('Right narrow coin slit', (14.37,13.77,-6.812),
         (14.54,14.47,-6.751),'rubber',group='Right service hardware')
    cube('Right coin return recess', (14.08,13.20,-6.809),
         (14.87,13.51,-6.752),'black',group='Right service hardware')
    cube('Right manufacturer identification plate', (13.54,8.82,-6.716),
         (15.23,9.19,-6.681),'ivory',north=('details',[8.25,12.25,11.75,15.75]),
         group='Right service hardware')
    for x,y in ((13.29,3.42),(15.49,3.42),(13.29,15.20),(15.49,15.20)):
        cube('Right panel fixing '+str((x,y)),(x-.055,y-.055,-6.734),
             (x+.055,y+.055,-6.678),'steel',group='Cabinet fasteners')

    # The standalone foot pedal projects from the machine. Its pressure plate
    # has geometric dark grip cuts, rather than an invented luminous button.
    cube('Pedal broad bevelled black body',(4.09,.24,-11.64),
         (11.91,1.12,-6.36),'black',group='Foot pedal')
    cube('Pedal clipped front nose',(4.37,.22,-11.91),
         (11.63,.89,-11.58),'rubber',group='Foot pedal')
    cube('Pedal outer left guard',(3.91,.20,-11.39),
         (4.39,1.43,-6.29),'black',group='Foot pedal')
    cube('Pedal outer right guard',(11.61,.20,-11.39),
         (12.09,1.43,-6.29),'black',group='Foot pedal')
    cube('Pedal stainless pressure plate',(4.47,1.12,-11.33),
         (11.53,1.39,-7.13),'steel',group='Foot pedal')
    cube('Pedal front brushed plate edge',(4.51,.91,-11.39),
         (11.49,1.32,-11.30),'silver',group='Foot pedal')

    def flat_triangle(name,points,y0,y1,material):
        z0,z1=min(z for x,z in points),max(z for x,z in points)
        rows=max(1,math.ceil((z1-z0)/.18))
        for row in range(rows):
            a=z0+(z1-z0)*row/rows;b=z0+(z1-z0)*(row+1)/rows;z=(a+b)/2
            crossings=[]
            for p,q in zip(points,points[1:]+points[:1]):
                if min(p[1],q[1])<=z<max(p[1],q[1]):
                    crossings.append(p[0]+(q[0]-p[0])*(z-p[1])/(q[1]-p[1]))
            if len(crossings)==2 and max(crossings)-min(crossings)>.005:
                cube(name+' row %02d'%row,(min(crossings),y0,a),
                     (max(crossings),y1,b),material,group='Pedal geometric grips')

    for name,points in (
            ('Central long triangular grip',[(7.18,-10.99),(8.62,-8.00),(8.19,-10.02)]),
            ('Left upper diagonal grip',[(4.92,-8.56),(7.32,-7.52),(5.49,-8.09)]),
            ('Left lower diagonal grip',[(4.91,-10.56),(7.00,-10.11),(5.48,-10.92)]),
            ('Right upper diagonal grip',[(8.67,-8.40),(11.05,-7.56),(10.49,-8.13)]),
            ('Right lower diagonal grip',[(8.59,-10.43),(11.03,-10.90),(10.51,-10.19)])):
        flat_triangle(name,points,1.391,1.431,'rubber')
    for x in (4.79,11.08):
        for z in (-10.94,-7.56):
            cube('Pedal pressure-plate screw '+str((x,z)),(x-.06,1.393,z-.06),
                 (x+.06,1.449,z+.06),'silver',group='Pedal fasteners')
    cube('Pedal small warning label',(9.72,1.392,-7.90),
         (10.92,1.426,-7.38),'ivory',up=('details',[12.25,12.25,15.75,15.75]),
         group='Foot pedal')
    cube('Pedal rear hinge dark housing',(4.84,.65,-7.24),
         (11.16,1.49,-5.85),'black',group='Pedal hinge')
    hinge=('x',45,(8,1.31,-7.05))
    cube('Inclined pedal hinge brushed cover',(5.03,1.31,-7.14),
         (10.97,3.39,-6.89),'steel',rotation=hinge,group='Pedal hinge')
    cube('Inclined hinge fine transverse fold',(5.09,2.31,-7.181),
         (10.91,2.38,-7.132),'rim_gray',rotation=hinge,group='Pedal hinge')
    for x in (5.30,10.66):
        for y in (1.57,3.10):
            cube('Inclined hinge screw '+str((x,y)),(x-.05,y-.05,-7.203),
                 (x+.05,y+.05,-7.151),'silver',rotation=hinge,group='Pedal fasteners')

    for x in (.52,15.48):
        for z in (-5.90,14.11):
            cube('Castor mounting stem '+str((x,z)),(x-.14,.63,z-.14),
                 (x+.14,1.49,z+.14),'steel',group='Castors and feet')
            cube('Castor silver wheel fork '+str((x,z)),(x-.43,.31,z-.36),
                 (x+.43,.80,z+.36),'silver',group='Castors and feet')
            cube('Castor dark rubber wheel '+str((x,z)),(x-.31,.08,z-.47),
                 (x+.31,.60,z+.47),'rubber',group='Castors and feet')
    for x in (1.53,14.47):
        cube('Front leveling foot '+str(x),(x-.36,.03,-6.57),
             (x+.36,.24,-5.88),'steel',group='Castors and feet')

    cube('Rear lower service-panel gasket',(.63,2.45,15.02),
         (15.37,16.97,15.12),'rubber',group='Rear service panels')
    cube('Rear lower charcoal service panel',(.81,2.63,15.121),
         (15.19,16.79,15.22),'charcoal',group='Rear service panels')
    for y in (4.21,12.49):
        cube('Rear cooling grille '+str(y),(4.86,y,15.23),
             (11.14,y+2.64,15.30),'vent',group='Rear ventilation')
    for side,x0,x1 in (('Left',-.16,-.08),('Right',16.08,16.16)):
        cube(side+' lower cabinet side vent',(x0,5.26,10.33),
             (x1,10.34,13.97),'vent',group='Rear ventilation')
        cube(side+' side transport handle',(x0-.02,13.20,10.89),
             (x1+.02,14.02,13.41),'rubber',group='Rear service panels')
    cube('Rear power inlet plate',(12.00,3.33,15.235),
         (14.31,4.98,15.319),'steel',group='Rear service panels')
    cube('Rear power socket',(12.54,3.78,15.325),
         (13.77,4.57,15.411),'rubber',group='Rear service panels')
    for x in (1.11,14.73):
        for y in (2.98,16.36):
            cube('Rear lower panel screw '+str((x,y)),(x,y,15.231),
                 (x+.14,y+.14,15.281),'steel',group='Cabinet fasteners')
