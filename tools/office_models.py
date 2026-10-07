"""
The home office pack's models (tools/living_lib.py has the palettes, tools/make_office_assets.py lists and exports them). Each function takes a living_lib Palette P.
Metres, centred on x and y, bottom at z = 0, FRONT = -Y (a desk's user sits at -y). A WALL piece is built with its back at y = +d / 2 and slid back so its back is the plane y = 0.
CLASSIC: turned legs, leather-topped desks, raised-panel drawers, brass. MODERN: slab tops, slim steel legs, black metal, mesh and shell chairs.
"""
from bathroom_models import _door
from bedroom_models import _drawer, _knob
from kitchen_lib import Mesh, material
from living_models import button, prism_x, soft, tapered_leg, turned_leg


def _pedestal(M, P, x0, x1, y0, y1, z0, z1, n):
    """A drawer pedestal: a carcass with n drawer fronts."""
    M.box(x0, x1, y0, y1, z0, z1, P.main, r=0.003, seg=1)
    h = (z1 - z0 - 0.03 - 0.008 * n) / n
    for k in range(n):
        za = z0 + 0.015 + k * (h + 0.008)
        _drawer(M, P, x0 + 0.012, x1 - 0.012, y0, za, za + h)


def office_desk(P):
    """A writing desk with a drawer pedestal, 1.50 x 0.70 x 0.76 m."""
    M = Mesh('office_office_desk')
    w, d, h = 1.50, 0.70, 0.76
    yf = -d / 2
    if P.classic:
        for sx in (-1, 1):
            turned_leg(M, sx * (w / 2 - 0.05), yf + 0.05, h - 0.04, P.main, r=0.036)
            turned_leg(M, sx * (w / 2 - 0.05), d / 2 - 0.05, h - 0.04, P.main, r=0.036)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.04, h, P.main, r=0.006, seg=2)
        leather = material('DeskLeather', (0.10, 0.18, 0.12), 0.7)
        M.box(-w / 2 + 0.06, w / 2 - 0.06, yf + 0.06, d / 2 - 0.06, h, h + 0.004, leather)
        _pedestal(M, P, w / 2 - 0.46, w / 2 - 0.04, yf + 0.03, d / 2 - 0.03, 0.10, h - 0.04, 3)
        M.box(-w / 2 + 0.05, w / 2 - 0.50, yf + 0.04, yf + 0.07, h - 0.12, h - 0.04, P.main)
    else:
        for sx in (-1, 1):
            M.box(sx * (w / 2 - 0.05) - 0.02, sx * (w / 2 - 0.05) + 0.02, yf + 0.05, d / 2 - 0.05, 0.0, h - 0.04, P.metal)
            M.box(sx * (w / 2 - 0.05) - 0.05, sx * (w / 2 - 0.05) + 0.05, yf + 0.03, yf + 0.07, 0.0, 0.02, P.metal)
            M.box(sx * (w / 2 - 0.05) - 0.05, sx * (w / 2 - 0.05) + 0.05, d / 2 - 0.07, d / 2 - 0.03, 0.0, 0.02, P.metal)
        M.box(-w / 2, w / 2, yf, d / 2, h - 0.04, h, P.main, r=0.004, seg=2)
        _pedestal(M, P, w / 2 - 0.50, w / 2 - 0.10, yf + 0.04, d / 2 - 0.04, 0.30, h - 0.04, 2)
    return M


def executive_desk(P):
    """An executive desk with two drawer pedestals and a modesty panel, 1.80 x 0.90 x 0.78 m."""
    M = Mesh('office_executive_desk')
    w, d, h = 1.80, 0.90, 0.78
    yf = -d / 2
    base = 0.08 if P.classic else 0.12
    pw = 0.52
    for sx in (-1, 1):
        x0, x1 = (-w / 2 + 0.03, -w / 2 + 0.03 + pw) if sx < 0 else (w / 2 - 0.03 - pw, w / 2 - 0.03)
        if P.classic:
            M.box(x0, x1, yf + 0.04, d / 2 - 0.04, 0.0, base, P.main)
        else:
            for ax in (x0 + 0.05, x1 - 0.05):
                for ay in (yf + 0.08, d / 2 - 0.08):
                    tapered_leg(M, ax, ay, base, P.metal, r=0.016)
        _pedestal(M, P, x0, x1, yf + 0.04, d / 2 - 0.04, base, h - 0.06, 3)
    M.box(-w / 2 + pw + 0.03, w / 2 - pw - 0.03, d / 2 - 0.06, d / 2 - 0.03, 0.12, h - 0.06, P.main)       # the modesty panel
    M.box(-w / 2, w / 2, yf, d / 2, h - 0.06, h, P.main, r=0.008 if P.classic else 0.004, seg=2)
    if P.classic:
        leather = material('DeskLeather', (0.10, 0.18, 0.12), 0.7)
        M.box(-w / 2 + 0.08, w / 2 - 0.08, yf + 0.08, d / 2 - 0.08, h, h + 0.004, leather)
        M.box(-0.35, 0.35, yf + 0.04, yf + 0.07, h - 0.14, h - 0.06, P.main)
    return M


