using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Kitchen runs: floor cabinets and appliances (properties.run_snap) held near each other snap edge to edge, fronts and backs flush; held near a wall they back onto it
    /// and slide into a corner; and a gap of up to <see cref="MaxFillerM"/> left between the end of a run and a wall is closed with a filler strip (<see cref="KitchenRunFiller"/>).
    /// </summary>
    public static class KitchenRun
    {
        public const float MaxFillerM = 0.5f;       // a wider gap is left for the player to fill with a cabinet
        public const float MaxJoinFillM = 0.05f;    // the gap between two pieces that a strip closes
        public const float MinFillerM = 0.01f;      // a narrower one is not worth a strip
        private const float SnapRadiusM = 1.0f;     // the cursor this close to a snapped spot takes it
        private const float WallReachM = 0.7f;      // a wall this close to the cursor is backed onto
        private const float CornerSlideM = 0.12f;   // a side wall this close to a piece backed onto a wall: it slides flush into the corner
        private const float JoinGapM = 0.0f;        // between two pieces of a run: none, so the counters meet flush (a 2 cm filler piece covers the seam: KitchenRunFiller)
        private const float WallGapM = 0.0f;        // between a piece and the wall it is backed onto: none
        public const string StripName = "RunFiller";

        /// <summary>The L-shaped corner base cabinet (kitchen_corner_base_*): a 0.9 m square footprint with a notch, its long arm on one wall and its back on the other.</summary>
        public static bool IsCorner(string itemId) { return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("kitchen_corner_base"); }

        private const float CornerArmM = 0.60f;     // the width of each arm of the L (kitchen_models.corner_base)
        private const float CornerReachM = 1.4f;    // a second wall this close to the first, on either side: it is a corner

        /// <summary>
        /// Sets a corner cabinet in a corner of a room: the nearest wall is found, then a wall at right angles to it within <see cref="CornerReachM"/> on either side. The cabinet backs onto one of
        /// them, and its long arm (its +x side) lies along the other, flush to both. False when the cursor is not near a corner (the usual snap then applies).
        /// </summary>
        private static bool TryCorner(GameObject ghost, Vector3 hit, out Vector3 position, out float yawDeg, out string reason)
        {
            position = hit; yawDeg = 0f; reason = null;
            if (!NearestWall(hit + Vector3.up * 0.45f, WallReachM, out RaycastHit w1)) return false;
            Vector3 n1 = w1.normal; n1.y = 0f; n1.Normalize();
            Vector3 along = Vector3.Cross(Vector3.up, n1);
            Vector3 probe = new Vector3(w1.point.x, hit.y + 0.45f, w1.point.z) + n1 * 0.45f;
            RaycastHit best = default;
            float bestD = float.MaxValue;
            float sign = 0f;
            for (int sg = -1; sg <= 1; sg += 2)
            {
                if (WallRay(probe, along * sg, CornerReachM, ghost.transform, out RaycastHit h)
                    && Vector3.Dot(new Vector3(h.normal.x, 0f, h.normal.z).normalized, -along * sg) > 0.9f && h.distance < bestD)
                { best = h; bestD = h.distance; sign = sg; }
            }
            if (sign == 0f) return false;
            Vector3 backNormal, backPoint;
            bool mir = Mirrored(ghost.transform);                                                // a mirrored cabinet has its long arm on the other side (-x)
            if (mir ? sign < 0f : sign > 0f) { backNormal = n1; backPoint = w1.point; }         // the long arm (+x) is on the wall at +along: the back is on the first wall
            else { backNormal = new Vector3(best.normal.x, 0f, best.normal.z).normalized; backPoint = best.point; }   // the other way round: back onto the second, the first is at its +x side
            Quaternion rot = Quaternion.LookRotation(backNormal, Vector3.up);
            yawDeg = rot.eulerAngles.y;
            ghost.transform.rotation = rot;
            if (!BodyRect(ghost.transform, out Rect gr, out float y0, out float y1)) return false;
            Vector3 right = rot * Vector3.right * (mir ? -1f : 1f);                              // where the model's +x points in the world
            Vector3 centre = new Vector3(backPoint.x, hit.y, backPoint.z) + backNormal * (gr.height * 0.5f + WallGapM);
            bool slid = false;
            if (WallRay(centre + Vector3.up * 0.45f, right, 1.5f, ghost.transform, out RaycastHit side))
            {
                centre += right * (side.distance - gr.width * 0.5f - WallGapM);                  // the long arm flush to the second wall
                slid = true;
            }
            if (Time.unscaledTime >= s_nextLog)
            {
                s_nextLog = Time.unscaledTime + 1.5f;
                Debug.Log("[KitchenCorner] back " + backPoint.ToString("0.00") + " normal " + backNormal.ToString("0.00") + " sign " + sign + " rect x " + gr.xMin.ToString("0.00") + ".." + gr.xMax.ToString("0.00")
                          + " z " + gr.yMin.ToString("0.00") + ".." + gr.yMax.ToString("0.00") + (slid ? " side wall at " + side.distance.ToString("0.00") : " no side wall") + " yaw " + yawDeg.ToString("0"));
            }
            Vector3 pivot = centre - Off(ghost.transform, gr);
            position = new Vector3(pivot.x, hit.y, pivot.z);
            // only the L is solid: the arm along the second wall (+x side, full depth) and the strip across the back (full width, back 0.6 m); the notch (front left) is the inner corner
            Rect arm = new Rect(gr.xMax - CornerArmM, gr.yMin, CornerArmM, gr.height);
            Rect back = new Rect(gr.xMin, gr.yMin, gr.width, CornerArmM);
            if (!Blocked(ghost.transform, position, arm, y0, y1, out reason)) Blocked(ghost.transform, position, back, y0, y1, out reason);
            return true;
        }

        private const float FrontOverhangM = 0.025f;
        private static float s_nextLog;

        /// <summary>The first thing a ray meets that is not the ghost (the shadow in hand) or a filler strip: true when it is a wall.</summary>
        private static bool WallRay(Vector3 origin, Vector3 dir, float reach, Transform ghost, out RaycastHit wall)
        {
            wall = default;
            RaycastHit[] hits = Physics.RaycastAll(origin, dir, reach, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null || (ghost != null && h.collider.transform.IsChildOf(ghost)) || h.collider.name == StripName) continue;
                if (!IsWall(h)) return false;
                wall = h;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Free placement on a kitchen counter (a cooktop, a toaster, a mixer on a base cabinet, a work counter, an island): the item goes where the CURSOR is on the counter's surface (the cursor ray
        /// meets the plane of the counter top, so pointing at a counter's front face does not drag it to the edge), in the counter's own turn, and may span several counters side by side. It is valid
        /// when counter carries all of it (the corners and the middle are each over a counter top of this height), nothing else stands there and it is not too tall.
        /// </summary>
        public static bool PlanOnCounter(PlacedObject under, GameObject ghost, Ray cursor, Vector3 fallback, float itemHeight, out Vector3 position, out string reason)
        {
            reason = null;
            float deckY = PalletDeck.DeckY(under);
            Vector3 at = fallback;
            if (new Plane(Vector3.up, new Vector3(0f, deckY, 0f)).Raycast(cursor, out float t)) at = cursor.GetPoint(t);
            position = new Vector3(at.x, deckY, at.z);
            if (!BodyRect(ghost.transform, out Rect mr, out _, out _)) { reason = "Loading..."; return false; }
            Quaternion rot = ghost.transform.rotation;                         // the counter's own turn (set by the caller)
            float sx = Mirrored(ghost.transform) ? -1f : 1f;
            position -= Off(ghost.transform, mr);                              // the middle of the footprint under the cursor
            position.y = deckY;
            if (itemHeight > PalletDeck.TopLimit) { reason = "It is too tall to stand there."; return false; }
            // the footprint in the world: its corners, edge middles and middle
            var pts = new List<Vector3>();
            float xl = mr.xMin, xr = mr.xMax, zl = mr.yMin, zh = mr.yMax;
            foreach (float px in new[] { xl, (xl + xr) * 0.5f, xr })
                foreach (float pz in new[] { zl, (zl + zh) * 0.5f, zh })
                    pts.Add(position + rot * new Vector3(px * sx, 0f, pz));
            Bounds box = new Bounds(pts[0], Vector3.zero);
            foreach (Vector3 p in pts) box.Encapsulate(p);
            if (!AllCarried(pts, deckY))
            {
                // near the back, the front or the end of a counter (or a wall behind it): slid back onto the counter instead of refused, so the item stays where the cursor is as nearly as it can
                Vector3 toward = under.transform.position - position; toward.y = 0f;
                Vector3 step = toward.sqrMagnitude > 1e-6f ? toward.normalized * 0.01f : Vector3.zero;
                Vector3 moved = Vector3.zero;
                bool ok = false;
                for (int k = 0; k < 40 && step != Vector3.zero; k++)
                {
                    moved += step;
                    var shifted = new List<Vector3>(pts.Count);
                    foreach (Vector3 q in pts) shifted.Add(q + moved);
                    if (AllCarried(shifted, deckY)) { ok = true; break; }
                }
                if (!ok) { reason = "Put it where the counter carries all of it."; return false; }
                position += moved;
                for (int i = 0; i < pts.Count; i++) pts[i] += moved;
                box = new Bounds(pts[0], Vector3.zero);
                foreach (Vector3 p in pts) box.Encapsulate(p);
            }
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o == under || o.transform.position.y < deckY - 0.02f || o.transform.position.y > deckY + 1.2f) continue;
                Rect r = PlacedObject.ColumnRect(new List<PlacedObject> { o });
                if (r.xMin + 0.01f < box.max.x && r.xMax - 0.01f > box.min.x && r.yMin + 0.01f < box.max.z && r.yMax - 0.01f > box.min.z) { reason = "Something is in the way."; return false; }
            }
            return true;
        }

        /// <summary>A small kitchen item that goes on a counter (a cooktop, a toaster, a mixer): a kitchen item that is not a run piece, light, and low.</summary>
        public static bool CountertopItem(string itemId, float heightM)
        {
            AssetCatalogItem c = string.IsNullOrEmpty(itemId) ? null : HudBindings.GetCatalogItem(itemId);
            return c != null && c.category == "kitchen" && !c.run_snap && c.weight_kg <= 20f && heightM <= 0.6f;
        }

        /// <summary>
        /// The kitchen counter whose TOP the cursor ray meets (the ray against the plane of each counter top, inside its footprint): the nearest one along the ray. The ground point behind a counter
        /// (what the cursor finds, placed objects are looked through) is no guide: it is behind the counter, so a counter would only be found at its far edge.
        /// </summary>
        public static bool CounterUnderRay(Ray ray, out PlacedObject counter)
        {
            counter = null;
            float best = float.MaxValue;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsRun(o.ItemId) || !PalletDeck.IsPallet(o.ItemId) || PalletDeck.IsShelving(o.ItemId)) continue;
                if (!PalletDeck.LocalRect(o.transform, o.gameObject, out Rect deck)) continue;
                if (!new Plane(Vector3.up, new Vector3(0f, PalletDeck.DeckY(o), 0f)).Raycast(ray, out float t) || t >= best) continue;
                Vector3 l = o.transform.InverseTransformPoint(ray.GetPoint(t));
                if (!new Rect(deck.x - 0.03f, deck.y - 0.03f, deck.width + 0.06f, deck.height + 0.06f).Contains(new Vector2(l.x, l.z))) continue;
                best = t; counter = o;
            }
            if (counter != null) return true;
            // none under the cursor: the counter whose top the ray passes within half a metre of (the cursor on the wall behind the counter, or past its end): the item is slid back onto it
            float near = 0.5f;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsRun(o.ItemId) || !PalletDeck.IsPallet(o.ItemId) || PalletDeck.IsShelving(o.ItemId)) continue;
                if (!PalletDeck.LocalRect(o.transform, o.gameObject, out Rect deck)) continue;
                if (!new Plane(Vector3.up, new Vector3(0f, PalletDeck.DeckY(o), 0f)).Raycast(ray, out float t)) continue;
                Vector3 l = o.transform.InverseTransformPoint(ray.GetPoint(t));
                float dx = Mathf.Max(deck.xMin - l.x, 0f, l.x - deck.xMax), dz = Mathf.Max(deck.yMin - l.z, 0f, l.z - deck.yMax);
                float dist = Mathf.Sqrt(dx * dx + dz * dz);
                if (dist < near) { near = dist; counter = o; }
            }
            return counter != null;
        }

        private static bool AllCarried(List<Vector3> pts, float deckY)
        {
            foreach (Vector3 p in pts) if (!CounterCarries(p, deckY)) return false;
            return true;
        }

        /// <summary>True when the point is over the top of a kitchen counter (a run piece with a deck) at this height.</summary>
        private static bool CounterCarries(Vector3 world, float deckY)
        {
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsRun(o.ItemId) || !PalletDeck.IsPallet(o.ItemId) || PalletDeck.IsShelving(o.ItemId)) continue;
                if (Mathf.Abs(PalletDeck.DeckY(o) - deckY) > 0.04f) continue;
                if (!PalletDeck.LocalRect(o.transform, o.gameObject, out Rect deck)) continue;
                Vector3 l = o.transform.InverseTransformPoint(world);
                if (new Rect(deck.x - 0.01f, deck.y - 0.01f, deck.width + 0.02f, deck.height + 0.02f).Contains(new Vector2(l.x, l.z))) return true;
            }
            return false;
        }

        /// <summary>True when a transform is mirrored left to right (a negative x scale: T while placing).</summary>
        private static bool Mirrored(Transform t) { return t.lossyScale.x < 0f; }

        /// <summary>The world offset from a mirrored or plain model's pivot to the middle of a footprint measured in its own model coordinates (<see cref="BodyRect"/> gives those, mirror or not).</summary>
        private static Vector3 Off(Transform t, Rect r) { return t.rotation * new Vector3(Mirrored(t) ? -r.center.x : r.center.x, 0f, r.center.y); }

        public static bool IsRun(string itemId)
        {
            AssetCatalogItem c = string.IsNullOrEmpty(itemId) ? null : HudBindings.GetCatalogItem(itemId);
            return c != null && c.run_snap;
        }

        /// <summary>
        /// Where a run piece held at <paramref name="hit"/> goes: against the nearest run piece (backs flush, in the turn of that piece), else backed onto the nearest wall, else false
        /// (free placement). <paramref name="turns"/> are the quarter turns the player added with R on top of the snapped turn (a cabinet turned to face along a wall, a corner).
        /// The ghost is turned to match; <paramref name="reason"/> is set when the spot is taken.
        /// </summary>
        public static bool TrySnap(string heldId, GameObject ghost, Vector3 hit, int turns, out Vector3 position, out float yawDeg, out string reason)
        {
            position = hit; yawDeg = 0f; reason = null;
            if (ghost == null || !IsRun(heldId)) return false;
            Vector2 hit2 = new Vector2(hit.x, hit.z);
            bool odd = (turns & 1) != 0;

            // 0) a corner cabinet goes INTO a corner of the room, its two long sides on the two walls (it is an L, not a box). It picks its own turn; once the player has turned it with R
            //    (turns != 0) the turn is theirs: it snaps to a neighbour or a wall like any other piece, in the turn they chose (four turns bring the corner lock back).
            if (IsCorner(heldId) && turns == 0 && TryCorner(ghost, hit, out position, out yawDeg, out reason)) return true;

            // 1) beside another piece of a run
            float best = SnapRadiusM * SnapRadiusM;
            bool found = false;
            Vector3 bestPos = default;
            float bestYaw = 0f;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || !IsRun(o.ItemId) || o.Level != 0) continue;
                if (Vector2.SqrMagnitude(new Vector2(o.transform.position.x, o.transform.position.z) - hit2) > 9f) continue;
                if (!BodyRect(o.transform, out Rect nr, out _, out _)) continue;
                float yaw = o.transform.eulerAngles.y + 90f * turns;
                ghost.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                if (!BodyRect(ghost.transform, out Rect mr, out _, out _)) return false;   // the ghost's model is still loading
                float eT = odd ? mr.height : mr.width, eN = odd ? mr.width : mr.height;      // its size along and across the piece it joins
                for (int s = -1; s <= 1; s += 2)
                {
                    float cx = nr.center.x + s * (nr.width * 0.5f + eT * 0.5f + JoinGapM);
                    float cz = nr.yMin + eN * 0.5f;                                              // backs flush
                    Vector3 centre = o.transform.TransformPoint(new Vector3(cx, 0f, cz));
                    Vector3 pivot = centre - Off(ghost.transform, mr);
                    float d = Vector2.SqrMagnitude(new Vector2(pivot.x, pivot.z) - hit2);
                    if (d >= best) continue;
                    best = d; bestPos = new Vector3(pivot.x, o.transform.position.y, pivot.z); bestYaw = yaw; found = true;
                }
                // a CORNER cabinet's long arm runs to the front along the side wall: the next cabinet continues along THAT wall, in front of the arm's end, turned a quarter turn (its back on the side wall)
                if (IsCorner(o.ItemId) && !IsCorner(heldId))
                {
                    float armYaw = o.transform.eulerAngles.y + (Mirrored(o.transform) ? 90f : -90f);
                    ghost.transform.rotation = Quaternion.Euler(0f, armYaw, 0f);
                    if (BodyRect(ghost.transform, out Rect ar, out _, out _))
                    {
                        Vector3 armCentre = o.transform.TransformPoint(new Vector3(nr.xMax - ar.height * 0.5f, 0f, nr.yMax + JoinGapM + ar.width * 0.5f));
                        Vector3 armPivot = armCentre - Off(ghost.transform, ar);
                        float da = Vector2.SqrMagnitude(new Vector2(armPivot.x, armPivot.z) - hit2);
                        if (da < best) { best = da; bestPos = new Vector3(armPivot.x, o.transform.position.y, armPivot.z); bestYaw = armYaw; found = true; }
                    }
                }
            }
            if (found)
            {
                ghost.transform.rotation = Quaternion.Euler(0f, bestYaw, 0f);
                position = bestPos; yawDeg = bestYaw;
                if (!BodyRect(ghost.transform, out Rect r, out float y0, out float y1)) return false;
                Blocked(ghost.transform, bestPos, r, y0, y1, out reason);
                return true;
            }

            // 2) backed onto a wall
            if (!NearestWall(hit + Vector3.up * 0.45f, WallReachM, out RaycastHit wall)) return false;
            Vector3 n = wall.normal; n.y = 0f; n.Normalize();
            float wallYaw = Mathf.Atan2(n.x, n.z) * Mathf.Rad2Deg + 90f * turns;
            Quaternion rot = Quaternion.Euler(0f, wallYaw, 0f);
            ghost.transform.rotation = rot;
            if (!BodyRect(ghost.transform, out Rect gr, out _, out _)) return false;
            float gT = odd ? gr.height : gr.width, gN = odd ? gr.width : gr.height;          // its size along the wall and out from it
            Vector3 centre2 = new Vector3(wall.point.x, hit.y, wall.point.z) + n * (gN * 0.5f + WallGapM);   // the middle of the footprint, its wall side on the wall
            Vector3 along = Vector3.Cross(Vector3.up, n);
            for (int s = -1; s <= 1; s += 2)                                                  // a side wall just beside it: slide flush into the corner
            {
                float reach = gT * 0.5f + CornerSlideM;
                if (Physics.Raycast(centre2 + Vector3.up * 0.45f, along * s, out RaycastHit side, reach, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore) && IsWall(side))
                { centre2 += along * s * (side.distance - gT * 0.5f - WallGapM); break; }
            }
            Vector3 pivot2 = centre2 - Off(ghost.transform, gr);
            position = new Vector3(pivot2.x, hit.y, pivot2.z); yawDeg = wallYaw;
            Blocked(ghost.transform, position, gr, 0f, 0f, out reason);
            return true;
        }

        /// <summary>The footprint of a model in the local space of <paramref name="frame"/> (the filler strips are not part of it) and its lowest and highest points above the frame's origin.</summary>
        public static bool BodyRect(Transform frame, out Rect rect, out float yMin, out float yMax)
        {
            rect = default; yMin = 0f; yMax = 0f;
            bool any = false;
            float x0 = 0f, x1 = 0f, z0 = 0f, z1 = 0f;
            foreach (MeshFilter mf in frame.GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name == StripName) continue;
                Bounds mb = mf.sharedMesh.bounds;
                Vector3 e = mb.extents, c = mb.center;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z);
                    Vector3 l = frame.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { x0 = x1 = l.x; z0 = z1 = l.z; yMin = yMax = l.y; any = true; }
                    else { x0 = Mathf.Min(x0, l.x); x1 = Mathf.Max(x1, l.x); z0 = Mathf.Min(z0, l.z); z1 = Mathf.Max(z1, l.z); yMin = Mathf.Min(yMin, l.y); yMax = Mathf.Max(yMax, l.y); }
                }
            }
            if (any) rect = new Rect(x0, z0, x1 - x0, z1 - z0);
            return any;
        }

        /// <summary>True when the collider belongs to a building (a wall, not a floor or a roof).</summary>
        public static bool IsWall(RaycastHit h)
        {
            return h.collider != null && Mathf.Abs(h.normal.y) < 0.3f && h.collider.GetComponentInParent<ConstructionSite>() != null;
        }

        /// <summary>The nearest wall of a building within reach of a point, looking in the four horizontal directions of the nearest building.</summary>
        private static bool NearestWall(Vector3 from, float reach, out RaycastHit wall)
        {
            wall = default;
            float best = float.MaxValue;
            bool any = false;
            for (int k = 0; k < 8; k++)
            {
                Vector3 dir = Quaternion.Euler(0f, k * 45f, 0f) * Vector3.forward;
                if (!Physics.Raycast(from, dir, out RaycastHit h, reach, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore) || !IsWall(h)) continue;
                // only a wall that faces the point squarely (a ray along a diagonal would meet a wall at an angle)
                if (Vector3.Dot(-dir, new Vector3(h.normal.x, 0f, h.normal.z).normalized) < 0.92f) continue;
                if (h.distance < best) { best = h.distance; wall = h; any = true; }
            }
            return any;
        }

        /// <summary>True (with a reason) when a wall or another piece is inside the footprint at that spot.</summary>
        private static bool Blocked(Transform ghostFrame, Vector3 pivot, Rect r, float y0, float y1, out string reason)
        {
            reason = null;
            Quaternion rot = ghostFrame.rotation;
            Vector3 centre = pivot + Off(ghostFrame, r);
            Vector3 half = new Vector3(r.width * 0.5f - 0.02f, 0.3f, r.height * 0.5f - 0.02f);
            if (half.x <= 0f || half.z <= 0f) return false;
            Vector3 mid = new Vector3(centre.x, pivot.y + 0.5f, centre.z);
            foreach (Collider c in Physics.OverlapBox(mid, half, rot, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
            {
                if (c.transform.IsChildOf(ghostFrame)) continue;
                if (c.name == StripName) continue;   // a filler strip gives way to the piece that takes its place
                if (c.GetComponentInParent<ConstructionSite>() != null) { reason = "The wall is in the way."; return true; }
                if (c.GetComponentInParent<PlacedObject>() != null) { reason = "Something is in the way."; return true; }
            }
            return false;
        }
    }

    /// <summary>
    /// On a placed run piece: once a second it looks along its two ends and, where a wall is within <see cref="KitchenRun.MaxFillerM"/> and nothing else stands in the gap,
    /// closes it with a filler made like the cabinets (a child object, not saved: it comes back from the positions on every load, and goes with the piece): a recessed toe kick
    /// at the bottom, the carcass above it up to the counter, and a strip of the counter on top, the full depth with its front overhang.
    /// </summary>
    public sealed class KitchenRunFiller : MonoBehaviour
    {
        private const float FrontOverhangM = 0.025f;   // the countertop stands this far out past the doors (kitchen_models.countertop)
        private const float SeamM = 0.02f;             // the filler piece over the joint of two touching cabinets: this wide
        private const float ToeM = 0.10f;              // the toe kick: its height ...
        private const float ToeSetbackM = 0.07f;       // ... and how far it is set back from the door fronts (kitchen_models.cabinet_carcass)
        private const float CounterM = 0.04f;          // a counter's thickness, when the model's own could not be found

        private PlacedObject _placed;
        private float _next;
        private readonly GameObject[] _strip = new GameObject[2];
        private readonly GameObject[] _kick = new GameObject[2];
        private readonly GameObject[] _top = new GameObject[2];
        private readonly float[] _gap = new float[2];
        private Material _body, _counter, _kickMat;
        private float _counterT;
        private float _cz0, _cz1, _bz0, _bz1;   // local z (depth) of the countertop and of the carcass: the strips follow THEM, not the handles and knobs that stand out of the front
        private bool _scanned;

        public static void AttachIfRun(PlacedObject placed)
        {
            if (placed == null || !KitchenRun.IsRun(placed.ItemId) || placed.GetComponent<KitchenRunFiller>() != null) return;
            KitchenRunFiller f = placed.gameObject.AddComponent<KitchenRunFiller>();
            f._placed = placed;
            f._next = Time.time + Random.Range(0.4f, 1.4f);
        }

        private void Update()
        {
            if (Time.time < _next) return;
            _next = Time.time + 1f;
            Refresh();
        }

        private void Refresh()
        {
            if (!KitchenRun.BodyRect(transform, out Rect r, out float y0, out float y1)) return;   // the model has not loaded
            if (!_scanned) { Scan(); _scanned = true; }
            // a counter piece's strips stop at the counter top (the sink's faucet and the like stand higher: the strip must not)
            if (_placed != null && PalletDeck.IsPallet(_placed.ItemId) && !PalletDeck.IsShelving(_placed.ItemId))
            {
                float deckLocal = PalletDeck.DeckY(_placed) - transform.position.y;
                if (deckLocal > 0.5f && deckLocal < y1) y1 = deckLocal;
            }
            float h2 = y1 - y0;
            // a counter piece (a base cabinet, a sink cabinet): the model's own counter, else a standard one on anything that is a counter's height
            float counterT = _counter != null && _counterT > 0.005f && _counterT < h2 ? _counterT : (h2 > 0.85f && h2 < 1.05f ? CounterM : 0f);
            bool counter = counterT > 0f;
            Material counterMat = _counter != null ? _counter : _body;
            for (int i = 0; i < 2; i++)
            {
                int s = i == 0 ? -1 : 1;
                float edge = s > 0 ? r.xMax : r.xMin;
                Vector3 origin = transform.TransformPoint(new Vector3(edge - s * 0.01f, 0.45f, r.center.y));
                float gap = 0f;
                bool neighbour = false, seam = false;
                RaycastHit[] hits = Physics.RaycastAll(origin, transform.TransformVector(new Vector3(s, 0f, 0f)).normalized, 0.01f + KitchenRun.MaxFillerM + 0.02f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
                System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
                foreach (RaycastHit h in hits)
                {
                    if (h.collider == null || h.collider.transform.IsChildOf(transform)) continue;   // its own body and strips
                    if (KitchenRun.IsWall(h)) gap = h.distance - 0.01f;                                // the first thing in the way is a wall; anything else means no strip
                    else
                    {
                        // another piece of the run a hand's width away: ONE of the two (the older) fills the gap between them with a strip
                        PlacedObject other = h.collider.GetComponentInParent<PlacedObject>();
                        if (other != null && other != _placed && h.collider.name != KitchenRun.StripName && KitchenRun.IsRun(other.ItemId) && Earlier(transform.position, other.transform.position)
                            && Vector3.Dot(transform.forward, other.transform.forward) > 0.98f && !KitchenRun.IsCorner(other.ItemId) && !KitchenRun.IsCorner(_placed.ItemId))   // side by side, facing the same way: not round a corner cabinet
                        {
                            gap = h.distance - 0.01f;
                            if (gap <= 0.003f) { seam = true; gap = 0f; }                                 // touching: a filler piece covers the seam
                            else { neighbour = gap <= KitchenRun.MaxJoinFillM; if (!neighbour) gap = 0f; }
                        }
                    }
                    break;
                }
                if (gap < KitchenRun.MinFillerM || gap > KitchenRun.MaxFillerM) gap = 0f;
                if (seam) gap = SeamM;
                gap = Mathf.Round(gap * 1000f) / 1000f;
                if (Mathf.Approximately(gap, _gap[i]) && (gap <= 0f) == (_strip[i] == null) && (_top[i] != null) == (gap > 0f && counter)) continue;
                _gap[i] = gap;
                if (gap <= 0f)
                {
                    Destroy(_strip[i]); Destroy(_kick[i]); Destroy(_top[i]);
                    _strip[i] = _kick[i] = _top[i] = null;
                    continue;
                }
                float w = seam ? SeamM : gap + (neighbour ? 0.002f : 0.005f);   // a hair into the wall (or the next cabinet), so no light shows between
                float cx = seam ? edge : edge + s * w * 0.5f;                  // a seam piece is centred on the joint: 1 cm into each cabinet
                // the carcass runs from the back of the piece to the door fronts; the counter overhangs them at the front
                float bodyZ0, bodyZ1, topZ0, topZ1;
                if (_counter != null && _cz1 > _cz0) { topZ0 = bodyZ0 = _cz0; topZ1 = _cz1; bodyZ1 = _cz1 - FrontOverhangM; }   // the model's own counter: its depth, the doors 2.5 cm behind its front edge
                else if (_bz1 > _bz0) { topZ0 = bodyZ0 = _bz0; topZ1 = bodyZ1 = _bz1; }                                       // no counter part: the carcass's own depth
                else { topZ0 = bodyZ0 = r.yMin; topZ1 = r.yMax; bodyZ1 = r.yMax - FrontOverhangM; }
                float bodyDepth = Mathf.Max(0.05f, bodyZ1 - bodyZ0);
                float bodyZ = (bodyZ0 + bodyZ1) * 0.5f;
                float bodyTop = y1 - counterT;
                bool toe = bodyTop - y0 > ToeM + 0.25f;   // a low piece has no kick
                float bodyBottom = y0 + (toe ? ToeM : 0f);
                if (_strip[i] == null) _strip[i] = MakeStrip(_body, true);
                _strip[i].transform.localPosition = new Vector3(cx, (bodyBottom + bodyTop) * 0.5f, bodyZ);
                _strip[i].transform.localScale = new Vector3(w, bodyTop - bodyBottom, bodyDepth);
                _strip[i].transform.localRotation = Quaternion.identity;
                if (toe)
                {
                    float kickDepth = Mathf.Max(0.05f, bodyDepth - ToeSetbackM);      // set back from the door fronts, flush with the back
                    if (_kick[i] == null) _kick[i] = MakeStrip(_kickMat != null ? _kickMat : _body, false);
                    _kick[i].transform.localPosition = new Vector3(cx, y0 + ToeM * 0.5f, bodyZ0 + kickDepth * 0.5f);
                    _kick[i].transform.localScale = new Vector3(w, ToeM, kickDepth);
                    _kick[i].transform.localRotation = Quaternion.identity;
                }
                else if (_kick[i] != null) { Destroy(_kick[i]); _kick[i] = null; }
                if (counter)
                {
                    if (_top[i] == null) _top[i] = MakeStrip(counterMat, false);
                    _top[i].transform.localPosition = new Vector3(cx, y1 - counterT * 0.5f - (seam ? 0.0003f : 0f), (topZ0 + topZ1) * 0.5f);   // (a seam piece a hair low, so it never fights the counters' own top)
                    _top[i].transform.localScale = new Vector3(w, counterT, Mathf.Max(0.05f, topZ1 - topZ0));
                    _top[i].transform.localRotation = Quaternion.identity;
                }
                else if (_top[i] != null) { Destroy(_top[i]); _top[i] = null; }
            }
        }

        /// <summary>One of two neighbours: the one lower along x (then z), so exactly one of a pair builds the strip between them.</summary>
        private static bool Earlier(Vector3 a, Vector3 b) { return a.x < b.x - 1e-4f || (Mathf.Abs(a.x - b.x) <= 1e-4f && a.z < b.z); }

        private GameObject MakeStrip(Material m, bool collider)
        {
            GameObject g = GameObject.CreatePrimitive(PrimitiveType.Cube);   // (the body strip's box collider keeps it hoverable: the cursor reads the piece it belongs to)
            g.name = KitchenRun.StripName;
            g.transform.SetParent(transform, false);
            if (!collider) Destroy(g.GetComponent<Collider>());
            if (m != null) g.GetComponent<Renderer>().sharedMaterial = m;
            return g;
        }

        /// <summary>
        /// The materials of the piece, found by their GEOMETRY (a model with several materials is one mesh with a part per material): the BODY is the biggest part (the carcass); the COUNTER is a thin
        /// part that makes the top of the piece (a countertop, 2 to 7 cm thick, as wide as the piece). A piece without a countertop (a refrigerator, a range) has none. The kick is the body, darker.
        /// </summary>
        private void Scan()
        {
            float top = float.MinValue;
            foreach (Renderer r in GetComponentsInChildren<Renderer>()) if (r.name != KitchenRun.StripName) top = Mathf.Max(top, r.bounds.max.y);
            if (_placed != null && PalletDeck.IsPallet(_placed.ItemId) && !PalletDeck.IsShelving(_placed.ItemId)) top = Mathf.Min(top, PalletDeck.DeckY(_placed));   // the counter's top, not the tap above it
            float bestVol = 0f, bestArea = 0f;
            foreach (Renderer r in GetComponentsInChildren<Renderer>())
            {
                if (r.name == KitchenRun.StripName) continue;
                Mesh mesh = r is MeshRenderer ? r.GetComponent<MeshFilter>()?.sharedMesh : null;
                Material[] mats = r.sharedMaterials;
                if (mesh == null)
                {
                    Vector3 s0 = r.bounds.size;
                    if (mats.Length > 0 && mats[0] != null && s0.x * s0.y * s0.z > bestVol) { bestVol = s0.x * s0.y * s0.z; _body = mats[0]; _bz0 = transform.InverseTransformPoint(r.bounds.center).z - s0.z * 0.5f; _bz1 = _bz0 + s0.z; }
                    continue;
                }
                for (int k = 0; k < mesh.subMeshCount && k < mats.Length; k++)
                {
                    if (mats[k] == null) continue;
                    Bounds mb = mesh.GetSubMesh(k).bounds;
                    Bounds wb = default;
                    float lz0 = 0f, lz1 = 0f;
                    for (int c = 0; c < 8; c++)
                    {
                        Vector3 corner = mb.center + Vector3.Scale(mb.extents, new Vector3((c & 1) == 0 ? -1 : 1, (c & 2) == 0 ? -1 : 1, (c & 4) == 0 ? -1 : 1));
                        Vector3 w = r.transform.TransformPoint(corner);
                        float lz = transform.InverseTransformPoint(w).z;
                        if (c == 0) { wb = new Bounds(w, Vector3.zero); lz0 = lz1 = lz; } else { wb.Encapsulate(w); lz0 = Mathf.Min(lz0, lz); lz1 = Mathf.Max(lz1, lz); }
                    }
                    float vol = wb.size.x * wb.size.y * wb.size.z, area = wb.size.x * wb.size.z;
                    if (vol > bestVol) { bestVol = vol; _body = mats[k]; _bz0 = lz0; _bz1 = lz1; }
                    if (wb.size.y >= 0.02f && wb.size.y <= 0.07f && wb.max.y >= top - 0.01f && area > bestArea) { bestArea = area; _counter = mats[k]; _counterT = wb.size.y; _cz0 = lz0; _cz1 = lz1; }
                }
            }
            if (_body == null) _body = _counter;
            if (_body != null)
            {
                _kickMat = new Material(_body) { name = "FillerKick" };   // the toe kick: the carcass finish, darker (it sits in shadow under the doors)
                Color c0 = _kickMat.HasProperty("_BaseColor") ? _kickMat.GetColor("_BaseColor") : (_kickMat.HasProperty("baseColorFactor") ? _kickMat.GetColor("baseColorFactor") : Color.gray);
                Color dark = new Color(c0.r * 0.35f, c0.g * 0.35f, c0.b * 0.35f, 1f);
                if (_kickMat.HasProperty("_BaseColor")) _kickMat.SetColor("_BaseColor", dark);
                if (_kickMat.HasProperty("baseColorFactor")) _kickMat.SetColor("baseColorFactor", dark);
                if (_kickMat.HasProperty("_BaseMap")) _kickMat.SetTexture("_BaseMap", null);
                if (_kickMat.HasProperty("baseColorTexture")) _kickMat.SetTexture("baseColorTexture", null);
            }
        }

        private void OnDestroy() { if (_kickMat != null) Destroy(_kickMat); }
    }
}
