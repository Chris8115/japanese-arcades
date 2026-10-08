"""Prepare framed arcade poster assets from supplied and restored prints.

First import: python scripts/make_arcade_posters.py --source-directory PATH
Rebuild:       python scripts/make_arcade_posters.py

The original sources remain byte-identical. Runtime copies retain the full image
with a small uniform downsample and narrow black bars above and below so every
print has the same physical dimensions as the original WACCA poster. Texture
dimensions support the default four atlas mip levels. Separate model geometry
adds visible black frame strips around the full print, without painting over it.
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
ART_SCALE = .91
EXPANSION = (
    ('project_diva_arcade_poster', 'Project DIVA Arcade', 'SEGA', 'project_diva_arcade_poster.webp', False),
    ('chunithm_luminous_plus_poster', 'CHUNITHM Luminous PLUS', 'SEGA', 'chunithm_luminous_plus_poster.webp', True),
    ('sound_voltex_exceed_gear_ensemble_poster', 'SOUND VOLTEX EXCEED GEAR Ensemble', 'KONAMI', 'sound_voltex_exceed_gear_ensemble_poster.webp', True),
    ('maimai_splash_poster', 'maimai Splash', 'SEGA', 'maimai_splash_poster.webp', True),
    ('sega_cygames_poster', 'SEGA Rhythm Games × Cygames', 'SEGA / Cygames', 'sega_cygames_poster.webp', True),
    ('maimai_universe_poster', 'maimai UNiVERSE', 'SEGA', 'maimai_universe_poster.webp', True),
    ('chunithm_paradise_poster', 'CHUNITHM PARADISE', 'SEGA', 'chunithm_paradise_poster.webp', True),
    ('we_love_music_game_poster', 'We Love Music Game', 'SEGA', 'we_love_music_game_poster.webp', True),
)


def framed_item(template, poster_id, title):
    """Black front/back rings meet the print without overlapping coplanar faces."""
    model = copy.deepcopy(template)
    model['textures'] = {'poster': f'japanesearcades:item/{poster_id}',
                         'particle': f'japanesearcades:item/{poster_id}',
                         'frame': 'japanesearcades:item/poster_frame_black'}
    original = template['elements'][0]
    x0, y0, z0 = original['from']
    x1, y1, z1 = original['to']
    dx, dy = (x1-x0)*(1-ART_SCALE)/2, (y1-y0)*(1-ART_SCALE)/2
    ix0, ix1, iy0, iy1 = x0+dx, x1-dx, y0+dy, y1-dy
    def face(texture):
        return {'texture': texture, 'uv': [0, 0, 16, 16]}
    model['elements'] = [{'name': 'Black outer edges', 'from': [x0,y0,z0], 'to': [x1,y1,z1],
                          'faces': {d: face('#frame') for d in ('east','west','up','down')}}]
    for name, bounds in (('Left', (x0,y0,ix0,y1)), ('Right', (ix1,y0,x1,y1)),
                         ('Bottom', (ix0,y0,ix1,iy0)), ('Top', (ix0,iy1,ix1,y1)),
                         (title+' print', (ix0,iy0,ix1,iy1))):
        a,b,c,d = bounds
        texture = '#poster' if name.endswith(' print') else '#frame'
        model['elements'].append({'name': name, 'from': [a,b,z0], 'to': [c,d,z1],
                                  'faces': {f: face(texture) for f in ('north','south')}})
    return model


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
        framed = Image.new('RGB', poster.size, '#000000')
        inset = poster.resize(tuple(round(d*ART_SCALE) for d in poster.size), Image.Resampling.LANCZOS)
        framed.paste(inset, ((poster.width-inset.width)//2, (poster.height-inset.height)//2))
        thumb = framed
        thumb.thumbnail((240, 330), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y))
        words = title.replace('×', 'x').split()
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
    parser.add_argument('--source-directory', type=Path, help='Directory containing original attachment filenames for first import.')
    args = parser.parse_args()
    (ART / 'sources').mkdir(parents=True, exist_ok=True)
    template = json.loads((ASSETS / 'models/item/wacca_poster.json').read_text(encoding='utf-8'))
    Image.new('RGB', (16,16), '#000000').save(ASSETS / 'textures/item/poster_frame_black.png')
    entries, previews = [], []
    prints = [(*p, False, False) for p in POSTERS] + [(*p, True) for p in EXPANSION]
    for poster_id, title, author, filename, restored, expansion in prints:
        source_path = ART / ('expansion/sources' if expansion else 'sources') / (poster_id + ('.webp' if expansion else '.jpg'))
        source_path.parent.mkdir(parents=True, exist_ok=True)
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
        artwork_path = ART / 'expansion/cleaned' / (poster_id+'.png') if restored else source_path
        with Image.open(source_path) as original:
            original_size = original.size
        with Image.open(artwork_path) as artwork:
            source = artwork.convert('RGB')
        # Both canvas dimensions are multiples of 64, avoiding an atlas-wide
        # mip-level reduction from a sprite with poorly divisible dimensions.
        canvas_size = (TEXTURE_WIDTH, TEXTURE_HEIGHT)
        scale = min(TEXTURE_WIDTH / source.width, TEXTURE_HEIGHT / source.height)
        assert scale <= 1, 'Do not upscale supplied prints'
        fitted_size = (round(source.width * scale), round(source.height * scale))
        fitted = source.resize(fitted_size, Image.Resampling.LANCZOS)
        assert canvas_size[1] >= fitted.height, 'Artwork must fit without cropping'
        top = (canvas_size[1] - fitted.height) // 2
        bottom = canvas_size[1] - fitted.height - top
        left = (canvas_size[0] - fitted.width) // 2
        right = canvas_size[0] - fitted.width - left
        canvas = Image.new('RGB', canvas_size, '#000000')
        canvas.paste(fitted, (left, top))
        texture_path = ASSETS / 'textures/painting' / (poster_id + '.png')
        item_texture_path = ASSETS / 'textures/item' / (poster_id + '.png')
        texture_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(texture_path)
        shutil.copyfile(texture_path, item_texture_path)
        model = framed_item(template, poster_id, title)
        model_path = ASSETS / 'models/item' / (poster_id + '.json')
        write_json(model_path, model)
        write_json(DATA / 'painting_variant' / (poster_id + '.json'),
                   {'width': 1, 'height': 2, 'asset_id': f'japanesearcades:{poster_id}'})

        # Audit exported files, including decoded pixels and actual model faces.
        output = Image.open(texture_path).convert('RGB')
        assert ImageChops.difference(output.crop((left, top, left+fitted.width, top+fitted.height)), fitted).getbbox() is None
        assert ImageChops.difference(output, canvas).getbbox() is None
        assert all(dimension % 16 == 0 for dimension in output.size), 'Must support four atlas mip levels'
        assert texture_path.read_bytes() == item_texture_path.read_bytes()
        assert sha256(source_path) == original_hash
        exported = json.loads(model_path.read_text(encoding='utf-8'))
        element = exported['elements'][0]
        face_count = sum(len(element['faces']) for element in exported['elements'])
        item_size = [element['to'][i] - element['from'][i] for i in range(3)]
        assert face_count == 14
        assert abs(item_size[0] - ITEM_WIDTH) < 1e-12 and item_size[1] == ITEM_HEIGHT
        assert exported['display'] == template['display']
        front_rects = [(e['from'][0], e['from'][1], e['to'][0], e['to'][1])
                       for e in exported['elements'] if 'south' in e['faces']]
        assert abs(sum((c-a)*(d-b) for a,b,c,d in front_rects)-ITEM_WIDTH*ITEM_HEIGHT) < 1e-10
        for i, (a,b,c,d) in enumerate(front_rects):
            for e,f,g,h in front_rects[i+1:]:
                assert max(0, min(c,g)-max(a,e))*max(0, min(d,h)-max(b,f)) < 1e-12
        entries.append({
            'id': poster_id, 'title': title, 'author': author,
            'source': {'file': str(source_path.relative_to(ROOT)).replace('\\', '/'),
                       'attachment_filename': filename, 'sha256': original_hash,
                       'bytes': source_path.stat().st_size, 'dimensions': list(original_size)},
            'artwork': {'file': artwork_path.relative_to(ROOT).as_posix(), 'sha256': sha256(artwork_path),
                        'dimensions': list(source.size), 'restored_with_imagegen': restored},
            'output': {'texture': f'japanesearcades:painting/{poster_id}',
                       'item_texture': f'japanesearcades:item/{poster_id}', 'sha256': sha256(texture_path),
                       'item_sha256': sha256(item_texture_path), 'dimensions': list(output.size)},
            'packing': {'operation': 'Uniform full-image downsample with centered black letterboxing',
                        'artwork_scale': scale, 'resampling': 'Pillow LANCZOS', 'scaled_dimensions': list(fitted_size),
                        'offset': [left, top], 'padding_left_top_right_bottom': [left, top, right, bottom],
                        'artwork_height_rounding': 'Nearest whole pixel', 'supported_mip_levels': 6,
                        'raster_aspect_rounding_error_percent': abs(canvas_size[1] / canvas_size[0] / HEIGHT - 1) * 100},
            'geometry': {'visual_dimensions_blocks': [WIDTH, HEIGHT], 'wall_support_grid_blocks': [1, 2],
                         'item_dimensions': item_size, 'item_faces': face_count,
                         'art_scale': ART_SCALE, 'placed_faces': 10,
                         'placed_face_source': 'Black back + 4 outer edges + 4 front frame strips + inset art'},
            'checks': 'PASS: immutable source, full-image resize pixels, identical atlas copies, four atlas mip levels, exact WACCA outer dimensions, 14 item faces',
        })
        previews.append((title, canvas))
    write_json(ART / 'manifest.json', {'poster_count': len(entries), 'posters': entries})
    contact_sheet(previews)
    print(json.dumps({'posters': len(entries), 'texture_dimensions': [TEXTURE_WIDTH, TEXTURE_HEIGHT],
                      'visual_dimensions_blocks': [WIDTH, HEIGHT], 'item_face_count_each': 14,
                      'placed_face_count_each': 10, 'checks': 'PASS'}, indent=2))


if __name__ == '__main__':
    main()
