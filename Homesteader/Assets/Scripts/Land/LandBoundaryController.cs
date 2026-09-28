using System.Collections.Generic;
using UnityEngine;
using Homesteader.Land;

namespace Homesteader.Land
{
    /// <summary>
    /// Creates and maintains invisible collision walls on the boundary between
    /// owned and unowned tiles, plus a faint yellow LineRenderer border on the
    /// owned side of those walls.
    ///
    /// Walls are box colliders placed along each border edge, tall enough to
    /// block the CharacterController but invisible. The yellow border is a
    /// LineRenderer that traces the same edges, slightly inside the owned tile.
    /// </summary>
    [RequireComponent(typeof(LineRenderer))]
    public class LandBoundaryController : MonoBehaviour
    {
        private LineRenderer _borderLine;
        private readonly List<GameObject> _wallObjects = new List<GameObject>();

        // Wall height and thickness
        private const float WallHeight = 8f;
        private const float WallThickness = 0.5f;
        // How far to inset the yellow line from the tile edge (so it sits on the owned side)
        private const float BorderInset = 0.3f;

        private void Awake()
        {
            _borderLine = GetComponent<LineRenderer>();
            _borderLine.loop = false;
            _borderLine.widthMultiplier = 0.15f;
            _borderLine.material = CreateBorderMaterial();
            _borderLine.startColor = new Color(1f, 0.92f, 0.23f, 0.35f); // faint yellow
            _borderLine.endColor = new Color(1f, 0.92f, 0.23f, 0.35f);
            _borderLine.positionCount = 0;
            _borderLine.alignment = LineAlignment.View;
            _borderLine.sortingOrder = 100;
        }

        private static Material CreateBorderMaterial()
        {
            // Unlit transparent so the line is always visible regardless of lighting
            var shader = Shader.Find("Unlit/Transparent");
            if (shader == null) shader = Shader.Find("Hidden/Internal-Colored");
            var mat = new Material(shader);
            mat.color = new Color(1f, 0.92f, 0.23f, 0.35f);
            return mat;
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
            BuildBorderLine(edges);
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

        private void BuildBorderLine(List<LandOwnershipSystem.BorderEdge> edges)
        {
            if (edges.Count == 0)
            {
                _borderLine.positionCount = 0;
                return;
            }

            // Sort edges into connected loops
            var loops = ConnectEdgesIntoLoops(edges);

            // Subdivide each edge segment so the line follows terrain elevation
            // instead of cutting straight through hills and valleys.
            const float sampleInterval = 2f; // metres between terrain height samples
            var positions = new List<Vector3>();
            foreach (var loop in loops)
            {
                for (int i = 0; i < loop.Count - 1; i++)
                {
                    var a = loop[i];
                    var b = loop[i + 1];
                    float segLen = Vector2.Distance(a, b);
                    int steps = Mathf.Max(2, Mathf.CeilToInt(segLen / sampleInterval));
                    for (int s = 0; s < steps; s++)
                    {
                        float t = (float)s / steps;
                        float px = Mathf.Lerp(a.x, b.x, t);
                        float pz = Mathf.Lerp(a.y, b.y, t);
                        float py = Homesteader.Generation.TerrainHeightDetector.GetGroundY(px, pz) + 0.05f;
                        positions.Add(new Vector3(px, py, pz));
                    }
                }
                // Add the final point of the loop
                var last = loop[loop.Count - 1];
                float ly = Homesteader.Generation.TerrainHeightDetector.GetGroundY(last.x, last.y) + 0.05f;
                positions.Add(new Vector3(last.x, ly, last.y));
                // Add a duplicate point to create a visual break between loops
                positions.Add(positions[positions.Count - 1]);
            }

            _borderLine.positionCount = positions.Count;
            _borderLine.SetPositions(positions.ToArray());
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
