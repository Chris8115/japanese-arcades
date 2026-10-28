"""Classic single-monitor white GITADORA cabinets; model pixels, north (-Z) front.

Reference: KONAMI's OverDrive GuitarFreaks / DrumMania product photographs.
Circles, guitar cutaways, pads and cymbals are mesh; grilles/printing are textures.
"""
import math
from initial_d_geometry import Geometry
from popn_music_geometry import _face, _surface, _xy_quad

COLORS={'white':'#ededeb','silver':'#aeb7bc','black':'#101318','dark':'#292d33',
        'chrome':'#dce3e5','gray':'#707c85','cream':'#fff5d8','wood':'#deb641',
        'red':'#e84c47','blue':'#359aca','green':'#81bf34','yellow':'#dfd945',
        'pink':'#c678bd','orange':'#e8873f','cyan':'#39bacb','rubber':'#414447'}


def circle(g,name,cx,cy,r,z,texture='speaker',segments=32,material='black'):
    for i in range(segments):
        a,b=math.tau*i/segments,math.tau*(i+1)/segments
        points=[(cx,cy,z),(cx+r*math.cos(a),cy+r*math.sin(a),z),(cx+r*math.cos(b),cy+r*math.sin(b),z)]
        uv=[(8,8),(8-8*math.cos(a),8-8*math.sin(a)),(8-8*math.cos(b),8-8*math.sin(b))]
        _face(g,f'{name} {i}',points,material,texture,uv,normal=(0,0,-1))


def ring(g,name,cx,cy,profile,mats,segments=32):
    for band,((r,z),(R,Z)) in enumerate(zip(profile,profile[1:])):
        for i in range(segments):
            a,b=math.tau*i/segments,math.tau*(i+1)/segments
            _face(g,f'{name} band{band} {i}',[(cx+r*math.cos(a),cy+r*math.sin(a),z),
                (cx+R*math.cos(a),cy+R*math.sin(a),Z),(cx+R*math.cos(b),cy+R*math.sin(b),Z),
                (cx+r*math.cos(b),cy+r*math.sin(b),z)],mats[band],normal=(math.cos((a+b)/2),math.sin((a+b)/2),-1))


def speaker(g,name,x,y,r,z):
    ring(g,name+' rim',x,y,[(r,z+.25),(r,z),(r-.12,z-.07),(r-.3,z+.04)],['white','silver','black'])
    circle(g,name+' perforated grille',x,y,r-.3,z+.035)


def rail(g,name,a,b,r=.18):
    g.tube(name,[a,b],r,'chrome',12)


def panel(g,name,x0,y0,x1,y1,z,texture,uv=(0,0,16,16),glow=False):
    _surface(g,name,[(x1,y1,z),(x1,y0,z),(x0,y0,z),(x0,y1,z)],texture,uv,glow=glow)


