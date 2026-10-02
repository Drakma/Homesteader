using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// What a building looks like follows what it was built from. A construction material whose manifest sets look_target (a comma list of
    /// roof, walls, interior, floor, chimney, foundation) with a colour, smoothness and metallic value (properties.look_*, edited in the asset
    /// kit) gives those parts of the building that look when a stage is built from it: birch logs make white-cream log walls, a paint its
    /// colour on the inside walls, carpet or tile the floor, corrugated steel a silver roof, a brick or field stone the chimney.
    /// A foundation item also names a style (look_style: poured, block, brick, stilts): the stage models hold the slab in an object called
    /// "Foundation", and for any other style ConstructionSite hides it and shows the matching variant model instead.
    /// The models name their materials (cabin: Log, Roof, Interior, Floor, Masonry; house: Siding, Shingle, ShingleDark, ...; variants:
    /// FoundationFace), which is what gets recoloured. ConstructionSite remembers the item ids that set the looks (saved with the site).
    /// </summary>
    public static class StructureLook
    {
        /// <summary>True when the item sets the look of at least one part; its catalog entry comes back in item.</summary>
        public static bool TryLook(string itemId, out AssetCatalogItem item)
        {
            item = HudBindings.GetCatalogItem(itemId);
            return item != null && !string.IsNullOrEmpty(item.look_target);
        }

        public static bool Styles(AssetCatalogItem item, string part)
        {
            if (item == null || string.IsNullOrEmpty(item.look_target)) return false;
            foreach (string t in item.look_target.Split(',')) if (t.Trim() == part) return true;
            return false;
        }

        /// <summary>The item that decides a part's look (the last one in the list that styles it), or null.</summary>
        public static AssetCatalogItem For(List<string> ids, string part)
        {
            AssetCatalogItem found = null;
            if (ids == null) return null;
            foreach (string id in ids)
                if (TryLook(id, out AssetCatalogItem item) && Styles(item, part)) found = item;
            return found;
        }

        /// <summary>The foundation style the items ask for: "block", "brick" or "stilts" (null for the poured slab or when none says).</summary>
        public static string FoundationStyle(List<string> ids)
        {
            AssetCatalogItem item = For(ids, "foundation");
            if (item == null || string.IsNullOrEmpty(item.look_style) || item.look_style == "poured") return null;
            return item.look_style;
        }

        /// <summary>Recolours the materials of a model according to the looks of the given items.</summary>
        public static void Apply(Transform root, List<string> lookItemIds)
        {
            if (root == null || lookItemIds == null || lookItemIds.Count == 0) return;
            AssetCatalogItem roof = For(lookItemIds, "roof"), walls = For(lookItemIds, "walls"), interior = For(lookItemIds, "interior"),
                             floor = For(lookItemIds, "floor"), chimney = For(lookItemIds, "chimney"), foundation = For(lookItemIds, "foundation");
            if (roof == null && walls == null && interior == null && floor == null && chimney == null && foundation == null) return;

            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    string name = Plain(mats[i].name);
                    AssetCatalogItem look = null;
                    if (name.StartsWith("Roof") || name.StartsWith("Shingle")) look = roof;
                    else if (name.StartsWith("Log") || name.StartsWith("Siding")) look = walls;
                    else if (name.StartsWith("Interior")) look = interior;
                    else if (name.StartsWith("Floor")) look = floor;
                    else if (name.StartsWith("Masonry")) look = chimney;
                    else if (name.StartsWith("FoundationFace")) look = foundation;
                    if (look == null) continue;
                    var m = new Material(mats[i]) { name = name };
                    Color c = Color.white;
                    ColorUtility.TryParseHtmlString(look.look_color, out c);
                    if (name.Contains("Dark")) c *= 0.65f;
                    c.a = 1f;
                    Set(m, c, look.look_smoothness, look.look_metallic);
                    mats[i] = m;
                    changed = true;
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        private static string Plain(string name)
        {
            int k = name.IndexOf(" (Instance)", System.StringComparison.Ordinal);
            return k >= 0 ? name.Substring(0, k) : name;
        }

        // glTFast's shader graph names its properties like glTF (baseColorFactor ...); a plain URP Lit material uses _BaseColor ...
        private static void Set(Material m, Color colour, float smoothness, float metallic)
        {
            if (m.HasProperty("baseColorFactor")) m.SetColor("baseColorFactor", colour);
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", colour);
            if (m.HasProperty("baseColorTexture")) m.SetTexture("baseColorTexture", null);   // a flat colour: the picture would tint it
            if (m.HasProperty("_BaseMap")) m.SetTexture("_BaseMap", null);
            if (m.HasProperty("metallicFactor")) m.SetFloat("metallicFactor", metallic);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", metallic);
            if (m.HasProperty("roughnessFactor")) m.SetFloat("roughnessFactor", 1f - smoothness);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", smoothness);
        }
    }
}
