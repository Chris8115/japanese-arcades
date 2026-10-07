# Fun pack mod development

This workspace is for our own mods for **Minecraft 1.21.1 / NeoForge 21.1.252**.
The starter mod is **Fun Pack Custom**, id `funpackcustom`, version `0.1.0`.
It registers `/funpackdev`, a small command to confirm that the mod is loaded.
The **Japanese Arcades** creative tab includes eighteen cabinets with music-disc playback:

- [Nostalgia Op.3 Arcade Cabinet](art/nostalgia-op3/README.md)
- [BeatStream Arcade Cabinet](art/beatstream/README.md)
- [Sound Voltex Valkyrie Arcade Cabinet](art/sound-voltex-valkyrie/README.md)
- [Sound Voltex NEMSYS Arcade Cabinet](art/sound-voltex-nemsys/README.md)
- [beatmania IIDX LIGHTNING MODEL](art/beatmania-iidx-lightning/README.md)
- [WACCA Reverse Arcade Cabinet](art/wacca/README.md)
- [Chunithm Paradise Lost Arcade Cabinet](art/chunithm/README.md)
- [Groove Coaster Arcade Cabinet](art/groove_coaster/README.md)
- [MÚSECA Arcade Cabinet](art/museca/README.md)
- [Project DIVA Arcade Future Tone Cabinet](art/project_diva/README.md)
- [Chrono Circle Arcade Cabinet](art/chrono_circle/README.md)
- [MUSIC DIVER Arcade Cabinet](art/music-diver/README.md)
- [maimai DX Twin Arcade Cabinet](art/maimai/README.md)
- [DDR SuperNOVA Arcade Cabinet](art/ddr_supernova/README.md)
- [Taiko no Tatsujin Arcade Cabinet](art/taiko/README.md)
- [Initial D Single Racing Cabinet](art/initial_d/README.md)
- [Jubeat Arcade Cabinet](art/jubeat/README.md)
- [ONGEKI bright Arcade Cabinet](art/ongeki/README.md)

Their model notes include editable files, previews, and use instructions. All are
three blocks high. maimai uses **two connected columns** and requires a supported,
clear **two-by-three-block** space. DDR SuperNOVA uses a **two-wide, three-deep**
supported footprint, including a real two-by-two dance stage and open handrails.
beatmania IIDX uses a **two-wide, two-deep** supported footprint, with two connected
rear cabinet columns and a low standing platform in front. Its two turntables
use subtle native texture animation around two banks of seven illuminated keys.
Taiko uses a **two-by-two supported footprint** with two playable drums angled
upward and slightly away from each other, plus festival artwork on the front
and side panels.
Left- or right-click the drumheads and rims with an empty hand or a stick for
different note-block percussion sounds. Sneak-left-click to remove it. Use the
rear cabinet for music discs; playing the drums leaves the disc running.
Initial D is a **one-wide, three-deep single-player cabinet** with a usable
seat. Its shell and controls stay within one block of width so neighboring
units can be placed flush in a row. Right-click its seat empty-handed to sit;
sneak to get out. Each cabinet has its own music-disc inventory.
The other cabinets occupy one vertical column.
BeatStream uses a copy of Nostalgia's chassis, with triangular illuminated speaker
grilles, a larger sloped touchscreen, a flat white control strip, and its own cutout topper.
Jubeat keeps its entire shell, speakers and cube topper inside one block of
width and depth, so independent cabinets can be placed directly side by side.
Its glass display cubes contain recessed artwork, and its sixteen buttons run
a multicolor idle animation. The small display above the buttons shares their slope.
ONGEKI bright has a separate white outer arch, circular side panels, a recessed
portrait monitor, two groups of three buttons, and a center lever. It uses the
standard kiosk ordering, Arcade Pass rewards, and saved music-disc playback.
Sound Voltex NEMSYS adds the original cabinet shape with four angular light wings,
square side speakers, four BT keys, two FX keys, and a pair of rotary knobs.
MUSIC DIVER adds a white wedge cabinet with an inclined circular play surface,
four raised strike pads, a smaller status display and a round circuit-lit marquee.
Allow additional clearance for the visible decks, wings, mats, and enclosures.
Each model's notes describe its dimensions.

