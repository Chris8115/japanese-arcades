# Claw Machine

A working white, cyan and pink glass prize cabinet, inspired by the supplied UFO Catcher Triple reference. The connected cabinet occupies **3 blocks wide × 2 deep × 3 tall**. All six floor cells must be supported and all eighteen occupied cells must be clear before placement.

Obtain it in the Japanese Arcades creative tab, with `/give @s funpackcustom:claw_machine`, or from the Arcade Ordering Kiosk's Machines tab for **24 iron ingots, 4 gold ingots, 1 diamond, 12 glass and 8 redstone**.

## Operator setup

Placement assigns the owner and prompts for a 4–32 character PIN or phrase. **Shift-right-click with an empty main hand** opens operator access from any cabinet section. The owner and creative players bypass the password; other operators must enter it. Password operators may restock and change play settings, but only the owner or creative players may change the PIN or remove the machine.

- **Price:** insert a real item stack. Its item, components and count set the cost of one attempt, just like the gachapon. The price stack is a retained template, not consumed by sales.
- **Prizes:** the 3×3 inventory grid corresponds to the visible positions in the cabinet. Its top row is the back of the cabinet; its bottom row is the front. Each occupied slot offers its **entire stack**, including names and other item components.
- **Collected:** nine slots hold payments. Withdraw these to make room for further plays.
- **Win %:** base payout chance, from 0% to 100%.
- **Ramp:** optionally increase the chance after each paid attempt until the chosen Nth attempt reaches 100%. A successful prize delivery resets the counter. N may be 1–1000; N=1 guarantees each stocked grab. With ramp disabled, every attempt uses the base chance.

The initial settings are 25% with a guaranteed fifth attempt. For example, 5% with N=5 gives successive chances of 5%, 28.75%, 52.5%, 76.25% and 100%, provided none of those attempts has already won. Operator settings and the current counter persist on the machine.

## Playing

Right-click the cabinet to aim. The view centers once on the glass without moving the player, then stays steady. A transparent screen leaves the machine visible and displays a small control strip at the bottom. Play uses a dedicated screen to avoid inventory-container overlays. The selected prize pad has a thin cyan outline:

- Click/hold the arrows, or use **WASD / arrow keys**.
- **Space / Drop** commits the attempt over the selected prize position.
- **Esc / Leave** closes the controls.

Aiming and leaving before Drop are free. Dropping over an empty slot, insufficient matching currency, or full payment storage does not charge the player; feedback appears just above the controls. Payment comes from the player's ordinary inventory or offhand. One player controls the machine at a time, and paid attempts prevent operator inventory changes. The usual HUD returns when the controls close, including when the server closes them automatically.

The claw visibly descends, grips the selected prize, lifts and returns toward the front-left prize chute. The server rolls the configured chance once per paid attempt. A losing grab opens above an empty position on that return path and drops the full stack back into the machine; when other positions are occupied, the newly emptied source position remains available. A winning grab reaches the chute and dispenses the full stack as an item entity reserved for the player to collect.

The unpaid aiming session expires if abandoned. Once paid, the animation finishes even if the player closes the controls, walks away or disconnects. Paid phases, the reserved prize, chosen result and return destination survive save/reload. Reopening a machine starts a new free aiming session after its current attempt finishes; it never automatically pays for another attempt.

## Preservation and access

Only the anchor cell owns an inventory. Removing any section removes the connected cabinet and returns its stock, price template and collected payments once. Creative removal returns contents without another cabinet item. Hoppers/pipes have no exposed inventory capability, pistons cannot move the cabinet, and explosions do not remove its cells. If another mod temporarily rejects world-item delivery, a pending winning delivery retries; returns from a removed machine are persisted separately until they can spawn in a loaded chunk.

Public machine updates contain only visible prize previews, price and animation poses. Password hashes, balances in the collection inventory, payout settings and the preselected win/loss result are never included in public block-entity updates. Control packets are validated against the current menu, player, machine position, unique session and sequence number.

## Assets

