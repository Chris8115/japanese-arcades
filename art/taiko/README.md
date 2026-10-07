# Taiko no Tatsujin arcade cabinet

A classic lantern-style Taiko cabinet based on the supplied references, with
two orange-brown barrel drums tilted upward and turned slightly outward,
cream heads and studded rims, wooden
cradles, a central CRT, ribbed festival lanterns, a broad Taiko 12 marquee,
orange floral panels wrapping the front and sides, and tethered drumsticks. The printed art is drawn from
shapes and type; the reference photos are not copied into the model textures.

## Obtaining and placing

Find **Taiko no Tatsujin Arcade Cabinet** in **Japanese Arcades**, use
`/give @s japanesearcades:taiko`, or order it from the Arcade Ordering Kiosk's
**Machines** tab for:

- 20 iron ingots
- 4 gold ingots
- 1 diamond
- 6 glass blocks
- 6 redstone dust

One item places the whole connected machine. It needs a solid, clear **2 x 2
block footprint** and is **3 blocks tall** at the rear cabinet. The front drum
sections occupy the lower two blocks. Placement supports all four directions
and consumes nothing if its occupied cells are obstructed or unsupported.

## Playing the drums

With an **empty hand or an ordinary stick**, left- or right-click either drum:

- **Cream drumhead:** Minecraft note-block bass drum, pitch 0.8.
- **Narrow outer rim:** Minecraft note-block hi-hat, pitch 1.2.

The server checks the actual tilted drum face under the player's aim, so heads
and rims stay aligned with the visible model in every orientation. Nearby
players hear the same sound. Both hands or mouse actions in the same two-tick
window produce one beat, preventing duplicate playback. Invalid tools, hidden
drums behind walls, spectators, and out-of-reach hits do not play notes.

Ordinary drum clicks do not mine the machine, including in creative mode.
**Sneak-left-click to remove it**, or use a mining tool. Drumsticks attached to
the model are decorative; a vanilla stick works for interaction. This cabinet
provides free-form percussion, without a scored rhythm minigame.

## Music discs and removal

Use the **rear cabinet** to insert and eject vanilla-compatible music discs,
as with the other arcade cabinets. Both rear columns share one jukebox and
save its disc and playback progress. Drum and pedestal interactions do not
eject the disc, so you can play percussion while music runs.

Removing any occupied section removes its matched machine. Survival removal
drops one cabinet plus its stored disc. Creative removal drops the stored
disc without duplicating the cabinet. Adjacent machines remain independent.

## Verification

All **73 dedicated-server GameTests** passed on 2026-10-06. Six Taiko tests
cover every occupied cell and orientation, neighboring machines, obstruction
and support loss, shared saved-disc playback, unobstructed disc ejection,
actual head/rim sound events, both mouse actions and hands, cooldowns, and
rejection of blocked, distant, or invalid-tool interactions. The kiosk catalog
test also pays the complete Taiko price and verifies one delivered cabinet.

The final small Minecraft client passed actual left/right mouse interactions
with empty hands and sticks after the outward drum rotation. It received exactly
two bass-drum and two rim sounds from four hits; creative drumming preserved
the cabinet. The real kiosk UI deducted the advertised materials and delivered
one Taiko. The development status command also confirmed the release mod was loaded.

Screenshots: [placed machine](taiko-in-game.png),
[decorated side and drum angle](taiko-side-in-game.png),
[ordering screen](taiko-ordering.png), and [completed order](taiko-order-receipt.png).

The same interaction and ordering checks passed in the full copied pack with
all **218 copied mod JARs**, JEI, and its shader renderer. The final probe
exited cleanly. The disposable fixture retained the pack's 10 GB heap, limited
active processors to eight, and disabled Distant Horizons background terrain
generation after memory exhaustion during earlier startup attempts. All
changes stayed in the ignored test copy; the original instance was untouched.
Pack screenshots show the [rendered drums and cabinet](taiko-in-pack.png),
[side artwork](taiko-side-in-pack.png), and
[successful order alongside JEI](taiko-ordering-in-pack.png).

The release package audit matched all 35 relevant resource files to source,
verified Java 21 class versions, and preserved every existing translation.

![Taiko cabinet in Minecraft](taiko-in-game.png)

## Geometry and editable sources

- `taiko.bbmodel`: editable Blockbench mesh project with embedded original art.
- `taiko.blend`: editable Blender scene grouped into the cabinet, lanterns,
  drums, cradles, podium, and tethered sticks, with packed textures and cameras.
- `geometry.json`: all source faces, UV coordinates, materials, bounds, and
  the exact drum hit geometry used to match the runtime.
- `taiko.png`, `taiko-front.png`, and `taiko-drums.png`: studio renders of the
  actual exported geometry, without replacing the machine with a generated image.

