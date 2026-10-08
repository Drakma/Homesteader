using System.Collections.Generic;
using Homesteader.Kitchen;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Shows what a PLACED dish holds, the way it would look on the table (the Meal Builder serves these on the counter):
    /// a Plated Meal has the foods' icons laid flat on the plate, a Bowl of Food has the soup / stew / salad texture filling the bowl,
    /// and a Drinking Glass is filled with its liquid (colour and opacity from the liquid, height from the litres in it).
    /// A handful of quads and one small mesh per dish, rebuilt only when what is in it changes. The dish models are fixed procedural
    /// ones (tools/make_tableware_assets.py), so the plate, bowl and glass measures below are theirs, taken from the model's own bottom.
    /// </summary>
    public sealed class DishView : MonoBehaviour
    {
        // measures of the tableware models, in metres from the model's bottom
        private const float PlateSurface = 0.011f, PlateIconSize = 0.15f;
        private const float BowlSurface = 0.046f, BowlRadius = 0.074f, BowlCrop = 0.55f;
        private const float GlassFloor = 0.012f, GlassTop = 0.108f, GlassRadiusLow = 0.0285f, GlassRadiusHigh = 0.0362f;

        private PlacedObject _placed;
        private int _signature = int.MinValue;
        private float _next;
        private readonly List<GameObject> _parts = new List<GameObject>();

        private static readonly Dictionary<string, Material> IconMaterials = new Dictionary<string, Material>();
        private static readonly Dictionary<string, Material> LiquidMaterials = new Dictionary<string, Material>();
        private static Mesh _disc;

        /// <summary>Adds the dish display to a placed plate, bowl or glass of the Meal Builder.</summary>
        public static void AttachIfDish(PlacedObject placed)
        {
            if (placed == null) return;
            string id = placed.ItemId;
            if (id != MealBuilder.PlatedMeal && id != MealBuilder.BowlMeal && id != MealBuilder.Glass) return;
            if (placed.GetComponent<DishView>() != null) return;
            placed.gameObject.AddComponent<DishView>()._placed = placed;
        }

        private void Update()
        {
            if (_placed == null || Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + 0.25f;
            int sig = Signature();
            if (sig == _signature) return;
            if (Rebuild()) _signature = sig;   // not ready yet (the model is still loading): try again on the next tick
        }

        private int Signature()
        {
            int h = 17;
            h = h * 31 + (_placed.LiquidId != null ? _placed.LiquidId.GetHashCode() : 0);
            h = h * 31 + Mathf.RoundToInt(_placed.WireUsed * 1000f);
            if (_placed.Contents != null)
                foreach (ContainerStack c in _placed.Contents) { h = h * 31 + (c.ItemId != null ? c.ItemId.GetHashCode() : 0); h = h * 31 + c.Count; }
            return h;
        }

        private bool Rebuild()
        {
            foreach (GameObject g in _parts) if (g != null) Destroy(g);
            _parts.Clear();
            if (!ModelBounds(out Bounds b)) return false;   // the model has not loaded yet
            switch (_placed.ItemId)
            {
                case MealBuilder.PlatedMeal: BuildPlate(b); break;
                case MealBuilder.BowlMeal: BuildBowl(b); break;
                default: BuildGlass(b); break;
            }
            return true;
        }

        /// <summary>The dish's own model in its local space (what this view added is left out).</summary>
        private bool ModelBounds(out Bounds b)
        {
            bool any = false;
            b = default;
            foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name.StartsWith("Dish")) continue;
                Bounds mb = mf.sharedMesh.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = mb.center + new Vector3((i & 1) == 0 ? -mb.extents.x : mb.extents.x, (i & 2) == 0 ? -mb.extents.y : mb.extents.y, (i & 4) == 0 ? -mb.extents.z : mb.extents.z);
                    Vector3 local = transform.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { b = new Bounds(local, Vector3.zero); any = true; } else b.Encapsulate(local);
                }
            }
            return any;
        }

        // ---------------------------------------------------------------- plate: the foods' icons laid flat on it

        private void BuildPlate(Bounds b)
        {
            var foods = new List<string>();
            if (_placed.Contents != null)
                foreach (ContainerStack c in _placed.Contents)
                    for (int i = 0; i < c.Count && foods.Count < MealBuilder.MaxFoods; i++) foods.Add(c.ItemId);
            if (foods.Count == 0) return;
            float y = b.min.y + PlateSurface;
            float size = foods.Count == 1 ? PlateIconSize : foods.Count == 2 ? 0.115f : 0.098f;
            for (int i = 0; i < foods.Count; i++)
            {
                Vector2 at = PlatePlace(foods.Count, i);
                var icon = new GameObject("DishIcon");
                icon.transform.SetParent(transform, false);
                icon.transform.localPosition = new Vector3(b.center.x + at.x, y + 0.0006f * (i + 1), b.center.z + at.y);
                icon.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);   // a quad faces -Z by default: lay it flat, facing up
                icon.transform.localScale = new Vector3(size, size, 1f);
                icon.AddComponent<MeshFilter>().sharedMesh = FillLook.QuadMesh;
                var mr = icon.AddComponent<MeshRenderer>();
                mr.sharedMaterial = IconMaterial(foods[i]);
                mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                _parts.Add(icon);
            }
        }

        /// <summary>Where food <paramref name="i"/> of <paramref name="n"/> sits on the plate (x, z from its middle).</summary>
        private static Vector2 PlatePlace(int n, int i)
        {
            switch (n)
            {
                case 1: return Vector2.zero;
                case 2: return new Vector2(i == 0 ? -0.058f : 0.058f, 0f);
                case 3: return i == 0 ? new Vector2(0f, 0.056f) : new Vector2(i == 1 ? -0.058f : 0.058f, -0.036f);
                default: return new Vector2(i % 2 == 0 ? -0.052f : 0.052f, i < 2 ? 0.052f : -0.052f);
            }
        }

        // ---------------------------------------------------------------- bowl: the soup / stew / salad texture fills it

        private void BuildBowl(Bounds b)
        {
            string food = null;
            if (_placed.Contents != null)
                foreach (ContainerStack c in _placed.Contents) if (c.Count > 0) { food = c.ItemId; break; }
            if (food == null) return;
            var disc = new GameObject("DishSurface");
            disc.transform.SetParent(transform, false);
            disc.transform.localPosition = new Vector3(b.center.x, b.min.y + BowlSurface, b.center.z);
            disc.transform.localScale = new Vector3(BowlRadius, 1f, BowlRadius);
            disc.AddComponent<MeshFilter>().sharedMesh = Disc();
            var mr = disc.AddComponent<MeshRenderer>();
            mr.sharedMaterial = IconMaterial(food);
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _parts.Add(disc);
        }

        /// <summary>A unit-radius disc lying flat facing up; its UVs cover only the middle of the icon, so the food's own texture shows and not the bowl round it.</summary>
        private static Mesh Disc()
        {
            if (_disc != null) return _disc;
            const int seg = 28;
            var v = new Vector3[seg + 1];
            var uv = new Vector2[seg + 1];
            var n = new Vector3[seg + 1];
            var t = new int[seg * 3];
            v[0] = Vector3.zero; uv[0] = new Vector2(0.5f, 0.5f); n[0] = Vector3.up;
            for (int i = 0; i < seg; i++)
            {
                float a = i * Mathf.PI * 2f / seg;
                float cx = Mathf.Cos(a), cz = Mathf.Sin(a);
                v[i + 1] = new Vector3(cx, 0f, cz);
                uv[i + 1] = new Vector2(0.5f + cx * 0.5f * BowlCrop, 0.5f + cz * 0.5f * BowlCrop);
                n[i + 1] = Vector3.up;
                t[i * 3] = 0; t[i * 3 + 1] = (i + 1) % seg + 1; t[i * 3 + 2] = i + 1;   // wound so the face looks up
            }
            _disc = new Mesh { name = "DishDisc", vertices = v, uv = uv, normals = n, triangles = t };
            return _disc;
        }

        // ---------------------------------------------------------------- glass: filled with its liquid

        private void BuildGlass(Bounds b)
        {
            string liquid = LiquidRules.LiquidIn(_placed.ItemId, _placed.LiquidId);
            float cap = LiquidRules.Capacity(_placed.ItemId);
            float held = LiquidRules.Held(_placed.ItemId, _placed.WireUsed);
            if (string.IsNullOrEmpty(liquid) || cap <= 0f || held < 0.005f) return;
            float fill = Mathf.Clamp01(held / cap);
            float low = b.min.y + GlassFloor;
            float height = (GlassTop - GlassFloor) * fill;
            float rTop = Mathf.Lerp(GlassRadiusLow, GlassRadiusHigh, fill);
            var go = new GameObject("DishLiquid");
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(b.center.x, low, b.center.z);
            go.AddComponent<MeshFilter>().sharedMesh = Frustum(GlassRadiusLow, rTop, height);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = LiquidMaterial(liquid);
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _parts.Add(go);
        }

        /// <summary>The liquid in a glass: a short cone (wider at the top) with a flat top, from y = 0 up to <paramref name="height"/>.</summary>
        private static Mesh Frustum(float rLow, float rHigh, float height)
        {
            const int seg = 24;
            var v = new List<Vector3>();
            var n = new List<Vector3>();
            var t = new List<int>();
            for (int i = 0; i <= seg; i++)   // the side
            {
                float a = i * Mathf.PI * 2f / seg;
                var dir = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
                v.Add(dir * rLow); n.Add(dir);
                v.Add(new Vector3(0f, height, 0f) + dir * rHigh); n.Add(dir);
            }
            for (int i = 0; i < seg; i++)
            {
                int k = i * 2;
                t.AddRange(new[] { k, k + 1, k + 2, k + 2, k + 1, k + 3 });
                t.AddRange(new[] { k, k + 2, k + 1, k + 2, k + 3, k + 1 });   // and its back, so the cone shows from inside too
            }
            int centre = v.Count;   // the top
            v.Add(new Vector3(0f, height, 0f)); n.Add(Vector3.up);
            int ring = v.Count;
            for (int i = 0; i < seg; i++)
            {
                float a = i * Mathf.PI * 2f / seg;
                v.Add(new Vector3(Mathf.Cos(a) * rHigh, height, Mathf.Sin(a) * rHigh)); n.Add(Vector3.up);
            }
            for (int i = 0; i < seg; i++) t.AddRange(new[] { centre, ring + (i + 1) % seg, ring + i });
            var mesh = new Mesh { name = "DishLiquid" };
            mesh.SetVertices(v); mesh.SetNormals(n); mesh.SetTriangles(t, 0);
            return mesh;
        }

        private void OnDestroy()
        {
            // the liquid's mesh is built per dish; the icon discs and materials are shared
            foreach (GameObject g in _parts)
            {
                if (g == null) continue;
                var mf = g.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null && mf.sharedMesh.name == "DishLiquid") Destroy(mf.sharedMesh);
            }
        }

        // ---------------------------------------------------------------- materials (one per food / liquid, shared)

        private static Material IconMaterial(string itemId)
        {
            if (IconMaterials.TryGetValue(itemId, out Material m) && m != null) return m;
            m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "DishIcon_" + itemId };
            Texture2D icon = PhoneController.GetItemIcon(null, itemId);
            m.SetColor("_BaseColor", icon != null ? Color.white : new Color(0.7f, 0.55f, 0.35f));
            if (icon != null) m.SetTexture("_BaseMap", icon);
            m.SetFloat("_Smoothness", 0.1f);
            m.SetFloat("_Cull", 0f);                       // seen from either side
            m.SetFloat("_AlphaClip", 1f);                  // the icon's transparent corners drop out
            m.SetFloat("_Cutoff", 0.5f);
            m.EnableKeyword("_ALPHATEST_ON");
            m.renderQueue = 2450;
            IconMaterials[itemId] = m;
            return m;
        }

        private static Material LiquidMaterial(string liquidId)
        {
            if (LiquidMaterials.TryGetValue(liquidId, out Material m) && m != null) return m;
            Color c = LiquidRules.FluidColor(liquidId);
            c.a = Mathf.Max(c.a, 0.75f);                  // a glass of water still reads as filled
            m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "DishLiquid_" + liquidId };
            m.SetColor("_BaseColor", c);
            m.SetFloat("_Smoothness", 0.7f);
            m.SetFloat("_Surface", 1f);                    // transparent
            m.SetFloat("_Blend", 0f);
            m.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            m.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            m.SetFloat("_ZWrite", 0f);
            m.SetOverrideTag("RenderType", "Transparent");
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = 3000;
            LiquidMaterials[liquidId] = m;
            return m;
        }
    }
}
