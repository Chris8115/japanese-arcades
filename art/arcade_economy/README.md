# Arcade Pass, Credits and collectible prizes

## Playing the loop

1. Open the existing Arcade Ordering Kiosk and choose **Passes**. **Get an Arcade
   Pass** issues a free blank card into the **To** slot if you do not have one.
   Otherwise, put the actual card you want to use into **To**.
2. Each material button
   trades **one** item from your inventory or offhand and adds the displayed
   amount to the inserted **To** card. The card's name and balances appear
   beside its slot; hover the item for its design and identity. Credits and
   Prize Points are different balances.
3. To combine cards, insert the card to drain into **From**, and the card to
   keep using into **To**, then transfer and confirm. All Credits and Prize
   Points move together. **From** becomes empty of funds, but both cards,
   their names, designs and identities remain available to keep or trade.
   Replacing either card cancels the confirmation. Cards in the rest of your
   inventory are not selected for the transfer.
4. Hold a pass and right-click any of the fourteen full-size arcade cabinets.
   An offhand pass works when the main hand is empty. A successful play spends
   Credits and awards a randomized rank and Prize Points, with a result message,
   note-block chime/bell and particles. The existing idle geometry, textures,
   lights, disc playback and empty-hand seat/drum interactions are preserved.
5. Return to **Prizes**, insert the card to pay with into **To**, and order a collectible.
   Delivery goes into your inventory or safely onto the ground if full.

The two slots hold real items for your own kiosk session. Shift-click a pass
to insert it into **To** first, then **From**; shift-click an inserted card to
take it back. Closing the kiosk returns both cards to you, with overflow
delivery if necessary. Switching tabs retains the inserted cards; the
**Machines** tab does not insert passes into hidden slots.

Gachapon keeps its separate operator-stocked currency/reward system. The kiosk
and prize figures do not award play points. Creative players pay the same
prices when using this loop. Cards are transferable bearer items, so their
balances travel with them when dropped, gifted or stored.

## Default economy

| One material | Credits received |
| --- | ---: |
| Iron ingot | 20 |
| Gold ingot | 60 |
| Emerald | 120 |
| Diamond | 240 |

Every machine initially costs **10 Credits** per play. A player can play once
every **60 ticks (3 seconds)** across all cabinets and held passes.

| Result | Default probability | Prize Points |
| --- | ---: | ---: |
| C | 45% | 10 |
| B | 30% | 20 |
| A | 18% | 40 |
| S | 6% | 80 |
| SS / Perfect | 1% | 150 |

These are simulated results, independent of the decorative game on the screen.
The server commits the debit and award together, before audiovisual feedback.
There is no charged-but-unpaid pending round to lose on disconnect or restart.

Concert glow sticks are modest kiosk rewards at **100 Prize Points each**, in
blue, red, yellow, green, pink, purple and orange. Each purchase delivers one
stick. The standard rank table averages 24 points per play, making these an
early reward; the existing figures, boxed mobs, cutouts and poster keep their
prices. Glow sticks are ordinary items that operators can also stock in claw
machines and gachapon. They have no crafting recipes.

The **Ivory Mech Suit** is a high-tier reward costing **25,000 Prize Points**.
Redeem its deployment item in the kiosk's Prizes tab; the server can change its
price with `prizes.mech_suit`. Operators can also stock the item in claw machines
and gachapon. It has no material crafting recipe.

## Configuration

NeoForge generates **`japanesearcades-arcade-economy.toml`** as a SERVER config and
syncs it to joining clients. The verification server writes it under `config/`.
Edit the server's generated file while it is stopped, then restart. The checked-in
[default example](economy-defaults.toml) documents all values; it is not loaded
as a second configuration. `ArcadeEconomyConfig` owns the runtime values.

- `[exchange]`: Credits per iron ingot, gold ingot, emerald or diamond.
- `[play]`: default cost, cooldown, weighted rank rows and machine overrides.
- `[prizes]`: point price for each collectible in the prize catalog.

Each glow-stick color has its own price key, such as
`prizes.blue_glow_stick = 100`; the other colors use the same naming pattern.
The kiosk's scrollable prize list includes all seven colors after the existing
collectibles, with mouse-wheel, arrow-key and Page Up/Down navigation.

Rank rows use `profile|label|weight|points`; weights are relative within their
profile. Add a new profile's rows and assign it to a cabinet with
`namespace:machine|cost|profile`. For example, retain the standard rows and add
`"expert|A|3|100"` and `"expert|S|1|250"`, then use
`machineOverrides = ["japanesearcades:initial_d|25|expert"]`.
Unknown profiles fall back to `standard`; an absent usable standard profile
disables play rather than silently inventing awards. Up to 64 rank rows per
profile are supported. Omit a rank row to remove that result.

