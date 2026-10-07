# Mob Collection prize figures

Six miniature Minecraft mobs are available as boxed arcade rewards: Creeper,
Zombie, Skeleton, Enderman, Slime and Axolotl. Each has three independently
placeable forms: boxed figure, loose figure and empty display box.

## Collect and display

- Redeem a boxed figure in the Arcade Kiosk's **Prizes** tab. Each costs
  **1,000 Prize Points** by default, configurable under `prizes.boxed_<mob>_figure`
  in `japanesearcades-arcade-economy.toml`.
- Operators can also stock the ordinary boxed items in existing claw and
  gachapon prize inventories. All three forms appear in the Japanese Arcades
  creative tab.
- Right-click a surface with any form to place it facing you.
- Right-click a placed full box with an empty hand to take out the figure.
  The matching empty box stays placed.
- Use the matching loose figure on a placed empty box to repack it.
- Sneak-right-click in the air while holding a boxed figure to open one in
  your inventory. This returns both the loose figure and its empty box.
- Breaking any form in survival drops exactly that form, so a filled box
  stays filled and an empty box stays empty. Creative removal drops nothing.

Opening and repacking convert exactly one source, including in creative.
When opening with a full inventory, outputs are delivered nearby; a canceled
delivery leaves the original collectible intact. Wrong mob figures do not fit
another mob's box. Decorations have ordinary saved block states and no block
entity, ticking animation or custom renderer.

## Size and model design

Boxes occupy 10/16 of a block in width, 14/16 in height and 8/16 in depth. Loose
figures fit an 8/16-square footprint and are at most 11.5/16 tall. The cardboard
shell, inset backing, front display window and miniature are actual geometry.
Printed detail is kept in textures, with cutout window highlights avoiding a
translucent render pass. Boxes share a collection identity, individual mob
colors and numbers 01–06.

| Mob | Loose figure faces | Boxed figure faces | Empty box faces |
| --- | ---: | ---: | ---: |
| Creeper | 55 | 93 | 38 |
| Zombie | 55 | 93 | 38 |
| Skeleton | 91 | 129 | 38 |
| Enderman | 56 | 94 | 38 |
| Slime | 55 | 93 | 38 |
| Axolotl | 47 | 85 | 38 |

Placed and inventory face counts are identical. Counts cover the whole object,
including packaging and the figure inside a full box. Each form uses baked
vanilla JSON geometry with no live mob renderer. `model-audit.json` records
exported bounds, counts and source texture hashes.

Runtime IDs use `japanesearcades:boxed_<mob>_figure`,
`japanesearcades:<mob>_figure`, and `japanesearcades:<mob>_figure_box`, where `<mob>`
is `creeper`, `zombie`, `skeleton`, `enderman`, `slime` or `axolotl`.

## Sources and verification

The model generator and native JSON assets preserve the Minecraft blocky mob
shapes. Mob texture sources are copied from the local Minecraft 1.21.1 client;
the packaging artwork is generated with the collection assets.

`MobFigureGameTests` exercises actual placement and loot in every facing,
opening/repacking, retained empty boxes, mismatches, neighboring displays,
creative behavior, both hands, and failed overflow delivery. The existing
economy tests exercise purchases of every new boxed reward.

The development build and all **153 GameTests** passed. The disposable native
client verified every model in all four facings, inventory models, missing
texture checks, resource reload and the reward kiosk's first and last mob
entries. Its report is under `runs/mob-figures-final-visual-probe/`.

Rebuild models with `python scripts/make_mob_figures.py`; retained skin PNGs
allow rebuilding without finding the Minecraft client JAR again. Pass
`--minecraft-jar <path>` to use a particular 1.21.1 client. Render the generated
geometry with `blender --background --python scripts/render_mob_figures.py`.
The renderer creates `mob-collection.png`, `boxed-loose-empty.png` and a packed,
editable `mob_collection.blend`. All 18 models also have editable Blockbench
sources and exported geometry JSON in this folder.
