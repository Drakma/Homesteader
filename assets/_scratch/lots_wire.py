import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')
S = 'Homesteader/Assets/Scripts/'


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:60])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


edit(S + 'UI/HudBindings.cs', [("                        else if (Homesteader.Growth.PathBuilder.CancelPlan()) { }",
                                "                        else if (Homesteader.Growth.PathBuilder.CancelPlan()) { }\n                        else if (Homesteader.Growth.LotBuilder.CancelPlan()) { }")])
edit(S + 'Save/GameSave.cs', [
    ("        public List<SavedPath> paths = new List<SavedPath>();", "        public List<SavedLot> lots = new List<SavedLot>();          // lots the player laid (LotRun)\n        public List<SavedPath> paths = new List<SavedPath>();"),
    ("        [Serializable] public struct SavedPath {", "        [Serializable] public struct SavedLot { public string style, itemId; public List<Vector3> points; }\n        [Serializable] public struct SavedPath {"),
])
edit(S + 'Save/GameSaveManager.cs', [
    ("            PathRun.Clear();", "            PathRun.Clear();\n            LotRun.Clear();"),
    ("            foreach (PathRun pr in PathRun.All)\n            {", "            foreach (LotRun lr in LotRun.All)\n                if (lr != null) s.lots.Add(new GameSave.SavedLot { style = lr.Style, itemId = lr.ItemId, points = new List<Vector3>(lr.Points) });\n            foreach (PathRun pr in PathRun.All)\n            {"),
    ("            // fences\n            foreach (GameSave.SavedFence sf in s.fences)", "            // lots\n            foreach (GameSave.SavedLot sl in s.lots)\n                if (sl.points != null && sl.points.Count >= 3) LotRun.Create(sl.style, sl.itemId, sl.points);\n\n            // fences\n            foreach (GameSave.SavedFence sf in s.fences)"),
])
edit('tools/generate_unity_asset_catalog.py', [('                        if props.get("path_material_item"):',
                                                '                        if props.get("lot_style") in ("dirt", "gravel", "asphalt", "concrete"):   # a lot blueprint (LotBuilder.cs)\n                            item_data["lot_style"] = props["lot_style"]\n                            item_data["lot_material_item"] = str(props.get("lot_material_item", ""))\n                            item_data["lot_m2_per_item"] = float(props.get("lot_m2_per_item", 3.0))\n                        if props.get("path_material_item"):')])
edit('assets/_schemas/_base_fences_paths.schema.json', [('    "path_material_item": {', '''    "lot_style": {
      "type": "string",
      "required": false,
      "default": "",
      "label": "Lot Surface",
      "enum": ["", "dirt", "gravel", "asphalt", "concrete"],
      "note": "On a LOT blueprint: the surface it lays over an area of any size and shape (the player clicks the corners; two corners make a rectangle). docs/LOTS.md."
    },
    "lot_material_item": {
      "type": "string",
      "required": false,
      "default": "",
      "label": "Lot Material",
      "note": "On a lot blueprint: the item id of the material it lays (one per lot_m2_per_item square metres), taken from the hotbar or the work site."
    },
    "lot_m2_per_item": {
      "type": "number",
      "required": false,
      "default": 3.0,
      "min": 0.5,
      "label": "Square Metres Per Item",
      "note": "On a lot blueprint: the area one item of its material covers; a lot of A square metres uses ceil(A / this) items."
    },
    "path_material_item": {''')])
print('ok')
