"""WACCA Reverse pedestal and continuous housing below/behind the touch bowl.

The supplied photographs show a plain black maintenance door, broad patterned
ivory cheeks, and a shallow sloping reader/coin fascia. The bowl is the input
surface: this module deliberately adds no rhythm buttons or encoder knobs.
"""

import math


def build_shell(cube, polygon):
    """Build the reference-based body; the main generator supplies bowl/header."""
    # Broad enclosed pedestal. Its white side panels and tapered front cheeks
    # surround an uninterrupted dark door, unlike an open arcade footwell.
    cube('Pedestal structural body', (-.58, .65, 4.32), (16.58, 17.48, 15.60),
         'black', group='Pedestal structure')
    cube('Black pedestal bottom plinth', (-.72, .23, 4.15), (16.72, 1.00, 15.70),
         'rubber', group='Plinth and feet')
    cube('Inset front service-door gasket', (.45, 1.04, 4.20), (15.55, 13.65, 4.35),
         'rubber', group='Front maintenance door')
    cube('Plain black front service door', (.68, 1.27, 4.10), (15.32, 13.46, 4.25),
         'charcoal', group='Front maintenance door')
    cube('Service door upper horizontal seam', (.54, 13.52, 4.065),
         (15.46, 13.67, 4.25), 'rubber', group='Front maintenance door')
    cube('Service door lower folded edge', (2.70, 1.13, 4.075),
         (13.30, 1.33, 4.21), 'black', group='Front maintenance door')

    left_cheek = [(-.76, .62), (3.47, .62), (2.61, 3.28), (1.53, 7.65),
                  (.75, 11.54), (.64, 13.48), (-.76, 13.97)]
    left_upper = [(-.78, 14.10), (.71, 13.65), (1.15, 14.75),
                  (.93, 16.67), (-.78, 17.27)]
    for side, mirror in (('Left', False), ('Right', True)):
        reflected = lambda points: [(16-x if mirror else x, y) for x, y in points]
        polygon(side+' patterned lower front cheek', reflected(left_cheek), 3.98, 4.52,
                'ivory', group='Ivory pedestal cheeks')
        polygon(side+' patterned upper front cheek', reflected(left_upper), 3.92, 4.58,
                'ivory', group='Ivory pedestal cheeks')
        a, b = (16.10, 16.79) if mirror else (-.79, -.10)
        cube(side+' full-height lower side skin', (a, .65, 4.35), (b, 16.18, 15.63),
             'ivory', group='Ivory pedestal cheeks')
        # Real side seams continue around the pedestal below the fascia.
        cube(side+' horizontal body seam', (a-.015, 12.72, 4.42),
             (b+.015, 12.84, 15.55), 'black', group='Side cabinet details')
        cube(side+' lower rear bumper', (a, .58, 13.68), (b, 1.06, 15.60),
             'rubber', group='Plinth and feet')
        for y, z in ((1.18, 14.82), (11.98, 14.82), (15.15, 14.82)):
            outer_a, outer_b = (16.80, 16.85) if mirror else (-.85, -.80)
            cube(side+' side fixing '+str(y), (outer_a, y, z),
                 (outer_b, y+.16, z+.16), 'steel', group='Side cabinet details')
        x = 15.44 if mirror else .38
        cube(side+' front lower fixing', (x-.09, .91, 3.92),
             (x+.09, 1.09, 4.055), 'steel', group='Cabinet hardware')
    # Small lock on the right ivory return, photographed near the lower door.
    cube('Front service lock square escutcheon', (14.72, 5.03, 3.87),
         (15.22, 5.55, 4.035), 'silver', group='Cabinet hardware')
    cube('Front service lock centre', (14.86, 5.17, 3.825),
         (15.08, 5.40, 3.925), 'steel', group='Cabinet hardware')
    cube('Front service lock keyway', (14.951, 5.195, 3.80),
         (15.000, 5.363, 3.845), 'black', group='Cabinet hardware')
    for y in (7.96, 11.55):
        cube('Front door discreet hinge '+str(y), (14.28, y, 4.025),
             (14.65, y+.20, 4.17), 'black', group='Cabinet hardware')
    # A low, dark ventilation insert blends into the bottom of the service door.
    cube('Low front air intake surround', (5.53, 1.57, 4.025),
         (10.47, 2.47, 4.145), 'black', group='Cabinet ventilation')
    cube('Low front air intake mesh', (5.72, 1.73, 3.992),
         (10.28, 2.30, 4.06), 'vent', group='Cabinet ventilation')
    for x in (.34, 14.94):
        for z in (4.92, 13.97):
            cube('Adjustable metal foot '+str((x, z)), (x+.15, .09, z+.15),
                 (x+.57, .64, z+.57), 'steel', group='Plinth and feet')
            cube('Dark levelling foot '+str((x, z)), (x, 0, z),
                 (x+.73, .22, z+.73), 'rubber', group='Plinth and feet')

    # The forward control fascia has a substantial enclosure behind it. Thin
    # courses close the slope to the rear body without filling the touch bowl.
    console_pivot = (8, 14.27, .65)
    console_tilt = ('x', 22.5, console_pivot)
    cube('Front console black lower valance', (-.63, 12.91, 1.43),
         (16.63, 14.12, 7.17), 'black', group='Control fascia enclosure')
    cube('Console lower front folded lip', (.02, 13.62, .58),
         (15.98, 14.07, 1.69), 'black', group='Control fascia enclosure')
    for row in range(14):
        y0 = 14.0+row*.28
        y1 = y0+.28
        front = .93+math.tan(math.radians(22.5))*(y0-14.27)+.63
        cube('Solid inclined console course %02d'%row, (-.38, y0, front),
             (16.38, y1, 8.22), 'black', group='Control fascia enclosure')
    # Broad pale shoulders rise from the side of the reader panel toward the
    # back of the bowl, matching the wedge visible in the supplied side photo.
    for side, mirror in (('Left', False), ('Right', True)):
        a, b = (15.79, 16.86) if mirror else (-.86, .21)
        for row in range(14):
            y0 = 14.10+row*.46
            y1 = y0+.46
            front = 1.22+(y0-14.10)*.77
            cube(side+' rising console side course %02d'%row, (a, y0, front),
                 (b, y1, 11.87), 'ivory', group='Inclined ivory shoulders')
        outer_a, outer_b = (16.865, 16.90) if mirror else (-.90, -.865)
        # A short black seam separates the pale inclined cover from the tower.
        for row in range(7):
            y0 = 16.94+row*.46
            front = 1.22+(y0-14.10)*.77
            cube(side+' console rear seam %02d'%row, (outer_a, y0, front+.14),
                 (outer_b, y0+.46, front+.30), 'black', group='Inclined ivory shoulders')
        for y, z in ((15.04, 3.31), (18.62, 7.49)):
            cube(side+' shoulder screw '+str(y), (outer_a, y, z),
                 (outer_b, y+.16, z+.16), 'steel', group='Cabinet hardware')

    fascia_outline = [(-.32, 14.22), (.54, 13.91), (15.46, 13.91),
                       (16.32, 14.22), (16.10, 17.74), (14.62, 18.11),
                       (1.38, 18.11), (-.10, 17.74)]
    fascia_inset = [(.10, 14.40), (.75, 14.16), (15.25, 14.16),
                     (15.90, 14.40), (15.75, 17.47), (14.55, 17.77),
                     (1.45, 17.77), (.25, 17.47)]
    polygon('Control fascia folded silver edge', fascia_outline, .60, 1.21,
            'silver', rotation=console_tilt, group='Printed control fascia')
    polygon('Control fascia magenta edge', fascia_inset, .55, .71,
            'magenta', rotation=console_tilt, glow=('north',), group='Printed control fascia')
    # Keep the flat printed sheet at its true 512:96 ratio. The artwork carries
    # card-reader, headphone, WACCA and coin labels; only real hardware is raised.
    cube('WACCA reader and coin printed panel', (.68, 14.52, .49),
         (15.32, 17.265, .61), 'black', north=('details', [0, 0, 16, 6]),
         rotation=console_tilt, glow=('north',), group='Printed control fascia')
    cube('Control fascia lower pale separator', (.91, 14.32, .515),
         (15.09, 14.385, .59), 'silver', rotation=console_tilt,
         group='Printed control fascia')
    for x, y in ((.47, 14.60), (15.37, 14.60), (.51, 17.31), (15.32, 17.31)):
        cube('Control fascia countersunk fixing '+str((x, y)), (x, y, .42),
             (x+.16, y+.16, .61), 'steel', rotation=console_tilt,
             group='Control fascia hardware')
    cube('Coin slot metal surround', (13.11, 15.64, .385),
         (13.69, 16.83, .58), 'silver', rotation=console_tilt,
         group='Control fascia hardware')
    cube('Coin slot recessed opening', (13.297, 15.83, .34),
         (13.501, 16.65, .43), 'rubber', rotation=console_tilt,
         group='Control fascia hardware')
    cube('Coin slot inner steel edge', (13.335, 15.88, .325),
         (13.371, 16.60, .365), 'steel', rotation=console_tilt,
         group='Control fascia hardware')
    cube('Headphone jack metal bezel', (8.105, 15.62, .355),
         (8.495, 16.01, .555), 'silver', rotation=console_tilt,
         group='Control fascia hardware')
    cube('Headphone jack dark centre', (8.213, 15.73, .30),
         (8.387, 15.90, .38), 'rubber', rotation=console_tilt,
         group='Control fascia hardware')

    # Continuous monitor carrier, deep enough to house the recessed circular LCD.
    # Its front stays behind z=8, leaving the bowl's 1.2..7.0 depth unobstructed.
    cube('Deep monitor tower', (-.49, 17.46, 8.07), (16.49, 38.67, 15.39),
         'black', group='Rear monitor housing')
    cube('Monitor housing rounded-top centre', (1.14, 38.65, 8.83),
         (14.86, 39.15, 15.29), 'black', group='Rear monitor housing')
    cube('Monitor rear folded crown', (2.17, 39.12, 10.13),
         (13.83, 39.38, 15.16), 'charcoal', group='Rear monitor housing')
    for side, a, b in (('Left', -.62, -.48), ('Right', 16.48, 16.62)):
        cube(side+' broad pale monitor side skin', (a, 19.50, 9.31),
             (b, 37.52, 15.46), 'ivory', group='Rear monitor housing')
        cube(side+' upper side bevel', (a, 37.50, 10.13),
             (b, 38.46, 15.30), 'ivory', group='Rear monitor housing')
        cube(side+' lower side transport grip', (a-.015, 22.06, 11.41),
             (b+.015, 22.65, 13.94), 'rubber', group='Side cabinet details')
        cube(side+' side transport grip lip', (a-.02, 22.63, 11.53),
             (b+.02, 22.78, 13.80), 'steel', group='Side cabinet details')
        for y in (20.24, 30.04, 36.66):
            cube(side+' monitor cover screw '+str(y), (a-.02, y, 14.77),
                 (b+.02, y+.15, 14.92), 'steel', group='Side cabinet details')

    # Useful back-of-cabinet detail is restrained: removable covers, cooling,
    # service locks and the mains inlet rather than a blank monolithic block.
    for label, y0, y1 in (('Lower', 1.57, 16.64), ('Monitor', 18.16, 37.85)):
        z = 15.68 if label == 'Lower' else 15.47
        cube(label+' rear service-panel gasket', (.61, y0, z),
             (15.39, y1, z+.09), 'rubber', group='Rear service panels')
        cube(label+' rear access panel', (.83, y0+.21, z+.075),
             (15.17, y1-.21, z+.145), 'charcoal', group='Rear service panels')
        for x in (1.15, 14.68):
            for y in (y0+.49, y1-.65):
                cube(label+' rear panel screw '+str((x, y)), (x, y, z+.15),
                     (x+.17, y+.17, z+.205), 'steel', group='Rear service panels')
    cube('Rear pedestal low cooling grille', (4.14, 2.31, 15.84),
         (11.86, 4.48, 15.90), 'vent', group='Cabinet ventilation')
    cube('Rear monitor upper cooling grille', (5.06, 32.94, 15.64),
         (10.94, 36.19, 15.69), 'vent', group='Cabinet ventilation')
    cube('Rear monitor lower cooling grille', (5.06, 20.02, 15.64),
         (10.94, 23.27, 15.69), 'vent', group='Cabinet ventilation')
    cube('Rear power inlet mounting plate', (11.37, 1.95, 15.84),
         (14.48, 3.41, 15.92), 'steel', group='Rear service panels')
    cube('Rear mains socket', (12.19, 2.32, 15.925),
         (13.34, 2.97, 15.99), 'rubber', group='Rear service panels')
    cube('Rear serial-label plate', (1.57, 15.09, 15.83),
         (4.26, 15.70, 15.89), 'silver', group='Rear service panels')
