# Nostalgia Op.3 cabinet

Arcade cabinet with jukebox playback for the Japanese Arcades creative tab. It has a one-block footprint
and occupies three vertical blocks. The shape and detail are adapted from the supplied
photos and Minecraft concept; dimensions are artistic estimates rather than manufacturer measurements.

The fidelity pass retains a Minecraft cuboid silhouette while bringing the casing,
keyboard deck, speaker wings, and marquee closer to the supplied cabinet photos.
The wider triangle sits against a rising metal threshold inside the footwell; small
triangular motifs replace the former diamond border. The predominantly black shell
has recessed service doors, transport grips, vents, fasteners, and adjustable feet.
The keyboard has clipped corners, 28 ivory keys, shallow black accents, printed
instructions, and a small inset slot. Both displays have matching ornamental detail.
The central Nostalgia plaque selects a wide band of its artwork so the lettering
keeps its height rather than compressing a square illustration into the fascia.
The open book folds forward around its recessed spine, with a taller burgundy-cat
page and layered page edges. Twelve staggered keys and three saturated rosettes
cascade forward/down across the upper fascia. Geometry remains deliberately stepped.
Greedy rectangle merging reduces the complete model from 1,315 to 858 cuboids while
preserving the artwork silhouettes. Cabinet surfaces use ambient occlusion; lit
screen faces explicitly disable it to retain their brightness in dark corners.

The lower triangle is a **physical triangular plate leaning into an open recessed footwell**.
The sloped touchscreen has a solid black enclosure joining it to the rear cabinet,
so the side profile is filled behind the screen as in the real cabinet photos.
The marquee follows the supplied Minecraft concept with an open music book and taller
burgundy-cat page, layered piano keys, separate blue/lavender/pink floral cutouts,
and smaller flower ornaments down the right monitor edge. The book has thick gold
covers, ivory page stacks, printed front pages, and raised spine bands. The flowers
have colored back layers and raised inner petals and medallions; the keys have
staggered heights and depths, coral accents, and small light insets. The cutout
silhouettes are stepped geometry, with their original transparent artwork on the fronts.
The keys and flowers project forward and cascade down over an ornate front fascia,
with the pink flower overlapping the upper monitor trim as in the concept.
The central speaker fascia and plaque lean back at 22.5 degrees. Both speaker wings
also face inward, with their outer edges projecting toward the player. Thin stepped
courses combine the vertical lean and inward angle using vanilla cuboid geometry.
The upper screen, rhythm display, keys, speakers, and book marquee are decorative.
The cabinet accepts music discs and uses Minecraft's native jukebox song playback;
there is no rhythm-game GUI or playable piano.
Screen faces stay fullbright and have light edges. The console and upper section emit
light levels 13 and 12. Bloom depends on your shader settings; vanilla Minecraft does
not add a bloom effect.

## Files

- `nostalgia-op3.bbmodel`: editable Blockbench project, with named part groups and embedded textures.
- `nostalgia-op3.blend`: Blender preview scene with packed textures; studio lights and floor are preview-only.
- `nostalgia-op3-front.png` / `nostalgia-op3-back.png` / `nostalgia-op3-side.png`: renders of the exported game geometry and UVs.
- `nostalgia-op3-marquee.png`: close-up of the layered top decoration.
- `nostalgia-op3-controls.png`: close-up of the angled speakers, lower display, and keyboard deck.
- `geometry.json`: complete cabinet cuboids used by the renderer.
- `artwork-source.png`: original, unchanged artwork generated with the built-in imagegen tool.
- `imagegen-prompt.txt`: the exact artwork generation prompt.
- `marquee-artwork-source.png`: original transparent marquee atlas made with the built-in imagegen tool.
- `marquee-imagegen-prompt.txt`: the exact reference-guided marquee artwork prompt.
- `marquee-artwork-v2.png`: current saturated blue/purple/pink rosettes and gold book pages, with preserved transparency.
- `marquee-imagegen-prompt-v2.txt`: exact built-in imagegen prompts and provenance for the current atlas.

