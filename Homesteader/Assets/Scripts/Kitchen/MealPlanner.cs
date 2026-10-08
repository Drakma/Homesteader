using System;
using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Kitchen
{
    /// <summary>One cooking the plan runs: a meal (the recipe), how many batches, what it takes from the kitchen's stock and the appliance it is cooked on.</summary>
    public sealed class PlanStep
    {
        public MealDef Meal;
        public int Batches = 1;
        public readonly Dictionary<string, int> Real = new Dictionary<string, int>();   // what this step takes out of the kitchen's stock (item id -> uses)
        public Transform Appliance;                                                       // where it is cooked (null when the kitchen has no object for it)
        public string ApplianceId = "";
    }

    /// <summary>A whole job worked out in advance: the cookings in the order they run (the first makes what the next one needs) and everything it takes out of the kitchen's stock.</summary>
    public sealed class MealPlan
    {
        public bool Ok;
        public string Why;                                             // why it cannot be done (null when it can)
        public readonly List<PlanStep> Steps = new List<PlanStep>();
        public readonly Dictionary<string, int> Real = new Dictionary<string, int>();   // all of it, steps and the plate included (item id -> uses)
    }

    /// <summary>
    /// Works out how to get a food the kitchen does not have yet: it is COOKED from its ingredients by the meal that makes it, and what that meal needs may itself be cooked (bread: flour
    /// milled from wheat, then baked with yeast and salt). Nothing is taken from the kitchen while planning; the plan says what would be, and the cooking routine then walks the ped
    /// from appliance to appliance and takes it all at the end (so stopping half way costs nothing).
    /// </summary>
    public static class MealPlanner
    {
        private const int MaxDepth = 4;

        private sealed class State
        {
            public Dictionary<string, int> Real;                              // what is left in the stock
            public Dictionary<string, int> Made = new Dictionary<string, int>();   // what the steps so far have cooked and not yet used
            public readonly List<PlanStep> Steps = new List<PlanStep>();
            public Dictionary<string, int> Sink;                              // the Real of the step being paid (or of the whole job)
            public readonly HashSet<string> Paid = new HashSet<string>();
        }

        private struct Snap
        {
            public Dictionary<string, int> Real, Made, Sink;
            public int Steps;
        }

        private static Snap Take(State s)
        {
            return new Snap { Real = new Dictionary<string, int>(s.Real), Made = new Dictionary<string, int>(s.Made), Sink = new Dictionary<string, int>(s.Sink), Steps = s.Steps.Count };
        }

        private static void Restore(State s, Snap k)
        {
            s.Real.Clear(); foreach (KeyValuePair<string, int> kv in k.Real) s.Real[kv.Key] = kv.Value;
            s.Made.Clear(); foreach (KeyValuePair<string, int> kv in k.Made) s.Made[kv.Key] = kv.Value;
            s.Sink.Clear(); foreach (KeyValuePair<string, int> kv in k.Sink) s.Sink[kv.Key] = kv.Value;
            if (s.Steps.Count > k.Steps) s.Steps.RemoveRange(k.Steps, s.Steps.Count - k.Steps);
        }

        private static int Count(Dictionary<string, int> d, string id) { return d.TryGetValue(id, out int n) ? n : 0; }
        private static int Have(State s, string id) { return Count(s.Made, id) + Count(s.Real, id); }

        /// <summary>Takes units of an item, what was cooked first and then the stock (the stock part is what the job takes from the kitchen).</summary>
        private static void TakeUnits(State s, string id, int units)
        {
            int fromMade = Math.Min(units, Count(s.Made, id));
            if (fromMade > 0) s.Made[id] -= fromMade;
            int rest = units - fromMade;
            if (rest > 0)
            {
                s.Real[id] = Count(s.Real, id) - rest;
                s.Sink[id] = Count(s.Sink, id) + rest;
            }
            s.Paid.Add(id);
        }

        /// <summary>Gets <paramref name="units"/> of an item: from what is there, and the rest by cooking it.</summary>
        private static bool Obtain(State s, string id, int units, int depth, KitchenScan scan, out string why)
        {
            why = null;
            int have = Have(s, id);
            if (have >= units) { TakeUnits(s, id, units); return true; }
            int deficit = units - have;
            int perItem = Mathf.Max(1, HudBindings.UsesPerItem(id));
            if (depth < MaxDepth)
            {
                foreach (MealDef meal in MealRegistry.All)
                {
                    if (meal.ResultContainer != null || meal.ResultId != id) continue;
                    Snap snap = Take(s);
                    int perBatch = meal.ResultQty * perItem;
                    int batches = Mathf.CeilToInt(deficit / (float)perBatch);
                    if (PayMeal(s, meal, batches, depth + 1, scan, out string failed))
                    {
                        s.Made[id] = Count(s.Made, id) + batches * perBatch;
                        TakeUnits(s, id, units);
                        return true;
                    }
                    Restore(s, snap);
                    why = failed;
                }
            }
            if (why == null) why = "Not enough " + HudBindings.GetItemName(id) + ".";
            return false;
        }

        private static bool PayMeal(State s, MealDef meal, int batches, int depth, KitchenScan scan, out string why)
        {
            why = null;
            foreach (List<string> group in meal.Appliances)
                if (!scan.HasAny(group)) { why = "No " + DescribeTools(group) + " in the kitchen for " + MealMaker.NameOf(meal) + "."; return false; }
            if (meal.Liquids != null && meal.Liquids.Count > 0) { why = MealMaker.NameOf(meal) + " is a blend poured at the Meals List."; return false; }
            var step = new PlanStep { Meal = meal, Batches = batches };
            Dictionary<string, int> outer = s.Sink;
            s.Sink = step.Real;
            foreach (ConstructionLine node in meal.Ingredients)
                if (!PayNode(node, s, batches, depth, scan, out why)) { s.Sink = outer; return false; }
            s.Sink = outer;
            scan.FindAppliance(meal.Appliances, out step.Appliance, out step.ApplianceId);
            s.Steps.Add(step);   // after the steps that made its ingredients
            return true;
        }

        private static string DescribeTools(List<string> group)
        {
            if (group == null || group.Count == 0) return "appliance";
            string t = group[0];
            return t.StartsWith("#") ? t.Substring(1).Replace("appliance_", "").Replace('_', ' ') : HudBindings.GetItemName(t);
        }

        private static bool PayNode(ConstructionLine node, State s, int mult, int depth, KitchenScan scan, out string why)
        {
            why = null;
            if (node.IsSection)
            {
                if (!string.IsNullOrEmpty(node.uses) && !AnyPaid(s, node.uses)) return true;
                if (!string.IsNullOrEmpty(node.not_uses) && AnyPaid(s, node.not_uses)) return true;
                if (string.Equals(node.mode, "any", StringComparison.OrdinalIgnoreCase))
                {
                    string last = null;
                    foreach (ConstructionLine child in node.items)
                    {
                        Snap snap = Take(s);
                        if (PayNode(child, s, mult, depth, scan, out string failed)) return true;
                        Restore(s, snap);
                        last = failed;
                    }
                    why = last;
                    return false;
                }
                foreach (ConstructionLine child in node.items) if (!PayNode(child, s, mult, depth, scan, out why)) return false;
                return true;
            }

            string spec = node.item_id ?? "";
            int need = Mathf.Max(1, Mathf.CeilToInt(node.quantity * mult - 1e-4f));
            if (spec.Length > 0 && spec[0] != '#' && spec[0] != '~') return Obtain(s, spec, need, depth, scan, out why);   // an item: cooked if the kitchen has none

            // a tag or an equivalency: only what is stocked or cooked already
            var ids = new List<string>(s.Real.Keys);
            foreach (string id in s.Made.Keys) if (!ids.Contains(id)) ids.Add(id);
            ids.Sort(StringComparer.Ordinal);
            if (spec.Length > 0 && spec[0] == '~')
            {
                float remaining = need;
                foreach (string id in ids)
                {
                    if (remaining <= 0f) break;
                    float v = GrowthRegistry.EquivalencyValue(spec.Substring(1), id);
                    int have = Have(s, id);
                    if (v <= 0f || have <= 0) continue;
                    int use = Mathf.Min(have, Mathf.CeilToInt(remaining / v));
                    TakeUnits(s, id, use);
                    remaining -= use * v;
                }
                if (remaining > 0f) why = "Not enough " + spec.Substring(1).Replace('_', ' ') + ".";
                return remaining <= 0f;
            }
            int left = need;
            foreach (string id in ids)
            {
                if (left <= 0) break;
                int have = Have(s, id);
                if (have <= 0 || !GrowthRegistry.ToolMatches(spec, id)) continue;
                int use = Mathf.Min(have, left);
                TakeUnits(s, id, use);
                left -= use;
            }
            if (left > 0 && spec.Length > 0 && spec[0] == '#')
            {
                // a tag (#flour): what the kitchen has is used first, then the first member it can COOK (wheat flour milled from wheat, corn flour from corn ...)
                foreach (string member in GrowthRegistry.ToolItems(spec))
                {
                    Snap snap = Take(s);
                    if (Obtain(s, member, left, depth, scan, out string failed)) { left = 0; why = null; break; }
                    Restore(s, snap);
                    why = failed;
                }
            }
            if (left > 0 && why == null) why = "Not enough " + spec.TrimStart('#').Replace('_', ' ') + ".";
            return left <= 0;
        }

        private static bool AnyPaid(State s, string spec)
        {
            foreach (string id in s.Paid) if (GrowthRegistry.ToolMatches(spec, id)) return true;
            return false;
        }

        /// <summary>
        /// The plan for a plate of foods (and the drink): each food from the stock, else cooked. <paramref name="withPlate"/>: the plate itself must be in stock too.
        /// Nothing is changed in the kitchen.
        /// </summary>
        public static MealPlan PlanFoods(List<string> foods, string drink, KitchenScan scan, bool withPlate = true, string bowl = "")
        {
            var plan = new MealPlan();
            var s = new State { Real = new Dictionary<string, int>(scan.Stock), Sink = plan.Real };
            bool hasDrink = !string.IsNullOrEmpty(drink);
            bool hasBowl = !string.IsNullOrEmpty(bowl);
            if (foods.Count == 0 && !hasDrink && !hasBowl) { plan.Why = "Put something on the plate, in the bowl or pick a drink."; return plan; }
            if (foods.Count > MealBuilder.MaxFoods) { plan.Why = "A plate takes four foods."; return plan; }
            var need = new Dictionary<string, int>();
            foreach (string f in foods) need[f] = Count(need, f) + 1;
            foreach (KeyValuePair<string, int> kv in need)
                if (!Obtain(s, kv.Key, kv.Value, 0, scan, out plan.Why)) return plan;
            if (hasBowl && !Obtain(s, bowl, 1, 0, scan, out plan.Why)) return plan;   // a soup, stew or salad comes with its own bowl
            if (foods.Count > 0 && withPlate)
            {
                if (Have(s, MealBuilder.Plate) < 1) { plan.Why = "No clean plate in the kitchen."; return plan; }
                TakeUnits(s, MealBuilder.Plate, 1);
            }
            if (hasDrink)
            {
                if (!(scan.Empties.TryGetValue(MealBuilder.Glass, out int glasses) && glasses > 0)) { plan.Why = "No empty glass in the kitchen."; return plan; }
                if (scan.Drinks.Find(d => d.Liquid == drink && d.Total > 0.01f) == null) { plan.Why = "No " + HudBindings.GetItemName(drink) + " left."; return plan; }
            }
            // the whole job: every step's stock plus the plate's and the foods'
            plan.Steps.AddRange(s.Steps);
            foreach (PlanStep st in plan.Steps) foreach (KeyValuePair<string, int> kv in st.Real) plan.Real[kv.Key] = Count(plan.Real, kv.Key) + kv.Value;
            plan.Ok = true;
            return plan;
        }
    }
}