def credenza(P):
    """A credenza with drawers and doors, 1.50 x 0.50 x 0.76 m."""
    M = Mesh('office_credenza')
    w, d, h = 1.50, 0.50, 0.76
    yf = -d / 2
    if P.classic:
        M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, 0.08, P.main)
        z0 = 0.08
    else:
        for sx in (-1, 1):
            tapered_leg(M, sx * (w / 2 - 0.06), yf + 0.06, 0.14, P.metal, r=0.018, splay=(sx * 0.02, -0.01))
            tapered_leg(M, sx * (w / 2 - 0.06), d / 2 - 0.06, 0.14, P.metal, r=0.018, splay=(sx * 0.02, 0.01))
        z0 = 0.14
    M.box(-w / 2, w / 2, yf, d / 2, z0, h - 0.03, P.main, r=0.003, seg=1)
    M.box(-w / 2 - (0.015 if P.classic else 0.0), w / 2 + (0.015 if P.classic else 0.0), yf - (0.02 if P.classic else 0.0), d / 2 + 0.005, h - 0.03, h, P.main, r=0.006, seg=2)
    third = (w - 0.04) / 3
    for k in range(3):
        a = -w / 2 + 0.02 + k * third
        if k == 1:
            for j in range(2):
                z = z0 + 0.02 + j * 0.2
                _drawer(M, P, a + 0.004, a + third - 0.004, yf, z, z + 0.19)
            _drawer(M, P, a + 0.004, a + third - 0.004, yf, z0 + 0.42, h - 0.05)
        else:
            _door(M, a + 0.004, a + third - 0.004, yf, z0 + 0.02, h - 0.05, P.main, P.classic)
            _knob(M, P, (a + third - 0.05) if k == 0 else (a + 0.05), yf - (0.026 if P.classic else 0.02), 0.40)
    return M


def filing_cabinet(P):
    """A two-drawer filing cabinet, 0.46 x 0.62 x 0.72 m."""
    M = Mesh('office_filing_cabinet')
    w, d, h = 0.46, 0.62, 0.72
    yf = -d / 2
    z0 = 0.04
    M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, z0, P.dark)
    M.box(-w / 2, w / 2, yf, d / 2, z0, h, P.main, r=0.004, seg=1)
    for z in (z0 + 0.02, z0 + 0.35):
        _drawer(M, P, -w / 2 + 0.014, w / 2 - 0.014, yf, z, z + 0.32, k=False)
        M.box(-0.06, 0.06, yf - 0.03, yf - 0.02, z + 0.24, z + 0.265, P.metal)
        M.box(-0.045, 0.045, yf - 0.021, yf - 0.019, z + 0.17, z + 0.20, P.paper)
    return M


def lateral_file(P):
    """A wide lateral filing cabinet with two drawers, 0.90 x 0.45 x 0.70 m."""
    M = Mesh('office_lateral_file')
    w, d, h = 0.90, 0.45, 0.70
    yf = -d / 2
    z0 = 0.04
    M.box(-w / 2 + 0.02, w / 2 - 0.02, yf + 0.03, d / 2 - 0.02, 0.0, z0, P.dark)
    M.box(-w / 2, w / 2, yf, d / 2, z0, h, P.main, r=0.004, seg=1)
    for z in (z0 + 0.02, z0 + 0.34):
        _drawer(M, P, -w / 2 + 0.014, w / 2 - 0.014, yf, z, z + 0.30, k=False)
        M.box(-0.10, 0.10, yf - 0.03, yf - 0.02, z + 0.22, z + 0.245, P.metal)
    return M


def whiteboard_wall(P):
    """A framed whiteboard with a marker tray, 1.20 x 0.05 x 0.90 m. A wall item."""
    M = Mesh('office_whiteboard_wall')
    w, h, d = 1.20, 0.90, 0.05
    yb = d / 2
    M.box(-w / 2, w / 2, yb - d, yb, 0.0, h, P.main, r=0.004, seg=1)
    board = material('WhiteboardWhite', (0.96, 0.96, 0.95), 0.25)
    M.box(-w / 2 + 0.03, w / 2 - 0.03, yb - d - 0.003, yb - d + 0.012, 0.06, h - 0.03, board)
    M.box(-0.30, 0.30, yb - d - 0.05, yb - d, 0.02, 0.05, P.main)
    for k, c in enumerate(((0.1, 0.1, 0.1), (0.7, 0.1, 0.1), (0.1, 0.2, 0.6))):
        M.box(-0.12 + 0.10 * k, -0.04 + 0.10 * k, yb - d - 0.035, yb - d - 0.01, 0.055, 0.075, material('Marker%d' % k, c, 0.5))
    M.shift(0, -d / 2, 0)
    return M


