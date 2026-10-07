"""The colours of the bathroom pack (no Blender needed: the build script, the icon step and the library all read them)."""
from living_colors import FABRICS, WOODS, colors as _living_colors  # noqa: F401

# glazed fixtures (toilets, sinks, tubs, the shower tray): style -> [(key, label, rgb)]
PORCELAIN = {
    'classic': [('white', 'White', (0.94, 0.94, 0.92)), ('bone', 'Bone', (0.86, 0.80, 0.66)), ('sage', 'Sage Green', (0.58, 0.68, 0.55)), ('black', 'Black', (0.04, 0.04, 0.045))],
    'modern': [('white', 'White', (0.95, 0.95, 0.95)), ('black', 'Matte Black', (0.05, 0.05, 0.055)), ('grey', 'Stone Grey', (0.52, 0.53, 0.54)), ('navy', 'Navy', (0.10, 0.16, 0.30))],
}
# metal accessories: style -> [(key, label, rgb, rough, metal)]
METALS = {
    'classic': [('chrome', 'Polished Chrome', (0.82, 0.83, 0.85), 0.14, 1.0), ('brass', 'Antique Brass', (0.70, 0.52, 0.22), 0.34, 1.0), ('bronze', 'Oiled Bronze', (0.20, 0.13, 0.08), 0.42, 0.8), ('black', 'Black Iron', (0.04, 0.04, 0.045), 0.45, 0.6)],
    'modern': [('chrome', 'Chrome', (0.82, 0.83, 0.85), 0.14, 1.0), ('nickel', 'Brushed Nickel', (0.62, 0.63, 0.64), 0.36, 1.0), ('black', 'Matte Black', (0.05, 0.05, 0.055), 0.62, 0.3), ('white', 'White', (0.94, 0.94, 0.94), 0.50, 0.0)],
}


def colors(style, kind):
    """[(key, label)] of a style's colours for a kind of piece: porcelain, metal, fabric or wood."""
    if kind == 'porcelain':
        return [(k, l) for k, l, _ in PORCELAIN[style]]
    if kind == 'metal':
        return [(k, l) for k, l, *_ in METALS[style]]
    return _living_colors(style, kind)
