# Stackable Gachapon model

An individual white capsule machine, authored to fit one Minecraft block. Copies can be placed flush vertically and immediately beside one another. The reference details are the softly rounded shell, clear-edged upper chamber, blue/yellow rotary surround, white turning handle, separate coin slot and lock, and the recessed capsule collection opening.

## Using the machine

Find **Gachapon Machine** in the **Japanese Arcades** creative tab, or use:

```mcfunction
/give @s japanesearcades:gachapon
```

Each unit occupies **1×1×1 blocks** and holds its own owner, password, price, prizes and collected payments. Sneak while placing another unit on top of an existing one. The first placement opens a prompt for the owner's chosen **4–32 character PIN or phrase**. If the prompt is closed, the owner can set a password through the operator inventory; sales stay disabled until one is set.

**Shift-right-click with an empty main hand** to operate a machine. Its owner and creative players open the inventory directly. Everyone else must enter the password. The owner or a creative player can change it in the inventory; changing it closes out existing password-authorized sessions. Password holders may restock, withdraw currency and change the price or reward amount, but cannot change the password or mine the machine.

- **Price:** put an actual currency item stack here. Its item, components and count define the cost. This stack stays in the slot as a price template and is returned when removed.
- **Rewards:** nine slots, like a dropper. A roll chooses uniformly among nonempty slots. Stack size does not increase the chance of that slot being selected; duplicate entries in multiple slots do.
- **Collected:** nine separate slots for accepted payments. Operators can withdraw these items. A full collection inventory stops sales without charging the buyer.
- **Items / roll:** choose **1–64** and press **Save**. The awarded amount is capped at the number of items remaining in the selected slot.
- **New password:** enter the replacement PIN or phrase and press **Set**. The owner's access does not depend on remembering it.

Players hold right-click while looking at the machine for a **two-second crank**. Payment comes from matching items in their inventory or offhand and is taken only at completion. Releasing the button or walking away pauses the crank. The same player can resume within **five seconds**; after that, progress and the reservation reset with **no payment taken**. One finished crank requires a release before another roll can begin.

Every successful roll dispenses **one Gachapon Capsule containing the whole reward amount**. For example, an amount of 16 with only 8 items left produces one capsule containing all 8. Right-click the capsule in hand to open it. It preserves the reward's names and other item components through saving and reloading; inventory overflow drops beside the player. Opening consumes the capsule, including in creative mode.

The machine displays **amount X currency icon** beside the dial and up to nine live reward icons in its upper window. Empty prize slots disappear from the display. Breaking a unit as its owner or in creative returns its stocked items, physical price template and collected currency. Hoppers and item pipes cannot bypass operator access; pistons and explosions do not move or break a stocked unit. World-admin commands remain authoritative.

`gachapon.bbmodel` contains the editable original meshes and embedded material/decal atlases. `gachapon.blend` contains the packed Blender studio scene with a single machine and a hidden 2×2 arrangement. All artwork is original procedural drawing; there are no downloaded logos or image-generation dependencies.

Rebuild the assets with `scripts/make_gachapon_model.py`. Render with Blender using `scripts/render_gachapon_model.py`. Add `-- --single-only` for the single view. The export uses NeoForge's built-in OBJ loader for genuine circular parts, rounded corner profiles and the independently rotating crank. There is no custom geometry loader.

## Live displays and sample previews

The price plaque and prize poster are intentionally blank in the static model. In game, the block entity renderer draws the configured amount and currency item on the plaque and up to nine actual reward-stack icons on the poster. It also rotates the separate crank model during a player's held interaction.

The PNG previews demonstrate a **sample inventory**, not fixed machine contents: diamonds, emeralds, an ender pearl, a nether star, a golden apple, iron, amethyst, a heart of the sea and a totem, at a sample price of two emeralds. The preview script reads their icons from the locally cached Minecraft client jar into ignored `build/gachapon-preview/`. Those icons are not copied into the mod or packed into the editable Blender file. The displayed PNGs are model renders with sample overlays, not screenshots from a running game.

Actual Minecraft screenshots are saved separately: [stacked machines with live displays](gachapon-in-game.png), [operator inventory](gachapon-inventory.png), [masked password setup](gachapon-password-setup.png), and [a dispensed capsule in hand](gachapon-capsule-in-game.png). The test machines use a different sample stock, including tools, a block and a spawn egg, to check several kinds of inventory icons.

## Model coordinates

Minecraft model coordinates use 16 units per block. North is the front (negative Z); a viewer facing the front sees increasing X to their left.

| Element | Coordinates |
| --- | --- |
| Complete machine bounds | X 0.22–15.78, Y 0–16, Z 0.096–15.78 |
| Crank pivot | (8.2, 5.0, 1.0) |
| Crank baked model | `japanesearcades:block/gachapon_crank`, centered at origin |
| Price center | (13.05, 7.0, 0.94) |
| Prize columns, left to right | X 11.9, 8.0, 4.1 |
| Prize rows, top to bottom | Y 13.72, 11.75, 9.78 |
| Prize display plane | Z 1.48, ahead of the poster at Z 1.60 |
| Prize icon size | 1.55 model units |

The transparent-looking chamber uses a clear opening, tinted perimeter facets and narrow highlights. This prevents translucent block sorting from obscuring or washing out the real prize icons. The capsule inventory item is a separate round two-color mesh with an equatorial seam.

## Validation

The Java 21 build and all 58 server GameTests passed on 2026-10-06. Eleven gachapon tests cover stack placement and setup, owner/creative/password access, stale packet rejection, password revocation, saved private data, hopper/mining protection, one-capsule contents, overflow, exact component-specific payments, full storage, changed quotes, refused item spawns, simultaneous buyers, and the 100-tick inactivity reset.

An isolated NeoForge client verified real inventory/price icons, all four facings, masked password screens and the operator inventory. A real client hold/release/resume interaction produced exactly one capsule and deducted exactly one configured payment. Runtime geometry was also baked with NeoForge's OBJ loader for body/crank in all facings plus both inventory models; materials, UVs and packaged resource references were checked. Full modpack compatibility is a separate check; this build has not been installed into the original instance.
