# Printed artwork generation

Created with the built-in `image_gen` tool, with transparent background enabled.
Style references: `art/hatsune_miku_cutout/miku-cutout-print.png` and
`art/kasane_teto_cutout/teto-cutout-print.png`. Both originals are unchanged.

Project source: [rin-cutout-print.png](rin-cutout-print.png), copied byte-for-byte from the generated PNG.
Character identity reference: [Piapro's official character page](https://piapro.net/intl/en_character.html).

## Final prompt

Use case: style-transfer. Asset type: transparent printed character artwork for a Minecraft cardboard cutout. The two input images are style references: our existing Miku and Teto cutout prints. Create one matching companion character, not a group. Match their large square cuboid head, blocky Minecraft limbs, coarse pixel textures, front orthographic view, friendly small pixel smile and standing wave pose, full body visible including footwear. All anatomy is simple Minecraft cuboids; no smooth anime anatomy. Isolated print artwork only, on a genuinely transparent exterior background and transparent gaps. Character itself opaque, crisp clean silhouette. No floor, shadow, glow, haze, cardboard edge, pedestal, text, logo, props or other characters. Portrait framing, centered with a little clear margin on every edge. Subject: KAGAMINE RIN in her recognizable classic outfit. Bright golden blonde short bob with angular bangs, huge WHITE bow atop the head made from chunky folded cuboid ribbon, small white hair clips. Blue-cyan pixel eyes and a white/dark headset. White sleeveless sailor-style top with dark charcoal collar trimmed yellow and a yellow neck bow, black shorts with yellow trim, dark charcoal detached arm warmers with yellow cuffs and matching chunky lower-leg warmers/boots with yellow accents. Keep the reference's playful Minecraft proportions and modest toy-like styling. Rin only, no long pigtails, no red/teal hair, no skirt. Friendly raised waving hand as in the reference.

## Geometry integration

The existing cardboard exporter reads the alpha silhouette to construct a thin
backing, folded support and foot. It copies the full-resolution RGBA print into
the runtime texture without resampling or repainting it. These image files have
colored RGB values in transparent pixels; the alpha channel supplies the clean
silhouette used in game.
