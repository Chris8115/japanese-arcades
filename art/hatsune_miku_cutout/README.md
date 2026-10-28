# Hatsune Miku cardboard cutout

A freestanding, Minecraft-style Hatsune Miku standee with teal twin-tails, a friendly wave, and a printed silhouette. The thin plate has kraft-cardboard edges and backing, a folded rear support, and a low cardboard foot. It is a separate arcade prize from the Miku figure.

The arcade kiosk price defaults to **1,500 Prize Points**, configurable as `prizes.hatsune_miku_cutout` in the server config `japanesearcades-arcade-economy.toml`.

## Source and regeneration

- Immutable print: [miku-cutout-print.png](miku-cutout-print.png)
- Exact generation and transparency-refinement prompts: [artwork-prompt.md](artwork-prompt.md)
- Generator: [make_hatsune_miku_cutout.py](../../scripts/make_hatsune_miku_cutout.py)
- Editable model: [hatsune_miku_cutout.bbmodel](hatsune_miku_cutout.bbmodel)
- Exported geometry: [hatsune_miku_cutout.geometry.json](hatsune_miku_cutout.geometry.json)
- Dimensions and face audit: [model-audit.json](model-audit.json)

From the repository root, with Python and Pillow installed:

```powershell
py scripts/make_hatsune_miku_cutout.py
```

The generator copies the print PNG byte-for-byte into the runtime texture. Alpha values of at least 128 define the physical silhouette; a 48 × 78 sampling grid supplies merged cardboard back rectangles and perimeter edges. The printed front retains the original full-resolution image. `--grid-width` can change the silhouette resolution, subject to the complete placed model's 1,000-face limit.

## Size, placement, and rendering

The standee measures **15.2 model units wide × 25.64449438 tall**, or **0.95 × 1.6027809 blocks**. Its plate is 0.64 model units thick, or 0.04 blocks. The base spans `x=3.6..12.4`, `z=4.8..11.2`; all placement angles remain inside one block column. Artwork proportions are preserved without stretching.

Placement uses lower and upper block sections and **16 yaw angles**, spaced 22.5° apart. The standing-sign rotation contract is `0=SOUTH`, `4=WEST`, `8=NORTH`, `12=EAST`. At rotation 0, the printed front faces south, along positive Z. The section boundary is at 16 model units; the upper section extends another 9.64449438 units.

The complete placed object contains **279 faces**: 192 lower and 87 upper, including the cardboard support. The standalone inventory model contains **255 faces**. All geometry uses static baked NeoForge OBJ models and cutout textures; there is **no block entity, custom block-entity renderer, or ticking**. The inventory model includes its own complete mesh and front-facing display transform.
