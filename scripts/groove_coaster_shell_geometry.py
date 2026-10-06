"""Groove Coaster's open footwell, booster pedestals and rear monitor support.

The controls and illuminated outer acrylic belong to the main generator.  This
module supplies the black folded-metal structure visible through and below them.
"""
import math


def build_shell(cube, polygon):
    """Emit the reference cabinet's metal base and two separate front supports."""
    # A shallow metal platform joins the front supports to the separate tower.
    # No wall closes the central space between the player's legs and the screen.
    cube('Platform black structural tray', (-3.84, .57, -9.35),
         (19.84, 1.68, 16.62), 'black', group='Foot platform')
    cube('Platform brushed stainless tread', (-3.70, 1.69, -9.16),
         (19.70, 1.98, 10.20), 'silver', group='Foot platform')
    cube('Platform rear dark tread', (-3.68, 1.70, 10.18),
         (19.68, 1.96, 16.49), 'charcoal', group='Foot platform')
    cube('Full width folded stainless front sill', (-3.89, .89, -9.48),
         (19.89, 1.98, -9.15), 'silver', group='Foot platform')
    cube('Front sill lower shadow', (-3.83, .65, -9.39),
         (19.83, .89, -9.14), 'rubber', group='Foot platform')
    for side, x in (('Left', -3.89), ('Right', 19.65)):
        cube(side+' platform folded side edge', (x, .83, -9.13),
             (x+.24, 1.97, 16.62), 'steel', group='Foot platform')
    # The front threshold is smooth; a few seams and fasteners establish its
    # folded construction without turning the footplate into patterned noise.
    for x in (-2.96, 18.75):
        cube('Front threshold screw '+str(x), (x-.065, 1.43, -9.515),
             (x+.065, 1.57, -9.47), 'steel', group='Platform fasteners')
    for x in (2.09, 13.76):
        cube('Footwell side tread seam '+str(x), (x, 1.983, -8.82),
             (x+.075, 2.005, 8.64), 'rim_gray', group='Foot platform')
    cube('Footwell rear tread seam', (2.14, 1.983, 8.50),
         (13.86, 2.005, 8.58), 'rim_gray', group='Foot platform')

    for side, x in (('Left', -2.82), ('Right', 18.82)):
        for label, z in (('front', -8.31), ('rear', 15.41)):
            name=side+' '+label+' adjustable foot'
            cube(name+' rubber sole', (x-.56, 0, z-.45),
                 (x+.56, .17, z+.45), 'rubber', group='Adjustable feet')
            cube(name+' broad metal pad', (x-.67, .17, z-.43),
                 (x+.67, .34, z+.43), 'steel', group='Adjustable feet')
            cube(name+' pad crossbar', (x-.43, .17, z-.67),
                 (x+.43, .34, z+.67), 'steel', group='Adjustable feet')
            cube(name+' upper pad shoulder', (x-.39, .34, z-.39),
                 (x+.39, .55, z+.39), 'silver', group='Adjustable feet')
            cube(name+' threaded spindle', (x-.13, .49, z-.13),
                 (x+.13, 1.15, z+.13), 'steel', group='Adjustable feet')

    # The two lower columns are narrow, leaving the broad steel floor visible.
    for side, x0, x1 in (('Left', -3.46, 1.55), ('Right', 14.45, 19.46)):
        cube(side+' pedestal shadow foot', (x0-.03, 1.98, -8.78),
             (x1+.03, 2.32, 2.63), 'rubber', group='Front pedestals')
        cube(side+' black pedestal body', (x0, 2.28, -8.58),
             (x1, 11.82, 2.47), 'black', group='Front pedestals')
        cube(side+' recessed front service door', (x0+.20, 2.61, -8.68),
             (x1-.20, 11.44, -8.57), 'charcoal', group='Pedestal access panels')
        cube(side+' front service door upper seam', (x0+.16, 11.45, -8.69),
             (x1-.16, 11.53, -8.54), 'rubber', group='Pedestal access panels')
        cube(side+' pedestal rear return', (x0+.18, 2.39, 2.43),
             (x1-.18, 11.58, 2.61), 'charcoal', group='Front pedestals')
        # Small service fasteners remain confined to the actual access door.
        for x in (x0+.36, x1-.36):
            cube(side+' upper door fixing '+str(x), (x-.06, 10.99, -8.727),
                 (x+.06, 11.11, -8.673), 'steel', group='Pedestal fasteners')
        inner=x1-.07 if side=='Left' else x0-.07
        cube(side+' inward service seam', (inner, 3.13, -7.76),
             (inner+.14, 10.43, 1.87), 'charcoal', group='Pedestal access panels')

    # Wide folded pods project inward beneath the boosters. Their upper face is
    # a smooth native 45-degree panel, backed by overlapping structural courses.
    # The front skin's X end faces are offset from the axis-aligned courses to
    # avoid the rotated-versus-unrotated coplanar seams seen on earlier cabinets.
    for side, x0, x1, cx in (('Left', -3.24, 3.30, 1.0),
                             ('Right', 12.70, 19.24, 15.0)):
        group='Sculpted booster supports'
        cube(side+' pod lower projecting nose', (x0+.05, 11.70, -9.04),
             (x1-.05, 12.77, 2.59), 'charcoal', group=group)
        for row in range(10):
            y0=12.72+row*.50
            cube(side+' angled pod structural course %02d'%row,
                 (x0, y0, -8.62+(y0-12.72)),
                 (x1, y0+.50, 2.49), 'black', group=group)
        pivot=(cx, 12.72, -9.03)
        slant=('x', 45, pivot)
        cube(side+' smooth angled pod face', (x0-.035, 12.72, -9.14),
             (x1+.035, 19.83, -8.40), 'black', rotation=slant, group=group)
        cube(side+' rear shoulder folded cap', (x0+.06, 17.35, -4.08),
             (x1-.06, 17.79, 2.51), 'charcoal', group=group)
        shelf_left, shelf_right = ((-2.15, 4.70) if side=='Left'
                                   else (11.30, 18.15))
        cube(side+' booster mounting shelf', (shelf_left, 17.08, -6.46),
             (shelf_right, 17.57, 1.82), 'black', group=group)

        if side=='Left':
            cube('Left sloped inset under booster', (-2.63, 13.11, -9.22),
                 (2.32, 18.81, -9.125), 'charcoal', rotation=slant,
                 group='Left sloping ventilation')
            for i in range(7):
                x=-.79+i*.39
                cube('Left pod fine silver ventilation stripe %02d'%i,
                     (x, 13.23, -9.252), (x+.10, 18.63, -9.207),
                     'steel', rotation=slant, group='Left sloping ventilation')
            cube('Left pod small service label', (-2.41, 13.47, -9.27),
                 (-1.18, 13.71, -9.219), 'ivory', rotation=slant,
                 group='Left sloping ventilation')
        else:
            # The real right support carries a compact angled card reader.
            # It is below the booster and leaves the luminous control ring clear.
            cube('Right angled reader outer shell', (14.09, 13.55, -9.46),
                 (18.71, 17.70, -9.15), 'charcoal', rotation=slant,
                 group='Angled card reader')
            cube('Right reader brushed faceplate', (14.28, 13.75, -9.51),
                 (18.53, 17.49, -9.451), 'steel', rotation=slant,
                 group='Angled card reader')
            cube('Right reader dark display bezel', (14.56, 14.60, -9.61),
                 (17.11, 16.94, -9.504), 'rubber', rotation=slant,
                 group='Angled card reader')
            cube('Right reader lit pale display', (14.78, 14.82, -9.637),
                 (16.89, 16.73, -9.596), 'ivory', rotation=slant,
                 north=('details', [.25, .25, 3.75, 3.75]),
                 glow=('north',), group='Angled card reader')
            cube('Right reader narrow card target', (17.47, 14.74, -9.61),
                 (18.23, 16.75, -9.503), 'rim_gray', rotation=slant,
                 group='Angled card reader')
            cube('Right reader lower instruction strip', (14.67, 14.02, -9.54),
                 (17.84, 14.30, -9.505), 'ivory', rotation=slant,
                 group='Angled card reader')
            for x in (14.45, 18.35):
                cube('Right card reader fixing '+str(x), (x-.065, 17.16, -9.56),
                     (x+.065, 17.29, -9.502), 'black', rotation=slant,
                     group='Angled card reader')

    # Coin and cashbox hardware occupy only the player-right front column.
    cube('Right pedestal metal coin plate', (16.05, 6.29, -8.84),
         (18.44, 10.15, -8.673), 'silver', group='Coin mechanism')
    cube('Coin slot dark vertical opening', (16.72, 8.83, -8.904),
         (16.91, 9.79, -8.837), 'rubber', group='Coin mechanism')
    cube('Coin slot raised edge', (16.62, 8.78, -8.947),
         (16.75, 9.85, -8.83), 'steel', group='Coin mechanism')
    cube('Coin return lever', (17.57, 7.05, -9.00),
         (18.12, 7.87, -8.82), 'steel', group='Coin mechanism')
    cube('Coin return lower dark recess', (16.54, 6.50, -8.91),
         (17.81, 6.96, -8.835), 'black', group='Coin mechanism')
    cube('Coin mechanism blue indicator', (17.74, 8.06, -8.95),
         (18.03, 8.33, -8.829), 'blue', glow=('north',), group='Coin mechanism')
    cube('Right cashbox lock mounting plate', (15.26, 8.01, -8.82),
         (15.76, 8.61, -8.66), 'steel', group='Coin mechanism')
    cube('Right cashbox lock keyway', (15.46, 8.15, -8.867),
         (15.54, 8.46, -8.814), 'rubber', group='Coin mechanism')
    for y in (4.65, 5.63):
        cube('Cashbox small identification label '+str(y), (16.02, y, -8.736),
             (17.64, y+.30, -8.679), 'ivory', group='Pedestal access panels')

    # Independent rear cabinet carries the tall portrait monitor. Its front is
    # intentionally far behind the booster columns, preserving the open trough.
    cube('Rear monitor column shadow foot', (-.01, 1.98, 9.94),
         (16.01, 2.42, 16.59), 'rubber', group='Rear monitor support')
    cube('Rear monitor support main enclosure', (.20, 2.30, 10.03),
         (15.80, 19.43, 16.48), 'black', group='Rear monitor support')
    cube('Rear column front service panel', (.47, 2.68, 9.91),
         (15.53, 18.75, 10.08), 'charcoal', group='Rear monitor support')
    cube('Rear support upper monitor saddle', (.07, 19.19, 9.64),
         (15.93, 21.02, 16.41), 'black', group='Rear monitor support')
    cube('Monitor saddle shallow front lip', (.40, 19.02, 9.52),
         (15.60, 19.45, 10.20), 'charcoal', group='Rear monitor support')
    cube('Footwell rear low cross brace', (1.66, 2.03, 7.64),
         (14.34, 3.37, 9.94), 'black', group='Footwell rear brace')
    cube('Rear brace stainless top strip', (2.00, 3.39, 7.84),
         (14.00, 3.50, 9.44), 'steel', group='Footwell rear brace')

    def octagon(cx, cy, radius):
        return [(cx+radius*math.cos(math.pi/8+i*math.pi/4),
                 cy+radius*math.sin(math.pi/8+i*math.pi/4)) for i in range(8)]

    polygon('Rear footwell woofer outer surround', octagon(6.14, 10.43, 2.57),
            9.73, 9.94, 'black', group='Recessed lower speaker', step=.25)
    polygon('Rear footwell dark woofer grille', octagon(6.14, 10.43, 2.27),
            9.68, 9.76, 'black_mesh', group='Recessed lower speaker', step=.25)
    for x in (.95, 15.05):
        cube('Rear column front panel lock '+str(x), (x-.13, 17.11, 9.84),
             (x+.13, 17.55, 9.921), 'steel', group='Rear column hardware')

    # Accessible service back, understated vents, socket and fixing points.
    cube('Rear support access-panel gasket', (.79, 2.85, 16.49),
         (15.21, 18.61, 16.57), 'rubber', group='Rear service panels')
    cube('Rear support access-panel face', (.95, 3.03, 16.565),
         (15.05, 18.43, 16.67), 'charcoal', group='Rear service panels')
    for y in (5.31, 14.05):
        cube('Rear column cooling grille '+str(y), (4.64, y, 16.68),
             (11.36, y+2.54, 16.75), 'vent', group='Rear cooling')
    for side, x0, x1 in (('Left', .06, .23), ('Right', 15.77, 15.94)):
        cube(side+' rear column side ventilation', (x0, 6.09, 12.40),
             (x1, 10.92, 15.85), 'vent', group='Rear cooling')
        cube(side+' rear column side transport handle', (x0-.025, 15.80, 13.21),
             (x1+.025, 16.63, 15.13), 'rubber', group='Rear column hardware')
    cube('Rear mains inlet metal plate', (12.08, 3.87, 16.681),
         (14.29, 5.31, 16.773), 'steel', group='Rear column hardware')
    cube('Rear mains socket', (12.56, 4.20, 16.78),
         (13.65, 4.94, 16.87), 'rubber', group='Rear column hardware')
    for x in (1.23, 14.64):
        for y in (3.40, 18.04):
            cube('Rear access-panel fixing '+str((x,y)), (x, y, 16.679),
                 (x+.14, y+.14, 16.731), 'steel', group='Rear column hardware')
