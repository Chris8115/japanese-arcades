# Printed artwork generation

Created with the built-in `image_gen` tool, transparent background enabled.
Project source: `miku-cutout-print.png`, copied byte-for-byte from the selected generated PNG.

## Generation prompt

Create a production-ready front artwork texture for a freestanding cardboard standee in a Minecraft mod. Subject: Hatsune Miku reimagined as an authentic Minecraft player character, full body, immediately recognizable teal long twin-tails, square cuboid head, simple large square turquoise pixel eyes, tiny pixel smile, grey sleeveless shirt with turquoise necktie, short black pleated-looking but BLOCKY skirt, black detached long sleeves with teal cuff trim, black knee-high boots, small black-and-magenta headset and rectangular hair ties. Her body must use Minecraft proportions and rectangular cuboid limbs, about 2 heads tall beneath the head, NO realistic human anatomy, NO smooth anime face, NO round eyes, NO curves. All textures should look like deliberately coarse Minecraft pixel art on solid box forms. Pose: friendly standing upright, feet slightly apart, one block arm raised in a small friendly wave, other arm lowered; twin-tail rectangular hair masses hang to about knee height with a few stepped pixel edges. The character is oriented directly toward camera in a front orthographic view with very slight shading of cuboid forms, symmetric forward-facing head and torso, NO three-quarter turn. Her whole silhouette including hair, wave, and boots fits comfortably in the frame with generous transparent margin. This is the image PRINTED on a cardboard cutout, so output only the isolated character art, NO actual standee, NO cardboard border/back/base, NO drop shadow or floor/contact shadow, NO environment, NO text, NO logo, NO extra props. Clean crisp solid opaque pixels inside the silhouette, fully transparent exterior background. Tall portrait composition.

## Transparency refinement prompt

Edit this image for a Minecraft cardboard cutout texture. Preserve the exact character, pose, cuboid shapes, pixel colors, facial expression, outfit and framing. Remove ALL exterior glow, halo, aura, shadow, vignette, haze and backdrop. Exterior pixels must be completely transparent, including the space between her legs and gaps beside the arms and twin tails. Character surfaces themselves must be fully opaque. Hard clean silhouette edges, with only minimal anti-aliasing. Do not add a border, ground, stand, text or other objects. Do not change the character's appearance; only fix the transparency and remove the colored halo outside the character.

The mesh generator derives a cutout silhouette from the alpha channel and retains the image colors and alpha in the runtime texture.
