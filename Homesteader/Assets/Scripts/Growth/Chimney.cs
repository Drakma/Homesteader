using System.Collections.Generic;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>What a chimney is made of and how tall (the geometry is built from it, so a saved one is rebuilt the same).</summary>
    public struct ChimneySpec
    {
        public float Thickness;   // the wall it stands against, metres
        public float Bottom;      // the lowest point of the stack, local y (below the floor line: the ground it stands on)
        public float Top;         // the top of the stack, local y (floor line = 0)
        public bool Brick;        // brick; false = fieldstone
    }

    /// <summary>Where a chimney kit would go, or why not.</summary>
    public struct ChimneyPlan
    {
        public bool Valid;
        public string Reason;
        public ConstructionSite Site;
        public Vector3 Origin;       // on the OUTER face of the wall, at the floor line
        public Quaternion Rotation;  // +z points out of the building, +x runs along the wall
        public ChimneySpec Spec;
    }

    /// <summary>
    /// A chimney built from a kit (properties.attach_surface = "chimney") on an outside wall of a finished building, aimed at from outside or from inside. The stack stands OUTSIDE the wall
    /// from the ground up to a metre past the roof it goes through; inside, a mantel-height breast with a firebox and a hearth stands against the wall. The firebox is a working
    /// fireplace (<see cref="Fireplace"/>). It is a child of the building, saved with it (GameSave.chimneys), and a wrench (Shift + right click) takes it down again.
    /// </summary>
    public sealed class PlacedChimney : MonoBehaviour
    {
        public static readonly List<PlacedChimney> All = new List<PlacedChimney>();
        public const float ReachMetres = 4f;

        public ConstructionSite Site { get; private set; }
        public string KitId { get; private set; }
        public ChimneySpec Spec { get; private set; }
        public Fireplace Fire { get; private set; }
        public float FuelMinutes;     // game minutes of wood in the firebox
        public bool FireLit;

        public static PlacedChimney Spawn(ConstructionSite site, string kitId, Vector3 position, Quaternion rotation, ChimneySpec spec, float fuel = 0f, bool lit = false)
        {
            var go = new GameObject("PlacedChimney");
            go.transform.SetParent(site.transform, true);
            go.transform.SetPositionAndRotation(position, rotation);
            var c = go.AddComponent<PlacedChimney>();
            c.Site = site;
            c.KitId = kitId;
            c.Spec = spec;
            c.FuelMinutes = fuel;
            c.FireLit = lit && fuel > 0f;
            GameObject geo = ChimneyBuilder.Build(spec, true, out Transform firebox, out Transform flue);
            geo.transform.SetParent(go.transform, false);
            c.Fire = go.AddComponent<Fireplace>();
            c.Fire.Bind(c, geo.transform, firebox, flue);
            return c;
        }

        private void OnEnable() { All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        /// <summary>Distance on the ground from a point to the chimney.</summary>
        public float DistanceTo(Vector3 p)
        {
            Vector3 c = transform.position;
            return new Vector2(p.x - c.x, p.z - c.z).magnitude;
        }

        /// <summary>The chimney under the cursor (the first thing the ray meets, the player aside), or null.</summary>
        public static PlacedChimney UnderCursor()
        {
            Camera cam = Camera.main != null ? Camera.main : FindAnyObjectByType<Camera>();
            if (cam == null || UnityEngine.InputSystem.Mouse.current == null || All.Count == 0) return null;
            return UnderRay(cam.ScreenPointToRay(UnityEngine.InputSystem.Mouse.current.position.ReadValue()));
        }

        public static PlacedChimney UnderRay(Ray ray)
        {
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null || h.collider.GetComponentInParent<PedController>() != null) continue;
                return h.collider.GetComponentInParent<PlacedChimney>();
            }
            return null;
        }

        /// <summary>Shift + right click with a wrench takes a chimney down into the toolbar (a plain right click says how). True when the click was for a chimney.</summary>
        public static bool TryPickUpAtRay(Ray ray, Vector3 playerPos)
        {
            if (!AttachedObject.WrenchInHand()) return false;   // anything else (firewood, a lighter) is for the fireplace: PlacementController handles it
            PlacedChimney c = UnderRay(ray);
            if (c == null) return false;
            string name = HudBindings.GetItemName(c.KitId);
            if (!AttachedObject.WrenchRemoval())
            {
                ToastNotificationSystem.ShowInfo(name, "Take it down with a wrench: Shift + right click.");
                return true;
            }
            if (c.DistanceTo(playerPos) > ReachMetres) { ToastNotificationSystem.ShowInfo("Too far", "Move closer to take it down."); return true; }
            if (c.FuelMinutes > 0f) { ToastNotificationSystem.ShowInfo(name, "Empty the firebox first."); return true; }
            HudState hud = HudState.Active;
            if (hud == null) return false;
            if (hud.AddItemToToolbar(c.KitId, 1, HudBindings.GetMaxStack(c.KitId)) < 1) { ToastNotificationSystem.ShowWarning("Toolbar full", "No free toolbar slot for that."); return true; }
            HudBindings.Instance?.RefreshToolbar();
            Destroy(c.gameObject);
            return true;
        }

        // ------------------------------------------------------------------ the save

        /// <summary>Everything of one chimney that a save keeps (its building is found by its place in the saved sites).</summary>
        public GameSave.SavedChimney Capture()
        {
            return new GameSave.SavedChimney
            {
                kitId = KitId,
                siteIndex = ConstructionSite.All.IndexOf(Site),
                localPosition = Site.transform.InverseTransformPoint(transform.position),
                localRotation = Quaternion.Inverse(Site.transform.rotation) * transform.rotation,
                thickness = Spec.Thickness, bottom = Spec.Bottom, top = Spec.Top, brick = Spec.Brick,
                fuelMinutes = FuelMinutes, fireLit = FireLit,
            };
        }

        public static List<GameSave.SavedChimney> CaptureAll()
        {
            var list = new List<GameSave.SavedChimney>();
            foreach (PlacedChimney c in All) if (c != null && c.Site != null && ConstructionSite.All.IndexOf(c.Site) >= 0) list.Add(c.Capture());
            return list;
        }

        public static void RestoreAll(List<GameSave.SavedChimney> saved)
        {
            if (saved == null) return;
            foreach (GameSave.SavedChimney s in saved)
            {
                if (s.siteIndex < 0 || s.siteIndex >= ConstructionSite.All.Count) continue;
                ConstructionSite host = ConstructionSite.All[s.siteIndex];
                if (host == null) continue;
                var spec = new ChimneySpec { Thickness = s.thickness, Bottom = s.bottom, Top = s.top, Brick = s.brick };
                Spawn(host, s.kitId, host.transform.TransformPoint(s.localPosition), host.transform.rotation * s.localRotation, spec, s.fuelMinutes, s.fireLit);
            }
        }
    }

    /// <summary>Works out where a chimney kit goes: the outside wall under the cursor, clear of windows, doors and other things, and how high the stack must be.</summary>
    public static class ChimneyPlanner
    {
        public const float StackHalf = 0.45f;       // half the width of the stack and the breast
        public const float StackDepth = 0.6f;       // how far the stack stands out of the wall
        public const float BreastDepth = 0.45f;     // how far the breast stands into the room
        public const float HearthDepth = 0.4f;
        public const float PastRoofM = 1f;          // the stack rises this far past the roof where it goes through
        private const float Reach = 3.5f;
        private const float Margin = 0.2f;          // clear wall wanted either side of the stack
        private const int HiddenLayer = 2;          // Ignore Raycast: where the cutaway puts the walls it hides

        public static ChimneyPlan Plan(Camera cam, Vector2 pointer, string kitId, PedController ped)
        {
            var plan = new ChimneyPlan();
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(pointer), 1000f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                Collider col = h.collider;
                if (col == null || col.GetComponentInParent<PedController>() != null) continue;
                if (col.GetComponentInParent<AttachedObject>() != null || col.GetComponentInParent<PlacedChimney>() != null) continue;
                if (col.gameObject.layer == HiddenLayer) continue;   // a wall the cutaway hides: looked through, to the walls the player can see
                ConstructionSite site = col.GetComponentInParent<ConstructionSite>();
                if (site == null) return plan;                       // the first thing hit is not a building
                plan.Site = site;
                if (!site.Finished) { plan.Reason = "Finish building it first."; return plan; }
                if (!AttachController.IsWallPart(col, site)) { plan.Reason = "Aim at a plain wall."; return plan; }

                // which outside wall: the nearest edge of the wing the cursor is in (a chimney goes on an OUTSIDE wall, from whichever side it is aimed at)
                Quaternion siteRot = site.transform.rotation;
                Vector3 lp = Quaternion.Inverse(siteRot) * (h.point - site.transform.position);
                Rect wr = site.WingRectNear(lp.x, lp.z);
                float dLeft = Mathf.Abs(lp.x - wr.xMin), dRight = Mathf.Abs(wr.xMax - lp.x), dBack = Mathf.Abs(lp.z - wr.yMin), dFront = Mathf.Abs(wr.yMax - lp.z);
                float edge = Mathf.Min(Mathf.Min(dLeft, dRight), Mathf.Min(dBack, dFront));
                if (edge > 0.8f) { plan.Reason = "A chimney goes on an outside wall."; return plan; }
                Vector3 nLocal = edge == dLeft ? Vector3.left : edge == dRight ? Vector3.right : edge == dBack ? Vector3.back : Vector3.forward;
                Vector3 nOut = siteRot * nLocal;
                Vector3 tangent = Vector3.Cross(Vector3.up, nOut);

                // the outer face of the wall at the cursor (looked for from outside, so a spot aimed at from inside lands on the same face)
                Vector3 po = h.point;
                bool found = false;
                RaycastHit[] probe = Physics.RaycastAll(h.point + nOut * 1.3f, -nOut, 2.8f, ~0, QueryTriggerInteraction.Ignore);
                System.Array.Sort(probe, (x, y) => x.distance.CompareTo(y.distance));
                foreach (RaycastHit ph in probe)
                {
                    if (ph.collider.GetComponentInParent<ConstructionSite>() != site || ph.collider.GetComponentInParent<AttachedObject>() != null || ph.collider.GetComponentInParent<PlacedChimney>() != null) continue;
                    if (!AttachController.IsWallPart(ph.collider, site)) continue;
                    po = ph.point; found = true; break;
                }
                if (!found) { plan.Reason = "Aim at a plain wall."; return plan; }
                float along = Vector3.Dot(po - site.transform.position, tangent);
                po += tangent * (Mathf.Round(along / 0.05f) * 0.05f - along);   // along the wall in small steps

                float thickness = AttachedObject.MeasureWall(site, po, nOut);
                if (thickness < 0.03f || thickness > 0.65f) thickness = AttachedObject.DefaultWall;

                // the floor inside, the ground outside, the wall top
                float floorY = site.transform.position.y + 0.3f;
                if (Physics.Raycast(po - nOut * (thickness + 0.7f) + Vector3.up * 1.5f, Vector3.down, out RaycastHit fh, 4f, ~0, QueryTriggerInteraction.Ignore) && fh.collider.GetComponentInParent<ConstructionSite>() == site)
                    floorY = fh.point.y;
                Vector3 outside = po + nOut * (StackDepth * 0.5f);
                float groundY = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(outside);
                float ceilY = site.CeilingY();
                po.y = floorY;

                plan.Origin = po;
                plan.Rotation = Quaternion.LookRotation(nOut, Vector3.up);
                var spec = new ChimneySpec { Thickness = thickness, Bottom = Mathf.Min(0f, groundY - floorY) - 0.2f, Brick = !(kitId ?? "").Contains("stone") };
                spec.Top = RoofTop(site, po, nOut, tangent, thickness, floorY, ceilY) + PastRoofM - floorY;
                plan.Spec = spec;

                plan.Reason = Check(site, ped, po, nOut, tangent, thickness, floorY, groundY, ceilY);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
        }

        /// <summary>The highest roof over the stack and the wall beside it (world y), or the top of the walls when there is none.</summary>
        private static float RoofTop(ConstructionSite site, Vector3 po, Vector3 nOut, Vector3 tangent, float thickness, float floorY, float ceilY)
        {
            float top = ceilY;
            for (float x = -StackHalf - 0.1f; x <= StackHalf + 0.1f + 1e-3f; x += 0.15f)
                for (float z = -thickness; z <= StackDepth + 0.2f; z += 0.2f)
                {
                    Vector3 s = po + tangent * x + nOut * z;
                    RaycastHit[] hits = Physics.RaycastAll(new Vector3(s.x, floorY + 40f, s.z), Vector3.down, 80f, ~0, QueryTriggerInteraction.Ignore);
                    foreach (RaycastHit h in hits)
                    {
                        if (h.collider.GetComponentInParent<ConstructionSite>() != site || h.collider.GetComponentInParent<PlacedChimney>() != null) continue;
                        if (!IsRoof(h.collider, site)) continue;
                        if (h.point.y > top) top = h.point.y;
                    }
                }
            return top;
        }

        private static bool IsRoof(Collider c, ConstructionSite site)
        {
            Transform stop = site.VisualRoot != null ? site.VisualRoot : site.transform;
            for (Transform t = c.transform; t != null && t != stop && t != site.transform; t = t.parent)
                if (t.name.StartsWith("Roof")) return true;
            return false;
        }

        /// <summary>Why a chimney cannot go here, or null: too far, a window or a door in the wall there, something standing where the stack or the breast would be.</summary>
        private static string Check(ConstructionSite site, PedController ped, Vector3 po, Vector3 nOut, Vector3 tangent, float thickness, float floorY, float groundY, float ceilY)
        {
            if (ped != null && new Vector2(po.x - ped.transform.position.x, po.z - ped.transform.position.z).magnitude > Reach + StackDepth) return "Too far: move closer.";
            foreach (PlacedChimney other in PlacedChimney.All)
                if (other != null && other.Site == site && new Vector2(other.transform.position.x - po.x, other.transform.position.z - po.z).magnitude < 1.6f) return "Too close to another chimney.";

            // the wall behind the whole width of the stack (and a hand either side), floor to eaves, must be plain wall: a ray from outside through every spot
            // that does not meet a wall part (a window or a door opening, an open door) or meets a door, a window, its frame or its trim, says no
            float w = StackHalf + Margin;
            for (float y = floorY + 0.15f; y <= ceilY - 0.1f + 1e-3f; y += 0.4f)
                for (float x = -w; x <= w + 1e-3f; x += 0.15f)
                {
                    Vector3 from = po + tangent * x + Vector3.up * (y - floorY) + nOut * 0.8f;
                    RaycastHit[] rays = Physics.RaycastAll(from, -nOut, 0.8f + thickness + 0.5f, ~0, QueryTriggerInteraction.Ignore);
                    System.Array.Sort(rays, (a, b) => a.distance.CompareTo(b.distance));
                    bool wall = false;
                    foreach (RaycastHit r in rays)
                    {
                        if (r.collider.GetComponentInParent<ConstructionSite>() != site || r.collider.GetComponentInParent<AttachedObject>() != null || r.collider.GetComponentInParent<PlacedChimney>() != null) continue;
                        wall = AttachController.IsWallPart(r.collider, site) && r.distance < 0.8f + 0.3f;
                        break;
                    }
                    if (!wall) return "A window or door is in the way.";
                }

            // anything mounted there (a light, a breaker box)
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != site) continue;
                Vector3 d = a.transform.position - po;
                if (Mathf.Abs(Vector3.Dot(d, tangent)) < StackHalf + 0.25f && Mathf.Abs(Vector3.Dot(d, nOut)) < thickness + BreastDepth + 0.6f && d.y > -0.3f && d.y < 2.6f) return "Something is mounted there.";
            }

            // the stack outside, the breast and hearth inside: nothing placed, planted or built there
            Quaternion rot = Quaternion.LookRotation(nOut, Vector3.up);
            Vector3 stackMid = po + nOut * (StackDepth * 0.5f);
            stackMid.y = Mathf.Max(groundY, floorY - 0.4f) + 0.3f + 0.7f;   // from 30 cm over the ground, 1.4 m tall
            string reason = Overlaps(stackMid, new Vector3(StackHalf, 0.7f, StackDepth * 0.5f), rot, site);
            if (reason != null) return reason;
            float roomZ = -(thickness + BreastDepth + HearthDepth * 0.5f);
            return Overlaps(po + nOut * roomZ + Vector3.up * 0.65f, new Vector3(StackHalf + 0.1f, 0.55f, (BreastDepth + HearthDepth) * 0.5f), rot, site);
        }

        private static string Overlaps(Vector3 centre, Vector3 half, Quaternion rot, ConstructionSite site)
        {
            foreach (Collider c in Physics.OverlapBox(centre, half, rot, ~0, QueryTriggerInteraction.Ignore))
            {
                if (c is TerrainCollider || c.gameObject.name == "Ground") continue;
                if (c.GetComponentInParent<PedController>() != null) continue;
                ConstructionSite s = c.GetComponentInParent<ConstructionSite>();
                if (s != null)
                {
                    for (Transform t = c.transform; t != null && t != s.transform; t = t.parent)
                        if (t.name.StartsWith("Porch")) return "The porch is in the way.";
                    continue;                                          // the building's own walls, floor and foundation
                }
                if (c.GetComponentInParent<PlacedChimney>() != null) return "Too close to another chimney.";
                return "Something is in the way.";
            }
            return null;
        }
    }

    /// <summary>Builds the chimney: the stack with a flue hole in its cap, the breast with a firebox, the mantel and the hearth, all from boxes with brick or stone drawn in metres.</summary>
    public static class ChimneyBuilder
    {
        public const string StackName = "ChimneyStack";                 // the outside part: StructureCutaway hides it with the roof
        private const float TileW = 0.69f, TileH = 0.6f;     // one picture of the masonry covers this much wall
        private static readonly Dictionary<string, Material> s_mats = new Dictionary<string, Material>();

        private sealed class Boxes
        {
            public readonly List<Vector3> V = new List<Vector3>();
            public readonly List<Vector3> N = new List<Vector3>();
            public readonly List<Vector2> UV = new List<Vector2>();
            public readonly List<int> T = new List<int>();

            // one box, x across, y up, z out; the picture is laid in metres on every face
            public void Box(float x0, float x1, float y0, float y1, float z0, float z1)
            {
                if (x1 - x0 < 1e-4f || y1 - y0 < 1e-4f || z1 - z0 < 1e-4f) return;
                Face(new Vector3(x0, y0, z1), new Vector3(x1, y0, z1), new Vector3(x1, y1, z1), new Vector3(x0, y1, z1), Vector3.forward, 0, 1);    // +z
                Face(new Vector3(x1, y0, z0), new Vector3(x0, y0, z0), new Vector3(x0, y1, z0), new Vector3(x1, y1, z0), Vector3.back, 0, 1);       // -z
                Face(new Vector3(x1, y0, z1), new Vector3(x1, y0, z0), new Vector3(x1, y1, z0), new Vector3(x1, y1, z1), Vector3.right, 2, 1);      // +x
                Face(new Vector3(x0, y0, z0), new Vector3(x0, y0, z1), new Vector3(x0, y1, z1), new Vector3(x0, y1, z0), Vector3.left, 2, 1);       // -x
                Face(new Vector3(x0, y1, z1), new Vector3(x1, y1, z1), new Vector3(x1, y1, z0), new Vector3(x0, y1, z0), Vector3.up, 0, 2);        // +y
                Face(new Vector3(x0, y0, z0), new Vector3(x1, y0, z0), new Vector3(x1, y0, z1), new Vector3(x0, y0, z1), Vector3.down, 0, 2);      // -y
            }

            private void Face(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 n, int uAxis, int vAxis)
            {
                int i = V.Count;
                foreach (Vector3 p in new[] { a, b, c, d })
                {
                    V.Add(p); N.Add(n);
                    UV.Add(new Vector2(p[uAxis] / TileW, p[vAxis] / TileH));
                }
                T.Add(i); T.Add(i + 1); T.Add(i + 2);   // clockwise seen from outside
                T.Add(i); T.Add(i + 2); T.Add(i + 3);
            }

            public Mesh ToMesh(string name)
            {
                var m = new Mesh { name = name };
                m.SetVertices(V); m.SetNormals(N); m.SetUVs(0, UV); m.SetTriangles(T, 0);
                m.RecalculateBounds();
                return m;
            }
        }

        /// <summary>The whole chimney, standing at the origin: +z out of the wall (the outer face is z = 0), +x along the wall, y up from the floor line. Empties: FireboxPoint, SmokePoint.</summary>
        public static GameObject Build(ChimneySpec s, bool solid, out Transform firebox, out Transform flue)
        {
            var root = new GameObject("Chimney");
            float T = s.Thickness;
            float half = ChimneyPlanner.StackHalf, depth = ChimneyPlanner.StackDepth;
            var masonry = new Boxes();   // the STACK (outside, up through the roof): hidden by the cutaway
            var stone = new Boxes();
            var soot = new Boxes();

            // the stack: from the ground to 12 cm under the top, with the cap and its flue hole (the flue floor is 5 cm thick: no two faces within millimetres of each other)
            float zIn = -0.02f, zOut = depth, top = s.Top;
            masonry.Box(-half, half, s.Bottom, top - 0.12f, zIn, zOut);
            float ch = half + 0.06f, hole = 0.14f, zc = (zIn + zOut) * 0.5f, zcOut = zOut + 0.06f;
            float c0 = top - 0.2f, c1 = top + 0.08f;
            stone.Box(-ch, ch, c0, c1, zIn, zc - hole);
            stone.Box(-ch, ch, c0, c1, zc + hole, zcOut);
            stone.Box(-ch, -hole, c0, c1, zc - hole, zc + hole);
            stone.Box(hole, ch, c0, c1, zc - hole, zc + hole);
            soot.Box(-hole, hole, top - 0.12f, top - 0.07f, zc - hole, zc + hole);

            var bMasonry = new Boxes();   // the BREAST (inside, mantel height): stays in the cutaway
            var bStone = new Boxes();
            var bSoot = new Boxes();
            // the breast inside: a back, two pillars, a lintel, the firebox floor, the mantel and a hearth in front. The room is on the -z side of the wall.
            float zi = -T + 0.02f;                                   // against the wall's inner face
            float bz = -T - ChimneyPlanner.BreastDepth;              // the front of the breast
            float fireDepth = 0.3f;
            float ow = half * 0.58f, fz0 = 0.05f, fz1 = 0.72f, breastTop = 1.15f;
            bMasonry.Box(-half, half, 0f, breastTop, bz + fireDepth, zi);
            bMasonry.Box(-half, -ow, 0f, breastTop, bz, zi);
            bMasonry.Box(ow, half, 0f, breastTop, bz, zi);
            bMasonry.Box(-half, half, fz1, breastTop, bz, zi);
            bStone.Box(-half - 0.08f, half + 0.08f, breastTop, breastTop + 0.05f, bz - 0.08f, zi);
            bMasonry.Box(-ow, ow, 0f, fz0, bz, zi);
            const float e = 0.004f;                                  // the soot lining, 4 mm proud
            bSoot.Box(-ow, ow, fz0, fz1, bz + fireDepth - e, bz + fireDepth);
            bSoot.Box(-ow, -ow + e, fz0, fz1, bz, bz + fireDepth);
            bSoot.Box(ow - e, ow, fz0, fz1, bz, bz + fireDepth);
            bSoot.Box(-ow, ow, fz1 - e, fz1, bz, bz + fireDepth);
            bSoot.Box(-ow, ow, fz0, fz0 + e, bz, bz + fireDepth);
            bStone.Box(-half - 0.1f, half + 0.1f, 0f, 0.05f, bz - ChimneyPlanner.HearthDepth, bz);

            // two groups: "Stack" (outside, up through the roof: the cutaway hides it) and "Breast" (inside)
            var stackGroup = new GameObject(StackName);
            stackGroup.transform.SetParent(root.transform, false);
            AddPart(stackGroup.transform, "Masonry", masonry, GetMaterial(s.Brick, 0));
            AddPart(stackGroup.transform, "Stone", stone, GetMaterial(s.Brick, 1));
            AddPart(stackGroup.transform, "Soot", soot, GetMaterial(s.Brick, 2));
            var breastGroup = new GameObject("Breast");
            breastGroup.transform.SetParent(root.transform, false);
            AddPart(breastGroup.transform, "Masonry", bMasonry, GetMaterial(s.Brick, 0));
            AddPart(breastGroup.transform, "Stone", bStone, GetMaterial(s.Brick, 1));
            AddPart(breastGroup.transform, "Soot", bSoot, GetMaterial(s.Brick, 2));

            firebox = new GameObject("FireboxPoint").transform;
            firebox.SetParent(root.transform, false);
            firebox.localPosition = new Vector3(0f, fz0, bz + fireDepth * 0.5f);
            firebox.localRotation = Quaternion.Euler(0f, 90f, 0f);   // its local z runs along the wall, where the logs lie
            flue = new GameObject("SmokePoint").transform;
            flue.SetParent(root.transform, false);
            flue.localPosition = new Vector3(0f, top + 0.08f, zc);

            if (solid)
            {
                var stackCols = new GameObject("Colliders");     // (the stack's own: the cutaway moves them off the mouse's rays when it hides the stack)
                stackCols.transform.SetParent(stackGroup.transform, false);
                AddBox(stackCols, new Vector3(0f, (s.Bottom + c1) * 0.5f, (zIn + zcOut) * 0.5f), new Vector3(ch * 2f, c1 - s.Bottom, zcOut - zIn));
                var breastCols = new GameObject("Colliders");
                breastCols.transform.SetParent(breastGroup.transform, false);
                AddBox(breastCols, new Vector3(0f, (breastTop + 0.05f) * 0.5f, (bz - 0.08f + zi) * 0.5f), new Vector3((half + 0.08f) * 2f, breastTop + 0.05f, zi - bz + 0.08f));
            }
            return root;
        }

        private static void AddBox(GameObject on, Vector3 centre, Vector3 size)
        {
            var b = on.AddComponent<BoxCollider>();
            b.center = centre;
            b.size = size;
        }

        private static void AddPart(Transform parent, string name, Boxes b, Material m)
        {
            if (b.V.Count == 0) return;
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = b.ToMesh(name);
            go.AddComponent<MeshRenderer>().sharedMaterial = m;
        }

        // ------------------------------------------------------------------ the masonry

        /// <summary>kind 0 = the stack and breast (brick or fieldstone), 1 = the cap, mantel and hearth (grey stone), 2 = soot.</summary>
        private static Material GetMaterial(bool brick, int kind)
        {
            string key = (brick ? "b" : "s") + kind;
            if (s_mats.TryGetValue(key, out Material m) && m != null) return m;
            Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            m = new Material(sh) { name = "Chimney_" + key, hideFlags = HideFlags.DontSave };
            Texture2D tex = kind == 0 ? Masonry(brick) : null;
            Color flat = kind == 1 ? new Color(0.5f, 0.49f, 0.47f) : new Color(0.08f, 0.07f, 0.07f);
            if (tex != null) { m.mainTexture = tex; m.color = Color.white; }
            else { m.color = flat; if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", flat); }
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", 0.1f);
            s_mats[key] = m;
            return m;
        }

        private static float Hash(int a, int b)
        {
            unchecked
            {
                uint h = (uint)(a * 374761393 + b * 668265263);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xFFFF) / 65535f;
            }
        }

        /// <summary>A tileable picture of brick (running bond) or of fieldstone (rough blocks), one tile = TileW x TileH metres.</summary>
        private static Texture2D Masonry(bool brick)
        {
            const int n = 128;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { name = brick ? "ChimneyBrick" : "ChimneyStone", wrapMode = TextureWrapMode.Repeat, hideFlags = HideFlags.DontSave };
            var px = new Color[n * n];
            Color mortar = new Color(0.62f, 0.6f, 0.56f);
            Color baseCol = brick ? new Color(0.55f, 0.22f, 0.16f) : new Color(0.52f, 0.5f, 0.46f);
            int[] rowH = brick ? new[] { 16, 16, 16, 16, 16, 16, 16, 16 } : new[] { 28, 36, 30, 34 };
            int y0 = 0;
            for (int row = 0; row < rowH.Length; row++)
            {
                const int bw = 43;
                int offset = brick ? (row % 2) * 21 : (int)(Hash(row, 7) * 20f);
                for (int y = y0; y < y0 + rowH[row] && y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        int bx = (x + offset) % (brick ? bw : n);
                        int idx = brick ? (x + offset) / bw : (x + offset) / 40;
                        bool seam = brick ? bx < 2 : ((x + offset) % 40 < 2 + (int)(Hash(row, idx) * 2f));
                        bool bed = y - y0 < 2;
                        Color c;
                        if (seam || bed) c = mortar;
                        else
                        {
                            float tone = 0.82f + Hash(row, idx) * 0.36f;
                            c = baseCol * tone;
                            c.a = 1f;
                        }
                        px[y * n + x] = c;
                    }
                y0 += rowH[row];
            }
            for (int y = y0; y < n; y++) for (int x = 0; x < n; x++) px[y * n + x] = mortar;
            tex.SetPixels(px);
            tex.Apply(true);
            return tex;
        }
    }
}
