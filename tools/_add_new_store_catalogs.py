import json, os

catalog_path = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\StoreCatalogs.json"
db = json.load(open(catalog_path, "r", encoding="utf-8"))

assets_root = r"C:\Users\casey\Desktop\Homesteader\assets"

def make_item(cat, item_id, override_cat=None, override_name=None, override_price=None):
    mf = os.path.join(assets_root, cat, item_id, f"{item_id}.json")
    if os.path.isfile(mf):
        d = json.load(open(mf, "r", encoding="utf-8"))
        if d.get("properties", {}).get("is_buyable") is not True:
            return None          # stores only stock is_buyable items
        return {
            "id": d.get("id", item_id),
            "name": override_name or d.get("name", item_id.replace("_", " ").title()),
            "category": override_cat or cat.capitalize(),
            "price": float(override_price or d.get("properties", {}).get("base_value", 50.0)),
            "unit": "ea",
            "description": d.get("description", ""),
            "icon": f"{item_id}.png",
            "v_type": ""
        }
    return None

# 1. Voltvision items (Electricity + Internet)
voltvision_items = []
for item_id in sorted(os.listdir(os.path.join(assets_root, "electricity"))):
    it = make_item("electricity", item_id, override_cat="Electronics")
    if it: voltvision_items.append(it)

for item_id in sorted(os.listdir(os.path.join(assets_root, "internet"))):
    it = make_item("internet", item_id, override_cat="Telecom")
    if it: voltvision_items.append(it)

# 2. Trailer Shack items (Trailers, Towing, Heavy Transport, Repair Tools)
trailershack_items = []
trailer_ids = [
    ("vehicles", "vehicle_trailer_utility_small", "Trailers", "Trailer Shack Utility 5x8", 1200.0),
    ("vehicles", "vehicle_trailer_utility_large", "Trailers", "Trailer Shack Heavy Flatbed 8x18", 3200.0),
    ("vehicles", "vehicle_trailer_livestock_small", "Trailers", "Trailer Shack Single-Axle Stock Hauler", 4500.0),
    ("vehicles", "vehicle_trailer_livestock_large", "Trailers", "Trailer Shack Gooseneck Cattle Hauler", 12000.0),
    ("vehicles", "vehicle_trailer_horse", "Trailers", "Trailer Shack Deluxe 2-Horse Slant Hauler", 9500.0),
    ("tools", "tool_chain_choker_logging", "Secure Towing", "Grade 70 Transport Binder Chain (20ft)", 145.0),
    ("tools", "tool_tongs_skidding_logging", "Secure Towing", "Heavy Forged Hauling Timber Tongs", 85.0),
    ("tools", "tool_cord_shore_power_50a", "Trailer Parts", "50-Amp RV & Trailer Shore Power Cable", 195.0),
    ("tools", "tool_impact_driver_cordless", "Trailer Repair", "Cordless High-Torque Lug Impact Wrench", 220.0),
    ("tools", "tool_angle_grinder_cordless", "Trailer Repair", "Cordless Frame & Metal Angle Grinder", 165.0),
    ("tools", "tool_wrench_adjustable", "Trailer Repair", "Wide-Capacity Adjustable Hitch Wrench", 35.0),
    ("tools", "tool_wrench_pipe", "Trailer Repair", "Heavy Duty Cast Iron Pipe Wrench 18-Inch", 48.0),
    ("tools", "tool_hammer_club", "Trailer Repair", "4-lb Forged Steel Club Drilling Hammer", 32.0),
    ("fuel", "fuel_can_diesel_5gal", "Transport Accessories", "5-Gallon Heavy Duty Yellow Diesel Jerry Can", 45.0),
    ("fuel", "fuel_gasoline", "Transport Accessories", "Fuel Transfer Pump & 5-Gal Gas Can", 55.0)
]

for cat, item_id, o_cat, o_name, o_price in trailer_ids:
    it = make_item(cat, item_id, override_cat=o_cat, override_name=o_name, override_price=o_price)
    if it: trailershack_items.append(it)

db["voltvision"] = voltvision_items
db["trailershack"] = trailershack_items

with open(catalog_path, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print(f"Added {len(voltvision_items)} items to voltvision and {len(trailershack_items)} items to trailershack.")

