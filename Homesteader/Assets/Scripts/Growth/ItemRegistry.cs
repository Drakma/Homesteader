using System;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Every mod asset that resolved a model, keyed by item id, so a toolbar item can be shown in the
    /// world (dropped on the ground). ModLoader is the only writer; gameplay code only reads.
    /// </summary>
    public static class ItemRegistry
    {
        public sealed class ItemInfo
        {
            public string Id;
            public string Name;
            public string Category;
            public GameObject Prefab;   // a lazily-loaded GLB template (inactive) or a generated prefab
            public bool Placeable = true;   // the manifest's properties.placeable: can the player put it on the ground (default yes)
            public List<LightDef> Lights = new List<LightDef>();   // lights the asset emits (manifest "lights")
        }

        private static readonly Dictionary<string, ItemInfo> items =
            new Dictionary<string, ItemInfo>(StringComparer.OrdinalIgnoreCase);

        public static void Clear() => items.Clear();

        /// <summary>First registration of an id wins (core content is loaded first).</summary>
        public static void Register(string id, string name, string category, GameObject prefab, List<LightDef> lights = null, bool placeable = true)
        {
            if (string.IsNullOrEmpty(id) || prefab == null || items.ContainsKey(id)) return;
            items[id] = new ItemInfo { Id = id, Name = name, Category = category, Prefab = prefab, Placeable = placeable, Lights = lights ?? new List<LightDef>() };
        }

        public static bool TryGet(string id, out ItemInfo info)
        {
            info = null;
            return !string.IsNullOrEmpty(id) && items.TryGetValue(id, out info);
        }
    }
}
