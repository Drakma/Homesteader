"""The garage / workshop pack's palette (tools/garage_models.py builds the pieces, tools/make_garage_assets.py lists and exports them): the living pack's wood plus painted steel."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitchen_lib as K  # noqa: E402
import living_lib as LL  # noqa: E402
from garage_colors import PAINT  # noqa: E402


class GaragePalette(LL.Palette):
    """`main` is the colour that varies: painted steel (paint) or wood. Fixed: bare steel, rubber, a bench top of oak planks, black handles."""

    def _main(self, kind, key):
        if kind == 'paint':
            rgb = [c for k, _, c in PAINT[self.style] if k == key][0]
            return K.material('Paint_%s_%s' % (self.style, key), rgb, 0.42, 0.25)
        return LL.Palette._main(self, kind, key)

    def __init__(self, style, kind, key):
        LL.Palette.__init__(self, style, kind, key)
        mat = K.material
        self.steel = mat('RawSteel', (0.62, 0.64, 0.66), 0.38, 1.0)
        self.rubber = mat('Rubber', (0.04, 0.04, 0.045), 0.9)
        self.top = self._wood('oak')
        self.handle = self.brass if self.classic else self.blackmetal
        self.ink = self.main if kind == 'paint' else self.frame
