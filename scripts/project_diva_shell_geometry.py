"""Project DIVA Arcade Future Tone's angular white lower service cabinet.

The supplied photographs show a tall, mostly plain base: broad black doors,
white folded sides with black side insets, and a silver toeplate. All detailing
here is solid cuboid geometry, with adjacent surfaces left to the exporter.
"""
import math


def build_shell(cube, polygon):
    """Emit the lower housing below the sloping display and four-button deck."""
    cube('Base continuous black structural chassis', (1.04, 1.03, -.20),
         (14.96, 16.50, 14.80), 'black', group='Lower chassis')
    cube('Base full-width bottom folded pan', (-.08, .87, -1.23),
         (16.08, 1.63, 14.84), 'ivory', group='Lower chassis')
    cube('Base rear dark bottom seam', (.28, .71, 12.90),
         (15.72, 1.05, 14.93), 'rubber', group='Lower chassis')

    # Each side is an actual thick white wall. The small forward turn of its
    # top edge supports the control overhang and matches the reference profile.
    for side, x0, x1 in (('Left', -.10, 1.19), ('Right', 14.81, 16.10)):
        cube(side+' lower white cabinet wall', (x0, 1.13, -.37),
             (x1, 11.91, 14.94), 'white', group='White base sidewalls')
        for row in range(10):
            y0 = 11.91 + row * .459
            y1 = y0 + .459
            front = -.37 - (row + 1) * .112
            cube(side+' upper forward sidewall course %02d'%row,
                 (x0, y0, front), (x1, y1, 14.94), 'white',
                 group='White base sidewalls')
        # A narrow, slightly lighter front return gives a folded sheet edge.
        xa, xb = (x0 + .19, x1) if side == 'Left' else (x0, x1 - .19)
        cube(side+' white front door return', (xa, 1.59, -.50),
             (xb, 15.37, -.26), 'ivory', group='White base sidewalls')
        cube(side+' upper inner supporting rail',
             (x0+.12, 15.17, -1.48), (x1-.12, 16.50, 3.82),
             'ivory', group='White base sidewalls')

    # The lower black face is deliberately broad and quiet, as in the real
    # machine: a main access door and a narrow divided service column at right.
    cube('Front cabinet dark continuous door surround', (1.13, 1.88, -.456),
         (14.87, 16.12, -.155), 'rubber', group='Front cabinet doors')
    cube('Front large black access door', (1.40, 2.05, -.525),
         (10.40, 15.70, -.432), 'black', group='Front cabinet doors')
    cube('Right upper coin access door', (10.57, 9.43, -.535),
         (14.59, 15.70, -.431), 'black', group='Front cabinet doors')
    cube('Right lower cash collection door', (10.57, 2.05, -.535),
         (14.59, 9.24, -.431), 'black', group='Front cabinet doors')
    cube('Main access door fine right folded lip', (10.29, 2.11, -.557),
         (10.41, 15.63, -.510), 'charcoal', group='Front cabinet doors')
    cube('Main door lower folded edge', (1.43, 2.04, -.558),
         (10.34, 2.15, -.510), 'charcoal', group='Front cabinet doors')
    cube('Service door separating horizontal seam', (10.57, 9.27, -.48),
         (14.59, 9.39, -.37), 'rubber', group='Front cabinet doors')

    def front_lock(name, x, y, size=.24):
        # Small stepped octagonal chrome lock cylinder, with a real keyway.
        cube(name+' square chrome seat', (x-size*.78, y-size, -.618),
             (x+size*.78, y+size, -.519), 'silver', group='Locks and coin hardware')
        cube(name+' chrome side facets', (x-size, y-size*.63, -.620),
             (x+size, y+size*.63, -.520), 'silver', group='Locks and coin hardware')
        cube(name+' inset cylinder face', (x-size*.65, y-size*.62, -.641),
             (x+size*.65, y+size*.62, -.612), 'steel', group='Locks and coin hardware')
        cube(name+' thin vertical keyway', (x-.024, y-size*.43, -.660),
             (x+.024, y+size*.43, -.634), 'rubber', group='Locks and coin hardware')

    front_lock('Main service access lock', 8.97, 14.46, .185)
    front_lock('Upper coin door left lock', 11.17, 13.28, .19)
    front_lock('Upper coin door right lock', 13.88, 14.36, .14)
    front_lock('Lower cashbox door lock', 11.16, 6.27, .185)
    cube('Coin return brushed frame', (11.30, 10.49, -.661),
         (12.69, 11.44, -.531), 'steel', group='Locks and coin hardware')
    cube('Coin return dark opening', (11.44, 10.60, -.692),
         (12.55, 11.30, -.650), 'rubber', group='Locks and coin hardware')
    cube('Coin return tilted silver inner catch', (11.47, 10.62, -.722),
         (12.51, 10.99, -.682), 'silver', group='Locks and coin hardware')
    cube('Coin return lower retaining lip', (11.39, 10.48, -.741),
         (12.62, 10.64, -.650), 'steel', group='Locks and coin hardware')

    # A shallow black shelf sits above a wide brushed-metal bevel at foot level.
    # Ten joined courses form the angled toeplate without rotated overlap faces.
    cube('Front toeplate dark upper ledge', (1.07, 1.20, -2.28),
         (14.93, 1.74, -.33), 'charcoal', group='Silver toeplate')
    for row in range(10):
        y0 = .66 + row*.105
        front = -2.43 + row*.116
        cube('Toeplate broad silver bevel course %02d'%row,
             (.22, y0, front), (15.78, y0+.105, -1.08),
             'silver', group='Silver toeplate')
    cube('Toeplate dark bottom folded seam', (.25, .55, -2.425),
         (15.75, .71, -1.70), 'steel', group='Silver toeplate')
    for side, x0, x1 in (('Left', -.05, .45), ('Right', 15.55, 16.05)):
        cube(side+' toeplate folded white end cap', (x0, .68, -2.17),
             (x1, 1.47, -.31), 'ivory', group='Silver toeplate')
        for row in range(6):
            y0=.66+row*.15
            cube(side+' toeplate end chamfer course %02d'%row,
                 (x0, y0, -2.39+row*.17), (x1, y0+.15, -1.30),
                 'ivory', group='Silver toeplate')

    def side_panel(name, points, x0, x1, material, step=.40):
        """Fill a cabinet-side Y/Z polygon with joined, shallow solid courses."""
        ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
        count = max(1, math.ceil((ymax-ymin)/step))
        for row in range(count):
            y0=ymin+(ymax-ymin)*row/count
            y1=ymin+(ymax-ymin)*(row+1)/count
            y=(y0+y1)/2
            crossings=[]
            for a,b in zip(points, points[1:]+points[:1]):
                if min(a[1],b[1]) <= y < max(a[1],b[1]):
                    crossings.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
            crossings.sort()
            for edge in range(0,len(crossings)-1,2):
                cube(name+' course %02d-%d'%(row,edge),
                     (x0,y0,crossings[edge]),(x1,y1,crossings[edge+1]),
                     material, group='Angular side insets')

    # Reference side print: one large dark angular inset, with a broad warm-grey
    # border that tapers into the plain white lower wall. No invented neon here.
    side_outline = [(2.46,16.50),(14.31,16.50),(14.31,4.10),
                    (9.08,3.34),(6.33,6.39),(2.46,9.51)]
    side_black = [(3.02,16.50),(13.93,16.50),(13.93,4.57),
                  (9.22,3.94),(6.75,6.79),(3.02,9.85)]
    for side, border_x, black_x in (
            ('Left',(-.16,-.071),(-.205,-.145)),
            ('Right',(16.071,16.16),(16.145,16.205))):
        side_panel(side+' grey angular side-panel surround', side_outline,
                   *border_x,'steel',step=.45)
        side_panel(side+' black angular side-panel inset', side_black,
                   *black_x,'black',step=.45)
        x0,x1 = (-.253,-.193) if side=='Left' else (16.193,16.253)
        cube(side+' SEGA side badge mounting face', (x0,10.08,8.02),
             (x1,11.10,11.11),'black', group='Side labels')
        cube(side+' small silver serial plate', (x0,10.16,12.12),
             (x1,10.72,13.47),'silver', group='Side labels')
        # Recessed white side carrying grip near the front edge of each wall.
        hx0,hx1 = (-.183,-.086) if side=='Left' else (16.086,16.183)
        cube(side+' transport handle steel recess', (hx0,12.69,.50),
             (hx1,13.32,2.50),'rim_gray',group='Transport handles')
        hx0,hx1 = (-.224,-.168) if side=='Left' else (16.168,16.224)
        cube(side+' transport handle dark inset', (hx0,12.82,.69),
             (hx1,13.16,2.31),'steel',group='Transport handles')
        hx0,hx1 = (-.246,-.198) if side=='Left' else (16.198,16.246)
        cube(side+' transport handle lower white finger lip', (hx0,12.79,.64),
             (hx1,12.92,2.36),'white',group='Transport handles')

    # Rear access is restrained industrial hardware: dark removable plate,
    # recessed intake grilles, horizontal slots, mains socket and screws.
    cube('Rear service door black gasket', (.83,2.18,14.780),
         (15.17,15.57,15.061),'rubber',group='Rear service panels')
    cube('Rear removable charcoal cover', (1.02,2.36,15.040),
         (14.98,15.38,15.144),'charcoal',group='Rear service panels')
    for y in (4.21,11.19):
        cube('Rear cooling grille surround '+str(y), (4.29,y,15.134),
             (11.71,y+2.15,15.217),'steel',group='Rear ventilation')
        cube('Rear cooling grille shadow '+str(y), (4.44,y+.14,15.210),
             (11.56,y+2.01,15.252),'rubber',group='Rear ventilation')
        for row in range(5):
            cube('Rear cooling louvre '+str((y,row)),(4.51,y+.24+row*.355,15.242),
                 (11.49,y+.35+row*.355,15.310),'charcoal',group='Rear ventilation')
    cube('Rear IEC mains plate',(12.42,3.05,15.134),
         (14.24,4.49,15.264),'steel',group='Rear service panels')
    cube('Rear IEC mains socket',(12.78,3.33,15.253),
         (13.84,3.95,15.365),'rubber',group='Rear service panels')
    cube('Rear mains switch',(12.92,4.10,15.255),
         (13.67,4.31,15.340),'black',group='Rear service panels')
    cube('Rear small identification label',(1.89,3.18,15.134),
         (3.41,3.85,15.206),'ivory',group='Rear service panels')
    for x in (1.35,14.51):
        for y in (2.70,8.50,14.96):
            cube('Rear captive screw '+str((x,y)),(x-.06,y-.06,15.140),
                 (x+.06,y+.06,15.197),'silver',group='Cabinet fasteners')
    for side, x0, x1 in (('Left',-.145,-.085),('Right',16.085,16.145)):
        for y,z in ((2.07,1.18),(2.07,13.88),(14.79,.35),(14.79,14.36)):
            cube(side+' sidewall fixing '+str((y,z)),(x0,y-.045,z-.045),
                 (x1,y+.045,z+.045),'silver',group='Cabinet fasteners')

    # Small feet are visible under all four corners; the front pair sit behind
    # the toeplate, leaving its full brushed face uninterrupted.
    for x in (.98,15.02):
        for z in (.53,13.78):
            cube('Levelling-foot threaded stem '+str((x,z)),(x-.12,.23,z-.12),
                 (x+.12,1.16,z+.12),'steel',group='Feet and castors')
            cube('Levelling-foot octagonal pad core '+str((x,z)),(x-.35,.055,z-.45),
                 (x+.35,.265,z+.45),'steel',group='Feet and castors')
            cube('Levelling-foot octagonal pad sides '+str((x,z)),(x-.45,.055,z-.32),
                 (x+.45,.265,z+.32),'steel',group='Feet and castors')
    for x in (2.05,13.95):
        cube('Rear castor steel mounting fork '+str(x),(x-.36,.24,13.28),
             (x+.36,.96,14.15),'silver',group='Feet and castors')
        cube('Rear castor small rubber wheel '+str(x),(x-.29,.06,13.10),
             (x+.29,.66,14.29),'rubber',group='Feet and castors')
