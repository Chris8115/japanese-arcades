"""Small cuboid/mesh authoring helpers for reference-based collectible figures."""
from initial_d_geometry import Geometry


class FigureGeometry(Geometry):
    """A per-figure 8 by 8 palette, with the existing native mesh primitives."""
    def face(self, name, points, material='white', texture='materials', uv=None, glow=False):
        if uv is None:
            index = self.colors.index(material)
            assert index < 64, 'Figure palettes support at most 64 colors'
            u, v = (index % 8) * 2, (index // 8) * 2
            uv = [(u+.5,v+.5),(u+.5,v+1.5),(u+1.5,v+1.5),(u+1.5,v+.5)][:len(points)]
        self.faces.append({'name':name,'group':self.group,'vertices':[list(p) for p in points],
                           'texture':'#'+texture,'uv':uv,'glow':glow})
