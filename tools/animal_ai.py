"""Animal AI definitions (assets/_ai/*.json): list, validate, save.

Mirrors the game's parser (Assets/Scripts/Animals/AnimalAIDefinition.cs) so a definition that saves clean
here loads clean in game. See docs/ANIMAL_AI.md and assets/_schemas/animal_ai.schema.json.
"""
import json
import os
import re

ACTION_TYPES = {"idle", "wander", "goto", "follow", "flee", "rest", "emote", "consume", "sequence"}
NEEDS_TARGET = {"goto", "follow", "flee", "consume"}
TERM_KEYS = ("need", "time", "hours", "weather", "season", "sense", "current", "event", "random")
CURVES = {"linear", "inverse", "squared", "sqrt", "closer", "farther"}
TIME_WORDS = {"day", "night", "dawn", "dusk"}
WEATHER = {"sunny", "partlycloudy", "cloudy", "rain", "thunderstorm", "snow", "blizzard", "wind", "fog"}
SEASONS = {"spring", "summer", "autumn", "winter"}
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def ai_dir(base_dir):
    return os.path.join(base_dir, "_ai")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validate_term(t, ctx, needs, behavior_ids, errors, warnings):
    if not isinstance(t, dict):
        errors.append(f"{ctx}: a term must be an object")
        return
    kinds = [k for k in TERM_KEYS if k in t]
    if not kinds:
        errors.append(f"{ctx}: a term needs one of {', '.join(TERM_KEYS)}")
        return
    if len(kinds) > 1:
        warnings.append(f"{ctx}: a term has several kind keys ({', '.join(kinds)}); only the first is used")
    kind = kinds[0]
    if kind == "need":
        if t["need"] not in needs:
            errors.append(f"{ctx}: unknown need '{t['need']}'")
    elif kind == "time":
        if str(t["time"]).lower() not in TIME_WORDS:
            errors.append(f"{ctx}: time must be one of {sorted(TIME_WORDS)}")
    elif kind == "hours":
        h = t["hours"]
        if not (isinstance(h, list) and len(h) == 2 and all(_num(x) for x in h)):
            errors.append(f"{ctx}: hours must be [from, to]")
    elif kind in ("weather", "season"):
        vals = t[kind] if isinstance(t[kind], list) else [t[kind]]
        allowed = WEATHER if kind == "weather" else SEASONS
        for v in vals:
            if str(v).lower() not in allowed:
                warnings.append(f"{ctx}: unknown {kind} '{v}'")
    elif kind == "current":
        if t["current"] not in behavior_ids:
            errors.append(f"{ctx}: 'current' refers to unknown behavior '{t['current']}'")
    if "curve" in t and t["curve"] not in CURVES:
        errors.append(f"{ctx}: curve must be one of {sorted(CURVES)}")
    for k in ("above", "below", "within", "beyond", "weight"):
        if k in t and not _num(t[k]):
            errors.append(f"{ctx}: '{k}' must be a number")


def _validate_action(a, ctx, errors, warnings, animations):
    if not isinstance(a, dict):
        errors.append(f"{ctx}: action must be an object")
        return
    typ = a.get("type")
    if typ not in ACTION_TYPES:
        errors.append(f"{ctx}: unknown action type '{typ}' (use {', '.join(sorted(ACTION_TYPES))})")
        return
    if typ in NEEDS_TARGET and not a.get("target"):
        errors.append(f"{ctx}: '{typ}' needs a \"target\"")
    if typ == "sequence":
        steps = a.get("steps")
        if not (isinstance(steps, list) and steps):
            errors.append(f"{ctx}: 'sequence' needs a non-empty \"steps\" list")
        else:
            for i, s in enumerate(steps):
                _validate_action(s, f"{ctx}/step{i + 1}", errors, warnings, animations)
    anim = a.get("anim")
    if anim and animations is not None and anim not in animations:
        warnings.append(f"{ctx}: anim '{anim}' is not in this definition's \"animations\" map, so it is used as a raw clip name")
    d = a.get("duration")
    if d is not None and not (_num(d) or (isinstance(d, list) and len(d) == 2 and all(_num(x) for x in d))):
        errors.append(f"{ctx}: duration must be a number or [min, max]")


