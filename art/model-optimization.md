# Arcade model optimization — 2026-10-06

The catalog was audited against release `dc5b705` (JAR SHA256
`9a0a7cd8d70e51bb4d97b0701435f007bc7fb360f70e454debdc9a21c9ae2c77`).
Editable Blockbench files, figure construction, cabinet proportions, artwork and
all 107 runtime PNG textures are preserved. Only exported geometry and display
rendering were optimized.

## Exported geometry

| Inventory model | Faces before | Faces after |
| --- | ---: | ---: |
| maimai | 35,953 | 23,826 |
| Sound Voltex Valkyrie | 9,372 | 6,980 |
| Nostalgia Op.3 | 5,148 | 4,353 |
| BeatStream | 1,764 | 1,452 |
| Claw machine | 738 | 607 |
| DDR SuperNOVA | 6,867 | 6,739 |
| MÚSECA | 10,162 | 9,983 |
| Chunithm | 4,154 | 4,113 |
| Project DIVA | 5,680 | 5,651 |
| WACCA | 7,052 | 7,031 |
| Groove Coaster | 5,993 | 5,977 |
| Jubeat (including glass) | 1,609 | 1,601 |

Other models retain their face counts. The pass also deduplicates repeated OBJ
position/UV declarations in the figures, Taiko, kiosk, gachapon and other mesh
assets; this reduces loading/file overhead without claiming a face-count saving.

Across the actual block and item exports, JSON faces fall from 130,570 to 122,771
and OBJ faces from 163,205 to 138,397: **32,607 fewer faces overall**. Total model
file content falls from 102,895,642 to 67,759,046 bytes (34%). These are source
asset totals, not a claim about compressed JAR size, VRAM, or per-frame work.

The JSON pass removes only entire covered faces, using closed, opaque boxes in
the same rotation pose as proof of occlusion. It does not subdivide partially
covered faces into more fragments. The OBJ pass joins only convex, coplanar
triangles/quads with continuous affine UVs in the same material/object/group
run. It preserves explicit normals, curved outlines, warped quads and UV seams.

Some dense meshes remain deliberately detailed. Chrono Circle's and other
cabinet palettes contain dither; merging by material name would alter that
detail. Taiko's round drums, ribs and lanterns likewise remain modeled. Texture
downsampling was not used. Jubeat's 24-frame pad sheet occupies a 512×512 atlas
slot; its 512×12288 source dimensions are not its per-frame GPU texture footprint.

## Live prize displays

Gachapon now uses the same guarded rendering path as the claw. Both share one
800,000-vertex LRU cache (approximately 40 MiB), rather than allocating a separate
cache per type. Model bake completion releases all cached geometry, sprites and
unsupported-model entries. The existing Sodium native path, Iris shadow handling,
animated sprite activation and native fallback remain in use. Gachapon price
text follows the geometry batch to avoid flushing the item buffer mid-display.

## Reproduction and validation

After running any model generator:

```text
python scripts/optimize_models.py --write
python scripts/optimize_models.py --check --report build/verification/model-audit.json
python scripts/test_catalog_json_geometry.py
python scripts/test_obj_mesh_optimizer.py
.\dev.cmd Build
```
