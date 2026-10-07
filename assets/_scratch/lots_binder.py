import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader')
S = 'Homesteader/Assets/Scripts/'


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


edit(S + 'UI/HudBindings.cs', [("        public float lot_m2_per_item;", "        public float lot_m2_per_item;\n        public string lot_binder_item;                              // a lot that is a MIX (asphalt: aggregate + bitumen): the second material, an item id or a ~equivalency\n        public float lot_binder_m2_per_item;                        // square metres one unit of the binder covers")])

edit(S + 'Growth/LotBuilder.cs', [
    # TryComplete: the needs
    ("""            float per = Mathf.Max(0.5f, item.lot_m2_per_item);
            int items = Mathf.Max(1, Mathf.CeilToInt(area / per - 0.001f));
            string material = string.IsNullOrEmpty(item.lot_material_item) ? _itemId : item.lot_material_item;
            int have = FenceBuilder.Available(material, _pts[0]);
            if (have < items)
            {
                ToastNotificationSystem.ShowWarning("Not enough materials", $"This lot needs {items} x {HudBindings.GetItemName(material)} (you have {have} in the toolbar and at the work site).");
                return;
            }
            string id = _itemId;
            Vector3 first = _pts[0];
            Reset();
            StartCoroutine(LayWalk(item, material, poly, items, first));""",
     """            List<Need> needs = NeedsOf(item, _itemId);
            foreach (Need n in needs)
            {
                int items = n.UnitsFor(area), have = Available(n.Spec, _pts[0]);
                if (have < items)
                {
                    ToastNotificationSystem.ShowWarning("Not enough materials", $"This lot needs {items} x {NameOf(n.Spec)} (you have {have} in the toolbar and at the work site).");
                    return;
                }
            }
            Vector3 first = _pts[0];
            Reset();
            StartCoroutine(LayWalk(item, needs, poly, first));"""),
    ("private System.Collections.IEnumerator LayWalk(AssetCatalogItem item, string material, List<Vector3> poly, int items, Vector3 site)",
     "private System.Collections.IEnumerator LayWalk(AssetCatalogItem item, List<Need> needs, List<Vector3> poly, Vector3 site)"),
    ("                    float seconds = Mathf.Clamp(2f + items * 0.25f, 2f, 14f);", "                    float seconds = Mathf.Clamp(2f + needs[0].UnitsFor(LotRun.PolygonArea(poly)) * 0.25f, 2f, 14f);"),
    ("""                if (FenceBuilder.Available(material, site) < items)
                    ToastNotificationSystem.ShowWarning("Out of materials", "The lot needs " + items + " x " + HudBindings.GetItemName(material) + ".");
                else
                {
                    FenceBuilder.Take(material, items, site);""",
     """                float area = LotRun.PolygonArea(poly);
                string lacking = null;
                foreach (Need n in needs) if (Available(n.Spec, site) < n.UnitsFor(area)) { lacking = n.UnitsFor(area) + " x " + NameOf(n.Spec); break; }
                if (lacking != null)
                    ToastNotificationSystem.ShowWarning("Out of materials", "The lot needs " + lacking + ".");
                else
                {
                    foreach (Need n in needs) TakeUnits(n.Spec, n.UnitsFor(area), site);"""),
    # panel
    ("""            float per = Mathf.Max(0.5f, item.lot_m2_per_item);
            int items = area > 0f ? Mathf.Max(1, Mathf.CeilToInt(area / per - 0.001f)) : 0;
            string material = string.IsNullOrEmpty(item.lot_material_item) ? _itemId : item.lot_material_item;
            Vector3 first = _pts.Count > 0 ? _pts[0] : Vector3.zero;""",
     """            List<Need> needs = NeedsOf(item, _itemId);
            Vector3 first = _pts.Count > 0 ? _pts[0] : Vector3.zero;
            string list = "";
            foreach (Need n in needs)
                list += (list.Length > 0 ? ", " : "") + (_pts.Count > 0 && area > 0f ? $"{NameOf(n.Spec)}: {n.UnitsFor(area)} of {Available(n.Spec, first)}" : NameOf(n.Spec) + ": one per " + UnitFormat.Area(n.M2));"""),
    ("""            _l2.text = _pts.Count > 0 ? $"{HudBindings.GetItemName(material)}: {items} of {FenceBuilder.Available(material, first)}" : HudBindings.GetItemName(material) + ": one per " + UnitFormat.Area(per);""",
     "            _l2.text = list;"),
    # helpers, before the 'breaking one up' section
    ("        // ------------------------------------------------------------------ breaking one up", """        // ------------------------------------------------------------------ the materials

        /// <summary>One material of a lot: an item id, or a ~equivalency (any mix of its members: the bucket or a pallet of them), and the area one unit of it covers.</summary>
        private struct Need
        {
            public string Spec;
            public float M2;
            public int UnitsFor(float area) { return Mathf.Max(1, Mathf.CeilToInt(area / Mathf.Max(0.5f, M2) - 0.001f)); }
        }

        private static List<Need> NeedsOf(AssetCatalogItem item, string fallback)
        {
            var list = new List<Need> { new Need { Spec = string.IsNullOrEmpty(item.lot_material_item) ? fallback : item.lot_material_item, M2 = item.lot_m2_per_item } };
            if (!string.IsNullOrEmpty(item.lot_binder_item))
                list.Add(new Need { Spec = item.lot_binder_item, M2 = item.lot_binder_m2_per_item > 0f ? item.lot_binder_m2_per_item : item.lot_m2_per_item });
            return list;
        }

        private static string NameOf(string spec) { return GrowthRegistry.IsEquivalency(spec) ? GrowthRegistry.EquivalencyLabel(spec) : HudBindings.GetItemName(spec); }

        private static float ValueOf(string spec, string id)
        {
            if (!GrowthRegistry.IsEquivalency(spec)) return string.Equals(spec, id, System.StringComparison.OrdinalIgnoreCase) ? 1f : 0f;
            return GrowthRegistry.EquivalencyValue(spec.Substring(1), id);
        }

        /// <summary>Every item id on hand (the toolbar and the work site) that counts towards a spec, with what one of it is worth.</summary>
        private static Dictionary<string, float> Members(string spec, Vector3 site)
        {
            var ids = new HashSet<string>();
            HudState hud = HudState.Active;
            if (hud != null) { hud.EnsureToolbarSlots(); foreach (ToolbarSlotData s in hud.Toolbar) if (s.Count > 0 && !string.IsNullOrEmpty(s.IconId)) ids.Add(s.IconId); }
            foreach (WorldItem w in WorldItem.All) if (w != null && FenceBuilder.InSite(site, w.transform.position)) ids.Add(w.ItemId);
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !FenceBuilder.InSite(site, o.transform.position)) continue;
                ids.Add(o.ItemId);
                if (o.Contents != null) foreach (ContainerStack cs in o.Contents) ids.Add(cs.ItemId);
            }
            var found = new Dictionary<string, float>();
            foreach (string id in ids) { float v = ValueOf(spec, id); if (v > 0f) found[id] = v; }
            return found;
        }

        private static int Available(string spec, Vector3 site)
        {
            float units = 0f;
            foreach (KeyValuePair<string, float> m in Members(spec, site)) units += m.Value * FenceBuilder.Available(m.Key, site);
            return Mathf.FloorToInt(units + 0.001f);
        }

        /// <summary>Uses up `units` of a spec: the small members first, then the smallest pack that covers the rest (a pallet), and what is left of that pack is put back as singles.</summary>
        private static void TakeUnits(string spec, int units, Vector3 site)
        {
            Dictionary<string, float> members = Members(spec, site);
            var order = new List<KeyValuePair<string, float>>(members);
            order.Sort((a, b) => a.Value.CompareTo(b.Value));
            string single = order.Count > 0 ? order[0].Key : null;
            float singleValue = order.Count > 0 ? order[0].Value : 1f;
            float remaining = units;
            foreach (KeyValuePair<string, float> m in order)
            {
                if (remaining <= 0.001f) break;
                int have = FenceBuilder.Available(m.Key, site);
                int need = Mathf.CeilToInt(remaining / m.Value - 0.001f);
                int take = Mathf.Min(have, need);
                if (take <= 0) continue;
                // a pack bigger than what is still owed is broken: take it whole and give the change back as singles
                FenceBuilder.Take(m.Key, take, site);
                float paid = take * m.Value;
                if (paid > remaining + 0.001f && single != null)
                {
                    int change = Mathf.FloorToInt((paid - remaining) / singleValue + 0.001f);
                    for (int i = 0; i < change; i++) WorldItem.TryDrop(single, site + new Vector3(0.3f * (i % 4) - 0.45f, 0.5f, 0.3f * (i / 4)));
                }
                remaining -= paid;
            }
        }

        // ------------------------------------------------------------------ breaking one up"""),
])

