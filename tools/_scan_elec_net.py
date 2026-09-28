import os, json

def scan_category(cat):
    base_dir = os.path.join(r"C:\Users\casey\Desktop\Homesteader\assets", cat)
    items = []
    if not os.path.isdir(base_dir):
        return items
    for item_id in sorted(os.listdir(base_dir)):
        item_dir = os.path.join(base_dir, item_id)
        if not os.path.isdir(item_dir):
            continue
        manifest_file = os.path.join(item_dir, f"{item_id}.json")
        if os.path.isfile(manifest_file):
            try:
                data = json.load(open(manifest_file, "r", encoding="utf-8"))
                items.append({
                    "id": data.get("id", item_id),
                    "name": data.get("name", item_id.replace("_", " ").title()),
                    "category": cat.capitalize(),
                    "price": float(data.get("properties", {}).get("base_value", 50.0)),
                    "unit": "ea",
                    "description": data.get("description", "Quality homestead hardware."),
                    "icon": f"{item_id}.png",
                    "v_type": ""
                })
            except Exception as e:
                print(f"Error {manifest_file}: {e}")
    return items

elec_items = scan_category("electricity")
net_items = scan_category("internet")
print(f"Found {len(elec_items)} electricity items and {len(net_items)} internet items.")
for it in elec_items[:5]:
    print(" ", it["id"], it["name"], it["price"])
for it in net_items[:5]:
    print(" ", it["id"], it["name"], it["price"])

