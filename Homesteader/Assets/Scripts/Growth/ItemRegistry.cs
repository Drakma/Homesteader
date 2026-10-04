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
            public bool Placeable;   // the manifest's properties.placeable: can the player put it on the ground (opt in, default no)
            public List<LightDef> Lights = new List<LightDef>();   // lights the asset emits (manifest "lights")
            public string AttachSurface = "";      // the manifest's properties.attach_surface: "wall" or "ceiling" = it mounts on a building (AttachController), "" = it does not
            public string AttachSide = "either";   // properties.attach_side: interior | exterior | either (wall mounts)
            public bool ProvidesPower;             // properties.provides_power: mounted on the outside of a building it brings electricity to it
        }

        private static readonly Dictionary<string, ItemInfo> items =
            new Dictionary<string, ItemInfo>(StringComparer.OrdinalIgnoreCase);

        public static void Clear() => items.Clear();

        /// <summary>First registration of an id wins (core content is loaded first).</summary>
        public static void Register(string id, string name, string category, GameObject prefab, List<LightDef> lights = null, bool placeable = true,
                                    string attachSurface = "", string attachSide = "either", bool providesPower = false)
        {
            if (string.IsNullOrEmpty(id) || prefab == null || items.ContainsKey(id)) return;
            items[id] = new ItemInfo
            {
                Id = id, Name = name, Category = category, Prefab = prefab, Lights = lights ?? new List<LightDef>(),
                AttachSurface = attachSurface ?? "", AttachSide = string.IsNullOrEmpty(attachSide) ? "either" : attachSide, ProvidesPower = providesPower,
                Placeable = placeable && string.IsNullOrEmpty(attachSurface),   // a thing that mounts on a wall or ceiling is not put on the ground
            };
        }

        public static bool TryGet(string id, out ItemInfo info)
        {
            info = null;
            return !string.IsNullOrEmpty(id) && items.TryGetValue(id, out info);
        }
    }
}