[Stackable Gachapon Machines](art/gachapon/README.md) are also available in the
Japanese Arcades tab. Each independent unit fits one block, with owner/password
operator access, nine prize slots, a currency price and a separate payment box.
Hold right-click to crank and receive one capsule containing the entire selected
reward amount. Walking away pauses the crank and resets it after five seconds
without payment. The price and prize item icons update on the machine itself.

The [Claw Machine](art/claw_machine/README.md) occupies a supported **three-wide,
two-deep, three-tall** space. Right-click for transparent bottom controls; use
WASD/arrows to aim and Space to drop. Shift-right-click empty-handed for operator
access, a physical currency price, the spatial 3×3 prize grid and payout settings.
Each slot offers its whole stack. The moving claw can slip a prize into an empty
position or carry it to the chute. Operators can set a fixed win chance or ramp
it to a guaranteed Nth attempt; a win resets the ramp. Only a stocked Drop costs
currency, and paid attempts finish after the player leaves.

[Arcade Ordering Kiosk](art/arcade_kiosk/README.md) provides a survival route to the
machines. Craft the two-block-tall kiosk with iron, glass, gold and redstone, then
select a machine to see its material costs. The **Order** button exchanges those
materials for the selected machine, putting it into the player's inventory or
dropping it nearby if full. The **Machines** and **Prizes** tabs can be extended as
new content is added. The **Passes** tab issues Arcade Passes, loads Credits from
iron, gold, emeralds or diamonds, and combines balances between cards placed in
real **From** and **To** slots. Both cards return when the kiosk closes. Use a pass
on a music arcade cabinet to spend Credits and earn randomized Prize Points,
then redeem them in **Prizes** for placeable Miku and Teto figures, a
[WACCA wall poster](art/wacca_poster/README.md), a
[Minecraft-style Hatsune Miku cardboard cutout](art/hatsune_miku_cutout/README.md), or
[boxed Minecraft mob figures](art/mob_figures/README.md). Creeper, Zombie,
Skeleton, Enderman, Slime and Axolotl figures can be displayed boxed or loose.
Opening a box keeps its empty packaging, which can also be placed and refilled.
Prices, rank
weights and machine profiles are server-configurable. See the
[Arcade Pass economy guide](art/arcade_economy/README.md) for controls, defaults,
configuration, transferable-card data and future loot support.

The freestanding Miku cutout costs 1,500 Prize Points by default and can also be
stocked in claw machines or gachapon. It is about 1.6 blocks tall, with printed
artwork, cardboard backing and a folded support. Place it on solid ground at
16 angles, spaced 22.5° apart like a standing sign. Breaking either half returns
one cutout in survival.

The separate [Custom Display Box](art/custom_display_box/README.md) displays one
item with an automatically colored package and printed name. Craft four with
eight paper around a glass pane. Place a box and right-click it with the item;
empty-hand right-click toggles angled or straight-on display. Sneak-right-click
unpacks it and keeps the labeled packaging. Sneak-use
a held filled box to unpack it in your inventory. Existing mob boxes retain
their original static models and behavior.

## Start here

Open this folder in VS Code. The Java and Gradle extensions are already installed.
Use **Terminal > Run Task** for the `Fun:` tasks, or open a terminal here:

```powershell
.\dev.cmd Build
.\dev.cmd Client
.\dev.cmd PackClient
```

- `Build` creates `build/libs/funpackcustom-0.1.0.jar` and a separate sources jar.
- `Client` launches a small Minecraft test instance with just NeoForge and our mod.
- `PackClient` launches a separate development copy of the full Fun pack with our mod loaded from source.
- `SyncPack` refreshes the copied mods, configs, resource packs, and pack scripts from the live pack.
- `Prepare` downloads game assets and prepares client/server launch files.
- `Server` launches a small dedicated server for checking server compatibility.
- `GameTest` runs 168 cabinet, claw machine, gachapon, figure, cutout, display box, poster, ordering and Arcade Pass economy integration tests in a disposable test world and exits.
- `Data` runs our data generators once we add them.

The script selects Java 21 locally. Your default Java installation remains available to other projects.
`dev.local.json` stores this computer's JDK and pack paths; it is excluded from Git.
On another computer, copy `dev.local.example.json` and fill in the actual paths.

## Write a feature

Start in `src/main/java/local/funpack/custom/FunPackCustom.java`.
Java code belongs under `src/main/java`; assets and recipes belong under `src/main/resources`.
Mod metadata is in `src/main/templates/META-INF/neoforge.mods.toml`.
Names, versions, and loader versions are in `gradle.properties`.

