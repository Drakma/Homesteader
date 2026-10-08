using System.Collections.Generic;
using UnityEngine;
using Homesteader.UI;

namespace Homesteader.Growth
{
    /// <summary>
    /// A portable generator (manifest: power_radius_tiles, max_power_w; pushed like a wheelbarrow). It powers everything that needs electricity (nothing battery powered needs it) within its
    /// radius of tiles, and ALL of a build site it stands in or reaches (the corded tools building it), but never a finished structure: a building runs on its own system. It shares what it makes among what it reaches: asked for more than its
    /// rated power, everything gets that share of its voltage. It runs while it exists: fuel is not modeled yet.
    /// </summary>
    public sealed class PortableGenerator : MonoBehaviour
    {
        public static readonly List<PortableGenerator> All = new List<PortableGenerator>();

        public float RatedW;
        public float RadiusTiles;
        public float DemandW;     // what the things it reaches would draw
        public float Ratio = 1f;  // the share of that it can give: 1 when it can meet it
        public bool Tripped;      // its breaker opened on an overload: it gives nothing until it has cooled (it resets itself)
        public float Heat;        // 0 cool .. 1 trips

        /// <summary>Its rated current in amps (manifest max_current_a), and what it carries now.</summary>
        public float RatedA { get { AssetCatalogItem it = HudBindings.GetCatalogItem(GetComponent<PlacedObject>() != null ? GetComponent<PlacedObject>().ItemId : ""); return it != null ? it.max_current_a : 0f; } }
        public float LoadA { get { return Mathf.Min(DemandW, RatedW * 1.5f) / WireNetwork.AcV; } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { All.Clear(); }

        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        /// <summary>Makes a placed object a generator when its manifest gives it a power radius.</summary>
        public static void Attach(GameObject go, string itemId)
        {
            if (go == null || go.GetComponent<PortableGenerator>() != null) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(itemId);
            if (info == null || info.power_radius_tiles <= 0f || info.max_power_w <= 0f) return;
            var g = go.AddComponent<PortableGenerator>();
            g.RatedW = info.max_power_w;
            g.RadiusTiles = info.power_radius_tiles;
        }

        private bool Covers(Vector3 pos)
        {
            Vector3 d = pos - transform.position;
            d.y = 0f;
            return d.magnitude <= RadiusTiles * PlantingValidator.GridSizeM;
        }

        /// <summary>
        /// True while a portable generator powers this build site: it stands in it or within its radius of it, and then the WHOLE site has power. A finished structure never: a building
        /// runs on its own system.
        /// </summary>
        public static bool Powers(ConstructionSite site)
        {
            if (site == null || site.Finished) return false;
            foreach (PortableGenerator g in All)
                if (g != null && g.RatedW > 0f && g.Ratio > 0f && g.ReachesSite(site)) return true;
            return false;
        }

        private bool ReachesSite(ConstructionSite site)
        {
            Vector3 p = transform.position;
            return site.IsInside(p) || site.DistanceOutside(p) <= RadiusTiles * PlantingValidator.GridSizeM;
        }

        /// <summary>How much of its voltage something at <paramref name="pos"/> gets from the generators that reach it: 0 when none does. For things that need electricity and are NOT part of a building (a building runs on its own system).</summary>
        public static float RatioAt(Vector3 pos)
        {
            float best = 0f;
            foreach (PortableGenerator g in All)
                if (g != null && g.RatedW > 0f && g.Covers(pos)) best = Mathf.Max(best, g.Ratio);
            return best;
        }

        private static float s_nextScan;

        public static void Tick(float dtH = 0f)
        {
            // a generator placed before this existed (or by any other route) has no component yet: found here, so every generator in the world works
            if (Time.unscaledTime >= s_nextScan)
            {
                s_nextScan = Time.unscaledTime + 2f;
                foreach (PlacedObject o in PlacedObject.All)
                    if (o != null && o.GetComponent<PortableGenerator>() == null) Attach(o.gameObject, o.ItemId);
            }
            if (All.Count == 0) return;
            foreach (PortableGenerator g in All) if (g != null) g.DemandW = 0f;
            LightEmitter.ForEachDemand((pos, site, watts) =>
            {
                if (site != null) return;   // a building's lights are the building's: a generator is not connected to structures
                foreach (PortableGenerator g in All)
                    if (g != null && g.Covers(pos)) g.DemandW += watts;
            });
            // the corded tools building at the sites it reaches
            foreach (ConstructionSite s in ConstructionSite.All)
            {
                if (s == null || s.Finished) continue;
                float draw = s.CordedDrawW();
                if (draw <= 0f) continue;
                foreach (PortableGenerator g in All) if (g != null && g.ReachesSite(s)) g.DemandW += draw;
            }
            float dtS = dtH * 3600f;
            foreach (PortableGenerator g in All)
            {
                if (g == null) continue;
                if (g.Tripped)
                {
                    g.Heat = Mathf.Max(0f, g.Heat - dtS / 120f);   // it cools, and resets itself
                    if (g.Heat <= 0f) g.Tripped = false;
                }
                else if (dtS > 0f && g.RatedW > 0f)
                {
                    float r = g.DemandW / (g.RatedW * 1.1f);   // a tenth over is allowed
                    g.Heat = r > 1f ? Mathf.Min(1f, g.Heat + dtS / WireNetwork.TripSeconds(r)) : Mathf.Max(0f, g.Heat - dtS / 600f);
                    if (g.Heat >= 1f) { g.Tripped = true; ToastNotificationSystem.ShowWarning("Generator tripped", "More was wanted than it makes. It resets when it has cooled."); }
                }
                g.Ratio = g.Tripped ? 0f : g.DemandW <= 0.01f ? 1f : Mathf.Clamp01(g.RatedW / g.DemandW);
            }
        }
    }
}
