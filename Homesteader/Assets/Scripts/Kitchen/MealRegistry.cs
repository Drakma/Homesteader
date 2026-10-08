using System;
using System.Collections.Generic;
using Homesteader.Modding;
using Homesteader.UI;

namespace Homesteader.Kitchen
{
    /// <summary>One meal: what a kitchen needs to make it and what it makes. Mod data (content type "meal", docs/COOKING.md, tools/meal_format.py).</summary>
    public sealed class MealDef
    {
        public string Id;
        public string Name;                                  // shown in the list (the result's name when the file gives none)
        public string Group = "Cooking";                     // the heading it is listed under
        public string ResultId;                              // the item made (for a filled container: the container, so its icon and name show)
        public int ResultQty = 1;
        public string ResultContainer;                       // a meal that FILLS a container (a jar, a bottle): the empty container it needs. It is not used up: it comes back full, with what it holds kept
        public string ResultLiquid;                          // ... and the liquid it is filled with (to the container's capacity, or ResultLiters)
        public float ResultLiters;                           // 0 = full
        public List<ConstructionLine> Ingredients = new List<ConstructionLine>();   // the recipe tree, consumed from the kitchen's containers and shelves
        public List<MealLiquid> Liquids = new List<MealLiquid>();                    // liquids the result is BLENDED from, poured out of the filled containers in the kitchen (they keep what is left)
        public List<List<string>> Appliances = new List<List<string>>();             // ANY ONE tool of EACH group must stand in the kitchen (not consumed)
        public string SourceMod;
    }

    /// <summary>One liquid of a blend: its share of the result container (0.6 = 60 percent of the bottle's capacity).</summary>
    public sealed class MealLiquid
    {
        public string Liquid;
        public float Share;
    }

    /// <summary>Every meal loaded from mods. A later mod's meal with the same id replaces the earlier one.</summary>
    public static class MealRegistry
    {
        private static readonly Dictionary<string, MealDef> byId = new Dictionary<string, MealDef>(StringComparer.OrdinalIgnoreCase);
        private static readonly List<string> order = new List<string>();

        public static IEnumerable<MealDef> All
        {
            get { foreach (string id in order) if (byId.TryGetValue(id, out MealDef m)) yield return m; }
        }

        public static int Count => byId.Count;

        public static void Clear() { byId.Clear(); order.Clear(); }

        public static void Register(MealDef meal)
        {
            if (meal == null || string.IsNullOrEmpty(meal.Id)) return;
            if (!byId.ContainsKey(meal.Id)) order.Add(meal.Id);
            byId[meal.Id] = meal;
        }

        /// <summary>Reads one meal file ({"meals": [ ... ]}) and registers its meals; returns how many. Problems go to <paramref name="warn"/>.</summary>
        public static int LoadFromJson(ModJsonValue root, string modId, Action<string> warn)
        {
            int n = 0;
            foreach (ModJsonValue m in root.Get("meals").Items)
            {
                string id = m.Get("id").AsString("");
                string resultId = m.Get("result").Get("item_id").AsString("");
                string container = m.Get("result").Get("container").AsString(""), liquid = m.Get("result").Get("liquid").AsString("");
                if (resultId.Length == 0) resultId = container;
                if (id.Length == 0 || resultId.Length == 0) { warn?.Invoke("a meal needs an id and a result item_id (or a container and a liquid)"); continue; }
                if (container.Length > 0 && liquid.Length == 0) { warn?.Invoke($"meal '{id}' fills a container but names no liquid"); continue; }
                var def = new MealDef
                {
                    Id = id,
                    Name = m.Get("name").AsString(""),
                    Group = m.Get("group").AsString("Cooking"),
                    ResultId = resultId,
                    ResultQty = Math.Max(1, m.Get("result").Get("quantity").AsInt(1)),
                    ResultContainer = container.Length > 0 ? container : null,
                    ResultLiquid = liquid.Length > 0 ? liquid : null,
                    ResultLiters = m.Get("result").Get("liters").AsFloat(0f),
                    SourceMod = modId,
                };
                foreach (ModJsonValue node in m.Get("ingredients").Items) def.Ingredients.Add(ReadNode(node));
                foreach (ModJsonValue l in m.Get("liquids").Items) def.Liquids.Add(new MealLiquid { Liquid = l.Get("liquid").AsString(""), Share = l.Get("share").AsFloat(0f) });
                foreach (ModJsonValue g in m.Get("appliances").Items) def.Appliances.Add(g.Get("tools").AsStringList());
                if (def.Ingredients.Count == 0 && def.Liquids.Count == 0) { warn?.Invoke($"meal '{id}' has no ingredients"); continue; }
                Register(def);
                n++;
            }
            return n;
        }

        private static ConstructionLine ReadNode(ModJsonValue node)
        {
            var line = new ConstructionLine();
            if (node.Has("items"))
            {
                line.section = node.Get("section").AsString("");
                line.mode = node.Get("mode").AsString("all");
                line.uses = node.Get("if").Get("uses").AsString("");
                line.not_uses = node.Get("if").Get("not_uses").AsString("");
                line.items = new List<ConstructionLine>();
                foreach (ModJsonValue child in node.Get("items").Items) line.items.Add(ReadNode(child));
            }
            else
            {
                line.item_id = node.Get("item_id").AsString("");
                line.quantity = node.Get("quantity").AsFloat(1f);
            }
            return line;
        }
    }
}
