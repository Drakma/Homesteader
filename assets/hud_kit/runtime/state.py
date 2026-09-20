"""state.py - HUD runtime state.

Top-level state container: vitals (signed -100..+100), resources
(metric units), held asset, toolbar slot selection. Each piece is a
small dataclass so the runtime can serialize for a Unity demo /
replay capture.
"""

import enum
from dataclasses import dataclass, field


class VitalId(enum.Enum):
    WELLNESS = "wellness"     # heart icon
    STAMINA = "stamina"       # running-man icon
    THIRST = "thirst"         # glass-of-water icon
    HUNGER = "hunger"         # bread icon


@dataclass
class Vital:
    """Player vital. value is signed, -100..+100. Negative = need,
    zero = balanced, positive = surplus."""
    id: VitalId
    value: int = 0


@dataclass
class ToolbarSlot:
    """One slot in the 10-slot hotbar."""
    icon_id: str = ""        # matches an asset_id from the catalog; "" = empty
    count: int = 0


class ResourceId(enum.Enum):
    WATER = "water"             # liters
    ELECTRICITY = "electricity" # watt-hours
    BANDWIDTH = "bandwidth"     # Mbps
    FUEL = "fuel"               # liters total; subspecies breakdown on hover


@dataclass
class Resource:
    """Resource total for a household meter. amount and unit determine
    how the value is rendered.
    """
    id: ResourceId
    amount: float = 0.0
    unit: str = ""
    subspecies: dict = field(default_factory=dict)
    # For FUEL: dict like {"gasoline": 12.5, "diesel": 0.0, "propane": 0.0}
    # Other resources: empty dict.

    @property
    def total(self) -> float:
        """Total amount across subspecies for compound resources (FUEL)."""
        if self.subspecies:
            return sum(self.subspecies.values())
        return self.amount


@dataclass
class HudState:
    """Top-level state singleton."""
    vitals: dict = field(default_factory=lambda: {
        VitalId.WELLNESS: Vital(VitalId.WELLNESS, 50),
        VitalId.STAMINA:  Vital(VitalId.STAMINA, 30),
        VitalId.THIRST:   Vital(VitalId.THIRST,   10),
        VitalId.HUNGER:   Vital(VitalId.HUNGER,  -20),
    })
    resources: dict = field(default_factory=lambda: {
        ResourceId.WATER: Resource(
            ResourceId.WATER, amount=120.5, unit="L"),
        ResourceId.ELECTRICITY: Resource(
            ResourceId.ELECTRICITY, amount=2400.0, unit="Wh"),
        ResourceId.BANDWIDTH: Resource(
            ResourceId.BANDWIDTH, amount=24.5, unit="Mbps"),
        ResourceId.FUEL: Resource(
            ResourceId.FUEL, subspecies={
                "gasoline": 12.5,
                "diesel": 3.0,
                "kerosene": 0.5,
                "propane": 0.0,
            }, unit="L"),
    })
    toolbar: list = field(default_factory=lambda: [
        ToolbarSlot(icon_id="wooden_axe", count=1),
        ToolbarSlot(),
        ToolbarSlot(icon_id="fishing_rod", count=1),
        ToolbarSlot(),
        ToolbarSlot(icon_id="apple", count=4),
        ToolbarSlot(),
        ToolbarSlot(icon_id="log_oak", count=12),
        ToolbarSlot(),
        ToolbarSlot(icon_id="cooked_fish", count=2),
        ToolbarSlot(),
    ])
    selected_slot: int = 0    # index into toolbar[]
    held_asset_id: str = "wooden_axe"

    def update_vital(self, v: Vital):
        self.vitals[v.id] = v

    def update_resource(self, r: Resource):
        self.resources[r.id] = r

    def select_slot(self, idx: int):
        idx = max(0, min(idx, len(self.toolbar) - 1))
        self.selected_slot = idx
        slot = self.toolbar[idx]
        self.held_asset_id = slot.icon_id or ""
