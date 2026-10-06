"""
The construction recipe format, in one place (used by the kit server, the catalog generator, the migration and the reference checks).

A recipe (a structure stage's `construction_recipe`) is a LIST of nodes; the list as a whole means "all of these". A node is

    a LINE      {"item_id": "<item id | #tag | ~equivalency>", "quantity": N}   (+ "per_depth_m": M on a well: N + M x the well's depth)
    a SECTION   {"section": "Masonry", "mode": "all" | "any", "if": {...}, "items": [ nodes ... ]}

mode "all"  every node of the section is needed.
mode "any"  ANY ONE node of the section, in full (a node may itself be a section: "2 x A and 1 x B" is an all-section inside an any-section).
if          the section only applies when the condition holds, so "if you use bricks you also need mortar" is an if-section:
              {"if": {"uses": "#brick"}}       some earlier line of the recipe is paid with an item that matches the spec (an item id, #tag or ~equivalency)
              {"if": {"not_uses": "#brick"}}   no earlier line is paid with such an item
            (both keys together: both must hold). A section whose condition is false is shown but needs nothing.

The legacy `{"any_of": [lines]}` is read as an "any" section.
"""
MAX_DEPTH = 6


def is_section(node):
    return isinstance(node, dict) and isinstance(node.get("items"), list)


def from_legacy(node):
    """{"any_of": [...]} -> an "any" section; everything else unchanged."""
    if isinstance(node, dict) and isinstance(node.get("any_of"), list):
        return {"section": "", "mode": "any", "items": [from_legacy(o) for o in node["any_of"]]}
    return node


def normalize(raw):
    """Cleans a recipe: legacy any_of converted, quantities numbers, empty sections dropped, one-line "all" sections kept as written.
    Returns (nodes, error). The error text names the problem for the editor."""
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, "construction_recipe must be an array."
    return _norm_list(raw, 1)


def _norm_list(raw, depth):
    if depth > MAX_DEPTH:
        return None, "recipe sections are nested too deeply (at most %d levels)." % MAX_DEPTH
    out = []
    for node in raw:
        node = from_legacy(node)
        if not isinstance(node, dict):
            return None, "each recipe line must be an object."
        if "items" in node and isinstance(node.get("items"), list):
            mode = str(node.get("mode", "all")).strip().lower()
            if mode not in ("all", "any"):
                return None, "a section's mode must be 'all' or 'any'."
            children, err = _norm_list(node["items"], depth + 1)
            if err:
                return None, err
            if not children:
                continue                        # an empty section needs nothing: drop it
            sec = {"section": str(node.get("section", "")).strip(), "mode": mode}
            cond = node.get("if")
            if isinstance(cond, dict):
                c = {}
                for key in ("uses", "not_uses"):
                    v = str(cond.get(key, "")).strip()
                    if v:
                        c[key] = v
                if c:
                    sec["if"] = c
            sec["items"] = children
            out.append(sec)
            continue
        item_id = str(node.get("item_id", "")).strip()
        if not item_id:
            return None, "a recipe line has no item_id."
        try:
            qty = float(node.get("quantity", 1))
        except (TypeError, ValueError):
            return None, "the quantity of %s must be a number." % item_id
        if qty <= 0:
            return None, "the quantity of %s must be greater than 0." % item_id
        line = {"item_id": item_id, "quantity": int(qty) if qty.is_integer() else qty}
        try:
            per = float(node.get("per_depth_m", 0) or 0)
        except (TypeError, ValueError):
            return None, "the per_depth_m of %s must be a number." % item_id
        if per > 0:
            line["per_depth_m"] = per            # a well: quantity + per_depth_m x the well's depth (docs/WELLS.md)
        out.append(line)
    return out, None


def lines(nodes):
    """Every line (leaf) of a recipe, depth first."""
    for n in nodes or []:
        n = from_legacy(n)
        if is_section(n):
            yield from lines(n["items"])
        elif isinstance(n, dict) and n.get("item_id"):
            yield n


def specs(nodes):
    """Every spec a recipe names: the lines' item ids and the conditions' specs."""
    for n in nodes or []:
        n = from_legacy(n)
        if is_section(n):
            for key in ("uses", "not_uses"):
                v = (n.get("if") or {}).get(key)
                if v:
                    yield v
            yield from specs(n["items"])
        elif isinstance(n, dict) and n.get("item_id"):
            yield n["item_id"]


def for_game(nodes):
    """The shape the game's catalog holds (AssetCatalog.json construction_stages[].recipe): the same nodes with the condition flattened
    (JsonUtility cannot read a key called "if"): {"item_id", "quantity"} or {"section", "mode", "uses", "not_uses", "items": [...]}."""
    out = []
    for n in nodes or []:
        n = from_legacy(n)
        if is_section(n):
            cond = n.get("if") or {}
            out.append({"item_id": "", "quantity": 0, "section": str(n.get("section", "")), "mode": n.get("mode", "all"),
                        "uses": cond.get("uses", ""), "not_uses": cond.get("not_uses", ""), "items": for_game(n["items"])})
        elif isinstance(n, dict) and n.get("item_id"):
            out.append({"item_id": str(n["item_id"]), "quantity": float(n.get("quantity", 1) or 1), "per_depth_m": float(n.get("per_depth_m", 0) or 0)})
    return out
