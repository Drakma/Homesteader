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

        private static readonly Dictionary<string, List<float>> HeightCache = new Dictionary<string, List<float>>();
        private static readonly List<float> NoDecks = new List<float>();
        private const float OpenTopM = 0.12f;   // a top shelf this close to the model's height is its open top (a table, a cabinet top): stacks go up to TopLimit
        private const float BoardM = 0.035f;   // a shelf board's thickness and a little air: what is lost between one shelf's top face and the underside of the next

        /// <summary>The height of each shelf's top face above the ground, lowest first (a shelving unit: properties.deck_heights), or empty for a pallet (one deck at the model height).</summary>
        public static List<float> DeckHeights(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return NoDecks;
            if (HeightCache.TryGetValue(itemId, out List<float> cached)) return cached;
            var list = new List<float>();
            AssetCatalogItem c = HudBindings.GetCatalogItem(itemId);
            if (c != null && c.support_surface && !string.IsNullOrEmpty(c.deck_heights))
                foreach (string part in c.deck_heights.Split(','))
                    if (float.TryParse(part.Trim(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float h) && h > 0f) list.Add(h);
            list.Sort();
            if (c != null) HeightCache[itemId] = list;
            return list;
        }

        /// <summary>A shelving unit: a pallet with several decks (shelves).</summary>
        public static bool IsShelving(string itemId) { return DeckHeights(itemId).Count > 1; }

        /// <summary>How much room there is above a deck: up to the next shelf (or the top of the unit). A pallet's stacks go as high as <see cref="TopLimit"/>.</summary>
        public static float Clearance(PlacedObject pallet, int deck)
        {
            List<float> hs = DeckHeights(pallet.ItemId);
            if (hs.Count == 0) return TopLimit;
            deck = Mathf.Clamp(deck, 0, hs.Count - 1);
            if (deck + 1 < hs.Count) return Mathf.Max(0.05f, hs[deck + 1] - hs[deck] - BoardM);
            // the topmost shelf: when it IS the top of the model (a desk, a cabinet or a table top) nothing is above it; otherwise a cap or the ceiling of the unit is
            if (hs[deck] >= pallet.Height - OpenTopM) return TopLimit;
            return Mathf.Max(0.05f, pallet.Height - hs[deck] - BoardM);
        }

        /// <summary>
        /// The shelving unit the camera ray goes into, and WHICH shelf: the ray is followed down through the unit and the first shelf whose top face it crosses inside the unit
        /// is the one (an upper shelf covers the ones below it from above, so a lower shelf is reached by pointing at its open front). <paramref name="point"/> is where it crosses.
        /// </summary>
        public static bool UnderRay(Ray ray, out PlacedObject pallet, out int deck, out Vector3 point)
        {
            pallet = null; deck = 0; point = default;
            float bestDist = float.MaxValue;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsShelving(o.ItemId)) continue;
                if (!LocalRect(o.transform, o.gameObject, out Rect footprint)) continue;
                List<float> hs = DeckHeights(o.ItemId);
                for (int d = hs.Count - 1; d >= 0; d--)
                {
                    var plane = new Plane(Vector3.up, new Vector3(0f, o.transform.position.y + hs[d], 0f));
                    if (!plane.Raycast(ray, out float enter)) continue;
                    Vector3 p = ray.GetPoint(enter);
                    Vector3 l = o.transform.InverseTransformPoint(p);
                    if (!footprint.Contains(new Vector2(l.x, l.z))) continue;
                    if (enter < bestDist) { bestDist = enter; pallet = o; deck = d; point = p; }
                    break;   // the first shelf the ray comes to
                }
            }
            return pallet != null;
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
                if (o == null || !IsPallet(o.ItemId) || IsShelving(o.ItemId)) continue;   // a shelving unit is found by the ray (UnderRay)
                if (!LocalRect(o.transform, o.gameObject, out Rect deck)) continue;
                Vector3 l = o.transform.InverseTransformPoint(world);
                float tol = KitchenRun.IsRun(o.ItemId) ? 0.06f : 0f;   // a kitchen counter pointed at on its front face still counts: the cursor lands on the face, at the edge of the top
                if (new Rect(deck.x - tol, deck.y - tol, deck.width + 2f * tol, deck.height + 2f * tol).Contains(new Vector2(l.x, l.z))) return o;
            }
            return null;
        }

        public static float DeckY(PlacedObject pallet, int deck = 0)
        {
            List<float> hs = DeckHeights(pallet.ItemId);
            if (hs.Count > 0) return pallet.transform.position.y + hs[Mathf.Clamp(deck, 0, hs.Count - 1)];
            return pallet.transform.position.y + pallet.Height;
        }

        /// <summary>True for a loose item standing on a pallet, counter or shelf (not furniture itself): it comes off by hand.</summary>
        public static bool RestsOnDeck(PlacedObject o)
        {
            if (o == null || IsPallet(o.ItemId) || ItemRegistry.NeedsWrench(o.ItemId)) return false;
            foreach (PlacedObject p in PlacedObject.All)
                if (p != null && p != o && IsPallet(p.ItemId) && Carried(p).Contains(o)) return true;
            return false;
        }

        /// <summary>What stands on the pallet now (everything above its deck inside its footprint), the pallet itself excluded. For a shelving unit <paramref name="deck"/> picks one shelf (-1: all of them).</summary>
        public static List<PlacedObject> Carried(PlacedObject pallet, int deck = -1)
        {
            var list = new List<PlacedObject>();
            if (!LocalRect(pallet.transform, pallet.gameObject, out Rect footprint)) return list;
            float lo = pallet.transform.position.y + 0.05f, hi = float.MaxValue;
            int decks = DeckHeights(pallet.ItemId).Count;
            if (decks > 0 && deck >= 0)
            {
                lo = DeckY(pallet, deck) - 0.02f;
                if (deck + 1 < decks) hi = DeckY(pallet, deck + 1) - 0.02f;
            }
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == pallet) continue;
                Vector3 l = pallet.transform.InverseTransformPoint(o.transform.position);
                float y = o.transform.position.y;
                if (footprint.Contains(new Vector2(l.x, l.z)) && y > lo && y < hi) list.Add(o);
            }
            return list;
        }

        /// <summary>
        /// Where an item of this size goes on the pallet: on top of an identical stack under the point when it is under its limit,
        /// otherwise in the free spot nearest the point. <paramref name="ignore"/> is an object to leave out (the one being placed).
        /// </summary>
        public static bool FindSpot(PlacedObject pallet, string itemId, Vector2 size, Vector3 wantWorld, PlacedObject ignore,
                                    out Vector3 position, out int level, out string reason, int deck = 0, float height = 0f)
        {
            position = default;
            level = 1;
            reason = null;
            if (!LocalRect(pallet.transform, pallet.gameObject, out Rect deckRect)) { reason = "The pallet has not loaded yet."; return false; }
            float deckY = DeckY(pallet, deck);
            float room = Clearance(pallet, deck);   // how high things may go on this deck
            if (height > room + 0.01f) { reason = "It is too tall for this shelf."; return false; }
            Vector3 wl = pallet.transform.InverseTransformPoint(wantWorld);
            Vector2 want = new Vector2(wl.x, wl.z);

            // the columns already on it
            var cols = new List<List<PlacedObject>>();
            foreach (PlacedObject o in Carried(pallet, deck))
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
                    float itemH = height > 0f ? height : top.Height;   // the new one's own height: the whole stack (what is there plus this one) must fit under the shelf above
                    if (topY - deckY + itemH > room + 0.01f) { reason = "That stack is as high as it goes."; return false; }
                    position = new Vector3(top.transform.position.x, topY, top.transform.position.z);
                    level = top.Level + 1;
                    return true;
                }
            }

            // 2) the free spot nearest the point
            float w = size.x, d = size.y;
            if (w > deckRect.width + 0.01f || d > deckRect.height + 0.01f) { reason = "That does not fit on the pallet."; return false; }
            const float gap = 0.01f, step = 0.05f;
            bool found = false;
            Vector2 best = default;
            float bestDist = float.MaxValue;
            for (float x = deckRect.xMin + w * 0.5f; x <= deckRect.xMax - w * 0.5f + 0.001f; x += step)
                for (float z = deckRect.yMin + d * 0.5f; z <= deckRect.yMax - d * 0.5f + 0.001f; z += step)
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
            level = 0;   // it rests on a shelf, not on another item: level 0 like anything standing on a support (SettleColumns renumbers a stack from 0)
            return true;
        }

        private static Rect Union(Rect a, Rect b)
        {
            float x0 = Mathf.Min(a.xMin, b.xMin), x1 = Mathf.Max(a.xMax, b.xMax), z0 = Mathf.Min(a.yMin, b.yMin), z1 = Mathf.Max(a.yMax, b.yMax);
            return new Rect(x0, z0, x1 - x0, z1 - z0);
        }
    }
}
