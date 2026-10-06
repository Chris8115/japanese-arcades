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

    # A narrow prismatic indicator on the left is separate from the LCD bezel.
    polygon('Left side illuminated shard', [(-.87,34.0),(-.20,33.45),
            (.45,39.54),(-.63,41.60)], 3.12,3.43,'amber',
            rotation=recline,glow=('north',),group='Monitor side light',step=.25)
    polygon('Side light ivory seam', [(-.73,34.25),(-.57,34.13),
            (.29,39.38),(.12,39.43)],3.065,3.145,'white',
            rotation=recline,glow=('north',),group='Monitor side light',step=.25)

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
    polygon('Left red folded marquee reverse',[(-1.42,42.0),(-2.0,44.45),
            (-.35,47.30),(1.68,43.68)],10.9,11.35,'red',
            rotation=('y',-22.5,(-.2,44.8,11.1)),group='Origami folds',step=.25)
    polygon('Left white folded paper plane',[(-1.87,44.35),(.58,46.97),
            (2.39,45.35),(.14,42.55)],10.53,10.77,'white',
            rotation=('y',22.5,(.15,44.7,10.65)),group='Origami folds',step=.25)
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
         'white',group='Origami folded returns')
    cube('Right paper folded return',(13.35,44.15,10.10),(16.10,44.46,13.70),
         'white',group='Origami folded returns')
    cube('Lower trailing paper folded return',(15.05,39.85,8.53),(15.41,40.20,12.47),
         'white',group='Origami folded returns')
    cube('Lower trailing paper frame attachment',(14.81,39.82,11.75),
         (15.43,41.65,12.62),'white',group='Origami folded returns')

    # The real deck rises gently toward the display. Native stepped courses
    # preserve that shallow rake without forcing a steeper legal cube angle.
    deck=[(-1.55,3.45),(17.55,3.45),(18.6,-4.90),(16.30,-7.50),
          (-.30,-7.50),(-2.6,-4.90)]  # X,Z footprint, clipped front corners.
    def deck_y(z): return 18.07+(z+7.50)*.145
    count=24
    for i in range(count):
        z0=-7.50+i*10.95/count
        z1=-7.50+(i+1)*10.95/count
        mid=(z0+z1)/2
        crossings=[]
        for a,b in zip(deck,deck[1:]+deck[:1]):
            if min(a[1],b[1])<=mid<max(a[1],b[1]):
                crossings.append(a[0]+(b[0]-a[0])*(mid-a[1])/(b[1]-a[1]))
        left,right=min(crossings),max(crossings)
        top=deck_y(mid)
        u0=8.25+(left+2.6)/21.2*7.5
        u1=8.25+(right+2.6)/21.2*7.5
        v0=.25+(z0+7.50)/10.95*7.5
        v1=.25+(z1+7.50)/10.95*7.5
        cube('Angled deck black undertray course %02d'%i,(left,top-.87,z0),(right,top-.17,z1),
             'black',group='Five-spinner deck')
        cube('Deck geometric printed top course %02d'%i,(left-.015,top-.17,z0),
             (right+.015,top,z1),'white',
             up=('details',[u0,v0,u1,v1]),
             north=('details',[u1,v0,u0,v0+.03125]),
             south=('details',[u0,v1-.03125,u1,v1]),
             group='Five-spinner deck')
    for i in range(4):
        z0=1.65+i*.55
        z1=z0+.55
        cube('Rear deck concealed support course '+str(i),(0,17.78,z0),
             (16,deck_y((z0+z1)/2)-.19,z1),'black',group='Deck support')
    cube('White printed controller front apron',(-.30,17.20,-7.555),(16.30,17.95,-7.405),
         'white',north=('details',[.25,8.25,15.75,11.75]),group='Deck front trim')
    cube('Center small rear function button',(7.47,19.67,2.44),(8.53,19.89,3.19),
         'charcoal',group='Deck hardware')
    cube('Rear function button silver cap',(7.60,19.89,2.56),(8.40,20.03,3.05),
         'silver',group='Deck hardware')
    for x,z in ((-1.0,-4.9),(17.0,-4.9),(.9,-6.93),(15.1,-6.93),(.1,2.9),(15.9,2.9)):
        y=deck_y(z)
        cube('Deck countersunk screw '+str((x,z)),(x-.075,y+.01,z-.075),
             (x+.075,y+.055,z+.075),'steel',group='Deck hardware')

    def drum(name,cx,cz,radius,y0,y1,material,glow=False):
        rows=math.ceil(radius*2/.25)
        for j in range(rows):
            z0=cz-radius+j*2*radius/rows
            z1=cz-radius+(j+1)*2*radius/rows
            zm=(z0+z1)/2
            half=math.sqrt(max(0,radius*radius-(zm-cz)**2))
            lo=round((cx-half)*4)/4
            hi=round((cx+half)*4)/4
            if hi<=lo: continue
            cube(name+' slice %02d'%j,(lo,deck_y(zm)+y0,z0),(hi,deck_y(zm)+y1,z1),
                 material,glow=glow,group='Five luminous spinners')

    for i,(x,z) in enumerate(((2.50,.42),(8,.42),(13.50,.42),(5.15,-4.02),(10.85,-4.02)),1):
        stem='Spinner %d '%i
        drum(stem+'thin graphite gasket',x,z,1.96,.01,.16,'steel')
        drum(stem+'white outer bevel',x,z,1.91,.16,.35,'ivory')
        drum(stem+'opal illuminated body',x,z,1.76,.35,.71,'pink' if i in (3,5) else 'white',True)
        drum(stem+'white upper shoulder',x,z,1.56,.71,.88,'white',True)
        drum(stem+'frosted top face',x,z,1.36,.88,.98,'ivory')
        # Centre geometric diamond, with intersecting triangles visible from above.
        drum(stem+'center medallion',x,z,.60,.985,1.015,'rim_gray')
        for j,(dx,dz,w,d) in enumerate(((-.4,-.055,.80,.11),(-.055,-.4,.11,.80))):
            y=deck_y(z+dz+d/2)+1.017
            cube(stem+'inlaid center line '+str(j),(x+dx,y,z+dz),
                 (x+dx+w,y+.018,z+dz+d),'steel',group='Spinner center inlays')
        for k in range(5):
            o=-.35+k*.15
            y=deck_y(z+o)+1.016
            cube(stem+'diagonal emblem A '+str(k),(x+o-.055,y,z+o-.055),
                 (x+o+.055,y+.020,z+o+.055),'white',group='Spinner center inlays')
            cube(stem+'diagonal emblem B '+str(k),(x-o-.055,y,z+o-.055),
                 (x-o+.055,y+.020,z+o+.055),'white',group='Spinner center inlays')
