"""Ivory Mech Suit: articulated, smooth armor, edited as procedural source.

Coordinates are Minecraft blocks: Y up, nose toward -Z, feet at zero.
The exported immutable meshes are replayed by MechSuitRenderer. No geometry is
built during a frame; small recesses use material contrast, not tiny cylinders.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
ART = ROOT / 'art/mech_suit'
COLORS = {
    'ivory': 0xE7E8E1, 'white': 0xF6F6EC, 'edge': 0xBFC6C4,
    'dark': 0x20232A, 'black': 0x0D1119, 'metal': 0x525965,
    'gold': 0xC5992E, 'goldlight': 0xF1CF61, 'red': 0x6E192D,
    'redlight': 0xB83C4D, 'cyan': 0x42DED9, 'cyanlight': 0xC3FFFF,
}
PARTS = {}
COMPONENTS = Counter()


def add(a, b): return tuple(x+y for x, y in zip(a, b))
def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(v):
    length = math.sqrt(sum(x*x for x in v))
    return mul(v, 1/length) if length > 1e-9 else (0, 1, 0)


def triangulate(points):
    """Ear clip the occasional concave blade/visor without filling its cutouts."""
    area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    order=list(range(len(points)))
    if area<0: order.reverse()
    result=[]
    def orient(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(order)>3:
        for j,b in enumerate(order):
            a,c=order[j-1],order[(j+1)%len(order)]
            if orient(points[a],points[b],points[c])<=1e-10: continue
            if any(orient(points[a],points[b],points[p])>=-1e-10 and orient(points[b],points[c],points[p])>=-1e-10 and orient(points[c],points[a],points[p])>=-1e-10 for p in order if p not in (a,b,c)): continue
            result.append((a,b,c));order.pop(j);break
        else:
            raise ValueError('Self-intersecting outline: '+str(points))
    result.append(tuple(order))
    return result


def part(name, parent, pivot):
    PARTS[name] = dict(name=name, parent=parent, pivot=pivot, faces=[])


def mesh(part_name, label, verts, faces, material='ivory', smooth=False, emission=False):
    normals = [unit(cross(sub(verts[f[1]], verts[f[0]]), sub(verts[f[2]], verts[f[0]]))) for f in faces]
    averaged = [(0, 0, 0)]*len(verts)
    if smooth:
        for ids, normal in zip(faces, normals):
            for i in ids: averaged[i] = add(averaged[i], normal)
        averaged = [unit(v) for v in averaged]
    for ids, normal in zip(faces, normals):
        expanded = list(ids) if len(ids) == 4 else list(ids)+[ids[-1]]
        data = []
        for i in expanded:
            data.extend(round(v, 5) for v in (*verts[i], *(averaged[i] if smooth else normal)))
        PARTS[part_name]['faces'].append([COLORS[material], int(emission), data])
    COMPONENTS[label] += len(faces)


def loft(name, label, profile, material='ivory', segments=14, smooth=True):
    """Each profile is (center X, Y, center Z, radius X, radius Z)."""
    verts = [(x+rx*math.cos(i*math.tau/segments), y, z+rz*math.sin(i*math.tau/segments))
             for x, y, z, rx, rz in profile for i in range(segments)]
    faces = []
    for j in range(len(profile)-1):
        for i in range(segments):
            n = (i+1) % segments
            faces.append((j*segments+i, (j+1)*segments+i, (j+1)*segments+n, j*segments+n))
    # End caps remain flat and do not change the side surface normals.
    mesh(name, label, verts, faces, material, smooth)
    for end, reverse in ((0, False), (len(profile)-1, True)):
        ring = verts[end*segments:(end+1)*segments]
        center = tuple(sum(p[i] for p in ring)/segments for i in range(3))
        cap = [center]+ring
        ids = [(0, i+1, (i+1) % segments+1) if reverse else (0, (i+1) % segments+1, i+1) for i in range(segments)]
        mesh(name, label, cap, ids, material)


def ellipsoid(name, label, center, radii, material='ivory', segments=12, rings=6):
    x, y, z = center
    rx, ry, rz = radii
    profile = []
    for j in range(rings+1):
        t = math.pi*(-.5+j/rings)
        profile.append((x, y+ry*math.sin(t), z, max(.001,rx*math.cos(t)), max(.001,rz*math.cos(t))))
    loft(name, label, profile, material, segments)


def rod(name, label, start, end, radius, material='dark', segments=10, end_radius=None):
    axis = unit(sub(end, start))
    tangent = unit(cross(axis, (1,0,0) if abs(axis[0]) < .8 else (0,0,1)))
    bitangent = cross(axis, tangent)
    verts = []
    for c, r in ((start,radius), (end, radius if end_radius is None else end_radius)):
        for i in range(segments):
            theta = i*math.tau/segments
            verts.append(add(c, add(mul(tangent, r*math.cos(theta)), mul(bitangent, r*math.sin(theta)))))
    faces = [(i, (i+1)%segments, segments+(i+1)%segments, segments+i) for i in range(segments)]
    mesh(name, label, verts, faces, material, True)
    # Every axis beam has closed ends, since fingers and thrusters can be seen end-on.
    for base, c, flip in ((0, start, True), (segments,end,False)):
        cap = [c]+verts[base:base+segments]
        ids = [(0,(i+1)%segments+1,i+1) if flip else (0,i+1,(i+1)%segments+1) for i in range(segments)]
        mesh(name, label, cap, ids, material)


def plate(name, label, outline, z, thickness=.035, material='ivory', bevel=.06, belly=.025):
    """Convex XY armor plate with a beveled edge and gently crowned front."""
    count = len(outline)
    center = tuple(sum(p[i] for p in outline)/count for i in range(2))
    verts = []
    for scale, depth in ((1,z+thickness), (1,z), (1-bevel,z-belly), (.45,z-belly*1.25)):
        verts.extend((center[0]+(x-center[0])*scale, center[1]+(y-center[1])*scale, depth) for x,y in outline)
    # Ensure outline points are CCW as viewed in XY. Front is -Z.
    area = sum(outline[i][0]*outline[(i+1)%count][1]-outline[(i+1)%count][0]*outline[i][1] for i in range(count))
    faces = []
    for ring in range(3):
        for i in range(count):
            n = (i+1)%count
            f=(ring*count+i, (ring+1)*count+i, (ring+1)*count+n, ring*count+n)
            faces.append(f if area > 0 else tuple(reversed(f)))
    mesh(name, label, verts, faces, material, True)
    front = [tuple(3*count+i for i in reversed(f)) for f in triangulate(outline)]
    mesh(name,label,verts,front,material)
    back = triangulate(outline)
    mesh(name,label,verts,back,'dark')


def port(name, label, x, y, z, radius=.085, direction=-1):
    """Recessed red apertures; white lip + dark cavity + red inner lens."""
    segments=10
    profile=[(radius,z+.007*direction),(radius*.96,z+.025*direction),
             (radius*.68,z+.03*direction),(radius*.59,z+.01*direction),
             (radius*.37,z+.014*direction)]
    verts=[(x+r*math.cos(i*math.tau/segments),y+r*math.sin(i*math.tau/segments),depth)
           for r,depth in profile for i in range(segments)]
    for j, mat in enumerate(('edge','white','black','red')):
        faces=[]
        for i in range(segments):
            n=(i+1)%segments
            f=(j*segments+i,j*segments+n,(j+1)*segments+n,(j+1)*segments+i)
            faces.append(tuple(reversed(f)) if direction < 0 else f)
        mesh(name,label,verts,faces,mat,True)
    ring=verts[-segments:]
    cap=[(x,y,z+.016*direction)]+ring
    faces=[(0,i+1,(i+1)%segments+1) for i in range(segments)]
    if direction<0: faces=[tuple(reversed(f)) for f in faces]
    mesh(name,label,cap,faces,'redlight')


def gem(name,label,outline,z,material='cyan',direction=-1):
    if direction == 1:
        before=len(PARTS[name]['faces'])
        gem(name,label,outline,-z,material)
        for face in PARTS[name]['faces'][before:]:
            raw=face[2]
            vertices=[raw[i:i+6] for i in range(0,24,6)]
            triangle=vertices[2]==vertices[3]
            if triangle:vertices.pop()
            for vertex in vertices:vertex[2]*=-1;vertex[5]*=-1
            vertices.reverse()
            if triangle:vertices.append(vertices[-1])
            face[2]=[value for vertex in vertices for value in vertex]
        return
    plate(name,label,outline,z,.012,'dark',.13,.018)
    cx=sum(p[0] for p in outline)/len(outline); cy=sum(p[1] for p in outline)/len(outline)
    points=[(cx+(x-cx)*.73,cy+(y-cy)*.78,z-.044) for x,y in outline]
    area=sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    verts=[(cx,cy,z-.065)]+points
    faces=[(0,i+1,(i+1)%len(points)+1) for i in range(len(points))]
    if area>0: faces=[tuple(reversed(f)) for f in faces]
    mesh(name,label,verts,faces,material,False,True)


def leaf_outline(cx,cy,width,height,lean=0,steps=24):
    # Pointed leaf, offset at the crown; sin gives a smooth narrow tip.
    points=[]
    for i in range(steps):
        t=i*math.tau/steps
        yy=math.cos(t)
        wave=math.sin(t)
        xx=math.copysign(abs(wave)**1.5,wave)*(0.60+.40*(yy+1)/2)
        points.append((cx+xx*width/2+lean*yy,cy+yy*height/2))
    return points


def orient_shield(name,side):
    """Lay the broad dark inner face against the outer forearm, white face outward."""
    center_x=side*1.51;center_z=.13
    angle=-side*math.pi/2
    c,s=math.cos(angle),math.sin(angle)
    PARTS[name]['pivot']=(center_x,3.40,center_z)
    for face in PARTS[name]['faces']:
        raw=face[2]
        for i in range(0,24,6):
            dx,dz=raw[i]-center_x,raw[i+2]-center_z
            nx,nz=raw[i+3],raw[i+5]
            raw[i]=round(center_x+c*dx+s*dz,5)
            raw[i+2]=round(center_z-s*dx+c*dz,5)
            raw[i+3]=round(c*nx+s*nz,5)
            raw[i+5]=round(-s*nx+c*nz,5)


def orient_sword(name,side):
    """Both tips point forward/down in their grips, rather than flaring sideways."""
    center_x=side*1.02;center_z=-.07
    angle=side*math.pi/2
    c,s=math.cos(angle),math.sin(angle)
    PARTS[name]['pivot']=(center_x,2.84,center_z)
    for face in PARTS[name]['faces']:
        raw=face[2]
        for i in range(0,24,6):
            dx,dz=raw[i]-center_x,raw[i+2]-center_z
            nx,nz=raw[i+3],raw[i+5]
            raw[i]=round(center_x+c*dx+s*dz,5)
            raw[i+2]=round(center_z-s*dx+c*dz,5)
            raw[i+3]=round(c*nx+s*nz,5)
            raw[i+5]=round(-s*nx+c*nz,5)


def build():
    part('torso','',(0,3.25,0))
    part('pelvis','torso',(0,2.83,0))
    part('head','torso',(0,4.16,0))
    # Narrow dark skeleton makes the armor plates legible and keeps the waist articulated.
    loft('torso','spine',[(0,2.84,.10,.20,.20),(0,3.15,.10,.23,.21),(0,3.70,.06,.39,.27),(0,4.02,.04,.34,.25)],'dark',12)
    for y in (3.05,3.18,3.31):
        loft('torso','abdominal ribs',[(0,y-.045,-.11,.22,.21),(0,y,-.16,.285,.24),(0,y+.045,-.10,.235,.22)],'ivory',12)
    ellipsoid('torso','rib armor',(0,3.78,0),(.67,.37,.36),'ivory',18,7)
    plate('torso','breastplate',[(-.38,3.96),(-.54,3.75),(-.36,3.53),(0,3.46),(.36,3.53),(.54,3.75),(.38,3.96)],-.315,.08,'white',.09,.105)
    plate('torso','gold breast beak',[(-.20,3.68),(-.14,3.47),(0,3.35),(.14,3.47),(.20,3.68)],-.44,.045,'gold',.16,.10)
    gem('torso','chest core',[(-.105,4.00),(-.14,3.85),(0,3.79),(.14,3.85),(.105,4.00)],-.39)
    for s in (-1,1):
        for x,y,r,z in ((.35,3.96,.10,-.453),(.54,3.77,.10,-.416),(.37,3.52,.095,-.414)):
            ellipsoid('torso','chest port housings',(s*x,y,z+.092),(r*1.19,r*1.17,.10),'ivory',10,4)
            port('torso','chest ports',s*x,y,z,r)
        rod('torso','collar cables',(s*.25,4.0,.12),(s*.16,4.24,.08),.08,'metal',8)
    ellipsoid('pelvis','pelvis joint',(0,2.82,.02),(.37,.25,.26),'dark',12,5)
    plate('pelvis','waist buckle',[(-.29,2.92),(-.24,2.69),(0,2.64),(.24,2.69),(.29,2.92)],-.23,.04,'ivory',.10,.05)
    port('pelvis','waist port',0,2.93,-.29,.09)
    plate('pelvis','pointed skirt',[(-.23,2.73),(-.17,2.37),(0,2.22),(.17,2.37),(.23,2.73)],-.24,.075,'white',.1,.065)
    gem('pelvis','waist core',[(-.095,2.73),(-.08,2.46),(0,2.41),(.08,2.46),(.095,2.73)],-.35)
    for s in (-1,1):
        outline=[(s*x,y) for x,y in ((.26,2.85),(.53,2.84),(.67,2.42),(.45,2.28),(.30,2.57))]
        plate('pelvis','hip plates',outline,-.1,.16,'ivory',.11,.06)
        # Rear engine has a central spine, side boosters, and long pointed back fins.
        rod('torso','rear exhaust',(s*.24,3.88,.43),(s*.24,3.44,.52),.15,'metal',12)
        port('torso','rear thruster',s*.24,3.91,.555,.13,1)
        port('torso','rear thruster',s*.24,3.65,.625,.095,1)
        outline=[(s*x,y) for x,y in ((.29,4.18),(.49,4.39),(.63,4.15),(.57,3.41),(.41,3.02),(.34,3.65))]
        plate('torso','rear fins',outline,.58,.14,'ivory',.09,.015)
        gem('torso','rear cyan',[(s*x,y) for x,y in ((.38,4.17),(.43,4.25),(.51,4.13),(.43,3.86))],.545)
    # Crown/helmet uses a smooth oval shell, long center crest, and a narrow masked face.
    rod('head','neck',(0,4.07,0),(0,4.34,0),.16,'dark',12)
    loft('head','helmet',[(0,4.23,.03,.15,.18),(0,4.35,.02,.25,.23),(0,4.56,.035,.25,.24),(0,4.72,.06,.13,.16),(0,4.79,.10,.025,.06)],'ivory',16)
    plate('head','helmet crest',[(-.09,4.62),(-.08,4.82),(0,5.0),(.085,4.84),(.13,4.68)],-.15,.21,'white',.08,.025)
    gem('head','crest cyan',[(-.038,4.68),(0,4.90),(.04,4.68),(0,4.62)],-.205)
    plate('head','red eye visor',[(-.23,4.51),(-.15,4.39),(0,4.36),(.15,4.39),(.23,4.51),(0,4.45)],-.222,.02,'red',.03,.032)
    for s in (-1,1):
        gem('head','eyes',[(s*x,y) for x,y in ((.025,4.455),(.195,4.48),(.13,4.417),(.055,4.411))],-.268,'cyanlight')
        plate('head','cheek guard',[(s*x,y) for x,y in ((.15,4.39),(.20,4.31),(.105,4.18),(.075,4.37))],-.22,.09,'white',.05,.045)
        plate('head','gold horn',[(s*x,y) for x,y in ((.16,4.50),(.28,4.55),(.60,4.80),(.47,4.51),(.25,4.43))],-.12,.035,'gold',.05,.032)
        port('head','temple port',s*.232,4.51,-.10,.047)
    plate('head','chin mask',[(-.075,4.36),(-.06,4.22),(0,4.17),(.06,4.22),(.075,4.36),(0,4.32)],-.27,.03,'white',.07,.045)
    gem('head','mouth core',[(-.03,4.35),(0,4.31),(.03,4.35),(0,4.38)],-.33)

    for s, side in ((-1,'left'),(1,'right')):
        arm='upper_arm_'+side; fore='forearm_'+side; sword='sword_'+side; wing='wing_'+side
        thigh='thigh_'+side; shin='shin_'+side; foot='foot_'+side
        part(arm,'torso',(s*.70,3.97,0))
        part(fore,arm,(s*.91,3.44,0))
        part(sword,fore,(s*1.01,2.84,-.05))
        part(wing,fore,(s*1.03,3.40,.11))
        part(thigh,'pelvis',(s*.37,2.74,.02))
        part(shin,thigh,(s*.52,1.60,.03))
        part(foot,shin,(s*.59,.40,-.03))
        ellipsoid(arm,'shoulder joint',(s*.71,3.97,.02),(.24,.23,.23),'dark',12,5)
        loft(arm,'upper arm',[(s*.94,3.45,.02,.14,.15),(s*.93,3.68,0,.21,.22),(s*.80,3.95,0,.22,.22)],'ivory',14)
        ellipsoid(arm,'shoulder cap',(s*.82,4.04,.00),(.32,.20,.30),'ivory',14,6)
        outline=[(s*x,y) for x,y in ((.67,4.12),(.86,4.14),(1.01,4.49),(.99,4.08),(.94,3.99))]
        plate(arm,'pointed shoulder',outline,-.05,.19,'white',.03,.025)
        outline=[(s*x,y) for x,y in ((.85,4.14),(.89,4.19),(1.01,4.49),(.975,4.21),(.92,4.07))]
        plate(arm,'shoulder gold edge',outline,-.090,.016,'gold',.02,.004)
        port(arm,'shoulder port',s*.85,4.03,-.318,.066)
        ellipsoid(fore,'elbow',(s*.91,3.45,0),(.15,.16,.16),'dark',12,5)
        loft(fore,'forearm armor',[(s*1.03,2.98,-.015,.14,.17),(s*1.04,3.15,-.005,.23,.26),(s*.94,3.38,0,.18,.20)],'ivory',14)
        plate(fore,'forearm blade',[(s*x,y) for x,y in ((1.0,3.15),(1.11,3.29),(1.10,3.66),(.97,3.41),(.92,3.16))],-.20,.04,'white',.06,.055)
        plate(fore,'forearm gold',[(s*x,y) for x,y in ((1.02,3.35),(1.10,3.64),(1.12,3.28),(1.07,3.19))],-.225,.012,'gold',.01,.01)
        ellipsoid(fore,'wrist',(s*1.025,2.94,-.03),(.12,.12,.12),'metal',10,4)
        loft(fore,'hand',[(s*1.025,2.70,-.06,.11,.12),(s*1.025,2.82,-.07,.145,.14),(s*1.025,2.96,-.05,.12,.11)],'dark',10,False)
        for k in range(3):
            rod(fore,'fingers',(s*(.94+k*.065),2.84,-.184),(s*(.94+k*.065),2.705,-.19),.032,'metal',6)
        # Broad leaf-shaped shields are distinct shells, not thick flat slabs.
        outline=leaf_outline(s*1.51,3.40,1.22,2.26,lean=s*.12,steps=28)
        plate(wing,'wing shield shell',outline,.13,.14,'ivory',.055,.17)
        # A clean dark inner shield visible from behind. It sits beyond the back face.
        inner=[(s*1.51+(x-s*1.51)*.82,3.40+(y-3.40)*.88) for x,y in outline]
        plate(wing,'wing shield inner',inner,.303,.028,'dark',.035,.012)
        # Crown gold medallion, six small dark teardrop vents, and red inner lenses.
        port(wing,'shield circular boss',s*1.50,3.73,-.085,.15)
        plate(wing,'shield gold motif',[(s*x,y) for x,y in ((1.41,3.72),(1.51,3.67),(1.75,3.98),(1.58,3.83),(1.46,3.85))],-.14,.02,'gold',.05,.012)
        for idx,(dx,y) in enumerate(((.0,4.14),(-.18,3.98),(.20,4.01),(-.25,3.70),(.22,3.52),(-.23,3.40))):
            x=s*(1.51+dx)
            outline=[]
            for i in range(12):
                t=i*math.tau/12
                yy=math.cos(t)
                outline.append((x+.045*math.sin(t)*(.56+.44*(yy+1)/2), y+.12*yy))
            plate(wing,'shield teardrop vents',outline,-.09,.006,'dark',.10,.008)
            ellipsoid(wing,'shield vent red', (x,y+.010,-.105),(.022,.023,.007),'redlight',8,3)
        # Rear bracing and glowing engine ribbons remain readable when airborne.
        rod(wing,'wing brace',(s*1.43,3.10,.354),(s*1.54,4.03,.354),.045,'metal',8)
        rod(wing,'wing engine',(s*1.60,3.85,.38),(s*1.57,3.20,.38),.073,'black',10)
        for yy in (3.28,3.43,3.58):
            gem(wing,'wing vents cyan',[(s*1.51,yy),(s*1.65,yy+.04),(s*1.65,yy+.09),(s*1.51,yy+.05)],.44,direction=1)
        orient_shield(wing,s)
        rod(fore,'shield mounting cuff',(s*1.17,3.18,.13),(s*1.32,3.18,.13),.115,'metal',10)
        # Curved black katana-like cleavers, with a real narrow metal edge.
        rod(sword,'sword grip',(s*1.02,2.56,-.07),(s*1.02,2.93,-.07),.060,'black',10)
        for yy in (2.58,2.64,2.70,2.76,2.82):
            rod(sword,'grip bands',(s*1.02,yy,-.07),(s*1.02,yy+.016,-.07),.064,'metal',8)
        rod(sword,'sword guard',(s*.86,2.64,-.07),(s*1.20,2.64,-.07),.045,'gold',10)
        # Sword sweeps outward, narrowing to a point; broad face remains dark.
        shape=[(1.02,2.62),(1.12,2.40),(1.31,2.17),(1.66,1.95),(2.05,1.76),
               (2.47,1.54),(2.85,1.28),(2.67,1.60),(2.28,1.91),(1.89,2.13),
               (1.51,2.30),(1.27,2.45),(1.14,2.64)]
        plate(sword,'curved sword',[(s*x,y) for x,y in shape],-.15,.085,'black',.055,.012)
        edge=[(1.11,2.45),(1.31,2.20),(1.66,1.985),(2.06,1.80),(2.48,1.58),(2.85,1.28),
              (2.47,1.54),(2.05,1.76),(1.66,1.95),(1.31,2.17),(1.12,2.40)]
        plate(sword,'sword silver edge',[(s*x,y) for x,y in edge],-.169,.013,'edge',0,.002)
        # The real cutting bevel is silver from either side. Without the reverse
        # ribbon, the mirrored left blade could read as backwards in oblique views.
        back_outline=[(s*x,y) for x,y in edge]
        mesh(sword,'reverse cutting edge',[(x,y,-.054) for x,y in back_outline],
             triangulate(back_outline),'edge')
        orient_sword(sword,s)
        # Athletic legs: slim skeleton, rounded tapered plates and pointed gold feet.
        rod(thigh,'hip axle',(s*.28,2.67,.02),(s*.55,2.62,.02),.145,'metal',10)
        loft(thigh,'thigh',[(s*.52,1.82,.04,.19,.20),(s*.48,2.10,0,.28,.30),(s*.38,2.50,0,.27,.28),(s*.36,2.65,.01,.17,.18)],'ivory',16)
        plate(thigh,'thigh front',[(s*x,y) for x,y in ((.29,2.46),(.46,2.57),(.62,2.09),(.54,1.93),(.39,2.14))],-.255,.034,'white',.07,.045)
        ellipsoid(shin,'knee',(s*.52,1.62,.045),(.18,.18,.18),'dark',12,5)
        plate(shin,'pointed knee',[(s*x,y) for x,y in ((.37,1.81),(.52,2.07),(.68,1.81),(.59,1.51),(.46,1.51))],-.18,.1,'white',.08,.065)
        plate(shin,'knee gold',[(s*x,y) for x,y in ((.49,1.88),(.53,2.07),(.59,1.89),(.56,1.73))],-.269,.02,'gold',.03,.006)
        loft(shin,'shin',[(s*.59,.49,.055,.16,.18),(s*.62,.74,.015,.25,.29),(s*.58,1.09,.015,.29,.32),(s*.52,1.46,.035,.18,.19)],'ivory',16)
        plate(shin,'shin crest',[(s*x,y) for x,y in ((.46,1.38),(.54,1.54),(.72,.98),(.64,.52),(.50,.58),(.45,1.00))],-.255,.065,'white',.065,.04)
        for yy,r in ((.68,.058),(1.19,.045)):
            port(shin,'leg ports',s*.61,yy,-.32,r)
        ellipsoid(foot,'ankle',(s*.59,.38,-.02),(.15,.12,.15),'dark',10,4)
        loft(foot,'foot shell',[(s*.59,.12,-.22,.17,.33),(s*.59,.21,-.23,.24,.39),(s*.59,.35,-.13,.19,.29),(s*.59,.43,-.04,.12,.16)],'ivory',12)
        # Gold armored toes extend toward the player and terminate in a pointed edge.
        loft(foot,'gold toe',[(s*.59,.09,-.36,.16,.34),(s*.59,.16,-.41,.21,.32),(s*.59,.27,-.39,.15,.20)],'gold',10)
        plate(foot,'toe tip',[(s*.43,.14),(s*.59,.28),(s*.75,.14),(s*.59,.055)],-.72,.055,'goldlight',.025,.007)
        # Short rear heel spur, matching the reference's bird-like gold heel.
        rod(foot,'heel claw',(s*.60,.18,.19),(s*.60,.10,.39),.09,'gold',8,end_radius=.012)


def write():
    ART.mkdir(parents=True,exist_ok=True)
    (ASSETS/'meshes').mkdir(parents=True,exist_ok=True)
    output=dict(format=1,units='blocks',height=5.0,front='-Z',parts=list(PARTS.values()))
    raw=json.dumps(output,separators=(',',':'))+'\n'
    (ASSETS/'meshes/mech_suit.json').write_text(raw,encoding='utf-8')
    # Shared by Blender and runtime; no duplicated geometry export to drift out of sync.
    counts={name:len(p['faces']) for name,p in PARTS.items()}
    for name,p in PARTS.items():
        for _,_,raw in p['faces']:
            vertices=[raw[i:i+3] for i in range(0,24,6)]
            area=cross(sub(vertices[1],vertices[0]),sub(vertices[2],vertices[0]))
            assert sum(value*value for value in area)>1e-18, (name,'zero-area exported face',vertices)
            assert all(math.isfinite(value) for value in raw), name
    audit=dict(total_faces=sum(counts.values()),total_vertices=sum(counts.values())*4,
               item_model='minecraft:item/generated deployment controller (extruded 32 px icon)',
               parts=counts,components=dict(COMPONENTS),height_blocks=5.0,
               under_10000_faces=sum(counts.values())<10000)
    audit['sword_rest_tip_center_vectors']={}
    for name,p in PARTS.items():
        if not name.startswith('sword_'):continue
        verts=[f[2][i:i+3] for f in p['faces'] for i in range(0,24,6)]
        lowest=min(v[1] for v in verts)
        tips=[v for v in verts if abs(v[1]-lowest)<1e-6]
        tip=[(min(v[i] for v in tips)+max(v[i] for v in tips))/2 for i in range(3)]
        audit['sword_rest_tip_center_vectors'][name]=[round(tip[i]-p['pivot'][i],5) for i in range(3)]
    (ART/'face-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    textures=ASSETS/'textures/entity';textures.mkdir(parents=True,exist_ok=True)
    Image.new('RGBA',(16,16),(255,255,255,255)).save(textures/'mech_suit.png')
    # The prize is a deployment controller, so inventory never renders the complete mech.
    image=Image.new('RGBA',(32,32),(0,0,0,0)); d=ImageDraw.Draw(image)
    d.polygon([(7,3),(24,3),(28,7),(28,25),(24,29),(7,29),(3,25),(3,7)],fill='#252A34')
    d.polygon([(8,5),(23,5),(26,8),(26,24),(23,27),(8,27),(5,24),(5,8)],fill='#DDE2DF')
    d.rectangle((8,8,23,21),fill='#172B37');d.rectangle((9,9,22,20),fill='#216170')
    d.polygon([(11,11),(13,13),(15,11),(16,9),(18,11),(20,13),(21,11),(20,17),(18,19),(13,19),(11,17)],fill='#F1EDDA')
    d.rectangle((14,14,18,15),fill='#57FFFF');d.point((16,17),fill='#C5A243')
    d.rectangle((10,23,13,24),fill='#CDA540');d.rectangle((18,23,21,24),fill='#64E7DD')
    d.line((7,6,24,6),fill='#FFFFFF');d.line((6,8,6,24),fill='#F6F7EE')
    itemtextures=ASSETS/'textures/item';itemtextures.mkdir(parents=True,exist_ok=True)
    image.save(itemtextures/'mech_suit.png')
    # ItemModelGenerator emits two main faces and one span per direction/anchor.
    spans=set()
    def solid(x,y): return 0<=x<32 and 0<=y<32 and image.getpixel((x,y))[3]>0
    for y in range(32):
        for x in range(32):
            if not solid(x,y):continue
            for facing,dx,dy in (('up',0,-1),('down',0,1),('left',-1,0),('right',1,0)):
                if not solid(x+dx,y+dy):spans.add((facing,y if dy else x))
    audit['inventory_faces']=2+len(spans)
    (ART/'face-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    itemmodel=dict(parent='minecraft:item/generated',textures={'layer0':'japanesearcades:item/mech_suit'})
    (ASSETS/'models/item/mech_suit.json').write_text(json.dumps(itemmodel,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__ == '__main__':
    build()
    write()
