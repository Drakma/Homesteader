import os
root = r"C:\Users\casey\Desktop\Homesteader\assets"
for cat in ["appliances", "tools", "food", "materials"]:
    p = os.path.join(root, cat)
    if os.path.exists(p):
        items = os.listdir(p)[:5]
        print(f"Sample items in {cat}:", items)
        for it in items[:2]:
            sub = os.path.join(p, it)
            if os.path.isdir(sub):
                print(f"  Files in {it}:", os.listdir(sub))