def corkboard_wall(P):
    """A framed cork board with pinned notes, 1.00 x 0.04 x 0.70 m. A wall item."""
    M = Mesh('office_corkboard_wall')
    w, h, d = 1.00, 0.70, 0.04
    yb = d / 2
    M.box(-w / 2, w / 2, yb - d, yb, 0.0, h, P.main, r=0.004, seg=1)
    cork = material('Cork', (0.66, 0.48, 0.28), 0.95)
    M.box(-w / 2 + 0.035, w / 2 - 0.035, yb - d - 0.003, yb - d + 0.012, 0.035, h - 0.035, cork)
    for k, (x, z, c) in enumerate(((-0.28, 0.45, (0.95, 0.9, 0.6)), (0.05, 0.38, (0.95, 0.95, 0.92)), (0.30, 0.50, (0.6, 0.8, 0.9)), (-0.05, 0.22, (0.95, 0.75, 0.8)))):
        M.box(x - 0.07, x + 0.07, yb - d - 0.01, yb - d - 0.004, z - 0.06, z + 0.06, material('Note%d' % k, c, 0.9))
        M.cyl((x, yb - d - 0.01, z + 0.045), (x, yb - d - 0.02, z + 0.045), 0.007, P.metal, seg=6)
    M.shift(0, -d / 2, 0)
    return M


# ------------------------------------------------------------------ chairs

def office_chair(P):
    """A swivel office chair on a five-star base, 0.62 x 0.62 x 1.08 m."""
    M = Mesh('office_office_chair')
    for k in range(5):
        import math
        a = math.radians(72 * k)
        M.cyl((0.0, 0.0, 0.10), (0.29 * math.cos(a), 0.29 * math.sin(a), 0.045), 0.02, P.metal if P.classic else P.chrome, seg=6)
        M.cyl((0.29 * math.cos(a) - 0.0, 0.29 * math.sin(a), 0.03), (0.29 * math.cos(a), 0.29 * math.sin(a), 0.045), 0.026, P.black, seg=8)
    M.cyl((0, 0, 0.09), (0, 0, 0.42), 0.035, P.metal if P.classic else P.chrome, seg=10)
    soft(M, -0.26, 0.26, -0.26, 0.24, 0.42, 0.52, P.main, r=0.05)
    if P.classic:
        soft(M, -0.24, 0.24, 0.20, 0.30, 0.50, 1.04, P.main, r=0.06)
        for sx in (-1, 1):
            M.box(sx * 0.30 - 0.025, sx * 0.30 + 0.025, -0.16, 0.14, 0.64, 0.68, P.frame)
            M.cyl((sx * 0.30, -0.12, 0.52), (sx * 0.30, -0.12, 0.65), 0.016, P.frame, seg=6)
        for bz in (0.62, 0.78, 0.94):
            button(M, 0.0, 0.20, bz, P.frame)
    else:
        prism_x(M, [(0.18, 0.50), (0.28, 0.50), (0.34, 1.06), (0.22, 1.06)], -0.23, 0.23, P.main)
        for sx in (-1, 1):
            M.box(sx * 0.28 - 0.015, sx * 0.28 + 0.015, -0.12, 0.10, 0.62, 0.65, P.black)
            M.box(sx * 0.28 - 0.01, sx * 0.28 + 0.01, 0.0, 0.03, 0.52, 0.62, P.black)
    return M


def guest_chair(P):
    """An upholstered guest chair on wood legs, 0.56 x 0.56 x 0.90 m."""
    M = Mesh('office_guest_chair')
    for sx in (-1, 1):
        if P.classic:
            turned_leg(M, sx * 0.22, -0.21, 0.44, P.frame, r=0.03)
            turned_leg(M, sx * 0.22, 0.22, 0.90, P.frame, r=0.03)
        else:
            tapered_leg(M, sx * 0.21, -0.20, 0.44, P.metal, r=0.017, splay=(sx * 0.02, -0.02))
            tapered_leg(M, sx * 0.21, 0.20, 0.44, P.metal, r=0.017, splay=(sx * 0.02, 0.02))
    soft(M, -0.25, 0.25, -0.25, 0.23, 0.42, 0.52, P.main, r=0.05)
    soft(M, -0.23, 0.23, 0.18, 0.25, 0.54, 0.88, P.main, r=0.05)
    if P.classic:
        for sx in (-1, 1):
            M.box(sx * 0.26 - 0.02, sx * 0.26 + 0.02, -0.20, 0.18, 0.58, 0.62, P.frame)
            M.cyl((sx * 0.26, -0.18, 0.52), (sx * 0.26, -0.18, 0.59), 0.014, P.frame, seg=6)
    return M
