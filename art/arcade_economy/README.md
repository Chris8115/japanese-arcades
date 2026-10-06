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
4. Hold a pass and right-click any of the twelve full-size arcade cabinets.
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
and prize miniatures do not award play points. Creative players pay the same
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

## Configuration

NeoForge generates **`funpackcustom-arcade-economy.toml`** as a SERVER config and
syncs it to joining clients. The verification server writes it under `config/`.
Edit the server's generated file while it is stopped, then restart. The checked-in
[default example](economy-defaults.toml) documents all values; it is not loaded
as a second configuration. `ArcadeEconomyConfig` owns the runtime values.

- `[exchange]`: Credits per iron ingot, gold ingot, emerald or diamond.
- `[play]`: default cost, cooldown, weighted rank rows and machine overrides.
- `[prizes]`: point price for each collectible in the prize catalog.

Rank rows use `profile|label|weight|points`; weights are relative within their
profile. Add a new profile's rows and assign it to a cabinet with
`namespace:machine|cost|profile`. For example, retain the standard rows and add
`"expert|A|3|100"` and `"expert|S|1|250"`, then use
`machineOverrides = ["funpackcustom:initial_d|25|expert"]`.
Unknown profiles fall back to `standard`; an absent usable standard profile
disables play rather than silently inventing awards. Up to 64 rank rows per
profile are supported. Omit a rank row to remove that result.

Balances are bounded to **1,000,000,000** each. An exchange, transfer, or play
that could exceed that bound is rejected without losing value.

## Data and future additions

The nonstackable card stores the persistent and network-synchronized
`funpackcustom:arcade_pass` data component: schema version, unique card ID,
design ResourceLocation, Credits, Prize Points and transaction revision.
Optional fields and the schema version leave room for later statistics,
mastery, achievements and collection tracking. Design IDs are independent of
balances; transfers preserve unknown designs and all other item components.
Only **Arcade Original** has artwork in this version.

No dungeon loot or extra designs are injected yet. Future loot can set only
the desired fields, with safe defaults for the rest. For example, a command
for testing a found card is:

