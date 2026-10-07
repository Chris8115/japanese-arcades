"""MUSECA's reclining monitor, faceted paper marquee and five-disc deck."""
import math
from PIL import Image


def build_upper(cube, polygon, art_dir):
    # Front-view source coordinates; the exporter mirrors X once for Java UVs.
    pivot = (8, 20, 3.6)
    recline = ('x', 22.5, pivot)
    bezel_uv = [.25, .25, 7.75, 7.75]

    cube('Reclining monitor black enclosure', (.05, 19.5, 3.92),
         (15.95, 43.15, 6.52), 'black', rotation=recline, group='Portrait enclosure')
    cube('Monitor white printed geometric fascia', (.27, 19.7, 3.65),
         (15.73, 43.25, 3.94), 'white', rotation=recline,
         north=('details', bezel_uv), group='Printed monitor frame')
    cube('Display inset charcoal gasket', (1.83, 20.70, 3.515),
         (14.17, 41.85, 3.75), 'rubber', rotation=recline, group='Portrait display')
    source = Image.open(art_dir/'display-artwork-source.png')
    screen_width = 11.75
    screen_height = screen_width * source.height/source.width
    assert 19.5 < screen_height < 22.0, 'Expected portrait 9:16 screen artwork'
    cube('MUSECA illuminated character title screen', (8-screen_width/2, 20.99, 3.435),
         (8+screen_width/2, 20.99+screen_height, 3.58), 'black', rotation=recline,
         north=('display', [0, 0, 16, 16]), glow=('north',), group='Portrait display')

    # Unequal black slashes and white returns are actual layers around the print.
    for side, points in (
        ('Left', [(-.13, 21.1), (.58, 21.1), (1.42, 42.1), (.07, 43.34), (-.48, 43.34)]),
        ('Right', [(14.56, 20.10), (15.33, 20.10), (16.15, 43.03), (15.2, 42.80)]),
    ):
        polygon(side+' angular black frame slash', points, 3.32, 3.64, 'black',
                rotation=recline, group='Asymmetric monitor trim', step=.3)
    polygon('Lower white folded screen rail', [(.24,19.42),(15.81,19.42),
            (15.66,20.75),(2.80,20.75)], 3.13, 3.53, 'white',
            front=('details',[.25,8.25,15.75,11.75]), rotation=recline,
            group='Printed monitor frame', step=.25)
    for x in (.60,15.35):
        for y in (20.1,29.6,41.9):
            cube('Monitor frame fixing '+str((x,y)),(x-.065,y,3.30),
                 (x+.065,y+.13,3.48),'silver',rotation=recline,group='Monitor fasteners')
    cube('Small screen lower warning plate',(6.53,20.64,3.39),(9.47,20.83,3.55),
         'ivory',rotation=recline,group='Monitor fasteners')

    # Compact square speaker boxes sit outside the lower display shoulders.
    for side, x0, x1 in (('Left',-2.40,.92),('Right',15.08,18.40)):
        rot=('y', -22.5 if side=='Left' else 22.5, ((x0+x1)/2,21.83,3.03))
        cube(side+' black speaker cabinet',(x0,20.06,2.37),(x1,23.58,4.23),
             'black',rotation=rot,group='Side speakers')
        cube(side+' silver speaker front edge',(x0+.10,20.16,2.265),(x1-.10,23.48,2.43),
             'steel',rotation=rot,group='Side speakers')
        cube(side+' mesh grille with geometric lines',(x0+.19,20.25,2.195),(x1-.19,23.39,2.30),
             'black',north=('details',[.25,12.25,3.75,15.75]),rotation=rot,group='Side speakers')
        for x in (x0+.28,x1-.42):
            for y in (20.40,23.10):
                cube(side+' speaker screw '+str((x,y)),(x,y,2.16),(x+.12,y+.12,2.25),
                     'silver',rotation=rot,group='Speaker fixings')

    # Rear support fills the space behind the reclining screen without making
    # a full-height rectangular body visible beside its narrow front frame.
    cube('Monitor continuous lower mounting collar',(1.0,17.65,3.25),(15.0,19.12,15.10),
         'black',group='Rear monitor spine')
    for i in range(24):
        y0=18.9+i*.94
        front=4.47+(y0-20)*math.tan(math.radians(22.5))
        if front < 15.40:
            cube('Monitor rear tapered spine course %02d'%i,(1.35,y0,front),
                 (14.65,y0+.94,15.40),'black',group='Rear monitor spine')
    cube('Rear upright access door',(2.00,21.0,15.43),(14.00,40.7,15.57),
         'charcoal',group='Rear access')
    for y in (23.0,36.0):
        cube('Rear monitor cooling grille '+str(y),(5.0,y,15.59),(11.0,y+1.75,15.70),
             'vent',group='Rear access')
    for x in (2.25,13.60):
        for y in (21.35,40.25):
            cube('Rear monitor door fixing '+str((x,y)),(x,y,15.58),
                 (x+.14,y+.14,15.73),'silver',group='Rear access')

    # Asymmetric header: character artwork is mounted behind the long white
    # wordmark. Folded facets then extend out from both edges of the backing.
    art_width=10.30
    source=Image.open(art_dir/'marquee-artwork-source.png')
    art_height=art_width*source.height/source.width
    art_top=49.90
    art_bottom=art_top-art_height
    outline=[(3.60,art_bottom+.16),(3.60,art_top-1.10),(5.7,art_top-.55),
             (9.25,art_top),(11.82,art_top-.45),(13.90,art_top-1.15),
             (13.90,art_bottom+.4),(11.5,art_bottom)]
    polygon('Cut character marquee printed backing',outline,3.00,3.28,'white',
            front=('marquee',[0,0,16,16]),rotation=recline,
            group='Character marquee',step=.25)
    polygon('Left origami illustration extension',[(-.4,44.25),(-.4,47.40),
            (1.95,49.1),(3.2,48.45),(6.15,49.4),(6.15,44.25)],4.27,4.51,'white',
            front=('marquee',[0,0,6,16]),rotation=recline,
            group='Character marquee',step=.25)
    for x in (2.1,13.2):
        cube('Marquee rear metal mounting tab '+str(x),(x,42.1,5.10),(x+.50,48.55,5.39),
             'black',rotation=recline,group='Marquee structure')
    cube('Character panel rear mounting cross rail',(2.10,46.65,4.93),(13.70,47.0,5.29),
         'black',rotation=recline,group='Marquee structure')
    for x in (4.8,11.8):
        cube('Printed character panel folded attachment '+str(x),(x,46.64,3.17),
             (x+.60,47.02,5.31),'white',rotation=recline,group='Marquee structure')
    for x in (1.0,14.0):
        cube('Logo board mounting return '+str(x),(x,42.40,3.20),
             (x+.50,44.10,5.22),'white',rotation=recline,group='Marquee structure')

    sign=[(-.65,42.68),(16.20,42.68),(17.2,45.10),(13.0,44.95),
          (12.6,46.10),(-.65,46.10)]
    polygon('Asymmetric marquee white wordmark board',sign,2.91,3.37,'white',
            rotation=recline,group='MUSECA wordmark board',step=.25)
    cube('Thin angular MUSECA wordmark',(0.04,42.86,2.835),(14.95,45.82,2.995),
         'white',north=('branding',[.125,.5,15.875,13]),rotation=recline,
         glow=('north',),group='MUSECA wordmark board')

    # These are independently tilted, thick paper facets, not a flat topper.
    # The production cabinet has a red folded-paper cluster on this corner,
    # descending beside the wordmark, rather than a long amber light bar.
    polygon('Left red folded marquee reverse',[(-1.42,40.55),(-2.0,44.45),
            (-.35,47.30),(1.68,43.68),(.88,40.35)],10.9,11.35,'red',
            rotation=('y',-22.5,(-.2,44.8,11.1)),group='Origami folds',step=.25)
    polygon('Left red pointed crown facet',[(-1.40,44.48),(-.20,47.30),
            (1.75,44.45)],10.25,10.49,'red',
            rotation=('y',-22.5,(.15,45.5,10.37)),group='Origami folds',step=.25)
    polygon('Left red broad folded front facet',[(-1.87,43.10),(-1.24,45.56),
            (.43,44.80),(1.16,41.14),(-.55,40.02)],10.53,10.77,'red',
            rotation=('y',22.5,(.15,44.7,10.65)),group='Origami folds',step=.25)
    polygon('Left paper fold narrow white crease',[(-1.25,45.59),(.43,44.85),
            (.45,44.73),(-1.28,45.47)],10.49,10.525,'ivory',
            rotation=('y',22.5,(.15,44.7,10.65)),group='Origami folds',step=.125)
    polygon('Right large silver paper facet',[(14.68,43.0),(18.91,45.40),
            (17.40,47.39),(14.70,46.88),(13.69,44.70)],11.43,11.72,'ivory',
            rotation=('y',-22.5,(15.4,45.1,11.55)),group='Origami folds',step=.25)
    polygon('Right white folded front facet',[(13.66,44.70),(17.28,43.80),
            (18.90,45.38),(15.49,45.80)],10.48,10.71,'white',
            rotation=('y',22.5,(15.5,44.7,10.6)),group='Origami folds',step=.25)
    polygon('Right red triangular paper underside',[(14.22,41.3),(17.29,43.79),
            (13.72,44.70)],10.40,10.67,'red',
            rotation=('y',22.5,(15.0,43.3,10.55)),group='Origami folds',step=.25)
    polygon('Lower right trailing origami shard',[(15.57,37.00),(18.25,39.52),
            (15.2,41.3),(17.87,41.9),(15.35,42.1)],8.58,8.91,'white',
            rotation=('y',-22.5,(16.3,40,8.75)),group='Origami folds',step=.25)
    polygon('Lower shard grey fold',[(15.58,37.05),(17.10,39.01),(15.21,41.15)],
            8.49,8.67,'rim_gray',rotation=('y',22.5,(16.1,39.5,8.58)),
            group='Origami folds',step=.25)
    # Fold returns connect the projecting origami faces back to the frame.
    # They are visible as thin paper planes from the side, not floating cutouts.
    cube('Left paper folded return',(.10,44.35,10.40),(1.05,44.62,13.26),
         'red',group='Origami folded returns')
    cube('Left lower red folded return',(.10,40.82,10.55),(.70,41.04,12.85),
         'red',group='Origami folded returns')
    cube('Right paper folded return',(13.35,44.15,10.10),(16.10,44.46,13.70),
         'white',group='Origami folded returns')
    cube('Lower trailing paper folded return',(15.05,39.85,8.53),(15.41,40.20,12.47),
         'white',group='Origami folded returns')
    cube('Lower trailing paper frame attachment',(14.81,39.82,11.75),
         (15.43,41.65,12.62),'white',group='Origami folded returns')

    # The planar deck, aligned hardware and radial spinners are generated in
    # museca_mesh_geometry.py. Keep the original printed front apron here.
    cube('White printed controller front apron',(-.30,17.20,-7.555),(16.30,17.95,-7.405),
         'white',north=('details',[.25,8.25,15.75,11.75]),group='Deck front trim')
