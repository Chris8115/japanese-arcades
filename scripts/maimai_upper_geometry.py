"""Paired maimai DX controls, upper displays and shared luminous canopy."""
import math
from PIL import Image


def build_upper(cube,polygon,art_dir):
    centers=(6.4,25.6)
    cy=26.0

    def band(name,cx,inner,outer,z0,z1,material,glow=False,texture=None):
        # All circles share the same Y grid, avoiding narrow face fragments
        # where their concentric layers intersect.
        first=math.floor((cy-outer)/.20)
        last=math.ceil((cy+outer)/.20)
        for row in range(first,last):
            y0=max(cy-outer,row*.20);y1=min(cy+outer,(row+1)*.20)
            if y1-y0<.001:continue
            ym=(y0+y1)/2-cy
            edge=math.sqrt(max(0,outer**2-ym**2))
            hole=math.sqrt(max(0,inner**2-ym**2)) if abs(ym)<inner else 0
            spans=[(-edge,edge)] if hole==0 else [(-edge,-hole),(hole,edge)]
            for segment,(a,b) in enumerate(spans):
                if b-a<.002:continue
                uv=None
                if texture:
                    key,(u0,v0,u1,v1)=texture
                    uv=(key,[u0+(a+outer)/(outer*2)*(u1-u0),
                        v0+(cy+outer-y1)/(outer*2)*(v1-v0),
                        u0+(b+outer)/(outer*2)*(u1-u0),
                        v0+(cy+outer-y0)/(outer*2)*(v1-v0)])
                cube(name+' row '+str((row,segment)),(cx+a,y0,z0),(cx+b,y1,z1),
                     material,north=uv,glow=glow,group='Twin circular control rings')

    def arc(cx,inner,outer,angle,half):
        steps=12
        angles=[angle-half+2*half*i/steps for i in range(steps+1)]
        return [(cx+outer*math.cos(math.radians(a)),cy+outer*math.sin(math.radians(a))) for a in angles]+[
            (cx+inner*math.cos(math.radians(a)),cy+inner*math.sin(math.radians(a))) for a in reversed(angles)]

    for player,cx in enumerate(centers,1):
        prefix='Player '+str(player)+' '
        band(prefix+'white sculpted ring seat',cx,5.52,7.86,-.20,.18,'white')
        band(prefix+'cool white outer luminous halo',cx,7.51,7.69,-.305,-.16,'white',glow=('north',))
        band(prefix+'silver circular surround',cx,5.61,7.43,-.53,-.18,'silver')
        band(prefix+'eight-button backing',cx,5.69,7.28,-.66,-.50,'rim_gray')
        band(prefix+'black inner screen gasket',cx,5.52,5.75,-.72,-.37,'black')
        band(prefix+'round touch display',cx,0,5.55,-.44,-.31,'black',
             glow=('north',),texture=('display',[0,0,16,16]))
        for button in range(8):
            angle=67.5-button*45
            label=prefix+'button '+str(button+1)+' '
            polygon(label+'individual gray socket',arc(cx,5.76,7.30,angle,20.65),
                    -.81,-.61,'steel',group='Sixteen separate ring buttons',step=.16)
            polygon(label+'pale sculpted cap',arc(cx,5.85,7.19,angle,19.25),
                    -.99,-.795,'ivory',group='Sixteen separate ring buttons',step=.16)
            polygon(label+'yellow translucent touch lens',arc(cx,6.02,7.07,angle,14.25),
                    -1.08,-.975,'yellow',glow=('north',),group='Sixteen separate ring buttons',step=.16)
            # A thin white outer lip catches the edge of each curved lens.
            polygon(label+'outer white lens edge',arc(cx,7.065,7.115,angle,13.8),
                    -1.092,-1.035,'white',group='Sixteen separate ring buttons',step=.16)
        # Four molded white radial ribs around each ring continue into the face.
        for angle in (45,135,225,315):
            rad=math.radians(angle)
            x=cx+8.17*math.cos(rad);y=cy+8.17*math.sin(rad)
            cube(prefix+'white diagonal molded rib '+str(angle),(x-.08,y-.46,-.14),
                 (x+.08,y+.46,.05),'white',rotation=('z',45 if angle in (135,315) else -45,(x,y,0)),
                 group='Molded facade ribs')

        # The upper LCD is a separate wide display framed by DX printed trim.
        bezel=[(cx-7.95,35.32),(cx+7.95,35.32),(cx+8.15,35.78),
               (cx+7.95,41.42),(cx-7.95,41.42),(cx-8.15,40.98)]
        polygon(prefix+'colorful upper display surround',bezel,-.11,.49,'coral',
                front=('details',[.125,8.125,7.875,11.875]),group='Upper display printed trim',step=.20)
        polygon(prefix+'upper display thick black rounded frame',[(cx-7.22,35.81),
                (cx+7.22,35.81),(cx+7.37,36.02),(cx+7.37,40.82),
                (cx+7.20,41.02),(cx-7.20,41.02),(cx-7.37,40.80),(cx-7.37,36.02)],
                -.43,-.075,'black',group='Upper display housings',step=.18)
        source=Image.open(art_dir/'upper-artwork-source.png')
        width=13.8;height=width*source.height/source.width
        center_y=38.4
        cube(prefix+'wide illuminated upper LCD',(cx-width/2,center_y-height/2,-.46),
             (cx+width/2,center_y+height/2,-.405),'black',
             north=('header',[0,0,16,16]),glow=('north',),group='Upper landscape LCDs')
        for x in (cx-7.74,cx+7.61):
            for y in (35.57,41.15):
                cube(prefix+'upper trim captive screw '+str((x,y)),(x,y,-.18),
                     (x+.11,y+.11,-.09),'silver',group='Upper display fixings')

    # A single deep black speaker rail ties both stations together, below the
    # uninterrupted coral diffuser. Two oval speakers sit above each display.
    cube('Shared black canopy speaker rail',(-2.7,41.62,-.22),(34.7,44.0,4.32),
         'black',group='Shared canopy structure')
    for i,cx in enumerate((2.5,10.25,21.75,29.5)):
        poly=[(cx-1.12,42.04),(cx+1.12,42.04),(cx+1.44,42.36),
              (cx+1.44,42.91),(cx+1.10,43.24),(cx-1.10,43.24),
              (cx-1.44,42.91),(cx-1.44,42.36)]
        polygon('Upper speaker '+str(i)+' silver rim',poly,-.29,-.17,'steel',
                group='Four upper speaker ovals',step=.14)
        poly=[(cx+(x-cx)*.89,42.64+(y-42.64)*.78) for x,y in poly]
        polygon('Upper speaker '+str(i)+' black perforated grille',poly,-.33,-.275,
                'black_mesh',group='Four upper speaker ovals',step=.14)

    visor_rotation=('x',-22.5,(16,43.84,-.04))
    visor=[(-3.10,43.94),(35.10,43.94),(35.15,46.18),(34.72,46.72),
           (34.18,46.94),(-2.18,46.94),(-2.72,46.72),(-3.15,46.18)]
    polygon('Single wide rounded coral luminous canopy',visor,-.18,1.19,'coral',
            rotation=visor_rotation,glow=('north','up'),group='Wide coral DX canopy',step=.20)
    # Rear bridge supports the deep visor without filling the opening in front.
    cube('Canopy rear dark tie beam',(-2.85,43.48,3.8),(34.85,45.4,12.6),
         'black',group='Shared canopy structure')
    # The centered colorful die-cut DX mark covers the gap in the speaker rail.
    cube('maimai DX small center header logo',(13.05,41.77,-.39),(18.95,44.66,-.34),
         'white',north=('branding',[.125,.25,15.875,15.75]),faces_only=('north',),
         glow=('north',),group='Die-cut center logo')

    # Round hand emblems protrude from the two outer upper cheeks, as in DX.
    for side,x0,x1 in (('Left',-3.28,-2.86),('Right',34.86,35.28)):
        for layer,(radius,depth,material) in enumerate(((2.07,.00,'coral'),
                (1.89,.12,'yellow'),(1.69,.19,'cyan'),(1.50,.24,'white'))):
            if side=='Left':xa,xb=x0-depth-.14,x1
            else:xa,xb=x0,x1+depth+.14
            for row in range(math.ceil(radius*2/.18)):
                y0=39.85-radius+row*.18;y1=min(39.85+radius,y0+.18)
                ym=(y0+y1)/2-39.85
                half=math.sqrt(max(0,radius*radius-ym*ym))
                uv=None
                if layer==3:
                    uv=('details',[8.125+(radius-half)/(2*radius)*3.75,
                        8.125+(39.85+radius-y1)/(2*radius)*3.75,
                        8.125+(radius+half)/(2*radius)*3.75,
                        8.125+(39.85+radius-y0)/(2*radius)*3.75])
                cube(side+' circular hand badge '+str((layer,row)),(xa,y0,1.0-half),
                     (xb,y1,1.0+half),material,west=uv if side=='Left' else None,
                     east=uv if side=='Right' else None,group='Outer circular hand badges')
