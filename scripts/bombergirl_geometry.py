"""Compact Bombergirl Rainbow cabinet, in Minecraft pixels, facing north (-Z).

The two screens, single detonation button, left joystick, clipped white monitor
surround, chevron light columns and acrylic topper follow Konami cabinet photos.
Printed detail remains texture detail. All polygons are planar triangles/quads.
"""
import math
from initial_d_geometry import Geometry
from popn_music_geometry import _face, _surface

COLORS = {
    'white':'#eeeeed', 'silver':'#b5bdc3', 'black':'#12151a', 'dark':'#252a30',
    'cyan':'#61e7df', 'orange':'#ffb534', 'yellow':'#ffe579', 'red':'#e81739',
    'blue':'#35a3e9', 'green':'#6ddca2', 'cream':'#fff7de', 'glass':'#182734',
    'pink':'#ef69bc', 'chrome':'#e6e9eb', 'charcoal':'#454d54', 'gray':'#77818a',
}

def plate(g,name,outline,z0,z1,material='white',texture=None,rect=None,glow=False):
    """Convex silhouette with a single affine print, no coplanar overlay."""
    cx=sum(x for x,y in outline)/len(outline);cy=sum(y for x,y in outline)/len(outline)
    if rect is None: rect=(min(x for x,y in outline),min(y for x,y in outline),max(x for x,y in outline),max(y for x,y in outline))
    x0,y0,x1,y1=rect
    def uv(x,y):return ((x1-x)/(x1-x0)*16,(y1-y)/(y1-y0)*16)
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        pts=[(cx,cy,z0),(*p,z0),(*q,z0)]
        _face(g,name+f' face{i}',pts,material,texture or 'materials',[uv(x,y) for x,y,z in pts] if texture else None,normal=(0,0,-1),glow=glow)
        _face(g,name+f' back{i}',[(cx,cy,z1),(*q,z1),(*p,z1)],material,normal=(0,0,1))
        _face(g,name+f' edge{i}',[(*p,z0),(*q,z0),(*q,z1),(*p,z1)],material,normal=(p[0]-cx,p[1]-cy,0))

def deck_y(z):return 14.25+.115*z

def deck_patch(g,name,x0,z0,x1,z1,texture,offset=.01,rect=(0,0,16,16),glow=False):
    _surface(g,name,[(x1,deck_y(z1)+offset,z1),(x1,deck_y(z0)+offset,z0),(x0,deck_y(z0)+offset,z0),(x0,deck_y(z1)+offset,z1)],texture,rect,normal=(0,1,-.115),glow=glow)

def lathe(g,name,cx,cz,profile,mats,segments=24):
    """Open underside: hidden joins do not create an extra bottom disk."""
    for j,((r,y),(R,Y)) in enumerate(zip(profile,profile[1:])):
        for i in range(segments):
            a,b=math.tau*i/segments,math.tau*(i+1)/segments
            def p(rad,t,h):return(cx+rad*math.cos(t),h,cz+rad*math.sin(t))
            if r==0:pts=[(cx,y,cz),p(R,a,Y),p(R,b,Y)]
            elif R==0:pts=[p(r,a,y),(cx,Y,cz),p(r,b,y)]
            else:pts=[p(r,a,y),p(R,a,Y),p(R,b,Y),p(r,b,y)]
            _face(g,f'{name} band{j} sector{i}',pts,mats[min(j,len(mats)-1)],normal=(math.cos((a+b)/2),.8,math.sin((a+b)/2)))

def screen_z(y):return 8.82+.09*(y-18.1)

def monitor_quad(g,name,points,texture=None,material='white',glow=False):
    pts=[(x,y,screen_z(y)) for x,y in points]
    uv=[((12.9-x)/9.8*16,(35-y)/17.7*16) for x,y in points] if texture else None
    _face(g,name,pts,material,texture or 'materials',uv,normal=(0,.09,-1),glow=glow)

