# Custom Display Box

The Custom Display Box is a separate collectible package for displaying your own items. It uses the same compact packaging style as the mob collection, with a clear cutout window, pale cardboard interior, navy print, an item-name label, and accents colored from the displayed item. The six preset mob boxes are unchanged.

## Use

- Find it in the creative tab, or craft **four boxes** with eight paper surrounding one glass pane.
- Place an empty box and right-click it with an item to insert **one item**. Inserting consumes one item even in creative mode.
- Right-click a filled box with an empty hand to toggle its contents between angled and straight-on views.
- Sneak-right-click with empty hands to retrieve its contents. The empty box remains placed and retains its label, color, and orientation preference.
- Sneak-use a filled box held in your hand to open one package and receive its contents and an empty box.
- Breaking a box in survival preserves its stored data in the dropped package. In creative mode, a filled box also drops its stored package to preserve the item; an empty box drops nothing.

The orientation preference stays with the box through saving, breaking/replacing, unpacking, and refilling. Existing boxes start in the original angled view. The shell, name label, and packaging color stay fixed when toggling.

Stored items retain their complete names and components. The printed label shortens names longer than 48 characters to fit the package; this does not rename the stored item. The matching bitmap font covers printable ASCII and Latin-1, with Minecraft's default font supplying other Unicode characters.

## Rendering and performance

The static shell contains **43 faces across 13 elements**, plus the contained item's model and printed label. Five cutout accent faces use tint index `0`; the navy print and cardboard remain untinted. The front window uses transparent cutout pixels and small opaque highlights, without a full translucent layer.

The placed box uses a block-entity renderer, and its inventory item uses a custom item renderer. Neither requires ticking. Item color and model fitting share a cache limited to 256 entries for both orientations together, cleared on resource reload. Items with custom renderers use their particle texture as the color fallback. Complete rendering cost depends on the contained item's own model.

The shell occupies model coordinates `x=3..13`, `y=0..14`, `z=4..12` and faces north. The live label is centered at `(8, 0.955, 3.985)` within `x=3.85..12.15`, `y=0.43..1.48`. Detailed UV, tint, label-transform, and interior-fit specifications are in [design.json](design.json).

## Rebuild the art

From the repository root, with Python and Pillow installed:

```powershell
py scripts/make_custom_display_box.py
```

The generator writes only the custom box's texture, block and item models, blockstates, loot table, bitmap font, and editable preview files. It imports shared drawing helpers from `make_mob_figures.py` without regenerating the preset mob assets. It uses Arial Bold on Windows, with a DejaVu fallback where available; use the same font environment for byte-identical texture output.

`custom_display_box.bbmodel` is the editable Blockbench model. `custom_display_box.geometry.json` contains the exported preview faces, including tint indices. The item model uses `minecraft:builtin/entity`, so a preview or renderer must draw the shell block model explicitly and honor both texture alpha and tint index `0`.
