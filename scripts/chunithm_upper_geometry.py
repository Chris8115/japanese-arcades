"""Reference-based Chunithm display, air-sensor wings, LED tower and marquee."""
import math
from PIL import Image


def build_upper(cube, polygon, art_dir):
    # The low landscape screen slopes upward toward the vertical LED tower.
    pivot=(8,16.8,2.9)
    slope=('x',45,pivot)
    width=14.4
    source=Image.open(art_dir/'display-artwork-source.png')
    height=width*source.height/source.width
    cube('Sloped monitor black enclosure',(.47,16.48,2.89),(15.53,17.10+height,3.54),
         'black',rotation=slope,group='Landscape display')
    cube('Sloped monitor silver inner frame',(.64,16.63,2.79),(15.36,16.98+height,2.94),
         'silver',rotation=slope,group='Landscape display')
    cube('Paradise Lost attract screen',(.8,16.8,2.70),(15.2,16.8+height,2.82),
         'rubber',north=('display',[0,0,16,16]),glow=('north',),rotation=slope,
         group='Landscape display')

    # A flat luminous touch strip, rather than a piano keyboard or raised buttons.
    cube('Touch slider black deck',(-.69,15.55,.06),(16.69,16.43,3.43),
         'black',group='Touch slider')
    cube('Touch slider pale front edge',(-.63,15.56,-.015),(16.63,15.81,.11),
         'silver',group='Touch slider')
    cube('Sixteen-zone touch slider glass',(.50,16.445,.51),(15.50,16.59,2.49),
         'pink',up=('lights',[12.25,.25,15.75,3.75]),
         glow=('up','north','east','west'),group='Touch slider')
    for i in range(1,16):
        x=.5+i*15/16
        cube('Touch slider fine zone divider %02d'%i,(x-.012,16.591,.60),(x+.012,16.606,2.4),
             'magenta',group='Touch slider')
    for x in (-.47,15.72):
        cube('Deck clear cyan return '+str(x),(x,16.14,.22),(x+.72,16.42,3.27),
             'cyan',glow=('up',),group='Touch slider')

    # Broad white rear housing with a genuinely recessed lighting matrix.
    cube('Deep upper black cabinet',(-.45,23.85,10.22),(16.45,42.36,15.53),
         'black',group='Upper cabinet')
    for side,x0,x1 in (('Left',-.73,-.43),('Right',16.43,16.73)):
        cube(side+' upper white rear skin',(x0,23.50,12.70),(x1,41.55,15.61),
             'white',group='Upper cabinet')
        for y in (24.8,39.9):
            cube(side+' upper side fixing '+str(y),(x0-.025,y,14.78),(x1+.025,y+.15,14.93),
                 'steel',group='Cabinet fasteners')
    cube('LED tower recessed frame',(1.18,25.19,9.48),(14.82,41.53,10.35),
         'steel',group='LED visualizer')
    cube('LED tower black inner frame',(1.48,25.45,9.32),(14.52,41.25,9.60),
         'rubber',group='LED visualizer')
    cube('Recessed cyan violet LED matrix',(1.92,25.79,9.235),(14.08,40.97,9.37),
         'black',north=('lights',[.25,.25,11.75,15.75]),glow=('north',),group='LED visualizer')
    for x in (1.36,14.47):
        cube('LED tower brushed side return '+str(x),(x,25.45,9.27),(x+.18,41.21,9.50),
             'silver',group='LED visualizer')
    cube('Visualizer lower identifying strip',(2.07,25.23,9.13),(13.93,25.64,9.30),
         'black',north=('details',[8.25,7.25,15.75,7.85]),group='LED visualizer')

    # Two capsule speakers flank the authentic central Aime card target.
    cube('Rose patterned speaker and reader band',(.1,23.16,8.87),(15.9,25.70,9.63),
         'black',north=('details',[.25,.25,15.75,3.75]),group='Speaker band')
    for side,x0,x1 in (('Left',1.00,5.45),('Right',10.55,15.0)):
        points=[(x0+.50,23.60),(x1-.5,23.60),(x1,24.02),(x1,24.68),
                (x1-.5,25.10),(x0+.5,25.10),(x0,24.68),(x0,24.02)]
        polygon(side+' recessed capsule speaker',points,8.78,8.91,'black_mesh',
                group='Speaker band',step=.25)
    cube('Aime central reader black surround',(7.25,23.49,8.76),(8.75,25.25,8.91),
         'rubber',group='Speaker band')
    cube('Aime illuminated card target',(7.41,23.66,8.68),(8.59,25.08,8.79),
         'white',north=('details',[8.5,4.25,11.5,6.75]),glow=('north',),group='Speaker band')

    # Sculpted side wings are deep Y/Z panels, not a flat printed front border.
    # The acrylic projects furthest toward the player at its middle elbow. Its
    # lower edge follows the same -22.5 degree line as the white service fascia,
    # then the upper edge returns toward the canopy at 45 degrees.
    lower_y,lower_z=16.6,.1-(16.6-15.8)*math.tan(math.radians(22.5))
    elbow_y=29.2
    elbow_z=lower_z-(elbow_y-lower_y)*math.tan(math.radians(22.5))
    top_y=42.3
    top_z=elbow_z+top_y-elbow_y
    profile=[(lower_z,lower_y),(elbow_z,elbow_y),(top_z,top_y),
             (13.50,42.0),(13.9,39.6),(12.7,26.0),(9.2,22.2),(lower_z+.65,lower_y)]

    def side_panel(name,x0,x1,material,printed=False):
        def mapped(part,a,b,mat,**kwargs):
            # Only the perimeter is opaque. The real wings are acrylic with
            # sparse technical printing, open to the room behind the cabinet.
            cube(part+' rear frame',(x0,a[1],b[0]-.26),(x1,b[1],b[0]),
                 mat,group='Air sensor wings')
            options={'group':'Clear sensor wings','faces_only':('east','west')}
            if printed:
                # The print is laid out in physical Y/Z coordinates, preserving
                # continuity as each scanline narrows toward the pointed ends.
                v0=4.25+(42.3-b[1])/(42.3-16.6)*11.5
                v1=4.25+(42.3-a[1])/(42.3-16.6)*11.5
                u0=.25+(a[0]+5.6)/19.6*7.5
                u1=.25+(b[0]+5.6)/19.6*7.5
                face=('details',[u0,v0,u1,v1])
                # Export swaps east/west in the global X mirror. These preserve
                # one continuous increasing-Z print across changing row widths.
                options['east']=face
                options['west']=('details',[u1,v0,u0,v1])
            center=(x0+x1)/2
            cube(part+' clear printed acrylic',(center-.025,a[1],a[0]),
                 (center+.025,b[1],b[0]),mat,**options)
        # Reuse the scanline polygon builder in Z/Y space with an X extrusion.
        miny,maxy=min(y for z,y in profile),max(y for z,y in profile)
        step=.25
        count=math.ceil((maxy-miny)/step)
        for row in range(count):
            low=miny+(maxy-miny)*row/count
            high=miny+(maxy-miny)*(row+1)/count
            y=(low+high)/2
            cross=[]
            for a,b in zip(profile,profile[1:]+profile[:1]):
                if min(a[1],b[1])<=y<max(a[1],b[1]):
                    cross.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
            if len(cross)<2:continue
            mapped(name+' course %02d'%row,(min(cross),low,0),(max(cross),high,0),material)

    for side,x0,x1 in (('Left',-1.26,-.63),('Right',16.63,17.26)):
        side_panel(side+' deep dark sensor wing',x0,x1,'black',printed=True)
        for label,y,z,finish,angle in (
                ('lower sloping',lower_y,lower_z,elbow_y,-22.5),
                ('upper returning',elbow_y,elbow_z,top_y,45)):
            length=(finish-y)/math.cos(math.radians(angle))
            cube(side+' '+label+' acrylic leading frame',
                 (x0,y,z-.15),(x1,y+length,z+.15),'black',
                 rotation=('x',angle,((x0+x1)/2,y,z)),group='Air sensor wings')
        # Bright inward-facing lower air sensors beside the screen.
        sensor_x=-.25 if side=='Left' else 15.63
        sensor_z=.1-(17.05-15.8)*math.tan(math.radians(22.5))
        cube(side+' white air-sensor mast',(sensor_x,17.05,sensor_z),(sensor_x+.62,24.17,sensor_z+.86),
             'white',rotation=('x',-22.5,(sensor_x,17.05,sensor_z)),group='Air sensors')
        cube(side+' cyan sensing strip',(sensor_x+.11,17.49,sensor_z-.11),(sensor_x+.51,23.79,sensor_z+.06),
             'cyan',north=('lights',[12.25,4.25,13.75,15.75]),glow=('north',),
             rotation=('x',-22.5,(sensor_x,17.05,sensor_z)),group='Air sensors')
        for y in (17.9,21.9):
            z=.1-(y-15.8)*math.tan(math.radians(22.5))+.18
            a,b=(x0+.10,sensor_x+.62) if side=='Left' else (sensor_x,x1-.10)
            cube(side+' air sensor mounting bridge '+str(y),(a,y,z),(b,y+.16,z+.32),
                 'steel',group='Air sensor mounts')

    # Wide, deep canopy above the glass-sided sensor space.
    canopy=[(-1.70,41.81),(-1.30,43.24),(.18,43.67),(15.82,43.67),
            (17.30,43.24),(17.70,41.81)]
    polygon('Upper black canopy',canopy,4.77,14.33,'black',group='Canopy',step=.5)
    cube('Canopy cyan underside strip',(.14,41.73,5.15),(15.86,41.82,6.56),
         'cyan',glow=('down','north'),group='Canopy lighting')
    for x in (-1.31,15.66):
        cube('Canopy pale corner accent '+str(x),(x,41.63,5.25),(x+1.65,42.33,6.32),
             'silver',group='Canopy')
        cube('Canopy cyan corner light '+str(x),(x+.18,41.86,5.16),(x+1.47,42.17,5.31),
             'cyan',glow=('north',),group='Canopy lighting')

    # Alpha silhouette is extruded as short native cuboid runs. The source pixels
    # remain unchanged, and mipmapped cutout rendering handles the printed edge.
    image=Image.open(art_dir/'marquee-artwork-source.png').convert('RGBA')
    alpha=image.getchannel('A')
    # Fit the visible die-cut sign, excluding the image generator's safe margins.
    # UVs still select original pixels; the source image is never cropped/scaled.
    bounds=alpha.point(lambda value:255 if value>=128 else 0).getbbox()
    ax,ay,bx,by=bounds
    left,width=-1.4,18.8
    height=width*(by-ay)/(bx-ax)
    bottom=47.4-height
    rows=max(1,math.ceil(height/.25))
    columns=max(1,math.ceil(width/.25))
    active={};rectangles=[]
    for row in range(rows):
        following={};col=0
        while col<columns:
            py=min(by-1,int(ay+(1-(row+.5)/rows)*(by-ay)))
            px=min(bx-1,int(ax+(col+.5)/columns*(bx-ax)))
            if alpha.getpixel((px,py))<128:
                col+=1;continue
            start=col
            while col<columns:
                px=min(bx-1,int(ax+(col+.5)/columns*(bx-ax)))
                if alpha.getpixel((px,py))<128:break
                col+=1
            key=(start,col)
            if key in active:
                rectangle=active.pop(key);rectangle[3]=row+1
            else:rectangle=[start,col,row,row+1]
            following[key]=rectangle
        rectangles.extend(active.values());active=following
    rectangles.extend(active.values())
    for i,(a,b,c,d) in enumerate(rectangles):
        coords=[(ax+a/columns*(bx-ax))/image.width*16,
                (ay+(1-d/rows)*(by-ay))/image.height*16,
                (ax+b/columns*(bx-ax))/image.width*16,
                (ay+(1-c/rows)*(by-ay))/image.height*16]
        cube('Colorful CHUNITHM marquee cutout %03d'%i,
             (left+a/columns*width,bottom+c/rows*height,4.40),
             (left+b/columns*width,bottom+d/rows*height,4.68),'white',
             north=('branding',coords),glow=('north',),group='Colorful marquee')

    # Back service panels and cooling remain readable in a freestanding arcade.
    cube('Upper rear service-panel gasket',(.50,25.20,15.58),(15.50,40.51,15.69),
         'rubber',group='Rear upper service panel')
    cube('Upper rear access panel',(.75,25.43,15.70),(15.25,40.28,15.81),
         'charcoal',group='Rear upper service panel')
    for y in (27.0,36.8):
        cube('Upper rear ventilation grille '+str(y),(5.07,y,15.83),(10.93,y+2.03,15.91),
             'vent',group='Rear upper service panel')
    for x in (1.15,14.65):
        for y in (25.9,39.7):
            cube('Upper rear screw '+str((x,y)),(x,y,15.83),(x+.14,y+.14,15.94),
                 'steel',group='Cabinet fasteners')
