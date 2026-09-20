"""grid_layout.py - the 3x3 cell grid the HUD rests on.

Every HUD panel declares:
  - cell: which of the 9 cells it lives in
  - anchor: where inside that cell the panel sits
  - size: panel width/height in pixels

Panel position is computed deterministically from canvas dimensions.
A panel anchor of `cell-center` places the panel centered in its cell.
`cell-top-left` places it flush to the cell's top-left + margin.
`cell-bottom-right` mirrors that to the bottom-right.

This file is the only place the canvas dimensions matter. The rest of
the HUD code talks in cells, not pixels.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

# Default 1920x1080 base canvas. Variable so we can scale down for
# previews without breaking layout invariants.
CANVAS_W = 1920
CANVAS_H = 1080

# Cell grid: 3x3.
CELL_COLS = 3
CELL_ROWS = 3

# Inner cell margin in pixels. Each cell edge keeps 12 px of breathing
# room before any panel content begins.
CELL_MARGIN_PX = 12


class Cell(str, Enum):
    """9-grid coordinates."""
    TOP_LEFT   = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT  = "top-right"
    MID_LEFT   = "mid-left"
    MID_CENTER = "mid-center"
    MID_RIGHT  = "mid-right"
    BOT_LEFT   = "bot-left"
    BOT_CENTER = "bot-center"
    BOT_RIGHT  = "bot-right"

    @property
    def col(self) -> int:
        return {
            "top-left": 0, "top-center": 1, "top-right": 2,
            "mid-left": 0, "mid-center": 1, "mid-right": 2,
            "bot-left": 0, "bot-center": 1, "bot-right": 2,
        }[self.value]

    @property
    def row(self) -> int:
        return {
            "top-left": 0, "top-center": 0, "top-right": 0,
            "mid-left": 1, "mid-center": 1, "mid-right": 1,
            "bot-left": 2, "bot-center": 2, "bot-right": 2,
        }[self.value]


class Anchor(str, Enum):
    """Where inside the cell to anchor a panel."""
    CELL_TOP_LEFT     = "cell-top-left"
    CELL_TOP_CENTER   = "cell-top-center"
    CELL_TOP_RIGHT    = "cell-top-right"
    CELL_MID_LEFT     = "cell-mid-left"
    CELL_CENTER       = "cell-center"
    CELL_MID_RIGHT    = "cell-mid-right"
    CELL_BOT_LEFT     = "cell-bot-left"
    CELL_BOT_CENTER   = "cell-bot-center"
    CELL_BOT_RIGHT    = "cell-bot-right"


def cell_rect(cell: Cell, canvas_w: int = CANVAS_W,
              canvas_h: int = CANVAS_H) -> Tuple[int, int, int, int]:
    """(x, y, w, h) of a cell on the current canvas."""
    cw = canvas_w // CELL_COLS
    ch = canvas_h // CELL_ROWS
    return (cell.col * cw, cell.row * ch, cw, ch)


def anchor_position(cell: Cell, anchor: Anchor,
                    panel_w: int, panel_h: int,
                    canvas_w: int = CANVAS_W,
                    canvas_h: int = CANVAS_H,
                    margin: int = CELL_MARGIN_PX) -> Tuple[int, int]:
    """(x, y) of a panel anchored within its cell."""
    cx, cy, cw, ch = cell_rect(cell, canvas_w, canvas_h)
    inner_w = cw - 2 * margin
    inner_h = ch - 2 * margin
    # Top-to-bottom alignment.
    if anchor in (Anchor.CELL_TOP_LEFT, Anchor.CELL_TOP_RIGHT,
                  Anchor.CELL_MID_LEFT, Anchor.CELL_CENTER,
                  Anchor.CELL_MID_RIGHT):
        y = cy + margin
    elif anchor in (Anchor.CELL_TOP_CENTER,):
        # Top + vertically centered horizontally doesn't make sense; treat
        # as default 'top edge with bias toward center'.
        y = cy + margin
    elif anchor in (Anchor.CELL_BOT_LEFT, Anchor.CELL_BOT_CENTER,
                    Anchor.CELL_BOT_RIGHT):
        y = cy + ch - margin - panel_h
    else:
        y = cy + (ch - panel_h) // 2
    # Horizontally.
    if anchor in (Anchor.CELL_TOP_LEFT, Anchor.CELL_MID_LEFT,
                  Anchor.CELL_BOT_LEFT):
        x = cx + margin
    elif anchor in (Anchor.CELL_TOP_RIGHT, Anchor.CELL_MID_RIGHT,
                    Anchor.CELL_BOT_RIGHT):
        x = cx + cw - margin - panel_w
    else:
        x = cx + (cw - panel_w) // 2
    return (x, y)


@dataclass(frozen=True)
class PanelPlacement:
    cell: Cell
    anchor: Anchor
    panel_w: int
    panel_h: int
    canvas_w: int = CANVAS_W
    canvas_h: int = CANVAS_H
    margin: int = CELL_MARGIN_PX
    name: str = ""

    def rect(self) -> Tuple[int, int, int, int]:
        x, y = anchor_position(self.cell, self.anchor,
                                self.panel_w, self.panel_h,
                                self.canvas_w, self.canvas_h,
                                self.margin)
        return (x, y, self.panel_w, self.panel_h)


# Predefined HUD placements. Future panels live here too.
PLACEMENTS = {
    # All window panels are square (1:1). Size scales with canvas via
    # m.px() in render_full. Future panels get their own square
    # dimensions here.
    "player_status":    PanelPlacement(Cell.TOP_LEFT, Anchor.CELL_TOP_LEFT,
                                       192, 192, margin=8,
                                       name="player_status"),
    "season_day_time":  PanelPlacement(Cell.TOP_CENTER, Anchor.CELL_TOP_CENTER,
                                       192, 192, margin=8,
                                       name="season_day_time"),
    "held_asset":       PanelPlacement(Cell.TOP_RIGHT, Anchor.CELL_TOP_RIGHT,
                                       192, 192, margin=8,
                                       name="held_asset"),
    # Speed chips anchor below the season/day/time panel; small (32 px
    # at design).
    "speed_controls":   PanelPlacement(Cell.TOP_CENTER, Anchor.CELL_TOP_CENTER,
                                       240, 32, name="speed_controls"),
    # Bot-center holds the 10-slot toolbar. The panel rect here
    # describes the BBox; slot_size and slot count determine the
    # actual rendered geometry inside render_toolbar.
    "toolbar":          PanelPlacement(Cell.BOT_CENTER,
                                       Anchor.CELL_BOT_CENTER,
                                       960, 96, name="toolbar",
                                       margin=0),
}
