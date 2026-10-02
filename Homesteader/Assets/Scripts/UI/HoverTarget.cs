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
        public static Transform Find()
        {
            if (!TryGetPointerPos(out Vector2 screenPos)) return null;

            HudBindings hud = HudBindings.Instance;
            if (hud != null && (HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos))) return null;

            Camera cam = GameCamera();
            if (cam == null) return null;

            // Structures/animals have colliders and hit normally. Crops and dropped items deliberately disable theirs
            // (walk-through by design - see PlantedGrowth.ShowModel / WorldItem.TryShow), so they never show up in a physics
            // raycast; fall back to nearest-on-the-ground-plane for those.
            if (TryHoverableHit(cam, screenPos, out RaycastHit hit)) return HoverRoot(hit.collider);
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

        /// <summary>The first non-ground, non-player thing under the cursor.</summary>
        private static bool TryHoverableHit(Camera cam, Vector2 screenPos, out RaycastHit result)
        {
            result = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));

            foreach (RaycastHit h in hits)
            {
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

        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;

            var iso = Object.FindAnyObjectByType<IsometricLockedCamera>();
            if (iso != null && iso.TryGetComponent(out cam)) return cam;

            return Object.FindAnyObjectByType<Camera>();
        }

        private static bool TryGetPointerPos(out Vector2 pos)
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
