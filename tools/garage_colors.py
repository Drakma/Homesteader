"""The colours of the garage / workshop pack (no Blender needed). Painted steel for the cabinets and tools, wood for benches and racks."""
from living_colors import WOODS

# painted steel: style -> [(key, label, rgb)]
PAINT = {
    'classic': [('red', 'Red', (0.60, 0.08, 0.07)), ('green', 'Forest Green', (0.10, 0.30, 0.18)), ('navy', 'Navy', (0.10, 0.16, 0.32)), ('black', 'Black', (0.05, 0.05, 0.055))],
    'modern': [('grey', 'Steel Grey', (0.45, 0.47, 0.50)), ('black', 'Matte Black', (0.05, 0.05, 0.055)), ('orange', 'Safety Orange', (0.85, 0.36, 0.06)), ('white', 'White', (0.92, 0.92, 0.92))],
}


def colors(style, kind):
    """[(key, label)] of a style's colours for a kind of piece: paint (steel) or wood."""
    if kind == 'paint':
        return [(k, l) for k, l, _ in PAINT[style]]
    return list(WOODS[style])
