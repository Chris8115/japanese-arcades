# Figure reference construction notes

These observations describe the user-supplied reference sheets. Byte-identical copies are retained as [Miku and Teto](references/miku-teto-reference.jpg) (originally `1-1000030160.jpg`) and [larger Miku sheet](references/miku-reference.jpg) (originally `2-1000030159.jpg`). Measurements below are approximate visual ratios, excluding the display base, rather than mechanical dimensions. Use the clearer Miku front/side views and the combined sheet's Teto views when judging likeness.

## Proportions and face

- The hair-covered head occupies approximately **35–38% of crown-to-sole height**. Preserve the body and tall boots instead of enlarging the head to half the figure's height.
- The vest is approximately **45–55% of the outer hair-head width**; the flared skirt reaches approximately **65–75%**. Keep the shoulders and waist visibly narrow.
- The first cubic draft's heads were too wide, eyes too low, and bangs too long. Those proportions were revised before rebuilding Miku's hair. The earlier shallow-window interpretation overemphasized hair coverage and should not be used as a fixed facial-width constraint.
- Use tall, narrow pixel eyes with a dark upper edge, colored lower iris, and restrained pale highlights. Miku uses teal/cyan and Teto uses rose. Keep the eyes visibly higher in the face, with space below them; central bangs should not descend almost to the iris bottoms. Avoid large white outlines, raised eye sockets, or separate protruding eyeballs.
- The lower cheeks have broad, subtle pale-pink pixels. Omit a protruding nose; make the mouth almost imperceptible. The face should read as one flat pixel-art surface under the hair.
- **Final Miku pixel correction:** after the hair rebuild, move the accepted eye pattern down one face pixel and use one blush pixel at each lower outer cheek corner. This is a palette/UV update on the existing face grid; preserve all head, hair and body vertices.
- The subsequent fringe adjustment extends the bangs down one hair-grid cell and brings the small side locks to the cheek line. It preserves that corrected eye/blush pattern, the crown, twin tails, headset and body.
- Each Miku eye has one blue iris column toward the nose, eye white outside that, and face color at the outer edge. Keep the dark upper eye pixels above the blue/white area and preserve all pixel positions.
- Shorten Miku's tall upper crown by four complete 0.375-unit courses, following the additional [close angle reference](references/miku-angle-reference.jpg). Lower the upper hair clips and tail roots with it, preserve the painted face and lower fringe/cheek locks, and retain full-sized cubes rather than flattening them.

## Voxel construction

- Build the silhouette from axis-aligned cuboids with deliberate stair steps. Avoid rounded caps, chamfered bevels, smooth curved slabs, cylinders, and cone-like hair.
- **Latest hair correction:** Miku's quarter-unit hair became crowded and flattened when the head was narrowed. Use larger, evenly proportioned hair cubes at the final head width; do not squeeze the completed hair horizontally. Preserve the accepted flat face while revising the hair.
- Use coherent clumps with broad color regions, rather than thin corrugated strands and tiny alternating surface tiles. Keep smaller details for skirt pleats, split vest hems, bows, and sleeve/boot trim. Large hidden internal masses can remain simple.
- Layer narrow gray vest panels over a dark, flared, tiered skirt. Colored trim is thin and stepped. Maintain visible skin between skirt and tall boots and at the upper arms.
- Arms angle outward in the reference poses. The Miku front view is slightly asymmetric; do not require exact agreement between poses drawn on different parts of the sheets.

## Miku

- Twin tails have thick roots, stepped outward middles, and several progressively narrower rectangular tips. They extend nearly to the boots. Staggered surface cubes and changes in outline should prevent them from reading as two broad uniform slabs.
- The rear bob is a compact stack of hair cubes covering the head down to the nape. Do not leave a broad horizontal skin band beneath the rear hair.
- Retain black/magenta headset blocks, a long turquoise tie, split gray vest hem, turquoise skirt/sleeve/boot accents, and a small dark base with a name plaque.

## Teto

- Match the accepted Miku face's square-pixel layout: rose irises toward the nose, eye white outside them, then skin at each outer edge. Use one blush pixel per cheek and the same subtle mouth.
- **Head proportion correction:** narrow the skin core to Miku's 3.28-unit width and 2.872-unit height. Keep Teto's accepted face pixels and body fixed. Rebuild the cap to Miku's 4.5-unit width and 5.25-unit depth, with its crown 3.25 units above the chin. Use true 0.375-unit hair cubes, broad fringe locks and a covered nape. Lower the curl roots and bows with the shortened cap; retain three compact stepped curl turns. The bows keep their small quarter-unit cubes.
- Drill tails are broken voxel spirals, with dark recesses and visible gaps between successive turns. Roots are wide and high beside the head; turns shrink toward points just below the chin/shoulder. Avoid a solid tapered cone or uniformly stacked horizontal rings.
- White bows are small clusters of cubes at the drill roots. The rear hair remains a compact layered cap.
- Retain the gray vest's magenta center details, tiered dark skirt, multiple narrow magenta cuff/hem bands, tall black boots, and the labeled display base.

## Review views

Check front and three-quarter views for skin exposure, eye placement, body width, and expression. Check side and rear views for hair depth, the covered nape, separated tail turns, and complete surfaces. Verify the actual Minecraft item preview and placed model after export; a studio render alone cannot reveal every material, culling, or depth issue.
