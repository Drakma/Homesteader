#!/usr/bin/env python3
"""Validate every item manifest in a category against that category's
optional schema file in assets/_schemas/<category>.schema.json.

A category with no schema file yet passes trivially (nothing to check) -
schemas get added one field at a time as real needs come up, not all
up front. See assets/_schemas/README.md.

Usage:
  py -3 validate_schema.py <category>
  py -3 validate_schema.py appliances
"""
import glob
import json
import os
import sys

# tools/ sits at the repo root, so one level up is the project root.
ASSETS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SCHEMAS_DIR = os.path.join(ASSETS_ROOT, "_schemas")

PY_TYPE = {"object": dict, "string": str, "number": (int, float), "boolean": bool, "array": list}


def check_value(value, spec, path):
    errors = []
    expected = spec["type"] if isinstance(spec, dict) else spec
    py_type = PY_TYPE.get(expected)
    if py_type is None:
        return errors
    if not isinstance(value, py_type) or isinstance(value, bool) and py_type is not bool:
        errors.append(f"{path}: expected {expected}, got {type(value).__name__}")
        return errors
    if expected == "number" and isinstance(spec, dict):
        if "min" in spec and value < spec["min"]:
            errors.append(f"{path}: {value} is below min {spec['min']}")
        if "max" in spec and value > spec["max"]:
            errors.append(f"{path}: {value} is above max {spec['max']}")
    if expected == "object" and isinstance(spec, dict) and "properties" in spec:
        for prop_name, prop_type in spec["properties"].items():
            if prop_name not in value:
                errors.append(f"{path}.{prop_name}: missing")
            else:
                errors.extend(check_value(value[prop_name], prop_type, f"{path}.{prop_name}"))
    if expected == "array" and isinstance(spec, dict) and "items" in spec:
        for i, elem in enumerate(value):
            errors.extend(check_value(elem, spec["items"], f"{path}[{i}]"))
    return errors


def validate_item(manifest, schema):
    errors = []
    target_key = schema.get("target", "category_fields")
    target = manifest.get(target_key, {})
    for field_name, field_spec in schema.get("fields", {}).items():
        if field_name not in target:
            if field_spec.get("required"):
                errors.append(f"{target_key}.{field_name}: missing (required)")
            continue
        errors.extend(check_value(target[field_name], field_spec, f"{target_key}.{field_name}"))
    return errors


def load_schemas(category):
    schemas = []
    for base_path in sorted(glob.glob(os.path.join(SCHEMAS_DIR, "_base*.schema.json"))):
        with open(base_path, "r", encoding="utf-8") as f:
            schemas.append(json.load(f))
    cat_path = os.path.join(SCHEMAS_DIR, f"{category}.schema.json")
    if os.path.exists(cat_path):
        with open(cat_path, "r", encoding="utf-8") as f:
            schemas.append(json.load(f))
    return schemas


def main(category):
    schemas = load_schemas(category)
    if not schemas:
        print(f"No schema defined yet for '{category}' - nothing to check.")
        return 0

    pattern = os.path.join(ASSETS_ROOT, category, "*", "*.json")
    manifest_paths = sorted(glob.glob(pattern))
    if not manifest_paths:
        print(f"No item manifests found under assets/{category}/")
        return 1

    total_errors = 0
    failed_items = 0
    for path in manifest_paths:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        # A growth group (is_growable) is checked against growth_group.schema.json by the server, never against the item schemas: its stages are the items.
        if isinstance(manifest, dict) and manifest.get("is_growable"):
            continue
        errors = []
        for schema in schemas:
            errors.extend(validate_item(manifest, schema))
        if errors:
            total_errors += len(errors)
            failed_items += 1
            item_id = manifest.get("id", os.path.basename(path))
            print(f"[FAIL] {item_id}")
            for e in errors:
                print(f"    {e}")

    checked = len(manifest_paths)
    print(f"\n{checked - failed_items}/{checked} items pass schema '{category}'")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py -3 validate_schema.py <category>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
