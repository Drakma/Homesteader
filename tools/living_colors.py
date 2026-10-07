"""The colours of the living room pack (no Blender needed: the build script, the icon step and the lib all read them)."""

# style -> [(key, label, rgb)]
FABRICS = {
    'classic': [('burgundy', 'Burgundy', (0.42, 0.09, 0.13)), ('forest', 'Forest Green', (0.10, 0.28, 0.18)), ('navy', 'Navy', (0.11, 0.17, 0.34)), ('camel', 'Camel Leather', (0.58, 0.40, 0.22))],
    'modern': [('charcoal', 'Charcoal', (0.20, 0.21, 0.23)), ('stone', 'Stone', (0.70, 0.69, 0.66)), ('teal', 'Teal', (0.09, 0.43, 0.46)), ('mustard', 'Mustard', (0.80, 0.59, 0.12))],
}
# wood: key -> (label, light, dark) ; white and black have no grain
WOOD_RGB = {
    'mahogany': ('Mahogany', (0.50, 0.22, 0.12), (0.26, 0.09, 0.05)),
    'walnut': ('Walnut', (0.42, 0.28, 0.17), (0.24, 0.15, 0.09)),
    'cherry': ('Cherry', (0.62, 0.28, 0.16), (0.40, 0.15, 0.08)),
    'oak': ('Oak', (0.78, 0.60, 0.38), (0.60, 0.42, 0.23)),
    'birch': ('Birch', (0.90, 0.80, 0.62), (0.78, 0.64, 0.44)),
}
WOODS = {
    'classic': [('mahogany', 'Mahogany'), ('walnut', 'Walnut'), ('cherry', 'Cherry'), ('oak', 'Oak')],
    'modern': [('birch', 'Birch'), ('walnut', 'Walnut'), ('white', 'White'), ('black', 'Black')],
}


def colors(style, kind):
    """[(key, label)] of the colours of a style for a kind of piece (fabric / rug use the fabric colours, wood the wood colours)."""
    if kind in ('fabric', 'rug'):
        return [(k, l) for k, l, _ in FABRICS[style]]
    return list(WOODS[style])
