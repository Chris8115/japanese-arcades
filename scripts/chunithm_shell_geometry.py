"""Chunithm Paradise Lost pedestal, metal footstep and solid display support.

The cabinet photographs have a comparatively plain white service body. The
light wall, canopy, display and touch slider belong to the main generator; this
module supplies their physical enclosure without putting controls on the screen.
"""
import math


def build_shell(cube, polygon):
    """Emit the lower housing and the open-front U-shaped metal footstep."""
    # The black chassis stands behind the metal step, lifting the white cabinet
    # clear of the floor. Its front stays open below the crossbar and side arms.
    cube('Pedestal black rear plinth', (-.45, .36, 6.08), (16.45, 3.49, 15.56),
         'black', group='Black pedestal')
    cube('Pedestal recessed front wall', (.65, 1.46, 4.86), (15.35, 3.50, 6.18),
         'rubber', group='Black pedestal')
    cube('Pedestal upper shadow band', (-.43, 2.77, 4.56), (16.43, 3.62, 15.60),
         'rubber', group='Black pedestal')

    # A brushed steel U frame: two forward arms and a transverse rear tread.
    # Keeping the centre of its front open matches the photographed step instead
    # of turning the whole footprint into a solid metal tray.
    for side, x0, x1 in (('Left', -.53, 1.05), ('Right', 14.95, 16.53)):
        cube(side+' footstep black structural arm', (x0, .21, -.73),
             (x1, 1.59, 10.37), 'black', group='Metal U footstep')
        cube(side+' footstep brushed metal tread', (x0+.06, 1.33, -.48),
             (x1-.06, 1.73, 10.32), 'silver', group='Metal U footstep')
        cube(side+' footstep front folded edge', (x0+.07, .67, -.81),
             (x1-.07, 1.41, -.45), 'steel', group='Metal U footstep')
        cube(side+' footstep toe bevel', (x0+.05, 1.09, -.77),
             (x1-.05, 1.47, -.39), 'silver',
             rotation=('x', 22.5, ((x0+x1)/2, 1.09, -.77)), group='Metal U footstep')
        cube(side+' step outer folded strip', (x0 if side == 'Left' else x1-.12, .61, -.29),
             (x0+.12 if side == 'Left' else x1, 1.44, 10.29),
             'steel', group='Metal U footstep')
    cube('Footstep broad transverse tread', (.97, 1.35, 2.37),
         (15.03, 1.78, 5.33), 'silver', group='Metal U footstep')
    cube('Footstep front crossbar fold', (1.02, .86, 2.25),
         (14.98, 1.50, 2.62), 'steel', group='Metal U footstep')
    cube('Footstep crossbar bright top edge', (1.02, 1.48, 2.25),
         (14.98, 1.79, 2.50), 'silver', group='Metal U footstep')
    cube('Footstep back black riser', (1.03, 1.71, 5.13),
         (14.97, 2.49, 5.48), 'rubber', group='Metal U footstep')
    for x in (.13, 15.08):
        for z in (.15, 13.78):
            cube('Adjustable steel foot '+str((x, z)), (x+.09, .12, z+.09),
                 (x+.58, .62, z+.58), 'steel', group='Cabinet feet')
            cube('Dark floor pad '+str((x, z)), (x, 0, z),
                 (x+.67, .21, z+.67), 'rubber', group='Cabinet feet')

    # The continuous front edge leans toward the player as it rises, meeting
    # the slider at z=.1 instead of leaving a deep unsupported control overhang.
    # All fascia details share one native rotation; doors and reader remain
    # planar, and their old y coordinates retain their intended world heights.
    angle = math.radians(22.5)
    cosine, tangent = math.cos(angle), math.tan(angle)
    pivot = (8, 15.8, .1)

    def fascia(name, start, end, material, **options):
        def local(point):
            x, y, z = point
            return (x, 15.8+(y-15.8)/cosine, .1+z-4.06)
        cube(name, local(start), local(end), material,
             rotation=('x', -22.5, pivot), **options)

    def body_front(y):
        return .1+(15.8-y)*tangent

    # Hidden courses fill the broad wedge behind the smooth rotated fascia.
    # Their .5-unit rise is smaller than the fascia's overlap, so the body
    # cannot leave an open seam between the inclined face and the side skins.
    count = math.ceil((15.84-3.53)/.5)
    for row in range(count):
        y0 = 3.53+(15.84-3.53)*row/count
        y1 = 3.53+(15.84-3.53)*(row+1)/count
        cube('Main white pedestal wedge course %02d'%row,
             (-.46, y0, body_front(y0)+.14), (16.46, y1, 15.47),
             'white', group='White lower cabinet')
    fascia('Main front folded panel', (-.37, 3.54, 4.06),
           (16.37, 15.84, 4.45), 'white', group='White lower cabinet')
    fascia('Front top shallow access-strip seam', (.10, 14.01, 4.015),
         (15.90, 14.08, 4.13), 'rim_gray', group='Front service panels')
    fascia('Front top access strip', (-.14, 14.09, 4.015),
         (16.14, 15.36, 4.08), 'ivory', group='Front service panels')
    for side, x0, x1 in (('Left', -.62, .02), ('Right', 15.98, 16.62)):
        for row in range(count):
            y0 = 3.48+(15.81-3.48)*row/count
            y1 = 3.48+(15.81-3.48)*(row+1)/count
            cube(side+' folded lower side wedge course %02d'%row,
                 (x0, y0, body_front(y0)+.12), (x1, y1, 15.53),
                 'white', group='White lower cabinet')
        # Rotated pieces bypass the axis-aligned exterior union. Offset both
        # end faces from the side courses so their shared X planes cannot fight.
        fascia(side+' smooth inclined front corner',
               (x0-.045, 3.48, 4.025), (x1+.045, 15.81, 4.53),
               'white', group='White lower cabinet')
        cube(side+' bottom side bevel', (x0+.05, 3.22, 5.35),
             (x1-.05, 3.52, 15.36), 'ivory', group='White lower cabinet')
        cube(side+' upper cabinet shadow seam', (x0-.015, 15.62, 5.11),
             (x1+.015, 15.76, 15.52), 'rubber', group='Side cabinet details')

    # Large service door on the upper left; the right carries the green reader
    # fitted to the machine in the first supplied real-machine photograph.
    fascia('Upper maintenance door outline', (.78, 9.39, 3.991),
         (10.64, 13.75, 4.075), 'rim_gray', group='Front service panels')
    fascia('Upper maintenance door face', (.87, 9.48, 3.965),
         (10.55, 13.66, 4.025), 'white', group='Front service panels')
    fascia('Reader backing access plate outline', (10.85, 9.19, 3.991),
         (15.36, 13.53, 4.075), 'rim_gray', group='Front service panels')
    fascia('Reader backing access plate', (10.94, 9.28, 3.962),
         (15.27, 13.44, 4.025), 'white', group='Front service panels')
    fascia('Lower grille metal surround', (.81, 4.05, 3.982),
         (9.39, 7.82, 4.090), 'rim_gray', group='Ventilation')
    fascia('Lower grille inset mesh', (1.01, 4.23, 3.947),
         (9.19, 7.63, 4.017), 'vent', group='Ventilation')
    fascia('Lower right access-door outline', (10.04, 3.98, 3.980),
         (15.47, 8.32, 4.085), 'rim_gray', group='Front service panels')
    fascia('Lower right access-door face', (10.14, 4.08, 3.950),
         (15.37, 8.22, 4.020), 'white', group='Front service panels')
    for name, x, y in (('Upper strip', 7.93, 14.83), ('Main service', 5.69, 13.03),
                       ('Reader plate', 13.02, 13.02), ('Lower service', 12.72, 5.64)):
        fascia(name+' lock mounting plate', (x-.22, y-.22, 3.86),
             (x+.22, y+.22, 4.02), 'silver', group='Service locks and fasteners')
        fascia(name+' lock dark keyway', (x-.028, y-.14, 3.815),
             (x+.028, y+.12, 3.890), 'black', group='Service locks and fasteners')
    for x, y in ((.25, 14.86), (15.61, 14.86), (1.02, 9.71), (10.36, 9.71),
                 (11.12, 9.57), (15.10, 9.57), (1.03, 4.31), (15.20, 4.33)):
        fascia('Front panel fixing '+str((x, y)), (x-.055, y-.055, 3.925),
             (x+.055, y+.055, 4.035), 'steel', group='Service locks and fasteners')

    # Compact clipped-corner housing and raised screen of the photographed venue
    # card reader. This is separate from the factory Aime area above the display.
    fascia('Front green reader black backing', (11.21, 10.26, 3.64),
         (14.99, 12.67, 3.99), 'charcoal', group='Green front card reader')
    fascia('Green reader central shell', (11.38, 10.42, 3.20),
         (14.82, 12.51, 3.73), 'green', glow=('north',), group='Green front card reader')
    fascia('Green reader upper clipped edge', (11.74, 12.50, 3.27),
         (14.47, 12.69, 3.72), 'green', glow=('north',), group='Green front card reader')
    fascia('Green reader lower clipped edge', (11.74, 10.25, 3.27),
         (14.47, 10.44, 3.72), 'green', glow=('north',), group='Green front card reader')
    fascia('Green reader screen bezel', (11.84, 10.87, 3.115),
         (14.16, 12.11, 3.36), 'rubber', group='Green front card reader')
    fascia('Green reader dark display', (12.04, 11.01, 3.085),
         (13.96, 11.96, 3.145), 'charcoal', group='Green front card reader')
    fascia('Green reader display status line', (12.33, 11.19, 3.073),
         (13.64, 11.30, 3.110), 'cyan', glow=('north',), group='Green front card reader')
    for y in (10.92, 11.52, 12.12):
        fascia('Green reader indicator '+str(y), (14.40, y, 3.12),
             (14.58, y+.18, 3.28), 'white', glow=('north',), group='Green front card reader')
    fascia('Small reader plate lower slot', (14.19, 9.47, 3.89),
         (14.95, 9.84, 4.02), 'charcoal', group='Green front card reader')

    # The inclined screen's solid support follows the 45-degree display. Its
    # front is slightly behind the bezel's rear plane at every height; no empty
    # triangular gap appears beside or behind the screen in side views.
    cube('Touch slider structural undertray', (-.50, 15.44, 1.57),
         (16.50, 16.66, 7.23), 'charcoal', group='Inclined screen enclosure')
    for row in range(17):
        y0 = 16.13+row*.40
        y1 = y0+.40
        front = y0-13.45
        cube('Solid display support course %02d'%row, (.06, y0, front),
             (15.94, y1, 12.77), 'black', group='Inclined screen enclosure')
    cube('Inclined display rear electronics', (.07, 19.14, 10.76),
         (15.93, 23.94, 15.47), 'black', group='Inclined screen enclosure')
    for side, x0, x1 in (('Left', -.73, .76), ('Right', 15.24, 16.73)):
        for row in range(9):
            y0 = 16.03+row*.78
            front = y0-13.48
            cube(side+' white sloped shoulder %02d'%row, (x0, y0, front),
                 (x1, y0+.78, 15.50), 'white', group='White side cheeks')
        cube(side+' upper rear side continuation', (x0, 23.03, 9.56),
             (x1, 23.94, 15.49), 'white', group='White side cheeks')
        a, b = (x1+.015, x1+.065) if side == 'Right' else (x0-.065, x0-.015)
        cube(side+' recessed transport handle surround', (a, 10.77, 11.60),
             (b, 11.61, 13.39), 'steel', group='Side cabinet details')
        cube(side+' transport handle dark inset', (a, 10.96, 11.83),
             (b, 11.39, 13.16), 'rubber', group='Side cabinet details')
        for y, z in ((4.01, 14.76), (14.72, 14.76), (21.99, 14.76)):
            cube(side+' side fixing '+str(y), (a, y, z),
                 (b, y+.15, z+.15), 'steel', group='Side cabinet details')

    cube('Rear lower access-panel gasket', (.58, 4.09, 15.55),
         (15.42, 14.98, 15.65), 'rim_gray', group='Rear service panels')
    cube('Rear white lower access panel', (.75, 4.27, 15.63),
         (15.25, 14.80, 15.71), 'ivory', group='Rear service panels')
    cube('Rear lower cooling grille', (4.77, 5.20, 15.715),
         (11.23, 7.88, 15.76), 'vent', group='Ventilation')
    cube('Rear upper display cooling grille', (5.29, 20.31, 15.475),
         (10.71, 22.93, 15.53), 'vent', group='Ventilation')
    cube('Rear mains inlet plate', (11.74, 4.53, 15.735),
         (14.20, 5.87, 15.80), 'steel', group='Rear service panels')
    cube('Rear mains socket', (12.40, 4.85, 15.80),
         (13.55, 5.48, 15.85), 'rubber', group='Rear service panels')
    for x in (1.02, 14.82):
        for y in (4.61, 14.42):
            cube('Rear access screw '+str((x, y)), (x, y, 15.72),
                 (x+.15, y+.15, 15.79), 'steel', group='Rear service panels')
