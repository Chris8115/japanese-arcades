# Mob Collection prize figures

The collection contains **all 82 vanilla Minecraft 1.21.1 mob types**, with one
boxed figure, loose figure and reusable empty box per mob: **246 placeable forms**.
This adds 76 figures to the original Creeper, Zombie, Skeleton, Enderman, Slime
and Axolotl. Their IDs, numbers 01–06, models, colors and packaging layout stay
compatible. New numbers 07–82 follow entity registry order.

The roster includes animals, aquatic mobs, villagers, Nether and End mobs,
bosses, and the command-only Giant, Illusioner and Zombie Horse. It represents
each mob type once, rather than every coat, color, age or profession variant.
The tropical fish uses an orange/white Kob palette, and the pufferfish is inflated.

## Collect and display

- Redeem any boxed figure in the Arcade Kiosk's **Prizes** tab for **1,000 Prize
  Points** by default. Each price is configurable under `prizes.boxed_<mob>_figure`
  in `japanesearcades-arcade-economy.toml`.
- Operators can stock boxed figures in existing claw and gachapon inventories.
  All three forms also appear in the Japanese Arcades creative tab.
- Place any form facing you. Right-click a placed full box with an empty hand
  to take out its figure; the empty box stays on display.
- Use the matching loose figure on its empty box to repack it.
- Sneak-right-click in the air while holding a boxed figure to open one in your
  inventory, receiving the figure and its empty box.
- Survival breaking drops exactly the current form. Opening and repacking
  convert one source, including in creative; mismatched figures cannot be packed.

Full-inventory delivery and cancellation retain the existing atomic exchange
behavior. All decorations save ordinary block states. The separate Custom
Display Box continues to accept arbitrary items independently of this collection.

## Model design and performance

The original box dimensions remain 10/16 × 14/16 × 8/16 blocks. Loose figures
fit the original 8/16-square footprint and 11.5/16 height limit. The navy plinth,
colored rim, printed nameplate, cardboard tray and windowed package are retained.
Packaging now reads “COLLECT ALL 82”; its collection numbers and accent colors
are defined in `scripts/mob_figure_catalog.py`.

New miniatures use captured vanilla geometry and textures, uniformly scaled
to fit. The dragon's long wings and tail make it shorter on its plinth than
upright mobs. Original cuboid models remain unchanged. Every model is static
and baked; there are no live mob renderers, block entities or ticking animations.

The largest complete model is **boxed Ender Dragon: 805 faces**; its loose
figure has 767. Empty boxes have 38 faces. Placed and inventory geometry have
the same counts, all far below the roughly 10,000-face budget. Exact per-form
counts and bounds are in [model-audit.json](model-audit.json).

Vanilla eye and clothing overlays are baked into matching base textures to
avoid coplanar flicker. Fish UVs that repeat beyond a texture boundary are
baked into tiled sprites, preventing atlas bleed. Captured vertex colors and
explicit normals preserve tint and lighting. Translucent/animated mob effects
become static cutout surfaces appropriate for display miniatures.

## Rebuild and inspect

Run `python scripts/make_mob_figures.py` with Pillow installed. The original
six skin PNGs and all 76 captured source meshes are retained, so regeneration
does not require a Minecraft client or a live renderer. `--minecraft-jar <path>`
can refresh the original six source skins from a local 1.21.1 client JAR.

All 246 forms have editable Blockbench sources and exported geometry JSONs
here. Blockbench embeds baked equivalents of captured vertex tints. The
runtime OBJ/JSON and geometry exports remain the canonical assets. Source
captures and exact vanilla texture hashes are documented in
[vanilla_meshes/README.md](vanilla_meshes/README.md).

Run `python scripts/render_mob_figure_expansion.py` to render the actual
exported meshes in Blender and generate [four collection sheets](expansion/previews/collection-01.jpg),
82 individual thumbnails and six boxed/loose/empty detail compositions.