After editing, build and run the small client. Create a disposable world and type `/funpackdev`.
Then test the same feature with `PackClient` to check interactions with the pack's other mods.
Game runs use `runs/client`, `runs/pack-client`, and `runs/server` respectively;
automated integration tests use `runs/gametest`.
The original pack and its saved worlds are separate from all of these directories.

The tests cover placement, disc insertion/ejection, native playback ticks, saved disc
and song progress, removal without duplicate drops, creative removal, and isolation
between neighboring cabinets. The WACCA, Chunithm, Groove Coaster, MÚSECA,
Project DIVA, and Chrono Circle tests include
saved-disc placement and playback restoration alongside insertion/ejection through
all three sections. Selection tests check Chunithm's acrylic overhang and Groove
Coaster's broad console and marquee in all four facings. Groove Coaster also checks
open footwell collision and unobstructed disc ejection in every facing. MÚSECA adds
rotated deck/marquee selection, the narrow projecting pedal's collision, and
unobstructed disc ejection beside its deeper base. Project DIVA checks its wide
button deck and topper selection and clear disc ejection in every facing.
Chrono Circle checks its clock/hood overhangs, low floor platform, and clear
disc ejection in every facing. maimai adds six-cell placement and cross-column
interaction, every break point in all four facings, adjacent-pair isolation,
saved playback, obstruction checks, and teardown after either support is lost.
DDR SuperNOVA adds twelve-cell placement/removal, every floor support and blocked
section, shared playback, adjacent-cabinet isolation, and physical standing,
step-on access, open dance space, and handrail collision in every facing.
Gachapon adds placement/setup, owner and password access, password-session revocation,
private save data, protected extraction, capsule contents and overflow, exact-item
payments, failed transaction rollback, concurrent buyers and the five-second crank
reset. The ordering kiosk adds two-cell placement/removal, all catalog material
transactions, invalid/stale requests, safe inventory overflow and creative pickup,
spawn-veto rollback, and the loaded shaped recipe. Taiko adds ten-cell placement
and removal in all directions, neighboring-cabinet isolation, shared saved-disc
playback, head/rim sound events, both mouse buttons and hands, cooldowns, and
rejection of invalid tools, blocked rays, and out-of-reach hits. Initial D adds
single-column placement/removal, exclusive seating in every direction, safe rear
aisle exits from a full row, blocked interactions/headroom, logout/removal cleanup,
and uninterrupted saved-disc playback while seated. Arcade Pass tests cover
versioned save/network data, all four exchanges, balance transfers, stale and
cross-player requests, atomic prize delivery, spawn-event reentrancy, live
configuration changes, all supported paid cabinets, weighted rewards, cooldowns,
invalid interaction rejection, and preservation of idle state and disc playback.
Physical pass-slot tests cover native insertion and shift-clicks, tab restrictions,
reinserted-card stale requests, separate viewer inventories, close/break/logout/death
returns, canceled overflow recovery, creative pickup, and swaps during delivery.
Miku and Teto figure tests exercise real placement, rotation, separate neighboring
figures and one-item loot drops; retired prize IDs are rejected by the kiosk.
Miku cutout tests cover all 16 placement angles, yaw rounding, obstructions,
world limits, both removal orders, support loss, neighboring-object isolation,
rotation/mirroring and saved block states. The prize transaction tests also
exercise its configured point price and delivery.
Jubeat tests cover all-facing saved playback, flush neighbors with independent
inventories, sloped selection and collision, disc ejection clearance, obstructed
placement and support-loss cleanup.
BeatStream tests cover disc use through every section, saved playback, all-facing
placement beside Nostalgia, neighbor isolation, single drops and support-loss cleanup.
WACCA poster tests cover all four wall facings, fixed artwork, save/reload,
survival and creative removal, support loss, blocked placement, and canceled spawns.
ONGEKI tests cover rotated placement and blocked placement, saved disc playback,
single drops, neighbor isolation, and selection through the open arch to its monitor.
NEMSYS tests cover disc use and persistence, one-item removal, all-facing placement,
blocked placement, wing selection and the recessed monitor's open front space.
IIDX tests cover eight-cell placement, shared saved-disc playback, every break point
and floor support, adjacent-cabinet isolation, blocked placement, world limits,
and standing, stepping onto and walking across its low platform in every facing.
MUSIC DIVER tests cover all-facing placement and obstructions, shared saved-disc
playback, every section and support removal, neighboring-cabinet isolation,
sloping-rim and marquee selection, and clear disc ejection beside the holster.
All 148 passed on 2026-10-07.
Visual checks and full-pack compatibility remain separate from these server tests.

