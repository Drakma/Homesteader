"""layout.py - explicit group hierarchy for the HUD.

Each top-level section (vitals, time, speed, resources) is a `Group`.
WIDGETS in a group are placed relative to the GROUP's local coordinate
origin (top-left) - just like HTML <div>s.

Group structure:
    BarGroup
        VitalsGroup
            VitalGroup (4)
                Icon
                BarGroup (icon + bar are siblings)
                    BarTrack + BarFillLeft + BarFillRight + BarCenter
        TimeGroup
            TimeString
        SpeedGroup
            SpeedChip * 5
        ResourcesGroup
            ResourceGroup (4)
                Icon + ValueText

Each Group knows its parent rect + its own bounding rect. Widgets
inside a group are placed by ORIGIN + OFFSET so groups can be moved
or re-flowed without re-touching widget math.
"""
import dataclasses
from typing import Tuple


@dataclasses.dataclass
class Rect:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    def right(self) -> int:
        return self.x + self.w

    def bottom(self) -> int:
        return self.y + self.h

    def is_inside(self, x: int, y: int) -> bool:
        return self.x <= x <= self.right() and self.y <= y <= self.bottom()


@dataclasses.dataclass
class VitalGroup:
    """Each vital has its own local rect. Icon is laid down on the
    left half, bar on the right half - both relative to this rect's
    origin.
    """
    vital_id: object
    icon_rect: Rect
    bar_rect: Rect
    hover_rect: Rect       # full vital card; hover text comes from here


@dataclasses.dataclass
class VitalsSection:
    outer_rect: Rect
    vitals: list   # list[VitalGroup]


@dataclasses.dataclass
class TimeSection:
    rect: Rect
    text: str


@dataclasses.dataclass
class SpeedChip:
    label: str
    is_active: bool
    rect: Rect


@dataclasses.dataclass
class SpeedSection:
    outer_rect: Rect
    chips: list   # list[SpeedChip]


@dataclasses.dataclass
class ResourceGroup:
    resource_id: object
    icon_rect: Rect
    text_rect: Rect


@dataclasses.dataclass
class ResourcesSection:
    outer_rect: Rect
    resources: list   # list[ResourceGroup]


@dataclasses.dataclass
class HudLayout:
    """Top-level layout container with all the sections laid out within
    the bar's inner rect.
    """
    bar_rect: Rect
    inner_rect: Rect
    vitals: VitalsSection
    time: TimeSection
    speed: SpeedSection
    resources: ResourcesSection


