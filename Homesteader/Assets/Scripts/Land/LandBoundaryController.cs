using System.Collections.Generic;
using UnityEngine;
using Homesteader.Land;

namespace Homesteader.Land
{
    /// <summary>
    /// Creates and maintains invisible collision walls on the boundary between
    /// owned and unowned tiles, plus a procedural post-and-rail fence along them
    /// (World/ProceduralFence.cs; it stops for water and leaves an opening for the road).
    ///
    /// Walls are box colliders placed along each border edge, tall enough to
    /// block the CharacterController but invisible.
    /// </summary>
    public class LandBoundaryController : MonoBehaviour
    {
        private GameObject _fence;
        private readonly List<GameObject> _wallObjects = new List<GameObject>();

        // Wall height and thickness
        private const float WallHeight = 8f;
        private const float WallThickness = 0.5f;

        private void Awake()
        {
            // The old yellow border line is gone (the fence replaces it). An older scene may still carry the
            // LineRenderer, so make sure it draws nothing.
            var line = GetComponent<LineRenderer>();
            if (line != null)
            {
                line.positionCount = 0;
                line.enabled = false;
            }
        }

        /// <summary>Rebuilds all walls and the border line from current ownership state.</summary>
        public void RebuildBoundaries()
        {
            // Clear old walls
            foreach (var w in _wallObjects)
            {
                if (w != null) Destroy(w);
            }
            _wallObjects.Clear();

            LandOwnershipSystem.Initialize();

            var edges = LandOwnershipSystem.ComputeBorderEdges();
            BuildWalls(edges);
            BuildFence(edges);
        }

        private void BuildWalls(List<LandOwnershipSystem.BorderEdge> edges)
        {
            foreach (var edge in edges)
            {
                float midX = (edge.x1 + edge.x2) * 0.5f;
                float midZ = (edge.z1 + edge.z2) * 0.5f;
                float lengthX = Mathf.Abs(edge.x2 - edge.x1);
                float lengthZ = Mathf.Abs(edge.z2 - edge.z1);
                float length = Mathf.Max(lengthX, lengthZ);
                if (length < 0.01f) continue;

                // Determine orientation: horizontal edge (along X) or vertical edge (along Z)
                bool isHorizontal = lengthX > lengthZ;

                var go = new GameObject($"LandWall_{midX:F0}_{midZ:F0}");
                go.transform.SetParent(transform);

                // Place the wall at ground level
                float groundY = Homesteader.Generation.TerrainHeightDetector.GetGroundY(midX, midZ);
                go.transform.position = new Vector3(midX, groundY + WallHeight * 0.5f, midZ);

                var col = go.AddComponent<BoxCollider>();
                col.size = new Vector3(
                    isHorizontal ? length + WallThickness : WallThickness,
                    WallHeight,
                    isHorizontal ? WallThickness : length + WallThickness
                );

                _wallObjects.Add(go);
            }
        }

        private void BuildFence(List<LandOwnershipSystem.BorderEdge> edges)
        {
            if (_fence != null) Destroy(_fence);
            _fence = null;
            if (edges.Count == 0) return;

            var gen = FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>();
            _fence = Homesteader.World.ProceduralFence.Build(transform, ConnectEdgesIntoLoops(edges), gen);
        }

        /// <summary>
        /// Greedily connects border edges into closed or open loops by matching
        /// endpoints. Returns a list of loops, each a list of (x,z) points.
        /// </summary>
        private List<List<Vector2>> ConnectEdgesIntoLoops(List<LandOwnershipSystem.BorderEdge> edges)
        {
            // Work with a mutable copy
            var remaining = new List<LandOwnershipSystem.BorderEdge>(edges);
            var loops = new List<List<Vector2>>();

            while (remaining.Count > 0)
            {
                var loop = new List<Vector2>();
                var first = remaining[0];
                remaining.RemoveAt(0);
                loop.Add(new Vector2(first.x1, first.z1));
                loop.Add(new Vector2(first.x2, first.z2));

                Vector2 currentEnd = new Vector2(first.x2, first.z2);
                bool found = true;

                while (found)
                {
                    found = false;
                    for (int i = 0; i < remaining.Count; i++)
                    {
                        var e = remaining[i];
                        var a = new Vector2(e.x1, e.z1);
                        var b = new Vector2(e.x2, e.z2);

                        if (Vector2.Distance(a, currentEnd) < 0.01f)
                        {
                            loop.Add(b);
                            currentEnd = b;
                            remaining.RemoveAt(i);
                            found = true;
                            break;
                        }
                        else if (Vector2.Distance(b, currentEnd) < 0.01f)
                        {
                            loop.Add(a);
                            currentEnd = a;
                            remaining.RemoveAt(i);
                            found = true;
                            break;
                        }
                    }
                }

                loops.Add(loop);
            }

            return loops;
        }
    }
}