```mcfunction
/give @s funpackcustom:arcade_pass[funpackcustom:arcade_pass={credits:75L,design:"funpackcustom:default"}]
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
This cosmetic update retains the existing `funpackcustom:default` design ID
and all pass functionality. The [artwork notes](arcade-pass-artwork.md) retain
the reference provenance and final image-generation prompt.
The four small placeable prizes retain their original illustrated artwork.
The pass is an inventory item; the four prizes are decorations.

| Prize ID | Display name | Default points | Source mesh faces |
| --- | --- | ---: | ---: |
| `arcade_poster` | Arcade Poster Stand | 150 | 439 |
| `arcade_cat_plush` | Arcade Cat Plush | 500 | 1,489 |
| `rhythm_star_trophy` | Rhythm Star Trophy | 750 | 445 |
| `mini_arcade_cabinet` | Mini Arcade Cabinet | 1,200 | 553 |

Point prices are owned by the arcade economy configuration, not embedded in
the models or `ArcadePrizeCatalog`. Prizes have no crafting recipes. Each drops
one copy of its own item when normally broken. The miniature has a decorative
illuminated star screen and marquee, without a block entity, playable game,
music inventory, or reward interaction.

All four models fit inside one block, below Y14/16. The block class uses a
shared compact X2–14, Y0–14, Z3–13 collision/selection envelope and horizontal
facing. The poster is explicitly a floor-standing acrylic plaque on a weighted
base; it does not claim wall attachment behavior. The cat has rounded teal
body, cream muzzle/tummy, pink inner ears, a star tag, and a curled tail. The
trophy has a raised gold star, teal/pink ribbons, and a musical-note medal.

## Files and rebuild

- `scripts/make_arcade_prizes.py` generates original prize textures, native OBJ/MTL,
  model wrappers, blockstates, inventory models, normal loot tables, source
  geometry, embedded-texture Blockbench files, and `art-lang.json`.
- `scripts/render_arcade_prizes.py` renders those source meshes directly and
  saves `arcade_prizes.blend`, with packed artwork and editable prize meshes.
- Each prize has `<id>.geometry.json`, `<id>.bbmodel`, and `<id>.png` here.
- `arcade-prizes.png` shows the four prizes side by side at their actual scale.
- `arcade-pass-source.png` is the immutable authored card artwork, based on the
  user's red-and-white e-amusement reference. `scripts/prepare_arcade_pass.py`
  copies it byte for byte to the `arcade-pass.png` preview. For the runtime
  `assets/funpackcustom/textures/item/arcade_pass.png`, it crops only exterior
  empty padding using the alpha channel's nonzero bounding box, fits the card
  within 496 × 310 pixels with LANCZOS while preserving aspect ratio, then
  centers it on a transparent 512 × 512 canvas. Alpha is resampled with the
  image, never thresholded or painted; the generated-item model is unchanged.
- `art-lang.json` supplies display-name translation entries for integration
  into the shared language file. It is not loaded by Minecraft itself.

From the repository root, run `python scripts/make_arcade_prizes.py`, followed
by `blender --background --python scripts/render_arcade_prizes.py`. These
scripts do not regenerate or modify any existing arcade cabinet assets.
Keep `arcade-pass-source.png` present when rebuilding; the generator reads this
authored source and never overwrites it.
To update only the card preview and runtime texture, run
`python scripts/prepare_arcade_pass.py`. This standalone command does not
regenerate prizes, models, blockstates, or loot tables.

## Model verification

The 2,926 source faces passed the isolated NeoForge 21.1.252 OBJ parse/bake
audit: **14,630 baked quads**, covering all four facings of all four blocks and
each inventory model. The audit checks unchanged face counts, finite positions,
UV coordinates, texture V orientation, and screen/marquee fullbright lighting.
The machine-local audit report is
`build/verification/arcade-prizes-obj-bake-audit.json`.

The studio renders were inspected for silhouette, readable miniature artwork,
correct texture direction, and joined plush limbs.

## Gameplay verification

The current kiosk screenshots show real **From** and **To** slots and the
red-and-white pass artwork. The earlier placed-prize screenshots remain valid;
the prize models and machine idle appearance have not changed.

On 2026-10-06, the Java 21 release Build and **all 100 dedicated-server
GameTests** passed. The original 16 economy tests cover persistent/network card
data, exact payments, transfers preserving both designs and names, revision
checks, overflow delivery, canceled/substituted spawns, callback reentrancy,
cross-player requests, live configuration changes, all twelve paid cabinets,
rank weighting, cooldowns, invalid clicks, and unchanged idle/disc state.

Four additional tests exercise native pass insertion, invalid items and hidden
tabs, shift-clicks, remove/reinsert stale requests, separate viewers, safe returns
after close/kiosk removal/logout/death, full creative inventories, canceled
return spawns, repeated closes and card replacement during prize delivery.

The final packaged JAR matches every source resource. Its 106 classes target
Java 21, all 216 pre-existing model/texture/blockstate resources are unchanged,
and all 76 pre-existing translations remain present. It contains no test
worlds, probe mod, authoring files or copied third-party dependencies.

The initial economy implementation's disposable small client completed the actual
networked loop at the minimum
**320 × 240** logical GUI size: pass issuance, all four exchanges, both-balance
transfer between different design IDs, billion-sized balance display, native
main/offhand machine clicks without double debit, all four point purchases
and actual prize placement, and the existing material-based machine order.
The short transfer-status wording was rebuilt and visually checked afterward.

That complete loop also passed in a fresh copied-pack world with **all 218
third-party mod JARs**, including its renderer and JEI. Both clients shut down
cleanly. The ignored pack fixture used a 10 GB heap, eight active processors
and disabled Distant Horizons background generation to fit the verification
workload; original instance files and saves were untouched. See the actual
[Passes tab in the pack](passes-in-pack.png),
[prize shop in the pack](prize-shop-in-pack.png), and
[redeemed prizes placed in the pack](earned-prizes-in-pack.png).

The physical-slot revision passed a fresh small-client check at **320 × 240**:
actual mouse insertion, rejection of non-pass items, shift-click insertion and
retrieval, hidden-slot protection on Machines, exact transfer of both balances
with a third inventory card untouched, confirmation cancellation after removing
and reinserting either initialized or raw cards, To-only credit loading and prize
payment, and return of all cards on close. The returned pass also completed a
paid cabinet play. The same slot sequence passed in a new copied-pack world
with all 218 third-party mod JARs. Both clients exited cleanly, and the Passes
and Prizes screenshots below and linked above were refreshed from these runs.

![Loading Credits onto a pass](passes-in-game.png)

![Confirming a transfer between passes](pass-transfer-in-game.png)

![Prize shop](prize-shop-in-game.png)

![The four purchased prizes placed in Minecraft](earned-prizes-in-game.png)
