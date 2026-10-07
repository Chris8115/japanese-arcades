# Printed artwork generation

Created with the built-in `image_gen` tool, transparent background enabled.
Reference/edit input: the project's original `art/hatsune_miku_cutout/miku-cutout-print.png`.
Project source: `teto-cutout-print.png`, copied byte-for-byte from the generated PNG.
Miku's existing artwork remains unchanged.

## Final prompt

Use case: style-transfer. Asset type: transparent printed character artwork for a Minecraft cardboard cutout. Edit the supplied Minecraft Miku character into a matching KASANE TETO companion cutout. Preserve the same square cuboid head, coarse pixel-art texture treatment, blocky limb proportions, orthographic front view, friendly standing wave, full-body framing, and simple small pixel smile. Replace all teal twin-tail hair with Kasane Teto's recognizable red/rose-red twin DRILL curls: short shoulder-length twin pigtails built from stepped square spiral tiers, three chunky stepped turns on each side, no long straight twin-tails. Short red bangs with a small angular ahoge. Red pixel eyes. Teto's classic dark charcoal sleeveless collared uniform with vivid red trim, narrow red necktie, short charcoal skirt with red edging, dark detached long sleeves with red cuffs, dark tall boots with red details, small black/red headset. All anatomy stays Minecraft cuboids and coarse pixels, no realistic anime proportions or rounded smooth anatomy. Only Teto, no Miku. Isolated full-body artwork ONLY: actual fully transparent exterior background including gaps between legs and arms/hair, solid opaque character surfaces, clean hard edges, NO glow, halo, haze, shadow, floor, cardboard border, base, text or logo. This is the print texture only; the game adds the physical cardboard.

The mesh generator reads the alpha silhouette to create the cardboard backing and preserves the source image bytes in the runtime texture.
