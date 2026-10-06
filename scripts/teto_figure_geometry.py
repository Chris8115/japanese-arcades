"""Kasane Teto shelf figure: stepped chibi hair, spiral drills and gray/pink dress."""
import math

from figure_geometry import FigureGeometry


COLORS = {
    'white': '#fff4e5', 'base': '#202933', 'base_edge': '#37434a',
    'teal': '#358c99', 'skin': '#f4ccb6', 'skin_light': '#ffe2ca',
    'skin_shadow': '#dfa392', 'blush': '#efb2b7',
    'hair': '#ce4165', 'hair_light': '#e56380', 'hair_bright': '#ef788d',
    'hair_red': '#b72e52', 'hair_shadow': '#8c2646', 'hair_deep': '#64273f',
    'eye_dark': '#603342', 'eye_red': '#d65378', 'eye_pink': '#f898b1',
    'eye_white': '#fff8ee', 'mouth': '#b57c84',
    'cloth': '#b4acac', 'cloth_light': '#d2c5c0', 'cloth_shadow': '#827e86',
    'pink': '#f05c88', 'pink_light': '#ff8aaa', 'pink_dark': '#b33360',
    'black': '#242430', 'black_light': '#383641', 'black_shadow': '#181b27',
    'silver': '#dbd2ce', 'bow_shadow': '#d5c5c4',
}