def cabinet(g,kind):
    drum=kind=='drummania'; cx=16 if drum else 8
    width=22 if drum else 18; x0,x1=cx-width/2,cx+width/2
    g.group='Cabinet shell'
    g.box('Black floor plinth',(x0-.7,0,2 if not drum else 5),(x1+.7,1.3,15.5),'black')
    # A single convex side profile, with recessed toe and backward-raked display.
    profile=[(1.3,2.2 if not drum else 5),(20,3.6 if not drum else 6),(25,5.2),
             (37.8,7.4),(38.2,14.8),(3,15.3),(1.3,14.8)]
    g.yz_shell('White tapered pedestal and monitor chassis',x0,x1,profile,'white')
    for x,sign in ((x0,-1),(x1,1)):
        # Broad factory wave graphic replaces dozens of decorative strips.
        _surface(g,f'Side wave graphic {sign}',[(x+sign*.035,36,8),(x+sign*.035,2.0,3.1 if not drum else 5.5),
                    (x+sign*.035,2.0,14.8),(x+sign*.035,36,14.7)],'side',
                    uvrect=(16,0,0,16) if sign>0 else (0,0,16,16),normal=(sign,0,0))
    g.group='Speaker and service fascia'
    z=2.05 if not drum else 4.88
    panel(g,'Lower wave fascia',x0+.2,1.6,x1-.2,19.4,z,'front')
    speaker(g,'Large cabinet woofer',cx+(1 if not drum else 0),9.8,4.05,z-.10)
    # Compact payment tower to the player's right (low model X).
    px=x0+.3
    g.box('Payment tower',(px,1.4,.6 if not drum else 2.8),(px+3.7,18,5.7),'white')
    panel(g,'Black coin service door',px+.2,2,px+3.5,16.8,.555 if not drum else 2.755,'service')
    start=len(g.faces)
    g.rounded('Angled reader and menu console',(px-.15,17.9,px+4.15,22.2),1.7,3.5,.25,'dark')
    panel(g,'Reader keypad and instructions',px+.12,18.15,px+3.88,21.9,1.655,'reader')
    g.transform(start,lambda x,y,z:(x,y,(z+(y-18)*.46)+(2.2 if drum else 0)))
    for i,(dx,dy,col) in enumerate(((.9,18.55,'blue'),(2.1,18.55,'red'),(3.1,18.55,'green'))):
        g.disc(f'Menu button {i}',px+dx,dy,.28,1.35+(dy-18)*.46+(2.2 if drum else 0),1.7+(dy-18)*.46+(2.2 if drum else 0),col,12)
    g.group='Single display'
    # A 16:9 monitor raked back by 9 degrees; front decal replaces the black plane.
    start=len(g.faces)
    w=18.3 if drum else 16.6
    g.rounded('Silver monitor surround',(cx-w/2-.42,23.8,cx+w/2+.42,35.2),5.15,6.0,.42,'silver')
    g.rounded('Black monitor bezel',(cx-w/2-.16,24.06,cx+w/2+.16,34.94),5.03,5.2,.26,'black')
    panel(g,'GITADORA screen',cx-w/2+.24,24.58,cx+w/2-.24,34.37,4.985,'screen_'+kind,glow=True)
    g.transform(start,lambda x,y,z:(x,y,z+(y-24)*.17))
    panel(g,'Name strip below screen',cx-5.3,22.8,cx+5.3,23.6,4.86,'title')
    # Upper white trim and chrome fan detail, printed rather than tiny mesh strips.
    panel(g,'Swept silver bridge',x0,35.9,x1,38.8,7.25,'bridge')
    g.group='Twin speaker marquee'
    hx0,hx1=x0-.9,x1+.9
    g.rounded('White header perimeter',(hx0,38.25,hx1,46.8),8.0,14.7,.72,'white')
    g.rounded('Black header face',(hx0+.22,38.5,hx1-.22,46.58),7.91,8.05,.57,'black')
    panel(g,'OverDrive illuminated marquee',cx-4.35,39.42,cx+4.35,45.75,7.855,'marquee',glow=True)
    for side,x in (('left',hx1-2.95),('right',hx0+2.95)):
        speaker(g,side+' upper fullrange',x,43.75,2.47,7.70)
        speaker(g,side+' lower tweeter',x,39.95,1.56,7.70)
    # Rear service geometry is deliberately sparse; printed vents carry the detail.
    g.group='Rear service'
    panel(g,'Rear service vents',cx-5,4,cx+5,30,15.36,'rear')
    # Turn the rear panel to +Z; panel winding otherwise faces front.
    g.faces[-1]['vertices'].reverse();g.faces[-1]['uv'].reverse()
    g.faces[-1]['uv']=[(16-u,v) for u,v in g.faces[-1]['uv']]
    for x in (x0+.9,x1-.9):
        g.box(f'Foot caster bracket {x}',(x-.45,0,12.8),(x+.45,.7,14.1),'gray')
    return (x0,x1)


def polygon(g,name,outline,z0,z1,mat='white'):
    """Extrude a concave guitar profile using a real ear-clipped front/back."""
    points=list(outline)
    if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))<0:points.reverse()
    indices=list(range(len(points))); tris=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(indices)>3:
        for j,i in enumerate(indices):
            a,b,c=indices[j-1],i,indices[(j+1)%len(indices)]
            if cross(points[a],points[b],points[c])<=1e-9:continue
            if any(k not in (a,b,c) and min(cross(points[a],points[b],points[k]),cross(points[b],points[c],points[k]),cross(points[c],points[a],points[k]))>=-1e-9 for k in indices):continue
            tris.append((a,b,c));indices.pop(j);break
        else:raise ValueError(name+' polygon cannot be triangulated')
    tris.append(tuple(indices))
    for i,t in enumerate(tris):
        _face(g,f'{name} front{i}',[(*points[k],z0) for k in t],mat,normal=(0,0,-1))
        _face(g,f'{name} back{i}',[(*points[k],z1) for k in t],mat,normal=(0,0,1))
    for i,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
        _face(g,f'{name} edge{i}',[(*a,z0),(*b,z0),(*b,z1),(*a,z1)],mat,normal=(b[1]-a[1],a[0]-b[0],0))


