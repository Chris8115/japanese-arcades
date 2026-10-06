"""The Op.3 open music book, cascading piano ribbon, and flower ornaments.

The fan is deliberately modeled with a changing depth and lower edge instead of
one straight extrusion. Printed sprites provide intricate native pixel artwork;
the cuboids supply a readable, restrained stepped silhouette in Minecraft.
"""


def build_marquee(cube, cutout_sprite):
    """Emit the complete book and key/rosette assembly in cabinet coordinates."""
    # The hidden brackets bridge the fascia and the book's recessed center fold.
    for x in (6.75, 8.65):
        cube('Book support bracket '+str(x), (x, 39.6, 9.72), (x+.46, 41.15, 10.72),
             'gold', group='Book supports')

    # A real open book forms a shallow V: the center spine is farthest back and
    # the outer page edges reach forward. The book still clears the piano fan.
    # The higher right page retains the distinctive silhouette of the real POP.
    spine_z = 10.50
    for name, cell, x0, x1, bottom, top, angle, hinge in (
            ('Left music', (0, 1), 1.00, 7.90, 40.75, 46.10, -22.5, 7.90),
            ('Right cat', (1, 1), 7.86, 14.92, 40.82, 47.65, 22.5, 7.86)):
        rotation = ('y', angle, (hinge, bottom, spine_z))
        cutout_sprite(name+' stepped gold book cover', cell,
                      (x0-.11, bottom-.13, spine_z+.29), (x1+.11, top+.14, spine_z+.68),
                      'gold', rotation=rotation, printed=False, group='Book covers')
        cutout_sprite(name+' ivory page edges', cell,
                      (x0-.035, bottom-.055, spine_z+.13), (x1+.035, top+.055, spine_z+.39),
                      'white_key', rotation=rotation, printed=False, group='Book page layers')
        cutout_sprite(name+' illustrated front page', cell,
                      (x0, bottom, spine_z), (x1, top, spine_z+.19),
                      'gold', rotation=rotation, group='Book artwork')
        # A few visible leaves catch light on the outer thickness of the book.
        # These are edge lines, not separate floating sheets in front of the art.
        edge = x0-.035 if name.startswith('Left') else x1-.075
        for n in range(3):
            z = spine_z+.17+n*.075
            cube(name+' outer page edge '+str(n), (edge, bottom+.27, z),
                 (edge+.11, top-.32, z+.025), 'ivory', rotation=rotation,
                 group='Book page layers')

    cube('Recessed book center spine', (7.67, 40.56, 10.40), (8.14, 45.57, 10.84),
         'gold', group='Book spine')
    for y in (41.24, 42.58, 43.92):
        cube('Raised book binding band '+str(y), (7.56, y, 10.31), (8.23, y+.17, 10.91),
             'gold', group='Book spine')

    # Each key has its own heel height and front depth. Together they make a
    # shallow crest on the left/middle, then visibly cascade over the right fascia.
    # The wide clear ivory faces and coral sharps match the real printed piano POP.
    keys = (
        (.50, 39.38, 3.25, 7.15),
        (1.65, 39.17, 3.60, 6.98),
        (2.80, 39.40, 3.45, 6.70),
        (3.95, 39.65, 3.76, 6.52),
        (5.10, 39.58, 3.65, 6.36),
        (6.25, 39.48, 3.98, 6.13),
        (7.40, 39.29, 3.82, 5.92),
        (8.55, 39.05, 3.76, 5.73),
        (9.70, 38.79, 3.65, 5.55),
        (10.85, 38.54, 3.44, 5.40),
        (12.00, 38.22, 3.31, 5.25),
        (13.15, 37.96, 3.08, 5.16),
    )
    for i, (x, y, height, front) in enumerate(keys):
        rotation = ('z', -22.5, (x+.515, y+.45, front+.36))
        color = ('blue', 'lavender', 'pink')[min(2, i//4)]
        cube('Piano ribbon ivory backing %02d'%i, (x-.035, y-.035, front+.56),
             (x+1.075, y+height+.07, front+1.02), 'ivory',
             rotation=rotation, group='Cascading piano ribbon')
        cube('Piano ribbon white key %02d'%i, (x, y, front),
             (x+1.04, y+height, front+.64), 'white_key',
             rotation=rotation, group='Cascading piano ribbon')
        cube('Piano ribbon tinted heel %02d'%i, (x, y-.09, front-.045),
             (x+1.04, y+.49, front+.10), color,
             rotation=rotation, group='Cascading piano ribbon')
        if i%7 not in (2, 6):
            cube('Piano ribbon coral sharp %02d'%i, (x+.73, y+1.03, front-.18),
                 (x+1.12, y+height+.15, front+.08), 'red_key',
                 rotation=rotation, group='Cascading piano ribbon')
        if i in (1, 5, 9):
            cube('Piano ribbon light sliver %02d'%i, (x+.12, y+.51, front-.058),
                 (x+.92, y+.61, front+.015), 'teal',
                 rotation=rotation, glow=('north',), group='Marquee lights')

    # Thin relief follows the key fan rather than becoming three large flower
    # balls. Broad saturated petals and gold centers remain legible at a distance.
    for name, cell, x, y, width, front, color in (
            ('Blue', (0, 0), .25, 39.75, 3.45, 6.48, 'blue'),
            ('Lavender', (1, 0), 5.24, 39.07, 3.66, 5.30, 'lavender'),
            ('Pink', (2, 0), 11.59, 37.88, 3.91, 4.44, 'pink')):
        rotation = ('z', -22.5, (x+width/2, y+width/2, front+.25))
        cutout_sprite(name+' rosette thin backing', cell,
                      (x-.085, y-.085, front+.24), (x+width+.085, y+width+.085, front+.77),
                      color, rotation=rotation, printed=False, group='Rosette backing layers')
        cutout_sprite(name+' cascading rosette', cell,
                      (x, y, front), (x+width, y+width, front+.31), 'ivory',
                      rotation=rotation, relief=.22, glow=('north',), group='Cascading rosettes')

    # The small right-side ornaments descend in size like the physical cutouts.
    # Their shallower layers keep the upper monitor trim visible around them.
    for name, cell, x, y, width, front, color in (
            ('Pink', (2, 0), 14.26, 34.80, 2.35, 7.12, 'pink'),
            ('Lavender', (1, 0), 14.42, 32.23, 2.05, 7.16, 'lavender'),
            ('Blue', (0, 0), 14.48, 30.26, 1.62, 7.20, 'blue')):
        cutout_sprite(name+' side flower backing', cell,
                      (x-.055, y-.055, front+.14), (x+width+.055, y+width+.055, front+.54),
                      color, printed=False, group='Monitor flower backing')
        cutout_sprite(name+' side monitor flower', cell,
                      (x, y, front), (x+width, y+width, front+.22), 'ivory',
                      relief=.12, glow=('north',), group='Monitor flowers')