The static cabinet is split into eighteen native block models, indexed `x + 3*z + 6*y`, with one separately rendered moving claw and live item displays. Model coordinates use 16 units per block; the full cabinet is 48×48×32 units. North is the front (negative Z). From the front, the inventory's left-to-right columns map to model X=40,24,8; its back-to-front rows map to Z=24,16,8.

The prize floor covers the full pedestal perimeter. The prize chute has interior side walls, a back, a floor and a ceiling collar, leaving the front prize-out opening and the upper delivery aperture open. Small offsets separate the cap and lining from the exterior shell to prevent overlapping faces from flickering.

The controls are centered clear of the chute. The aperture rim ends behind the pink belt and ahead of the nearest prize pad; its bars meet edge-to-edge. The raised white control cap separates the screen bezel from the belt's top face, eliminating the overlapping trim and flicker. Prize-grid coordinates and the chute's delivery point are unchanged.

Detailed arcade prizes reuse a bounded, renderer-local mesh cache instead of decoding their full item models every frame. The cache preserves their 3D geometry, UVs, baked lighting and display transforms. Camera-facing checks skip back faces only for native passes that already enable culling; shadow passes retain the full mesh. Vanilla rendering replays primitive vertex data without per-quad temporary allocations. Sodium keeps its native bulk quad encoder when the current vertex consumer supports it; extended Iris shader buffers that reject the fast path use the primitive cache instead of falling back to repeated quad decoding. Animated sprites are marked active through Sodium's optional API. Count labels are drawn together after items to avoid repeated buffer flushes.

Dynamic, enchanted, tinted or custom-rendered items use the normal item renderer. Unknown render passes retain all faces. The cache is bounded to 800,000 vertices (roughly 40 MiB including its quad data/references) and is discarded when Minecraft rebuilds its block-entity renderers on resource reload. Neither Iris nor Sodium is required; unavailable optional hooks fall back conservatively. Payment, inventory and payout logic are unchanged.

Generate the static models, textures and editable Blockbench source with `scripts/make_claw_machine_model.py`. Render with Blender using `--background --python scripts/render_claw_machine_model.py`. `claw-machine.bbmodel` and `claw-machine.blend` preserve the editable geometry and packed textures. The hero, front, side and controls previews show the actual cabinet geometry with a parked claw. These studio previews are separate from the live Minecraft verification screenshots.

Gameplay screenshots from the initial implementation: [cabinet](claw-angle-in-game.png), [operator inventory](operator-in-game.png), [play controls](play-controls-in-game.png), [slipping prize](claw-slipping-in-game.png), [landed prize](claw-landed-in-game.png), [winning payout](claw-payout-in-game.png).

Earlier seam repair close-ups: [left side](sealed-left-seam.png), [right side](sealed-right-seam.png), [chute](sealed-chute-front.png), [chute from the left](sealed-chute-left-oblique.png), [chute from the right](sealed-chute-right-oblique.png), [deck](sealed-deck-oblique.png), [front](sealed-front.png).

## Verification

`./dev.cmd GameTest` passed all **125 required tests**, including the new placement and transaction suites. The claw tests cover all four orientations, every breakable cabinet section, placement obstructions, operator access, exclusive sessions, stale/forged controls, exact payment components, whole-stack wins, forced loss relocation, ramp/reset behavior, paid-phase reloads, rejected item spawns and reentrant removal without duplicate rewards. Final log: `build/verification/claw-gametest-final.log` (ignored runtime output).

The initial gameplay release passed setup, operator inventory/settings, keyboard/mouse controls, insufficient-currency and empty-target feedback, camera framing, HUD restoration, paid Escape, a winning full-stack payout and a forced losing grab in the small native Minecraft client. The loss moved all 17 diamonds from the back-right position into the empty center position, charged exactly three emeralds and produced no world award. Seventeen screenshots and the completed probe result are under `runs/claw-release-visual-probe/` (ignored). The saved gameplay images above all come from that run at GUI scale 4.

