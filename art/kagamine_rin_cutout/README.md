# Kagamine Rin cardboard cutout

A Minecraft-style Rin standee with blonde bob, oversized white bow and yellow-trimmed outfit, matching the Miku and Teto set.
It has the same friendly wave, thin kraft-cardboard silhouette, folded rear
support, low foot and overall height.

Available in the kiosk's **Cutouts** category for **1,500 Prize Points** by
default, configurable as `prizes.kagamine_rin_cutout` in
`japanesearcades-arcade-economy.toml`. It is also in the creative tab.

## Source and regeneration

- Immutable print: [rin-cutout-print.png](rin-cutout-print.png)
- Built-in image-generation prompt and references: [artwork-prompt.md](artwork-prompt.md)
- Generator: [make_kagamine_rin_cutout.py](../../scripts/make_kagamine_rin_cutout.py)
- Shared exporter: [make_hatsune_miku_cutout.py](../../scripts/make_hatsune_miku_cutout.py)
- Editable Blockbench model: [kagamine_rin_cutout.bbmodel](kagamine_rin_cutout.bbmodel)
- Preview geometry: [kagamine_rin_cutout.geometry.json](kagamine_rin_cutout.geometry.json)
- Export audit: [model-audit.json](model-audit.json)

With Python and Pillow available, from the repository root:

```powershell
py scripts/make_kagamine_rin_cutout.py
```

The wrapper writes only this character's outputs and copies the source PNG
byte-for-byte into the runtime texture. Alpha at least 128 defines the
cardboard silhouette, with merged back rectangles and coarse perimeter edges.
The front print retains the full image resolution and original proportions.

## Placement and performance

Overall size is **12.96551026 × 25.64449438 model units**, approximately
**0.8103 blocks wide × 1.6028 blocks tall**. The printed plate is
0.04 blocks thick. It uses two block sections with **16 placement angles**,
spaced 22.5 degrees apart, and fits inside one block column at every angle.
Rotation follows signs: `0=SOUTH, 4=WEST, 8=NORTH, 12=EAST`.

The complete placed object has **314 faces** (192 lower + 122 upper);
the inventory model has **288 faces**. Counts include the backing and
support. These are static baked NeoForge OBJ models: no block entity,
custom block-entity renderer or ticking. Outlines contain at most nine boxes.

## Verification

`dev.cmd Build` succeeded and **all 219 required GameTests passed**.
Existing cutout tests now exercise all four characters, including every
placement angle, persistence, support loss, either-half removal and all mixed
character pairs. Reward tests redeem all 116 catalog entries and cover search.

An isolated native client passed **900 checks** on the final release JAR.
All 128 block states and four inventory models passed texture, UV, bounds,
outline and face-count audits before and after resource reload. Both new rewards
were purchased through the real kiosk: 5,000 points became 3,500 then 2,000,
with one of each cutout delivered, credits unchanged and the pass returned.
The reward browser also passed its 320×240 layout check.

All 144 new packaged resources match source bytes. Existing Miku/Teto assets and
the shared placement/exporter code are unchanged. See the shared
[verification receipt](native-verification.json) for the release hash.

- [Rin and Len together](verification/01-rin-and-len-front.png)
- [All four characters](verification/02-four-character-lineup.png)
- [Angled view](verification/03-rin-and-len-angle.png)
- [Cardboard backs and supports](verification/04-cardboard-backs-and-feet.png)
- [All 16 rotations of each](verification/05-sixteen-rotations-each.png)
- [Inventory models](verification/07-cutout-inventory-models.png)
- [Rin reward](verification/08-rin-cutout-reward.png)
- [Len reward](verification/09-len-cutout-reward.png)
- [Minimum reward browser](verification/10-minimum-cutout-rewards.png)