In model units (16 units per block), the assembled model spans X **0.3–31.7**,
Y **0.05–48**, and Z **−15.865–14.93**. The north-facing front is negative Z.
The two drumhead centers are **(8,24,−9)** and **(24,24,−9)**. Both tilt
upward by **35°**, and each complete drum and cradle turns outward by **8°**.
The primary normal is **(−cos 35° sin 8°, sin 35°, −cos 35° cos 8°)**;
the secondary normal has the opposite X component. Their horizontal in-plane
axes are **(cos 8°,0,−sin 8°)** and **(cos 8°,0,sin 8°)**, respectively.
The unprinted cream head has radius **6.1**;
the studded outer rim has radius **6.8**. The barrel bodies have 64 sides and
bulge gently between the front head and smaller rear membrane. Each lantern
has a curved body, 19 raised ribs, red end caps, and a curved transparent crest.
Its cream paper and ribs share fullbright lighting, retaining the rib relief
without dark striping in dim worlds. Both exposed podium sides have dedicated
festival artwork aligned with the front panel.
The decorative wooden saddles use triangulated concave profiles.

The runtime clips positions and UVs together at X=16, Y=16/32, and Z=0, then
translates each fragment into one of its ten occupied cells. All 40 blockstate
orientations and the complete item model use NeoForge's native OBJ loader.
There is no per-frame block-entity rendering cost for the static cabinet.

The initial native NeoForge 21.1.252 bake audit passed **99,078 baked quads**
across those 40 rotated block models and the item. It checked every source
face survived, coordinates stayed finite, UVs and texture V orientation stayed
correct, and the screen, marquee, and lantern faces retained fullbright light.
That result predates the geometry reduction described below. The isolated bake
audit is separate from the live-client resource and texture-atlas checks.

### Geometry reduction, 2026-10-07

The assembled world model now contains **14,750 faces**, reduced from **20,130**
(**26.73%**). The complete item and authoring model contains **13,174 faces**,
reduced from **18,382** (**28.33%**). The savings come from excessive radial
subdivisions on small details, not from simplifying the playable drum surfaces:

- Lantern bodies and all 19 raised ribs use 32 radial segments instead of 48.
  Their vertical profile, rib depth, curved crest, and fullbright materials remain.
- All 40 black tacks and eight silver latches per drum remain in place. Their
  tiny circular outlines use fewer segments, and buried rear caps are omitted.
- Wooden cradle scrolls, the eight petals on each flower boss, and small rounded
  cabinet corners retain their shapes with fewer subdivisions. Buried petal backs
  are omitted.
- All **2,176 source faces** defining the 64-sided barrel bodies, membranes,
  head skirts, front rims, and playable drumheads are exactly unchanged, including
  their vertices, UVs, materials, and lighting flags. Drum hit geometry and overall
  bounds also match the backup exactly. All eight texture PNG hashes are unchanged.

[optimization-audit.json](optimization-audit.json) records the before/after counts,
per-export results, unchanged texture hashes, and protected-geometry checks.
Every Taiko OBJ also passes the conservative optimizer's idempotence check.

To regenerate the model, run `scripts/make_taiko_model.py` with Python and
Pillow. It calls `scripts/taiko_textures.py` for the original signs and cabinet
art, and uses the existing `ddr_mesh_export` clipping helpers. Add
`--reuse-textures` to update geometry while preserving the existing PNGs. Each
Taiko OBJ is conservatively optimized within this generator, without rewriting
other machines. To regenerate
the previews and packed Blender project, run Blender in background mode with
`--python scripts/render_taiko_model.py`. Add `-- --single-only` to render
only the main three-quarter preview. `--samples 16` provides a faster preview;
`--resolution-percent 75` also reduces its dimensions. Other cabinet assets are
not modified.

## Optimization client verification � 2026-10-07

The integrated build and asset audit passed. All 18 texture PNGs across maimai,
Taiko and Chrono Circle retain their original hashes; 68 relevant packaged assets
match the current source files. The catalog optimizer reports zero pending changes.

The disposable Minecraft client verified all **240 native block states** and
the complete item model for this cabinet, with finite vertices/UVs and no missing
textures. Placement and resource reload passed. Six fixed camera views were
compared before and after with Sodium 0.8.13, Iris 1.8.14-beta.1 and Complementary
Reimagined r5.9.3. No custom per-frame cabinet renderer was added.

See the [optimized cabinet](taiko-optimized-quarter.png) and
[control detail](taiko-optimized-controls.png). Reports are in the ignored
`build/verification/top-three-audit.json` and
`runs/top-three-after-visual-probe/native-report.json`. These are geometry and
appearance checks, not an FPS benchmark. Gameplay Java did not change.

Original files are preserved at Git tag
`backup/top-three-before-optimization-20261007-104418` and in a verified external
ZIP archive of all 121 original files. Rollback should revert only this optimization.
