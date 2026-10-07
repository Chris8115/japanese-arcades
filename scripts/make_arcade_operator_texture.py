"""Original 64px clothing overlays using the vanilla villager UV layout."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
red = "#ad293e"
red_light = "#cc354b"
red_dark = "#762436"
teal = "#38c8c4"
teal_dark = "#228d98"
shirt = "#283949"
cream = "#f4e8c7"

# Shirt torso: top/bottom and side strip, beneath the longer apron layer.
draw.rectangle((22, 20, 37, 25), fill=shirt)
draw.rectangle((16, 26, 43, 37), fill=shirt)
draw.rectangle((22, 26, 29, 27), fill=teal_dark)

# Jacket UV faces: side, front, side, back. Only the apron-length area is opaque.
draw.rectangle((0, 44, 5, 59), fill=red_dark)
draw.rectangle((6, 44, 13, 59), fill=red)
draw.rectangle((14, 44, 19, 59), fill=red_dark)
draw.rectangle((20, 44, 27, 59), fill=shirt)
draw.rectangle((6, 44, 6, 59), fill=teal_dark)
draw.rectangle((13, 44, 13, 59), fill=teal_dark)
draw.rectangle((7, 45, 7, 50), fill=red_light)
draw.rectangle((0, 51, 27, 52), fill=teal_dark)
draw.rectangle((6, 51, 13, 51), fill=teal)
draw.rectangle((6, 59, 13, 59), fill=teal)
# Chest badge and a little joystick pocket emblem.
draw.rectangle((10, 46, 12, 47), fill=cream)
draw.point((11, 46), fill=teal_dark)
draw.rectangle((8, 54, 11, 57), fill=red_dark)
draw.line((9, 55, 9, 56), fill=cream)
draw.point((9, 54), fill=teal)
draw.line((8, 57, 11, 57), fill=teal)
draw.point((11, 55), fill=cream)

# Upper sleeves keep the villager's underlying forearms and clasped hands visible.
draw.rectangle((44, 22, 59, 25), fill=red)
draw.rectangle((44, 26, 59, 28), fill=red)
draw.line((44, 28, 59, 28), fill=teal_dark)

for entity in ("villager", "zombie_villager"):
    path = ROOT / "src/main/resources/assets/funpackcustom/textures/entity" / entity / "profession/arcade_operator.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    path.with_suffix(".png.mcmeta").write_text('{"villager":{"hat":"none"}}\n', encoding="utf-8")

preview = ROOT / "build/verification/arcade-operator-texture.png"
preview.parent.mkdir(parents=True, exist_ok=True)
image.resize((512, 512), Image.Resampling.NEAREST).save(preview)
print("Created original arcade operator overlays: 64x64 RGBA, red apron and teal trim.")
