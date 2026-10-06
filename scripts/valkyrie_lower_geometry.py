"""Valkyrie model's open pedestal, acrylic control deck and lower speaker wings.

The broad black silhouette, luminous hanging V and seven-button/two-knob control
layout follow the supplied real cabinet photographs. Dimensions are in model
pixels; one block is 16 units. Every emitted part remains a vanilla cuboid.
"""

import math


def build_lower(cube, uv, polygon, speaker):
    """Emit the pedestal and console, ending at the portrait monitor's y=24 join."""
    # Substantial continuous rear shell, but a genuinely hollow front footwell.
    cube('Pedestal rear cabinet', (-.55, 1.05, 11.20), (16.55, 18.40, 15.65),
         'black', group='Pedestal shell')
    cube('Pedestal left side wall', (-.70, 1.05, 4.35), (.50, 18.2, 15.7),
         'black', group='Pedestal shell')
    cube('Pedestal right side wall', (15.50, 1.05, 4.35), (16.70, 18.2, 15.7),
         'black', group='Pedestal shell')
    cube('Footwell shadow ceiling', (.45, 16.70, 3.40), (15.55, 18.15, 11.40),
         'charcoal', group='Pedestal shell')
    cube('Footwell inner back', (.45, 1.20, 11.08), (15.55, 16.78, 11.30),
         'charcoal', group='Pedestal shell')

    # The real legs widen into low angular feet. Clipped profiles are intentional
    # Minecraft-sized steps, with folded silver edges only on the inside faces.
    left_leg = [(-.75, .60), (1.18, .60), (1.18, 2.15), (.62, 4.95),
                (.68, 13.9), (1.20, 17.85), (-.75, 17.85)]
    left_trim = [(1.03, 1.03), (1.27, 1.03), (1.27, 2.10), (.82, 5.04),
                 (.86, 13.80), (1.35, 17.77), (1.12, 17.77), (.64, 13.82),
                 (.61, 5.04), (1.03, 2.10)]
    for side, mirror in (('Left', False), ('Right', True)):
        points = lambda seq: [(16-x if mirror else x, y) for x, y in seq]
        polygon(side+' angular front leg', points(left_leg), 3.40, 5.15,
                'black', group='Structural legs')
        polygon(side+' folded inner leg edge', points(left_trim), 3.33, 3.51,
                'silver', group='Structural legs')
        x = 15.00 if mirror else .76
        cube(side+' upper leg seam', (x, 14.10, 3.285), (x+.23, 17.72, 3.375),
             'steel', group='Structural legs')
        for y in (1.40, 16.83):
            x = 15.77 if mirror else .06
            cube(side+' leg fixing '+str(y), (x, y, 3.30), (x+.18, y+.18, 3.45),
                 'silver', group='Cabinet hardware')

    cube('Lower chassis plinth', (-.70, .47, 3.65), (16.70, 1.05, 15.70),
         'black', group='Threshold and feet')
    cube('Brushed silver footwell floor', (1.21, .94, 3.37), (14.79, 1.18, 11.30),
         'silver', group='Threshold and feet')
    cube('Folded silver front kick plate', (1.20, .47, 3.26), (14.80, 1.18, 3.54),
         'silver', group='Threshold and feet')
    cube('Kick plate upper glint', (1.24, 1.17, 3.26), (14.76, 1.24, 3.58),
         'white', group='Threshold and feet')
    cube('Footwell rear raised floor', (1.30, 1.15, 9.76), (14.70, 1.35, 11.29),
         'steel', group='Threshold and feet')
    for x in (.27, 14.88):
        for z in (4.05, 13.9):
            cube('Levelling stem '+str((x, z)), (x+.17, .12, z+.17),
                 (x+.59, .54, z+.59), 'steel', group='Threshold and feet')
            cube('Rubber levelling foot '+str((x, z)), (x, 0, z),
                 (x+.78, .20, z+.78), 'rubber', group='Threshold and feet')

    # The suspended central light assembly ends well above the floor. Its two
    # independently framed tapered blades read as a V, not a solid cyan slab.
    # A dark speaker niche remains open between the upper portions of the blades.
    left_blade = [(3.10, 16.93), (5.12, 16.93), (7.47, 3.53), (6.16, 3.53)]
    left_lens = [(3.43, 16.63), (4.94, 16.63), (7.14, 3.84), (6.36, 3.84)]
    left_recess = [(3.61, 16.58), (4.15, 16.58), (6.63, 4.06), (6.40, 4.06)]
    for side, mirror in (('Left', False), ('Right', True)):
        points = lambda seq: [(16-x if mirror else x, y) for x, y in seq]
        polygon(side+' lower blade metal frame', points(left_blade), 7.38, 8.20,
                'silver', group='Luminous lower V')
        polygon(side+' lower blade etched acrylic', points(left_lens), 7.27, 7.47,
                'glass', front=('wing', [0, 6, 16, 16]),
                group='Luminous lower V', glow=('north',))
        polygon(side+' lower blade cyan inlay', points(left_recess), 7.22, 7.30,
                'cyan', group='Luminous lower V', glow=('north',))
        # Broken light rails and plated joints echo the circuit paths visible in
        # the real cabinet without covering the broad glass with tiny geometry.
        for index, (y, length) in enumerate(((5.10, 1.60), (8.75, 2.65), (13.30, 2.10))):
            cx = 6.27-(y-4.0)*.201
            if mirror:
                cx = 16-cx
            angle = -22.5 if mirror else 22.5
            c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            trace = [(cx+dx*c-dy*s, y+dx*s+dy*c)
                     for dx, dy in ((-.06, 0), (.06, 0), (.06, length), (-.06, length))]
            polygon(side+' inner light trace '+str(index), trace, 7.195, 7.235,
                    'cyan_bright', glow=('north',), group='Luminous lower V', step=.10)
        for y, x in ((4.04, 6.63), (9.12, 5.52), (16.24, 3.49)):
            x = 16-x if mirror else x
            cube(side+' blade fastener '+str(y), (x-.09, y, 7.19), (x+.09, y+.18, 7.30),
                 'steel', group='Luminous lower V')

    cube('Subwoofer niche backplate', (5.00, 9.20, 8.36), (11.00, 16.95, 9.25),
         'black', group='Lower subwoofer')
    speaker('Recessed pedestal subwoofer', 8, 12.63, 8.28, 2.05,
            group='Lower subwoofer', silver=True)
    cube('Subwoofer lower transverse silver brace', (5.64, 9.25, 7.37),
         (10.36, 9.57, 8.34), 'silver', group='Lower subwoofer')
    for x in (5.90, 9.93):
        cube('Subwoofer brace fixing '+str(x), (x, 9.32, 7.30),
             (x+.17, 9.49, 7.40), 'steel', group='Lower subwoofer')
    polygon('Central lower acrylic spear', [(6.53, 8.93), (9.47, 8.93), (8.46, 3.61), (7.54, 3.61)],
            8.13, 8.44, 'glass', front=('wing', [0, 6, 16, 16]),
            group='Luminous lower V', glow=('north',))
    polygon('Central lower dark dividing seam', [(7.78, 8.91), (8.22, 8.91), (8.11, 3.65), (7.89, 3.65)],
            8.065, 8.17, 'charcoal', group='Luminous lower V')
    cube('Lower V terminating silver bracket', (6.20, 3.37, 7.27), (9.80, 3.65, 8.45),
         'steel', group='Luminous lower V')

    # Tall exterior graphics and restrained access-panel hardware remain visible
    # from the sides/back; the public-facing silhouette stays uncluttered.
    for side, a, b in (('Left', -.76, -.705), ('Right', 16.705, 16.76)):
        cube(side+' SOUND VOLTEX side graphic', (a, 2.06, 5.02), (b, 16.34, 8.59),
             'black', east=('side', [0, 0, 16, 16]), west=('side', [0, 0, 16, 16]),
             group='Side service details')
        cube(side+' lower cooling vent recess', (a, 3.31, 11.60), (b, 7.92, 14.52),
             'vent', group='Side service details')
        cube(side+' transport handle recess', (a, 14.98, 11.36), (b, 15.66, 13.90),
             'rubber', group='Side service details')
    cube('Rear lower access-panel gasket', (.44, 1.81, 15.66), (15.56, 16.75, 15.76),
         'rubber', group='Rear service details')
    cube('Rear lower maintenance door', (.71, 2.08, 15.75), (15.29, 16.48, 15.82),
         'black', group='Rear service details')
    cube('Rear ventilation grille', (5.86, 11.70, 15.83), (10.14, 14.69, 15.87),
         'vent', group='Rear service details')
    cube('Rear power connection plate', (11.80, 2.75, 15.83), (14.23, 4.30, 15.89),
         'steel', group='Rear service details')
    cube('Rear power socket', (12.49, 3.07, 15.89), (13.47, 3.71, 15.97),
         'rubber', group='Rear service details')
    for x in (1.07, 14.73):
        for y in (2.41, 16.05):
            cube('Rear service screw '+str((x, y)), (x, y, 15.83),
                 (x+.16, y+.16, 15.90), 'steel', group='Rear service details')

    # Thick black control-deck undertray and its clipped front corners. The
    # cyan-edged acrylic top is a shallow shelf; it is not a piano keyboard.
    for i in range(4):
        front, back = i*.35, (i+1)*.35+.02
        inset = (3-i)*.34
        cube('Clipped control deck undertray '+str(i), (-1.45+inset, 17.77, front),
             (17.45-inset, 19.22, back), 'black', group='Control deck enclosure')
        cube('Clipped acrylic front edge '+str(i), (-1.51+inset, 19.15, front-.035),
             (17.51-inset, 19.36, back+.015), 'teal', glow=('north', 'up'),
             group='Illuminated acrylic control deck')
    cube('Broad black deck undertray', (-1.45, 17.77, 1.40), (17.45, 19.23, 11.85),
         'black', group='Control deck enclosure')
    cube('Acrylic deck silver substrate', (-1.50, 19.20, 1.40), (17.50, 19.34, 8.50),
         'steel', group='Illuminated acrylic control deck')
    cube('Etched cyan acrylic playing surface', (-1.38, 19.34, 1.43),
         (17.38, 19.41, 8.35), 'glass', glow=('up',),
         group='Illuminated acrylic control deck')
    for x in (-1.53, 17.39):
        cube('Acrylic side light seam '+str(x), (x, 19.24, 1.39), (x+.14, 19.44, 8.38),
             'cyan', glow=('north', 'up', 'east', 'west'),
             group='Illuminated acrylic control deck')
    # A dark central field keeps the tactile white keys and black FX buttons
    # legible through the transparent-panel effect at normal play distance.
    cube('Control layout smoked centre panel', (3.14, 19.42, 1.41), (12.86, 19.46, 7.71),
         'charcoal', group='Controls')
    for x in (3.18, 12.72):
        cube('Centre panel cyan pinstripe '+str(x), (x, 19.468, 1.54),
             (x+.10, 19.484, 7.59), 'cyan', glow=('up',), group='Controls')
    cube('Start button square socket', (7.35, 19.47, 5.35), (8.65, 19.62, 6.47),
         'rubber', group='Seven-button layout')
    cube('Start button blue surround', (7.49, 19.61, 5.48), (8.51, 19.79, 6.34),
         'blue', glow=('up',), group='Seven-button layout')
    cube('Start button white face', (7.63, 19.79, 5.61), (8.37, 19.84, 6.20),
         'button', glow=('up',), group='Seven-button layout')
    for i in range(4):
        x = 4.12+i*1.94
        cube('BT-'+str(i+1)+' black socket', (x-.12, 19.46, 3.43),
             (x+1.76, 19.62, 5.46), 'rubber', group='Seven-button layout')
        cube('BT-'+str(i+1)+' silver key surround', (x-.035, 19.60, 3.52),
             (x+1.675, 19.70, 5.37), 'steel', group='Seven-button layout')
        cube('BT-'+str(i+1)+' white square key', (x+.07, 19.69, 3.62),
             (x+1.57, 19.93, 5.27), 'button', glow=('up',),
             group='Seven-button layout')
    for label, x in (('L', 4.70), ('R', 8.88)):
        cube('FX-'+label+' socket', (x-.15, 19.46, 2.09),
             (x+2.57, 19.62, 3.38), 'rubber', group='Seven-button layout')
        cube('FX-'+label+' orange indicator rim', (x-.035, 19.61, 2.18),
             (x+2.455, 19.68, 3.30), 'pink', group='Seven-button layout')
        cube('FX-'+label+' broad black key', (x+.05, 19.67, 2.27),
             (x+2.36, 19.91, 3.20), 'black', group='Seven-button layout')

    # Chunky dodecagon-like encoders are assembled in X/Z courses. Their raised
    # silver grips, black collar and blue marker are visible from all directions.
    for label, cx in (('Left', 1.10), ('Right', 14.90)):
        cz = 3.65
        for ring, radius, y0, y1, material in (
                ('luminous socket', 1.51, 19.44, 19.52, 'cyan'),
                ('rubber collar', 1.31, 19.50, 19.68, 'rubber'),
                ('encoder grip', 1.04, 19.67, 20.25, 'silver'),
                ('encoder cap', .94, 20.24, 20.34, 'steel')):
            for row in range(5):
                z0 = -radius+2*radius*row/5
                z1 = -radius+2*radius*(row+1)/5
                half = math.sqrt(max(0, radius*radius-((z0+z1)/2)**2))
                cube(label+' '+ring+' '+str(row), (cx-half, y0, cz+z0),
                     (cx+half, y1, cz+z1), material,
                     glow=('up',) if material == 'cyan' else False,
                     group='Twin VOL encoders')
        cube(label+' encoder blue position mark', (cx-.095, 20.345, cz+.18),
             (cx+.095, 20.39, cz+.83), 'cyan_bright', glow=('up',),
             group='Twin VOL encoders')

    # Front belt is text at its true six-to-one aspect, on a stepped angular
    # metal-edged plate. The centre touchscreen has its own separate 3:1 artwork.
    belt = [(2.52, 19.01), (13.48, 19.01), (12.80, 17.70), (3.20, 17.70)]
    polygon('Valkyrie belt silver surround', belt, -.16, .20, 'silver',
            group='Valkyrie nameplate')
    polygon('Valkyrie belt printed face', [(2.77, 18.88), (13.23, 18.88),
                                         (12.66, 17.84), (3.34, 17.84)],
            -.205, -.13, 'black', group='Valkyrie nameplate')
    cube('Valkyrie model belt title', (4.25, 17.72, -.23), (11.75, 18.97, -.19),
         'black', north=('details', [4, 0, 16, 4]), group='Valkyrie nameplate')
    cube('Front belt upper cyan seam', (2.75, 19.015, -.19), (13.25, 19.10, .01),
         'cyan', glow=('north', 'up'), group='Valkyrie nameplate')
    # Flat labels on the actual playing surface, rather than a made-up side
    # terminal. They leave the two VOL knobs and seven central keys unobstructed.
    cube('Small printed safety label', (11.70, 19.476, 6.51), (12.55, 19.492, 7.46),
         'white', up=('details', [4, 4, 8, 8]), group='Control-deck hardware')
    cube('Control deck coin slot surround', (15.52, 19.465, 1.89),
         (16.67, 19.54, 2.53), 'silver', group='Control-deck hardware')
    cube('Control deck coin aperture', (15.82, 19.541, 2.13),
         (16.39, 19.57, 2.27), 'rubber', group='Control-deck hardware')
    for x, z in ((-.63, 2.03), (16.49, 2.03), (-.65, 7.78), (16.49, 7.78)):
        cube('Deck countersunk screw '+str((x, z)), (x, 19.421, z),
             (x+.16, 19.451, z+.16), 'silver', group='Control-deck hardware')

    # Two angular silver housings cant upward at the touchscreen's angle. Each
    # wing's outer shoulder rises higher than its inner edge as on the photos.
    cube('Console rear electronics enclosure', (-.34, 19.34, 7.10),
         (16.34, 24.10, 13.05), 'black', group='Lower speaker enclosure')
    outline = [(-1.47, 24.09), (.72, 23.91), (3.70, 23.00), (4.21, 20.47),
               (3.66, 20.18), (-.62, 20.48), (-1.52, 22.79)]
    inset = [(-1.19, 23.73), (.65, 23.62), (3.42, 22.79), (3.83, 20.65),
             (3.49, 20.50), (-.39, 20.76), (-1.19, 22.82)]
    for side, cx, mirror in (('Left', 1.19, False), ('Right', 14.81, True)):
        points = lambda seq: [(16-x if mirror else x, y) for x, y in seq]
        tilt = ('x', 22.5, (cx, 20.44, 6.28))
        polygon(side+' lower speaker black housing', points(outline), 6.35, 7.52,
                'black', group='Canted lower speaker wings', rotation=tilt)
        polygon(side+' lower speaker folded silver plate', points(outline), 6.18, 6.44,
                'silver', group='Canted lower speaker wings', rotation=tilt)
        polygon(side+' lower speaker pale inset', points(inset), 6.12, 6.23,
                'white', group='Canted lower speaker wings', rotation=tilt)
        speaker(side+' lower speaker', cx, 21.98, 6.01, 1.77,
                rotation=tilt, group='Canted lower speaker wings')
        for index, (x, y) in enumerate(((-1.06, 23.53), (-.36, 20.83), (3.36, 20.76))):
            x = 16-x if mirror else x
            cube(side+' speaker fixing '+str(index), (x-.09, y, 6.025),
                 (x+.09, y+.18, 6.14), 'steel', rotation=tilt,
                 group='Canted lower speaker wings')
        # The real plates have angular black circuit inlays beside their grille.
        x = 15.74 if mirror else .26
        cube(side+' speaker lower black accent', (x-.55, 20.53, 6.06),
             (x+.50, 20.65, 6.13), 'black', rotation=tilt,
             group='Canted lower speaker wings')

    tilt = ('x', 22.5, (8, 20.65, 6.52))
    cube('Auxiliary display silver chassis', (4.00, 20.52, 6.48),
         (12.00, 23.61, 7.25), 'steel', rotation=tilt, group='Auxiliary touchscreen')
    cube('Auxiliary display black bezel', (4.34, 20.70, 6.37),
         (11.66, 23.38, 6.59), 'rubber', rotation=tilt, group='Auxiliary touchscreen')
    cube('Auxiliary EXCEED GEAR touchscreen', (4.59, 20.91, 6.325),
         (11.41, 23.18, 6.40), 'black', north=('branding', [0, 0, 16, 16]),
         rotation=tilt, glow=('north',), group='Auxiliary touchscreen')
    cube('Auxiliary display bottom status line', (4.67, 20.81, 6.30),
         (11.33, 20.875, 6.42), 'cyan', rotation=tilt, glow=('north',),
         group='Auxiliary touchscreen')
