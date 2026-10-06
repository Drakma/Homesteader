"""
The rest of the building materials (weatherproofing, framing and beams, masonry mixes, interior finishing, fasteners and hardware, insulation, wire and
plumbing supplies), added to the ones of make_building_items.py. Same pipeline: headless Blender, procedural GLB, manifest, tags; run the icons afterwards.

    blender --background --python tools/make_building_items2.py
    python tools/render_icon_from_model.py assets/building/<id>/<id>.glb assets/building/<id>/<id>.png        (every new item)
    python tools/generate_unity_asset_catalog.py ; python tools/package_catalog_as_mods.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_building_items as mod  # noqa: E402
import make_structure_stages as base  # noqa: E402

M = base.material


# ------------------------------------------------------------------ generic shapes

def label_panel(b, w, d, h, label_rgb):
    """The front of a box: a colour band that says what kind of thing it is, with a white paper label over it (a heading bar and two lines of text)."""
    b.box(-w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.004, -d / 2, h * 0.2, h * 0.8, M('Label', label_rgb, 0.8))          # the colour band
    paper, ink = M('LabelPaper', (0.95, 0.95, 0.92), 0.85), M('LabelInk', (0.12, 0.12, 0.14), 0.8)
    b.box(-w / 2 + 0.03, w / 2 - 0.03, -d / 2 - 0.007, -d / 2 - 0.004, h * 0.34, h * 0.66, paper)                      # the label over the band
    b.box(-w / 2 + 0.045, w / 2 - 0.045, -d / 2 - 0.009, -d / 2 - 0.007, h * 0.55, h * 0.61, ink)                       # a heading
    b.box(-w / 2 + 0.045, w / 2 * 0.35, -d / 2 - 0.009, -d / 2 - 0.007, h * 0.45, h * 0.49, ink)                        # two lines of text
    b.box(-w / 2 + 0.045, w / 2 * 0.1, -d / 2 - 0.009, -d / 2 - 0.007, h * 0.38, h * 0.42, ink)


def tape_seam(b, w, d, h):
    """The taped seam across the top, where the two flaps meet (the tape runs down both sides a little)."""
    tape = M('Tape', (0.8, 0.7, 0.45), 0.7)
    b.box(-w / 2 - 0.002, w / 2 + 0.002, -0.014, 0.014, h, h + 0.004, tape)                      # over the top
    b.box(-w / 2 - 0.004, -w / 2, -0.014, 0.014, h * 0.9, h + 0.004, tape)                       # down the left side
    b.box(w / 2, w / 2 + 0.004, -0.014, 0.014, h * 0.9, h + 0.004, tape)                         # and the right
    b.box(-w / 2 - 0.002, w / 2 + 0.002, -d / 2 - 0.004, -d / 2, h * 0.9, h * 0.94, tape)        # a strip along the front top edge
    b.box(-w / 2, w / 2, -0.001, 0.001, h, h + 0.005, M('Seam', (0.35, 0.28, 0.15), 0.8))         # the line of the flaps meeting


def carton(name, w, d, h, body, label):
    b = base.Builder(name)
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, M('Carton', body, 0.85))
    label_panel(b, w, d, h, label)
    tape_seam(b, w, d, h)
    return b


def bucket(name, r, h, body, lid, band):
    b = base.Builder(name)
    b.log((0, 0, 0), (0, 0, h * 0.95), r, M('Bucket', body, 0.6), sides=16)
    b.log((0, 0, h * 0.95), (0, 0, h), r * 1.04, M('Lid', lid, 0.6), sides=16)
    b.log((0, 0, h * 0.3), (0, 0, h * 0.72), r * 1.012, M('BucketLabel', band, 0.7), sides=16)
    b.box(-r * 0.5, r * 0.5, -0.01, 0.01, h, h + 0.035, M('Handle', (0.3, 0.3, 0.3), 0.5))
    return b


def roll(name, r, length, wrap, core_rgb, core_r=None):
    """A roll lying on its side, its axis along x."""
    b = base.Builder(name)
    b.log((-length / 2, 0, r), (length / 2, 0, r), r, M('Wrap', wrap, 0.8), sides=18)
    b.log((-length / 2 - 0.004, 0, r), (length / 2 + 0.004, 0, r), core_r or r * 0.3, M('Core', core_rgb, 0.8), sides=10)
    return b


def sheet(name, w, d, h, rgb, edge):
    b = base.Builder(name)
    b.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, h, M('Sheet', rgb, 0.8))
    b.box(-w / 2 - 0.002, w / 2 + 0.002, -d / 2 - 0.002, d / 2 + 0.002, h * 0.46, h * 0.54, M('Edge', edge, 0.7))
    return b


def bundle(name, count_x, count_z, length, w, t, rgb, strap=(0.2, 0.25, 0.3)):
    """Boards lying along x, stacked count_x wide and count_z high, strapped."""
    b = base.Builder(name)
    wood = M('Timber', rgb, 0.85)
    for i in range(count_x):
        for k in range(count_z):
            y0 = (i - count_x / 2) * w
            z0 = k * t
            b.box(-length / 2, length / 2, y0 + 0.002, y0 + w - 0.002, z0 + 0.002, z0 + t - 0.002, wood)
    sm = M('Strap', strap, 0.5)
    for x in (-length * 0.3, length * 0.3):
        b.box(x - 0.012, x + 0.012, -count_x * w / 2 - 0.004, count_x * w / 2 + 0.004, -0.004, count_z * t + 0.004, sm)
    return b


def spool(name, r, width, wire, flange=(0.55, 0.38, 0.2)):
    b = base.Builder(name)
    b.log((0, -width / 2, r), (0, width / 2, r), r * 0.35, M('SpoolCore', flange, 0.8), sides=10)
    b.log((0, -width / 2, r), (0, -width / 2 + 0.012, r), r, M('Flange', flange, 0.8), sides=18)
    b.log((0, width / 2 - 0.012, r), (0, width / 2, r), r, M('Flange', flange, 0.8), sides=18)
    b.log((0, -width / 2 + 0.012, r), (0, width / 2 - 0.012, r), r * 0.86, M('Wire', wire, 0.5), sides=18)
    return b


def can(name, r, h, body, cap, label):
    b = base.Builder(name)
    b.log((0, 0, 0), (0, 0, h), r, M('Can', body, 0.5), sides=14)
    b.log((0, 0, h * 0.28), (0, 0, h * 0.7), r * 1.012, M('CanLabel', label, 0.7), sides=14)
    b.log((0, 0, h), (0, 0, h + 0.03), r * 0.7, M('Cap', cap, 0.5), sides=10)
    b.log((0, 0, h + 0.03), (0, -0.04, h + 0.05), 0.008, M('Cap', cap, 0.5), sides=6)     # the nozzle
    return b


def bag(name, w, h, d, body, band):
    return mod.bag(name, w, h, d, body, band)


# ------------------------------------------------------------------ specific things

def gutter():
    b = base.Builder('building_gutter_section')
    m = M('Gutter', (0.85, 0.86, 0.88), 0.4)
    L = 3.0
    b.box(-L / 2, L / 2, -0.06, 0.06, 0.0, 0.012, m)
    b.box(-L / 2, L / 2, -0.06, -0.048, 0.0, 0.09, m)
    b.box(-L / 2, L / 2, 0.048, 0.06, 0.0, 0.11, m)
    return b


def downspout():
    b = base.Builder('building_downspout')
    m = M('Gutter', (0.85, 0.86, 0.88), 0.4)
    b.box(-0.035, 0.035, -0.05, 0.05, 0.12, 3.0, m)
    b.box(-0.035, 0.035, -0.05, 0.05, 0.0, 0.12, m)
    b.box(-0.035, 0.035, -0.2, 0.05, 0.0, 0.07, m)   # the elbow out at the bottom
    return b


def soffit():
    return sheet('building_soffit_panel', 0.3, 2.4, 0.015, (0.93, 0.92, 0.88), (0.8, 0.8, 0.8))


def concrete_block():
    b = base.Builder('building_concrete_block')
    gray = M('Block', (0.62, 0.62, 0.6), 0.95)
    dark = M('BlockCore', (0.35, 0.35, 0.34), 0.95)
    b.box(-0.2, 0.2, -0.1, 0.1, 0.0, 0.2, gray)
    for x in (-0.1, 0.1):
        b.box(x - 0.055, x + 0.055, -0.06, 0.06, 0.2, 0.201, dark)
    return b


def beam_glulam():
    b = base.Builder('building_beam_glulam')
    wood = M('Glulam', (0.82, 0.66, 0.42), 0.8)
    line = M('Lamination', (0.62, 0.48, 0.28), 0.8)
    L = 4.0
    b.box(-L / 2, L / 2, -0.065, 0.065, 0.0, 0.3, wood)
    for z in (0.075, 0.15, 0.225):
        b.box(-L / 2 - 0.001, L / 2 + 0.001, -0.066, 0.066, z - 0.002, z + 0.002, line)
    return b


def lumber_board(name, length, w, t, rgb):
    b = base.Builder(name)
    b.box(-length / 2, length / 2, -w / 2, w / 2, 0.0, t, M('Timber', rgb, 0.85))
    return b


def door_frame(name, w, h):
    b = base.Builder(name)
    wood = M('Jamb', (0.85, 0.8, 0.7), 0.7)
    j = 0.04
    b.box(-w / 2, -w / 2 + j, -0.07, 0.07, 0.0, h, wood)
    b.box(w / 2 - j, w / 2, -0.07, 0.07, 0.0, h, wood)
    b.box(-w / 2, w / 2, -0.07, 0.07, h - j, h, wood)
    b.box(-w / 2 - 0.02, -w / 2, -0.09, 0.09, 0.0, h + 0.02, wood)     # the casing
    b.box(w / 2, w / 2 + 0.02, -0.09, 0.09, 0.0, h + 0.02, wood)
    b.box(-w / 2 - 0.02, w / 2 + 0.02, -0.09, 0.09, h, h + 0.04, wood)
    return b


def knob_set():
    b = base.Builder('building_door_hardware_set')
    brass = M('Brass', (0.75, 0.6, 0.3), 0.3)
    b.log((0, 0, 0.05), (0.0, -0.05, 0.05), 0.05, brass, sides=14)           # the knob rose
    b.log((0, -0.05, 0.05), (0.0, -0.09, 0.05), 0.025, brass, sides=10)
    b.log((0, -0.09, 0.05), (0.0, -0.13, 0.05), 0.04, brass, sides=14)       # the knob
    b.box(-0.03, 0.03, 0.0, 0.1, 0.0, 0.1, brass)                             # the latch plate
    for x in (0.16, 0.22):
        b.box(x, x + 0.04, -0.005, 0.005, 0.0, 0.09, brass)                   # a hinge leaf pair
    return b


def gate_latch():
    b = base.Builder('building_gate_latch')
    steel = M('Latch', (0.3, 0.3, 0.32), 0.5)
    b.box(-0.09, 0.09, -0.01, 0.01, 0.0, 0.03, steel)
    b.box(-0.09, -0.07, -0.025, 0.01, 0.0, 0.07, steel)
    b.box(0.07, 0.09, -0.025, 0.01, 0.0, 0.07, steel)
    b.log((-0.09, -0.012, 0.045), (0.09, -0.012, 0.045), 0.012, steel, sides=8)
    return b


def valve():
    b = base.Builder('building_valve_ball_pvc')
    white = M('PVC', (0.92, 0.92, 0.9), 0.5)
    red = M('Handle', (0.75, 0.15, 0.12), 0.5)
    b.log((-0.07, 0, 0.04), (0.07, 0, 0.04), 0.03, white, sides=12)
    b.log((0, 0, 0.04), (0, 0, 0.1), 0.028, white, sides=10)
    b.box(-0.05, 0.05, -0.008, 0.008, 0.1, 0.115, red)
    return b


def foam_board():
    return sheet('building_insulation_foam_board', 1.2, 2.4, 0.05, (0.55, 0.72, 0.9), (0.45, 0.62, 0.8))


# ------------------------------------------------------------------ the table

ITEMS2 = [
    # weatherproofing
    ('building_house_wrap_roll', 'House Wrap Roll', 'A roll of house wrap for sheathing, 1.5 m wide.', lambda: roll('building_house_wrap_roll', 0.16, 1.5, (0.93, 0.93, 0.9), (0.6, 0.45, 0.28)), 11.0, 6, 95, ['weatherproofing']),
    ('building_roofing_felt_roll', 'Roofing Felt Roll', 'A roll of tar paper under the roofing.', lambda: roll('building_roofing_felt_roll', 0.14, 0.95, (0.16, 0.16, 0.17), (0.55, 0.42, 0.25)), 22.0, 6, 55, ['weatherproofing']),
    ('building_flashing_roll', 'Flashing Roll', 'A roll of aluminium flashing for roof edges, valleys and chimneys.', lambda: roll('building_flashing_roll', 0.09, 0.3, (0.8, 0.82, 0.84), (0.45, 0.45, 0.47)), 4.0, 10, 38, ['weatherproofing']),
    ('building_weatherstripping_roll', 'Weather Stripping', 'A roll of door and window weather stripping.', lambda: roll('building_weatherstripping_roll', 0.06, 0.1, (0.18, 0.18, 0.2), (0.7, 0.7, 0.7)), 0.5, 20, 9, ['weatherproofing']),
    ('building_gutter_section', 'Gutter Section', 'A length of aluminium gutter.', gutter, 3.0, 10, 28, ['weatherproofing']),
    ('building_downspout', 'Downspout', 'A downspout with its bottom elbow.', downspout, 3.5, 10, 24, ['weatherproofing']),
    ('building_soffit_panel', 'Soffit Panel', 'A vented vinyl soffit panel for the underside of the eaves.', soffit, 1.5, 10, 14, ['weatherproofing']),
    ('building_fascia_board', 'Fascia Board', 'A 2.4 m fascia board for the roof edge.', lambda: lumber_board('building_fascia_board', 2.4, 0.14, 0.02, (0.95, 0.95, 0.92)), 2.2, 20, 11, ['weatherproofing', 'trim']),
    # framing and beams
    ('building_beam_glulam', 'Glulam Beam', 'A laminated beam, 4 m by 130 mm by 300 mm.', beam_glulam, 80.0, 2, 220, ['beams']),
    ('building_lumber_rafter_2x8', 'Rafter 2x8', 'A 2x8 board cut for rafters, 4 m long.', lambda: lumber_board('building_lumber_rafter_2x8', 4.0, 0.19, 0.04, (0.74, 0.58, 0.36)), 14.0, 10, 24, ['rafters']),
    ('building_lumber_joist_2x10', 'Joist 2x10', 'A 2x10 board for floor joists, 4 m long.', lambda: lumber_board('building_lumber_joist_2x10', 4.0, 0.235, 0.04, (0.74, 0.58, 0.36)), 18.0, 10, 30, ['joists']),
    # masonry
    ('building_concrete_block', 'Concrete Block', 'A standard 200 x 200 x 400 mm hollow concrete block.', concrete_block, 17.0, 40, 3, ['masonry_units']),
    ('building_grout_bag', 'Grout Bag', 'A bag of tile grout.', lambda: bag('building_grout_bag', 0.3, 0.42, 0.1, (0.8, 0.78, 0.74), (0.35, 0.55, 0.4)), 11.0, 20, 16, ['tile_setting']),
    ('building_thinset_bucket', 'Tile Adhesive (Bucket)', 'A bucket of tile adhesive.', lambda: bucket('building_thinset_bucket', 0.14, 0.36, (0.95, 0.95, 0.93), (0.2, 0.35, 0.6), (0.9, 0.6, 0.15)), 18.0, 10, 28, ['tile_setting']),
    # interior finishing
    ('building_trim_baseboard', 'Baseboard Bundle', 'A bundle of primed baseboard, 2.4 m lengths.', lambda: bundle('building_trim_baseboard', 4, 3, 2.4, 0.09, 0.016, (0.95, 0.95, 0.92)), 10.0, 6, 40, ['trim']),
    ('building_trim_casing', 'Door and Window Casing', 'A bundle of primed casing, 2.4 m lengths.', lambda: bundle('building_trim_casing', 3, 3, 2.4, 0.07, 0.016, (0.95, 0.95, 0.92)), 8.0, 6, 34, ['trim']),
    ('building_joint_compound_bucket', 'Joint Compound (Bucket)', 'A bucket of drywall joint compound.', lambda: bucket('building_joint_compound_bucket', 0.15, 0.36, (0.94, 0.94, 0.92), (0.9, 0.9, 0.9), (0.25, 0.45, 0.75)), 24.0, 10, 22, ['drywall_finishing']),
    ('building_drywall_tape_roll', 'Drywall Tape', 'A roll of paper drywall tape.', lambda: roll('building_drywall_tape_roll', 0.05, 0.06, (0.93, 0.92, 0.85), (0.6, 0.6, 0.6)), 0.4, 20, 5, ['drywall_finishing']),
    ('building_door_frame_interior', 'Interior Door Frame', 'A prehung interior door frame with casing, for a 0.9 m door.', lambda: door_frame('building_door_frame_interior', 0.92, 2.1), 14.0, 6, 70, ['door_frames']),
    ('building_door_frame_exterior', 'Exterior Door Frame', 'A prehung exterior door frame with casing, for a 1.2 m door.', lambda: door_frame('building_door_frame_exterior', 1.22, 2.3), 22.0, 4, 120, ['door_frames']),
    # fasteners and hardware
    ('building_door_hardware_set', 'Door Hardware Set', 'A door knob set with its latch and a pair of hinges.', knob_set, 0.8, 20, 24, ['door_hardware']),
    ('building_gate_latch', 'Gate Latch', 'A steel gravity latch for a gate.', gate_latch, 0.4, 20, 12, ['door_hardware']),
    # insulation
    ('building_insulation_foam_board', 'Rigid Foam Board', 'A 1.2 m by 2.4 m sheet of rigid foam board insulation.', foam_board, 4.0, 10, 36, ['insulation']),
    ('building_insulation_spray_foam', 'Spray Foam Can', 'A can of expanding spray foam for gaps and edges.', lambda: can('building_insulation_spray_foam', 0.035, 0.26, (0.95, 0.85, 0.2), (0.15, 0.15, 0.17), (0.2, 0.3, 0.55)), 0.6, 20, 9, ['insulation']),
    ('building_insulation_blown_bag', 'Blown Insulation Bag', 'A bag of loose-fill attic insulation.', lambda: bag('building_insulation_blown_bag', 0.5, 0.75, 0.3, (0.88, 0.62, 0.7), (0.95, 0.95, 0.95)), 12.0, 10, 26, ['insulation']),
    # electrical and plumbing supplies
    ('building_romex_14_2_spool', 'Romex 14-2 Spool', 'A spool of 14-2 NM cable for lighting circuits.', lambda: spool('building_romex_14_2_spool', 0.2, 0.18, (0.93, 0.93, 0.9)), 9.0, 4, 70, []),
    ('building_romex_10_3_spool', 'Romex 10-3 Spool', 'A spool of 10-3 NM cable for heavy circuits.', lambda: spool('building_romex_10_3_spool', 0.22, 0.2, (0.15, 0.15, 0.17)), 16.0, 4, 130, []),
    ('building_pvc_cement_can', 'PVC Cement', 'A can of PVC solvent cement with a dauber.', lambda: can('building_pvc_cement_can', 0.045, 0.1, (0.7, 0.7, 0.72), (0.2, 0.2, 0.22), (0.85, 0.55, 0.1)), 0.5, 20, 11, ['plumbing_supplies']),
    ('building_pvc_primer_can', 'PVC Primer', 'A can of purple PVC primer.', lambda: can('building_pvc_primer_can', 0.045, 0.1, (0.7, 0.7, 0.72), (0.2, 0.2, 0.22), (0.55, 0.25, 0.65)), 0.5, 20, 9, ['plumbing_supplies']),
    ('building_valve_ball_pvc', 'PVC Ball Valve', 'A 1 inch PVC ball valve.', valve, 0.3, 20, 14, ['plumbing_supplies']),
]


def main():
    mod.ITEMS = mod.ITEMS + ITEMS2
    mod.main()


if __name__ == '__main__':
    main()
