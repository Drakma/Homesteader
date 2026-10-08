"""
The icons of the phone shop's category tiles (Resources/StoreCategoryIcons/<slug>.png, 128 x 128 RGBA), made from Gemini contact sheets.

    python tools/make_store_category_icons.py prompt 1          (prints the Gemini prompt of sheet 1: 4 x 4 objects on dark slate #2b3442)
    python tools/make_store_category_icons.py crop 1 <sheet.png>   (cuts the sheet into one icon per category, in reading order)
    python tools/make_store_category_icons.py list             (every category and its sheet position)

The sheet is generated with the gemini_generate tool (docs/ITEM_ICON_STYLE_GUIDE.md: low-poly, isometric 3/4, dark slate background, no text). Cropping finds each object as a blob
on the slate, keys the slate out, fits the object into 104 px in a 128 px canvas (12 px margin) and writes it under the category's slug. A shop tile with no icon file shows
an item of its category instead (PhoneController.TileIcon). The categories come from tools/store_categories.py.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'Homesteader', 'Assets', 'Resources', 'StoreCategoryIcons')

# sheet -> [(category label, what to draw)] in reading order (row 1 left to right, then row 2 ...)
SHEETS = {
    1: [('Lumber & Framing', 'a neat stack of lumber boards and a 2x4 stud'), ('Concrete & Masonry', 'a stack of red bricks next to a bag of cement'),
        ('Roofing', 'a corner section of a shingled roof'), ('Siding & Cladding', 'a few vinyl siding panels leaning together'),
        ('Plumbing & Pipe', 'white PVC pipes with an elbow fitting'), ('Insulation & Drywall', 'a roll of pink fiberglass insulation next to a sheet of drywall'),
        ('Fasteners & Hardware', 'a pile of nails, screws and a bolt'), ('Flooring', 'wood floor planks with a floor tile'),
        ('Fencing & Outdoor', 'a short wooden fence section with a gate'), ('Dirt, Gravel & Stone', 'a pile of gravel and stones'),
        ('Doors & Windows', 'a wooden door next to a framed window'), ('Trim & Flashing', 'a trim board and a roll of metal flashing'),
        ('Boxes & Packaging', 'a stack of cardboard boxes'), ('Electrical Wire', 'a spool of electrical wire'),
        ('Shelving', 'a wall shelf with a few items'), ('Building Supplies', 'a yellow hard hat on top of rolled blueprints')],
    2: [('Chimneys', 'a brick chimney stack with a flue cap'), ('Structures & Kits', 'a small log cabin'),
        ('Garden & Farm Tools', 'a shovel and a hoe crossed'), ('Logging & Saws', 'an axe and a chainsaw'),
        ('Power Tools', 'a cordless drill'), ('Hand Tools', 'a claw hammer and an adjustable wrench'),
        ('Farm Materials', 'a coil of rope and a bundle of wool'), ('Hay, Straw & Bedding', 'a square hay bale'),
        ('Water', 'a blue water tank with a water drop'), ('Fuel', 'a red jerry can'),
        ('Waste', 'a green septic tank'), ('Farming', 'a seed packet with a green sprout'),
        ('Ranching', 'a feed bag and a feed bucket'), ('Logging', 'a stack of cut logs'),
        ('Vehicles', 'a pickup truck'), ('Trailers', 'a utility trailer')],
    3: [('Trailer Parts', 'a trailer hitch ball and coupler'), ('Trailer Repair', 'a wrench beside a trailer wheel'),
        ('Secure Towing', 'a tow chain and a padlock'), ('Telecom', 'a satellite dish'),
        ('Lighting', 'a pendant light with a glowing bulb'), ('Solar Panels', 'a solar panel'),
        ('Solar Mounts', 'a ground-mounted solar rack'), ('Batteries', 'a battery bank of two batteries'),
        ('Controllers & Inverters', 'a solar charge controller box with a small display'), ('Generators', 'a portable generator'),
        ('Breakers & Wiring', 'a breaker box with its door open'), ('Wind & Power Poles', 'a small wind turbine'),
        ('Appliances', 'a white refrigerator'), ('Bathroom', 'a toilet'),
        ('Bedroom', 'a bed with a pillow'), ('Decor', 'a potted plant beside a curtain')],
    4: [('Dining', 'a dining table with two chairs'), ('Garage', 'a workbench with a vise'),
        ('Kitchen', 'a stove with a pot on it'), ('Laundry', 'a washing machine with a laundry basket'),
        ('Living Room', 'a sofa'), ('Office', 'a desk with a chair'),
        ('Vegetables', 'a carrot, a tomato and a cabbage'), ('Fruit', 'a few apples'),
        ('Nuts', 'a small pile of pecans'), ('Baked Goods', 'a loaf of bread and a muffin'),
        ('Cooked Meat & Fish', 'a grilled steak on a plate'), ('Raw Meat & Fish', 'a raw steak and a fish fillet'),
        ('Dairy & Eggs', 'a milk bottle and a few eggs'), ('Flour & Grains', 'a flour sack and a sheaf of wheat'),
        ('Farm Crops', 'an ear of corn and a bundle of wheat'), ('Pantry Staples', 'a salt shaker and a sugar jar')],
    5: [('Jars & Bottles', 'a jar of jam and a bottle of oil')],
}


def slug(label):
    return re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')


def prompt(n):
    items = SHEETS[n]
    cols = 4 if len(items) > 1 else 1
    rows = (len(items) + cols - 1) // cols
    words = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen']
    lines = []
    for r in range(rows):
        row = items[r * cols:(r + 1) * cols]
        lines.append('row %d: ' % (r + 1) + '; '.join('(%d) %s' % (r * cols + i + 1, d) for i, (_, d) in enumerate(row)))
    grid = ('a clean %d columns by %d rows grid of %d separate objects, each object floating centered in its own equal cell with generous empty space around it, no overlap between cells'
            % (cols, rows, len(items))) if len(items) > 1 else 'a single object floating centered with generous empty space around it'
    return ('A 3D low-poly faceted render sheet of MODERN homestead store category icons: %s. Style: clean video game asset icon, low-poly 3D model with chunky simplified geometry '
            'and clearly visible flat polygon facets on every surface, soft studio key lighting from top-left, isometric 3/4 front view, no cast shadows, no pedestal. Background: '
            'solid uniform DARK SLATE (hex #2b3442) completely plain and flat, no gradient, no borders, no card frames, no grid lines, no text, no labels, no watermark. '
            'The %s objects in reading order (left to right, top to bottom): %s.' % (grid, words[len(items) - 1], ' '.join(lines)))


def crop(n, path):
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    items = SHEETS[n]
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    bg = np.median(np.concatenate([a[:6, :6].reshape(-1, 3), a[:6, -6:].reshape(-1, 3), a[-6:, :6].reshape(-1, 3), a[-6:, -6:].reshape(-1, 3)]), axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    fg = dist > 28
    fg = ndimage.binary_opening(fg, iterations=1)
    blob = ndimage.binary_dilation(fg, iterations=max(4, w // 90))
    lab, count = ndimage.label(blob)
    objs = ndimage.find_objects(lab)
    sizes = [(int((lab[o] == i + 1).sum()), i + 1, o) for i, o in enumerate(objs)]
    sizes.sort(reverse=True)
    keep = sizes[:len(items)]
    if len(keep) < len(items) or '--grid' in sys.argv:
        return crop_grid(n, im, a, dist, items)   # two objects ran together: cut the sheet into its equal cells instead
    # reading order: rows by the centre y (a row is within half an object's height), then x
    cells = []
    for _, idx, o in keep:
        cy = (o[0].start + o[0].stop) / 2
        cx = (o[1].start + o[1].stop) / 2
        cells.append((cy, cx, idx, o))
    cols = 4 if len(items) > 1 else 1
    cells.sort(key=lambda c: c[0])
    ordered = []
    for r in range(0, len(cells), cols):
        row = sorted(cells[r:r + cols], key=lambda c: c[1])
        ordered.extend(row)
    os.makedirs(OUT, exist_ok=True)
    for (label, _), (cy, cx, idx, o) in zip(items, ordered):
        # the soft alpha: how far each pixel is from the slate
        sub = (lab[o] == idx) | ndimage.binary_dilation(lab[o] == idx, iterations=3)
        d = dist[o]
        alpha = np.clip((d - 14) / 26.0, 0.0, 1.0) * sub
        rgb = np.asarray(im)[o]
        rgba = np.dstack([rgb, (alpha * 255).astype(np.uint8)])
        icon = Image.fromarray(rgba.astype(np.uint8), 'RGBA')
        box = icon.getbbox()
        if box:
            icon = icon.crop(box)
        icon.thumbnail((104, 104), Image.LANCZOS)
        canvas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        canvas.paste(icon, ((128 - icon.width) // 2, (128 - icon.height) // 2), icon)
        canvas.save(os.path.join(OUT, slug(label) + '.png'))
        print('icon', slug(label), icon.size)


def crop_grid(n, im, a, dist, items):
    """The sheet cut into 4 x 4 equal cells (the objects sit in the middle of their cells): each cell's foreground, fitted into the icon canvas."""
    import numpy as np
    from PIL import Image
    h, w, _ = a.shape
    cols = 4 if len(items) > 1 else 1
    rows = (len(items) + cols - 1) // cols
    os.makedirs(OUT, exist_ok=True)
    for k, (label, _) in enumerate(items):
        r, c = divmod(k, cols)
        y0, y1, x0, x1 = int(r * h / rows), int((r + 1) * h / rows), int(c * w / cols), int((c + 1) * w / cols)
        d = dist[y0:y1, x0:x1]
        alpha = np.clip((d - 14) / 26.0, 0.0, 1.0)
        rgb = np.asarray(im)[y0:y1, x0:x1]
        icon = Image.fromarray(np.dstack([rgb, (alpha * 255).astype(np.uint8)]).astype(np.uint8), 'RGBA')
        box = icon.getbbox()
        if box:
            icon = icon.crop(box)
        icon.thumbnail((104, 104), Image.LANCZOS)
        canvas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        canvas.paste(icon, ((128 - icon.width) // 2, (128 - icon.height) // 2), icon)
        canvas.save(os.path.join(OUT, slug(label) + '.png'))
        print('icon (grid)', slug(label), icon.size)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    if cmd == 'prompt':
        print(prompt(int(sys.argv[2])))
    elif cmd == 'crop':
        crop(int(sys.argv[2]), sys.argv[3])
    else:
        for n, items in SHEETS.items():
            for i, (label, d) in enumerate(items):
                print(n, i + 1, label, '|', d)
