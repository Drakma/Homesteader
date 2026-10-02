using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Makes the procedural forest solid: tree trunks and the bigger rocks block the player and the animals.
    /// The trees and rocks are baked into chunk meshes and there are thousands of them, so real colliders exist only
    /// near the player: a pool of capsule colliders is moved onto whichever solids are within range and re-placed as the
    /// player walks. The colliders sit on the "Ignore Raycast" layer, so the mouse (hover, planting, placing) still
    /// sees straight through them to the ground; they only stop bodies.
    /// </summary>
    public static class ForestSolids
    {
        private struct Solid
        {
            public Vector3 Pos;
            public float Radius;
            public float Height;
            public ForestTree Tree;   // null for a rock
        }

        private const float CellSize = 16f;
        private const float ActiveRange = 30f;       // colliders are kept within this many metres of the player
        private const float MoveThreshold = 2.5f;    // re-place them after the player moves this far
        private const int PoolSize = 320;
        private const float MinRockRadius = 0.40f;   // smaller stones and scree are walk-over

        private static readonly List<Solid> Solids = new List<Solid>();
        private static readonly Dictionary<Vector2Int, List<int>> Grid = new Dictionary<Vector2Int, List<int>>();
        private static Streamer _streamer;
        private static bool _dirty;

        public static int Count => Solids.Count;

        /// <summary>Forget the previous world's solids (start of a generation).</summary>
        public static void Clear()
        {
            Solids.Clear();
            Grid.Clear();
            _dirty = true;
            if (_streamer != null) Object.Destroy(_streamer.gameObject);
            _streamer = null;
        }

        /// <summary>Create the object that moves colliders onto the solids near the player. Call after the scatter is merged
        /// (ProceduralVegetation.Combine removes the scatter's children, this one must be made after it).</summary>
        public static void StartStreaming(Transform root)
        {
            if (_streamer != null) Object.Destroy(_streamer.gameObject);
            var go = new GameObject("ForestSolids");
            go.transform.SetParent(root, false);
            _streamer = go.AddComponent<Streamer>();
            _dirty = true;
        }

        private static void Add(Solid s)
        {
            int index = Solids.Count;
            Solids.Add(s);
            var cell = new Vector2Int(Mathf.FloorToInt(s.Pos.x / CellSize), Mathf.FloorToInt(s.Pos.z / CellSize));
            if (!Grid.TryGetValue(cell, out List<int> list)) { list = new List<int>(); Grid[cell] = list; }
            list.Add(index);
        }

        public static void AddTree(ForestTree tree)
        {
            Add(new Solid { Pos = tree.Position, Tree = tree });
        }

        /// <summary>A rock mesh placed at a transform: solid when it is big enough to be in the way.</summary>
        public static void AddRock(Mesh mesh, Transform placed)
        {
            Vector3 e = mesh.bounds.extents;
            Vector3 sc = placed.lossyScale;
            float radius = Mathf.Max(e.x * sc.x, e.z * sc.z);
            if (radius < MinRockRadius) return;
            Add(new Solid { Pos = placed.position, Radius = radius * 0.85f, Height = Mathf.Max(radius * 1.2f, mesh.bounds.size.y * sc.y) });
        }

        /// <summary>A tree was felled (or something else changed): re-place the colliders now.</summary>
        public static void MarkDirty() { _dirty = true; }

        /// <summary>Place the colliders around a point right now (a teleport, or a test), without waiting for the next update.</summary>
        public static void PlaceNow(Vector3 center)
        {
            if (_streamer != null) _streamer.PlaceAround(center);
        }

        private sealed class Streamer : MonoBehaviour
        {
            public void PlaceAround(Vector3 center)
            {
                if (_pool.Count == 0) Awake();
                _lastPlayerPos = center;
                _dirty = false;
                Place(center);
            }

            private readonly List<CapsuleCollider> _pool = new List<CapsuleCollider>();
            private Transform _player;
            private Vector3 _lastPlayerPos = new Vector3(float.MaxValue, 0f, 0f);
            private float _nextCheck;

            private void Awake()
            {
                if (_pool.Count > 0) return;
                for (int i = 0; i < PoolSize; i++)
                {
                    var go = new GameObject("ForestSolid");
                    go.layer = 2;   // Ignore Raycast: stops bodies, invisible to the mouse raycasts
                    go.transform.SetParent(transform, false);
                    var col = go.AddComponent<CapsuleCollider>();
                    col.direction = 1;
                    col.enabled = false;
                    _pool.Add(col);
                }
            }

            private void Update()
            {
                if (Time.unscaledTime < _nextCheck && !_dirty) return;
                _nextCheck = Time.unscaledTime + 0.2f;

                if (_player == null)
                {
                    var ped = FindAnyObjectByType<PedController>();
                    if (ped != null) _player = ped.transform;
                    if (_player == null) return;
                }

                Vector3 p = _player.position;
                if (!_dirty && (p - _lastPlayerPos).sqrMagnitude < MoveThreshold * MoveThreshold) return;
                _lastPlayerPos = p;
                _dirty = false;
                Place(p);
            }

            private void Place(Vector3 center)
            {
                int used = 0;
                int cx0 = Mathf.FloorToInt((center.x - ActiveRange) / CellSize), cx1 = Mathf.FloorToInt((center.x + ActiveRange) / CellSize);
                int cz0 = Mathf.FloorToInt((center.z - ActiveRange) / CellSize), cz1 = Mathf.FloorToInt((center.z + ActiveRange) / CellSize);
                float rangeSq = ActiveRange * ActiveRange;

                for (int cx = cx0; cx <= cx1; cx++)
                {
                    for (int cz = cz0; cz <= cz1; cz++)
                    {
                        if (!Grid.TryGetValue(new Vector2Int(cx, cz), out List<int> list)) continue;
                        foreach (int index in list)
                        {
                            Solid s = Solids[index];
                            float dx = s.Pos.x - center.x, dz = s.Pos.z - center.z;
                            if (dx * dx + dz * dz > rangeSq) continue;
                            if (used >= _pool.Count) break;

                            float radius, height;
                            if (s.Tree != null)
                            {
                                if (s.Tree.Felled) continue;
                                ForestTrees.TrunkSize(s.Tree, out radius, out height);
                            }
                            else
                            {
                                radius = s.Radius;
                                height = s.Height;
                            }

                            CapsuleCollider col = _pool[used++];
                            col.radius = radius;
                            col.height = Mathf.Max(height, radius * 2f);
                            col.transform.position = s.Pos + Vector3.up * (col.height * 0.5f - 0.05f);
                            col.enabled = true;
                        }
                    }
                }
                for (int i = used; i < _pool.Count; i++) _pool[i].enabled = false;
            }
        }
    }
}
