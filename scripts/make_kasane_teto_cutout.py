"""Rebuild the matching Teto standee without writing any Miku art assets.

The shared exporter preserves the PNG bytes and character proportions, adds the
same kraft silhouette and folded support, and bakes all sixteen yaw angles.
"""
from make_hatsune_miku_cutout import main


if __name__=='__main__':
    main(name='kasane_teto_cutout',display_title='Kasane Teto Cardboard Cutout',
         source_filename='teto-cutout-print.png',short_name='Teto',
         max_art_height=24.64449438202247)
