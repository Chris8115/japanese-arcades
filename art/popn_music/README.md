# pop'n music Sunny Park

Reference-based reconstruction of the familiar white widescreen pop'n music
cabinet. The orange double-circle speaker pods, tilted yellow display surround,
curved cyan-edged console, nine domed keys and printed white pedestal follow
Konami's Sunny Park cabinet photographs. The shaped edition topper is separate
from the narrow rainbow light strip and orange speaker fascia.

The rear keys are **yellow, blue, blue, yellow**; the staggered front keys are
**white, green, red, green, white**, viewed from the player's position.

Place one cabinet item on a supported floor with a clear space three blocks
high. It occupies one vertical block column; leave clearance beside
the console and in front of its curved lip. The cabinet faces the player and
can be rotated in all four horizontal directions. Breaking any section returns
one cabinet in survival. The arcade kiosk offers it through the Machines tab.

Use a Minecraft music disc on any section to start or eject it. The cabinet
saves the disc and playback progress and supports the existing Arcade Pass
economy. Controls and displays are decorative; this addition does not implement
the pop'n music rhythm game.

```text
/give @s japanesearcades:popn_music
```

The geometry uses three static native OBJ sections with cached selection shapes,
no per-frame cabinet renderer, and a separate inventory model. Speaker holes,
printed decorations and small panel markings use texture detail. Final exported
counts are **5,070 placed faces** across all three sections and **4,928 inventory
faces**, both below the approximately 10,000-face budget. The overall visual
envelope is about **1.34 blocks wide × 1.15 blocks deep × 2.99 blocks tall**.
Detailed counts and export validation are in [model-audit.json](model-audit.json)
and [geometry.json](geometry.json).

## Editable sources and previews

- [Blockbench model](popn_music.bbmodel)
- `popn_music.blend` (generated locally)
- [Three-quarter view](popn_music.png)
- [Front](popn_music-front.png), [side](popn_music-side.png), and [controls](popn_music-controls.png)
- [Minecraft with Complementary shaders](shader-three-quarter.png)
- [Preserved generated artwork](sunny-park-artwork-source.png)
- [Artwork prompt and provenance](imagegen-prompt.txt)

Regenerate with Python/Pillow, then render with Blender:

```powershell
python scripts/make_popn_music_model.py
blender --background --python scripts/render_popn_music_model.py
```

Geometry, textures and export settings are maintained in
`scripts/popn_music_geometry.py`, `scripts/popn_music_textures.py`, and
`scripts/make_popn_music_model.py`. The generator is authoritative; transfer
manual modeling changes back into it before regenerating.

## References

- [Konami Sunny Park product page](https://www.konami.com/arcadegames/products/am_popn_sunnypark/)
- [Official cabinet render](https://www.konami.com/products_master_kam/jp_publish/am_popn_sunnypark/jp/ja/images/pkg.jpg)
- [Konami TUNE STREET cabinet](https://www.konami.com/products_master_kam/jp_publish/am_popn_19/jp/ja/images/pop19.jpg), showing the same white widescreen chassis.
- [HD cabinets photographed by DJ Damien](https://commons.wikimedia.org/wiki/File:Pop%27n_music_HD_machines.jpg), CC BY-SA 2.0; used to check console shape, button order and side graphics. The photo is not embedded in the shipped model.

Dimensions are inferred from photographs, rather than a manufacturer CAD file.
The Sunny Park display/marquee illustration was newly generated with the built-in
image tool using the cabinet render as a visual reference. Its original pixels
are saved separately; runtime copies are sized for game texture atlases. Utility
prints and decals are drawn by the texture generator. This is a fan-made model.
