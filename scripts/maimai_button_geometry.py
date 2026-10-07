"""Exact curved button-layer outlines instead of horizontal cuboid scanlines."""


def curved_button(name,outline,z0,z1,material,palette_uv,glow=False):
    """Retain the canonical arc's twelve sections and all closed layer faces.

    The upper generator supplies outer points followed by reversed inner
    points. Adjacent front quads share radial boundaries and the small ends
    remain closed. The shape's relief and material layers are unchanged.
    """
    half=len(outline)//2
    assert len(outline)%2==0 and half>=2,(name,len(outline))
    outer=outline[:half];inner=list(reversed(outline[half:]));result=[]
    u,v,U,V=palette_uv(material)
    uv=[(u,v),(u,V),(U,V),(U,v)]

    def face(suffix,points,lit=False):
        result.append({'name':name+suffix,'group':'Sixteen separate ring buttons',
                       'texture':'#materials','glow':lit,
                       'vertices':[[32-x,y,z] for x,y,z in reversed(points)],
                       'uv':list(reversed(uv))})

    for i in range(half-1):
        o,O=outer[i:i+2];a,A=inner[i:i+2]
        face(' smooth front %02d'%i,[(*o,z0),(*a,z0),(*A,z0),(*O,z0)],bool(glow is True or glow and 'north' in glow))
        face(' smooth back %02d'%i,[(*o,z1),(*O,z1),(*A,z1),(*a,z1)])
        face(' outer wall %02d'%i,[(*o,z0),(*O,z0),(*O,z1),(*o,z1)])
        face(' inner wall %02d'%i,[(*A,z0),(*a,z0),(*a,z1),(*A,z1)])
    face(' starting end',[(*inner[0],z0),(*outer[0],z0),(*outer[0],z1),(*inner[0],z1)])
    face(' ending end',[(*outer[-1],z0),(*inner[-1],z0),(*inner[-1],z1),(*outer[-1],z1)])
    return result
