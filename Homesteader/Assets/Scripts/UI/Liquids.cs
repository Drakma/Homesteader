using System;
using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// Liquids and liquid containers (the kit's liquids category and liquid_container component). A liquid is an item with a
    /// fluid colour, an opacity and a weight per litre (its weight_kg); a liquid container is an item with liquid_capacity_l
    /// that holds ONE liquid at a time, by volume. These are the lookups and the arithmetic; the contents of a particular
    /// container are a (liquid id, litres) pair.
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

        /// <summary>Kilograms per litre of a liquid (the item's weight_kg).</summary>
        public static float WeightPerLitre(string liquidId)
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

        /// <summary>Litres of this liquid that still fit, given what the container already holds (one liquid at a time).</summary>
        public static float RoomFor(string containerId, string heldLiquidId, float heldLitres, string liquidId)
        {
            if (!Accepts(containerId, liquidId)) return 0f;
            if (heldLitres > 0.0001f && !string.Equals(heldLiquidId, liquidId, StringComparison.Ordinal)) return 0f;
            return Mathf.Max(0f, Capacity(containerId) - heldLitres);
        }

        /// <summary>What the liquid inside weighs.</summary>
        public static float WeightOf(string liquidId, float litres) { return litres * WeightPerLitre(liquidId); }
    }
}
