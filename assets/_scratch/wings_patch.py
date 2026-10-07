import os
os.chdir(r'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\Growth')


def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)


OLD_BODY = """            float x0 = float.MaxValue, x1 = float.MinValue, zAll0 = float.MaxValue, zAll1 = float.MinValue, zSide0 = float.MaxValue, zSide1 = float.MinValue;
            bool any = false, side = false;
            if (root != null)
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
                {
                    bool wall = false, sideWall = false;
                    for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                        if (t.name.StartsWith("Wall_")) { wall = true; sideWall = t.name == "Wall_Left" || t.name == "Wall_Right"; break; }
                    if (!wall) continue;
                    Bounds b = r.bounds;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                        Vector3 l = inv * (c - transform.position);
                        x0 = Mathf.Min(x0, l.x); x1 = Mathf.Max(x1, l.x);
                        zAll0 = Mathf.Min(zAll0, l.z); zAll1 = Mathf.Max(zAll1, l.z);
                        if (sideWall) { zSide0 = Mathf.Min(zSide0, l.z); zSide1 = Mathf.Max(zSide1, l.z); side = true; }
                        any = true;
                    }
                }
            Rect rect = !any ? new Rect(-_foot.x * 0.5f, -_foot.y * 0.5f, _foot.x, _foot.y)
                             : side ? Rect.MinMaxRect(x0, zSide0, x1, zSide1) : Rect.MinMaxRect(x0, zAll0, x1, zAll1);
            if (root != null && any) { _wallRectFor = root; _wallRect = rect; }
            return rect;
        }"""

NEW_BODY = """            // A wall part named "Wall_Left@B" belongs to the wing "B" (an L-shaped house is two wings): each wing has its own rectangle. A name without "@" is the main (and only) wing.
            var wings = new Dictionary<string, float[]>();   // x0, x1, zAll0, zAll1, zSide0, zSide1, side (0/1)
            bool any = false;
            if (root != null)
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
                {
                    bool wall = false, sideWall = false;
                    string wing = "";
                    for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                        if (t.name.StartsWith("Wall_"))
                        {
                            wall = true;
                            int at = t.name.IndexOf('@');
                            string baseName = at >= 0 ? t.name.Substring(0, at) : t.name;
                            wing = at >= 0 ? t.name.Substring(at + 1) : "";
                            sideWall = baseName == "Wall_Left" || baseName == "Wall_Right";
                            break;
                        }
                    if (!wall) continue;
                    if (!wings.TryGetValue(wing, out float[] w)) { w = new[] { float.MaxValue, float.MinValue, float.MaxValue, float.MinValue, float.MaxValue, float.MinValue, 0f }; wings[wing] = w; }
                    Bounds b = r.bounds;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                        Vector3 l = inv * (c - transform.position);
                        w[0] = Mathf.Min(w[0], l.x); w[1] = Mathf.Max(w[1], l.x);
                        w[2] = Mathf.Min(w[2], l.z); w[3] = Mathf.Max(w[3], l.z);
                        if (sideWall) { w[4] = Mathf.Min(w[4], l.z); w[5] = Mathf.Max(w[5], l.z); w[6] = 1f; }
                        any = true;
                    }
                }
            var rects = new List<Rect>();
            foreach (float[] w in wings.Values) rects.Add(w[6] > 0.5f ? Rect.MinMaxRect(w[0], w[4], w[1], w[5]) : Rect.MinMaxRect(w[0], w[2], w[1], w[3]));
            Rect rect = !any ? new Rect(-_foot.x * 0.5f, -_foot.y * 0.5f, _foot.x, _foot.y) : rects[0];
            for (int i = 1; i < rects.Count; i++) rect = Rect.MinMaxRect(Mathf.Min(rect.xMin, rects[i].xMin), Mathf.Min(rect.yMin, rects[i].yMin), Mathf.Max(rect.xMax, rects[i].xMax), Mathf.Max(rect.yMax, rects[i].yMax));
            if (root != null && any) { _wallRectFor = root; _wallRect = rect; _wallRects = rects; }
            return rect;
        }

        /// <summary>The rectangle of each wing of the building (one for a plain building, two for an L). In the building's own space.</summary>
        public List<Rect> WallRects() { WallRect(); return _wallRects.Count > 0 ? _wallRects : new List<Rect> { WallRect() }; }

        /// <summary>True when the building has more than one wing (an L, a T): its walls do not make one rectangle.</summary>
        public bool MultiWing { get { return WallRects().Count > 1; } }

        /// <summary>True when a point (building space, x and z) is inside the walls of any wing.</summary>
        public bool InsideAnyWing(float x, float z)
        {
            foreach (Rect r in WallRects()) if (x >= r.xMin && x <= r.xMax && z >= r.yMin && z <= r.yMax) return true;
            return false;
        }

        /// <summary>The wing's rectangle that holds a point (building space), or the nearest one.</summary>
        public Rect WingRectNear(float x, float z)
        {
            Rect best = WallRect();
            float bestD = float.MaxValue;
            foreach (Rect r in WallRects())
            {
                float dx = Mathf.Max(0f, Mathf.Max(r.xMin - x, x - r.xMax)), dz = Mathf.Max(0f, Mathf.Max(r.yMin - z, z - r.yMax));
                float d = dx * dx + dz * dz;
                if (d < bestD) { bestD = d; best = r; }
            }
            return best;
        }"""

edit('ConstructionSite.cs', [
    ("        private Rect _wallRect;               // x, z (as x, y) of the walls in the building's own space\n        private Transform _wallRectFor;",
     "        private Rect _wallRect;               // x, z (as x, y) of the walls in the building's own space (the box round every wing)\n        private List<Rect> _wallRects = new List<Rect>();   // one rectangle per wing of an L-shaped building; a plain building has one\n        private Transform _wallRectFor;"),
    (OLD_BODY, NEW_BODY),
    ("            Rect r = WallRect();\n            Vector3 l = Quaternion.Inverse(transform.rotation) * (world - transform.position);\n            return l.x >= r.xMin && l.x <= r.xMax && l.z >= r.yMin && l.z <= r.yMax;",
     "            WallRect();\n            Vector3 l = Quaternion.Inverse(transform.rotation) * (world - transform.position);\n            return InsideAnyWing(l.x, l.z);"),
])
edit('PlacementController.cs', [
    ("            Rect r = site.WallRect();\n            float wall = AttachedObject.DefaultWall + 0.02f;\n            float half = Mathf.Max(size.x, size.y) * 0.5f;\n            Quaternion rot = site.transform.rotation;\n            Vector3 l = Quaternion.Inverse(rot) * (hit - site.transform.position);",
     "            Quaternion rot = site.transform.rotation;\n            Vector3 l = Quaternion.Inverse(rot) * (hit - site.transform.position);\n            Rect r = site.WingRectNear(l.x, l.z);   // the wing the cursor is in (an L-shaped house has two)\n            float wall = AttachedObject.DefaultWall + 0.02f;\n            float half = Mathf.Max(size.x, size.y) * 0.5f;"),
])
edit('AttachController.cs', [
    ("                Rect wr = site.WallRect();                                        // the walls' rectangle",
     "                Rect wr = site.WingRectNear(lp.x, lp.z);                          // the walls' rectangle (of the wing the cursor is in)"),
])
edit('RoomMap.cs', [
    ("bool wall = WallAt(new Vector3(w.x, ceiling - 0.12f, w.z), half, rot, root)",
     "bool wall = !site.InsideAnyWing(l.x, l.z) || WallAt(new Vector3(w.x, ceiling - 0.12f, w.z), half, rot, root)"),
])
print('ok')
