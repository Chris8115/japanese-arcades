# Default Arcade Pass artwork

Updated 2026-10-06 using the built-in `image_gen` tool, with the user's supplied
photo `1000030162.jpg` as the visual reference. KONAMI, e-amusement and Amusement
IC lettering/marks reproduce that requested reference. The other collectible
prize artwork remains original.

`arcade-pass-source.png` preserves the generated transparent RGBA artwork.
`arcade-pass.png` is the preview. The runtime square texture is prepared by
`scripts/prepare_arcade_pass.py`, maintaining card proportions and transparency.
Only the default item's appearance changes; its ID, data component, balances
and existing card design ID remain the same.

## Final generation prompt

Use case: precise-object-edit. Asset type: Minecraft inventory item texture for an Arcade Pass. Input image is the visual reference. Recreate the FRONT of exactly this white and red KONAMI e-amusement pass as crisp flat print-ready artwork, perfectly straight front-facing and level, no photographic perspective. Preserve its recognizable layout: white upper field; red KONAMI lettering at top-left; cluster of red bubbles mixed with smaller lime, blue, orange dots diagonally above center; the layered scarlet/coral/dark red swoops filling the lower region and rising along the right side, meeting a smaller curved lobe at lower-left; white rounded lowercase exact text "e-amusement pass" across the right red area; the white Amusement IC logo at lower-left and black e-amusement logo at lower-right as in reference. Use clean smooth shapes and sharp legible typography, faithful colors, no extra slogans or designs. Remove the plastic sleeve, glare, fabric background, grain and shadows. Output a square 1024x1024 RGBA canvas with a SINGLE horizontal rounded rectangle card centered, 976 pixels wide by 616 pixels high, so card edges roughly x24..1000 y204..820. Everything outside the card must be truly transparent; white card surface remains opaque. Keep all four rounded corners and the entire card visible. No depth, bevel, mockup, external border or cast shadow. This is the final transparent sprite used directly in the game.
