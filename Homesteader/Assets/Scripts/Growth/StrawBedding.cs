using System.Collections;
using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Straw bedding on the floor of a room. With a straw bale in the active slot a right click on the floor of a building spreads bedding over
    /// THAT ROOM: the stretch of floor round the click that the walls, the partitions and the door headers close off (a closed door closes it too).
    /// One bale covers <see cref="M2PerBale"/> square metres; a bigger room takes more bales from the slot. A right click on the bedding with a
    /// shovel in the active slot takes it up again (mucking out; nothing is given back).
    ///
    /// The bedding is a PLACED OBJECT of the item <see cref="BeddingItem"/> standing in a corner of the room, so it is saved and restored with
    /// every other placed object (item, position, heading: nothing new in the save). Its model is hidden; this component finds the room again from
    /// where it stands and lays the straw as one mesh. The mesh is not a child of the placed object (the packing of placed things goes by an
    /// object's own bounds) and has no collider: it is walked over, and things are placed on the floor through it.
    /// </summary>
    public sealed class StrawBedding : MonoBehaviour
    {
        public const string BeddingItem = "mat_bedding_straw";
        public const float M2PerBale = 12f;

        private const float Cell = 0.25f;          // the grid the room is found on
        private const float Thick = 0.05f;         // how deep the straw lies
        private const int MaxCells = 6400;         // 400 square metres: anything bigger is not a room
        private const float ReachM = 6f;
        private static readonly float[] WallHeights = { 0.3f, 1.0f, 2.2f, 2.34f };   // knee walls, walls, the header over an inside door and over an outside one

        private static readonly List<StrawBedding> s_all = new List<StrawBedding>();
        private static Region s_pending;           // the room just found by the click, handed to the component being made (so it is not searched twice)
        private static Material s_material;

        private sealed class Region
        {
            public ConstructionSite Site;
            public Vector3 Origin, Ax, Az;         // the centre of cell (0, 0) and the two directions of the grid (the building's own)
            public float FloorY;
            public HashSet<long> Cells = new HashSet<long>();
            public float Area => Cells.Count * Cell * Cell;
            public Vector3 Centre(int i, int j) { Vector3 p = Origin + Ax * (i * Cell) + Az * (j * Cell); p.y = FloorY; return p; }
            public bool Contains(Vector3 world)
            {
                if (Mathf.Abs(world.y - FloorY) > 0.35f) return false;
                Vector3 d = world - Origin;
                return Cells.Contains(Key(Mathf.RoundToInt(Vector3.Dot(d, Ax) / Cell), Mathf.RoundToInt(Vector3.Dot(d, Az) / Cell)));
            }
        }

        private static long Key(int i, int j) { return ((long)(i + 100000) << 32) | (uint)(j + 100000); }

        private PlacedObject _placed;
        private Region _region;
        private GameObject _mesh;

        public static bool IsBale(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("mat_bale_straw"); }

        /// <summary>Called for every placed object as it is made (a fresh spread, or a save being restored).</summary>
        public static void AttachIfBedding(PlacedObject placed)
        {
            if (placed != null && placed.ItemId == BeddingItem && placed.GetComponent<StrawBedding>() == null) placed.gameObject.AddComponent<StrawBedding>();
        }

        private void Awake()
        {
            _placed = GetComponent<PlacedObject>();
            foreach (Transform child in transform) child.gameObject.SetActive(false);   // the item's own model (a heap of straw) is only its icon
            s_all.Add(this);
            if (s_pending != null) { _region = s_pending; s_pending = null; BuildMesh(); }
            else StartCoroutine(FindRoomLater());
        }

        /// <summary>A restored save puts the placed objects back before the buildings: wait for the floor to be there.</summary>
        private IEnumerator FindRoomLater()
        {
            for (int tries = 0; tries < 240 && _region == null; tries++)
            {
                if (FindFloor(transform.position, out RaycastHit hit, out ConstructionSite site)) _region = Flood(hit.point, site);
                if (_region == null) yield return new WaitForSeconds(0.5f);
            }
            if (_region != null) BuildMesh();
        }

        private void OnDestroy()
        {
            s_all.Remove(this);
            if (_mesh != null) Destroy(_mesh);
        }

        // ------------------------------------------------------------------ the clicks

        /// <summary>A right click with a straw bale in the active slot. False when the first thing under the cursor is not the floor of a building.</summary>
        public static bool TrySpreadAtRay(Ray ray, string heldId, Transform player)
        {
            if (!IsBale(heldId)) return false;
            if (!FloorUnderRay(ray, out RaycastHit hit, out ConstructionSite site)) return false;
            if (player != null && Vector3.Distance(player.position, hit.point) > ReachM)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to spread the straw.");
                return true;
            }
            if (BeddingAt(hit.point) != null)
            {
                ToastNotificationSystem.ShowInfo("Straw bedding", "This room already has bedding.");
                return true;
            }
            Region region = Flood(hit.point, site);
            if (region == null)
            {
                ToastNotificationSystem.ShowInfo("Straw bedding", "That is not a room: the floor here is not closed off by walls.");
                return true;
            }
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return true;
            int bales = Mathf.Max(1, Mathf.CeilToInt(region.Area / M2PerBale - 0.01f));
            int held = hud.Toolbar[hud.SelectedSlot].Count;
            if (held < bales)
            {
                ToastNotificationSystem.ShowInfo("Straw bedding", "This room (" + UnitFormat.Area(region.Area) + ") takes " + bales + " bales; you are holding " + held + ".");
                return true;
            }
            if (!ItemRegistry.TryGet(BeddingItem, out ItemRegistry.ItemInfo info) || info.Prefab == null)
            {
                ToastNotificationSystem.ShowInfo("Straw bedding", "The straw bedding item is not loaded.");
                return true;
            }
            if (!hud.ConsumeFromSelectedSlot(bales)) return true;
            HudBindings.Instance?.RefreshToolbar();

            // it stands in a corner of the room, out of the way (any spot of the room finds the same room again when a save is restored)
            long corner = 0; int best = int.MaxValue;
            foreach (long k in region.Cells)
            {
                int i = (int)(k >> 32) - 100000, j = (int)(uint)k - 100000;
                if (i + j < best) { best = i + j; corner = k; }
            }
            Vector3 anchor = region.Centre((int)(corner >> 32) - 100000, (int)(uint)corner - 100000);
            s_pending = region;
            PlacedObject placed = PlacementController.SpawnPlaced(BeddingItem, info, anchor, site.YawDeg, false);
            s_pending = null;
            if (placed == null) return true;
            ToastNotificationSystem.ShowSuccess("Straw bedding", "Spread " + bales + (bales == 1 ? " bale" : " bales") + " over " + UnitFormat.Area(region.Area) + ".");
            return true;
        }

        /// <summary>A right click with a shovel in the active slot on bedding takes it up. False when there is no bedding under the cursor.</summary>
        public static bool TryMuckOutAtRay(Ray ray, string heldId, Transform player)
        {
            if (s_all.Count == 0 || string.IsNullOrEmpty(heldId) || !GrowthRegistry.HeldToolMatches("#tool_shovel", heldId)) return false;
            if (!FloorUnderRay(ray, out RaycastHit hit, out _)) return false;
            StrawBedding bed = BeddingAt(hit.point);
            if (bed == null) return false;
            if (player != null && Vector3.Distance(player.position, hit.point) > ReachM)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to muck it out.");
                return true;
            }
            Destroy(bed.gameObject);
            ToastNotificationSystem.ShowInfo("Straw bedding", "Mucked out the room.");
            return true;
        }

        private static StrawBedding BeddingAt(Vector3 world)
        {
            foreach (StrawBedding b in s_all) if (b != null && b._region != null && b._region.Contains(world)) return b;
            return null;
        }

        // ------------------------------------------------------------------ finding the room

        private static bool Skip(Collider c)
        {
            return c == null || c.GetComponentInParent<PedController>() != null || c.GetComponentInParent<PlacedObject>() != null
                || c.GetComponentInParent<WorldItem>() != null || c.GetComponentInParent<AttachedObject>() != null;
        }

        /// <summary>The floor of a building under the cursor: the first thing the ray meets, when that is a level face of a building.</summary>
        private static bool FloorUnderRay(Ray ray, out RaycastHit floor, out ConstructionSite site)
        {
            floor = default; site = null;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (Skip(h.collider)) continue;
                site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null || h.normal.y < 0.7f) return false;
                floor = h;
                return true;
            }
            return false;
        }

        /// <summary>The floor of a building straight under a point (from a little above it).</summary>
        private static bool FindFloor(Vector3 at, out RaycastHit floor, out ConstructionSite site)
        {
            floor = default; site = null;
            RaycastHit[] hits = Physics.RaycastAll(at + Vector3.up * 0.6f, Vector3.down, 1.3f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (Skip(h.collider) || h.normal.y < 0.7f) continue;
                site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null) return false;
                floor = h;
                return true;
            }
            return false;
        }

        /// <summary>True when something of the building stands between two neighbouring cells (a wall, a partition, a closed door, a door header).</summary>
        private static bool Blocked(Region r, Vector3 a, Vector3 b)
        {
            Vector3 d = b - a;
            float len = d.magnitude;
            d /= len;
            foreach (float h in WallHeights)
            {
                foreach (RaycastHit hit in Physics.RaycastAll(a + Vector3.up * h, d, len, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                    if (!Skip(hit.collider) && hit.collider.GetComponentInParent<ConstructionSite>() == r.Site) return true;
                foreach (RaycastHit hit in Physics.RaycastAll(b + Vector3.up * h, -d, len, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))   // a one-sided face seen from the other side
                    if (!Skip(hit.collider) && hit.collider.GetComponentInParent<ConstructionSite>() == r.Site) return true;
            }
            return false;
        }

        /// <summary>The room round a point of floor: the connected cells of floor at that height that nothing of the building divides. Null when it is not closed off.</summary>
        private static Region Flood(Vector3 start, ConstructionSite site)
        {
            if (site == null) return null;
            var r = new Region { Site = site, FloorY = start.y };
            r.Ax = site.transform.right; r.Ax.y = 0f; r.Ax.Normalize();
            r.Az = site.transform.forward; r.Az.y = 0f; r.Az.Normalize();
            r.Origin = new Vector3(start.x, start.y, start.z);

            var floorKnown = new Dictionary<long, bool>();
            bool IsFloor(int i, int j)
            {
                long k = Key(i, j);
                if (floorKnown.TryGetValue(k, out bool v)) return v;
                v = FindFloor(r.Centre(i, j), out RaycastHit h, out ConstructionSite s) && s == site && Mathf.Abs(h.point.y - r.FloorY) < 0.15f;
                floorKnown[k] = v;
                return v;
            }
            if (!IsFloor(0, 0)) return null;

            var queue = new Queue<Vector2Int>();
            queue.Enqueue(Vector2Int.zero);
            r.Cells.Add(Key(0, 0));
            var steps = new[] { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) };
            while (queue.Count > 0)
            {
                Vector2Int c = queue.Dequeue();
                foreach (Vector2Int s in steps)
                {
                    int ni = c.x + s.x, nj = c.y + s.y;
                    long k = Key(ni, nj);
                    if (r.Cells.Contains(k) || !IsFloor(ni, nj)) continue;
                    if (Blocked(r, r.Centre(c.x, c.y), r.Centre(ni, nj))) continue;
                    r.Cells.Add(k);
                    if (r.Cells.Count > MaxCells) return null;      // it ran out through an opening: not a room
                    queue.Enqueue(new Vector2Int(ni, nj));
                }
            }
            return r.Cells.Count >= 4 ? r : null;
        }

        // ------------------------------------------------------------------ the straw

        private void BuildMesh()
        {
            if (_region == null || _mesh != null) return;
            Region r = _region;
            var verts = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();
            float half = Cell * 0.5f, top = r.FloorY + Thick, bottom = r.FloorY + 0.002f;

            void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d)
            {
                int n = verts.Count;
                verts.Add(a); verts.Add(b); verts.Add(c); verts.Add(d);
                foreach (Vector3 p in new[] { a, b, c, d }) uvs.Add(new Vector2((p.x + p.y) * 0.6f, (p.z + p.y) * 0.6f));
                tris.Add(n); tris.Add(n + 1); tris.Add(n + 2); tris.Add(n); tris.Add(n + 2); tris.Add(n + 3);
            }

            foreach (long k in r.Cells)
            {
                int i = (int)(k >> 32) - 100000, j = (int)(uint)k - 100000;
                Vector3 c = r.Centre(i, j);
                Vector3 x = r.Ax * half, z = r.Az * half;
                // the straw is not dead level: each corner of a cell lies a little higher or lower, the same at every cell that shares it
                float H(int ci, int cj) { return top + (Mathf.PerlinNoise((i + ci) * 0.37f + 11.3f, (j + cj) * 0.37f + 4.7f) - 0.5f) * 0.03f; }
                Vector3 p00 = c - x - z, p10 = c + x - z, p11 = c + x + z, p01 = c - x + z;
                p00.y = H(0, 0); p10.y = H(1, 0); p11.y = H(1, 1); p01.y = H(0, 1);
                Quad(p00, p01, p11, p10);
                // a skirt down to the floor along the edges of the room that have no neighbour (a doorway, the rim of the room)
                if (!r.Cells.Contains(Key(i - 1, j))) Quad(new Vector3(p00.x, bottom, p00.z), new Vector3(p01.x, bottom, p01.z), p01, p00);
                if (!r.Cells.Contains(Key(i + 1, j))) Quad(new Vector3(p11.x, bottom, p11.z), new Vector3(p10.x, bottom, p10.z), p10, p11);
                if (!r.Cells.Contains(Key(i, j - 1))) Quad(new Vector3(p10.x, bottom, p10.z), new Vector3(p00.x, bottom, p00.z), p00, p10);
                if (!r.Cells.Contains(Key(i, j + 1))) Quad(new Vector3(p01.x, bottom, p01.z), new Vector3(p11.x, bottom, p11.z), p11, p01);
            }

            var mesh = new Mesh { name = "StrawBedding" };
            if (verts.Count > 65000) mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            mesh.SetVertices(verts);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            _mesh = new GameObject("StrawBedding");
            _mesh.transform.SetParent(transform.parent, false);
            _mesh.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = _mesh.AddComponent<MeshRenderer>();
            mr.sharedMaterial = StrawMaterial();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }

        private static Material StrawMaterial()
        {
            if (s_material != null) return s_material;
            const int n = 128;
            var px = new Color[n * n];
            var rnd = new System.Random(4711);
            Color baseC = new Color(0.80f, 0.66f, 0.32f);
            for (int i = 0; i < px.Length; i++) px[i] = baseC * (0.86f + (float)rnd.NextDouble() * 0.2f);
            // stalks: short strokes lying every which way, some lighter and some in shadow
            for (int s = 0; s < 900; s++)
            {
                float x = (float)rnd.NextDouble() * n, y = (float)rnd.NextDouble() * n;
                float a = (float)rnd.NextDouble() * Mathf.PI;
                float dx = Mathf.Cos(a), dy = Mathf.Sin(a);
                int len = 6 + rnd.Next(14);
                float tone = rnd.NextDouble() < 0.35 ? 0.62f : 1.0f + (float)rnd.NextDouble() * 0.25f;
                Color c = new Color(0.86f, 0.74f, 0.4f) * tone;
                for (int t = 0; t < len; t++)
                {
                    int ix = ((int)(x + dx * t) % n + n) % n, iy = ((int)(y + dy * t) % n + n) % n;
                    px[iy * n + ix] = c;
                }
            }
            for (int i = 0; i < px.Length; i++) px[i].a = 1f;
            var tex = new Texture2D(n, n, TextureFormat.RGB24, true) { name = "StrawBedding", wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.DontSave };
            tex.SetPixels(px);
            tex.Apply(true);
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");
            s_material = new Material(lit) { name = "StrawBedding", hideFlags = HideFlags.DontSave };
            s_material.SetColor("_BaseColor", Color.white);
            s_material.SetTexture("_BaseMap", tex);
            s_material.SetFloat("_Smoothness", 0.05f);
            s_material.SetFloat("_Cull", 0f);          // both faces: the skirts are seen from either side
            return s_material;
        }
    }
}
