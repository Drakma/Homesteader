using System;
using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// Liquids and liquid containers (the kit's liquids category and liquid_container component). A liquid is an item with a
    /// fluid colour, an opacity and a weight per liter (its weight_kg); a liquid container is an item with liquid_capacity_l
    /// that holds ONE liquid at a time, by volume. These are the lookups and the arithmetic; the contents of a particular
    /// container are a (liquid id, liters) pair.
    /// </summary>
    public static class LiquidRules
    {
        public static bool IsLiquid(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && !string.IsNullOrEmpty(info.liquid_color);
        }

        public static bool IsLiquidContainer(string itemId) => Capacity(itemId) > 0f;

        public static float Capacity(string containerId)
        {
            var info = HudBindings.GetCatalogItem(containerId);
            return info != null ? info.liquid_capacity_l : 0f;
        }

        /// <summary>Kilograms per liter of a liquid (the item's weight_kg).</summary>
        public static float WeightPerLiter(string liquidId)
        {
            var info = HudBindings.GetCatalogItem(liquidId);
            return info != null && info.weight_kg > 0f ? info.weight_kg : 1f;
        }

        /// <summary>The fluid colour, with its opacity (0 to 1) as the alpha.</summary>
        public static Color FluidColor(string liquidId)
        {
            var info = HudBindings.GetCatalogItem(liquidId);
            if (info == null || string.IsNullOrEmpty(info.liquid_color) || !ColorUtility.TryParseHtmlString(info.liquid_color, out Color c))
                return new Color(0.5f, 0.7f, 0.9f, 0.35f);
            c.a = Mathf.Clamp01(info.liquid_opacity_pct / 100f);
            return c;
        }

        /// <summary>True when this container takes this liquid (its accepts list: exact ids and #tags; empty = any liquid).</summary>
        public static bool Accepts(string containerId, string liquidId)
        {
            var c = HudBindings.GetCatalogItem(containerId);
            if (c == null || c.liquid_capacity_l <= 0f || !IsLiquid(liquidId)) return false;
            if (c.liquid_accepts == null || c.liquid_accepts.Count == 0) return true;
            foreach (string a in c.liquid_accepts)
                if (!string.IsNullOrEmpty(a) && GrowthRegistry.ToolMatches(a, liquidId)) return true;
            return false;
        }

        /// <summary>Liters of this liquid that still fit, given what the container already holds (one liquid at a time).</summary>
        public static float RoomFor(string containerId, string heldLiquidId, float heldLiters, string liquidId)
        {
            if (!Accepts(containerId, liquidId)) return 0f;
            if (heldLiters > 0.0001f && !string.Equals(heldLiquidId, liquidId, StringComparison.Ordinal)) return 0f;
            return Mathf.Max(0f, Capacity(containerId) - heldLiters);
        }

        /// <summary>Liters a container of this item holds when nothing has been done to it: what it is sold filled with (a jug of water), else none (an empty propane tank).</summary>
        public static float DefaultLiters(string containerId)
        {
            var c = HudBindings.GetCatalogItem(containerId);
            return c != null && !string.IsNullOrEmpty(c.liquid_filled_with) ? Mathf.Min(c.liquid_filled_l > 0f ? c.liquid_filled_l : c.liquid_capacity_l, c.liquid_capacity_l) : 0f;
        }

        /// <summary>
        /// Liters in a carried or placed container, from the number stored with it (a toolbar slot's or a placed object's WireUsed: the same number a spool of wire keeps its used
        /// metres in, so it is saved and travels with the item already). The number is the CHANGE from the default, so an untouched item needs none.
        /// </summary>
        public static float Held(string containerId, float stored) { return Mathf.Clamp(DefaultLiters(containerId) + stored, 0f, Capacity(containerId)); }

        /// <summary>The number to store for the container to hold <paramref name="liters"/>.</summary>
        public static float StoredFor(string containerId, float liters) { return Mathf.Clamp(liters, 0f, Capacity(containerId)) - DefaultLiters(containerId); }

        /// <summary>The liquid a container holds: the one it was filled with, else what it is sold filled with, else the only liquid it takes ("" when it could be several).</summary>
        public static string LiquidIn(string containerId, string filledWith)
        {
            if (!string.IsNullOrEmpty(filledWith)) return filledWith;
            var c = HudBindings.GetCatalogItem(containerId);
            if (c == null) return "";
            if (!string.IsNullOrEmpty(c.liquid_filled_with)) return c.liquid_filled_with;
            return c.liquid_accepts != null && c.liquid_accepts.Count == 1 && !c.liquid_accepts[0].StartsWith("#") ? c.liquid_accepts[0] : "";
        }

        /// <summary>What a container holds, for the look-at panel: "1,200 L of Diesel Fuel (of 3,785 L)" or "Empty (3,785 L)".</summary>
        public static string Describe(string containerId, string filledWith, float stored)
        {
            float held = Held(containerId, stored), cap = Capacity(containerId);
            if (held <= 0.01f) return "Empty (" + UnitFormat.Volume(cap) + ")";
            string liquid = LiquidIn(containerId, filledWith);
            return UnitFormat.Volume(held) + (string.IsNullOrEmpty(liquid) ? "" : " of " + HudBindings.GetItemName(liquid)) + " (of " + UnitFormat.Volume(cap) + ")";
        }

        /// <summary>What the liquid inside weighs.</summary>
        public static float WeightOf(string liquidId, float liters) { return liters * WeightPerLiter(liquidId); }
    }
}
