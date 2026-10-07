# Kasane Teto cardboard cutout

A matching Minecraft-style Teto standee with red twin-drill hair, a friendly wave, and a printed silhouette. It uses the same thin kraft-cardboard construction, folded rear support, and low foot as the Miku cutout. The artwork retains its original proportions, and the two standees have the same overall height.

The arcade kiosk price defaults to **1,500 Prize Points**, configurable as `prizes.kasane_teto_cutout` in the server config `funpackcustom-arcade-economy.toml`.

## Source and regeneration

- Immutable print: [teto-cutout-print.png](teto-cutout-print.png)
- Exact artwork-generation prompt: [artwork-prompt.md](artwork-prompt.md)
- Generator: [make_kasane_teto_cutout.py](../../scripts/make_kasane_teto_cutout.py)
- Shared geometry exporter: [make_hatsune_miku_cutout.py](../../scripts/make_hatsune_miku_cutout.py)
- Editable model: [kasane_teto_cutout.bbmodel](kasane_teto_cutout.bbmodel)
- Preview geometry: [kasane_teto_cutout.geometry.json](kasane_teto_cutout.geometry.json)
- Dimensions and face audit: [model-audit.json](model-audit.json)

From the repository root, with Python and Pillow installed:

```powershell
py scripts/make_kasane_teto_cutout.py
```

The Teto wrapper reuses the existing geometry exporter and writes only Teto outputs. It copies the source PNG byte-for-byte into the runtime texture. Alpha values of at least 128 define the physical silhouette; merged back rectangles and perimeter edges come from a coarse sampling grid. The printed front retains the full-resolution image. The generator enforces a complete placed model budget below 1,000 faces. Miku's generated assets remain unchanged.

## Size, placement, and rendering

The cutout measures **12.94458291 model units wide × 25.64449438 tall**, or approximately **0.8090 × 1.6028 blocks**. The plate is 0.64 model units thick, or 0.04 blocks. Its horizontal bounds are `x=1.52770855..14.47229145`; the shared base spans `x=3.6..12.4`, `z=4.8..11.2`.

Placement uses lower and upper block sections and **16 yaw angles**, spaced 22.5° apart. The standing-sign rotation contract is `0=SOUTH`, `4=WEST`, `8=NORTH`, `12=EAST`; at rotation 0, the printed front faces positive Z. All angles fit inside one block column. The upper section extends 9.64449438 model units above the lower block.

The complete placed object contains **378 faces**: 191 lower and 187 upper, including the cardboard support. The inventory model contains **357 faces**. These are static baked NeoForge OBJ models with cutout textures, with no block entity, custom block-entity renderer, or ticking. The inventory model includes the complete standee and a centered front-facing display transform.

## Verification

`dev.cmd Build` succeeded and all **170 required GameTests passed**. The shared
cutout tests exercise both characters at all 16 placement angles, yaw rounding,
blocked placement, support loss, either-half removal, creative removal,
rotation/mirroring and saved block states. Mixed-character tests also check
neighbor isolation and rejection of mismatched upper/lower halves. The kiosk
transaction tests cover Teto's point price, delivery and stale-request handling.

A disposable Minecraft 1.21.1 / NeoForge 21.1.252 client verified all 32 Teto
states, native face counts, textures, item rendering and resource reload.
The original Miku states retain their native face counts and valid textures.
Front, angled, cardboard-back, kiosk and side-by-side screenshots were visually
checked. All 72 packaged Teto resources match the source files byte-for-byte.
The original pack and saves were untouched. See
[native-verification.json](native-verification.json) for the release hash.

- [Front view](01-teto-front.png)
- [Angled view](02-teto-angle.png)
- [Cardboard back](03-cardboard-back.png)
- [All 16 angles](04-sixteen-angles.png)
- [After resource reload](05-reloaded-teto.png)
- [Kiosk reward](06-cutout-reward.png)
- [Teto and Miku together](07-miku-and-teto.png)
