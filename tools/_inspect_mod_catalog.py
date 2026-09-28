import os
import json

root = r"C:\Users\casey\Desktop\Homesteader\mods"

# Categories needed:
# 1. Tank You: fuel
# 2. Board Meeting: logging
# 3. Nail It: materials, building, tools
# 4. Hay There: ranching
# 5. Lettuce Shop: food, ingredients
# 6. Shift Happens: personal vehicles (cars, trucks, motorcycles)
# 7. Drafting Behind You: structures
# 8. Tractor Beam: farming vehicles / equipment
# 9. Sofa So Good: appliances (and furniture)

cats = ["fuel", "logging", "materials", "building", "tools", "ranching", "food", "ingredients", "vehicles", "structures", "appliances"]

for cat in cats:
    mod_dir = os.path.join(root, "homesteader", cat)
    if os.path.exists(mod_dir):
        items = [d for d in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, d))]
        print(f"\nCategory [{cat}] ({len(items)} items):")
        # print first 6 items with their manifest names
        for it in items[:6]:
            mf = os.path.join(mod_dir, it, f"{it}.json")
            name = it
            if os.path.exists(mf):
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        name = d.get("name", it)
                except:
                    pass
            print(f"   {it} -> {name}")
