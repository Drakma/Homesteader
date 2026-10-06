"""Resolves a schema's "uses" list of shared field sets into one flat "fields" object.

A category (or component) schema can say

    "uses": ["fuel:fuel_type", "power"]

which pulls fields from assets/_schemas/_fieldset_<name>.schema.json ("name" = every field of the set, "name:a,b" = only those). The schema's own
"fields" entry for the same name is merged ON TOP of the set's (its attributes win), so a category states only what differs: its own "required"
and "note". A field that only the set defines is added after the schema's own fields.

Every reader of a schema's fields (the server's validation, validate_schema.py, the item popup via /api/schema's "resolved_fields") goes through
resolve_schema(), so the rest of the code never sees "uses". A schema without "uses" is returned untouched.
"""
import json
import os

FIELDSET_PREFIX = "_fieldset_"


def load_fieldset(name, schemas_dir):
    path = os.path.join(schemas_dir, FIELDSET_PREFIX + name + ".schema.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_schema(schema, schemas_dir):
    """A copy of `schema` whose "fields" include everything it "uses" (or `schema` itself when it uses nothing)."""
    if not isinstance(schema, dict):
        return schema
    uses = schema.get("uses")
    if not uses:
        return schema
    shared = {}
    for entry in uses:
        name, _, only = str(entry).partition(":")
        try:
            fieldset = load_fieldset(name.strip(), schemas_dir)
        except (OSError, ValueError) as e:
            raise ValueError(f"field set '{name}' used by schema '{schema.get('category', '?')}' could not be loaded: {e}")
        wanted = [w.strip() for w in only.split(",") if w.strip()] if only else None
        for fname, spec in (fieldset.get("fields") or {}).items():
            if wanted is None or fname in wanted:
                shared[fname] = spec
        if wanted:
            missing = [w for w in wanted if w not in (fieldset.get("fields") or {})]
            if missing:
                raise ValueError(f"field set '{name}' has no field {', '.join(missing)} (used by schema '{schema.get('category', '?')}')")
    own = schema.get("fields") or {}
    fields = {}
    for fname, spec in own.items():
        fields[fname] = {**shared.get(fname, {}), **(spec if isinstance(spec, dict) else {})}
    for fname, spec in shared.items():
        if fname not in fields:
            fields[fname] = dict(spec)
    out = dict(schema)
    out["fields"] = fields
    return out
