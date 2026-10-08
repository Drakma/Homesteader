using System;
using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// What a kitchen holds, worked out from one object in it (the one that was right clicked): the appliances standing in it and everything stocked in its
    /// containers (cabinets, pantry, fridges, freezers ...) and on its shelves. "In the kitchen" means the same room of a finished building (RoomMap), or, when
    /// the object is out in the open, within <see cref="Radius"/> metres of it. Nothing is saved: it is made fresh whenever the Meals List opens or refreshes.
    /// </summary>
    /// <summary>A drink in the kitchen: a filled liquid container in a cabinet or on a shelf, and how much it holds. The Meal Builder pours from it.</summary>
    public sealed class DrinkSource
    {
        public string Liquid;
        public float Liters;                  // what ONE container of it holds
        public int Containers = 1;            // how many identical ones
        public PlacedObject Box;              // in a placed container ...
        public ContainerStack Stack;
        public Shelf Shelf;                   // ... or on a shelf
        public Shelf.Held Held;

        public float Total => Liters * Containers;

        /// <summary>Pours up to <paramref name="liters"/> out of ONE container (splitting it off its stack) and returns what came out.</summary>
        public float Draw(float liters)
        {
            if (Stack != null && Box != null)
            {
                ContainerStack st = Stack;
                if (st.Count > 1)
                {
                    st.Count--;
                    st = new ContainerStack { ItemId = st.ItemId, Count = 1, Liquid = st.Liquid, Stored = st.Stored };
                    Box.Contents.Add(st);
                }
                float have = LiquidRules.Held(st.ItemId, st.Stored), take = Mathf.Min(liters, have);
                st.Stored = LiquidRules.StoredFor(st.ItemId, have - take);
                if (have - take < 0.001f) st.Liquid = "";
                return take;
            }
            if (Held != null)
            {
                float have = LiquidRules.Held(Held.ItemId, Held.WireUsed), take = Mathf.Min(liters, have);
                Held.WireUsed = LiquidRules.StoredFor(Held.ItemId, have - take);
                if (have - take < 0.001f) Held.LiquidId = "";
                return take;
            }
            return 0f;
        }
    }

    public sealed class KitchenScan
    {
        public const float Radius = 6f;

        public Vector3 Center { get; private set; }
        public readonly List<string> Appliances = new List<string>();                 // the item id of every placed or mounted thing in the kitchen
        public readonly List<Transform> ApplianceObjects = new List<Transform>();     // ... and where each one stands (the same order)
        public readonly List<PlacedObject> Containers = new List<PlacedObject>();     // placed containers with stock
        public readonly List<Shelf> Shelves = new List<Shelf>();
        public readonly List<PlacedObject> Counters = new List<PlacedObject>();       // the placed pieces that carry things on top (base cabinets, the island, the work counter ...)
        public readonly Dictionary<string, int> Stock = new Dictionary<string, int>(); // everything stocked, pooled by item id, in USES (a bag of flour that holds 10 counts 10)
        public readonly Dictionary<string, int> Empties = new Dictionary<string, int>(); // the EMPTY liquid containers (jars, bottles) in stock: a filled one is not an ingredient
        public readonly List<DrinkSource> Drinks = new List<DrinkSource>();               // the filled containers of a drink (`#drink`): juice, milk, water ...
        public readonly List<DrinkSource> Liquids = new List<DrinkSource>();              // ALL the filled liquid containers (drinks, oils ...): what a blend pours from

        public static KitchenScan At(Vector3 center)
        {
            var scan = new KitchenScan { Center = center };
            ConstructionSite site = null;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.Finished && s.IsInside(center)) { site = s; break; }
            int room = site != null ? RoomMap.RoomAt(site, center) : -1;
            bool InKitchen(Vector3 p)
            {
                if (site != null && room >= 0) return site.IsInside(p) && RoomMap.RoomAt(site, p) == room;
                return (p - center).sqrMagnitude <= Radius * Radius;
            }

            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !InKitchen(o.transform.position)) continue;
                scan.Appliances.Add(o.ItemId);
                scan.ApplianceObjects.Add(o.transform);
                if (PalletDeck.IsPallet(o.ItemId) && !PalletDeck.IsShelving(o.ItemId)) scan.Counters.Add(o);
                if (o.Contents == null || !ContainerRules.IsContainer(o.ItemId)) continue;
                scan.Containers.Add(o);
                foreach (ContainerStack st in o.Contents)
                {
                    if (st.Count <= 0) continue;
                    if (LiquidRules.IsLiquidContainer(st.ItemId))
                    {
                        if (string.IsNullOrEmpty(st.Liquid) && LiquidRules.Held(st.ItemId, st.Stored) < 0.01f) scan.AddEmpty(st.ItemId, st.Count);
                        else scan.AddDrink(st.ItemId, st.Liquid, st.Stored, st.Count, o, st, null, null);
                        continue;
                    }
                    scan.Add(st.ItemId, ContainerRules.UsesLeft(st, HudBindings.UsesPerItem(st.ItemId)));   // (an item holding several uses counts them all)
                }
            }
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || !InKitchen(a.transform.position)) continue;
                scan.Appliances.Add(a.ItemId);
                scan.ApplianceObjects.Add(a.transform);
                Shelf shelf = a.GetComponent<Shelf>();
                if (shelf == null) continue;
                scan.Shelves.Add(shelf);
                foreach (Shelf.Held h in shelf.Items)
                {
                    if (LiquidRules.IsLiquidContainer(h.ItemId))
                    {
                        if (string.IsNullOrEmpty(h.LiquidId) && LiquidRules.Held(h.ItemId, h.WireUsed) < 0.01f) scan.AddEmpty(h.ItemId, 1);
                        else scan.AddDrink(h.ItemId, h.LiquidId, h.WireUsed, 1, null, null, shelf, h);
                        continue;
                    }
                    if (!string.IsNullOrEmpty(h.LiquidId)) continue;
                    int per = HudBindings.UsesPerItem(h.ItemId);
                    if (per > 1) scan.Add(h.ItemId, Mathf.Max(0, per - Mathf.RoundToInt(h.WireUsed)));
                    else if (h.WireUsed <= 0.01f) scan.Add(h.ItemId, 1);
                }
            }
            return scan;
        }

        /// <summary>One USE of a liquid in a recipe line (a splash of oil): a recipe line `#cooking_oil x 4` is 0.2 L poured out of the kitchen's filled bottles.</summary>
        public const float LiquidUseL = 0.05f;

        private void AddDrink(string containerId, string liquidFilledWith, float stored, int count, PlacedObject box, ContainerStack stack, Shelf shelf, Shelf.Held held)
        {
            string liquid = LiquidRules.LiquidIn(containerId, liquidFilledWith);
            float liters = LiquidRules.Held(containerId, stored);
            if (string.IsNullOrEmpty(liquid) || liters < 0.01f) return;
            var src = new DrinkSource { Liquid = liquid, Liters = liters, Containers = count, Box = box, Stack = stack, Shelf = shelf, Held = held };
            Liquids.Add(src);
            Add(liquid, Mathf.FloorToInt(liters * count / LiquidUseL + 1e-3f));   // a liquid is also stock in uses, so a recipe line can ask for it (oil for deep frying)
            if (GrowthRegistry.ToolMatches("#drink", liquid)) Drinks.Add(src);
        }

        private void AddEmpty(string itemId, int count)
        {
            Empties.TryGetValue(itemId, out int have);
            Empties[itemId] = have + count;
        }

        private void Add(string itemId, int count)
        {
            Stock.TryGetValue(itemId, out int have);
            Stock[itemId] = have + count;
        }

        /// <summary>The appliance a meal is cooked on: the nearest one to the player of the first group's tools. False when there is none.</summary>
        public bool FindAppliance(List<List<string>> groups, out Transform where, out string itemId)
        {
            where = null;
            itemId = "";
            if (groups == null || groups.Count == 0) return false;
            var ped = PedController.Current;
            Vector3 from = ped != null ? ped.transform.position : Center;
            float best = float.MaxValue;
            for (int i = 0; i < Appliances.Count; i++)
                foreach (string tool in groups[0])
                    if (GrowthRegistry.ToolMatches(tool, Appliances[i]))
                    {
                        Transform tr = i < ApplianceObjects.Count ? ApplianceObjects[i] : null;
                        float d = tr != null ? (tr.position - from).sqrMagnitude : float.MaxValue * 0.5f;
                        if (itemId.Length == 0 || d < best) { best = d; where = tr; itemId = Appliances[i]; }
                        break;
                    }
            return itemId.Length > 0;
        }

        /// <summary>True when some appliance in the kitchen is one of the tools (an item id, #tag or ~equivalency; any one will do).</summary>
        public bool HasAny(List<string> tools)
        {
            if (tools == null || tools.Count == 0) return true;
            foreach (string tool in tools)
                foreach (string id in Appliances)
                    if (GrowthRegistry.ToolMatches(tool, id)) return true;
            return false;
        }
    }

    /// <summary>Works out which meals a kitchen can make, and makes them: the ingredients are taken out of its containers and shelves and the result goes to the toolbar.</summary>
    public static class MealMaker
    {
        /// <summary>The ingredients a meal would use from the stock (item id -> how many), or null when the kitchen cannot make it.</summary>
        public static Dictionary<string, int> Plan(MealDef meal, KitchenScan scan)
        {
            foreach (List<string> group in meal.Appliances) if (!scan.HasAny(group)) return null;
            if (meal.ResultContainer != null && !(scan.Empties.TryGetValue(meal.ResultContainer, out int empty) && empty > 0)) return null;   // it needs an empty one to fill
            foreach (KeyValuePair<string, float> need in LiquidNeed(meal))
                if (TotalLiters(scan, need.Key) + 1e-3f < need.Value) return null;                                                   // a blend needs enough of each oil
            var state = new State { Inv = new Dictionary<string, int>(scan.Stock) };
            foreach (ConstructionLine node in meal.Ingredients) if (!Pay(node, state)) return null;
            return state.Taken;
        }

        /// <summary>The liquids a blend pours: liquid id -> litres (its share of the result container's capacity).</summary>
        public static Dictionary<string, float> LiquidNeed(MealDef meal)
        {
            var need = new Dictionary<string, float>();
            if (meal.Liquids == null || meal.ResultContainer == null) return need;
            float cap = LiquidRules.Capacity(meal.ResultContainer);
            foreach (MealLiquid l in meal.Liquids) need[l.Liquid] = (need.TryGetValue(l.Liquid, out float have) ? have : 0f) + l.Share * cap;
            return need;
        }

        public static float TotalLiters(KitchenScan scan, string liquid)
        {
            float total = 0f;
            foreach (DrinkSource d in scan.Liquids) if (d.Liquid == liquid) total += d.Total;
            return total;
        }

        /// <summary>Pours litres of a liquid out of the kitchen's filled containers (the fullest first); each container keeps what is left.</summary>
        public static void DrawLiquid(KitchenScan scan, string liquid, float liters)
        {
            while (liters > 1e-4f)
            {
                DrinkSource best = null;
                foreach (DrinkSource d in scan.Liquids) if (d.Liquid == liquid && d.Total > 1e-3f && (best == null || d.Liters > best.Liters)) best = d;
                if (best == null) return;
                float drawn = best.Draw(liters);
                if (drawn <= 1e-5f) return;
                liters -= drawn;
                best.Liters = Mathf.Max(0f, best.Liters - drawn);   // (a split-off container is no longer one of several)
                if (best.Containers > 1 && best.Stack != null) best.Containers--;
                if (best.Liters <= 1e-3f) scan.Liquids.Remove(best);
            }
        }

        /// <summary>Every meal the kitchen can make right now.</summary>
        public static List<MealDef> Makeable(KitchenScan scan)
        {
            var list = new List<MealDef>();
            foreach (MealDef m in MealRegistry.All) if (Plan(m, scan) != null) list.Add(m);
            return list;
        }

        public static string NameOf(MealDef meal)
        {
            if (!string.IsNullOrEmpty(meal.Name)) return meal.Name;
            return HudBindings.GetItemName(meal.ResultId);
        }

        /// <summary>Makes one batch: takes the ingredients out of the kitchen, puts the result in the toolbar. False (with the reason) when it cannot.</summary>
        public static bool Make(MealDef meal, KitchenScan scan, out string why)
        {
            why = null;
            Dictionary<string, int> taken = Plan(meal, scan);
            if (taken == null) { why = "The kitchen no longer has what it takes."; return false; }
            HudState hud = HudState.Active;
            if (hud == null) { why = "Nothing to cook with."; return false; }
            hud.EnsureToolbarSlots();
            if (meal.ResultContainer != null ? FreeSlot(hud) < 0 : ToolbarRoomFor(hud, meal.ResultId) < meal.ResultQty) { why = "No room in the toolbar for it."; return false; }

            ConsumeStock(taken, scan);
            foreach (KeyValuePair<string, float> need in LiquidNeed(meal)) DrawLiquid(scan, need.Key, need.Value);
            if (meal.ResultContainer != null)
            {
                // an empty jar or bottle is taken from the kitchen (a container, else a shelf) and comes back FULL, the liquid kept in it
                bool took = TakeEmpty(scan, meal.ResultContainer);
                float liters = meal.ResultLiters > 0f ? Mathf.Min(meal.ResultLiters, LiquidRules.Capacity(meal.ResultContainer)) : LiquidRules.Capacity(meal.ResultContainer);
                hud.Toolbar[FreeSlot(hud)] = new ToolbarSlotData { IconId = meal.ResultContainer, Count = 1, LiquidId = meal.ResultLiquid, WireUsed = LiquidRules.StoredFor(meal.ResultContainer, liters) };
                if (!took) why = null;
            }
            else hud.AddItemToToolbar(meal.ResultId, meal.ResultQty, HudBindings.GetMaxStack(meal.ResultId), useContainers: false);
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        public static int FreeSlot(HudState hud)
        {
            for (int i = 0; i < hud.Toolbar.Count; i++)
                if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) return i;
            return -1;
        }

        /// <summary>Takes what a plan uses (item id -> how many uses) out of the kitchen's containers, then its shelves.</summary>
        public static void ConsumeStock(Dictionary<string, int> taken, KitchenScan scan)
        {
            foreach (KeyValuePair<string, int> kv in taken)
            {
                if (LiquidRules.IsLiquid(kv.Key)) { DrawLiquid(scan, kv.Key, kv.Value * KitchenScan.LiquidUseL); continue; }   // a liquid line: poured out of the filled bottles
                int left = kv.Value, per = HudBindings.UsesPerItem(kv.Key);
                foreach (PlacedObject box in scan.Containers)
                {
                    if (left <= 0) break;
                    left -= ContainerRules.ConsumeUses(box.Contents, kv.Key, left, per);
                }
                foreach (Shelf shelf in scan.Shelves)
                    if (left > 0) left -= shelf.ConsumeUses(kv.Key, left, per);
            }
        }

        /// <summary>Takes ONE empty liquid container (a jar, a glass) out of the kitchen: a container first, then a shelf.</summary>
        public static bool TakeEmpty(KitchenScan scan, string containerItem)
        {
            foreach (PlacedObject box in scan.Containers)
            {
                ContainerStack plain = box.Contents.Find(s => s.ItemId == containerItem && !s.HasState && s.Count > 0);
                if (plain == null) continue;
                ContainerRules.Remove(box.Contents, containerItem, 1);
                return true;
            }
            foreach (Shelf shelf in scan.Shelves) if (shelf.ConsumeEmpty(containerItem)) return true;
            return false;
        }

        private static int ToolbarRoomFor(HudState hud, string itemId)
        {
            int max = Mathf.Max(1, HudBindings.GetMaxStack(itemId)), room = 0;
            for (int i = 0; i < hud.Toolbar.Count; i++)
            {
                ToolbarSlotData t = hud.Toolbar[i];
                if (t.Count <= 0 || string.IsNullOrEmpty(t.IconId)) room += max;
                else if (t.IconId == itemId && t.Contents == null && string.IsNullOrEmpty(t.LiquidId)) room += Mathf.Max(0, max - t.Count);
            }
            return room;
        }

        // ------------------------------------------------------------------ the recipe tree

        private sealed class State
        {
            public Dictionary<string, int> Inv;                                        // what is left to take
            public readonly Dictionary<string, int> Taken = new Dictionary<string, int>();
            public readonly List<string> Paid = new List<string>();                    // the items the lines so far were paid with

            public State Copy()
            {
                var c = new State { Inv = new Dictionary<string, int>(Inv) };
                foreach (KeyValuePair<string, int> kv in Taken) c.Taken[kv.Key] = kv.Value;
                c.Paid.AddRange(Paid);
                return c;
            }

            public void Take(string id, int n)
            {
                Inv[id] -= n;
                Taken.TryGetValue(id, out int have);
                Taken[id] = have + n;
                if (!Paid.Contains(id)) Paid.Add(id);
            }
        }

        /// <summary>One node of the recipe tree (docs/CONSTRUCTION.md): a line, or a section "all" / "any" with an optional uses / not_uses condition.</summary>
        private static bool Pay(ConstructionLine node, State s)
        {
            if (node.IsSection)
            {
                if (!string.IsNullOrEmpty(node.uses) && !s.Paid.Exists(id => GrowthRegistry.ToolMatches(node.uses, id))) return true;      // the condition fails: it needs nothing
                if (!string.IsNullOrEmpty(node.not_uses) && s.Paid.Exists(id => GrowthRegistry.ToolMatches(node.not_uses, id))) return true;
                if (string.Equals(node.mode, "any", StringComparison.OrdinalIgnoreCase))
                {
                    foreach (ConstructionLine child in node.items)
                    {
                        State trial = s.Copy();
                        if (!Pay(child, trial)) continue;
                        s.Inv = trial.Inv;
                        foreach (KeyValuePair<string, int> kv in trial.Taken) s.Taken[kv.Key] = kv.Value;
                        foreach (string id in trial.Paid) if (!s.Paid.Contains(id)) s.Paid.Add(id);
                        return true;
                    }
                    return false;
                }
                foreach (ConstructionLine child in node.items) if (!Pay(child, s)) return false;
                return true;
            }

            string spec = node.item_id ?? "";
            int need = Mathf.Max(1, Mathf.CeilToInt(node.quantity - 1e-4f));
            var keys = new List<string>(s.Inv.Keys);
            keys.Sort(StringComparer.Ordinal);
            if (spec.StartsWith("~"))
            {
                // an equivalency: any mix of its members worth `need` units
                float remaining = need;
                string name = spec.Substring(1);
                foreach (string id in keys)
                {
                    if (remaining <= 0f) break;
                    float v = GrowthRegistry.EquivalencyValue(name, id);
                    if (v <= 0f || s.Inv[id] <= 0) continue;
                    int use = Mathf.Min(s.Inv[id], Mathf.CeilToInt(remaining / v));
                    s.Take(id, use);
                    remaining -= use * v;
                }
                return remaining <= 0f;
            }
            int left = need;
            foreach (string id in keys)
            {
                if (left <= 0) break;
                if (s.Inv[id] <= 0 || !GrowthRegistry.ToolMatches(spec, id)) continue;
                int use = Mathf.Min(s.Inv[id], left);
                s.Take(id, use);
                left -= use;
            }
            return left <= 0;
        }
    }
}
