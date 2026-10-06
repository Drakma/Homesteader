using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Tidies what lies about and lays it out in neat lines:
    ///   * partly used piles of the same material (sand, gravel, dirt) are combined into the fewest piles;
    ///   * loose building materials lying on the ground are gathered; where a pack exists for them (a stack, bundle, case, pallet) they are packed into it
    ///     (10 loose bricks become a brick stack of 10); what is left over (a few bags, boards) is PILED: stacked on top of each other, as high as is neat;
    ///   * identical placed stackables (crates, boxes) are put into neat stacks.
    /// Used when a structure is finished (its yard, <see cref="Run"/>) and by the tidy tool (<see cref="RunArea"/>: a rectangle the player dragged out, plus what lies
    /// INSIDE a structure in it, tidied inside that structure on its floor).
    /// LAYOUT: every kind of thing gets its own LINE, all turned the same way, spaced by its real size (a small gap between): piles first, then packs, then single things
    /// in stacks. A line that runs out of room starts the next one. Nothing is ever thrown away: whatever does not fit is left where it was. Anything else is left alone.
    /// </summary>
    public static class YardTidy
    {
        private const float Gap = 0.2f;           // between neighbours in a line
        private const float LaneGap = 0.35f;      // between lines
        private const float FirstLane = 1.2f;     // metres from the foundation edge to the first line of a yard
        private const float EdgeMargin = 0.4f;    // kept clear of the yard's outer edge
        private const float NeatHeight = 1.3f;    // a pile of single things is stacked up to about this high
        private const int MaxPile = 8;

        /// <summary>The lines of the tidy area: a cursor that hands out the next spot of the current line.</summary>
        private sealed class Layout
        {
            private readonly Quaternion _turn;
            private readonly Vector3 _origin;
            private readonly float _zStart, _zEnd, _maxX;
            private readonly System.Func<Vector3, float> _groundY;
            private readonly System.Func<Vector3, Vector2, bool> _blocked;   // a spot (centre, size) that cannot be used: a structure stands there
            private float _laneX;          // local x of the current line's near edge
            private float _laneDepth;      // how deep (x) the current line is so far
            private float _z;              // local z cursor along the line
            private bool _started, _full;

            // origin: the centre of the frame; yawDeg its heading (lines run along local z); laneStartX where the first line stands across (local x); zStart / zEnd where
            // lines start and how far they may run along (local z); maxX how far out (local x) the last line may stand; groundY the height of the ground (the floor) at a point
            public Layout(Vector3 origin, float yawDeg, float laneStartX, float zStart, float zEnd, float maxX, System.Func<Vector3, float> groundY = null, System.Func<Vector3, Vector2, bool> blocked = null)
            {
                _turn = Quaternion.Euler(0f, yawDeg, 0f);
                _origin = origin;
                _zStart = zStart;
                _zEnd = zEnd;
                _maxX = maxX;
                _laneX = laneStartX;
                _z = zStart;
                _groundY = groundY;
                _blocked = blocked;
            }

            public bool Full => _full;
            public Quaternion Turn => _turn;
            public Vector3 Origin => _origin;

            /// <summary>Starts a new line (a new kind of thing).</summary>
            public void NewLine()
            {
                if (_started && _laneDepth > 0f) { _laneX += _laneDepth + LaneGap; _laneDepth = 0f; }
                _z = _zStart;
                _started = true;
                if (_laneX > _maxX) _full = true;
            }

            /// <summary>The centre for something of the given size (x: across the line, z: along it), moving the cursor on. A spot a structure stands on is skipped: the line goes on past it.</summary>
            public bool Next(Vector2 size, out Vector3 world)
            {
                world = default;
                if (_full) return false;
                if (!_started) NewLine();
                for (int guard = 0; guard < 400; guard++)
                {
                    if (_z + size.y > _zEnd && _z > _zStart)    // the line is full: the next line
                    {
                        _laneX += _laneDepth + LaneGap;
                        _laneDepth = 0f;
                        _z = _zStart;
                        if (_laneX > _maxX) { _full = true; return false; }
                    }
                    Vector3 local = new Vector3(_laneX + size.x * 0.5f, 0f, _z + size.y * 0.5f);
                    Vector3 at = _origin + _turn * local;
                    if (_blocked != null && _blocked(at, size)) { _z += 0.4f; continue; }   // skip around the structure: slide along the line
                    _laneDepth = Mathf.Max(_laneDepth, size.x);
                    _z += size.y + Gap;
                    at.y = _groundY != null ? _groundY(at) : Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(at);
                    world = at;
                    return true;
                }
                _full = true;
                return false;
            }
        }

        /// <summary>True when a thing of this size at this spot would touch a structure (its footprint and a little round it).</summary>
        private static bool OnStructure(Vector3 at, Vector2 size)
        {
            float reach = Mathf.Max(size.x, size.y) * 0.5f + 0.3f;
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.Stage >= 1 && s.DistanceOutside(at) < reach) return true;
            return false;
        }

        /// <summary>The size of an object across (x) and along (z) the building's axes.</summary>
        private static Vector2 LocalSize(GameObject go, Quaternion turn)
        {
            Quaternion inv = Quaternion.Inverse(turn);
            bool any = false;
            Vector3 mn = Vector3.zero, mx = Vector3.zero;
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
            {
                Bounds b = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = b.center + new Vector3((i & 1) == 0 ? -b.extents.x : b.extents.x, (i & 2) == 0 ? -b.extents.y : b.extents.y, (i & 4) == 0 ? -b.extents.z : b.extents.z);
                    Vector3 l = inv * c;
                    if (!any) { mn = mx = l; any = true; }
                    else { mn = Vector3.Min(mn, l); mx = Vector3.Max(mx, l); }
                }
            }
            return any ? new Vector2(Mathf.Max(0.2f, mx.x - mn.x), Mathf.Max(0.2f, mx.z - mn.z)) : new Vector2(0.8f, 0.8f);
        }

        /// <summary>The height of the floor (or the ground) under a point, found by a ray from just above where things stand (other things and the player do not count).</summary>
        private static float FloorY(Vector3 p, float baseY)
        {
            RaycastHit[] hits = Physics.RaycastAll(new Vector3(p.x, baseY + 0.8f, p.z), Vector3.down, 3f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null || h.collider.GetComponentInParent<PlacedObject>() != null || h.collider.GetComponentInParent<WorldItem>() != null) continue;
                return h.point.y;
            }
            return baseY;
        }

        /// <summary>
        /// Stands a column of objects (already made, bottom first) at the next spot of the line, turned the way of the layout, one on top of the other.
        /// False when the line has no room: the objects are removed again (they are new copies; what they were made from is not touched).
        /// </summary>
        private static bool Stand(Layout layout, List<PlacedObject> column, float yaw)
        {
            if (column.Count == 0) return true;
            Vector2 size = LocalSize(column[0].gameObject, Quaternion.Euler(0f, yaw, 0f));
            if (!layout.Next(size, out Vector3 at))
            {
                foreach (PlacedObject o in column) if (o != null) o.Remove();
                return false;
            }
            float y = at.y;
            for (int level = 0; level < column.Count; level++)
            {
                PlacedObject o = column[level];
                o.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                o.SetYaw(yaw);
                o.Relocate(new Vector3(at.x, y, at.z), level);
                y += o.Height;
            }
            return true;
        }

        /// <summary>Makes up to <paramref name="count"/> of an item as placed objects and piles them: columns as high as is neat, one column after another along the line. Returns how many were placed.</summary>
        private static int Pile(Layout layout, string itemId, int count, float yaw)
        {
            if (count <= 0 || !ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info) || info.Prefab == null) return 0;
            int made = 0;
            int perColumn = 0;
            while (made < count)
            {
                var column = new List<PlacedObject>();
                PlacedObject first = PlacementController.SpawnPlaced(itemId, info, layout.Origin, yaw, false);
                if (first == null) break;
                column.Add(first);
                if (perColumn == 0) perColumn = Mathf.Clamp(Mathf.FloorToInt(NeatHeight / Mathf.Max(0.05f, first.Height)), 1, MaxPile);
                while (column.Count < perColumn && made + column.Count < count)
                {
                    float y = layout.Origin.y;
                    foreach (PlacedObject o in column) y += o.Height;
                    PlacedObject next = PlacementController.SpawnPlaced(itemId, info, new Vector3(layout.Origin.x, y, layout.Origin.z), yaw, false, column.Count);
                    if (next == null) break;
                    column.Add(next);
                }
                int n = column.Count;
                if (!Stand(layout, column, yaw)) break;
                made += n;
            }
            return made;
        }

        /// <summary>The building yard of a finished structure, laid out in lines on one side of the building.</summary>
        public static void Run(ConstructionSite site)
        {
            if (site == null) return;
            Vector2 foot = ConstructionSite.FootprintOf(site.StructureId);
            float halfX = foot.x * 0.5f, halfZ = foot.y * 0.5f;
            var layout = new Layout(site.transform.position, site.YawDeg, halfX + FirstLane, -halfZ, halfZ + 1.5f, halfX + ConstructionSite.YardM - EdgeMargin, null, OnStructure);
            Tidy(layout, site.YawDeg, p => site.InYard(p));
        }

        /// <summary>
        /// A rectangle on the ground (world x, z) the player dragged out: what lies on the open ground in it is tidied into lines along its longer side, starting at the
        /// edge nearest the player; what lies INSIDE a structure in it is tidied inside that structure, on its floor.
        /// </summary>
        public static void RunArea(Rect area, Vector3 playerPos)
        {
            Rect grown = new Rect(area.xMin - 0.15f, area.yMin - 0.15f, area.width + 0.3f, area.height + 0.3f);
            // what lies INSIDE a structure the rectangle touches is tidied too, but OUTSIDE: it is carried out into the lines of the area
            var touched = new List<ConstructionSite>();
            foreach (ConstructionSite s in ConstructionSite.All)
                if (s != null && s.Stage >= 1 && FootprintTouches(s, ConstructionSite.FootprintOf(s.StructureId), grown)) touched.Add(s);
            // the lines run along the rectangle's longer side
            Vector3 centre = new Vector3(area.center.x, 0f, area.center.y);
            centre.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(centre);
            bool longZ = area.height >= area.width;
            float across = longZ ? area.width : area.height, along = longZ ? area.height : area.width;
            float yaw = longZ ? 0f : 90f;
            Vector3 local = Quaternion.Euler(0f, -yaw, 0f) * (playerPos - centre);
            if (local.x > 0f) yaw += 180f;
            var outer = new Layout(centre, yaw, -across * 0.5f + 0.25f, -along * 0.5f, along * 0.5f + 0.3f, across * 0.5f + 0.4f, null, OnStructure);   // the lines skip around structures
            Tidy(outer, yaw, p =>
            {
                foreach (ConstructionSite s in touched) if (s.DistanceOutside(p) <= 0.05f) return true;   // inside a structure the rectangle touches: carried out
                if (!grown.Contains(new Vector2(p.x, p.z))) return false;
                foreach (ConstructionSite s in ConstructionSite.All) if (s != null && s.Stage >= 1 && s.DistanceOutside(p) <= 0.05f) return false;   // inside some other structure: left alone
                return true;
            });
        }

        /// <summary>True when the rectangle (world x, z) overlaps the structure's footprint (turned as it stands).</summary>
        private static bool FootprintTouches(ConstructionSite site, Vector2 foot, Rect rect)
        {
            Quaternion turn = Quaternion.Euler(0f, site.YawDeg, 0f);
            float hx = foot.x * 0.5f, hz = foot.y * 0.5f;
            float minX = float.MaxValue, maxX = float.MinValue, minZ = float.MaxValue, maxZ = float.MinValue;
            foreach (Vector2 c in new[] { new Vector2(-hx, -hz), new Vector2(hx, -hz), new Vector2(hx, hz), new Vector2(-hx, hz) })
            {
                Vector3 w = site.transform.position + turn * new Vector3(c.x, 0f, c.y);
                minX = Mathf.Min(minX, w.x); maxX = Mathf.Max(maxX, w.x); minZ = Mathf.Min(minZ, w.z); maxZ = Mathf.Max(maxZ, w.z);
            }
            return rect.Overlaps(new Rect(minX, minZ, maxX - minX, maxZ - minZ));
        }

        /// <summary>The floor height of what lies in a place: the middle of the heights of the objects there (NaN when nothing lies there).</summary>
        private static float BaseHeight(System.Func<Vector3, bool> inArea)
        {
            var ys = new List<float>();
            foreach (PlacedObject o in PlacedObject.All) if (o != null && o.Level == 0 && inArea(o.transform.position)) ys.Add(o.transform.position.y);
            foreach (WorldItem w in WorldItem.All) if (w != null && inArea(w.transform.position)) ys.Add(w.transform.position.y);
            if (ys.Count == 0) return float.NaN;
            ys.Sort();
            return ys[ys.Count / 2];
        }

        private static void Tidy(Layout layout, float yaw, System.Func<Vector3, bool> inArea)
        {
            var placed = new List<PlacedObject>();
            foreach (PlacedObject o in PlacedObject.All) if (o != null && inArea(o.transform.position) && o.Level == 0 && o != WheelbarrowPush.Active?.Placed && !WaterTap.IsFixed(o.ItemId)) placed.Add(o);   // (a spigot post or a macerator is plumbed in: it stays)
            var carried = new HashSet<PlacedObject>();
            foreach (PlacedObject o in placed) if (PalletDeck.IsPallet(o.ItemId)) foreach (PlacedObject c in PalletDeck.Carried(o)) carried.Add(c);   // what a pallet carries goes with it
            placed.RemoveAll(o => carried.Contains(o));
            var loose = new List<WorldItem>();
            foreach (WorldItem w in WorldItem.All) if (w != null && inArea(w.transform.position)) loose.Add(w);

            // 1. partly used piles of one material: combined, one line per material. The new piles are made FIRST; the old ones go only when all of it found a place.
            var pilesByScoop = new Dictionary<string, List<PlacedObject>>();
            foreach (PlacedObject o in placed)
                if (GrowthRegistry.BulkOf(o.ItemId, out string scoop, out _)) { if (!pilesByScoop.TryGetValue(scoop, out List<PlacedObject> l)) pilesByScoop[scoop] = l = new List<PlacedObject>(); l.Add(o); }
            foreach (var kv in pilesByScoop)
            {
                if (kv.Value.Count < 2 || layout.Full) continue;
                int total = 0;
                foreach (PlacedObject p in kv.Value)
                {
                    GrowthRegistry.BulkOf(p.ItemId, out _, out int full);
                    int left = 0;
                    if (p.Contents != null) foreach (ContainerStack c in p.Contents) left += c.Count;
                    total += left > 0 ? left : full;
                }
                layout.NewLine();
                var made = new List<PlacedObject>();
                bool all = true;
                foreach (KeyValuePair<string, int> plan in WheelbarrowPush.PlanPiles(kv.Key, total))
                {
                    PlacedObject pile = WheelbarrowPush.SpawnPileAt(plan.Key, kv.Key, plan.Value, layout.Origin, yaw);
                    if (pile == null) { all = false; break; }
                    if (!Stand(layout, new List<PlacedObject> { pile }, yaw)) { all = false; break; }
                    made.Add(pile);
                }
                if (all) foreach (PlacedObject p in kv.Value) { if (p != null) p.Remove(); }
                else foreach (PlacedObject p in made) { if (p != null) p.Remove(); }   // no room for all of it: the old piles stay as they were
            }

            // 2. loose building materials: packed where a pack exists (a line of packs), what is left over piled up. Only what is really placed is taken away.
            var gone = new HashSet<WorldItem>();
            var byItem = new SortedDictionary<string, List<WorldItem>>();
            foreach (WorldItem w in loose)
            {
                AssetCatalogItem info = HudBindings.GetCatalogItem(w.ItemId);
                if (info == null || (info.category != "building" && info.category != "materials")) continue;
                if (!byItem.TryGetValue(w.ItemId, out List<WorldItem> l)) byItem[w.ItemId] = l = new List<WorldItem>();
                l.Add(w);
            }
            foreach (var kv in byItem)
            {
                int n = kv.Value.Count;
                if (n < 2 && GrowthRegistry.PacksOf(kv.Key).Count == 0) continue;   // a lone item with no pack stays put
                if (!ItemRegistry.TryGet(kv.Key, out ItemRegistry.ItemInfo single) || single.Prefab == null) continue;   // nothing to pile (no model)
                if (layout.Full) break;
                layout.NewLine();
                int remaining = n;
                foreach (var pack in GrowthRegistry.PacksOf(kv.Key))
                {
                    if (!ItemRegistry.TryGet(pack.Key, out ItemRegistry.ItemInfo pinfo) || pinfo.Prefab == null) continue;
                    while (remaining >= pack.Value && !layout.Full)
                    {
                        PlacedObject made = PlacementController.SpawnPlaced(pack.Key, pinfo, layout.Origin, yaw, false);
                        if (made == null) break;
                        if (ContainerRules.StackingLimit(pack.Key) > 1) placed.Add(made);   // a pack that stacks is set into its stack in step 3
                        else if (!Stand(layout, new List<PlacedObject> { made }, yaw)) { made.Remove(); break; }
                        remaining -= pack.Value;
                    }
                }
                int piled = Pile(layout, kv.Key, remaining, yaw);
                int consumed = (n - remaining) + piled;
                for (int i = 0; i < consumed && i < kv.Value.Count; i++) if (kv.Value[i] != null) { gone.Add(kv.Value[i]); Object.Destroy(kv.Value[i].gameObject); }   // only what was placed elsewhere
            }

            // 2a. PLACED lumber, bricks and the like (every piece, whatever level it stands at): made up into the biggest packs it makes, then the next size, as the sawmill does; what is
            // left over stays loose and is stacked in step 3. Only a pack that found its place takes pieces away.
            var packable = new SortedDictionary<string, List<PlacedObject>>();
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !inArea(o.transform.position) || carried.Contains(o) || o == WheelbarrowPush.Active?.Placed || WaterTap.IsFixed(o.ItemId)) continue;
                if (GrowthRegistry.BulkOf(o.ItemId, out _, out _) || GrowthRegistry.PacksOf(o.ItemId).Count == 0) continue;
                if (!packable.TryGetValue(o.ItemId, out List<PlacedObject> pl)) packable[o.ItemId] = pl = new List<PlacedObject>();
                pl.Add(o);
            }
            foreach (var kv in packable)
            {
                int total = kv.Value.Count, used = 0;
                bool started = false;
                foreach (var pack in GrowthRegistry.PacksOf(kv.Key))
                {
                    if (!ItemRegistry.TryGet(pack.Key, out ItemRegistry.ItemInfo pinfo) || pinfo.Prefab == null) continue;
                    while (total - used >= pack.Value && !layout.Full)
                    {
                        if (!started) { layout.NewLine(); started = true; }
                        PlacedObject made = PlacementController.SpawnPlaced(pack.Key, pinfo, layout.Origin, yaw, false);
                        if (made == null) break;
                        if (ContainerRules.StackingLimit(pack.Key) > 1) placed.Add(made);   // a pack that stacks is set into its stack in step 3
                        else if (!Stand(layout, new List<PlacedObject> { made }, yaw)) { made.Remove(); break; }
                        used += pack.Value;
                    }
                }
                if (used <= 0) continue;
                kv.Value.Sort((a, b) => b.Level.CompareTo(a.Level));   // the top of each stack goes first
                for (int i = 0; i < used && i < kv.Value.Count; i++)
                {
                    placed.Remove(kv.Value[i]);
                    kv.Value[i].Remove();
                }
            }

            // 2b. every other loose item (what is left over, other kinds of thing): lined up, one line per kind, each turned the same way
            var looseByItem = new SortedDictionary<string, List<WorldItem>>();
            foreach (WorldItem w in loose)
            {
                if (w == null || gone.Contains(w)) continue;
                if (!looseByItem.TryGetValue(w.ItemId, out List<WorldItem> l)) looseByItem[w.ItemId] = l = new List<WorldItem>();
                l.Add(w);
            }
            foreach (var kv in looseByItem)
            {
                if (layout.Full) break;
                layout.NewLine();
                foreach (WorldItem w in kv.Value)
                {
                    if (w == null) continue;
                    Vector2 size = LocalSize(w.gameObject, Quaternion.Euler(0f, yaw, 0f));
                    if (!layout.Next(size, out Vector3 at)) break;
                    w.transform.position = at;
                    w.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                }
            }

            // 3. identical placed stackables: neat stacks, one line per kind (they are moved, never removed)
            var byStack = new SortedDictionary<string, List<PlacedObject>>();
            foreach (PlacedObject o in placed)
            {
                if (o == null || GrowthRegistry.BulkOf(o.ItemId, out _, out _)) continue;
                if (ContainerRules.StackingLimit(o.ItemId) <= 1) continue;
                if (!byStack.TryGetValue(o.ItemId, out List<PlacedObject> l)) byStack[o.ItemId] = l = new List<PlacedObject>();
                l.Add(o);
            }
            foreach (var kv in byStack)
            {
                int limit = ContainerRules.StackingLimit(kv.Key);
                layout.NewLine();
                int i = 0;
                while (i < kv.Value.Count)
                {
                    var column = new List<PlacedObject>();
                    while (column.Count < limit && i < kv.Value.Count) { if (kv.Value[i] != null) column.Add(kv.Value[i]); i++; }
                    if (column.Count == 0) continue;
                    Vector2 size = LocalSize(column[0].gameObject, Quaternion.Euler(0f, yaw, 0f));
                    if (!layout.Next(size, out Vector3 at)) break;
                    float y = at.y;
                    for (int level = 0; level < column.Count; level++)
                    {
                        PlacedObject o = column[level];
                        o.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                        o.SetYaw(yaw);
                        o.Relocate(new Vector3(at.x, y, at.z), level);
                        y += o.Height;
                    }
                }
            }

            // 3b. everything else that stands on its own (pallets, packs, single things): one line per kind, each turned the same way; a pallet takes what it carries along
            var rest = new SortedDictionary<string, List<PlacedObject>>();
            foreach (PlacedObject o in placed)
            {
                if (o == null || GrowthRegistry.BulkOf(o.ItemId, out _, out _) || ContainerRules.StackingLimit(o.ItemId) > 1) continue;
                if (!rest.TryGetValue(o.ItemId, out List<PlacedObject> l)) rest[o.ItemId] = l = new List<PlacedObject>();
                l.Add(o);
            }
            foreach (var kv in rest)
            {
                if (layout.Full) break;
                layout.NewLine();
                foreach (PlacedObject o in kv.Value)
                {
                    if (o == null) continue;
                    Vector2 size = LocalSize(o.gameObject, Quaternion.Euler(0f, yaw, 0f));
                    if (!layout.Next(size, out Vector3 at)) break;
                    MoveWithLoad(o, at, yaw);
                }
            }
        }

        /// <summary>Moves a placed object to a spot, turned to a heading; what a pallet carries moves and turns with it.</summary>
        private static void MoveWithLoad(PlacedObject o, Vector3 at, float yaw)
        {
            List<PlacedObject> load = PalletDeck.IsPallet(o.ItemId) ? PalletDeck.Carried(o) : null;
            Quaternion oldRot = o.transform.rotation;
            var local = new List<Vector3>();
            var rot = new List<Quaternion>();
            if (load != null)
                foreach (PlacedObject c in load) { local.Add(o.transform.InverseTransformPoint(c.transform.position)); rot.Add(Quaternion.Inverse(oldRot) * c.transform.rotation); }
            o.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            o.SetYaw(yaw);
            o.Relocate(at, o.Level);
            if (load == null) return;
            for (int i = 0; i < load.Count; i++)
            {
                if (load[i] == null) continue;
                load[i].transform.rotation = o.transform.rotation * rot[i];
                load[i].SetYaw(load[i].transform.eulerAngles.y);
                load[i].Relocate(o.transform.TransformPoint(local[i]), load[i].Level);
            }
        }
    }
}
