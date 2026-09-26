"""Validation for the "lights" list on an asset manifest (assets/_schemas/light_emitter.schema.json).

Mirrors LightDef.ParseList in Assets/Scripts/Growth/LightEmitter.cs. validate_lights returns (errors, warnings).
"""
import re

TYPES = {"point", "spot"}
ON_MODES = {"always", "night", "hours"}
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_lights(lights):
    errors, warnings = [], []
    if lights is None:
        return errors, warnings
    if not isinstance(lights, list):
        return ['"lights" must be a list of light objects'], warnings
    seen = set()
    for i, l in enumerate(lights):
        ctx = f"lights[{i}]"
        if not isinstance(l, dict):
            errors.append(f"{ctx}: must be an object")
            continue
        lid = l.get("id", "light")
        if lid in seen:
            errors.append(f"{ctx}: duplicate id '{lid}'")
        seen.add(lid)
        t = str(l.get("type", "point")).lower()
        if t not in TYPES:
            errors.append(f"{ctx}: type must be one of {sorted(TYPES)}")
        if "color" in l and not (isinstance(l["color"], str) and COLOR_RE.match(l["color"])):
            errors.append(f"{ctx}: color must be a hex string like #FFE9C0")
        for k, lo, hi in (("intensity", 0, None), ("range_m", 0.1, None), ("spot_angle_deg", 1, 179),
                          ("fade_minutes", 0, None), ("dusk_lead_minutes", 0, None), ("dawn_lag_minutes", 0, None), ("flicker", 0, 1), ("startup_flicker", 0, 1), ("startup_seconds", 0.1, None), ("min_level", 0, 1), ("power_w", 0, None),
                          ("pitch_deg", None, None), ("yaw_deg", None, None)):
            if k in l:
                v = l[k]
                if not _num(v):
                    errors.append(f"{ctx}: {k} must be a number")
                elif (lo is not None and v < lo) or (hi is not None and v > hi):
                    errors.append(f"{ctx}: {k} must be {'>= ' + str(lo) if hi is None else 'between ' + str(lo) + ' and ' + str(hi)}")
        off = l.get("offset_m")
        if off is not None and not (isinstance(off, list) and len(off) == 3 and all(_num(x) for x in off)):
            errors.append(f"{ctx}: offset_m must be [x, y, z] in metres")
        on = str(l.get("on", "night")).lower()
        if on not in ON_MODES:
            errors.append(f"{ctx}: on must be one of {sorted(ON_MODES)}")
        elif on == "hours":
            h = l.get("hours")
            if not (isinstance(h, list) and len(h) == 2 and all(_num(x) for x in h)):
                errors.append(f"{ctx}: on \"hours\" needs hours: [from, to]")
        for k in ("shadows", "requires_power"):
            if k in l and not isinstance(l[k], bool):
                errors.append(f"{ctx}: {k} must be true or false")
        if t != "spot" and ("spot_angle_deg" in l or "pitch_deg" in l or "yaw_deg" in l):
            warnings.append(f"{ctx}: spot_angle_deg / pitch_deg / yaw_deg only apply to spot lights")
    return errors, warnings
