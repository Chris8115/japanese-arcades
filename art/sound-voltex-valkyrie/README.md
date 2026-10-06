# Sound Voltex Valkyrie cabinet

Sound Voltex Valkyrie is the second cabinet in the **Japanese Arcades** creative tab.
Its shape follows the supplied Exceed Gear cabinet photos, adapted to Minecraft's
stepped cuboid geometry. Dimensions are visual estimates, not manufacturer measurements.

The black chassis carries a tall portrait screen, cyan/purple acrylic wings, four
ring-lit speakers, a layered angular marquee, and a broad control deck. Two knobs,
four BT keys, two FX keys, a start button, and the small central display are modeled
separately. The recessed footwell has a suspended luminous V, central subwoofer,
silver threshold, and open space beneath the light assembly. Side graphics, rear
service panels, vents, handles, feet, and fasteners complete the casing.
The lower blue bars, central insert, and subwoofer lean gently backward by about
10 degrees. Their lower ends sit near the middle of the footwell; the upper ends
recede roughly 2.36 model units (0.15 blocks) toward the rear. Fine cuboid courses
approximate that shallow ramp within vanilla's model rotation constraints.

The cabinet is slightly wider than one block: about **1.1 blocks at the base**, **1.2
at the deck**, and **1.375 across the upper wings**. It occupies one placement column
of three vertical blocks, with a model height just under three blocks. Leave room on
both sides for the overhanging deck and wings; placing cabinets two blocks apart
gives them clear separation. Rotated selection/collision shapes follow these broader
section bounds.

The screens, controls, light panels, and speakers are decorative. Music discs use
Minecraft's native jukebox playback; the cabinet does not run a rhythm-game GUI.
Screen and light faces remain fullbright. The base emits light level 10 and the two
upper sections emit level 13. Bloom depends on shaders; vanilla lighting does not
add a bloom effect.

## Try it in Minecraft

Launch `dev.cmd Client` or `dev.cmd PackClient`, then choose **Sound Voltex Valkyrie
Arcade Cabinet** in the **Japanese Arcades** creative tab. The command is:

```text
/give @s funpackcustom:sound_voltex_valkyrie
```

Place it on a solid floor with three clear vertical blocks and side clearance. The
front faces the player. Breaking any section removes the cabinet; survival drops
one cabinet item from the base.

Right-click any section while holding a music disc to insert it and start playback.
Right-click again to eject it. Each cabinet stores one disc and saves its playback
progress. Valid registered modded jukebox songs use the same path. Removal stops
playback and returns the disc once, including creative removal. The base also supplies
jukebox redstone/comparator output and a one-slot container. Nearby cabinets retain
their own independent discs and playback.

Restart the development client after Java changes. F3+T reloads model and texture
changes only.

## Editable files and previews

- `sound-voltex-valkyrie.bbmodel`: grouped Blockbench Generic Model with embedded textures.
- `sound-voltex-valkyrie.blend`: Blender preview scene with packed textures.
- `sound-voltex-valkyrie-front.png`, `sound-voltex-valkyrie-back.png`, and `sound-voltex-valkyrie-side.png`: full cabinet renders.
- `sound-voltex-valkyrie-controls.png`: control deck and lower speaker close-up.
- `sound-voltex-valkyrie-footwell.png`: close-up of the recessed, sloping lower light assembly.
- `sound-voltex-valkyrie-marquee.png`: upper speaker, wing, and marquee close-up.
- `geometry.json`: complete cabinet geometry and UV data used by the renderer.
- `display-artwork-source.png` and `marquee-artwork-source.png`: original artwork generated with the built-in imagegen tool.
- `imagegen-prompts.txt`: exact artwork prompts and provenance.

The source artwork is generated pixel art inspired by the supplied references,
including the machine title for identification. Runtime packing copies its pixels
unchanged into power-of-two textures. Technical patterns and material details are
drawn by the generator. The current complete model contains **1,562 cuboids**:
620 in the base, 446 in the console, and 496 in the upper section.

Open the `.bbmodel` file in Blockbench to edit the complete cabinet. It uses Generic
Model format because the complete cabinet spans three blocks. The deterministic
generator creates the three bounded Java block models, their facing variants, the
inventory model, textures, geometry export, and Blockbench project:

- `scripts/make_valkyrie_model.py`: main generator, surface artwork, upper cabinet, and exports.
- `scripts/valkyrie_lower_geometry.py`: base, footwell, control deck, and lower speakers.
- `scripts/render_valkyrie_model.py`: renders the exported cuboids and UVs in Blender.

Regeneration replaces generated files. Save manual Blockbench edits separately or
transfer them into the generator before rebuilding. The preview renderer uses the
game geometry and textures with studio lighting; its floor and lights are not part
of the Minecraft model, and in-game lighting/shaders can look different.

The builder requires Python with Pillow. The renderer runs inside Blender 5.0.
On this machine, from the repository root:

```powershell
& 'python' scripts/make_valkyrie_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' -b --python scripts/render_valkyrie_model.py
.\dev.cmd Build
```

## Runtime verification

`dev.cmd GameTest` runs ten native integration tests in a disposable world: six for
Nostalgia and four for Valkyrie. The Valkyrie tests exercise all-section insertion
and ejection, non-disc rejection, ticking and saved playback, survival removal with
exactly one disc and cabinet drop, creative removal beside a playing Nostalgia, and
placement/ejection with saved disc data. All ten passed on 2026-10-05. These server
tests do not verify the rendered appearance or full-pack client compatibility.

The final build and small development-client resource load also passed on
2026-10-05, with no missing cabinet models or textures. The export audit checks
all 12 facing/part variants, local section reconstruction, vanilla model bounds
and rotations, and matching Blockbench geometry/UVs and six embedded textures.
The six studio views were inspected for silhouette, lettering, and control
clearance. Full-pack gameplay compatibility has not been re-tested for Valkyrie.

The block/item ID is `funpackcustom:sound_voltex_valkyrie`. Resources are under
`src/main/resources/assets/funpackcustom`. `SoundVoltexCabinetBlock.java` supplies
the wider bounds and inherits placement and interactions from `NostalgiaCabinetBlock.java`.
Both cabinets use `NostalgiaJukeboxBlockEntity.java` and Minecraft's native
`JukeboxSongPlayer`. The original Nostalgia registry and saved-data IDs are retained.
No additional mod dependencies are required.
