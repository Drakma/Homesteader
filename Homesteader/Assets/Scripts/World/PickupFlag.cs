using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// The pickup-zone flag (building_pickup_flag). The player plants it, and it marks one corner of the market pickup zone: a <see cref="Tiles"/> by <see cref="Tiles"/> tile
    /// square that reaches from the flag toward the road (the road point nearest the flag). The zone is that square, not a radius: what lies in it is what the Market app sells
    /// and where deliveries are dropped (DeliveryService.ResolveZone, MarketPickup.InZone). With no flag the old zone (beside the first house) is used. The first flag placed rules.
    /// The square is drawn on the ground while the pointer is on the flag, so the player sees exactly where it is. docs/MARKET.md.
    /// </summary>
    public sealed class PickupFlag : MonoBehaviour
    {
        public const string ItemId = "building_pickup_flag";
        public const int Tiles = 10;

        private static readonly List<PickupFlag> All = new List<PickupFlag>();
        private PlacedObject _placed;
        private LineRenderer _line;
        private Material _mat;
        private Rect _drawn;
        private float _nextLook;
        private bool _hovered;

        public static bool IsFlag(string itemId) { return itemId == ItemId; }

        public static PickupFlag AttachIfFlag(PlacedObject placed)
        {
            if (placed == null || !IsFlag(placed.ItemId)) return null;
            var f = placed.gameObject.AddComponent<PickupFlag>();
            f._placed = placed;
            All.Add(f);
            return f;
        }

        private void OnDestroy()
        {
            All.Remove(this);
            if (_mat != null) Destroy(_mat);
        }

        // ------------------------------------------------------------------ the zone

        private static int _cachedFrame = -1;
        private static bool _cachedHas;
        private static Rect _cachedRect;
        private static int _cachedStop;

        /// <summary>The pickup square (x, z in world metres) and the road point nearest it. False when no flag is planted (or there is no road yet).</summary>
        public static bool TryZone(out Rect rect, out int stopIndex)
        {
            if (_cachedFrame != Time.frameCount)
            {
                _cachedFrame = Time.frameCount;
                _cachedHas = Compute(out _cachedRect, out _cachedStop);
            }
            rect = _cachedRect;
            stopIndex = _cachedStop;
            return _cachedHas;
        }

        private static bool Compute(out Rect rect, out int stopIndex)
        {
            rect = default;
            stopIndex = 0;
            PickupFlag flag = null;
            foreach (PickupFlag f in All) if (f != null && f._placed != null) { flag = f; break; }   // the first flag placed
            if (flag == null) return false;
            HomesteaderTerrainGenerator gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
            IReadOnlyList<Vector2> road = gen != null ? gen.RoadPoints : null;
            if (road == null || road.Count < 8) return false;
            Vector3 p = flag.transform.position;
            Vector2 at = new Vector2(p.x, p.z);
            float best = float.MaxValue;
            for (int i = 0; i < road.Count; i++)
            {
                float d = (road[i] - at).sqrMagnitude;
                if (d < best) { best = d; stopIndex = i; }
            }
            stopIndex = Mathf.Max(2, stopIndex);
            Vector2 to = road[stopIndex] - at;
            float g = PlantingValidator.GridSizeM, len = Tiles * g;
            // the flag stands on its own tile, the corner of the square: it reaches toward the road along each axis
            float x0 = to.x >= 0f ? p.x - g * 0.5f : p.x + g * 0.5f - len;
            float z0 = to.y >= 0f ? p.z - g * 0.5f : p.z + g * 0.5f - len;
            rect = new Rect(x0, z0, len, len);
            return true;
        }

        /// <summary>The middle of the square, on the ground.</summary>
        public static Vector3 CentreOf(Rect r)
        {
            Vector3 c = new Vector3(r.center.x, 0f, r.center.y);
            c.y = TerrainHeightDetector.GetSurfaceY(c.x, c.z);
            return c;
        }

        // ------------------------------------------------------------------ the square on the ground

        private void Update()
        {
            if (Time.unscaledTime >= _nextLook)   // looked at a few times a second, not every frame
            {
                _nextLook = Time.unscaledTime + 0.1f;
                Transform hit = Homesteader.UI.HoverTarget.Find();
                _hovered = hit != null && hit.GetComponentInParent<PickupFlag>() == this;
            }
            if (!_hovered || !TryZone(out Rect r, out _) || All.Count == 0 || All[0] != this)
            {
                if (_line != null) _line.enabled = false;   // the square shows while the pointer is on the ruling flag
                return;
            }
            if (_line == null)
            {
                var go = new GameObject("PickupZoneOutline");
                go.transform.SetParent(transform, false);
                _line = go.AddComponent<LineRenderer>();
                _line.useWorldSpace = true;
                _line.loop = true;
                _line.widthMultiplier = 0.1f;
                _mat = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { color = new Color(1f, 0.45f, 0.08f, 1f) };
                _line.sharedMaterial = _mat;
                _drawn = default;
            }
            _line.enabled = true;
            if (_drawn == r) return;
            _drawn = r;
            var pts = new List<Vector3>();
            int n = Tiles;
            for (int i = 0; i < n; i++) pts.Add(Ground(r.xMin + r.width * i / n, r.yMin));
            for (int i = 0; i < n; i++) pts.Add(Ground(r.xMax, r.yMin + r.height * i / n));
            for (int i = 0; i < n; i++) pts.Add(Ground(r.xMax - r.width * i / n, r.yMax));
            for (int i = 0; i < n; i++) pts.Add(Ground(r.xMin, r.yMax - r.height * i / n));
            _line.positionCount = pts.Count;
            _line.SetPositions(pts.ToArray());
        }

        private static Vector3 Ground(float x, float z)
        {
            return new Vector3(x, TerrainHeightDetector.GetSurfaceY(x, z) + 0.12f, z);
        }
    }
}
