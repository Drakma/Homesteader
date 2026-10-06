using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The rooms of a finished building, worked out from its own walls: the space inside the walls is cut into small cells, a cell is closed where a
    /// wall of the model stands just under the ceiling (there a partition is whole: its doorways have a header over them, and a half-height stall
    /// wall does not reach), and the open cells that touch each other are one room. Nothing is authored per building and nothing is saved: the map is
    /// made once for the model that stands and made again when the model changes. Used by the lights (<see cref="LightEmitter"/>: a room's lights
    /// are on only while the player is in that room).
    /// </summary>
    public sealed class RoomMap
    {
        private const float Cell = 0.2f;

        private static readonly Dictionary<ConstructionSite, RoomMap> s_maps = new Dictionary<ConstructionSite, RoomMap>();
        private static readonly Collider[] s_hits = new Collider[24];

        private Transform _for;          // the model the map was made from
        private Rect _rect;              // the walls' rectangle, in the building's own space
        private int _nx, _nz;
        private int[] _room;             // per cell: the room's number, or -1 where a wall stands
        private int _rooms;
        private int _playerRoom = -1;    // the room the player was last in (kept while they stand in a doorway)
        private float _nextTry;

        /// <summary>How many rooms the building has (0 while its model is still loading).</summary>
        public static int Count(ConstructionSite site) { RoomMap m = For(site); return m != null ? m._rooms : 0; }

        /// <summary>The room a world point is in, or -1 (outside the walls, in a wall with no room beside it, or the building has no map yet).</summary>
        public static int RoomAt(ConstructionSite site, Vector3 world)
        {
            RoomMap m = For(site);
            return m != null ? m.Find(site, world) : -1;
        }

        /// <summary>The room the player is in: as <see cref="RoomAt"/>, but standing in a doorway (under its header) they are still in the room they came from.</summary>
        public static int PlayerRoom(ConstructionSite site, Vector3 player)
        {
            RoomMap m = For(site);
            if (m == null) return -1;
            if (!site.IsInsideWalls(player)) { m._playerRoom = -1; return -1; }
            int cell = m.CellAt(site, player);
            if (cell >= 0 && m._room[cell] >= 0) m._playerRoom = m._room[cell];
            else if (m._playerRoom < 0) m._playerRoom = m.Find(site, player);
            return m._playerRoom;
        }

        private static RoomMap For(ConstructionSite site)
        {
            if (site == null || !site.Finished) return null;
            Transform root = site.VisualRoot;
            if (root == null) return null;
            if (!s_maps.TryGetValue(site, out RoomMap m)) { m = new RoomMap(); s_maps[site] = m; }
            if (m._for != root && Time.unscaledTime >= m._nextTry)
            {
                m._nextTry = Time.unscaledTime + 2f;   // (the model may still be loading: its walls have no colliders yet)
                m.Build(site, root);
            }
            return m._for == root ? m : null;
        }

        private int CellAt(ConstructionSite site, Vector3 world)
        {
            Vector3 l = Quaternion.Inverse(site.transform.rotation) * (world - site.transform.position);
            int ix = Mathf.FloorToInt((l.x - _rect.xMin) / Cell), iz = Mathf.FloorToInt((l.z - _rect.yMin) / Cell);
            return ix < 0 || iz < 0 || ix >= _nx || iz >= _nz ? -1 : iz * _nx + ix;
        }

        /// <summary>The room of the cell under the point, or of the nearest open cell within 0.6 m (a lamp on a wall sits in the wall's cell).</summary>
        private int Find(ConstructionSite site, Vector3 world)
        {
            int cell = CellAt(site, world);
            if (cell < 0) return -1;
            if (_room[cell] >= 0) return _room[cell];
            int cx = cell % _nx, cz = cell / _nx, best = -1, bestD = int.MaxValue;
            for (int dz = -3; dz <= 3; dz++)
                for (int dx = -3; dx <= 3; dx++)
                {
                    int x = cx + dx, z = cz + dz;
                    if (x < 0 || z < 0 || x >= _nx || z >= _nz || _room[z * _nx + x] < 0) continue;
                    int d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; best = _room[z * _nx + x]; }
                }
            return best;
        }

        private void Build(ConstructionSite site, Transform root)
        {
            if (root.GetComponentInChildren<Collider>() == null) return;   // not loaded yet
            _rect = site.WallRect();
            _nx = Mathf.Max(1, Mathf.CeilToInt(_rect.width / Cell));
            _nz = Mathf.Max(1, Mathf.CeilToInt(_rect.height / Cell));
            _room = new int[_nx * _nz];
            Quaternion rot = site.transform.rotation;
            // two heights just under the ceiling: over the doorways' headers (an interior door is 2.05 m), under the joists
            float ceiling = site.CeilingY();
            var half = new Vector3(Cell * 0.5f, 0.03f, Cell * 0.5f);
            int open = 0;
            for (int iz = 0; iz < _nz; iz++)
                for (int ix = 0; ix < _nx; ix++)
                {
                    Vector3 l = new Vector3(_rect.xMin + (ix + 0.5f) * Cell, 0f, _rect.yMin + (iz + 0.5f) * Cell);
                    Vector3 w = site.transform.position + rot * l;
                    bool wall = WallAt(new Vector3(w.x, ceiling - 0.12f, w.z), half, rot, root) || WallAt(new Vector3(w.x, ceiling - 0.3f, w.z), half, rot, root);
                    _room[iz * _nx + ix] = wall ? -1 : -2;   // -2: open, no room yet
                    if (!wall) open++;
                }
            _rooms = 0;
            _playerRoom = -1;
            if (open == 0)   // nothing open at that height (a model this does not suit): one room
            {
                for (int i = 0; i < _room.Length; i++) _room[i] = 0;
                _rooms = 1;
                _for = root;
                return;
            }
            var stack = new Stack<int>();
            var sizes = new List<int>();
            for (int i = 0; i < _room.Length; i++)
            {
                if (_room[i] != -2) continue;
                int id = _rooms++, size = 0;
                _room[i] = id;
                stack.Push(i);
                while (stack.Count > 0)
                {
                    int c = stack.Pop(), x = c % _nx, z = c / _nx;
                    size++;
                    if (x > 0) Take(c - 1, id, stack);
                    if (x < _nx - 1) Take(c + 1, id, stack);
                    if (z > 0) Take(c - _nx, id, stack);
                    if (z < _nz - 1) Take(c + _nx, id, stack);
                }
                sizes.Add(size);
            }
            // a pocket of a few cells (inside a chimney breast, between two studs) is not a room: it counts as wall
            int min = Mathf.CeilToInt(0.5f / (Cell * Cell));   // half a square metre
            for (int i = 0; i < _room.Length; i++) if (_room[i] >= 0 && sizes[_room[i]] < min) _room[i] = -1;
            _for = root;
            Dbg.Log("[Rooms] " + site.name + ": " + sizes.FindAll(s => s >= min).Count + " room(s), " + _nx + " x " + _nz + " cells");
        }

        private void Take(int cell, int id, Stack<int> stack)
        {
            if (_room[cell] != -2) return;
            _room[cell] = id;
            stack.Push(cell);
        }

        /// <summary>True where a part of the building's own model stands (not its roof, not a thing mounted on it).</summary>
        private static bool WallAt(Vector3 at, Vector3 half, Quaternion rot, Transform root)
        {
            int n = Physics.OverlapBoxNonAlloc(at, half, s_hits, rot, ~0, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                Transform t = s_hits[i].transform;
                if (!t.IsChildOf(root)) continue;
                bool skip = false;
                for (Transform p = t; p != null && p != root; p = p.parent)
                    if (p.name == "Roof" || p.name.StartsWith("Door") || p.GetComponent<AttachedObject>() != null) { skip = true; break; }
                if (!skip) return true;
            }
            return false;
        }
    }
}
