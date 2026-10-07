using System.Collections;
using Homesteader.Generation;
using Homesteader.UI;
using Homesteader.World;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The hoe turns ground into farmland. With a hoe (the #tool_hoe tag) in the active slot, a right click on open ground takes one swing and turns the grid
    /// square under the cursor into farmland (<see cref="FarmlandSoil"/>): tilled furrows on the terrain, and crops that need farmland can be planted in it.
    /// Water, roads, ground that already is farmland and ground with something standing on it are left alone.
    /// </summary>
    public static class Tiller
    {
        private const float ReachM = 3.5f;
        private const float SwingSeconds = 1.3f;

        public static bool HoeHeld()
        {
            string held = ConstructionSite.HeldItem();
            return !string.IsNullOrEmpty(held) && GrowthRegistry.HeldToolMatches("#tool_hoe", held);
        }

        /// <summary>The open ground under the cursor (terrain, not water, nothing in front of it), with the point.</summary>
        private static HomesteaderTerrainGenerator s_gen;
        internal static HomesteaderTerrainGenerator GeneratorShared() { return Generator(); }
        private static HomesteaderTerrainGenerator Generator() { if (s_gen == null) s_gen = Object.FindAnyObjectByType<HomesteaderTerrainGenerator>(); return s_gen; }

        public static bool GroundUnderCursor(Camera cam, Vector2 pointer, out Vector3 point)
        {
            point = default;
            if (cam == null) return false;
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, pointer);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<Terrain>() == null) return false;
                point = h.point;
                var gen = Generator();
                if (gen == null) return true;
                Vector3 o = gen.transform.position;
                return !gen.IsWaterAt(point.x - o.x, point.z - o.z);
            }
            return false;
        }

        /// <summary>The open ground under the cursor that a hoe can till (not water, a road or farmland already), with the point.</summary>
        public static bool TillableUnderCursor(Camera cam, Vector2 pointer, out Vector3 point)
        {
            point = default;
            if (cam == null) return false;
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, pointer);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<Terrain>() == null) return false;   // something else is in front of the ground
                point = h.point;
                var gen = Generator();
                if (gen == null) return false;
                Vector3 o = gen.transform.position;
                float lx = point.x - o.x, lz = point.z - o.z;
                if (gen.IsWaterAt(lx, lz) || gen.IsNearRoad(lx, lz, 0.5f)) return false;
                return !FarmlandSoil.IsFarmland(point);
            }
            return false;
        }

        /// <summary>Right click with a hoe: one swing, one square of farmland. False when the active slot is not a hoe or the ground cannot be tilled.</summary>
        public static bool TryTill(Camera cam, Vector2 pointer, Transform player)
        {
            if (!HoeHeld() || !TillableUnderCursor(cam, pointer, out Vector3 at)) return false;
            if (player != null && new Vector2(player.position.x - at.x, player.position.z - at.z).magnitude > ReachM)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to till.");
                return true;
            }
            var ped = player != null ? player.GetComponent<PedController>() : PedController.Current;
            if (ped == null) { Finish(at); return true; }
            ped.gameObject.AddComponent<TillJob>().Run(ped, at);
            return true;
        }

        private static void Finish(Vector3 at, Vector3? from = null)
        {
            FarmlandSoil.Till(at, from);
        }

        private sealed class TillJob : MonoBehaviour
        {
            public void Run(PedController ped, Vector3 at) { StartCoroutine(Go(ped, at)); }

            private IEnumerator Go(PedController ped, Vector3 at)
            {
                bool animated = ped.BeginWork("Hoe", at);
                float end = Time.time + SwingSeconds;
                bool cancelled = false;
                while (Time.time < end)
                {
                    if (ped.ManualInput) { cancelled = true; break; }
                    yield return null;
                }
                if (animated) ped.EndWork("Hoe");
                if (!cancelled) Finish(at, ped.transform.position);
                Destroy(this);
            }
        }
    }
}