Balances are bounded to **1,000,000,000** each. An exchange, transfer, or play
that could exceed that bound is rejected without losing value.

## Data and future additions

The nonstackable card stores the persistent and network-synchronized
`japanesearcades:arcade_pass` data component: schema version, unique card ID,
design ResourceLocation, Credits, Prize Points and transaction revision.
Optional fields and the schema version leave room for later statistics,
mastery, achievements and collection tracking. Design IDs are independent of
balances; transfers preserve unknown designs and all other item components.
Only **Arcade Original** has artwork in this version.

No dungeon loot or extra designs are injected yet. Future loot can set only
the desired fields, with safe defaults for the rest. For example, a command
for testing a found card is:

```mcfunction
/give @s japanesearcades:arcade_pass[japanesearcades:arcade_pass={credits:75L,design:"japanesearcades:default"}]
```

Its ID is assigned on its first kiosk insertion or balance mutation. Gameplay requests identify
the fixed kiosk pass slot, card ID and revision; they never supply a price,
reward amount, resulting stack, or trusted balance. The server validates the
nearby bound kiosk, player, card and available funds, then commits snapshots
atomically. Failed/stale requests, canceled item spawns and recursive spawn
callbacks cannot duplicate a purchase or erase payment. Transfers keep **From** as
a real empty collectible instead of consuming it.

## Collectible art

The Arcade Pass uses reference-based red-and-white e-amusement artwork,
following the user's supplied KONAMI card reference. The authored transparent
PNG is retained unchanged as `arcade-pass-source.png`, and the preview is a
byte-identical copy. The runtime item receives technical square padding and
aspect-preserving downsampling, with the source alpha retained and no redrawing.
This cosmetic update retains the existing `japanesearcades:default` design ID
and all pass functionality. The [artwork notes](arcade-pass-artwork.md) retain
the reference provenance and final image-generation prompt.
The two small placeable prizes follow the user's Miku and Teto figure references.
The pass is an inventory item; the figures are three-dimensional decorations.
The WACCA poster uses the supplied artwork and hangs on a wall like a painting.

| Prize ID | Display name | Default points |
| --- | --- | ---: |
| `hatsune_miku_figure` | Hatsune Miku Figure | 2,500 |
| `kasane_teto_figure` | Kasane Teto Figure | 2,500 |
| `wacca_poster` | WACCA Poster | 750 |
| `nostalgia_poster` | Nostalgia Poster | 750 |
| `nostalgia_op2_poster` | Nostalgia Op.2 Poster | 750 |
| `nostalgia_forte_poster` | Nostalgia FORTE Poster | 750 |
| `sound_voltex_exceed_gear_poster` | SOUND VOLTEX EXCEED GEAR Poster | 750 |
| `sound_voltex_vivid_wave_poster` | SOUND VOLTEX VIVID WAVE Poster | 750 |
| `taiko_drum_n_fun_poster` | Taiko no Tatsujin: Drum 'n' Fun! Poster | 750 |
| `wacca_s_poster` | WACCA S Poster | 750 |
| `wacca_reverse_poster` | WACCA Reverse Poster | 750 |
| `wacca_lily_poster` | WACCA Lily Poster | 750 |
| `wacca_lily_r_poster` | WACCA Lily R Poster | 750 |
| `jubeat_festo_poster` | jubeat festo Poster | 750 |
| `project_diva_arcade_poster` | Hatsune Miku: Project DIVA Arcade Poster | 750 |
| `chunithm_luminous_plus_poster` | CHUNITHM LUMINOUS PLUS Poster | 750 |
| `sound_voltex_exceed_gear_ensemble_poster` | SOUND VOLTEX EXCEED GEAR Ensemble Poster | 750 |
| `maimai_splash_poster` | maimai Splash Poster | 750 |
| `sega_cygames_poster` | SEGA / Cygames Poster | 750 |
| `maimai_universe_poster` | maimai UNiVERSE Poster | 750 |
| `chunithm_paradise_poster` | CHUNITHM PARADISE Poster | 750 |
| `we_love_music_game_poster` | WE LOVE MUSIC GAME Poster | 750 |
| `hatsune_miku_cutout` | Hatsune Miku Cardboard Cutout | 1,500 |
| `kasane_teto_cutout` | Kasane Teto Cardboard Cutout | 1,500 |
| `kagamine_rin_cutout` | Kagamine Rin Cardboard Cutout | 1,500 |
| `kagamine_len_cutout` | Kagamine Len Cardboard Cutout | 1,500 |
| `boxed_creeper_figure` | Boxed Creeper Figure | 1,000 |
| `boxed_zombie_figure` | Boxed Zombie Figure | 1,000 |
| `boxed_skeleton_figure` | Boxed Skeleton Figure | 1,000 |
| `boxed_enderman_figure` | Boxed Enderman Figure | 1,000 |
| `boxed_slime_figure` | Boxed Slime Figure | 1,000 |
| `boxed_axolotl_figure` | Boxed Axolotl Figure | 1,000 |

