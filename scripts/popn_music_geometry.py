"""Native, moderately tessellated Sunny Park HD cabinet geometry.

Pixel coordinates: sixteen pixels per block; the player faces the -Z side.
Artwork and the shared exporter live in make_popn_music_model.py. Circular controls
are real shallow domes, while printed labels and speaker perforations use UVs.
"""
from __future__ import annotations

import math

from initial_d_geometry import Geometry


COLORS = {
    "white": "#eeeef0", "silver": "#bfc3c8", "black": "#10131a", "dark": "#242932",
    "cyan": "#30bfde", "orange": "#ff9d19", "yellow": "#f7db32", "red": "#ed2841",
    "blue": "#159deb", "green": "#28c686", "cream": "#fff7d7", "glass": "#253c45",
    "pink": "#ef5999", "chrome": "#e4e8e8", "charcoal": "#3c434b", "gray": "#7b828d",
}
MATERIALS = list(COLORS)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _face(g, name, vertices, material="white", texture="materials", uv=None, normal=None, glow=False):
    """Keep every face's winding outward, including the rotated console."""
    vertices = [tuple(p) for p in vertices]
    if normal is not None:
        a = [vertices[1][i]-vertices[0][i] for i in range(3)]
        b = [vertices[2][i]-vertices[0][i] for i in range(3)]
        n = _cross(a, b)
        if sum(n[i]*normal[i] for i in range(3)) < 0:
            vertices.reverse()
            if uv is not None:
                uv = list(reversed(uv))
    if len(vertices)==4:
        a=[vertices[1][i]-vertices[0][i] for i in range(3)]
        b=[vertices[2][i]-vertices[0][i] for i in range(3)]
        n=_cross(a,b)
        size=math.sqrt(sum(v*v for v in n))
        distance=abs(sum(n[i]*(vertices[3][i]-vertices[0][i]) for i in range(3)))/size if size else 0
        if distance>1e-6:
            for suffix,ids in ((" triangle A",(0,1,2)),(" triangle B",(0,2,3))):
                g.face(name+suffix,[vertices[i] for i in ids],material,texture,[uv[i] for i in ids] if uv else None,glow)
            return
    g.face(name, vertices, material, texture, uv, glow)


def _surface(g, name, corners, texture, uvrect=(0, 0, 16, 16), normal=(0, 0, -1), glow=False):
    """Corners are viewer top-left, bottom-left, bottom-right, top-right."""
    u, v, U, V = uvrect
    _face(g, name, corners, texture=texture, uv=[(u,v),(u,V),(U,V),(U,v)], normal=normal, glow=glow)


def _xy_quad(g, name, x0, y0, x1, y1, z, texture, uvrect=(0,0,16,16), glow=False):
    _surface(g, name, [(x1,y1,z),(x1,y0,z),(x0,y0,z),(x0,y1,z)], texture, uvrect, glow=glow)


def _ring_z(g, name, cx, cy, profile, materials, segments=48):
    """Lathed circle facing -Z; each profile is (radius, z)."""
    for j, ((r,z),(R,Z)) in enumerate(zip(profile, profile[1:])):
        for i in range(segments):
            a, b = math.tau*i/segments, math.tau*(i+1)/segments
            pts=[(cx+r*math.cos(a),cy+r*math.sin(a),z),
                 (cx+R*math.cos(a),cy+R*math.sin(a),Z),
                 (cx+R*math.cos(b),cy+R*math.sin(b),Z),
                 (cx+r*math.cos(b),cy+r*math.sin(b),z)]
            _face(g, name+f" {j} {i}", pts, materials[min(j,len(materials)-1)], normal=(0,0,-1))


def _circle_z(g, name, cx, cy, radius, z, material="black", texture=None, segments=48):
    for i in range(segments):
        a,b=math.tau*i/segments,math.tau*(i+1)/segments
        pts=[(cx,cy,z),(cx+radius*math.cos(a),cy+radius*math.sin(a),z),
             (cx+radius*math.cos(b),cy+radius*math.sin(b),z)]
        uv=[(8,8),(8-8*math.cos(a),8-8*math.sin(a)),(8-8*math.cos(b),8-8*math.sin(b))] if texture else None
        _face(g,name+f" {i}",pts,material,texture or "materials",uv,normal=(0,0,-1))


def _deck_y(z):
    # Slight rear rise retains the broad, nearly horizontal two-row button deck.
    return 17.15 + .045*(z+1.2)