The deterministic entry point is `scripts/make_nostalgia_model.py`. Cabinet,
console, and marquee geometry are separated into `nostalgia_cabinet_geometry.py`,
`nostalgia_console_geometry.py`, and `nostalgia_marquee_geometry.py` beside it.
`nostalgia_surface_art.py` draws the native pixel artwork for the rhythm display,
keyboard labels, side insert, and trim. The entry point writes the three
Minecraft section models, blockstate variants, inventory model, textures, and Blockbench project.
`scripts/render_nostalgia_model.py` reads those same cuboids and UVs and renders them with Blender.
Running the generator replaces generated model files, so preserve manual Blockbench edits separately
or apply the changes to the generator when keeping it as the canonical source.
Open `nostalgia-op3.bbmodel` in Blockbench to edit the complete grouped cabinet.
It is a Generic Model because the cabinet spans three blocks; the generator supplies
the separate bounded Java block models used by the mod. Embedded textures make the
project portable. The preview renderer uses the same geometry and UVs as the game,
with studio lighting; Minecraft lighting and shader settings can look different.

The builder needs Python with Pillow; the renderer runs inside Blender 5.0.
On this machine the bundled Python is available at
`python`.

```powershell
& 'python' scripts/make_nostalgia_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' -b --python scripts/render_nostalgia_model.py
.\dev.cmd Build
```

## Try it in Minecraft

Run `dev.cmd Client` or `dev.cmd PackClient`, open a creative test world, and select
**Nostalgia Op.3 Arcade Cabinet** from the **Japanese Arcades** creative tab.
Alternatively, use `/give @s funpackcustom:nostalgia_op3`.
Place on a solid floor with three clear vertical blocks. The front faces the player.
Breaking any section removes the other sections; the base supplies the survival item drop.

Right-click any section while holding a music disc to insert one and start playback.
Right-click again to eject the disc. Discs with a valid `JUKEBOX_PLAYABLE` song component
use the same playback system, including registered modded songs. Each cabinet stores
one disc in its base; the saved disc and song progress survive saving and loading.
Breaking the cabinet stops playback and returns the disc once, including creative removal.
The base also provides jukebox redstone/comparator output and a one-slot container.
Restart the development client after Java changes; F3+T reloads model/texture changes only.

## Verification

`dev.cmd Build` packages the mod. `dev.cmd GameTest` runs six native
[NeoForge Game Tests](https://docs.neoforged.net/docs/1.21.1/misc/gametest/) in `runs/gametest`:
insertion/ejection through all sections, playback ticks and non-disc rejection,
disc and playback progress persistence followed by removal, creative removal,
blocked placement, and placing/ejecting a cabinet with saved disc data.
All six passed on 2026-10-05. The structure template can be regenerated with
`scripts/make_gametest_template.py`.
The subsequent visual-only fidelity pass passes the build and an export audit:
all 858 cuboids have valid dimensions and vanilla rotation/bounds, all 12 facing/part
variants resolve, seven textures and their UVs agree with Blockbench, section-local
coordinates reconstruct the complete model, and regeneration is deterministic.

Minecraft resources are in `src/main/resources/assets/funpackcustom`, and the block's
placement and interaction implementation is `NostalgiaCabinetBlock.java`.
`NostalgiaJukeboxBlockEntity.java` stores the disc and delegates audio to Minecraft's
`JukeboxSongPlayer`, so playback uses the normal jukebox volume category and sound events.
The implementation uses [NeoForge's block registration](https://docs.neoforged.net/docs/1.21.1/blocks/)
and [JSON cuboid models](https://docs.neoforged.net/docs/1.21.1/resources/client/models/).
No additional mod dependencies are needed.

The artwork is original generated pixel art inspired by the provided references, with the
machine title retained for identification. Runtime texture packing copies the artwork pixels
unchanged into a power-of-two sheet; it does not resample or crop the source image.