`SyncPack` overwrites files that exist in the source pack's configuration. Close the development
game before syncing, and keep permanent custom content in source control rather than only in `runs/`.
Removed mod jars from the previous snapshot are removed only from the development copy.
The snapshot records copied mod filenames and SHA-256 hashes.

To use another mod's Java API, add its documented Maven repository and `compileOnly` dependency
in `build.gradle`, and declare any required runtime dependency in the mod metadata.
Only the pack test client discovers the copied pack mods. The small client stays fast to start.

## Model export optimization

Editable cabinet/figure sources stay under `art/` and their `scripts/make_*`
generators. After regenerating a model, run the conservative export pass before
building (Python 3 with Pillow):

```powershell
python scripts/optimize_models.py --write
python scripts/optimize_models.py --check --report build/verification/model-audit.json
python scripts/test_catalog_json_geometry.py
python scripts/test_obj_mesh_optimizer.py
.\dev.cmd Build
```

With no flags, `optimize_models.py` only audits the catalog. `--check` fails when
an export still contains removable geometry or duplicate OBJ declarations.
The checked-in runtime assets are already optimized; normal builds need neither
Python nor Pillow. The pass leaves artwork, animation sheets and editable source
models intact. It removes fully hidden JSON faces, joins compatible coplanar OBJ
faces, and indexes repeated OBJ vertices/UVs. It preserves curved outlines, UV
seams, separate material layers and translucent glass. It does not simplify
faces merely because they use the same material: several palettes contain real
dither detail that would be lost by flattening their UVs.

Claw and gachapon prize displays share a bounded client mesh cache, cleared after
each model/resource reload. Dynamic, tinted, enchanted and external-mod items
retain native rendering. Native in-game views and shader checks remain necessary
after geometry/rendering changes; the export checks alone do not verify lighting.

See [the catalog optimization measurements](art/model-optimization.md).

## Install a finished build

Run `Build`, then copy the **regular jar** (not `-sources.jar`) into the target instance's `mods`
folder while Minecraft is closed. Replace previous versions of our jar so only one remains.
For features needed on both sides, install the same jar on the client and server.
Nothing in the development commands installs a jar into your existing playable instance.

## Server and debugging

The development server uses NeoForge's development launch mode. The helper binds it to
**127.0.0.1:25575** and uses offline mode so the development client can join locally.
The helper reapplies those connection settings each time. This server is for local tests;
the full pack client and the small server have different mod sets, so use `Client` to join it.
Type `stop` in the server terminal to shut it down cleanly.

Attach VS Code's Java debugger to a development game by running
`.\dev.cmd DebugClient`, then using the checked-in **Attach to Minecraft** configuration.
The JVM waits for the debugger on port 5005 before starting the game.
For the full pack use `.\dev.cmd DebugPackClient`.

## Project origin and references

The Gradle wrapper is from the official
[NeoForge 1.21.1 ModDevGradle MDK](https://github.com/NeoForgeMDKs/MDK-1.21.1-ModDevGradle),
commit `7819b902a351b03fe71db00754d103b5a31c4ebf`.
Its template license is retained in `TEMPLATE_LICENSE.txt`.
Our mod starts with the All Rights Reserved metadata setting; choose a license before publishing.

Setup verified on 2026-10-05: the release jar built with Java 21 bytecode; the full pack
client loaded our mod and completed startup; the small server started on 127.0.0.1:25575,
executed `funpackdev`, and saved its test world on shutdown. The Java debugger also reached
its waiting state on port 5005. Gameplay compatibility of future features needs testing as we add them.

- [NeoForge 1.21.1 getting started](https://docs.neoforged.net/docs/1.21.1/gettingstarted/)
- [NeoForge 1.21.1 concepts](https://docs.neoforged.net/docs/1.21.1/concepts/)
- [ModDevGradle configuration](https://docs.neoforged.net/toolchain/docs/plugins/mdg/)
