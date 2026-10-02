using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Flat-shaded oriented-box mesher for the procedural props (bridges, fences). Boxes are added in world space with a
    /// material slot each; ToMesh turns the slots into submeshes.
    /// </summary>
    public sealed class BoxMesher
    {
        private readonly List<Vector3> _v = new List<Vector3>();
        private readonly List<Vector3> _n = new List<Vector3>();
        private readonly Dictionary<int, List<int>> _t = new Dictionary<int, List<int>>();

        public int VertexCount => _v.Count;

        /// <summary>An oriented box: centre, three axes (right, up, forward) and half extents along them.</summary>
        public void Box(Vector3 c, Vector3 r, Vector3 u, Vector3 f, Vector3 h, int mat)
        {
            Vector3 rx = r * h.x, uy = u * h.y, fz = f * h.z;
            Vector3 p000 = c - rx - uy - fz, p100 = c + rx - uy - fz, p010 = c - rx + uy - fz, p110 = c + rx + uy - fz;
            Vector3 p001 = c - rx - uy + fz, p101 = c + rx - uy + fz, p011 = c - rx + uy + fz, p111 = c + rx + uy + fz;
            Quad(p010, p110, p111, p011, u, mat);     // top
            Quad(p000, p001, p101, p100, -u, mat);    // bottom
            Quad(p100, p101, p111, p110, r, mat);     // right
            Quad(p000, p010, p011, p001, -r, mat);    // left
            Quad(p001, p011, p111, p101, f, mat);     // front
            Quad(p000, p100, p110, p010, -f, mat);    // back
        }

        /// <summary>A box running from a to b (a beam, rail or plank), thickness given as half extents across.</summary>
        public void Beam(Vector3 a, Vector3 b, float halfAcross, float halfUp, int mat)
        {
            Vector3 f = (b - a).normalized;
            Vector3 r = Vector3.Cross(Vector3.up, f);
            if (r.sqrMagnitude < 0.01f) r = Vector3.right;
            r.Normalize();
            Vector3 u = Vector3.Cross(f, r).normalized;
            Box((a + b) * 0.5f, r, u, f, new Vector3(halfAcross, halfUp, (b - a).magnitude * 0.5f + 0.02f), mat);
        }

        private void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 outward, int mat)
        {
            Vector3 n = Vector3.Cross(b - a, d - a);
            if (n.sqrMagnitude < 1e-10f) return;
            n.Normalize();
            // Wind so the face points along 'outward'.
            if (Vector3.Dot(n, outward) < 0f) { (b, d) = (d, b); n = -n; }

            if (!_t.TryGetValue(mat, out List<int> tris)) { tris = new List<int>(); _t[mat] = tris; }
            int i = _v.Count;
            _v.Add(a); _v.Add(b); _v.Add(c); _v.Add(d);
            _n.Add(n); _n.Add(n); _n.Add(n); _n.Add(n);
            tris.Add(i); tris.Add(i + 1); tris.Add(i + 2);
            tris.Add(i); tris.Add(i + 2); tris.Add(i + 3);
        }

        public Mesh ToMesh(string name, int subMeshes)
        {
            var mesh = new Mesh { name = name, indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(_v);
            mesh.SetNormals(_n);
            mesh.subMeshCount = subMeshes;
            for (int i = 0; i < subMeshes; i++)
                mesh.SetTriangles(_t.TryGetValue(i, out List<int> tris) ? tris : new List<int>(), i);
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
