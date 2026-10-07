# Japanese arcade

A compact, two-story Japanese game center with dark timber posts, red stripped-mangrove beams, a stepped blackstone roof, cherry planters, lanterns and large native painting signs. The downstairs arcade opens onto a broad entrance; a two-wide staircase reaches the balcony lounge around an open atrium.

The complete template is **19 × 18 × 19 blocks** (X/Y/Z), including roof eaves and entrance landscaping. Its front faces north. The ground-floor surface is at local Y=1, with walking space at Y=2; the lounge surface is at Y=6, with walking space at Y=7. See [floor plans](floor-plans.svg) and the exact [layout manifest](layout.json).

## Contents

- Six usable music cabinets: Jubeat, WACCA, Chunithm, Taiko, Project DIVA and Nostalgia. Each includes every required multiblock part and an empty jukebox anchor.
- One accessible arcade kiosk and a persistent adult villager, initially unemployed so it can claim the kiosk naturally. No fixed world-coordinate job site is stored in the template.
- Four boxed mob figures on display plinths, lounge seating, tables, bookshelves and a red daybed.
- A service chest containing 8 paper and 3 bread. It introduces no competing profession workstation. Cabinets begin without discs; there are no stocked claw-machine or gachapon inventories.
- Four native paintings: the vertical Japanese sign, GAME CENTER entrance sign, side invader mural and rear Fuji mural. Their solid backing and unobstructed display volumes are checked by the generator.

The architecture uses ordinary vanilla blocks. The only placed entities are the four paintings and resident villager; the six cabinet jukeboxes retain their existing behavior.

## Native templates

`japanesearcades:arcade/japanese_arcade` is the standalone building. `japanesearcades:arcade/japanese_arcade_village` adds one `north_up` jigsaw at local `(9,1,0)`, with name/target `minecraft:building_entrance` and final state `minecraft:dirt_path`. The connector occupies the same ground-surface level as a village road. World-generation pools and the painting anchor processor are maintained separately from this asset generator.

The optional `japanesearcades:arcade/japanese_arcade_integrated_village` variant instead puts its connector at `(9,2,0)`, with name/target `integrated_villages:house` and final state `minecraft:air`. Integrated Villages roads connect through walking air, so this one-block-higher connector keeps the arcade floor aligned with those roads. The building and furnishings otherwise match the standalone template.

For a manual preview in a test world, use `/place structure japanesearcades:japanese_arcade`. The generated `japanesearcades:arcade_test` empty fixture and `japanesearcades:arcade/test_road` connector fixture support runtime placement and rotation tests.

## Regeneration

Run from the repository root:

```text
python scripts/make_japanese_arcade_structure.py
```

The [generator](../../scripts/make_japanese_arcade_structure.py) uses only the Python standard library and writes deterministic compressed structure NBT, `layout.json` and `floor-plans.svg`. Its checks cover machine parts and floor support, entry clearance, staircase headroom, resident spawn clearance, and mural support/clearance. NBT includes explicit air so placement clears its rooms and roof space; unused perimeter cells in the bottom two layers are omitted from NBT to preserve surrounding terrain.

## Verified in Minecraft 1.21.1 / NeoForge 21.1.252

Build and all **179 required GameTests** passed on 2026-10-07. New tests cover
additive pool reconciliation, all four building rotations, mural attachment,
perimeter terrain preservation, native road attachment, dry terrain/build-height
checks, natural single-worker kiosk employment, restocking and real trades at
all five career levels.

A normal generated overworld (seed `20261007`) located an independent arcade
in the start chunk reported at `(1056, 0, 352)`. All six cabinet inventories and
their rotated sections were intact, all four paintings survived, and the
resident claimed its kiosk and opened the native Arcade Operator trade screen.

A second disposable client loaded Integrated Villages 1.3.3, Integrated API,
Create, Supplementaries, Moonlight and Dungeons & Taverns from the copied test
pack. It checked injection and actual jigsaw attachment through all eight
supported IV house pools, temporarily forcing arcade selection only inside that
test world and restoring each pool afterward. Every entrance met its road at
walking height, with all furnishings, paintings and residents intact. This is
targeted compatibility verification, not a test of every mod in the full pack.

See [native evidence and exact tested artifact/mod hashes](native-verification.json).
The test harness and disposable worlds remain under ignored `build/` and `runs/`.

![Naturally generated arcade](screenshots/natural-front.png)
![Arcade at sunset](screenshots/natural-evening.png)
![Ground-floor cabinets](screenshots/ground-floor.png)
![Upstairs lounge](screenshots/upstairs-lounge.png)
![Native operator trading screen](screenshots/operator-trades.png)
