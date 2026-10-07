"""Two rigid triangular speaker prisms with exact compound-angle planar faces.

The main cabinet remains native cuboids. These12 mesh polygons replace144
independently rotated strips, so both outer rims are genuinely straight edges.
Coordinates returned here are already in the final north-facing cabinet frame.
"""
import math


def build_speakers(material_uv):
    faces=[]
    s,c=math.sin(math.radians(22.5)),math.cos(math.radians(22.5))
    material_tile=material_uv('black')
    material_pixel=[(material_tile[0]+material_tile[2])/2,(material_tile[1]+material_tile[3])/2]
    for side,x0,x1,hinge,angle,flip in (('Left',.75,4.4,4.2,-22.5,False),('Right',11.6,15.25,11.8,22.5,True)):
        sy,cy=math.sin(math.radians(angle)),math.cos(math.radians(angle))
        triangle=[(x0,26),(x1,27.9),(x0,29.8)] if not flip else [(x1,26),(x0,27.9),(x1,29.8)]

        def transform(p):
            x,y,z=p
            dx,dz=x-hinge,z-6.45
            # Inward yaw first, then the cabinet's22.5-degree backward pitch.
            xx=hinge+dx*cy+dz*sy
            zz=6.45-dx*sy+dz*cy
            yy=26+(y-26)*c-(zz-6.45)*s
            zz=6.45+(y-26)*s+(zz-6.45)*c
            return [16-xx,yy,zz]

        center=transform([sum(x for x,y in triangle)/3,27.9,6.45+.60])

        def face(label,vertices,texture='#materials',uv=None,glow=False):
            points=[transform(v) for v in vertices]
            coords=uv if uv else [material_pixel[:] for _ in points]
            a,b,d=points[:3]
            u=[b[i]-a[i] for i in range(3)];v=[d[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            outside=[sum(p[i] for p in points)/len(points)-center[i] for i in range(3)]
            if sum(n[i]*outside[i] for i in range(3))<0:
                points.reverse();coords=list(reversed(coords))
            faces.append({'name':side+' rigid triangular speaker '+label,'vertices':points,'uv':coords,'texture':texture,'glow':glow,'group':'Rigid triangular speaker wings'})

        front=[(x,y,6.45) for x,y in triangle]
        back=[(x,y,7.65) for x,y in triangle]
        face('front substrate',front)
        face('rear housing',back)
        for i in range(3):
            j=(i+1)%3
            face('straight edge %d'%i,[front[i],back[i],back[j],front[j]])
        # The solid triangle itself supplies the silhouette. Art is mapped once
        # across one planar polygon, with no segmented UV or raised outer strip.
        front_art=[(x,y,6.45-.025) for x,y in triangle]
        art_uv=[[(x-x0)/(x1-x0)*16 if not flip else (x1-x)/(x1-x0)*16,(29.8-y)/3.8*16] for x,y in triangle]
        face('continuous cyan grille',front_art,'#speaker',art_uv,True)
    return faces


def build_separator(material_uv):
    """Two continuous flat plates join the screens at the inward triangle tips."""
    faces=[]
    seam_y=27.73492062465493
    seam_z=7.245
    # These are cabinet-world coordinates, independent of the mirrored author
    # convention. Both front faces share exactly the same full-width seam edge.
    panels=(
        ('Broad white lower display bridge','ivory',
         [[.8,26.35,5.30],[15.2,26.35,5.30],[15.2,seam_y,seam_z],[.8,seam_y,seam_z]],
         [0,-.16,.12]),
        ('Black upper display transition','black',
         [[.8,seam_y,seam_z],[15.2,seam_y,seam_z],[15.2,29.62,7.77],[.8,29.62,7.77]],
         [0,0,.12]),
    )
    for name,material,front,offset in panels:
        back=[[p[i]+offset[i] for i in range(3)] for p in front]
        center=[sum(p[i] for p in front+back)/8 for i in range(3)]
        tile=material_uv(material)
        pixel=[(tile[0]+tile[2])/2,(tile[1]+tile[3])/2]
        polygons=[('front',front),('back',back)]+[('edge %d'%i,[front[i],back[i],back[(i+1)%4],front[(i+1)%4]])for i in range(4)]
        for label,points in polygons:
            a,b,c=points[:3]
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            outside=[sum(p[i] for p in points)/len(points)-center[i] for i in range(3)]
            if sum(normal[i]*outside[i] for i in range(3))<0:points=list(reversed(points))
            faces.append({'name':name+' '+label,'vertices':points,'uv':[pixel[:] for _ in points],
                          'texture':'#materials','glow':False,'group':'White-black display separator'})
    return faces
