"""Import and prepare the eleven supplied arcade poster prints.

First import: python scripts/make_arcade_posters.py --source-directory PATH
Rebuild:       python scripts/make_arcade_posters.py

The original JPEGs remain byte-identical. Runtime copies retain the full image
with a small uniform downsample and narrow black bars above and below so every
print has the same physical dimensions as the original WACCA poster. Texture
dimensions support the default four atlas mip levels.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/arcade_posters'
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
DATA = ROOT / 'src/main/resources/data/japanesearcades'
POSTERS = (
    ('nostalgia_poster', 'Nostalgia', 'KONAMI', 'nostalgia_poster.jpg'),
    ('nostalgia_op2_poster', 'Nostalgia Op.2', 'KONAMI', 'nostalgia_op2_poster.jpg'),
    ('nostalgia_forte_poster', 'Nostalgia FORTE', 'KONAMI', 'nostalgia_forte_poster.jpg'),
    ('sound_voltex_exceed_gear_poster', 'SOUND VOLTEX EXCEED GEAR', 'KONAMI', 'sound_voltex_exceed_gear_poster.jpg'),
    ('sound_voltex_vivid_wave_poster', 'SOUND VOLTEX VIVID WAVE', 'KONAMI', 'sound_voltex_vivid_wave_poster.jpg'),
    ('taiko_drum_n_fun_poster', "Taiko no Tatsujin: Drum 'n' Fun!", 'Bandai Namco Entertainment', 'taiko_drum_n_fun_poster.jpg'),
    ('wacca_s_poster', 'WACCA S', 'Marvelous / HARDCORE TANO*C', 'wacca_s_poster.jpg'),
    ('wacca_reverse_poster', 'WACCA Reverse', 'Marvelous / HARDCORE TANO*C', 'wacca_reverse_poster.jpg'),
    ('wacca_lily_poster', 'WACCA Lily', 'Marvelous / HARDCORE TANO*C', 'wacca_lily_poster.jpg'),
    ('wacca_lily_r_poster', 'WACCA Lily R', 'Marvelous / HARDCORE TANO*C', 'wacca_lily_r_poster.jpg'),
    ('jubeat_festo_poster', 'jubeat festo', 'KONAMI', 'jubeat_festo_poster.jpg'),
)
WIDTH = 1.0
HEIGHT = 4096.0 / 2979.0
ITEM_HEIGHT = 15.0
ITEM_WIDTH = ITEM_HEIGHT / HEIGHT
TEXTURE_WIDTH = 512
TEXTURE_HEIGHT = 704


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def contact_sheet(previews: list[tuple[str, Image.Image]]) -> None:
    # A review-only montage; these thumbnails never replace the source artwork.
    columns, cell_w, cell_h, margin = 4, 264, 404, 18
    rows = math.ceil(len(previews) / columns)
    sheet = Image.new('RGB', (columns * cell_w + margin * 2, rows * cell_h + margin * 2 + 38), '#171b24')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    heading = ImageFont.load_default(size=22)
    draw.text((margin, margin), 'ARCADE POSTERS - same size as WACCA', fill='#ffffff', font=heading)
    for index, (title, poster) in enumerate(previews):
        x = margin + (index % columns) * cell_w
        y = margin + 42 + (index // columns) * cell_h
        thumb = poster.copy()
        thumb.thumbnail((240, 330), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y))
        words = title.split()
        lines, current = [], ''
        for word in words:
            candidate = (current + ' ' + word).strip()
            if draw.textlength(candidate, font=font) > cell_w - 16 and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        for line_index, line in enumerate(lines):
            draw.text((x + (cell_w - draw.textlength(line, font=font)) / 2, y + 342 + line_index * 19),
                      line, fill='#eeeeee', font=font)
    sheet.save(ART / 'contact-sheet.jpg', quality=92)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path, help='Directory containing the eleven original attachment filenames.')
    args = parser.parse_args()
    (ART / 'sources').mkdir(parents=True, exist_ok=True)
    template = json.loads((ASSETS / 'models/item/wacca_poster.json').read_text(encoding='utf-8'))
    entries, previews = [], []
    for poster_id, title, author, filename in POSTERS:
        source_path = ART / 'sources' / (poster_id + '.jpg')
        if args.source_directory:
            supplied = args.source_directory / filename
            if not supplied.is_file():
                raise SystemExit('Missing supplied image: ' + str(supplied))
            if source_path.exists() and sha256(source_path) != sha256(supplied):
                raise SystemExit('Refusing to replace immutable source: ' + str(source_path))
            if supplied.resolve() != source_path.resolve():
                shutil.copyfile(supplied, source_path)
            assert source_path.read_bytes() == supplied.read_bytes()
        if not source_path.is_file():
            raise SystemExit('Missing source; first run with --source-directory: ' + str(source_path))
        original_hash = sha256(source_path)
        with Image.open(source_path) as original:
            assert original.format == 'JPEG'
            source = original.convert('RGB')
        # Both canvas dimensions are multiples of 64, avoiding an atlas-wide
        # mip-level reduction from a sprite with poorly divisible dimensions.
        canvas_size = (TEXTURE_WIDTH, TEXTURE_HEIGHT)
        scale = TEXTURE_WIDTH / source.width
        assert scale <= 1, 'Do not upscale supplied prints'
        fitted_size = (TEXTURE_WIDTH, round(source.height * scale))
        fitted = source.resize(fitted_size, Image.Resampling.LANCZOS)
        assert canvas_size[1] >= fitted.height, 'Artwork must fit without cropping'
        top = (canvas_size[1] - fitted.height) // 2
        bottom = canvas_size[1] - fitted.height - top
        canvas = Image.new('RGB', canvas_size, '#000000')
        canvas.paste(fitted, (0, top))
        texture_path = ASSETS / 'textures/painting' / (poster_id + '.png')
        item_texture_path = ASSETS / 'textures/item' / (poster_id + '.png')
        texture_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(texture_path)
        shutil.copyfile(texture_path, item_texture_path)
        model = copy.deepcopy(template)
        model['textures'] = {'poster': f'japanesearcades:item/{poster_id}', 'particle': f'japanesearcades:item/{poster_id}'}
        model['elements'][0]['name'] = title + ' poster print'
        model_path = ASSETS / 'models/item' / (poster_id + '.json')
        write_json(model_path, model)
        write_json(DATA / 'painting_variant' / (poster_id + '.json'),
                   {'width': 1, 'height': 2, 'asset_id': f'japanesearcades:{poster_id}'})

        # Audit exported files, including decoded pixels and actual model faces.
        output = Image.open(texture_path).convert('RGB')
        assert ImageChops.difference(output.crop((0, top, fitted.width, top + fitted.height)), fitted).getbbox() is None
        assert ImageChops.difference(output, canvas).getbbox() is None
        assert all(dimension % 16 == 0 for dimension in output.size), 'Must support four atlas mip levels'
        assert texture_path.read_bytes() == item_texture_path.read_bytes()
        assert sha256(source_path) == original_hash
        exported = json.loads(model_path.read_text(encoding='utf-8'))
        element = exported['elements'][0]
        face_count = sum(len(element['faces']) for element in exported['elements'])
        item_size = [element['to'][i] - element['from'][i] for i in range(3)]
        assert face_count == 6
        assert abs(item_size[0] - ITEM_WIDTH) < 1e-12 and item_size[1] == ITEM_HEIGHT
        assert exported['display'] == template['display']
        entries.append({
            'id': poster_id, 'title': title, 'author': author,
            'source': {'file': str(source_path.relative_to(ROOT)).replace('\\', '/'),
                       'attachment_filename': filename, 'sha256': original_hash,
                       'bytes': source_path.stat().st_size, 'dimensions': list(source.size)},
            'output': {'texture': f'japanesearcades:painting/{poster_id}',
                       'item_texture': f'japanesearcades:item/{poster_id}', 'sha256': sha256(texture_path),
                       'item_sha256': sha256(item_texture_path), 'dimensions': list(output.size)},
            'packing': {'operation': 'Uniform full-image downsample with centered black letterboxing',
                        'artwork_scale': scale, 'resampling': 'Pillow LANCZOS', 'scaled_dimensions': list(fitted_size),
                        'offset': [0, top], 'padding_left_top_right_bottom': [0, top, 0, bottom],
                        'artwork_height_rounding': 'Nearest whole pixel', 'supported_mip_levels': 6,
                        'raster_aspect_rounding_error_percent': abs(canvas_size[1] / canvas_size[0] / HEIGHT - 1) * 100},
            'geometry': {'visual_dimensions_blocks': [WIDTH, HEIGHT], 'wall_support_grid_blocks': [1, 2],
                         'item_dimensions': item_size, 'item_faces': face_count,
                         'placed_faces': 12, 'placed_face_source': 'Shared vanilla PaintingRenderer: 1 x 2 cells, 6 quads per cell'},
            'checks': 'PASS: immutable source, full-image resize pixels, identical atlas copies, four atlas mip levels, exact WACCA item dimensions, 6 item faces',
        })
        previews.append((title, canvas))
    write_json(ART / 'manifest.json', {'poster_count': len(entries), 'posters': entries})
    contact_sheet(previews)
    print(json.dumps({'posters': len(entries), 'texture_dimensions': [TEXTURE_WIDTH, TEXTURE_HEIGHT],
                      'visual_dimensions_blocks': [WIDTH, HEIGHT], 'item_face_count_each': 6,
                      'placed_face_count_each': 12, 'checks': 'PASS'}, indent=2))


if __name__ == '__main__':
    main()
