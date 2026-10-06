"""Reference-based cabinet shell and recessed lower assembly.

Coordinates use the generator's front-view convention before its final X mirror.
Only vanilla cuboids are emitted; the small deliberate steps keep the silhouette
legible alongside Minecraft blocks while preserving the real cabinet's recesses.
"""


def build_cabinet(cube, uv):
    """Emit the shell, footwell, triangular panel, and service-panel details."""
    # The rear tower is continuous and substantial. Broad unbroken black surfaces
    # are characteristic of the real cabinet, especially beside the lower screen.
    for y0, y1, label in ((1.4, 16, 'Base'), (16, 32, 'Console'), (32, 39.4, 'Display')):
        cube(label+' back shell', (1.2, y0, 8.8), (14.8, y1, 15.1), group='Back cabinet')

    # Black cheeks form a genuinely open footwell; the triangle is several pixels
    # behind the front rails and its upper vertex leans still farther into it.
    for side, x0, x1 in (('Left', 1.2, 2.15), ('Right', 13.85, 14.8)):
        cube(side+' footwell wall', (x0, 1.4, 4.3), (x1, 16, 9.0), group='Recessed footwell')
        cube(side+' footwell return', (x0, 2.4, 4.12), (x1, 15.9, 4.48),
             'black_key', group='Recessed footwell')
    cube('Footwell interior floor', (2.15, 1.75, 5.2), (13.85, 2.15, 9.12),
         'black_key', group='Recessed footwell')
    cube('Footwell top return', (2.0, 15.35, 4.15), (14.0, 16, 9.0), group='Recessed footwell')

    # The silver threshold wraps onto the side corners. Its rising inner surface
    # visually joins the inset triangular acrylic instead of leaving it floating.
    cube('Lower black plinth', (1.05, .48, 4.1), (14.95, 1.20, 15.18),
         'black_key', group='Metal threshold and feet')
    cube('Brushed metal front kick rail', (.95, .88, 3.90), (15.05, 1.90, 4.40),
         'silver', group='Metal threshold and feet')
    cube('Metal threshold front step', (1.0, 1.76, 4.10), (15.0, 2.03, 4.70),
         'silver', group='Metal threshold and feet')
    cube('Metal threshold middle step', (1.18, 1.97, 4.65), (14.82, 2.26, 5.19),
         'silver', group='Metal threshold and feet')
    cube('Metal threshold inner step', (1.40, 2.20, 5.14), (14.60, 2.52, 5.73),
         'silver', group='Metal threshold and feet')
    cube('Threshold inner dark seam', (2.18, 2.49, 5.68), (13.82, 2.57, 5.90),
         'black_key', group='Metal threshold and feet')
    for side, x0, x1 in (('Left', .95, 1.24), ('Right', 14.76, 15.05)):
        cube(side+' metal base return', (x0, .88, 4.25), (x1, 1.53, 14.90),
             'silver', group='Metal threshold and feet')
        cube(side+' front footplate fastener', (x0+.04, 1.20, 3.865), (x0+.20, 1.36, 3.915),
             'black_key', group='Metal threshold and feet')
    for x in (1.7, 13.5):
        for z in (4.7, 13.5):
            cube('Adjustable foot stem '+str((x, z)), (x+.18, .22, z+.18), (x+.62, .90, z+.62),
                 'silver', group='Metal threshold and feet')
            cube('Square rubber foot '+str((x, z)), (x, 0, z), (x+.8, .33, z+.8),
                 'black_key', group='Metal threshold and feet')

    # Continuous artwork UVs across the stepped triangular silhouette. A separate
    # dark substrate gives a narrow physical rim without a bright projecting fin.
    triangle_tilt = ('x', 22.5, (8, 2.45, 5.43))
    rows = 18
    width, height = 4.70, 8.0
    for i in range(rows):
        y0 = 2.45+i*height/rows
        y1 = 2.45+(i+1)*height/rows
        half = width*(1-i/rows)
        cube('Triangular inset dark edge %02d'%i, (8-half-.09, y0-.025, 5.465),
             (8+half+.09, y1+.025, 5.735), 'black_key', rotation=triangle_tilt,
             group='Recessed triangle')
        u0, u1 = 32-half/width*28, 32+half/width*28
        v0, v1 = 58-(i+1)/rows*53, 58-i/rows*53
        triangle_uv = [12+u0/16, 8+v0/16, 12+u1/16, 8+v1/16]
        cube('Recessed triangle engraved face %02d'%i, (8-half, y0, 5.425),
             (8+half, y1, 5.51), 'triangle', north=('materials', triangle_uv),
             rotation=triangle_tilt, group='Recessed triangle')

    # Two low-contrast service doors behind the recess, including a real key lock
    # on the right. The recess remains visibly deeper than both patterned rails.
    cube('Inset service door gasket', (3.15, 8.55, 8.51), (13.45, 15.66, 8.91),
         'black_key', group='Footwell service doors')
    cube('Upper maintenance hatch', (3.36, 10.05, 8.475), (8.78, 15.42, 8.57),
         'black', group='Footwell service doors')
    cube('Right maintenance hatch', (9.01, 8.77, 8.475), (13.24, 15.42, 8.57),
         'black', group='Footwell service doors')
    cube('Maintenance lock bezel', (9.33, 12.05, 8.385), (9.63, 12.53, 8.49),
         'silver', group='Footwell service doors')
    cube('Maintenance lock slot', (9.455, 12.13, 8.35), (9.51, 12.44, 8.40),
         'black_key', group='Footwell service doors')
    for y in (9.15, 14.65):
        cube('Right hatch hinge '+str(y), (12.95, y, 8.39), (13.20, y+.48, 8.51),
             'black_key', group='Footwell service doors')

    # The original machine uses little triangular shards, not a string of gems.
    # Repeated three-step wedges communicate that graphic at Minecraft scale.
    for side, x0, mirrored in (('Left', 1.25, False), ('Right', 13.65, True)):
        cube(side+' patterned rail substrate', (x0, 2.51, 4.035), (x0+1.1, 15.82, 4.18),
             'black_key', group='Triangular side ornament')
        for motif in range(9):
            bottom = 2.80+motif*1.39
            for step in range(3):
                strip_width = .86*(3-step)/3
                a = x0+.08 if not mirrored else x0+1.02-strip_width
                cube(side+' triangle border %02d step %d'%(motif, step),
                     (a, bottom+step*.29, 3.995), (a+strip_width, bottom+(step+1)*.29, 4.065),
                     'silver' if motif%3 == 1 else 'ivory', group='Triangular side ornament')
            # A single small shard breaks the repeated band toward the recess.
            a = x0+.80 if not mirrored else x0+.08
            cube(side+' scattered border shard %02d'%motif, (a, bottom+.95, 3.995),
                 (a+.19, bottom+1.14, 4.065), 'silver', group='Triangular side ornament')

    # The ivory side art is a thin applied insert, with a clear black perimeter.
    # Its narrower area leaves the large dark shell and its profile readable.
    for side, edge, direction in (('Left', 1.2, -1), ('Right', 14.8, 1)):
        a, b = sorted((edge, edge+direction*.11))
        c, d = sorted((edge+direction*.115, edge+direction*.15))
        cube(side+' side art dark surround', (a, 20.0, 10.70), (b, 38.15, 14.96),
             'black_key', group='Side cabinet details')
        cube(side+' ivory side insert', (c, 20.24, 10.95), (d, 37.90, 14.73), 'ivory',
             east=('side', [0, 0, 16, 16]), west=('side', [0, 0, 16, 16]),
             group='Side cabinet details')
        # A narrow recessed transport grip is visible on the photographed sides.
        cube(side+' transport grip surround', (a, 14.45, 10.92), (b, 15.20, 13.57),
             'black_key', group='Side cabinet details')
        cube(side+' transport grip upper lip', (c, 15.12, 10.98), (d, 15.28, 13.50),
             'black', group='Side cabinet details')
        # The low rear grille is restrained, unlike the former full-height patch.
        cube(side+' lower vent frame', (a, 3.05, 11.67), (b, 6.94, 14.32),
             'black_key', group='Side cabinet details')
        vent = uv('vent')
        vent_crop = [vent[0], vent[1], vent[2], vent[1]+2.1]
        cube(side+' lower ventilation grille', (c, 3.24, 11.85), (d, 6.75, 14.14),
             'black', east=('materials', vent_crop), west=('materials', vent_crop),
             group='Side cabinet details')
        for y, z in ((2.10, 14.46), (15.54, 14.46), (38.40, 14.46)):
            cube(side+' shell screw '+str(y), (c, y, z), (d, y+.15, z+.15),
                 'silver', group='Side cabinet details')

    # Rear access panels and vents also read correctly when the cabinet is placed
    # away from a wall. All details are shallow and use the same restrained scale.
    cube('Rear lower service panel', (2.05, 2.28, 15.11), (13.95, 15.36, 15.19),
         'black_key', group='Rear service panels')
    cube('Rear upper service panel', (2.05, 16.10, 15.11), (13.95, 37.90, 15.19),
         'black_key', group='Rear service panels')
    for x0, x1 in ((2.62, 6.55), (9.45, 13.38)):
        cube('Rear low ventilation '+str(x0), (x0, 3.07, 15.195), (x1, 7.02, 15.24),
             'vent', group='Rear service panels')
        cube('Rear upper ventilation '+str(x0), (x0, 32.88, 15.195), (x1, 36.05, 15.24),
             'vent', group='Rear service panels')
    cube('Rear power plate', (10.76, 2.55, 15.245), (12.62, 3.94, 15.28),
         'black', group='Rear service panels')
    cube('Rear power socket', (11.19, 2.91, 15.285), (12.09, 3.51, 15.32),
         'silver', group='Rear service panels')
    cube('Rear power socket inset', (11.35, 3.03, 15.325), (11.93, 3.36, 15.355),
         'black_key', group='Rear service panels')
    for x in (2.25, 13.53):
        for y in (2.50, 15.0, 16.40, 37.48):
            cube('Rear access fastener '+str((x, y)), (x, y, 15.20), (x+.17, y+.17, 15.255),
                 'silver', group='Rear service panels')

