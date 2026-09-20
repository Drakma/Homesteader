"""divlayout.py - HTML-style layout for the HUD.

Each top-level section is a `Div` (analogous to a <div>): a bounding
rect on the canvas, with widgets anchored INSIDE the div by their
alignment (top-left / top-center / top-right / middle-center /
middle-right / bottom-left / bottom-center / bottom-right).

The Div system covers two responsibilities:
  - *position* (where the div sits on the canvas)
  - *anchor* (where a child sits INSIDE its parent div)

Children do NOT compute coordinates relative to the parent's
top-left. They say "I'm top-center / bottom-right / etc." and the
layout places them. Moving the parent moves everything inside.

Anchor names (3x3 grid, center is the default 'middle-center'):

    top-left      | top-center      | top-right
    --------------+-----------------+--------------
    middle-left   | middle-center   | middle-right
    --------------+-----------------+--------------
    bottom-left   | bottom-center   | bottom-right

Each Div has:
    name        : str
    origin      : (x, y)            canvas pixel top-left
    size        : (w, h)

Each Widget has:
    div         : parent Div
    name        : str
    size        : (w, h)
    anchor      : Anchor (where in its parent it sits)
    pad         : int  (additional padding from the div edge)

Wiget.abs_x() and abs_y() compute the canvas pixel coord.
"""
import dataclasses
import enum


class Anchor(enum.Enum):
    """Where a child sits inside its parent div.

    Naming convention: vertical-position + horizontal-position.
    """
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    MIDDLE_LEFT = "middle-left"
    MIDDLE_CENTER = "middle-center"
    MIDDLE_RIGHT = "middle-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"


@dataclasses.dataclass
class Div:
    """A rectangular region on the canvas, like a <div>."""
    name: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    def right(self) -> int:
        return self.x + self.w

    def bottom(self) -> int:
        return self.y + self.h

    def inside_offset(self, anchor: Anchor, w: int, h: int, pad: int) -> tuple:
        """Compute child top-left offset so the child sits at `anchor`
        INSIDE this div, with extra `pad` from the div's edges.
        Returns (cx, cy) - the offset within the div where the child's
        top-left should land (or for inline layouts, base coord).
        """
        # Vertical position.
        if anchor.value.startswith("top"):
            cy = pad
        elif anchor.value.startswith("middle"):
            cy = (self.h - h) // 2
        else:  # bottom
            cy = self.h - h - pad
        # Horizontal position.
        if anchor.value.endswith("left"):
            cx = pad
        elif anchor.value.endswith("center"):
            cx = (self.w - w) // 2
        else:  # right
            cx = self.w - w - pad
        return (cx, cy)


@dataclasses.dataclass
class Widget:
    """A single widget placed inside a parent Div.

    Two ways to position a widget:
      1) anchor + pad  : place at div corner with N px padding from
                          the div's bounding edge.
      2) explicit x_off: place at absolute (div.x + x_off, div.y + y_off)
                          in parent local coordinates.

    For sub-units (e.g. a vital card sitting at column N inside vitals
    div), use explicit x_off. For one-off widgets placed at fixed
    corners, use anchor + pad.
    """
    name: str
    div: Div
    w: int
    h: int
    anchor: Anchor = Anchor.MIDDLE_CENTER       # if used
    pad: int = 0                                # padding from div edge
    x_off: int = None                          # explicit parent x
    y_off: int = None                          # explicit parent y

    def abs_box(self):
        if self.x_off is not None and self.y_off is not None:
            cx, cy = self.x_off, self.y_off
        else:
            cx, cy = self.div.inside_offset(self.anchor,
                                              self.w, self.h, self.pad)
        return (self.div.x + cx, self.div.y + cy, self.w, self.h)

    def abs_x(self) -> int:
        if self.x_off is not None:
            cx = self.x_off
        else:
            cx, _ = self.div.inside_offset(self.anchor, self.w, self.h,
                                             self.pad)
        return self.div.x + cx

    def abs_y(self) -> int:
        if self.y_off is not None:
            cy = self.y_off
        else:
            _, cy = self.div.inside_offset(self.anchor, self.w, self.h,
                                             self.pad)
        return self.div.y + cy


@dataclasses.dataclass
class Page:
    """A collection of named Divs. Move any div's x/y; widgets
    arranged inside follow.
    """
    divs: dict = dataclasses.field(default_factory=dict)

    def add(self, div):
        self.divs[div.name] = div

    def get(self, name):
        return self.divs[name]

    def move(self, name, dx, dy):
        d = self.get(name)
        d.x += dx
        d.y += dy
        return d


