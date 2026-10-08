using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// Eating and drinking: the Eat / drink key (G) uses the item in the active toolbar slot. A food is eaten one at a time; a Plated Meal is eaten whole (everything on it);
    /// a filled drink (a glass, a bottle of juice, water ...) is sipped a quarter litre at a time. What each gives is the item's manifest: hunger_restore (category_fields),
    /// thirst_restore, stamina_restore and wellness_modifier (properties), for a drink per 0.25 L. What is left when it is eaten comes from `properties.leaves_item`
    /// (a soup leaves its bowl, a plated meal its plate). Docs: docs/COOKING.md.
    /// </summary>
    public static class Consumption
    {
        public const float SipLiters = 0.25f;

        private struct Gain { public float Hunger, Thirst, Stamina, Wellness; }

        private static Gain GainOf(AssetCatalogItem it, float scale)
        {
            return new Gain { Hunger = it.hunger_restore * scale, Thirst = it.thirst_restore * scale, Stamina = it.stamina_restore * scale, Wellness = it.wellness_modifier * scale };
        }

        private static bool Full(HudState s, Gain g)
        {
            bool needsHunger = g.Hunger > 0.01f, needsThirst = g.Thirst > 0.01f;
            if (!needsHunger && !needsThirst) return false;
            return (!needsHunger || s.GetVitalValue(VitalId.Hunger) >= 98) && (!needsThirst || s.GetVitalValue(VitalId.Thirst) >= 98);
        }

        private static void Apply(HudState s, Gain g)
        {
            Add(s, VitalId.Hunger, g.Hunger);
            Add(s, VitalId.Thirst, g.Thirst);
            Add(s, VitalId.Stamina, g.Stamina);
            Add(s, VitalId.Wellness, g.Wellness);
        }

        private static void Add(HudState s, VitalId id, float amount)
        {
            if (Mathf.Abs(amount) < 0.01f) return;
            s.SetVitalValue(id, Mathf.Clamp(s.GetVitalValue(id) + Mathf.RoundToInt(amount), -100, 100));
        }

        /// <summary>Uses the held item: eats it or drinks from it. Says why when it cannot.</summary>
        public static bool TryConsumeHeld()
        {
            HudState s = HudState.Active;
            if (s == null || s.SelectedSlot < 0 || s.SelectedSlot >= s.Toolbar.Count) return false;
            int idx = s.SelectedSlot;
            ToolbarSlotData slot = s.Toolbar[idx];
            if (string.IsNullOrEmpty(slot.IconId) || slot.Count <= 0) return false;
            AssetCatalogItem it = HudBindings.GetCatalogItem(slot.IconId);
            if (it == null) return false;

            // a Plated Meal or a Bowl of Food: everything on it
            if (slot.IconId == MealBuilder.PlatedMeal || slot.IconId == MealBuilder.BowlMeal)
            {
                var total = new Gain();
                int foods = 0;
                if (slot.Contents != null)
                    foreach (ContainerStack c in slot.Contents)
                    {
                        AssetCatalogItem f = HudBindings.GetCatalogItem(c.ItemId);
                        if (f == null || c.Count <= 0) continue;
                        Gain g = GainOf(f, c.Count);
                        total.Hunger += g.Hunger; total.Thirst += g.Thirst; total.Stamina += g.Stamina; total.Wellness += g.Wellness;
                        foods += c.Count;
                    }
                if (foods == 0) { ToastNotificationSystem.ShowInfo("Nothing to eat", "The plate is empty."); return false; }
                if (Full(s, total)) { ToastNotificationSystem.ShowInfo("Not hungry", "You are too full to eat this now."); return false; }
                Apply(s, total);
                Leave(s, idx, slot, it);
                KitchenAnimator.Play(PedController.Current, KitchenAnimator.Gesture.Eat, Mathf.Clamp(foods, 1, 4) * 1.5f);
                return true;
            }

            // a drink: a liquid container holding something drinkable
            if (it.liquid_capacity_l > 0f)
            {
                string liquid = LiquidRules.LiquidIn(slot.IconId, slot.LiquidId);
                float held = LiquidRules.Held(slot.IconId, slot.WireUsed);
                AssetCatalogItem l = string.IsNullOrEmpty(liquid) ? null : HudBindings.GetCatalogItem(liquid);
                if (l == null || held < 0.01f || !GrowthRegistry.ToolMatches("#drink", liquid)) return false;
                float sip = Mathf.Min(SipLiters, held);
                Gain g = GainOf(l, sip / SipLiters);
                if (Full(s, g)) { ToastNotificationSystem.ShowInfo("Not thirsty", "You are not thirsty."); return false; }
                Apply(s, g);
                slot.WireUsed = LiquidRules.StoredFor(slot.IconId, held - sip);
                if (held - sip < 0.001f) slot.LiquidId = "";
                s.Toolbar[idx] = slot;
                HudBindings.Instance?.RefreshToolbar();
                KitchenAnimator.Play(PedController.Current, KitchenAnimator.Gesture.Drink, 1.7f);
                return true;
            }

            // a food
            if (it.hunger_restore <= 0f && it.thirst_restore <= 0f) return false;
            Gain food = GainOf(it, 1f);
            if (Full(s, food)) { ToastNotificationSystem.ShowInfo("Not hungry", "You are too full to eat this now."); return false; }
            Apply(s, food);
            Leave(s, idx, slot, it);
            KitchenAnimator.Play(PedController.Current, KitchenAnimator.Gesture.Eat, 1.5f);
            return true;
        }

        /// <summary>One item of the slot is gone; what it leaves (a bowl, a plate) goes into the slot when it is empty, else the toolbar, else the ground.</summary>
        private static void Leave(HudState s, int idx, ToolbarSlotData slot, AssetCatalogItem eaten)
        {
            slot.Count--;
            slot.Contents = null;
            string left = eaten.leaves_item;
            if (slot.Count <= 0) slot = string.IsNullOrEmpty(left) ? ToolbarSlotData.Empty() : new ToolbarSlotData { IconId = left, Count = 1 };
            else if (!string.IsNullOrEmpty(left)) GiveBack(s, left);
            s.Toolbar[idx] = slot;
            s.SelectSlot(idx);
            HudBindings.Instance?.RefreshToolbar();
        }

        private static void GiveBack(HudState s, string itemId)
        {
            int max = Mathf.Max(1, HudBindings.GetCatalogItem(itemId)?.max_stack ?? 1);
            for (int i = 0; i < s.Toolbar.Count; i++)
            {
                ToolbarSlotData t = s.Toolbar[i];
                if (t.IconId == itemId && t.Count > 0 && t.Count < max && t.Contents == null && string.IsNullOrEmpty(t.LiquidId)) { t.Count++; s.Toolbar[i] = t; return; }
            }
            for (int i = 0; i < s.Toolbar.Count; i++)
                if (s.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(s.Toolbar[i].IconId)) { s.Toolbar[i] = new ToolbarSlotData { IconId = itemId, Count = 1 }; return; }
            PedController ped = PedController.Current;
            if (ped != null && ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) && info.Prefab != null)
                PlacementController.SpawnPlaced(itemId, info, ped.transform.position + ped.transform.forward * 0.6f, 0f, false, 0, null);
        }
    }

    /// <summary>
    /// Hunger and thirst fall with game time (so eating and drinking mean something): hunger from full to empty in 5 game days, thirst in 3. Only while the game runs (not paused).
    /// Nothing else happens at the bottom of the scale yet. The vitals are saved with the game (the admin sliders and the phone still set them directly).
    /// </summary>
    public sealed class Metabolism : MonoBehaviour
    {
        public const float HungerDaysEmpty = 5f, ThirstDaysEmpty = 3f;
        private float _hunger, _thirst;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<Metabolism>() != null) return;
            var go = new GameObject("Metabolism");
            DontDestroyOnLoad(go);
            go.AddComponent<Metabolism>();
        }

        private void Update()
        {
            HudState s = HudState.Active;
            TimeSystem time = TimeSystem.Instance;
            if (s == null || time == null || time.IsPaused || HudBindings.Instance == null) return;
            float minutes = Time.unscaledDeltaTime * TimeSystem.SpeedToMultiplier(time.CurrentSpeed) * TimeConstants.GameMinutesPerRealSecondAt1X;
            _hunger += minutes * 200f / (HungerDaysEmpty * TimeConstants.CycleGameMinutes);
            _thirst += minutes * 200f / (ThirstDaysEmpty * TimeConstants.CycleGameMinutes);
            Drain(s, VitalId.Hunger, ref _hunger);
            Drain(s, VitalId.Thirst, ref _thirst);
        }

        private static void Drain(HudState s, VitalId id, ref float acc)
        {
            if (acc < 1f) return;
            int whole = Mathf.FloorToInt(acc);
            acc -= whole;
            s.SetVitalValue(id, s.GetVitalValue(id) - whole);
        }
    }
}