def guitar(g):
    g.group='White five-button guitar controller'
    # A compact real double-cutaway body, avoiding a rectangular toy silhouette.
    outline=[(-1.1,0),(-2.0,.35),(-2.5,1.25),(-2.6,2.5),(-2.12,3.8),(-1.75,4.7),
             (-2.02,5.8),(-1.65,6.65),(-.95,5.62),(-.63,4.92),(.45,5.02),
             (.98,6.5),(1.45,7.0),(1.62,6.5),(1.22,5.1),(1.3,4.6),
             (2.0,3.5),(2.36,2.25),(2.12,1.05),(1.34,.25),(.30,0)]
    body=[(x+13.4,y+17.0) for x,y in outline]
    polygon(g,'Sculpted white guitar body',body,1.35,2.55,'white')
    inset=[((x-13.4)*.92+13.4,(y-20)*.94+20) for x,y in body]
    polygon(g,'Front white body bevel',inset,1.15,1.36,'white')
    # Black scratch plate, neck and five individually raised fret switches.
    polygon(g,'Black pickguard',[(12.9,18.0),(14.6,18.4),(14.9,20.4),(13.7,21.3),(13.65,23.5),(12.8,23.1),(12.2,20.1)],1.08,1.17,'black')
    g.box('Maple guitar neck',(12.65,22,1.32),(14.15,36.8,2.18),'wood')
    g.box('Dark fingerboard',(12.82,23.3,1.19),(13.98,36.9,1.36),'dark')
    for i,col in enumerate(('red','green','blue','yellow','pink')):
        g.rounded(f'{col} fret switch',(12.87,32.0+i*.94,13.94,32.70+i*.94),.99,1.23,.16,col)
    polygon(g,'Maple headstock',[(12.63,36.6),(13.84,36.6),(14.3,39),(13.7,39.65),(12.8,39.1),(12.55,38)],1.32,2.12,'wood')
    for i in range(5):
        g.disc(f'Tuner {i}',14.15,36.95+i*.42,.17,1.45,1.85,'chrome',10)
    g.rounded('Silver pick lever',(12.65,19.0,14.37,19.55),.91,1.16,.1,'silver')
    g.disc('Controller function knob',14.9,18.55,.3,1.0,1.17,'black',16)
    rail(g,'Guitar hanger',(13.3,35.8,3.2),(13.3,35.8,5.5),.24)
    g.group='Guitar lead'
    cable=[(13.2,17.1,1.65),(12.2,16.4,1.4),(10.5,15.2,1.0),(10.1,12.2,.9),
           (9.6,10.8,.8),(8.6,10.1,.85),(7.9,10.8,1),(8.0,12.3,1.15),(8.7,13.2,1.4)]
    g.tube('Black coiled controller cable',cable,.105,'black',8)


def pad(g,name,center,r,color,tilt=18,cymbal=False):
    g.group='Drum kit pads and cymbals'
    cx,cy,cz=center; tilt=math.radians(tilt)
    def point(radius,angle,h):
        x=radius*math.cos(angle); z=radius*math.sin(angle)
        return (cx+x,cy+h*math.cos(tilt)+z*math.sin(tilt),cz+z*math.cos(tilt)-h*math.sin(tilt))
    profile=[(r*.88,-.45),(r,-.25),(r,.04),(r*.95,.16),(r*.86,.18)] if not cymbal else [(r*.80,-.21),(r,-.06),(r,.05),(r*.97,.13),(r*.34,.24),(.25,.42)]
    mats=['dark','black',color,'rubber'] if not cymbal else ['black','dark',color,'rubber','dark']
    count=32
    for band,((a,h),(b,H)) in enumerate(zip(profile,profile[1:])):
        for i in range(count):
            t,T=i*math.tau/count,(i+1)*math.tau/count
            # The lower flared band faces down. An always-upward hint turns
            # those faces inward, leaving a visible gap above the bottom cap.
            # Derive the outward normal from the profile, then tilt it with
            # the shell instead of assuming that every band faces upward.
            angle=(t+T)/2; radial=H-h; axial=a-b
            normal=(radial*math.cos(angle),
                    axial*math.cos(tilt)+radial*math.sin(angle)*math.sin(tilt),
                    radial*math.sin(angle)*math.cos(tilt)-axial*math.sin(tilt))
            _face(g,f'{name} shell{band}-{i}',[point(a,t,h),point(b,t,H),point(b,T,H),point(a,T,h)],mats[band],normal=normal)
    rr,hh=profile[-1]
    for i in range(count):
        a,b=i*math.tau/count,(i+1)*math.tau/count
        _face(g,f'{name} rubber head{i}',[point(0,0,hh),point(rr,a,hh),point(rr,b,hh)],texture='pad',
              uv=[(8,8),(8-8*math.cos(a),8-8*math.sin(a)),(8-8*math.cos(b),8-8*math.sin(b))],normal=(0,1,-math.sin(tilt)))
    # Black underside closes the controller only once, without unseen screw arrays.
    bottom_radius,bottom_height=profile[0]
    for i in range(count):
        a,b=i*math.tau/count,(i+1)*math.tau/count
        _face(g,f'{name} underside{i}',[point(0,0,bottom_height),point(bottom_radius,a,bottom_height),point(bottom_radius,b,bottom_height)],'black',normal=(0,-1,math.sin(tilt)))
    g.group='Drum rack'
    g.box(name+' mounting clamp',(cx-.43,cy-2,cz+.12),(cx+.43,cy-.7,cz+.82),'black')