def _dome(g, name, cx, cz, color):
    # Black flange, chrome lip, and five smooth dome bands: 288 faces per key.
    profile=[(1.24,0),(1.27,.075),(1.25,.16),(1.12,.235),
             (1.06,.265),(1.025,.40),(.94,.555),(.77,.69),(.46,.785),(0,.825)]
    colors=["black","dark","black","chrome",color,color,color,color,color]
    segments=32
    for j,((r,h),(R,H)) in enumerate(zip(profile,profile[1:])):
        for i in range(segments):
            a,b=math.tau*i/segments,math.tau*(i+1)/segments
            def p(rad,angle,height):
                z=cz+rad*math.sin(angle)
                return (cx+rad*math.cos(angle),_deck_y(z)+height,z)
            pts=[p(r,a,h),p(R,a,H),p(R,b,H),p(r,b,h)] if R else [p(r,a,h),p(0,0,H),p(r,b,h)]
            mid=(a+b)/2
            _face(g,name+f" band{j} sector{i}",pts,colors[j],normal=(math.cos(mid),1,math.sin(mid)))


def _hull(points):
    points=sorted(set(points))
    def turn(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in points:
        while len(lo)>=2 and turn(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    hi=[]
    for p in reversed(points):
        while len(hi)>=2 and turn(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]


def _rounded_pod(g, name, cx, cy, outward):
    # Convex pear housing joins the large woofer to its high/outboard tweeter.
    tx,ty=cx+outward*.77,cy+2.4
    outline=_hull([(cx+2.56*math.cos(i*math.tau/48),cy+2.56*math.sin(i*math.tau/48)) for i in range(48)]+
                  [(tx+1.27*math.cos(i*math.tau/32),ty+1.27*math.sin(i*math.tau/32)) for i in range(32)])
    center=(cx,cy+.63)
    rings=[(1,9.60),(1.01,8.86),(.98,8.48),(.945,8.28)]
    for j,((s,z),(S,Z)) in enumerate(zip(rings,rings[1:])):
        for i,p in enumerate(outline):
            q=outline[(i+1)%len(outline)]
            def pt(v,k,d):return (center[0]+(v[0]-center[0])*k,center[1]+(v[1]-center[1])*k,d)
            _face(g,name+f" orange rim {j} {i}",[pt(p,s,z),pt(q,s,z),pt(q,S,Z),pt(p,S,Z)],"orange",normal=(p[0]-cx,p[1]-cy,-.7))
    s,z=rings[-1]
    for i,p in enumerate(outline):
        q=outline[(i+1)%len(outline)]
        _face(g,name+f" orange face {i}",[(center[0],center[1],z),
            (center[0]+s*(p[0]-center[0]),center[1]+s*(p[1]-center[1]),z),
            (center[0]+s*(q[0]-center[0]),center[1]+s*(q[1]-center[1]),z)],"orange",normal=(0,0,-1))
    _ring_z(g,name+" woofer",cx,cy,[(2.15,8.26),(2.11,8.09),(1.97,8.035),(1.87,8.09),(1.76,8.22)],
            ["white","chrome","silver","charcoal"])
    _circle_z(g,name+" grille",cx,cy,1.765,8.215,texture="speaker")
    _ring_z(g,name+" tweeter",tx,ty,[(.77,8.25),(.74,8.08),(.60,8.04),(.53,8.13)],["orange","chrome","charcoal"],32)
    _circle_z(g,name+" tweeter grille",tx,ty,.535,8.125,texture="speaker",segments=32)


def _console(g):
    # Ordered convex X/Z outline: a shallow bowed front, rounded side corners,
    # then the simple rear edge. This is visibly softer than a rounded box.
    outline=[]
    for x,z,start in ((17.28,6.78,0),(-1.28,6.78,90),(-1.28,-.68,180)):
        for i in range(9):
            a=math.radians(start+i*90/8)
            outline.append((x+1.42*math.cos(a),z+1.42*math.sin(a)))
    for i in range(1,33):
        x=-1.28+18.56*i/32
        outline.append((x,-3.1+((x-8)/9.28)**2))
    for i in range(1,9):
        a=math.radians(270+i*90/8)
        outline.append((17.28+1.42*math.cos(a),-.68+1.42*math.sin(a)))
    # Top is one plane, split into a clean fan for reliable OBJ clipping.
    cx,cz=8,2.3
    def uv(x,z):return (16*(18.7-x)/21.4,16*(8.2-z)/11.3)
    for i,(x,z) in enumerate(outline):
        X,Z=outline[(i+1)%len(outline)]
        _face(g,f"Console printed top {i}",[(cx,_deck_y(cz),cz),(x,_deck_y(z),z),(X,_deck_y(Z),Z)],
              texture="console",uv=[uv(cx,cz),uv(x,z),uv(X,Z)],normal=(0,1,-.045))
        # The thin luminous cyan trim is continuous all around the console.
        for label,y0,y1,mat in [("white upper",-.40,0,"white"),("cyan stripe",-.62,-.40,"cyan"),("white skirt",-1.22,-.62,"white")]:
            points=[(x,_deck_y(z)+y0,z),(X,_deck_y(Z)+y0,Z),(X,_deck_y(Z)+y1,Z),(x,_deck_y(z)+y1,z)]
            if label=="white upper" and max(z,Z)<.01:
                _face(g,f"Console {label} {i}",points,texture="console_edge",
                      uv=[(16*(18.7-x)/21.4,16),(16*(18.7-X)/21.4,16),(16*(18.7-X)/21.4,0),(16*(18.7-x)/21.4,0)],
                      normal=(x-cx,0,z-cz))
            else:
                _face(g,f"Console {label} {i}",points,mat,normal=(x-cx,0,z-cz))
        _face(g,f"Console underside {i}",[(cx,_deck_y(cz)-1.22,cz),(X,_deck_y(Z)-1.22,Z),(x,_deck_y(z)-1.22,z)],"white",normal=(0,-1,.045))
    # Curved white bridge from the top of the deck to the monitor's lower bezel.
    profile=[(17.46,6.90),(17.57,7.23),(17.86,7.62),(18.30,7.99),(18.86,8.27),(19.22,8.43)]
    for i,((y,z),(Y,Z)) in enumerate(zip(profile,profile[1:])):
        _face(g,f"Console rear curved bridge {i}",[(-1.53,y,z),(17.53,y,z),(17.53,Y,Z),(-1.53,Y,Z)],"white",normal=(0,1,-1))
    for side,x in (("right",-1.53),("left",17.53)):
        for i,((y,z),(Y,Z)) in enumerate(zip(profile,profile[1:])):
            _face(g,f"Console bridge {side} closure {i}",[(x,16.55,8.55),(x,y,z),(x,Y,Z)],"white",normal=(-1 if x<8 else 1,0,0))
    # Viewer sees physical right at low X. The card reader is behind the keys.
    g.box("Card reader plinth",(-.55,17.43,4.93),(3.12,17.59,7.68),"dark")
    _surface(g,"e-amusement reader",[(3.02,17.602,7.58),(3.02,17.602,5.03),(-.45,17.602,5.03),(-.45,17.602,7.58)],
             "details",(8,0,16,8),normal=(0,1,0))
    # Semicircular raised instruction/art inset behind the center of the keys.
    hump=[(9.35+3.36*math.cos(i*math.pi/24),17.51+1.80*math.sin(i*math.pi/24)) for i in range(25)]
    g.prism("Semicircle card holder shell",hump,5.88,6.42,"black")
    for i in range(24):
        p,q=hump[i],hump[i+1]
        pts=[(9.35,17.51,5.865),(*p,5.865),(*q,5.865)]
        uv=[(4,16)]+[(4+(9.35-x)*4/3.36,16-(y-17.51)*8/1.80) for x,y in (p,q)]
        _face(g,f"Semicircle printed art {i}",pts,texture="details",uv=uv,normal=(0,0,-1))
    for i in range(24):
        a,b=i*math.pi/24,(i+1)*math.pi/24
        _face(g,f"Semicircle magenta surround {i}",[(9.35+3.36*math.cos(a),17.51+1.8*math.sin(a),5.84),
              (9.35+3.36*math.cos(b),17.51+1.8*math.sin(b),5.84),(9.35+3.22*math.cos(b),17.51+1.68*math.sin(b),5.835),
              (9.35+3.22*math.cos(a),17.51+1.68*math.sin(a),5.835)],"pink",normal=(0,0,-1))
    g.group="Nine domed arcade buttons"
    for i,(x,color) in enumerate(zip((.15,4.05,8,11.95,15.85),("white","green","red","green","white"))):
        _dome(g,f"Front {i+1} {color}",x,-.18,color)
    for i,(x,color) in enumerate(zip((2.1,6,10,13.9),("yellow","blue","blue","yellow"))):
        _dome(g,f"Rear {i+1} {color}",x,2.53,color)


def _monitor(g):
    def z(y):return 6.25+.30*(y-18)
    # Screen's planar 16:9 aperture is framed by broad yellow printed glass.
    g.yz_shell("Rear black monitor case",-1.38,17.38,[(17.1,9.15),(31.9,11.35),(32.55,12.0),(32.55,15.3),(17.1,15.3)],"black")
    x0,x1=-1.52,17.52;y0,y1=18.90,31.5
    # Slightly bevelled light shell. The convex tapered side cheeks are white.
    for side,x,outer in (("right",x0,-1.70),("left",x1,17.70)):
        _face(g,f"Monitor {side} cheek",[(x,y0,z(y0)),(x,y1,z(y1)),(outer,y1,11.34),(outer,y0,8.54)],"white",normal=(-1 if x<8 else 1,0,0))
    _face(g,"Monitor top white bevel",[(x0,y1,z(y1)),(x1,y1,z(y1)),(17.70,31.74,11.34),(-1.70,31.74,11.34)],"white",normal=(0,1,0))
    _face(g,"Monitor lower white bevel",[(x1,y0,z(y0)),(x0,y0,z(y0)),(-1.70,18.68,8.54),(17.70,18.68,8.54)],"white",normal=(0,-1,-1))
    # Actual image opening and its tiny dark inner trim.
    sx0,sx1=-.15,16.15;sy0,sy1=21.50,30.30
    aperture=[(sx0,sy0),(sx1,sy0),(sx1,sy1),(sx0,sy1)]
    outer=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    for i in range(4):
        q=(i+1)%4
        points=[(outer[i][0],outer[i][1],z(outer[i][1])),(outer[q][0],outer[q][1],z(outer[q][1])),
            (aperture[q][0],aperture[q][1],z(aperture[q][1])-.015),(aperture[i][0],aperture[i][1],z(aperture[i][1])-.015)]
        _face(g,f"Yellow monitor bezel {i}",points,texture="bezel",uv=[(16*(x1-x)/(x1-x0),16*(y1-y)/(y1-y0)) for x,y,z0 in points],normal=(0,.3,-1))
    rim=.085
    # Put native black rim immediately ahead of image with no overlapping plane.
    inner=[(sx0+rim,sy0+rim),(sx1-rim,sy0+rim),(sx1-rim,sy1-rim),(sx0+rim,sy1-rim)]
    for i in range(4):
        j=(i+1)%4
        _face(g,f"Monitor inner black rim {i}",[(aperture[i][0],aperture[i][1],z(aperture[i][1])-.021),
              (aperture[j][0],aperture[j][1],z(aperture[j][1])-.021),
              (inner[j][0],inner[j][1],z(inner[j][1])-.021),(inner[i][0],inner[i][1],z(inner[i][1])-.021)],"black",normal=(0,.3,-1))
    _surface(g,"Sunny Park attract screen",[(sx1-rim,sy1-rim,z(sy1-rim)-.025),(sx1-rim,sy0+rim,z(sy0+rim)-.025),
             (sx0+rim,sy0+rim,z(sy0+rim)-.025),(sx0+rim,sy1-rim,z(sy1-rim)-.025)],"screen",normal=(0,.3,-1),glow=True)
    # Small white corner screws and two cyan side-edge strips remain geometry.
    for x in (x0+.28,x1-.28):
        for y in (y0+.35,y1-.35):
            _circle_z(g,f"Monitor screw {x} {y}",x,y,.085,z(y)-.04,"silver",segments=8)
    for side,x in (("right",x0-.04),("left",x1+.04)):
        _face(g,f"Monitor cyan {side} trim",[(x,19.0,z(19.0)),(x,31.45,z(31.45)),(x,31.45,z(31.45)+.14),(x,19.0,z(19.0)+.14)],"cyan",normal=(-1 if x<8 else 1,0,0))


def _base(g):
    g.box("Recessed dark toe kick",(-.40,.37,.27),(16.40,1.30,14.7),"black")
    # Main shell incl. its rear is closed; side skins wrap the sloped tower.
    profile=[(.95,.05),(15.95,.05),(17.05,8.80),(31.10,12.20),(31.10,14.80),(.95,14.80)]
    g.yz_shell("White lower pedestal",-.65,16.65,profile,"white")
    # Front is deliberately two doors rather than a repeated mirrored texture.
    g.box("Front service door",(3.63,1.22,-.018),(16.12,15.08,.068),"white")
    _xy_quad(g,"Pop-kun service-door print",3.66,1.25,16.09,15.05,-.025,"front")
    g.rounded("Black coin and lock strip",(-.13,1.30,3.30,14.84),-.046,.095,.18,"black")
    _xy_quad(g,"Coin panel labels",-.09,1.37,3.26,14.77,-.049,"details",(8,8,16,16))
    # Native hardware makes the front look solid even at close range.
    g.box("Coin insert chrome rim",(.47,12.45,-.18),(2.54,13.94,-.052),"silver")
    g.box("Coin insert black center",(.65,12.68,-.198),(2.36,13.72,-.18),"dark")
    g.box("Coin slot",(1.42,12.83,-.21),(1.64,13.60,-.198),"black")
    g.box("Coin return surround",(.66,8.13,-.17),(2.41,10.23,-.052),"gray")
    g.box("Coin return well",(.86,8.36,-.188),(2.21,10.03,-.17),"black")
    _circle_z(g,"Coin lower round lock",1.66,3.40,.18,-.09,"silver",segments=12)
    _circle_z(g,"Front service lock",4.15,7.13,.17,-.10,"silver",segments=12)
    for x in (4.03,15.75):
        for y in (1.63,14.68):
            _circle_z(g,f"Service screw {x} {y}",x,y,.065,-.08,"silver",segments=8)
    # Side artwork is a single UV image projected onto the clean shell polygon.
    yc=sum(y for y,z in profile)/len(profile);zc=sum(z for y,z in profile)/len(profile)
    for label,x,normal in (("right",-.663,(-1,0,0)),("left",16.663,(1,0,0))):
        def uv(y,z):
            return ((z-.05)*16/14.75,(31.1-y)*16/30.15)
        for i,(y,z) in enumerate(profile):
            Y,Z=profile[(i+1)%len(profile)]
            _face(g,f"{label} side cabinet graphic {i}",[(x,yc,zc),(x,y,z),(x,Y,Z)],texture="side",uv=[uv(yc,zc),uv(y,z),uv(Y,Z)],normal=normal)
    # Back black service panel and texture-free vent slits (only six shallow bars).
    g.box("Back service cover",(.10,1.18,14.79),(15.90,28.52,14.92),"black")
    for y in (3,3.25,3.5,3.75,4,4.25):
        g.box(f"Back vent {y}",(4.2,y,14.925),(11.8,y+.08,14.96),"charcoal")
    # Four polished levelers are small eight-sided posts and broad foot pads.
    for x in (-.16,16.16):
        for z in (1.12,13.78):
            start=len(g.faces)
            g.disc(f"Leveler pad {x} {z}",x,z,.40,0,.13,"silver",12)
            g.disc(f"Leveler stem {x} {z}",x,z,.19,.13,.99,"gray",8)
            # Helpers make discs normal to Z; swap their local Y/Z axes.
            g.transform(start,lambda X,Y,Z:(X,Z,Y))
            for f in g.faces[start:]:
                f["vertices"].reverse(); f["uv"].reverse()


def _header(g):
    g.box("Header rear support",(-.90,31.50,11.55),(16.90,40.37,14.60),"black")
    g.yz_shell("Speaker white bridge",-1.60,17.60,[(31.44,9.18),(32.71,8.50),(33.20,10.03),(33.20,13.25),(31.44,13.25)],"white")
    g.rounded("Orange speaker crossbar",(-1.20,33.03,17.20,39.23),9.0,10.85,.55,"orange")
    for side,cx,outward in (("right",1.1,-1),("left",14.9,1)):
        _rounded_pod(g,side+" paired speaker",cx,35.64,outward)
    # Signature central inverted trapezoid panel between the two orange pods.
    center=[(5.30,33.55),(10.70,33.55),(12.40,38.94),(3.60,38.94)]
    g.prism("Speaker-center gold frame",center,8.55,9.02,"yellow")
    inner=[(5.48,33.72),(10.52,33.72),(12.10,38.70),(3.90,38.70)]
    # Standard rectangular art naturally maps into the trapezoid as on cabinet.
    _surface(g,"Speaker center Sunny Park badge",[(12.10,38.70,8.53),(10.52,33.72,8.53),(5.48,33.72,8.53),(3.90,38.70,8.53)],"details",(0,0,8,8),glow=True)
    g.box("Rainbow lamp black housing",(-1.55,39.57,9.88),(17.55,40.63,12.05),"black")
    _xy_quad(g,"Rainbow header diffuser",-1.27,39.75,17.27,40.40,9.865,"rainbow",glow=True)
    # Thin mounting legs sit behind the edition-specific standee silhouette.
    g.box("Topper right mount",(1.50,40.40,11.39),(2.00,44.5,11.70),"silver")
    g.box("Topper left mount",(14.0,40.40,11.39),(14.5,44.5,11.70),"silver")
    # A real thin, die-cut standee: rounded badge peaks above the central logo.
    # The broad central printable area stays intact rather than cropping words.
    outline=[(-.35,40.47),(16.35,40.47),(16.8,40.92),(16.8,45.95)]
    badges=[(-.1,45.6,1.55),(2.4,45.8,1.75),(5.5,46.35,1.15),
            (8.7,46.3,1.25),(13.85,45.75,2.05),(16.0,45.45,1.20)]
    for i in range(49):
        x=16.8-17.6*i/48
        y=46.50
        for bx,by,r in badges:
            if abs(x-bx)<r:y=max(y,by+math.sqrt(r*r-(x-bx)**2))
        # Ease into the two rounded shoulders instead of a rectangular corner.
        if x>16.2:y=min(y,45.95+math.sqrt(max(0,.6**2-(x-16.2)**2)))
        if x<-.2:y=min(y,45.95+math.sqrt(max(0,.6**2-(x+.2)**2)))
        point=(x,min(47.8,y))
        if point!=outline[-1]:outline.append(point)
    outline.extend([(-.8,40.92)])
    cx,cy=8,44.0
    def uv(x,y):return (16*(16.8-x)/17.6,16*(47.8-y)/7.33)
    for i,(x,y) in enumerate(outline):
        X,Y=outline[(i+1)%len(outline)]
        _face(g,f"Sunny Park die-cut marquee art {i}",[(cx,cy,10.79),(x,y,10.79),(X,Y,10.79)],texture="marquee",
              uv=[uv(cx,cy),uv(x,y),uv(X,Y)],normal=(0,0,-1),glow=True)
        _face(g,f"Sunny Park matte paper reverse {i}",[(cx,cy,10.91),(x,y,10.91),(X,Y,10.91)],"cream",normal=(0,0,1))
        _face(g,f"Sunny Park cut paper edge {i}",[(x,y,10.79),(X,Y,10.79),(X,Y,10.91),(x,y,10.91)],"cream",normal=(x-cx,y-cy,0))


def build():
    g=Geometry(MATERIALS)
    g.group="White pedestal and service hardware"
    _base(g)
    g.group="Curved printed console"
    _console(g)
    g.group="Tilted widescreen and white bezel"
    _monitor(g)
    g.group="Orange paired speakers and Sunny Park marquee"
    _header(g)
    bounds=[[min(v[i] for f in g.faces for v in f["vertices"]),max(v[i] for f in g.faces for v in f["vertices"])] for i in range(3)]
    metadata={
        "cabinet":"pop'n music Sunny Park — white HD cabinet",
        "design":"White HD cabinet with tilted 16:9 screen, nine shallow domed buttons, paired orange speaker pods, cyan console trim, separate shaped topper.",
        "button_layout":{"front_player_left_to_right":["white","green","red","green","white"],"back_player_left_to_right":["yellow","blue","blue","yellow"]},
        "topology":{"button_segments":32,"button_profile_bands":9,"woofer_segments":48,"tweeter_segments":32},
        "source_face_count":len(g.faces),"geometry_bounds_pixels":bounds,
        "texture_regions":{"details":{"speaker_badge":[0,0,8,8],"card_reader":[8,0,16,8],"semicircle_art":[0,8,8,16],"coin_panel":[8,8,16,16]},
            "console":"full UV: U from x=18.7 to -2.7; V from z=8.2 (rear) to -3.1 (front)",
            "front":"full UV on main service door x=3.66..16.09, y=1.25..15.05; viewer right coin strip is separate",
            "side":"full UV projected from y=.95..31.10 and z=.05..14.80", "screen":"full 16:9 landscape image", "marquee":"opaque art mapped to a physical die-cut silhouette"},
    }
    return g,metadata


if __name__=="__main__":
    g,m=build()
    print(m)
