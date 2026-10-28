# GITADORA classic white cabinets

Two static models based on the single-monitor **OverDrive** white cabinets:

- [KONAMI GuitarFreaks product page](https://www.konami.com/arcadegames/products/am_gitadora_gf/)
- [KONAMI DrumMania product page](https://www.konami.com/arcadegames/products/am_gitadora_dm/)

The corresponding official product photographs are retained in `references/`:

- `official-guitarfreaks-overdrive.jpg`: `https://img.konami.com/products_master_kam/jp_publish/am_gitadora_gf/jp/ja/images/pkg.jpg`
- `official-drummania-overdrive.jpg`: `https://img.konami.com/products_master_kam/jp_publish/am_gitadora_dm/jp/ja/images/pkg.jpg`

Geometry reproduces the white/silver shell, single display, twin stacked speaker pods, front woofer, payment console, and instrument layout. GuitarFreaks has a concave double-cutaway white controller, five raised fret buttons, a pick lever, headstock and cable. DrumMania has all seven colored pad/cymbal inputs, rack brackets, two pedals and two stored sticks. A stool is omitted because it is absent from the reference photograph.

Printed panels and static title cards are original procedural interpretations of the OverDrive livery. No low-resolution photograph is stretched over the model. Speaker perforations, rubber grain, rear vents, pedal ribs, keypad legends and service details use textures rather than individual mesh elements. These are decorative cabinets using the mod's existing interaction; the screens do not implement rhythm-game playback.

## Final mesh and texture audit

| Cabinet | Complete placed faces | Full item faces | Placement |
|---|---:|---:|---|
| GuitarFreaks | 2,054 | 1,950 | Three vertical cells, `part=base/console/marquee` |
| DrumMania | 3,199 | 2,767 | Two by two footprint, ten occupied cells, `section=0..9` |

The complete placed counts include every instrument, cable, cymbal, mounting bracket, rail, pedal and platform, plus any extra faces introduced at cell boundaries. Counts are not FPS measurements. All 15 final OBJ files were independently parsed for valid indices, finite UVs/positions, triangle/quad topology, planar faces, nonzero area and DrumMania cell bounds; see `runtime_audit.json`.

There are 14 unique textures shared by both cabinets. The largest dimension is **512 pixels**. Total base RGBA storage is **3,211,264 bytes (3.0625 MiB)** before mipmaps and atlas packing. Every texture dimension is divisible by 16, preserving four mip levels. Identical materials and printed panels are shared; only the screen subtitle differs between games. See `texture_audit.json` for dimensions and file sizes. Texture allocations inside Minecraft's combined atlas are measured separately by native verification.

GuitarFreaks bounds in model pixels: X -1.9..17.9, Y 0..46.8, Z .555..15.5. DrumMania: X .65..31.35, Y 0..46.8, Z -15.3..15.5. Sixteen pixels equal one block; north/front is -Z. DrumMania's rear-left base is the anchor. The right column is +X; the forward row is -Z. Sections 0/1 are rear bases; 2/3 forward platform; 4/5 rear console; 6/7 rear marquee; 8/9 forward controls. Geometry is clipped into each occupied cell for local lighting and rendering.

## Editable assets and regeneration

- `guitarfreaks/gitadora_guitarfreaks.bbmodel` and `drummania/gitadora_drummania.bbmodel`: grouped editable meshes with embedded textures.
- The corresponding `.blend` files, generated locally by the render script, contain the actual exported runtime item meshes, packed textures, and a separate studio preview scene.
- Hero/front renders and DrumMania controls render come from the shipped OBJ geometry. No alternate high-detail render model is used.

Run `python scripts/make_gitadora_models.py` with Pillow available to regenerate textures, runtime OBJ/MTL/JSON, blockstates and Blockbench sources. `scripts/gitadora_geometry.py` contains the geometry; `scripts/gitadora_textures.py` contains the printed panels. Run Blender with `--background --python scripts/render_gitadora_models.py` for packed Blender files and studio images. The generator's static full-item model is intended to be paired with the separately captured one-face GUI icon through the existing client wrapper.
