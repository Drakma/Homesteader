using System;
using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// The Meal Builder's rules: up to four edible foods on a plate, one soup / stew / salad in a bowl and one drink in a glass, all taken from the kitchen (the same room, or 6 m round the clicked object).
    /// The foods are eaten from what is stocked (category food), the plate and the glass are clean ones from its cabinets and shelves, and the drink is poured out of a filled container
    /// of a drink (`#drink`: juice, milk, water ...). The result is a Plated Meal (a container item holding the foods) and a Drinking Glass (a liquid container holding the drink), both in the toolbar.
    /// </summary>
    public static class MealBuilder
    {
        public const string Plate = "kitchen_plate", Bowl = "kitchen_bowl", PlatedMeal = "kitchen_plated_meal", BowlMeal = "kitchen_bowl_meal", Glass = "kitchen_glass";
        public const int MaxFoods = 4;

        /// <summary>A food that goes on a plate: not one that is served in a bowl (a soup leaves its bowl when eaten).</summary>
        public static bool OnPlate(AssetCatalogItem it)
        {
            return it != null && it.category == "food" && it.leaves_item != Bowl;
        }

        /// <summary>
        /// Starts loading the serving dishes' models (a model loads from disk the first time something asks for it, and a placed object made from one that has not loaded stays empty and
        /// cannot be packed on a counter). The Meal Builder calls this when it opens, so they are ready by the time Make is clicked.
        /// </summary>
        public static void Warm()
        {
            foreach (string id in new[] { PlatedMeal, BowlMeal, Glass })
                if (ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) && info.Prefab != null)
                    info.Prefab.GetComponent<Homesteader.Modding.GlbTemplate>()?.EnsureLoading();
        }

        /// <summary>True when the models of the dishes this meal serves are loaded.</summary>
        private static bool DishesLoaded(bool plate, bool bowl, bool glass)
        {
            bool Ready(string id)
            {
                if (!ItemRegistry.TryGet(id, out ItemRegistry.ItemInfo info) || info.Prefab == null) return true;
                var g = info.Prefab.GetComponent<Homesteader.Modding.GlbTemplate>();
                if (g == null || g.Failed) return true;
                g.EnsureLoading();
                return g.Ready;
            }
            return (!plate || Ready(PlatedMeal)) && (!bowl || Ready(BowlMeal)) && (!glass || Ready(Glass));
        }

        /// <summary>A food that is served in a bowl: a soup, stew or salad (it carries its own bowl, which it leaves when eaten).</summary>
        public static bool InBowl(AssetCatalogItem it)
        {
            return it != null && it.category == "food" && it.leaves_item == Bowl;
        }

        /// <summary>The edible foods stocked in the kitchen (category food), by name.</summary>
        public static List<string> Foods(KitchenScan scan, bool bowl = false)
        {
            var list = new List<string>();
            foreach (KeyValuePair<string, int> kv in scan.Stock)
            {
                if (kv.Value <= 0) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(kv.Key);
                if (bowl ? InBowl(it) : OnPlate(it)) list.Add(kv.Key);
            }
            list.Sort((a, b) => string.Compare(HudBindings.GetItemName(a), HudBindings.GetItemName(b), StringComparison.OrdinalIgnoreCase));
            return list;
        }

        /// <summary>The drinks the kitchen has: liquid id and the litres of it in all.</summary>
        public static List<KeyValuePair<string, float>> Drinks(KitchenScan scan)
        {
            var totals = new Dictionary<string, float>();
            foreach (DrinkSource d in scan.Drinks) { totals.TryGetValue(d.Liquid, out float have); totals[d.Liquid] = have + d.Total; }
            var list = new List<KeyValuePair<string, float>>(totals);
            list.Sort((a, b) => string.Compare(HudBindings.GetItemName(a.Key), HudBindings.GetItemName(b.Key), StringComparison.OrdinalIgnoreCase));
            return list;
        }

        public static int Stocked(KitchenScan scan, string itemId) { return scan.Stock.TryGetValue(itemId, out int n) ? n : 0; }

        /// <summary>Why the meal cannot be made now (foods that are not stocked are COOKED if the kitchen can), or null when it can.</summary>
        public static string Missing(List<string> foods, string drink, KitchenScan scan, string bowl = "")
        {
            return MealPlanner.PlanFoods(foods, drink, scan, true, bowl).Why;
        }

        /// <summary>Every food that can go on the plate: the stocked ones and the ones the kitchen can cook from what it has.</summary>
        public static List<string> Candidates(KitchenScan scan, bool bowl = false)
        {
            var set = new HashSet<string>(Foods(scan, bowl));
            foreach (MealDef m in MealRegistry.All)
            {
                if (m.ResultContainer != null || set.Contains(m.ResultId)) continue;
                AssetCatalogItem it = HudBindings.GetCatalogItem(m.ResultId);
                if (bowl ? !InBowl(it) : !OnPlate(it)) continue;
                var none = new List<string>();
                var one = new List<string> { m.ResultId };
                bool ok = bowl ? MealPlanner.PlanFoods(none, "", scan, false, m.ResultId).Ok : MealPlanner.PlanFoods(one, "", scan, false).Ok;
                if (ok) set.Add(m.ResultId);
            }
            var list = new List<string>(set);
            list.Sort((a, b) => string.Compare(HudBindings.GetItemName(a), HudBindings.GetItemName(b), StringComparison.OrdinalIgnoreCase));
            return list;
        }

        /// <summary>
        /// Serves the meal (after any cooking): the foods, the plate and every cooking's ingredients are taken out of the kitchen, a glass is taken and the drink poured. The Plated Meal (a
        /// container holding the foods) and the filled glass are put ON THE NEAREST COUNTER (a placed piece that carries things on top: a base cabinet, the island, the work counter ...), the
        /// glass beside the plate; the player right clicks them to pick them up. A kitchen with no counter room puts them in the toolbar instead (else on the floor by the clicked object).
        /// It plans again on the kitchen as it is NOW, so a kitchen that changed while the ped was cooking is checked.
        /// </summary>
        public static bool Make(List<string> foods, string drink, KitchenScan scan, out string why, string bowl = "")
        {
            MealPlan plan = MealPlanner.PlanFoods(foods, drink, scan, true, bowl);
            why = plan.Why;
            if (!plan.Ok) return false;
            HudState hud = HudState.Active;
            if (hud == null) { why = "Nothing to serve with."; return false; }
            if (!DishesLoaded(foods.Count > 0, !string.IsNullOrEmpty(bowl), !string.IsNullOrEmpty(drink))) { why = "The dishes are still loading: try again in a moment."; return false; }
            hud.EnsureToolbarSlots();
            bool hasDrink = !string.IsNullOrEmpty(drink);
            bool hasBowl = !string.IsNullOrEmpty(bowl);
            int slotsNeeded = (foods.Count > 0 ? 1 : 0) + (hasBowl ? 1 : 0) + (hasDrink ? 1 : 0);
            if (scan.Counters.Count == 0)
            {
                int freeSlots = 0;
                for (int i = 0; i < hud.Toolbar.Count; i++) if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) freeSlots++;
                if (freeSlots < slotsNeeded) { why = "No counter in the kitchen to put it on, and no room in the toolbar."; return false; }
            }

            Served.Clear();
            MealMaker.ConsumeStock(plan.Real, scan);   // the foods that were stocked, the plate and what the cookings used (the cooked foods go straight on the plate)

            var ped = PedController.Current;
            Vector3 near = ped != null ? ped.transform.position : scan.Center;
            PlacedObject plate = null, bowlObj = null;
            if (hasBowl)
            {
                var inBowl = new List<ContainerStack> { new ContainerStack { ItemId = bowl, Count = 1 } };   // the soup carries its own bowl, which the cooking already took
                bowlObj = PlaceOnCounter(scan, BowlMeal, inBowl, "", 0f, near);
                if (bowlObj == null) GiveOrDrop(hud, scan, new ToolbarSlotData { IconId = BowlMeal, Count = 1, Contents = inBowl });
            }
            if (foods.Count > 0)
            {
                var contents = new List<ContainerStack>();
                foreach (string f in foods)
                {
                    ContainerStack st = contents.Find(x => x.ItemId == f);
                    if (st != null) st.Count++; else contents.Add(new ContainerStack { ItemId = f, Count = 1 });
                }
                plate = PlaceOnCounter(scan, PlatedMeal, contents, "", 0f, bowlObj != null ? bowlObj.transform.position : near);
                if (plate == null) GiveOrDrop(hud, scan, new ToolbarSlotData { IconId = PlatedMeal, Count = 1, Contents = contents });
            }
            if (hasDrink)
            {
                MealMaker.TakeEmpty(scan, Glass);
                float cap = LiquidRules.Capacity(Glass);
                DrinkSource src = null;
                foreach (DrinkSource d in scan.Drinks)
                    if (d.Liquid == drink && d.Total > 0.01f && (src == null || (src.Liters < cap && d.Liters > src.Liters) || (d.Liters >= cap && d.Liters < src.Liters))) src = d;
                float drawn = src != null ? src.Draw(cap) : 0f;
                float stored = LiquidRules.StoredFor(Glass, drawn);
                PlacedObject glass = PlaceOnCounter(scan, Glass, null, drink, stored, plate != null ? plate.transform.position : bowlObj != null ? bowlObj.transform.position : near);   // beside the plate
                if (glass == null) GiveOrDrop(hud, scan, new ToolbarSlotData { IconId = Glass, Count = 1, LiquidId = drink, WireUsed = stored });
            }
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }

        /// <summary>The dishes served in this one Make call (world x, z and radius), so the next one is packed beside them and never on them.</summary>
        private static readonly List<Vector3> Served = new List<Vector3>();

        /// <summary>How far a served dish reaches from its middle (metres): the plate, the bowl, the glass.</summary>
        private static float DishRadius(string itemId) { return itemId == PlatedMeal ? 0.135f : itemId == BowlMeal ? 0.105f : 0.045f; }

        /// <summary>
        /// Puts one item on the free spot of the nearest counter to <paramref name="near"/> (counters nearer than 2.5 m first, nearest first), keeping what it holds; null when no counter has room.
        /// The spot is found here, circle against circle: everything already standing on the counter (its own footprint, else a default reach) and the dishes this meal has served so far are kept
        /// clear, so the plate, the bowl and the glass always sit side by side.
        /// </summary>
        private static PlacedObject PlaceOnCounter(KitchenScan scan, string itemId, List<ContainerStack> contents, string liquid, float stored, Vector3 near)
        {
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return null;
            float r = DishRadius(itemId);
            var counters = new List<PlacedObject>(scan.Counters);
            counters.RemoveAll(c => c == null);
            counters.Sort((a, b) => (a.transform.position - near).sqrMagnitude.CompareTo((b.transform.position - near).sqrMagnitude));
            foreach (PlacedObject onto in counters)
            {
                if (!PalletDeck.LocalRect(onto.transform, onto.gameObject, out Rect deck)) continue;
                if (deck.width < 2f * r || deck.height < 2f * r) continue;
                float deckY = PalletDeck.DeckY(onto);
                var taken = new List<Vector3>(Served);   // x, z, radius
                foreach (PlacedObject o in PalletDeck.Carried(onto))
                {
                    if (PalletDeck.LocalRect(onto.transform, o.gameObject, out Rect orect))
                    {
                        Vector3 mid = onto.transform.TransformPoint(new Vector3(orect.center.x, 0f, orect.center.y));
                        taken.Add(new Vector3(mid.x, mid.z, 0.5f * Mathf.Max(orect.width, orect.height)));
                    }
                    else taken.Add(new Vector3(o.transform.position.x, o.transform.position.z, 0.12f));
                }
                const float gap = 0.015f, step = 0.03f;
                bool found = false;
                Vector3 best = default;
                float bestDist = float.MaxValue;
                for (float x = deck.xMin + r; x <= deck.xMax - r + 0.001f; x += step)
                    for (float z = deck.yMin + r; z <= deck.yMax - r + 0.001f; z += step)
                    {
                        Vector3 w = onto.transform.TransformPoint(new Vector3(x, 0f, z));
                        bool free = true;
                        foreach (Vector3 t in taken)
                        {
                            float dx = w.x - t.x, dz = w.z - t.y, need = r + t.z + gap;
                            if (dx * dx + dz * dz < need * need) { free = false; break; }
                        }
                        if (!free) continue;
                        float d = (w.x - near.x) * (w.x - near.x) + (w.z - near.z) * (w.z - near.z);
                        if (d < bestDist) { bestDist = d; best = w; found = true; }
                    }
                if (!found) continue;
                var spot = new Vector3(best.x, deckY, best.z);
                PlacedObject obj = PlacementController.SpawnPlaced(itemId, info, spot, onto.transform.eulerAngles.y, false, 1, contents);
                if (obj == null) continue;
                obj.Relocate(spot, 0);   // it rests on the counter, not on another item
                obj.LiquidId = liquid;
                obj.WireUsed = stored;
                Served.Add(new Vector3(best.x, best.z, r));
                return obj;
            }
            return null;
        }

        /// <summary>No counter has room: the toolbar takes it, else it is put down on the floor by the clicked object.</summary>
        private static void GiveOrDrop(HudState hud, KitchenScan scan, ToolbarSlotData slot)
        {
            for (int i = 0; i < hud.Toolbar.Count; i++)
                if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { hud.Toolbar[i] = slot; return; }
            if (ItemRegistry.TryGet(slot.IconId, out ItemRegistry.ItemInfo info) && info.Prefab != null)
            {
                PlacedObject o = PlacementController.SpawnPlaced(slot.IconId, info, scan.Center, 0f, false, 0, slot.Contents);
                if (o != null) { o.LiquidId = slot.LiquidId; o.WireUsed = slot.WireUsed; }
            }
        }
    }
}