`./dev.cmd Build` passed for the initial gameplay release, SHA-256 `bd92fbcd354045f17fb04762b3d8d5f6d44c4578f746164b08c3fce81162f23a`. The release contains the eighteen cabinet models and runtime textures, with no verification helper, third-party jars or authoring files.

An earlier build passed the gameplay probe with 218 copied third-party mods, but showed extra inventory overlays on the controls. Play now uses a plain screen with its own menu type. The final copied-pack retry exhausted JVM native memory before the gameplay sequence, so **full-pack compatibility remains unverified**. The separate small-client run above passed on the initial gameplay release. `build/verification/claw-native-final-audit.json` preserves the build hashes, screenshots and separate outcomes. The original pack and its saves were not modified.

The deck/chute geometry correction passed `./dev.cmd Build` and a focused native small-client inspection from seven camera positions against a contrasting floor and background. Both side seams and the chute interior are closed, without the added lining's coplanar hatching; the upper delivery aperture and front port remain open. That geometry revision used JAR SHA-256 `924fc6b1efe603387af2a78cb4812a8adef20e512cae7d7baf841e5a9af5996d`. Compared with the gameplay-verified release, only eight model JSON entries differ and every Java class is byte-identical. Evidence: `build/verification/claw-sealed-native-audit.json`, `build/verification/claw-seam-static-audit.json`, and the earlier seam close-ups above. Editable Blockbench/Blender sources and studio previews were regenerated from the same geometry.


The chute/control and rendering correction passed `./dev.cmd Build` and native before/after comparisons on the final release JAR, SHA-256 `9a0a7cd8d70e51bb4d97b0701435f007bc7fb360f70e454debdc9a21c9ae2c77`. The small client and a copied Sodium 0.8.13 / Iris 1.8.14-beta.1 subset both passed stocked rendering, a moving heavy-prize grab, oblique views, resource reload and clean exit. ComplementaryReimagined r5.9.3 was explicitly enabled for the shader comparison. Final views: [chute and controls](performance-chute-in-game.png), [stocked cabinet](performance-stocked-in-game.png), [active grab](performance-grab-in-game.png).

| Renderer | Nine prizes | Claw rendering time, before → after | Observed FPS, before → after |
| --- | --- | --- | --- |
| Native client | Mixed cabinets | 12.12 → 5.59 ms | 77 → 136 |
| Native client | Taiko cabinets | 20.62 → 6.24 ms | 46 → 145 |
| Sodium / Iris, shaders off | Mixed cabinets | 8.53 → 5.84 ms | 96 → 136 |
| Sodium / Iris, shaders off | Taiko cabinets | 11.72 → 8.35 ms | 68 → 94 |
| Sodium / Iris, Complementary on | Mixed cabinets | 15.62 → 10.15 ms | 51 → 74 |
| Sodium / Iris, Complementary on | Taiko cabinets | 26.41 → 12.46 ms | 28 → 63 |

These are first-case results from an isolated 1280×960 flat-world scene at a fixed camera, with VSync/capping disabled, three seconds of warmup, and at least six seconds / 120 samples per case. Rendering times measure elapsed wall time inside the claw renderer, not exclusive CPU accounting. Scheduling/driver variation affected FPS; the audit preserves every repeated case, percentile and empty/vanilla-item control instead of selecting the best run. These numbers do not predict FPS in the complete user world. The full third-party pack was not re-run.

The final vanilla lighting comparison against the baseline found under 0.07 mean RGB difference in static prize regions, verifying that explicit baked normals preserve their original shading. Geometry checks confirm the rim clears the belt, stock pad and relocated controls, with no change to prize coordinates or delivery point. All common/server classes are byte-identical to the gameplay-verified baseline. Evidence is saved under `build/verification/claw-performance/comparison.json`, `build/verification/claw-performance-runtime-audit.json`, `build/verification/claw-controls-clearance-audit.json` and `build/verification/claw-performance-build.log` (ignored verification output). The original pack and its saves were not modified.
