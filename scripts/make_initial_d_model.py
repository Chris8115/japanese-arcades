"""Single-width classic Initial D Stage 3 sit-down cabinet and bucket seat."""
import math
from pathlib import Path
from PIL import Image, ImageDraw
from initial_d_geometry import Geometry,export
from initial_d_textures import build_textures

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/initial_d'
ASSETS=ROOT/'src/main/resources/assets/funpackcustom';TEX=ASSETS/'textures/block'
for p in (ART,TEX,ASSETS/'models/block',ASSETS/'models/item',ASSETS/'blockstates'):p.mkdir(parents=True,exist_ok=True)
build_textures(TEX)
COLORS={'white':'#eceee8','ivory':'#d9ddd5','silver':'#aab2b3','edge':'#727c7e',
    'black':'#15191b','dark':'#30383b','seat':'#4f5556','seat_light':'#6a7070',
    'green':'#27744d','lime':'#6aa65a','red':'#aa343b','blue':'#4b88b1',
    'yellow':'#dac45b','chrome':'#d1d7d8','glass':'#243a43','rubber':'#242a2b'}
atlas=Image.new('RGB',(256,256));d=ImageDraw.Draw(atlas)
for i,col in enumerate(COLORS.values()):
    x,y=(i%4)*64,(i//4)*64;d.rectangle((x,y,x+63,y+63),fill=col)
atlas.save(TEX/'initial_d_materials.png')
g=Geometry(COLORS);box=g.box;rounded=g.rounded;face=g.face;decal=g.decal;disc=g.disc;tube=g.tube

g.group='Compact single white upright'
profile=[(.8,4.0),(15.2,4.0),(18.6,.90),(32.7,4.92),(33.12,14.87),(.8,14.87)]
g.yz_shell('Angular cream monitor carcass',.64,15.36,profile,'white')
rounded('Upright charcoal base',(.65,.18,15.35,1.21),3.60,15.10,.14,'black')
rounded('White lower coin panel',(1.07,1.29,14.93,15.62),3.77,4.12,.18,'white')
rounded('Upright coin service door',(5.43,3.42,10.57,12.91),3.64,3.79,.19,'dark')
box('Silver coin inlet',(6.17,10.74,3.59),(9.83,11.26,3.65),'silver')
box('Coin insertion shadow',(6.68,10.91,3.575),(9.32,11.08,3.603),'black')
rounded('Coin return pocket',(6.32,6.09,9.68,7.55),3.61,3.66,.13,'black')
disc('Coin door key',9.89,4.47,.14,3.58,3.67,'silver',16)
for x in (1.37,14.19):box('Front white case seam '+str(x),(x,2.0,3.735),(x+.045,14.62,3.79),'ivory')

g.group='Sloped CRT and single marquee'
start=len(g.faces)
rounded('Thick black CRT bezel',(.98,19.35,15.02,32.58),.66,1.14,.28,'black')
rounded('CRT glass recessed rim',(1.32,21.14,14.68,31.25),.613,.69,.24,'edge')
decal('Mountain pass racing CRT',(1.56,21.40,14.44,31.06),.596,'screen',True)
rounded('Lower CRT bezel lip',(1.26,19.56,14.74,21.15),.581,.67,.14,'dark')
for x in (1.78,14.22):disc('CRT bottom fixing '+str(x),x,19.95,.067,.55,.59,'silver',12)
g.transform(start,lambda x,y,z:(x,y,z+(y-19.35)*.245))
rounded('Upper twin-speaker bar',(.82,32.58,15.18,34.24),4.13,7.65,.22,'white')
for x in (1.58,10.13):
    rounded('Marquee black speaker '+str(x),(x,32.91,x+4.30,33.96),4.106,4.16,.17,'black')
    for row in range(3):box('Speaker grille line %s %s'%(x,row),(x+.30,33.09+row*.24,4.09),(x+4.01,33.15+row*.24,4.115),'dark')
for x in (2.15,12.97):box('Independent topper bracket '+str(x),(x,33.54,7.47),(x+.88,34.91,8.42),'dark')
rounded('One-player white marquee frame',(.32,34.15,15.68,41.0),5.89,8.66,.22,'white')
rounded('Topper thin green inner rim',(.62,34.48,15.38,40.68),5.77,5.92,.12,'green')
decal('Single Initial D Stage 3 marquee',(.79,34.65,15.21,40.51),5.756,'marquee',True)
box('Topper black rear band',(.40,34.22,8.57),(15.60,40.91,8.83),'dark')

g.group='Racing case decals'
for x,left in ((.621,True),(15.379,False)):
    # Side art spans the lower upright, away from the sloped front edge.
    pts=[(x,31.51,14.60),(x,2.37,14.60),(x,2.37,4.35),(x,31.51,4.35)];uv=[(0,0),(0,16),(16,16),(16,0)]
    if left:uv=[(16-u,v) for u,v in uv];pts.reverse();uv.reverse()
    face('Upright Initial D side print '+str(left),pts,texture='side',uv=uv)
rounded('Back access door',(1.47,2.35,14.53,31.72),14.878,14.98,.12,'ivory')
for row in range(8):box('Rear cooling vent '+str(row),(5.11,23.39+row*.39,14.987),(10.89,23.54+row*.39,15.026),'dark')
for x in (1.89,14.11):
    for y in (2.88,30.84):box('Rear casing screw %s %s'%(x,y),(x-.06,y-.06,14.99),(x+.06,y+.06,15.03),'chrome')

g.group='Low connector and pedal well'
box('Full single-machine underframe',(.67,.05,-31.39),(15.33,.70,14.85),'black')
box('Slim silver connecting platform',(1.05,.65,-30.97),(14.95,1.24,4.16),'silver')
box('Black floor insert',(1.34,1.235,-19.16),(14.66,1.46,3.98),'rubber')
for x in (1.07,14.19):
    box('Low molded green sill '+str(x),(x,1.2,-30.20),(x+.74,3.00,-1.82),'green')
    box('Silver sill top edge '+str(x),(x,2.96,-30.22),(x+.74,3.12,-1.8),'silver')
for x,left in ((1.04,True),(14.96,False)):
    pts=[(x,2.96,-1.84),(x,.80,-1.84),(x,.80,-30.35),(x,2.96,-30.35)];uv=[(0,0),(0,16),(16,16),(16,0)]
    if left:uv=[(16-u,v) for u,v in uv];pts.reverse();uv.reverse()
    face('Connecting floor side logo '+str(left),pts,texture='pedestal_side',uv=uv)
for x in (2.6,3.6,4.6,5.6,6.6,7.6,8.6,9.6,10.6,11.6,12.6):box('Floor non-slip raised rib '+str(x),(x,1.47,-15.4),(x+.13,1.55,-4.9),'dark')
g.yz_shell('Sloped pedal housing',3.40,12.60,[(1.5,-6.63),(1.5,-.3),(5.65,-.3),(5.65,-1.25)],'dark')
for x,w,label in ((4.4,2.8,'Brake'),(9.05,1.75,'Accelerator')):
    start=len(g.faces);box(label+' pedal',(x,2.4,-4.25),(x+w,5.35,-3.75),'silver')
    for row in range(5):box(label+' tread '+str(row),(x+.17,2.66+row*.49,-4.30),(x+w-.17,2.79+row*.49,-4.247),'rubber')
    g.transform(start,lambda X,y,z:(X,y,z+(y-2.4)*.47))

g.group='Dashboard steering and controls'
dash_profile=[(15.76,-6.87),(18.95,-7.60),(20.35,-3.75),(20.35,1.61),(16.60,3.34)]
g.yz_shell('Cream dashboard pod',.83,15.17,dash_profile,'white')
g.yz_shell('Charcoal dashboard upper deck',1.11,14.89,[(18.78,-7.39),(19.22,-7.47),(20.42,-3.69),(20.42,1.48),(19.75,1.74)],'dark')
start=len(g.faces)
rounded('Dashboard green lower face',(1.12,16.02,14.88,18.69),-6.93,-6.75,.22,'green')
decal('Dashboard printed instructions',(1.48,16.21,14.52,18.48),-6.955,'details')
for x in (1.32,14.68):disc('Dashboard fixing '+str(x),x,16.32,.067,-6.974,-6.94,'silver',12)
g.transform(start,lambda x,y,z:(x,y,z-(y-15.76)*(.73/3.19)))
# Steering faces the seat. Its upper edge tilts toward the monitor by 16 degrees.
start=len(g.faces)
g.torus('Black leather steering rim',0,0,0,2.97,.33,'black',40,8)
disc('Steering center rear hub',0,0,.97,-.23,.63,'dark',32)
for i,angle in enumerate((30,150,270)):
    a=math.radians(angle);b=math.radians(angle+13);c=math.radians(angle-13)
    outline=[(.46*math.cos(c),.46*math.sin(c)),(2.80*math.cos(c),2.80*math.sin(c)),
        (2.80*math.cos(b),2.80*math.sin(b)),(.46*math.cos(b),.46*math.sin(b))]
    g.prism('Brushed three-spoke steering '+str(i),outline,-.21,.08,'silver')
disc('Steering black center cap',0,0,.72,-.35,-.20,'black',32)
disc('Steering silver badge',0,0,.28,-.371,-.35,'silver',24)
for a in (0,120,240):
    t=math.radians(a);disc('Steering bolt '+str(a),.47*math.cos(t),.47*math.sin(t),.052,-.369,-.35,'chrome',12)
angle=math.radians(16);c,s=math.cos(angle),math.sin(angle)
g.transform(start,lambda x,y,z:(7.10+x,20.20+y*c-z*s,-7.40+y*s+z*c))
tube('Steering column',[(7.10,20.14,-6.85),(7.10,19.24,-3.7)],.68,'black',16)
# Left/right button positions are kept wholly inside the single-player shell.
for x,mat in ((1.98,'blue'),(3.22,'red'),(12.67,'yellow')):
    disc('Round dash button '+str(x),x,19.46,.35,-6.455,-6.15,'black',20)
    disc('Colored dash button '+str(x),x,19.46,.26,-6.477,-6.445,mat,20)
rounded('Right side sequential-shifter surround',(12.37,18.61,14.59,21.05),-4.31,-3.11,.17,'black')
tube('Sequential shift chrome stick',[(13.48,19.5,-3.81),(13.48,21.6,-4.18)],.16,'chrome',12)
disc('Shift black knob',13.48,21.64,.48,-4.63,-3.79,'black',24)

g.group='Adjustable single gray bucket seat'
rounded('Seat floor mounting block',(2.73,1.32,13.27,5.53),-28.54,-19.2,.33,'dark')
for x in (3.81,11.59):
    box('Seat slider rail '+str(x),(x,5.54,-29.21),(x+.60,7.41,-18.72),'silver')
    box('Seat slider black track '+str(x),(x-.18,7.18,-28.91),(x+.78,8.35,-18.95),'black')
tube('Seat adjustment handle',[(4.2,6.82,-18.73),(4.2,6.82,-17.81),(11.8,6.82,-17.81),(11.8,6.82,-18.73)],.15,'dark',10)
# Cushion is rounded in the horizontal XZ plane, with real sculpted side bolsters.
start=len(g.faces)
rounded('Rounded bucket seat cushion',(3.13,-28.12,12.87,-18.57),-11.50,-8.53,.60,'seat')
g.transform(start,lambda x,z,neg_y:(x,-neg_y,z))
box('Cushion central upholstery',(4.10,11.502,-27.37),(11.90,11.544,-19.44),'seat_light')
for row in range(7):box('Cushion fine horizontal stitch '+str(row),(4.33,11.555,-26.84+row*.97),(11.67,11.577,-26.80+row*.97),'seat')
# Seat back is tapered and leans away from the steering wheel by a few degrees.
back_outline=[(3.12,10.4),(12.88,10.4),(13.62,15.4),(13.20,23.6),(11.50,25.2),(11.06,28.1),
    (4.94,28.1),(4.50,25.2),(2.80,23.6),(2.38,15.4)]
start=len(g.faces);g.prism('Contoured dark bucket back shell',back_outline,-29.15,-27.72,'dark')
rounded('Seat inside central upholstery',(4.1,11.46,11.9,25.10),-27.76,-27.46,.63,'seat_light')
rounded('Raised integrated gray headrest',(4.89,24.12,11.11,27.83),-29.33,-27.38,.56,'seat')
for x in (3.38,11.62):rounded('Seat wraparound side bolster '+str(x),(x,11.1,x+1.0,23.37),-28.40,-26.78,.43,'seat')
for y in (13.2,15.0,16.8,18.6,20.4,22.2):box('Seat back fine stitch '+str(y),(4.46,y,-27.442),(11.54,y+.045,-27.419),'seat')
decal('Initial D branded seat rear',(3.55,12.4,12.45,23.81),-29.171,'seat_back')
for x in (5.17,9.22):rounded('Seat harness dark aperture '+str(x),(x,23.25,x+1.62,24.00),-29.173,-27.38,.14,'black')
g.transform(start,lambda x,y,z:(x,y,z-(y-10.4)*.075))
for x in (2.80,12.12):
    start=len(g.faces);rounded('Cushion raised side bolster '+str(x),(x,-27.58,x+1.08,-19.11),-13.58,-10.71,.45,'seat')
    g.transform(start,lambda X,z,neg_y:(X,-neg_y,z))
disc('Seat rear access fastening',8,11.79,.12,-29.32,-29.18,'silver',16)

textures={key:'funpackcustom:block/initial_d_'+key for key in ('materials','marquee','screen','side','seat_back','pedestal_side','details')}
textures['particle']=textures['materials']
export(ROOT,g,textures,{'seat_geometry':{'cushion_center':[8,11.55,-24],'cushion_top':11.55,
    'cushion_bounds':[[3.13,12.87],[8.53,11.55],[-28.12,-18.57]],'back_top':28.1,
    'rider_facing':'south when cabinet faces north'},'notes':'Single cabinet, all visible geometry inside one-block width. Seven occupied cells; no shared topper or side wings.'})
