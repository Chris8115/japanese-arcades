"""Geometry/UV invariants for the optional post-export OBJ optimizer."""

import unittest

from obj_mesh_optimizer import optimize_obj


def obj(polygons, *, uv=None, normals=False, boundary=None):
    lines = ["# authored fixture", "mtllib funpackcustom:models/block/example.mtl", "o cabinet", "g fascia", "s off", "usemtl face"]
    index = 1
    for number, polygon in enumerate(polygons):
        if boundary and number:
            lines.append(boundary)
        for p in polygon:
            lines.append("v " + " ".join(map(str, p)))
        for p in polygon:
            values = uv(number, p) if uv else p[:2]
            lines.append("vt " + " ".join(map(str, values)))
        if normals:
            lines.extend("vn 0 0 1" for _ in polygon)
        lines.append("f " + " ".join(f"{i}/{i}" + (f"/{i}" if normals else "") for i in range(index, index + len(polygon))))
        index += len(polygon)
    return "\n".join(lines) + "\n"


LEFT = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
RIGHT = [(1, 0, 0), (2, 0, 0), (2, 1, 0), (1, 1, 0)]


class ObjMeshOptimizerTests(unittest.TestCase):
    def test_adjacent_textured_rectangles_keep_outer_corners_and_affine_uv(self):
        output, stats = optimize_obj(obj([LEFT, RIGHT]))
        self.assertEqual((stats["input_faces"], stats["output_faces"]), (2, 1))
        self.assertEqual(stats["deduplicated_positions"], 2)
        self.assertEqual(stats["deduplicated_uvs"], 2)
        vertices, uvs = [], []
        for line in output.splitlines():
            if line.startswith("v "):
                vertices.append(tuple(map(float, line.split()[1:])))
            elif line.startswith("vt "):
                uvs.append(tuple(map(float, line.split()[1:])))
            elif line.startswith("f "):
                pairs = [tuple(map(int, word.split("/"))) for word in line.split()[1:]]
                points = {vertices[v - 1] for v, _ in pairs}
                self.assertEqual(points, {(0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0)})
                for v, t in pairs:
                    self.assertEqual(vertices[v - 1][:2], uvs[t - 1])
        for directive in ("mtllib funpackcustom:models/block/example.mtl", "o cabinet", "g fascia", "s off", "usemtl face"):
            self.assertIn(directive, output)

    def test_triangles_merge_without_changing_the_diagonal_interpolation(self):
        output, stats = optimize_obj(obj([LEFT[:3], [LEFT[0], LEFT[2], LEFT[3]]]))
        self.assertEqual(stats["output_faces"], 1)
        self.assertEqual(len(next(line for line in output.splitlines() if line.startswith("f ")).split()), 5)

    def test_uv_seam_is_not_merged(self):
        _, stats = optimize_obj(obj([LEFT, RIGHT], uv=lambda n, p: (p[0] - n, p[1])))
        self.assertEqual(stats["output_faces"], 2)

    def test_non_affine_quad_is_not_merged(self):
        _, stats = optimize_obj(obj([LEFT, RIGHT], uv=lambda n, p: (p[0], p[1] + (.1 if p == LEFT[2] else 0))))
        self.assertEqual(stats["output_faces"], 2)

    def test_curved_outline_and_nonplanar_quad_are_preserved(self):
        folded = [(1, 0, 0), (2, 0, .1), (2, 1, .1), (1, 1, 0)]
        _, stats = optimize_obj(obj([LEFT, folded]))
        self.assertEqual(stats["output_faces"], 2)
        nonplanar = [(1, 0, 0), (2, 0, 0), (2, 1, .1), (1, 1, 0)]
        _, stats = optimize_obj(obj([LEFT, nonplanar]))
        self.assertEqual(stats["output_faces"], 2)

    def test_concave_union_and_opposite_winding_are_preserved(self):
        triangle = [(1, 0, 0), (2, -.5, 0), (1, 1, 0)]
        _, stats = optimize_obj(obj([LEFT, triangle]))
        self.assertEqual(stats["output_faces"], 2)
        _, stats = optimize_obj(obj([LEFT, list(reversed(RIGHT))]))
        self.assertEqual(stats["output_faces"], 2)

    def test_explicit_normals_remain_explicit_and_prevent_merging(self):
        output, stats = optimize_obj(obj([LEFT, RIGHT], normals=True))
        self.assertEqual(stats["output_faces"], 2)
        self.assertEqual(stats["deduplicated_normals"], 7)
        self.assertEqual(output.count("vn 0 0 1\n"), 1)
        for line in output.splitlines():
            if line.startswith("f "):
                self.assertTrue(all(word.endswith("/1") for word in line.split()[1:]))

    def test_material_object_group_and_smoothing_boundaries_are_retained(self):
        for directive in ("usemtl other", "o other", "g other", "s 1"):
            with self.subTest(directive=directive):
                output, stats = optimize_obj(obj([LEFT, RIGHT], boundary=directive))
                self.assertEqual(stats["output_faces"], 2)
                self.assertIn(directive, output)

    def test_negative_references_resolve_before_global_index_deduplication(self):
        source = "v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nf -3/-3 -2/-2 -1/-1\n"
        output, stats = optimize_obj(source)
        self.assertEqual(stats["output_faces"], 1)
        self.assertIn("f 1/1 2/2 3/3", output)

    def test_unknown_syntax_is_skipped_byte_for_byte(self):
        source = obj([LEFT]) + "curv 0 1 1 2 3\n"
        output, stats = optimize_obj(source)
        self.assertEqual(output, source)
        self.assertIn("unsupported OBJ directive", stats["skipped"])

    def test_long_strip_and_repeat_run_are_stable(self):
        polygons = [[(x, 0, 0), (x + 1, 0, 0), (x + 1, 1, 0), (x, 1, 0)] for x in range(40)]
        output, stats = optimize_obj(obj(polygons))
        self.assertEqual(stats["output_faces"], 1)
        repeated, repeated_stats = optimize_obj(output)
        self.assertEqual(repeated, output)
        self.assertEqual(repeated_stats["merged_faces"], 0)


if __name__ == "__main__":
    unittest.main()
