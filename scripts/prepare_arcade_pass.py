"""Pack authored card art for a square Minecraft item texture without stretching."""
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/arcade_economy'
SOURCE = ART / 'arcade-pass-source.png'
PREVIEW = ART / 'arcade-pass.png'
TEXTURE = ROOT / 'src/main/resources/assets/funpackcustom/textures/item/arcade_pass.png'


def prepare_arcade_pass(source=SOURCE, preview=PREVIEW, texture=TEXTURE):
    """Keep the original preview; only crop empty alpha padding and fit the item."""
    source, preview, texture = Path(source), Path(preview), Path(texture)
    source_data = source.read_bytes()
    with Image.open(io.BytesIO(source_data)) as authored:
        original_size = authored.size
        card = authored.convert('RGBA')
    # getbbox counts every nonzero alpha value, including faint edge pixels.
    # No threshold, recoloring, or painted replacement background is applied.
    alpha_bounds = card.getchannel('A').getbbox()
    if alpha_bounds is None:
        raise ValueError('Arcade Pass source contains no visible artwork')
    card = card.crop(alpha_bounds)
    scale = min(496 / card.width, 310 / card.height)
    fitted_size = (max(1, round(card.width * scale)), max(1, round(card.height * scale)))
    card = card.resize(fitted_size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    offset = ((512 - card.width) // 2, (512 - card.height) // 2)
    # Copy the already-resampled RGBA pixels directly: no alpha multiplication.
    canvas.paste(card, offset)
    preview.parent.mkdir(parents=True, exist_ok=True)
    texture.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(source_data)
    canvas.save(texture)
    return {'source_size': original_size, 'alpha_bounds': alpha_bounds,
            'fitted_size': fitted_size, 'offset': offset, 'texture_size': canvas.size}


if __name__ == '__main__':
    print(json.dumps(prepare_arcade_pass(), indent=2))