Point prices are owned by the arcade economy configuration, not embedded in
the models or `ArcadePrizeCatalog`. Prizes have no crafting recipes. Each drops
one copy of its own item when normally broken. Figures have no block entity,
playable game or music inventory. The [mob collection](../mob_figures/README.md)
also supports opening and repacking its display boxes while keeping every figure
and empty box as a separate placeable item.

The [WACCA poster](../wacca_poster/README.md) is 1 block wide and about 1⅜ blocks
tall, with support from two vertical wall blocks. It always displays the same artwork and returns its own poster
item when broken in survival, so it can be rehung. Ordinary paintings do not
randomly select it. The full source image fits inside a visible black front
frame without cropping or stretching; the outside dimensions remain unchanged.

The [eleven additional posters](../arcade_posters/README.md) and the
[eight-print expansion](../arcade_posters/expansion/README.md) share those exact
physical dimensions and placement behavior. All twenty posters have a visible
black front frame, with each full supplied image fitted inside it without
cropping or distortion. Each has its own prize item and configurable 750-point
default price. The original WACCA print and registered identities are preserved.

Both models fit inside one block, below Y15/16. The block class uses a shared
compact X2–14, Y0–15, Z3–13 collision/selection envelope and horizontal facing.
Each chibi figure has a layered outfit, pixel eyes, stepped voxel hair, boots, a
dark display base with teal trim, and a named plaque. Miku has long teal
twin-tails and a black/pink headset. Teto has pink drill curls and white bows.

The initial poster, cat plush, trophy, and miniature cabinet were removed at
the user's request, including their registry entries and runtime assets.
Existing copies of those retired items/blocks are not migrated to the figures.

The current figures are built from cuboids, with interior voxel faces removed.
Both figures' hair uses equal-sided 0.375-unit cubes at its final head width, with
broader clumps and fewer surface stripes. It is not compressed horizontally
after construction. Finer clothing details and Teto's bows use a quarter-unit
grid. Hair, tunic hems, skirt pleats and boots have square steps; cuboid sleeves
are posed at angles. Face pixels stay flat and square. See the
[reference construction notes](figure-reference-notes.md) for the supplied
sheets and the visual details used during the rebuild.

## Files and rebuild

- `scripts/miku_figure_geometry.py` and `scripts/teto_figure_geometry.py` author
  the two figures, using the palette mesh helpers in `scripts/figure_geometry.py`.
- `scripts/make_arcade_prizes.py` generates palette/nameplate textures, native OBJ/MTL,
  model wrappers, blockstates, inventory models, normal loot tables, source
  geometry, embedded-texture Blockbench files, and `art-lang.json`.
- `scripts/render_arcade_prizes.py` renders those source meshes directly and
  saves `arcade_prizes.blend`, with packed artwork and editable prize meshes.
- Each prize has `<id>.geometry.json`, `<id>.bbmodel`, and `<id>.png` here.
- `arcade-prizes.png` shows the two figures side by side at their actual scale.
- `miku-face-detail.png` and `teto-face-detail.png` show the exported faces
  closely. `--miku-face-only` or `--teto-face-only` refreshes the corresponding
  detail and front views. `--miku-only` or `--teto-only` refreshes that figure's
  views, the pair and packed scene; a full render refreshes both figures.
- `arcade-pass-source.png` is the immutable authored card artwork, based on the
  user's red-and-white e-amusement reference. `scripts/prepare_arcade_pass.py`
  copies it byte for byte to the `arcade-pass.png` preview. For the runtime
  `assets/japanesearcades/textures/item/arcade_pass.png`, it crops only exterior
  empty padding using the alpha channel's nonzero bounding box, fits the card
  within 496 × 310 pixels with LANCZOS while preserving aspect ratio, then
  centers it on a transparent 512 × 512 canvas. Alpha is resampled with the
  image, never thresholded or painted; the generated-item model is unchanged.
- `art-lang.json` supplies display-name translation entries for integration
  into the shared language file. It is not loaded by Minecraft itself.

From the repository root, run `python scripts/make_arcade_prizes.py`, followed
by `blender --background --python scripts/render_arcade_prizes.py`. These
scripts do not regenerate or modify any existing arcade cabinet assets.
The figure generator leaves the pass artwork unchanged.
To update only the card preview and runtime texture, run
`python scripts/prepare_arcade_pass.py`. This standalone command does not
regenerate prizes, models, blockstates, or loot tables.
