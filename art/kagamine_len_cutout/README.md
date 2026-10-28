# Kagamine Len cardboard cutout

A Minecraft-style Len standee with stepped blonde hair, upward tuft, short ponytail and yellow tie, matching the Miku and Teto set.
It has the same friendly wave, thin kraft-cardboard silhouette, folded rear
support, low foot and overall height.

Available in the kiosk's **Cutouts** category for **1,500 Prize Points** by
default, configurable as `prizes.kagamine_len_cutout` in
`japanesearcades-arcade-economy.toml`. It is also in the creative tab.

## Source and regeneration

- Immutable print: [len-cutout-print.png](len-cutout-print.png)
- Built-in image-generation prompt and references: [artwork-prompt.md](artwork-prompt.md)
- Generator: [make_kagamine_len_cutout.py](../../scripts/make_kagamine_len_cutout.py)
- Shared exporter: [make_hatsune_miku_cutout.py](../../scripts/make_hatsune_miku_cutout.py)
- Editable Blockbench model: [kagamine_len_cutout.bbmodel](kagamine_len_cutout.bbmodel)
- Preview geometry: [kagamine_len_cutout.geometry.json](kagamine_len_cutout.geometry.json)
- Export audit: [model-audit.json](model-audit.json)

With Python and Pillow available, from the repository root:

```powershell
py scripts/make_kagamine_len_cutout.py
```

The wrapper writes only this character's outputs and copies the source PNG
byte-for-byte into the runtime texture. Alpha at least 128 defines the
cardboard silhouette, with merged back rectangles and coarse perimeter edges.
The front print retains the full image resolution and original proportions.

## Placement and performance

Overall size is **12.85366486 × 25.64449438 model units**, approximately
**0.8034 blocks wide × 1.6028 blocks tall**. The printed plate is
0.04 blocks thick. It uses two block sections with **16 placement angles**,
spaced 22.5 degrees apart, and fits inside one block column at every angle.
Rotation follows signs: `0=SOUTH, 4=WEST, 8=NORTH, 12=EAST`.

The complete placed object has **349 faces** (191 lower + 158 upper);
the inventory model has **323 faces**. Counts include the backing and
support. These are static baked NeoForge OBJ models: no block entity,
custom block-entity renderer or ticking. Outlines contain at most nine boxes.
