using Homesteader.Growth;
using Homesteader.Modding;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.UI
{
    /// <summary>
    /// What world object is under the cursor (a structure, animal, placed prop, planted crop or dropped item). WAILA describes it.
    /// Procedural forest trees are not found here: they are baked into chunk meshes, so WailaPanel asks ForestTrees for them.
    /// </summary>
    public static class HoverTarget
    {
        /// <summary>The hovered object's root transform, or null (over the HUD, over bare ground, or nothing there).</summary>
        private static int s_hitFrame = -1, s_findFrame = -1;
        private static Vector2 s_hitPos, s_findPos;
        private static Camera s_hitCam;
        private static RaycastHit[] s_hits = new RaycastHit[0];
        private static Transform s_found;

        /// <summary>
        /// Everything under the pointer, nearest first, from ONE RaycastAll and sort shared by every caller in the same frame (the cursor, WAILA,
        /// the construction card, placement and planting all ask the same question). Colliders destroyed since are skipped by the callers' null check.
        /// </summary>
        public static RaycastHit[] SortedHits(Camera cam, Vector2 screenPos)
        {
            if (s_hitFrame == Time.frameCount && s_hitCam == cam && s_hitPos == screenPos)
            {
                // a collider destroyed since the ray was cast this frame (a panel fitted, an item picked up) is dropped, so no caller trips on it
                bool stale = false;
                foreach (RaycastHit h in s_hits) if (h.collider == null) { stale = true; break; }
                if (stale) s_hits = System.Array.FindAll(s_hits, h => h.collider != null);
                return s_hits;
            }
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            s_hits = hits;
            s_hitFrame = Time.frameCount;
            s_hitCam = cam;
            s_hitPos = screenPos;
            return hits;
        }

        public static Transform Find()
        {
            if (s_findFrame == Time.frameCount && TryGetPointerPos(out Vector2 again) && again == s_findPos) return s_found;   // asked already this frame
            Transform t = FindUncached();
            s_found = t;
            s_findFrame = Time.frameCount;
            TryGetPointerPos(out s_findPos);
            return t;
        }

        private static Transform FindUncached()
        {
            if (!TryGetPointerPos(out Vector2 screenPos)) return null;

            HudBindings hud = HudBindings.Instance;
            if (hud != null && (HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos))) return null;

            Camera cam = GameCamera();
            if (cam == null) return null;

            // Structures/animals have colliders and hit normally. Crops and dropped items deliberately disable theirs
            // (walk-through by design - see PlantedGrowth.ShowModel / WorldItem.TryShow), so they never show up in a physics
            // raycast; fall back to nearest-on-the-ground-plane for those.
            bool solid = TryHoverableHit(cam, screenPos, out RaycastHit hit);
            // a mounted item (a light, a breaker box, a wall battery) has only a trigger box, which the shared query ignores: it counts when it is nearer than the first solid thing
            Transform soft = AttachedObject.All.Count > 0 || WireNode.All.Count > 0
                ? SoftTarget(cam.ScreenPointToRay(screenPos), solid ? hit.distance : float.MaxValue) : null;   // (a second ray, only when something mounted or wired exists)
            if (soft != null) return soft;
            if (solid) return HoverRoot(hit.collider);
            return TryFindNearbyCropOrItem(cam, screenPos);
        }

        /// <summary>
        /// A collider added by GlbAssetResolver sits on the same GameObject as its MeshFilter, which for a multi-part model is a
        /// leaf part, not the whole instance - walk up to the GlbTemplate clone's root so the ENTIRE object is the target.
        /// Falls back to the collider's own transform for anything that isn't a GLB instance (e.g. a plain scene prop).
        /// </summary>
        private static Transform HoverRoot(Collider c)
        {
            GlbTemplate tpl = c.GetComponentInParent<GlbTemplate>();
            return tpl != null ? tpl.transform : c.transform;
        }

        /// <summary>
        /// WAILA sees everything: a mounted item, a wired device or a placed object that is only a trigger (or sits behind a hidden wall's layer) is still a target when it is
        /// nearer than the first solid thing.
        /// </summary>
        private static Transform SoftTarget(Ray ray, float maxDistance)
        {
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.distance > maxDistance) break;
                if (h.collider == null || !h.collider.isTrigger) continue;   // solid things are the normal pass
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                AttachedObject a = h.collider.GetComponentInParent<AttachedObject>();
                if (a != null) return a.transform;
                PlacedObject p = h.collider.GetComponentInParent<PlacedObject>();
                if (p != null) return p.transform;
                WireNode n = h.collider.GetComponentInParent<WireNode>();
                if (n != null) return n.transform;
            }
            return null;
        }

        /// <summary>The first non-ground, non-player thing under the cursor.</summary>
        private static bool TryHoverableHit(Camera cam, Vector2 screenPos, out RaycastHit result)
        {
            result = default;
            RaycastHit[] hits = SortedHits(cam, screenPos);

            foreach (RaycastHit h in hits)
            {
                if (h.collider == null) continue;
                if (IsGround(h.collider)) continue;
                if (IsLandBoundaryWall(h.collider)) continue;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                result = h;
                return true;
            }
            return false;
        }

        /// <summary>Matches PlantingValidator's ground check: terrain or the flat scene "Ground".</summary>
        private static bool IsGround(Collider c)
        {
            return c is TerrainCollider || c.gameObject.name == "Ground";
        }

        /// <summary>The invisible box colliders LandBoundaryController places along owned/unowned tile edges to physically block
        /// the CharacterController. They have no visual and aren't meant to be hoverable.</summary>
        private static bool IsLandBoundaryWall(Collider c)
        {
            return c.gameObject.name.StartsWith("LandWall_");
        }

        /// <summary>Nearest planted crop or dropped item to wherever the mouse ray hits the ground plane, within a small radius.</summary>
        private static Transform TryFindNearbyCropOrItem(Camera cam, Vector2 screenPos)
        {
            var groundPlane = new Plane(Vector3.up, Vector3.zero);
            Ray ray = cam.ScreenPointToRay(screenPos);
            if (!groundPlane.Raycast(ray, out float enter)) return null;
            Vector3 hit = ray.GetPoint(enter);

            const float radius = 0.6f;
            float bestDistSq = radius * radius;
            Transform best = null;

            foreach (PlantedGrowth g in PlantedGrowth.All)
            {
                if (g == null) continue;
                float d = (g.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; best = g.transform; }
            }
            if (best != null) return best;

            foreach (WorldItem it in WorldItem.All)
            {
                if (it == null) continue;
                float d = (it.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; best = it.transform; }
            }
            return best;
        }

        internal static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;

            var iso = IsometricLockedCamera.Current;
            if (iso != null && iso.TryGetComponent(out cam)) return cam;

            return Object.FindAnyObjectByType<Camera>();
        }

        internal static bool TryGetPointerPos(out Vector2 pos)
        {
#if ENABLE_INPUT_SYSTEM
            Mouse m = Mouse.current;
            if (m == null) { pos = default; return false; }
            pos = m.position.ReadValue();
            return true;
#else
            pos = Input.mousePosition;
            return true;
#endif
        }
    }
}
