using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Growth
{
    /// <summary>
    /// The fixtures that use water (docs/SEPTIC.md): a sink, a flush toilet, the shower, the washers and the dishwashers (manifest category_fields.water_per_use_l).
    /// Standing in a finished building, a right click uses one: it takes its liters from the building's water (the tanks its inlet reaches, as the taps do) and
    /// sends them down the drain to the building's septic system (<see cref="Septic.Drain"/>). An electric one (power_draw_w) also needs the building's power.
    /// A fixture that cannot drain, has no water or no power says why and does nothing. Shift + right click picks it up as usual.
    /// </summary>
    public static class Fixtures
    {
        private const float Reach = 3f;
        private static Material s_drops;

        /// <summary>A right click; true when it was on a fixture in a building (so nothing else reacts to it).</summary>
        public static bool TryRightClick(Transform player)
        {
            Keyboard kb = Keyboard.current;
            if (kb != null && kb.shiftKey.isPressed) return false;   // Shift: pick it up
            PlacedObject o = PlacementController.PlacedUnderCursor();
            if (o == null) return false;
            AssetCatalogItem it = HudBindings.GetCatalogItem(o.ItemId);
            if (it == null || it.water_per_use_l <= 0f) return false;
            ConstructionSite site = null;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.Finished && s.IsInside(o.transform.position)) { site = s; break; }
            if (site == null) return false;                          // out in the yard it is just an object: picked up as usual
            if (player != null && Vector3.Distance(player.position, o.transform.position) > Reach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to use it.");
                return true;
            }
            float liters = it.water_per_use_l;
            string name = HudBindings.GetItemName(o.ItemId);
            if (!Septic.Drain(site, liters, false, out string why)) { ToastNotificationSystem.ShowInfo("It won't drain", why); return true; }
            if (it.power_draw_w > 0f && WireNetwork.SupplyRatio(site) < 0.85f)
            {
                ToastNotificationSystem.ShowInfo("No power", "The " + name + " needs the building's power.");
                return true;
            }
            WireNetwork.WaterFor(site, out float all, out float _);
            if (all < liters)
            {
                ToastNotificationSystem.ShowInfo("No water", all < 0.5f ? "The building has no water: pipe its water inlet to a tank (through a pump from a cistern)."
                                                                       : "Not enough water: it takes " + UnitFormat.Volume(liters) + ".");
                return true;
            }
            WireNetwork.DrawWater(site, liters, false, out string _, out float _);
            Septic.Drain(site, liters, true, out string _);
            Splash(o);
            return true;
        }

        /// <summary>The water running: a short spray of drops at the fixture (the result on screen; no toast).</summary>
        private static void Splash(PlacedObject o)
        {
            Bounds b = new Bounds(o.transform.position + Vector3.up * 0.5f, Vector3.one * 0.5f);
            bool any = false;
            foreach (Renderer r in o.GetComponentsInChildren<Renderer>()) { if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
            var go = new GameObject("FixtureWater");
            go.transform.position = new Vector3(b.center.x, b.max.y - 0.05f, b.center.z);
            go.transform.rotation = Quaternion.LookRotation(Vector3.down);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.duration = 1.2f;
            main.loop = false;
            main.startLifetime = 0.5f;
            main.startSpeed = 1.2f;
            main.startSize = 0.025f;
            main.gravityModifier = 1f;
            main.startColor = new Color(0.65f, 0.8f, 0.95f, 0.8f);
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            var em = ps.emission;
            em.rateOverTime = 70f;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 12f;
            shape.radius = 0.03f;
            var pr = go.GetComponent<ParticleSystemRenderer>();
            if (s_drops == null)
            {
                Shader sh = Shader.Find("Universal Render Pipeline/Particles/Unlit") ?? Shader.Find("Sprites/Default");
                s_drops = new Material(sh) { hideFlags = HideFlags.DontSave };
                s_drops.SetFloat("_Surface", 1);
                s_drops.SetColor("_BaseColor", Color.white);
                s_drops.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
                s_drops.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            }
            pr.sharedMaterial = s_drops;
            ps.Play();
            Object.Destroy(go, 2.5f);
        }
    }
}