def _raw(base_dir, ai_id):
    """A definition file from assets/_ai (raw, no inheritance), or None."""
    if not base_dir or not ID_RE.match(ai_id or ""):
        return None
    path = os.path.join(ai_dir(base_dir), ai_id + ".json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def resolve(defn, base_dir, chain=None, problems=None):
    """Merges the `extends` chain under defn, like AnimalAIRegistry.Resolve in the game: needs / animations /
    senses / movement keys override by name, behaviours by id ({"id": x, "disabled": true} removes one)."""
    chain = set(chain or ())
    problems = problems if problems is not None else []
    out = {"needs": {}, "senses": {}, "movement": {}, "animations": {}, "behaviors": [], "tags": []}

    def overlay(src):
        for t in src.get("tags") or []:
            if t not in out["tags"]:
                out["tags"].append(t)
        out["needs"].update(src.get("needs") or {})
        out["senses"].update(src.get("senses") or {})
        out["movement"].update(src.get("movement") or {})
        out["animations"].update(src.get("animations") or {})
        for b in src.get("behaviors") or []:
            if not isinstance(b, dict):
                continue
            at = next((i for i, x in enumerate(out["behaviors"]) if x.get("id") == b.get("id")), -1)
            if b.get("disabled"):
                if at >= 0:
                    out["behaviors"].pop(at)
            elif at >= 0:
                out["behaviors"][at] = b
            else:
                out["behaviors"].append(b)

    did = defn.get("id")
    if did:
        chain.add(did)
    for pid in defn.get("extends") or []:
        if pid in chain:
            problems.append("circular extends: '" + pid + "'")
            continue
        parent = _raw(base_dir, pid)
        if parent is None:
            problems.append("extends unknown definition '" + pid + "' (looked in assets/_ai)")
            continue
        overlay(resolve(parent, base_dir, chain, problems))
    overlay(defn)
    return out


MEDIUMS = {"ground", "water", "air"}


def validate(defn, base_dir=None):
    """Returns (errors, warnings). Errors block saving; warnings are advisory.
    base_dir lets `extends` find its parents in assets/_ai."""
    errors, warnings = [], []
    if not isinstance(defn, dict):
        return ["definition must be a JSON object"], warnings
    did = defn.get("id")
    if not isinstance(did, str) or not ID_RE.match(did):
        errors.append("\"id\" is required, lower snake_case (letters, digits, underscore; starts with a letter)")
    applies = defn.get("applies_to")
    if defn.get("abstract"):
        if applies is not None and not (isinstance(applies, list) and all(isinstance(x, str) for x in applies)):
            errors.append("\"applies_to\" must be a list of item ids or \"species:<name>\"")
    elif not (isinstance(applies, list) and applies and all(isinstance(x, str) for x in applies)):
        errors.append("\"applies_to\" must be a non-empty list of item ids or \"species:<name>\" (or set \"abstract\": true for a template)")
    tg = defn.get("tags")
    if tg is not None and not (isinstance(tg, list) and all(isinstance(x, str) for x in tg)):
        errors.append("\"tags\" must be a list of strings")
    ext = defn.get("extends")
    if ext is not None and not (isinstance(ext, list) and all(isinstance(x, str) for x in ext)):
        errors.append("\"extends\" must be a list of definition ids")
        ext = []
    problems = []
    merged = resolve(defn, base_dir, problems=problems) if ext else None
    for pr in problems:
        (errors if pr.startswith("circular") else warnings).append(pr)

    needs = defn.get("needs", {})
    if not isinstance(needs, dict):
        errors.append("\"needs\" must be an object")
        needs = {}
    all_needs = dict(merged["needs"]) if merged else needs
    for name, n in needs.items():
        if not isinstance(n, dict):
            errors.append(f"need '{name}' must be an object")
            continue
        for k in ("start", "rate_per_game_hour", "min", "max"):
            if k in n and not _num(n[k]):
                errors.append(f"need '{name}': '{k}' must be a number")

    mv = defn.get("movement")
    if isinstance(mv, dict):
        if "medium" in mv and str(mv["medium"]).lower() not in MEDIUMS:
            errors.append("movement.medium must be one of " + ", ".join(sorted(MEDIUMS)))
        for k in ("walk_speed", "run_speed", "turn_speed_deg", "max_slope_deg", "arrive_dist_m", "hover_m", "depth_m", "walk_native_mps", "run_native_mps"):
            if k in mv and not _num(mv[k]):
                errors.append("movement." + k + " must be a number")
    animations = defn.get("animations", {})
    if animations is not None and not isinstance(animations, dict):
        errors.append("\"animations\" must be an object mapping slot -> clip name")
        animations = {}

    all_anims = dict(merged["animations"]) if merged else (animations or {})

    behaviors = defn.get("behaviors")
    if behaviors is None and merged:
        behaviors = []
    if not isinstance(behaviors, list) or (not behaviors and not (merged and merged["behaviors"])):
        errors.append("\"behaviors\" must be a non-empty list (or inherited through \"extends\")")
        return errors, warnings
    all_ids = [b.get("id") for b in (merged["behaviors"] if merged else behaviors) if isinstance(b, dict)]

    ids = []
    for b in behaviors:
        bid = b.get("id") if isinstance(b, dict) else None
        if not isinstance(bid, str) or not bid:
            errors.append("every behavior needs an \"id\"")
        elif bid in ids:
            errors.append(f"duplicate behavior id '{bid}'")
        else:
            ids.append(bid)

    for b in behaviors:
        if not isinstance(b, dict) or b.get("disabled"):
            continue
        ctx = f"behavior '{b.get('id')}'"
        _validate_action(b.get("action"), ctx + "/action", errors, warnings, all_anims)
        for key in ("requires", "score"):
            for i, t in enumerate(b.get(key, []) or []):
                _validate_term(t, f"{ctx}/{key}[{i}]", all_needs, all_ids, errors, warnings)
        until = (b.get("action") or {}).get("until") if isinstance(b.get("action"), dict) else None
        if until is not None:
            _validate_term(until, ctx + "/until", all_needs, all_ids, errors, warnings)
        for k in ("base", "cooldown_s", "min_s", "priority"):
            if k in b and not _num(b[k]):
                errors.append(f"{ctx}: '{k}' must be a number")
        if not b.get("requires") and not b.get("score"):
            warnings.append(f"{ctx}: no requires or score, so it always scores exactly its \"base\"")
    return errors, warnings


def list_profiles(base_dir):
    """Every definition in assets/_ai with a validation summary (for the kit's AI dropdown)."""
    out = []
    d = ai_dir(base_dir)
    if not os.path.isdir(d):
        return out
    for fname in sorted(os.listdir(d)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(d, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                defn = json.load(f)
        except Exception as e:
            out.append({"id": fname[:-5], "file": fname, "valid": False, "error": str(e), "applies_to": [], "behaviors": 0})
            continue
        errors, warnings = validate(defn, base_dir)
        out.append({
            "abstract": bool(defn.get("abstract")),
            "extends": defn.get("extends", []),
            "id": defn.get("id", fname[:-5]),
            "file": fname,
            "applies_to": defn.get("applies_to", []),
            "behaviors": len(defn.get("behaviors", []) or []),
            "needs": list((defn.get("needs") or {}).keys()),
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        })
    return out


def get_profile(base_dir, ai_id):
    path = os.path.join(ai_dir(base_dir), f"{ai_id}.json")
    if not ID_RE.match(ai_id or "") or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(base_dir, defn):
    """Validates and writes assets/_ai/<id>.json. Returns (ok, errors, warnings)."""
    errors, warnings = validate(defn, base_dir)
    if errors:
        return False, errors, warnings
    os.makedirs(ai_dir(base_dir), exist_ok=True)
    path = os.path.join(ai_dir(base_dir), f"{defn['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(defn, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return True, [], warnings


if __name__ == "__main__":
    import sys
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
    bad = 0
    for p in list_profiles(base):
        print(("OK   " if p.get("valid") else "FAIL ") + p["id"], f"({p['behaviors']} behaviors)")
        for e in p.get("errors", []) or [p.get("error", "")]:
            if e:
                print("   error:", e)
                bad += 1
        for w in p.get("warnings", []):
            print("   warn: ", w)
    sys.exit(1 if bad else 0)