def build():
    g=Geometry(COLORS)
    g.group='Steel plinth and service cabinet'
    # Small rubber feet and a silver projecting foot ledge are characteristic.
    for i,x in enumerate((1.7,14.3)):
        for j,z in enumerate((2.1,14.2)):
            lathe(g,f'Rubber foot {i}-{j}',x,z,[(.36,0),(.36,.32),(.29,.45),(0,.45)],['black'],12)
    g.box('Lower black plinth',(1.0,.35,2.0),(15.0,.8,15.2),'black')
    g.yz_shell('Silver foot ledge',.8,15.2,[(.65,.6),(1.12,.6),(1.52,2.25),(1.52,14.9),(.65,14.9)],'silver')
    g.box('Black lower case',(1.15,1.5,4.2),(14.85,14.6,15.1),'black')
    # Main door print occupies the face itself, separated from its frame.
    g.box('Service door silver rim',(1.55,2.05,4.06),(14.45,13.73,4.18),'silver')
    _surface(g,'Printed white service door',[(14.22,13.50,4.045),(14.22,2.28,4.045),(1.78,2.28,4.045),(1.78,13.50,4.045)],'front')
    # Recessed rear access panel and its ventilation remain one printed face.
    _surface(g,'Rear service panel',[(1.5,14.3,15.12),(1.5,2,15.12),(14.5,2,15.12),(14.5,14.3,15.12)],'rear',normal=(0,0,1))
    for side,x,out in [('left',14.86,1),('right',1.14,-1)]:
        z0,z1=(14.9,4.3) if out>0 else (4.3,14.9)
        _surface(g,'Lower '+side+' side graphic',[(x,14.55,z0),(x,1.55,z0),(x,1.55,z1),(x,14.55,z1)],'side',normal=(out,0,0))
    g.box('Rear upright core',(3.0,14.4,12.1),(13.0,35.9,15.25),'black')
    g.box('Rear white spine',(3.25,15.0,15.25),(12.75,35.6,15.5),'white')
    _surface(g,'Upper rear ventilation',[(4.1,32.1,15.51),(4.1,18.2,15.51),(11.9,18.2,15.51),(11.9,32.1,15.51)],'rear',normal=(0,0,1))

    g.group='Low dual-screen control deck'
    outline=[(.2,1.15),(.9,.45),(15.1,.45),(15.8,1.15),(15.8,10.85),(14.55,12.05),(1.45,12.05),(.2,10.85)]
    # Planar top fan; decals are in their own apertures in the common UV print.
    for i,(x,z) in enumerate(outline):
        X,Z=outline[(i+1)%len(outline)]
        def uv(x,z):return((15.8-x)/15.6*16,(12.05-z)/11.6*16)
        pts=[(8,deck_y(6),6),(x,deck_y(z),z),(X,deck_y(Z),Z)]
        _face(g,f'Deck top {i}',pts,texture='deck',uv=[uv(p[0],p[2]) for p in pts],normal=(0,1,-.115))
        for band,(low,high,mat) in enumerate([(-.22,0,'white'),(-1.15,-.22,'black')]):
            _face(g,f'Deck side {i}-{band}',[(x,deck_y(z)+low,z),(X,deck_y(Z)+low,Z),(X,deck_y(Z)+high,Z),(x,deck_y(z)+high,z)],mat,normal=(x-8,0,z-6))
        _face(g,f'Deck underside {i}',[(8,deck_y(6)-1.15,6),(X,deck_y(Z)-1.15,Z),(x,deck_y(z)-1.15,z)],'black',normal=(0,-1,.115))
    # Glass is flush above the printed deck without a duplicate deck image.
    deck_patch(g,'Horizontal touch display',2.85,2.55,11.45,8.35,'touch',.018,glow=True)
    # Actual left joystick (high X as seen from the north).
    g.box('Joystick angular black pedestal',(12.03,deck_y(2.9),2.8),(13.72,15.06,5.3),'black')
    lathe(g,'Joystick boot',12.85,4.12,[(.51,15.07),(.47,15.25),(.35,15.46),(.20,15.57)],['dark','charcoal','black'],20)
    lathe(g,'Joystick shaft',12.85,4.12,[(.135,15.45),(.135,16.42)],['gray'],16)
    lathe(g,'Joystick black ball',12.85,4.12,[(0,16.22),(.29,16.30),(.44,16.52),(.46,16.74),(.38,16.96),(.20,17.12),(0,17.17)],['black'],24)
    # Large detonator ring on the rear shelf; turned surfaces carry the shape.
    yy=deck_y(10)
    lathe(g,'Detonation button black ring',8,10,[(2.22,yy+.02),(2.22,yy+.12),(2.04,yy+.23),(1.62,yy+.23),(1.43,yy+.34),(1.09,yy+.34),(1.04,yy+.46)],['black','silver','black','dark','silver','black'],32)
    lathe(g,'Detonation red lens',8,10,[(1.01,yy+.42),(1.01,yy+.64),(.92,yy+.91),(.68,yy+1.09),(.32,yy+1.18),(0,yy+1.20)],['red'],32)
    # Printed ring uses UV mapping on a real annular surface.
    for i in range(32):
        a,b=math.tau*i/32,math.tau*(i+1)/32
        pts=[(8+r*math.cos(t),yy+.23,10+r*math.sin(t)) for r,t in [(2.04,a),(2.04,b),(1.62,b),(1.62,a)]]
        _face(g,f'Printed detonation ring{i}',pts,texture='button',uv=[(8+(p[0]-8)*16/4.1,8-(p[2]-10)*16/4.1) for p in pts],normal=(0,1,0))
    deck_patch(g,'Card reader contact pad',10.75,9.2,12.42,10.94,'details',.028,(0,0,8,8))
    deck_patch(g,'Coin slot labels',3.05,9.12,4.35,11.12,'details',.028,(8,0,16,8))
    g.box('Coin slot raised metal lip',(3.44,deck_y(10.2)+.04,9.48),(3.81,deck_y(10.2)+.19,10.74),'silver')
    g.box('Coin slot black opening',(3.55,deck_y(10.2)+.192,9.62),(3.69,deck_y(10.2)+.202,10.56),'black')

    g.group='Portrait display and white angular frame'
    # The exposed front frame is four planar bands, not overlapping slabs.
    outer=[(3.1,17.3),(12.9,17.3),(12.9,33.9),(11.8,35.0),(10.2,35.0),(9.8,34.65),(6.2,34.65),(5.8,35.0),(4.2,35.0),(3.1,33.9)]
    # Black monitor box ends behind the open front surround.
    g.box('Portrait rear housing',(3.0,17.25,10.51),(13.0,34.6,12.13),'dark')
    # Trim quad bands, with upper sculpted silhouette tessellated in clean planes.
    monitor_quad(g,'Frame bottom',[(3.1,17.3),(12.9,17.3),(11.82,18.42),(4.18,18.42)],'bezel')
    monitor_quad(g,'Frame left',[(12.9,17.3),(12.9,33.9),(11.82,32.72),(11.82,18.42)],'bezel')
    monitor_quad(g,'Frame right',[(4.18,18.42),(4.18,32.72),(3.1,33.9),(3.1,17.3)],'bezel')
    upper=[(3.1,33.9),(4.2,35),(5.8,35),(6.2,34.65),(9.8,34.65),(10.2,35),(11.8,35),(12.9,33.9)]
    for i in range(len(upper)-1):
        p,q=upper[i],upper[i+1]
        lo=max(4.18,min(11.82,p[0]));hi=max(4.18,min(11.82,q[0]))
        pts=[p,q,(hi,32.72),(lo,32.72)]
        if lo==hi:pts=pts[:3]
        monitor_quad(g,f'Frame sculpted top {i}',pts,'bezel')
    for i,p in enumerate(outer):
        q=outer[(i+1)%len(outer)]
        _face(g,f'Monitor shell bevel {i}',[(p[0],p[1],screen_z(p[1])),(q[0],q[1],screen_z(q[1])),(q[0],q[1],12.15),(p[0],p[1],12.15)],'silver',normal=(p[0]-8,p[1]-26,0))
    # Narrow rubber gasket surrounds the physical 9:16 display aperture.
    for i,(pts) in enumerate([[(4.18,18.42),(11.82,18.42),(11.67,18.62),(4.33,18.62)],[(11.82,18.42),(11.82,32.72),(11.67,32.52),(11.67,18.62)],[(11.82,32.72),(4.18,32.72),(4.33,32.52),(11.67,32.52)],[(4.18,32.72),(4.18,18.42),(4.33,18.62),(4.33,32.52)]]):
        monitor_quad(g,f'Black glass gasket{i}',pts,material='black')
    _surface(g,'Portrait attract screen',[(11.67,32.52,screen_z(32.52)),(11.67,18.62,screen_z(18.62)),(4.33,18.62,screen_z(18.62)),(4.33,32.52,screen_z(32.52))],'screen',normal=(0,.09,-1),glow=True)

    g.group='Chevron lamps and speaker pods'
    for side,sgn in [('left',1),('right',-1)]:
        def sx(x):return 8+sgn*x
        pts=[(sx(x),y) for x,y in [(5.15,19.7),(7.25,21.1),(7.25,32.55),(6.1,34.0),(5.1,32.55)]]
        plate(g,side+' light black housing',pts,9.62,11.92,'black')
        pts=[(sx(x),y) for x,y in [(5.44,20.65),(6.93,21.55),(6.93,32.38),(6.12,33.48),(5.40,32.35)]]
        plate(g,side+' luminous light blade',pts,9.58,9.60,'white',texture='lights',glow=True)
        # Three physical dark chevrons segment the lighting, as on the cabinet.
        for j,y in enumerate((23.35,27.25,31.05)):
            p=[(sx(5.41),y+.85,9.545),(sx(6.95),y-.02,9.545),(sx(6.95),y+.28,9.545),(sx(5.41),y+1.18,9.545)]
            _face(g,side+f' dark chevron{j}',p,'black',normal=(0,0,-1))
        cx=sx(6.04)
        pod=[(cx-1.0,16.9),(cx+1.0,16.9),(cx+1.12,19.45),(cx+.78,19.78),(cx-.79,19.78),(cx-1.12,19.43)]
        plate(g,side+' speaker white pod',pod,8.46,10.65,'silver')
        octagon=[(cx+1.02*math.cos(math.pi/8+i*math.tau/8),18.34+1.02*math.sin(math.pi/8+i*math.tau/8)) for i in range(8)]
        plate(g,side+' speaker black octagon',octagon,8.43,8.45,'black',texture='speaker',rect=(cx-1.04,17.30,cx+1.04,19.38))

    g.group='Backlit title and illustrated acrylic topper'
    sign=[(.25,35.55),(1.05,34.90),(14.95,34.90),(15.75,35.55),(15.75,37.60),(14.95,38.28),(1.05,38.28),(.25,37.60)]
    plate(g,'Title lightbox',sign,9.45,11.0,'silver')
    sign=[(.46,35.62),(1.15,35.08),(14.85,35.08),(15.54,35.62),(15.54,37.52),(14.85,38.08),(1.15,38.08),(.46,37.52)]
    plate(g,'Printed title lens',sign,9.42,9.44,'white',texture='marquee',glow=True)
    # Alpha cutout is printed acrylic, two single faces. Its illustration never
    # becomes per-pixel geometry and it remains readable from the rear.
    _surface(g,'Official Rainbow character topper',[(14.85,47.50,10.42),(14.85,37.90,10.42),(1.15,37.90,10.42),(1.15,47.50,10.42)],'topper',normal=(0,0,-1))
    _surface(g,'Opaque white topper backing',[(1.15,47.50,10.46),(1.15,37.90,10.46),(14.85,37.90,10.46),(14.85,47.50,10.46)],'topper_back',normal=(0,0,1))
    for x in (4.5,11.5):
        g.box('Topper support '+str(x),(x-.10,37.7,10.47),(x+.10,40.0,10.68),'silver')
    # Remove covered annulus and cut the horizontal LCD aperture out of the
    # deck. This gives each visible surface exactly one depth and one material.
    from ddr_mesh_export import pieces,quads
    final=[]
    for f in g.faces:
        if f['name'].startswith('Detonation button black ring band2 '):continue
        if not f['name'].startswith('Deck top '):final.append(f);continue
        fragments=[list(zip(f['vertices'],f['uv']))]
        for axis,levels in [(0,[2.85,11.45]),(2,[2.55,8.35])]:
            fragments=[frag for poly in fragments for frag in pieces(poly,axis,levels)]
        for i,poly in enumerate(fragments):
            x=sum(p[0] for p,u in poly)/len(poly);z=sum(p[2] for p,u in poly)/len(poly)
            if 2.85<x<11.45 and 2.55<z<8.35:continue
            for j,q in enumerate(quads(poly)):
                final.append({**f,'name':f['name']+f' aperture {i}-{j}','vertices':[p for p,u in q],'uv':[u for p,u in q]})
    g.faces=final
    return g,{'id':'bombergirl','edition':'Bombergirl Rainbow','design':'Konami original portrait/touchscreen seated cabinet',
        'front':'north (-Z)','nominal_cells':[1,3,1],'reference_page':'https://www.konami.com/arcadegames/products/am_bombergirl/',
        'notes':['Separate stool deliberately omitted; cabinet fits one horizontal cell.','Joystick, detonation button and speakers are physical geometry; perforations, fasteners and printed detail are textures.']}
