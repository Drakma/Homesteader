using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Pallets (any asset with properties.support_surface = true) carry things on top. Placing an item over a pallet's deck puts it ON
    /// the deck, in the pallet's own turn, packed in the free space (side by side, and identical items stacked up to their stacking
    /// limit). A pallet that still carries things cannot be picked up. The packing works in the pallet's local space, so it holds at any turn.
    /// </summary>
    public static class PalletDeck
    {
        public const float TopLimit = 1.6f;   // metres above the deck: nothing is stacked higher than this

        public static bool IsPallet(string itemId)
        {
            AssetCatalogItem c = HudBindings.GetCatalogItem(itemId);
            return c != null && c.support_surface;
        }

        /// <summary>The footprint (x, z) of an object's meshes in the local space of <paramref name="frame"/>; false until a model has loaded.</summary>
        public static bool LocalRect(Transform frame, GameObject obj, out Rect rect)
        {
            rect = default;
            bool any = false;
            float x0 = 0f, x1 = 0f, z0 = 0f, z1 = 0f;
            foreach (MeshFilter mf in obj.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null) continue;
                Bounds mb = mf.sharedMesh.bounds;
                Vector3 e = mb.extents, c = mb.center;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z);
                    Vector3 l = frame.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { x0 = x1 = l.x; z0 = z1 = l.z; any = true; }
                    else { x0 = Mathf.Min(x0, l.x); x1 = Mathf.Max(x1, l.x); z0 = Mathf.Min(z0, l.z); z1 = Mathf.Max(z1, l.z); }
                }
            }
            if (any) rect = new Rect(x0, z0, x1 - x0, z1 - z0);
            return any;
        }

        /// <summary>The pallet whose deck the point is over (nothing else is checked), or null.</summary>
        public static PlacedObject PalletUnder(Vector3 world)
        {
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsPallet(o.ItemId)) continue;
                if (!LocalRect(o.transform, o.gameObject, out Rect deck)) continue;
                Vector3 l = o.transform.InverseTransformPoint(world);
                if (deck.Contains(new Vector2(l.x, l.z))) return o;
            }
            return null;
        }

        public static float DeckY(PlacedObject pallet) { return pallet.transform.position.y + pallet.Height; }

        /// <summary>What stands on the pallet now (everything above its deck inside its footprint), the pallet itself excluded.</summary>
        public static List<PlacedObject> Carried(PlacedObject pallet)
        {
            var list = new List<PlacedObject>();
            if (!LocalRect(pallet.transform, pallet.gameObject, out Rect deck)) return list;
            float y = pallet.transform.position.y + 0.05f;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == pallet) continue;
                Vector3 l = pallet.transform.InverseTransformPoint(o.transform.position);
                if (deck.Contains(new Vector2(l.x, l.z)) && o.transform.position.y > y) list.Add(o);
            }
            return list;
        }

        /// <summary>
        /// Where an item of this size goes on the pallet: on top of an identical stack under the point when it is under its limit,
        /// otherwise in the free spot nearest the point. <paramref name="ignore"/> is an object to leave out (the one being placed).
        /// </summary>
        public static bool FindSpot(PlacedObject pallet, string itemId, Vector2 size, Vector3 wantWorld, PlacedObject ignore,
                                    out Vector3 position, out int level, out string reason)
        {
            position = default;
            level = 1;
            reason = null;
            if (!LocalRect(pallet.transform, pallet.gameObject, out Rect deck)) { reason = "The pallet has not loaded yet."; return false; }
            float deckY = DeckY(pallet);
            Vector3 wl = pallet.transform.InverseTransformPoint(wantWorld);
            Vector2 want = new Vector2(wl.x, wl.z);

            // the columns already on it
            var cols = new List<List<PlacedObject>>();
            foreach (PlacedObject o in Carried(pallet))
            {
                if (o == ignore) continue;
                List<PlacedObject> col = null;
                foreach (List<PlacedObject> c in cols)
                {
                    Vector3 q = c[0].transform.position, p = o.transform.position;
                    if (Mathf.Abs(q.x - p.x) < 0.08f && Mathf.Abs(q.z - p.z) < 0.08f) { col = c; break; }
                }
                if (col == null) { col = new List<PlacedObject>(); cols.Add(col); }
                col.Add(o);
            }
            foreach (List<PlacedObject> c in cols) c.Sort((a, b) => a.transform.position.y.CompareTo(b.transform.position.y));

            // 1) stack on an identical column under the point
            int limit = Mathf.Max(1, ContainerRules.StackingLimit(itemId));
            var rects = new List<Rect>();
            foreach (List<PlacedObject> c in cols)
            {
                Rect r = default;
                bool any = false;
                foreach (PlacedObject o in c)
                {
                    if (!LocalRect(pallet.transform, o.gameObject, out Rect orect)) continue;
                    r = any ? Union(r, orect) : orect;
                    any = true;
                }
                if (!any) continue;
                rects.Add(r);
                PlacedObject top = c[c.Count - 1];
                bool under = new Rect(r.x - 0.05f, r.y - 0.05f, r.width + 0.1f, r.height + 0.1f).Contains(want);
                if (under && top.ItemId == itemId && c.Count < limit)
                {
                    float topY = top.transform.position.y + top.Height;
                    if (topY + 0.01f - deckY > TopLimit) { reason = "That stack is as high as it goes."; return false; }
                    position = new Vector3(top.transform.position.x, topY, top.transform.position.z);
                    level = top.Level + 1;
                    return true;
                }
            }

            // 2) the free spot nearest the point
            float w = size.x, d = size.y;
            if (w > deck.width + 0.01f || d > deck.height + 0.01f) { reason = "That does not fit on the pallet."; return false; }
            const float gap = 0.01f, step = 0.05f;
            bool found = false;
            Vector2 best = default;
            float bestDist = float.MaxValue;
            for (float x = deck.xMin + w * 0.5f; x <= deck.xMax - w * 0.5f + 0.001f; x += step)
                for (float z = deck.yMin + d * 0.5f; z <= deck.yMax - d * 0.5f + 0.001f; z += step)
                {
                    var cand = new Rect(x - w * 0.5f - gap, z - d * 0.5f - gap, w + 2f * gap, d + 2f * gap);
                    bool free = true;
                    foreach (Rect r in rects) if (cand.Overlaps(r)) { free = false; break; }
                    if (!free) continue;
                    float dist = (new Vector2(x, z) - want).sqrMagnitude;
                    if (dist < bestDist) { bestDist = dist; best = new Vector2(x, z); found = true; }
                }
            if (!found) { reason = "The pallet is full."; return false; }
            Vector3 world = pallet.transform.TransformPoint(new Vector3(best.x, 0f, best.y));
            position = new Vector3(world.x, deckY, world.z);
            level = 1;
            return true;
        }

        private static Rect Union(Rect a, Rect b)
        {
            float x0 = Mathf.Min(a.xMin, b.xMin), x1 = Mathf.Max(a.xMax, b.xMax), z0 = Mathf.Min(a.yMin, b.yMin), z1 = Mathf.Max(a.yMax, b.yMax);
            return new Rect(x0, z0, x1 - x0, z1 - z0);
        }
    }
}