edit('tools/generate_unity_asset_catalog.py', [('                            item_data["lot_m2_per_item"] = float(props.get("lot_m2_per_item", 3.0))',
                                                '                            item_data["lot_m2_per_item"] = float(props.get("lot_m2_per_item", 3.0))\n                            if props.get("lot_binder_item"):   # a lot that is a mix (asphalt: gravel and bitumen)\n                                item_data["lot_binder_item"] = str(props["lot_binder_item"])\n                                item_data["lot_binder_m2_per_item"] = float(props.get("lot_binder_m2_per_item", props.get("lot_m2_per_item", 3.0)))')])
edit('assets/_schemas/_base_fences_paths.schema.json', [('    "path_material_item": {', '''    "lot_binder_item": {
      "type": "string",
      "required": false,
      "default": "",
      "label": "Lot Binder",
      "note": "On a lot blueprint that is a MIX (asphalt: gravel aggregate and bitumen): the second material, an item id or a ~equivalency (~bitumen is a bucket, or a pallet of 10 or 20)."
    },
    "lot_binder_m2_per_item": {
      "type": "number",
      "required": false,
      "default": 3.0,
      "min": 0.5,
      "label": "Square Metres Per Binder",
      "note": "The area one unit of the binder covers."
    },
    "path_material_item": {''')])
edit('tools/make_lot_blueprints.py', [
    ("m2=6.0, price=650, fill=(52, 52, 58)", "m2=6.0, binder='~bitumen', binder_m2=4.0, price=650, fill=(52, 52, 58)"),
    ("            'lot_style': c['style'], 'lot_material_item': c['material'], 'lot_m2_per_item': c['m2'],\n        },",
     "            'lot_style': c['style'], 'lot_material_item': c['material'], 'lot_m2_per_item': c['m2'],\n            **({'lot_binder_item': c['binder'], 'lot_binder_m2_per_item': c['binder_m2']} if c.get('binder') else {}),\n        },"),
])
print('ok')