def make_layout(*, canvas_w, canvas_h,
                header_h=48,
                toolbar_w=752, toolbar_h=80,
                vital_w_each=120, vital_gap=8,
                vital_icon=20, vital_bar_w=68, vital_bar_h=14,
                vital_bar_right_pad=16,
                vital_bar_left_pad=2,
                res_w_each=64, res_gap=8,
                res_icon=20, res_text_pad=2,
                speed_chip=10, speed_chip_gap=2, speed_text_pad=20):
    """Construct the layout's divs based on explicit dimensions.

    All sizes in DESIGN pixels (will scale with m.s at render time).

    Each Widget declares its anchor inside its parent div. The
    renderer uses Anchor.inside_offset() to compute exact positions.
    """
    p = Page()

    # ---- Header (status bar at top) ----
    header = Div(name="header", x=0, y=0, w=canvas_w, h=header_h)
    p.add(header)

    # ---- Vitals (left third of the header) ----
    n_v = 4
    vitals_total_w = n_v * vital_w_each + (n_v - 1) * vital_gap
    vitals = Div(
        name="vitals",
        x=header.x + 8,
        y=header.y + 4,
        w=vitals_total_w,
        h=header_h - 8,
    )
    p.add(vitals)

    # ---- Time + speed (center third + below-it speed row) ----
    # Time gets a small band at the top; speed gets the larger remainder
    # so the 28px speed chips render close to their natural size.
    time_w = canvas_w // 3
    time_x = (canvas_w - time_w) // 2
    time_h = max(12, int((header_h - 8) * 0.30))
    time = Div(name="time", x=time_x, y=header.y + 4,
              w=time_w, h=time_h)
    p.add(time)
    speed_h = (header_h - 8) - time_h
    speed = Div(name="speed", x=time_x, y=time.bottom() + 1,
                w=time_w, h=speed_h)
    p.add(speed)

    # ---- Resources (right third of the header) ----
    # Cell width is icon + 0 gap + 64 px text (text_part_w).
    res_text_part_w = 80
    res_cell_w = res_icon + res_text_pad + res_text_part_w   # 22 + 2 + 80 = 104
    res_total_w = n_v * res_cell_w + (n_v - 1) * res_gap
    resources = Div(
        name="resources",
        x=header.right() - res_total_w - 8,
        y=header.y + 4,
        w=res_total_w,
        h=header_h - 8,
    )
    p.add(resources)

    # ---- Toolbar (bottom-center) ----
    toolbar = Div(
        name="toolbar",
        x=(canvas_w - toolbar_w) // 2,
        y=canvas_h - toolbar_h - 8,
        w=toolbar_w, h=toolbar_h,
    )
    p.add(toolbar)

    # ---- Vital children: each vital is its own DIV (sub-div) with
    # icon + bar inside. Moving the vital div moves both children.
    # Cells: width auto-fits to icon + bar + gap, no inner padding.
    # Outer right padding: vital_cell_right_pad.
    vital_widgets: list = []
    vital_cells: list = []
    for i in range(n_v):
        # Cell auto-fits: width = icon + pad + bar.
        cell_w = vital_icon + vital_bar_left_pad + vital_bar_w
        # Card stack: i-th card.
        # Outer right padding flows as: leave 8 px between cells.
        card_x = i * cell_w + i * 8
        # Create a sub-div for this vital card.
        vital_cell = Div(
            name=f"vital_cell_{i}",
            x=vitals.x + card_x,
            y=vitals.y,
            w=cell_w,
            h=vitals.h,
        )
        vital_cells.append(vital_cell)
        # Icon: middle-left of the vital cell (anchor middle-left).
        icon_w = Widget(
            name=f"vital_icon_{i}", div=vital_cell,
            w=vital_icon, h=vital_icon,
            anchor=Anchor.MIDDLE_LEFT,
        )
        # Bar: middle-center of the vital cell, offset right by
        # icon + left pad.
        bar_y_off = max(0, (vital_cell.h - vital_bar_h) // 2)
        bar_w_w = Widget(
            name=f"vital_bar_{i}", div=vital_cell,
            w=vital_bar_w, h=vital_bar_h,
            x_off=vital_icon + vital_bar_left_pad,
            y_off=bar_y_off,
        )
        vital_widgets.append(icon_w)
        vital_widgets.append(bar_w_w)

    # ---- Time + speed with anchors ----
    # Time: top-center of the time div (full-width, top edge).
    # Speed chips: middle-center of the speed div (5 chips total).
    time_text = Widget(name="time_text", div=time,
                        w=time_w, h=time_h,
                        anchor=Anchor.MIDDLE_CENTER)
    speed_widgets: list = []
    n_chips = 5
    chip_total_w = n_chips * speed_chip + (n_chips - 1) * speed_chip_gap
    chip_left = max(0, (speed.w - chip_total_w) // 2)
    speed_chip_y = max(0, (speed.h - speed_chip) // 2)
    for i in range(n_chips):
        chip_off = i * (speed_chip + speed_chip_gap)
        speed_widgets.append(Widget(
            name=f"speed_chip_{i}", div=speed,
            w=speed_chip, h=speed_chip,
            x_off=chip_left + chip_off, y_off=speed_chip_y,
        ))

    # ---- Resources with anchors ----
    # Each resource: icon top-left of the resource's cell + bar top-left.
    resource_widgets: list = []
    resource_cells: list = []
    for i in range(n_v):
        # Each resource slot has an 8 px outer-left pad before the icon.
        cell_x = i * (res_cell_w + res_gap) + 8
        cell = Div(name=f"resource_cell_{i}",
                    x=resources.x + cell_x,
                    y=resources.y,
                    w=res_cell_w, h=resources.h)
        # Icon: vertically middle inside the cell (no horizontal pad;
        # the renderer centers horizontally).
        icon_y_offset = (cell.h - res_icon) // 2
        icon_w = Widget(
            name=f"res_icon_{i}", div=cell,
            w=res_icon, h=res_icon,
            x_off=0, y_off=icon_y_offset,
        )
        # Text: explicit position after the icon, vertically middle.
        text_x = res_icon + res_text_pad
        text_w_w = Widget(
            name=f"res_text_{i}", div=cell,
            w=res_text_part_w, h=11,
            x_off=text_x,
            y_off=(cell.h - 11) // 2,
        )
        resource_cells.append(cell)
        resource_widgets.append(icon_w)
        resource_widgets.append(text_w_w)

    # ---- Toolbar slots: explicit x_offset per slot ----
    n_slots = 10
    slot_size = 64
    slot_gap = 8
    toolbar_widgets: list = []
    for i in range(n_slots):
        cell_x = i * (slot_size + slot_gap)
        slot_w = Widget(
            name=f"toolbar_slot_{i}", div=toolbar,
            w=slot_size, h=slot_size,
            x_off=cell_x, y_off=2,
        )
        toolbar_widgets.append(slot_w)

    return {
        "page": p,
        "divs": dict(p.divs),
        "vital_widgets": vital_widgets,
        "vital_cells": vital_cells,
        "speed_widgets": speed_widgets,
        "resource_widgets": resource_widgets,
        "resource_cells": resource_cells,
        "toolbar_widgets": toolbar_widgets,
    }


# All sizes are in DESIGN pixel coordinates. The renderer scales them
# to actual canvas via m.px() in render.py.
SIZE = {
    "header_h":       48,
    "toolbar_w":      752,
    "toolbar_h":      80,
    "vital_w_each":   120,
    "vital_gap":      6,
    "vital_icon":     20,
    "vital_bar_w":    68,
    "vital_bar_h":    14,
    "vital_left_pad": 4,
    "vital_bar_left_pad": 2,
    "vital_bar_right_pad": 16,
    "res_w_each":     64,
    "res_gap":        0,
    "res_icon":       20,
    "res_text_pad":   0,
    "res_text_part_w": 80,
    "speed_chip":     10,
    "speed_chip_gap": 2,
    "speed_text_pad": 20,    # vertical offset below time text
}


def build_layout(canvas_w: int, canvas_h: int):
    return make_layout(
        canvas_w=canvas_w, canvas_h=canvas_h,
        header_h=SIZE["header_h"],
        toolbar_w=SIZE["toolbar_w"], toolbar_h=SIZE["toolbar_h"],
        vital_w_each=SIZE["vital_w_each"], vital_gap=SIZE["vital_gap"],
        vital_icon=SIZE["vital_icon"], vital_bar_w=SIZE["vital_bar_w"],
        vital_bar_h=SIZE["vital_bar_h"],
        res_w_each=SIZE["res_w_each"], res_gap=SIZE["res_gap"],
        res_icon=SIZE["res_icon"], res_text_pad=SIZE["res_text_pad"],
        speed_chip=SIZE["speed_chip"], speed_chip_gap=SIZE["speed_chip_gap"],
        speed_text_pad=SIZE["speed_text_pad"],
    )