def compute_hud_layout(*, bar_rect, sprite_inset, m, vital_card_w,
                       vital_card_gap, icon_size, bar_w_v, res_icon_size,
                       res_cell_w, res_gap, speed_chip_w, speed_gap,
                       pad_v_time_to_speed):
    """Compute section rects and individual widget rects.

    All math is in design-pixel units; m.px() returns design px scaled
    to the output canvas. We operate in design units here.
    """
    inner_x = bar_rect.x + sprite_inset
    inner_y = bar_rect.y + sprite_inset
    inner_w = bar_rect.w - 2 * sprite_inset
    inner_h = bar_rect.h - 2 * sprite_inset
    inner = Rect(x=inner_x, y=inner_y, w=inner_w, h=inner_h)

    # Section origins (design px).
    # Vitals: left third.
    vital_section_w = inner_w // 3
    vitals = VitalsSection(
        outer_rect=Rect(inner.x, inner.y, vital_section_w, inner_h),
        vitals=[],
    )
    # Time: centered vertical band, centered horizontally.
    time_band_w = inner_w // 3
    time_x = inner.x + (inner_w - time_band_w) // 2
    time_band_h = inner_h // 2 - m._px(2) if hasattr(m, "_px") else \
        max(8, inner_h // 4)
    time = TimeSection(
        rect=Rect(time_x, inner.y + (inner_h - time_band_h) // 2,
                  time_band_w, time_band_h),
        text="",
    )
    # Speed row: right under the time band, centered vertically in
    # the lower half of the inner rect.
    chip_w = m.px(speed_chip_w)
    chip_gap = m.px(speed_gap)
    speed_outer_w = inner_w // 3
    speed_outer_x = inner.x + 2 * (inner_w // 3)
    speed_outer = Rect(speed_outer_x, inner.y,
                       speed_outer_w, inner_h)
    speed = SpeedSection(outer_rect=speed_outer, chips=[])

    # Resources: right third.
    res_section_w = inner_w - 2 * (inner_w // 3)
    res_outer = Rect(inner.x + 2 * (inner_w // 3),
                     inner.y, res_section_w, inner_h)
    resources = ResourcesSection(outer_rect=res_outer, resources=[])

    # ---- Vitals sub-layout ----
    vx = vitals.outer_rect.x
    vital_section_inner_w = vitals.outer_rect.w - 2 * m.px(sprite_inset // 3)
    # Distribute 4 vitals across the inner width (left-edge aligned via
    # vx + vital_section_w_offset).
    v_x_offset = (vital_section_inner_w -
                  (4 * m.px(vital_card_w) + 3 * m.px(vital_card_gap))) // 2
    if v_x_offset < 0:
        v_x_offset = 0
    vx += v_x_offset + m.px(sprite_inset // 4)
    icon_px = m.px(icon_size)
    bar_px = m.px(bar_w_v)
    bar_gap_px = m.px(8)
    vital_card_px = m.px(vital_card_w)
    vital_card_gap_px = m.px(vital_card_gap)
    for vid in ["wellness", "stamina", "thirst", "hunger"]:
        # Vital card vertical centering within inner.
        card_y = inner.y + (inner_h - icon_px) // 2
        # Icon on the left.
        icon_rect = Rect(vx, card_y, icon_px, icon_px)
        # Bar centered on icon-height middle, to the right of icon.
        bar_y = card_y + (icon_px - bar_px) // 2
        bar_rect = Rect(vx + icon_px + 6, bar_y, bar_px, bar_px)  # gap
        # Hover area = full vital card width.
        hover_rect = Rect(vx, card_y, vital_card_px, icon_px)
        vitals.vitals.append(VitalGroup(
            vital_id=vid,
            icon_rect=icon_rect,
            bar_rect=bar_rect,
            hover_rect=hover_rect,
        ))
        vx += vital_card_px + vital_card_gap_px

    # ---- Resources sub-layout ----
    rx_right_edge = res_outer.right() - m.px(sprite_inset)
    res_inner_padding = m.px(2)
    res_total = 4 * m.px(res_cell_w) + 3 * m.px(res_gap)
    rx_start = rx_right_edge - res_total
    # Center vertically inside res_outer.
    res_y = res_outer.y + (res_outer.h - m.px(res_icon_size)) // 2
    rxi = rx_start
    for rid in ["water", "electricity", "bandwidth", "fuel"]:
        icon_rect = Rect(rxi, res_y,
                         m.px(res_icon_size), m.px(res_icon_size))
        text_rect = Rect(rxi + m.px(res_icon_size) + m.px(2), res_y,
                         m.px(res_cell_w), m.px(res_icon_size))
        resources.resources.append(ResourceGroup(
            resource_id=rid,
            icon_rect=icon_rect,
            text_rect=text_rect,
        ))
        rxi += m.px(res_cell_w) + m.px(res_gap)

    # ---- Speed chips ----
    n_chips = 5
    row_total = n_chips * chip_w + (n_chips - 1) * chip_gap
    chip_y_top = time.rect.bottom() + m.px(pad_v_time_to_speed)
    chip_y = min(speed.outer_rect.bottom() - chip_w - m.px(2),
                 chip_y_top)
    cx_start = speed.outer_rect.x + (speed.outer_rect.w - row_total) // 2
    speed_labels = ["||", "1x", "3x", "5x", "9x"]
    for i, lbl in enumerate(speed_labels):
        chip_x = cx_start + i * (chip_w + chip_gap)
        speed.chips.append(SpeedChip(
            label=lbl, is_active=(i == 1),
            rect=Rect(chip_x, chip_y, chip_w, chip_w),
        ))

    return HudLayout(
        bar_rect=Rect(bar_rect.x, bar_rect.y, bar_rect.w, bar_rect.h),
        inner_rect=inner,
        vitals=vitals,
        time=time,
        speed=speed,
        resources=resources,
    )