def drums(g):
    g.group='Drum platform'
    g.box('Black shared floor platform',(.65,0,-15.3),(31.35,.85,15.5),'black')
    g.box('Aluminium platform lip',(.8,.85,-15.15),(31.2,1.1,15.3),'silver')
    # The front knee space remains open between slim rack supports and pedals.
    g.group='Drum rack'
    for x in (3.0,29.0):
        rail(g,f'Front post{x}',(x,1,-6),(x,23,-6),.23)
        rail(g,f'Rack foot{x}',(x,1.4,-11),(x,1.4,4),.25)
        g.box(f'Rack collar{x}',(x-.4,14.4,-6.4),(x+.4,15.3,-5.6),'black')
    rail(g,'Rack crossbar',(3,15,-5.8),(29,15,-5.8),.24)
    rail(g,'Low rear rack brace',(5,7,1.5),(27,7,1.5),.20)
    for spec in [('Left crash',(27.9,28.1,-2.0),3.25,'pink',12,True),
                 ('Hi hat',(28.2,22.2,-8.4),2.65,'blue',19,True),
                 ('Snare',(21.8,17.3,-10.3),3.1,'yellow',12,False),
                 ('High tom',(20.5,23.4,-1.7),3.0,'green',23,False),
                 ('Low tom',(12.0,23.4,-1.7),3.0,'red',23,False),
                 ('Floor tom',(5.0,17.8,-8.9),3.0,'orange',15,False),
                 ('Right crash',(4.1,28.7,-1.0),3.2,'cyan',28,True)]:pad(g,*spec)
    # The original cabinet carries toms on short brackets. A separate long pole
    # for every pad would misrepresent its open knee space and waste geometry.
    g.group='Drum rack'
    supports={
        'Left crash':[(29,22.6,-6),(27.9,23.3,-1.6),(27.9,27.6,-1.6)],
        'Hi hat':[(29,20.5,-6),(28.2,21.7,-8.0)],
        'Snare':[(21.8,15,-5.8),(21.8,16.8,-9.9)],
        'High tom':[(20.5,21.5,4.5),(20.5,22.9,-1.3)],
        'Low tom':[(12,21.5,4.5),(12,22.9,-1.3)],
        'Floor tom':[(5,15,-5.8),(5,17.3,-8.5)],
        'Right crash':[(3,22.6,-6),(4.1,24,-.6),(4.1,28.2,-.6)]}
    for name,points in supports.items():g.tube(name+' short support',points,.17,'chrome',12)
    g.group='Twin foot pedals'
    for i,x in enumerate((11.6,20.1)):
        g.box(f'Pedal{i} base',(x-1.55,1.13,-14.6),(x+1.55,1.7,-8.0),'black')
        g.box(f'Pedal{i} heel',(x-1.32,1.7,-14.45),(x+1.32,2.3,-12.8),'dark')
        _surface(g,f'Pedal{i} ribbed tread',[(x+1.18,2.45,-8.25),(x+1.18,1.83,-12.8),
                (x-1.18,1.83,-12.8),(x-1.18,2.45,-8.25)],'pedal',normal=(0,1,-.12))
        rail(g,f'Pedal{i} hinge',(x-1.5,2.3,-8.45),(x+1.5,2.3,-8.45),.22)
        g.box(f'Pedal{i} kick tower',(x-.62,1.6,-8.4),(x+.62,4.7,-7.6),'black')
    g.group='Stick holder'
    g.box('White stick cup',(26.2,16,3.9),(27.7,19,5.4),'white')
    for i in range(2):g.tube(f'Wood drumstick{i}',[(26.45+i*.65,16.3,4.4),(26.35+i*.80,21.3,4.0)],.11,'wood',8)


def build(kind):
    assert kind in ('guitarfreaks','drummania')
    g=Geometry(COLORS)
    cabinet(g,kind)
    if kind=='guitarfreaks':guitar(g)
    else:drums(g)
    return g,{'name':'GITADORA OverDrive '+('GuitarFreaks' if kind=='guitarfreaks' else 'DrumMania'),
              'design':'Classic white single-monitor cabinet; static displayed instruments',
              'reference':'https://www.konami.com/arcadegames/products/am_gitadora_'+('gf' if kind=='guitarfreaks' else 'dm')+'/',
              'units':'16 model pixels per Minecraft block; north -Z front',
              'gameplay':'Decorative arcade with existing jukebox interaction; no rhythm game simulation'}