def build():
    g = FigureGeometry(COLORS)
    box, prism, face = g.box, g.prism, g.face

    g.group = 'Teto stepped display base'
    box('Teto plinth lower step', (2.5, 0, 3.5), (13.5, .73, 12.5), 'base')
    box('Teto plinth beveled-looking upper step', (2.75, .73, 3.75), (13.25, .96, 12.25), 'base_edge')
    box('Teto plinth teal front stripe', (2.73, .74, 3.475), (13.27, .91, 3.755), 'teal')
    box('Teto plinth teal left stripe', (2.725, .74, 3.76), (2.91, .91, 12.24), 'teal')
    box('Teto plinth teal right stripe', (13.09, .74, 3.76), (13.275, .91, 12.24), 'teal')
    g.decal('Teto nameplate', (5, .25, 11, .75), 3.48, 'nameplate')

    g.group = 'Teto boots and small legs'
    for i, x in enumerate((6.03, 8.69)):
        side = 'viewer right' if i == 0 else 'viewer left'
        box('Teto bare thigh ' + side, (x+.20, 3.11, 7.0), (x+1.10, 4.78, 8.41), 'skin')
        box('Teto thigh highlight ' + side, (x+.20, 3.50, 6.986), (x+.66, 4.46, 7.02), 'skin_light')
        box('Teto boot upright ' + side, (x+.09, 1.32, 6.75), (x+1.23, 3.41, 8.73), 'black')
        box('Teto boot outer panel ' + side, (x+.08, 1.51, 6.98), (x+.28, 3.05, 8.55), 'black_light')
        box('Teto thigh boot pink band ' + side, (x+.07, 3.16, 6.73), (x+1.25, 3.43, 8.75), 'pink_dark')
        box('Teto boot pink band face ' + side, (x+.12, 3.21, 6.704), (x+1.20, 3.39, 6.744), 'pink')
        box('Teto square boot toe ' + side, (x, 1.10, 5.96), (x+1.32, 1.91, 8.74), 'black_shadow')
        box('Teto toe upper leather ' + side, (x+.10, 1.89, 6.08), (x+1.20, 2.10, 7.30), 'black')
        box('Teto boot sole ' + side, (x-.05, .98, 5.91), (x+1.37, 1.15, 8.80), 'black_shadow')
        box('Teto pink toe inset ' + side, (x+.77, 1.18, 5.89), (x+1.17, 1.51, 5.968), 'pink_dark')
        box('Teto boot pink shin detail ' + side, (x+.46, 2.33, 6.716), (x+.77, 2.87, 6.757), 'pink')
        box('Teto boot silver tab ' + side, (x+.40, 2.85, 6.699), (x+.84, 3.02, 6.76), 'silver')

    g.group = 'Teto pleated skirt'
    count = 12
    for i in range(count):
        a, b = i*math.tau/count, (i+1)*math.tau/count
        # Broad alternating facets make deliberate pleats rather than voxel noise.
        def point(angle, y, rx, rz):
            return (8+rx*math.cos(angle), y, 7.95+rz*math.sin(angle))
        y = 4.37 - (.10 if i % 2 else 0)
        upper = [point(a, 5.89, 1.89, 1.12), point(b, 5.89, 1.89, 1.12)]
        lower = [point(a, y, 2.58, 1.72), point(b, y, 2.58, 1.72)]
        face('Teto skirt pleat %02d' % i, [upper[0], upper[1], lower[1], lower[0]], 'black' if i % 2 else 'black_light')
        hem_top = [point(a, y+.22, 2.51, 1.68), point(b, y+.22, 2.51, 1.68)]
        face('Teto skirt pink hem %02d' % i, [hem_top[0], hem_top[1], lower[1], lower[0]], 'pink')
        face('Teto skirt underside %02d' % i, [(8, 4.28, 7.95), lower[0], lower[1]], 'black_shadow')
    box('Teto skirt waistband', (6.05, 5.60, 6.72), (9.95, 6.02, 9.13), 'black_shadow')

    g.group = 'Teto gray pink trimmed tunic'
    prism('Teto flared gray tunic body', [(5.88, 5.63), (10.12, 5.63), (9.51, 8.89), (6.49, 8.89)], 6.48, 9.22, 'cloth_shadow')
    prism('Teto light gray front tunic', [(5.98, 5.49), (7.34, 5.38), (8, 5.61), (8.66, 5.38), (10.02, 5.49),
          (9.34, 8.65), (8.52, 9.01), (7.48, 9.01), (6.66, 8.65)], 6.43, 6.55, 'cloth')
    prism('Teto tunic left front tail', [(6.06, 5.33), (7.31, 5.18), (7.45, 6.55), (6.43, 6.80)], 6.373, 6.48, 'cloth_light')
    prism('Teto tunic right front tail', [(8.69, 5.18), (9.94, 5.33), (9.57, 6.80), (8.55, 6.55)], 6.373, 6.48, 'cloth_light')
    box('Teto central pink button placket', (7.83, 5.58, 6.346), (8.17, 8.60, 6.454), 'pink_dark')
    for i in range(5):
        y = 5.99 + i*.46
        box('Teto front button %d' % i, (7.905, y, 6.30), (8.095, y+.17, 6.367), 'pink_light')
    for i, x in enumerate((7.10, 8.68)):
        box('Teto vertical dress pink piping %d' % i, (x, 5.64, 6.354), (x+.18, 8.38, 6.462), 'pink')
        box('Teto waist short pocket %d' % i, (x-.23, 6.73, 6.307), (x+.45, 6.92, 6.386), 'cloth_shadow')
    box('Teto neck', (7.26, 8.76, 7.10), (8.74, 9.79, 8.53), 'skin')
    prism('Teto left collar', [(6.90, 8.73), (7.40, 8.37), (7.98, 8.70), (7.29, 9.06)], 6.39, 6.51, 'cloth_light')
    prism('Teto right collar', [(8.02, 8.70), (8.60, 8.37), (9.10, 8.73), (8.71, 9.06)], 6.39, 6.51, 'cloth_light')
    box('Teto high collar pink knot', (7.82, 8.50, 6.297), (8.18, 8.91, 6.442), 'pink')
    box('Teto back center seam', (7.88, 5.91, 9.218), (8.12, 8.65, 9.262), 'pink_dark')
    box('Teto back small collar panel', (7.26, 8.10, 9.236), (8.74, 8.78, 9.28), 'cloth_light')
    for i in range(3):box('Teto back collar tiny mark %d' % i, (7.48+i*.32, 8.40, 9.279), (7.64+i*.32, 8.61, 9.306), 'pink')

    g.group = 'Teto outstretched detached sleeves'
    for sign, side in ((-1, 'model left'), (1, 'model right')):
        start = len(g.faces)
        x0 = 8+sign*1.98
        box('Teto bare upper arm '+side, (-.42, -1.40, 7.04), (.42, -.04, 8.31), 'skin')
        box('Teto arm skin light '+side, (-.40, -1.24, 7.00), (.08, -.15, 7.075), 'skin_light')
        prism('Teto flared detached black sleeve '+side, [(-.73, -3.02), (.73, -3.02), (.53, -1.25), (-.53, -1.25)], 6.79, 8.47, 'black')
        box('Teto sleeve pink upper band '+side, (-.56, -1.58, 6.767), (.56, -1.31, 8.49), 'pink_dark')
        box('Teto sleeve pink upper face '+side, (-.54, -1.51, 6.735), (.54, -1.32, 6.792), 'pink')
        box('Teto sleeve broad pink cuff '+side, (-.75, -3.08, 6.752), (.75, -2.81, 8.50), 'pink')
        box('Teto sleeve front black inset '+side, (-.42, -2.70, 6.765), (.43, -1.71, 6.805), 'black_shadow')
        box('Teto sleeve narrow gray stitched stripe '+side, (-.31, -2.62, 6.732), (-.19, -1.83, 6.779), 'black_light')
        box('Teto little uncovered hand '+side, (-.40, -3.37, 6.97), (.43, -3.02, 8.19), 'skin_light')
        a = math.radians(sign*23)
        g.transform(start, lambda x,y,z,a=a,x0=x0: (x0+x*math.cos(a)-y*math.sin(a), 8.65+x*math.sin(a)+y*math.cos(a), z))

    g.group = 'Teto oversized pixel head'
    box('Teto main skin head', (5.32, 9.52, 5.26), (10.68, 12.70, 9.89), 'skin')
    face('Teto flat pale face', [(5.32,12.70,5.258),(10.68,12.70,5.258),
         (10.68,9.52,5.258),(5.32,9.52,5.258)], 'skin_light')
    box('Teto chin step', (5.72, 9.37, 5.39), (10.28, 9.66, 9.36), 'skin')
    box('Teto hair rear mass', (5.08, 9.66, 8.87), (10.92, 13.49, 10.60), 'hair_red')
    box('Teto hair crown volume', (5.08, 12.30, 5.17), (10.92, 13.63, 10.38), 'hair')
    box('Teto raised crown tier', (5.52, 13.55, 5.61), (10.48, 13.91, 10.10), 'hair_light')
    box('Teto upper crown step', (6.09, 13.86, 6.09), (9.91, 14.09, 9.74), 'hair')
    # A continuous backing and abutting front locks avoid coplanar overlaps,
    # which appear as black rectangles in the native/studio render.
    box('Teto continuous forehead hair backing', (5.09,11.75,5.035), (10.91,13.64,5.39), 'hair')
    bangs = ((5.09,10.18,13.20,'hair_red'), (5.65,11.41,13.53,'hair'),
            (6.30,11.78,13.77,'hair_light'), (7.02,11.28,13.88,'hair'),
            (7.73,10.98,13.97,'hair_light'), (8.46,11.77,13.85,'hair_bright'),
            (9.18,11.39,13.68,'hair'), (9.88,10.12,13.37,'hair_red'))
    for i, (x, low, high, mat) in enumerate(bangs):
        edge = bangs[i+1][0] if i+1<len(bangs) else 10.91
        box('Teto deliberate stepped bang %d' % i, (x,low,4.987), (edge,high,5.42), mat)
    box('Teto left cheek length hair', (4.96, 9.73, 5.43), (5.46, 12.69, 8.92), 'hair_red')
    box('Teto right cheek length hair', (10.54, 9.73, 5.43), (11.04, 12.69, 8.92), 'hair_red')
    for i, x in enumerate((5.62, 6.51, 7.40, 8.29, 9.18)):
        box('Teto back grouped hair lock %d' % i, (x,9.60+(i%2)*.16,10.572), (x+.87,13.34-(i%2)*.24,10.77), 'hair' if i%2 else 'hair_light')
    box('Teto lower back hair rim', (5.51, 9.49, 8.92), (10.49, 9.73, 10.50), 'hair_shadow')

    g.group = 'Teto readable pixel face'
    def painted_pixel(name, x0, y0, x1, y1, material):
        # All expression pixels share one drawing plane, a hair's breadth
        # above the skin. No raised frames, lips, nose or stacked pupils.
        face(name, [(x0,y1,5.255),(x1,y1,5.255),
             (x1,y0,5.255),(x0,y0,5.255)], material)

    pixels = [' LLLLL ', ' WRRRR ', ' WHDDR ', ' WRDDR ',
              ' WRRII ', ' WIIII ', '  III  ']
    palette = {'L':'eye_dark', 'W':'eye_white', 'H':'eye_white',
               'R':'eye_red', 'D':'eye_dark', 'I':'eye_pink'}
    for i, center in enumerate((6.66,9.34)):
        for row, line in enumerate(pixels):
            for column, pixel in enumerate(line):
                if pixel == ' ':continue
                x0 = center+(column-3.5)*.18
                y1 = 11.53-row*.20
                painted_pixel('Teto eye %d painted pixel %d %d'%(i,row,column),
                              x0,y1-.20,x0+.18,y1,palette[pixel])
    for i, x in enumerate((5.70,9.83)):
        painted_pixel('Teto subtle painted cheek %d'%i,x,9.96,x+.47,10.10,'blush')
    painted_pixel('Teto tiny painted mouth',7.86,9.81,8.14,9.88,'mouth')

    g.group = 'Teto true spiral drill twin tails'
    for side, cx, chirality in (('left',3.68,1),('right',12.32,-1)):
        # A filled pink octagonal hair mass supports chunky descending curls.
        # Short shoulders in the taper give the drill a deliberate tiered shape;
        # exposed material between turns is a shallow groove, never an opening.
        tiers = [(13.31,1.06),(12.82,1.02),(12.29,.94),(12.15,.88),
                 (11.36,.78),(11.20,.70),(10.38,.61),(10.20,.53),
                 (9.38,.39),(9.20,.31),(8.31,.13)]
        for tier, ((y0,r0),(y1,r1)) in enumerate(zip(tiers,tiers[1:])):
            for i in range(8):
                a,b=i*math.tau/8,(i+1)*math.tau/8
                face('Teto %s drill solid stepped hair core %d %d'%(side,tier,i),[(cx+r0*math.cos(a),y0,8.76+r0*math.sin(a)),
                     (cx+r0*math.cos(b),y0,8.76+r0*math.sin(b)),(cx+r1*math.cos(b),y1,8.76+r1*math.sin(b)),
                     (cx+r1*math.cos(a),y1,8.76+r1*math.sin(a))], 'hair' if i in (4,5,6) else 'hair_red')
        for end, (y,r), upward in (('top',tiers[0],True),('tip',tiers[-1],False)):
            for i in range(8):
                a,b=i*math.tau/8,(i+1)*math.tau/8
                points=[(cx,y,8.76),(cx+r*math.cos(b),y,8.76+r*math.sin(b)),(cx+r*math.cos(a),y,8.76+r*math.sin(a))]
                if not upward:points.reverse()
                face('Teto %s drill filled %s cap %d'%(side,end,i),points,'hair_light' if upward else 'hair_red')
        sections=[];steps=32
        for i in range(steps+1):
            t=i/steps;a=chirality*(i*math.pi/4)+.22
            r=1.03*(1-t)+.21*t;y=12.87-4.37*t
            halfwidth=.24*(1-t)+.11*t;halfheight=.44*(1-t)+.24*t
            # Cross section is outer-bottom, inner-bottom, inner-top, outer-top.
            sections.append([(cx+(r+dr)*math.cos(a),y+dy,8.76+(r+dr)*math.sin(a))
                             for dr,dy in ((halfwidth,-halfheight),(-halfwidth,-halfheight),(-halfwidth,halfheight),(halfwidth,halfheight))])
        for i in range(steps):
            a,b=sections[i],sections[i+1]
            front=math.sin(chirality*(i+.5)*math.pi/4+.22)<-.15
            for j in range(4):
                points=[a[j],b[j],b[(j+1)%4],a[(j+1)%4]]
                if chirality<0:points.reverse()
                mat='hair_light' if j==2 else ('hair' if front else 'hair_red')
                if j==0:mat='hair_red'
                face('Teto %s continuous drill turn %02d surface %d'%(side,i,j),points,mat)
        first,last=sections[0],list(reversed(sections[-1]))
        if chirality<0:first=list(reversed(first));last=list(reversed(last))
        face('Teto '+side+' drill top end cap',first,'hair')
        face('Teto '+side+' drill tapered tip cap',last,'hair_red')
        # Connector is behind the temple, joining the drill to the head.
        xlo,xhi=(4.33,5.40) if side=='left' else (10.60,11.67)
        box('Teto '+side+' tied hair root',(xlo,12.15,7.82),(xhi,13.29,9.31),'hair_red')

    g.group = 'Teto cream white hair bows'
    for side, cx in (('left',4.64),('right',11.36)):
        start=len(g.faces)
        prism('Teto '+side+' bow left folded wing',[(-1.0,13.56),(-.14,13.75),(-.14,14.07),(-.86,14.58)],7.07,7.48,'white')
        prism('Teto '+side+' bow right folded wing',[(.14,13.75),(1.0,13.56),(.86,14.58),(.14,14.07)],7.07,7.48,'white')
        box('Teto '+side+' bow central knot',(-.21,13.66,6.984),(.21,14.21,7.55),'bow_shadow')
        box('Teto '+side+' bow bright knot face',(-.15,13.72,6.954),(.15,14.14,7.014),'white')
        prism('Teto '+side+' bow ribbon end',[(-.07,13.87),(.26,13.60),(.37,13.12),(.00,13.28)],7.05,7.40,'white')
        g.transform(start,lambda x,y,z,cx=cx:(x+cx,y,z))

    # A compact reference-style chibi silhouette. Keep the display base and
    # drill width fixed while making the face larger relative to the body.
    anchor, body_scale, head_scale = 9.37, .82, 1.10
    head_bottom = .96+(anchor-.96)*body_scale
    head_groups = {'Teto oversized pixel head', 'Teto readable pixel face',
                   'Teto cream white hair bows'}
    for mesh_face in g.faces:
        group = mesh_face['group']
        if group == 'Teto stepped display base':continue
        points = []
        for x,y,z in mesh_face['vertices']:
            if group == 'Teto oversized pixel head' and z < 5.26:
                z = 5.26+(z-5.26)*.30
            if group in head_groups:
                x = 8+(x-8)*head_scale
                y = head_bottom+(y-anchor)*head_scale
            elif group == 'Teto true spiral drill twin tails':
                y = head_bottom+(y-anchor)*head_scale
            else:
                x = 8+(x-8)*.95
                y = .96+(y-.96)*body_scale
            points.append([x,y,z])
        mesh_face['vertices'] = points

    return g
