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

The tests cover real gaps, opaque/alpha safety, rotation, exact UV/emission
preservation, 7,056 external visibility rays, OBJ winding/area/UV continuity,
material boundaries, unsupported input, and repeat-run stability. Catalog
`--check` verifies idempotence and validates local model/texture references.
The complete export before/after report lives in ignored
`build/verification/model-optimization/source-optimization.json`.

Native before/after checks use an isolated 1280×960 client with matching camera,
world and settings. The baseline and candidate catalog probe audits all 22 item
models and 1,076 block states and captures front/oblique placed views plus native
inventory contact sheets. Live-display timing uses six-second samples after
warmup; reported durations are renderer wall time, not thread CPU time. Original
pack files and saved worlds are not used as test destinations.

The native catalog runs both passed: 22 item models, 1,076 block states, and no
missing sprites. Native item rendering falls from 149,888 to 133,709 baked quads;
every item's sprite-reference set is preserved. The candidate cache held nine
models / 295,672 vertices before
reload and zero afterward, then rendered both displays successfully again.
Clean oblique comparisons preserve silhouettes and artwork; both figure views
are pixel-identical. Animated Jubeat pads are compared separately. Some front
captures contain fixture teardown particles and are excluded from image
equivalence claims; the clean oblique views and item contact sheets provide the
comparison evidence.

| Nine detailed cabinets displayed | Before mean | After mean |
| --- | ---: | ---: |
| Gachapon renderer | 15.94 ms | 4.70 ms |
| Claw renderer | 6.55 ms | 5.49 ms |

These isolated renderer measurements are not a promised FPS increase in a full
modpack. Repeated post-reload samples were 5.08 ms (gachapon) and 4.81 ms (claw).
The candidate JAR used for these checks has SHA256
`171346408fb81ff9e454dd4324daabc4487ed45efd3945a1a1b895bf8f15492a`.

A separate copied Sodium 0.8.13 + Iris 1.8.14-beta.1 client with
ComplementaryReimagined r5.9.3 passed the catalog audit, targeted visual checks,
and shared-cache reload checks. Both stocked display machines rendered correctly
after reload. All test clients exited cleanly. This checks the relevant renderer
combination; the complete original modpack was not rerun for this asset pass.
Consolidated native evidence is in ignored
`build/verification/model-optimization/native-catalog-comparison.json`.
