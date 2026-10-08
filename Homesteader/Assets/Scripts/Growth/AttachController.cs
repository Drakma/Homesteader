using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Growth
{
    /// <summary>
    /// Mounting things on a finished building: a breaker box or a light with properties.attach_surface in the active slot. The first left click
    /// brings out a translucent preview that follows the cursor over the walls (a wall item sits flat on the wall under the cursor, outside or
    /// inside as its attach_side says) or the ceiling (a ceiling light hangs from the ceiling over the floor under the cursor); blue is valid, red is
    /// not. A second left click or Enter mounts it, Esc or walking away puts it back, R turns a ceiling light. A right click takes a mounted one down
    /// (AttachedObject.TryPickUpAtRay). Bootstraps itself; docs/ATTACHED_ITEMS.md.
    /// </summary>
    public sealed class AttachController : MonoBehaviour
    {
        private static readonly Color ValidTint = new Color(0.55f, 0.8f, 1f);
        private static readonly Color InvalidTint = new Color(1f, 0.35f, 0.3f);
        private const float GhostAlpha = 0.5f;
        private const float Reach = 3.5f;          // metres on the ground from the player to what is mounted
        private const float Snap = 0.05f;
        private const float RoofReach = 6f;       // a roof item is put up from the GROUND (there are no ladders): the player has to be this close to the building
        private const float CurtainAboveWindowM = 0.10f;   // a curtain or a drape hangs with its top this far above the window it covers
        private const float UpperBottomM = 0.92f + 0.437f + 0.02f;   // every wall cabinet hangs with its bottom 2 cm above the tallest counter appliance (the grain mill, 0.437 m) standing on a counter (0.92 m)
        private const float MinApart = 0.3f;       // two mounted things are never closer than this

        private GameObject _ghost;
        private string _ghostId;
        private Bounds _local;                     // the model's bounds in its own space (back plane z = 0 and sticking out towards +z, bottom y = 0 for a wall item; top y = height for a ceiling one)
        private bool _placing;
        private string _placingId;
        private int _startFrame;
        private Vector3 _startPed;
        private int _turn;                         // quarter turns of a ceiling item

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<AttachController>() != null) return;
            var go = new GameObject("AttachController");
            DontDestroyOnLoad(go);
            go.AddComponent<AttachController>();
        }

        private struct Plan
        {
            public bool Valid;
            public string Reason;
            public ConstructionSite Site;
            public Vector3 Position;
            public float UpperBottom;      // a wall cabinet: the world y its bottom must be at (NaN for anything else)
            public Quaternion Rotation;
            public float Thickness;        // a through-the-wall item: how thick the wall is there
            public Vector3 GuideFrom;      // a ceiling item: the floor spot the cursor is on (a line rises from it to the item)
            public bool HasGuide;
        }

        private void Update()
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null || HudBindings.KeyboardCaptured) { HideGhost(); return; }

            bool rotate = Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PlaceRotate);
            if (rotate && !_placing && !hud.IsPointerOverUI(Pointer()) && TurnMounted(GameCamera(), Pointer())) return;   // aims a thing that is already up on a roof
            string held = HeldId();
            // a thing that stands on the ground but may ALSO go up on a roof (a dish, a yagi, an access point: properties.roof_mount): this takes over only while the cursor is on a roof
            bool roofOption = !string.IsNullOrEmpty(held) && ItemRegistry.TryGet(held, out ItemRegistry.ItemInfo ro) && string.IsNullOrEmpty(ro.AttachSurface) && RoofMount(held);
            if (string.IsNullOrEmpty(held) || !ItemRegistry.TryGet(held, out ItemRegistry.ItemInfo info) || (string.IsNullOrEmpty(info.AttachSurface) && !roofOption) || info.Prefab == null)
            {
                _placing = false;
                HideGhost();
                return;
            }
            // STANDS on the roof, upright, and turns freely: a roof_mount item, whether it also goes on the ground (no attach_surface) or is a roof item only (attach_surface roof).
            // (Without this a yagi whose manifest says attach_surface roof was laid on the slope like a solar rack, which only turns on a flat roof, a quarter turn at a time.)
            bool upright = roofOption || (info.AttachSurface == "roof" && RoofMount(held));
            if (_placing && held != _placingId) _placing = false;
            if (_placing && Escape()) _placing = false;
            var ped = PedController.Current;
            if (_placing && !roofOption && ped != null && (ped.transform.position - _startPed).sqrMagnitude > 0.0025f) _placing = false;   // walked away (a roof preview follows the cursor instead: it ends when the cursor leaves the roof)

            Camera cam = GameCamera();
            Vector2 pointer = Pointer();
            if (!_placing)
            {
                HideGhost();
                // a dish, yagi or access point: its roof preview comes up as soon as the cursor is on a roof (no first click: the ground preview has just stepped aside)
                bool hoverRoof = roofOption && cam != null && !hud.IsPointerOverUI(pointer) && OverRoof(cam, pointer);
                if (hoverRoof && s_roofLog != held) { s_roofLog = held; Dbg.Log("[Roof] " + held + " over a roof: the roof preview takes it (R turns it " + RoofTurnDeg + " degrees)"); }
                if (cam != null && !hud.IsPointerOverUI(pointer) && (roofOption ? hoverRoof : LeftClicked()))
                {
                    _placing = true;
                    _placingId = held;
                    _startFrame = roofOption ? -1 : Time.frameCount;
                    _startPed = ped != null ? ped.transform.position : Vector3.zero;
                }
                if (!_placing) return;
            }
            if (cam == null || hud.IsPointerOverUI(pointer)) { HideGhost(); return; }
            if (info.AttachSurface == "chimney") { UpdateChimney(held, cam, pointer, ped); return; }   // a chimney kit: its own preview and rules (Chimney.cs)
            if (!EnsureGhost(held, info)) return;

            if (rotate && upright) Dbg.Log("[Roof] R with " + held + " over a roof: turn " + _turn + " -> next");
            if ((info.AttachSurface == "ceiling" || info.AttachSurface == "roof" || upright) && rotate)
                _turn += upright && UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.shiftKey.isPressed ? -1 : 1;

            Plan plan = upright ? PlanRoofUpright(cam, pointer, ped) : info.AttachSurface == "ceiling" ? PlanCeiling(cam, pointer, info, ped) : info.AttachSurface == "roof" ? PlanRoof(cam, pointer, info, ped) : PlanWall(cam, pointer, info, ped);
            if (plan.Site == null && plan.Reason == null) { if (roofOption) _placing = false; HideGhost(); return; }   // the cursor is not over a building (a ground item off the roof: back to placing it on the ground)
            _ghost.SetActive(true);
            _ghost.transform.SetPositionAndRotation(plan.Position, plan.Rotation);
            if (upright) Net.Preview(held, plan.Position, plan.Rotation * Vector3.forward);   // a yagi: its signal shows while it is aimed
            if (info.AttachThrough) AttachedObject.ApplyThrough(_ghost, plan.Thickness > 0.02f ? plan.Thickness : AttachedObject.DefaultWall);   // the other side's plate shows in the preview too
            GhostVisual.Apply(_ghost, plan.Valid ? ValidTint : InvalidTint, GhostAlpha);
            ShowGuide(plan);

            bool confirm = Enter() || (LeftClicked() && Time.frameCount != _startFrame);
            if (!confirm) return;
            if (!plan.Valid) { ToastNotificationSystem.ShowWarning("Can't mount it here", plan.Reason); return; }
            Mount(held, info, plan);
            _placing = false;
            HideGhost();
        }

        // ------------------------------------------------------------------ where it goes

        private static readonly string[] NotWall = { "Door", "Window", "Frame", "Framing", "Trim", "Roof", "Foundation", "Porch", "Stud", "Joist", "Rafter", "Beam", "Post", "Sill", "Header", "Casing" };

        /// <summary>True unless the collider is part of a door, a window, framing, trim, a beam, the foundation or the roof: wall items go on the wall surface itself (every layer of a wall counts, whatever it is called).</summary>
        internal static bool IsWallPart(Collider c, ConstructionSite site)
        {
            Transform stop = site.VisualRoot != null ? site.VisualRoot : site.transform;   // (the model's own name says nothing about the part)
            for (Transform t = c.transform; t != null && t != stop && t != site.transform; t = t.parent)
                foreach (string bad in NotWall)
                    if (t.name.StartsWith(bad, System.StringComparison.OrdinalIgnoreCase)) return false;
            return true;
        }

        private const int HiddenLayer = 2;   // Ignore Raycast: where the cutaway puts the walls it hides

        private Plan PlanWall(Camera cam, Vector2 pointer, ItemRegistry.ItemInfo info, PedController ped)
        {
            var plan = new Plan();
            Ray ray = cam.ScreenPointToRay(pointer);
            // every layer, so the walls the cutaway hides (on Ignore Raycast) are seen and skipped: the cursor passes through them to the walls behind
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                bool hidden = h.collider.gameObject.layer == HiddenLayer;
                if (hidden) continue;   // anything the cutaway hides (a wall, a roof): looked through, so the cursor reaches the walls the player can see
                if (site == null) return plan;   // the first thing hit is not a building: nothing to mount on
                plan.Site = site;
                // Wall items go on WALLS only: not on a door, its frame or trim, a window and its frame, the foundation, the roof or any other framing
                if (!IsWallPart(h.collider, site)) { plan.Reason = "Mount it on a wall, not on framing."; return plan; }
                // A wall is made of layers (cladding, sheathing, logs, siding boards, the inside finish) and the cursor ray may reach any of them, with
                // normals that tilt on a log or a board edge. So the wall plane comes from the BUILDING: the face of its footprint nearest the point
                // (a building's walls are square to it), the side from the way the surface that was hit faces. The surface to sit on is then found by
                // looking at the wall straight on, from outside (or inside) at the cursor's spot: the first thing met there is the outermost layer.
                Vector3 hp = h.point;
                Quaternion siteRot = site.transform.rotation;
                Vector3 lp = Quaternion.Inverse(siteRot) * (hp - site.transform.position);
                Rect wr = site.WingRectNear(lp.x, lp.z);                          // the walls' rectangle (of the wing the cursor is in) (a porch is outside it, though inside the footprint)
                float dLeft = Mathf.Abs(lp.x - wr.xMin), dRight = Mathf.Abs(wr.xMax - lp.x), dBack = Mathf.Abs(lp.z - wr.yMin), dFront = Mathf.Abs(wr.yMax - lp.z);
                float edgeDist = Mathf.Min(Mathf.Min(dLeft, dRight), Mathf.Min(dBack, dFront));
                Vector3 nLocal = edgeDist == dLeft ? Vector3.left : edgeDist == dRight ? Vector3.right : edgeDist == dBack ? Vector3.back : Vector3.forward;
                Vector3 nOut = siteRot * nLocal;
                float facing = Vector3.Dot(h.normal, nOut);
                bool inRect = lp.x > wr.xMin + 0.02f && lp.x < wr.xMax - 0.02f && lp.z > wr.yMin + 0.02f && lp.z < wr.yMax - 0.02f;
                bool outerSurface = Mathf.Abs(facing) > 0.2f ? facing > 0f : !inRect || edgeDist < 0.06f;
                Vector3 n = outerSurface ? nOut : -nOut;                           // out of the wall, on the side that was aimed at
                if (inRect && edgeDist > 0.5f)
                {
                    // an INTERIOR wall (a partition between rooms, with its door casings): it does not face the nearest outside wall, it faces the way its own surface does.
                    // Square to the building, from the surface that was hit (the outside-wall rule above turned a sconce on a partition sideways).
                    Vector3 hn = Quaternion.Inverse(siteRot) * h.normal;
                    hn.y = 0f;
                    if (hn.sqrMagnitude < 0.25f) { plan.Reason = "Mount it on a wall, not on framing."; return plan; }
                    Vector3 nl2 = Mathf.Abs(hn.x) > Mathf.Abs(hn.z) ? new Vector3(Mathf.Sign(hn.x), 0f, 0f) : new Vector3(0f, 0f, Mathf.Sign(hn.z));
                    n = siteRot * nl2;
                }

                // along the wall and up it in small steps, flat on the wall
                Vector3 p = hp;
                p.x = Mathf.Round(p.x / Snap) * Snap;
                p.y = Mathf.Round(p.y / Snap) * Snap;
                p.z = Mathf.Round(p.z / Snap) * Snap;
                p -= n * Vector3.Dot(p - hp, n);                                   // the rounding moved it along the normal too: back onto the plane
                Collider surface = h.collider;
                RaycastHit[] probe = RaycastBothFaces(p + n * 0.6f, -n, 1.3f);   // (hidden walls too: the inner face of a cut-away wall)
                System.Array.Sort(probe, (x, y) => x.distance.CompareTo(y.distance));
                foreach (RaycastHit ph in probe)
                {
                    if (ph.collider.GetComponentInParent<ConstructionSite>() != site) continue;
                    if (ph.collider.GetComponentInParent<AttachedObject>() != null) continue;
                    if (!IsWallPart(ph.collider, site)) continue;                  // trim and framing in front of the wall are not the surface
                    p = new Vector3(ph.point.x, p.y, ph.point.z) ;
                    surface = ph.collider;
                    break;
                }
                Vector3 tangent = Vector3.Cross(Vector3.up, n);
                float upperBottom = float.NaN;
                if (IsUpper(info)) { upperBottom = FloorBelow(site, p, n) + UpperBottomM; p.y = upperBottom + _local.size.y * 0.5f; p = SnapUpper(site, p, n, tangent); }   // wall cabinets hang at one standard height and snap to each other
                bool hangs = info.Id != null && (info.Id.StartsWith("decor_curtains") || info.Id.StartsWith("decor_drapes"));
                float hangTop = float.NaN;
                if (hangs && StructureWindows.OpeningNear(site, p, n, out Vector3 winCentre, out float headY))
                {
                    p += tangent * Vector3.Dot(winCentre - p, tangent);   // centred on the window ...
                    hangTop = headY + CurtainAboveWindowM;                 // ... its top 10 cm above it
                }
                if (info.Id != null && info.Id.StartsWith("kitchen_range_hood")) p = CentreOnCooktop(p, n, tangent);   // a hood over a cooktop or range centres on it
                string cornerReason = KeepOffCorner(site, info, ref p, n, tangent);   // a wall item never goes into the wall at the end of its wall; a corner cabinet goes INTO the corner
                plan.Rotation = Quaternion.LookRotation(n, Vector3.up);   // measured in the game: a wall model occupies z = 0 .. +depth, so +z points out of the wall
                plan.Position = p + n * 0.003f - Vector3.up * (_local.size.y * 0.5f);   // the pivot is the bottom of the item
                plan.UpperBottom = upperBottom;
                if (hangs)   // curtains and drapes: the top is 10 cm above the window, and never through the ceiling
                {
                    float top = float.IsNaN(hangTop) ? plan.Position.y + _local.max.y : hangTop;
                    top = Mathf.Min(top, site.CeilingY() - 0.02f);
                    plan.Position.y = top - _local.max.y;
                }
                if (!float.IsNaN(upperBottom)) plan.Position.y = upperBottom - _local.min.y;   // the model's own lowest point on the standard line, whatever shape it is
                if (info != null && info.Id != null && info.Id.StartsWith("kitchen_range_hood"))
                    plan.Position.y = Mathf.Min(plan.Position.y, site.CeilingY() - _local.size.y - 0.01f);   // the chimney tops out at the ceiling, never through it
                // The wall's layers do not all end in one plane (a thicker band, a plate, a lower or upper layer): the probe above read only the spot under the cursor. Every spot the item covers
                // is looked at, and the item stands off the FRONTMOST wall surface it spans, so no part of it (the tall chimney of a range hood) sinks into the wall.
                if (!info.AttachThrough && _local.min.z < -0.002f) plan.Position += n * -_local.min.z;   // a model that reaches behind its origin (the wall cabinets: 3.4 cm) stands off by that much, so its back is on the wall, not in it
                float push = info.Id != null && info.Id.StartsWith("kitchen_wall_corner") ? 0f : FrontmostWall(site, p, n, tangent, plan.Position.y, _local.size.x, _local.size.y);   // (a corner cabinet's arm reaches the side wall, which read as a wall in front and stood the whole cabinet off the back wall: bigger and nearer than its neighbours)
                if (push > 0.003f) { p += n * push; plan.Position += n * push; }
                if (info.AttachThrough) plan.Thickness = AttachedObject.MeasureWall(site, p, n);
                plan.Reason = cornerReason ?? Check(site, info, p, n, tangent, surface, ped, true);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
        }

        /// <summary>RaycastAll that also meets back faces: a wall layer whose collider faces away from the room (a one-sided inner finish) is still the surface nearest the room, not skipped for the layer behind it.</summary>
        private static RaycastHit[] RaycastBothFaces(Vector3 origin, Vector3 dir, float reach)
        {
            bool old = Physics.queriesHitBackfaces;
            Physics.queriesHitBackfaces = true;
            RaycastHit[] hits = Physics.RaycastAll(origin, dir, reach, ~0, QueryTriggerInteraction.Ignore);
            Physics.queriesHitBackfaces = old;
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            return hits;
        }

        /// <summary>How far (m) the frontmost wall surface under the item's footprint (a grid over its width and height, from the bottom at bottomY) lies in front of the plane through p; 0 when none does.</summary>
        private float FrontmostWall(ConstructionSite site, Vector3 p, Vector3 n, Vector3 tangent, float bottomY, float width, float height)
        {
            float push = 0f;
            int cols = Mathf.Max(2, Mathf.CeilToInt(width / 0.1f)), rows = Mathf.Max(2, Mathf.CeilToInt(height / 0.1f));
            for (int i = 0; i <= cols; i++)
                for (int j = 0; j <= rows; j++)
                {
                    Vector3 s = p + tangent * ((i / (float)cols - 0.5f) * width * 0.96f);
                    s.y = bottomY + height * (j / (float)rows);
                    RaycastHit[] hits = RaycastBothFaces(s + n * 0.6f, -n, 1.3f);
                    System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
                    foreach (RaycastHit h in hits)
                    {
                        if (h.collider.GetComponentInParent<ConstructionSite>() != site) continue;
                        if (h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                        if (!IsWallPart(h.collider, site)) continue;
                        if (Mathf.Abs(Vector3.Dot(h.normal, n)) < 0.5f) break;   // the edge of a board or a log, not a face
                        push = Mathf.Max(push, Vector3.Dot(h.point - p, n));
                        break;
                    }
                }
            return Mathf.Min(push, 0.4f);
        }

        /// <summary>A range hood with a cooktop or a range below it (against the same wall, within 0.8 m along it) is slid to the cooktop's centre.</summary>
        private static Vector3 CentreOnCooktop(Vector3 p, Vector3 n, Vector3 tangent)
        {
            float bestD = 0.8f, shift = 0f;
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null || o.ItemId == null) continue;
                bool cook = o.ItemId.StartsWith("kitchen_cooktop") || (o.ItemId.StartsWith("kitchen_range_") && !o.ItemId.StartsWith("kitchen_range_hood"));
                if (!cook) continue;
                Bounds b = default; bool any = false;
                foreach (Renderer r in o.GetComponentsInChildren<Renderer>()) { if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
                if (!any || b.center.y > p.y) continue;
                float off = Vector3.Dot(b.center - p, n);
                if (off < -0.2f || off > 1.2f) continue;   // not against this wall
                float along = Vector3.Dot(b.center - p, tangent);
                if (Mathf.Abs(along) < bestD) { bestD = Mathf.Abs(along); shift = along; }
            }
            return p + tangent * shift;
        }

        private static bool IsUpper(ItemRegistry.ItemInfo info) { return info != null && info.Id != null && info.Id.StartsWith("kitchen_wall_c"); }
        private static bool IsUpper(string id) { return id != null && id.StartsWith("kitchen_wall_c"); }

        /// <summary>The floor of the room in front of the wall spot (world y).</summary>
        private static float FloorBelow(ConstructionSite site, Vector3 p, Vector3 n)
        {
            RaycastHit[] hits = Physics.RaycastAll(p + n * 0.3f, Vector3.down, 6f, ~0, QueryTriggerInteraction.Ignore);
            float floor = float.NaN;
            foreach (RaycastHit h in hits)   // the LOWEST upward face of the building: a counter, a filler strip or a shelf below the spot is not the floor
            {
                if (h.collider.GetComponentInParent<ConstructionSite>() != site || h.collider.GetComponentInParent<AttachedObject>() != null || h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                if (h.normal.y > 0.5f && (float.IsNaN(floor) || h.point.y < floor)) floor = h.point.y;
            }
            return float.IsNaN(floor) ? site.transform.position.y : floor;
        }

        /// <summary>The span a mounted item covers along the wall (its click box), in the wall's own direction.</summary>
        private static bool AlongRange(Transform tr, Vector3 tangent, out float lo, out float hi)
        {
            lo = hi = 0f;
            BoxCollider box = tr.GetComponent<BoxCollider>();
            if (box == null) return false;
            float c = Vector3.Dot(tr.TransformPoint(box.center), tangent);
            float half = 0.5f * (Mathf.Abs(Vector3.Dot(tr.right, tangent)) * box.size.x + Mathf.Abs(Vector3.Dot(tr.forward, tangent)) * box.size.z);
            lo = c - half; hi = c + half;
            return true;
        }

        /// <summary>Slides a wall cabinet along its wall so it touches the nearest wall cabinet beside it (within a quarter metre).</summary>
        private Vector3 SnapUpper(ConstructionSite site, Vector3 p, Vector3 n, Vector3 tangent)
        {
            float pa = Vector3.Dot(p, tangent);
            float lo = pa + _local.center.x - _local.size.x * 0.5f, hi = lo + _local.size.x;
            float best = 0.25f, delta = 0f;
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != site || !IsUpper(a.ItemId) || Vector3.Dot(a.transform.forward, n) < 0.95f || Mathf.Abs(Vector3.Dot(a.transform.position - p, n)) > 0.12f) continue;
                if (!AlongRange(a.transform, tangent, out float alo, out float ahi)) continue;
                float d1 = alo - hi, d2 = ahi - lo;       // my right edge to its left edge, my left edge to its right edge
                if (Mathf.Abs(d1) < best) { best = Mathf.Abs(d1); delta = d1; }
                if (Mathf.Abs(d2) < best) { best = Mathf.Abs(d2); delta = d2; }
            }
            return p + tangent * delta;
        }

        /// <summary>The first thing a ray meets that is not the preview, a mounted item or a placed one: true when it is a wall of the building.</summary>
        private bool WallAhead(ConstructionSite site, Vector3 origin, Vector3 dir, float reach, out RaycastHit wall)
        {
            wall = default;
            RaycastHit[] hits = Physics.RaycastAll(origin, dir, reach, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null || (_ghost != null && h.collider.transform.IsChildOf(_ghost.transform))) continue;
                if (h.collider.GetComponentInParent<AttachedObject>() != null || h.collider.GetComponentInParent<PlacedObject>() != null || h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<ConstructionSite>() != site || !IsWallPart(h.collider, site)) return false;
                wall = h;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Keeps a wall item inside its wall: the wall at either end (a corner) is looked for along the wall at the height of the item, and the item is moved away from it by as much as it
        /// would have sunk in. A CORNER wall cabinet (kitchen_wall_corner_*: an L whose side arm is on its +x side, the left as you face it) is moved INTO the corner so the arm lies flush on
        /// the corner wall, or refused (with the reason) when there is no corner on that side. Returns the reason it cannot go here, or null.
        /// </summary>
        private string KeepOffCorner(ConstructionSite site, ItemRegistry.ItemInfo info, ref Vector3 p, Vector3 n, Vector3 tangent)
        {
            float half = _local.size.x * 0.5f;
            if (half < 0.05f) return null;
            bool corner = info != null && info.Id != null && info.Id.StartsWith("kitchen_wall_corner");
            Vector3 origin = p + n * 0.1f;
            if (corner)
            {
                // the side arm is on the item's +x side: the corner wall must be that way, within reach of the arm
                if (WallAhead(site, origin, tangent, 1.2f, out RaycastHit side) && Vector3.Dot(side.normal, -tangent) > 0.8f)
                {
                    p += tangent * (side.distance - half - 0.003f);
                    return null;
                }
                return "Hang it in a corner: the corner wall must be on its left as you face it (mount it on the other wall of the corner).";
            }
            for (int sg = -1; sg <= 1; sg += 2)
            {
                if (WallAhead(site, origin, tangent * sg, half + 0.02f, out RaycastHit end) && Vector3.Dot(end.normal, -tangent * sg) > 0.8f && end.distance < half + 0.003f)
                    p -= tangent * sg * (half + 0.003f - end.distance);      // it would sink into the wall at this end: slid back out
            }
            return null;
        }

        /// <summary>
        /// A roof item (a solar panel rack): aimed at the roof from the ground. It lies flat on the roof surface under the cursor, its long side running up the
        /// slope (on a flat roof along the building, R turns it). The player does not climb: only the distance to the building counts (RoofReach).
        /// </summary>
        private Plan PlanRoof(Camera cam, Vector2 pointer, ItemRegistry.ItemInfo info, PedController ped)
        {
            var plan = new Plan();
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, pointer);
            foreach (RaycastHit h in hits)
            {
                if (h.collider == null) continue;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null) return plan;                     // the first thing hit is not a building
                plan.Site = site;
                Vector3 n = h.normal;
                plan.Position = h.point;
                plan.Rotation = Quaternion.identity;
                bool onRoof = h.point.y > site.CeilingY() + 0.15f || RoofNamed(h.collider, site);
                if (!onRoof || n.y < 0.3f) { plan.Reason = "Aim at the roof."; return plan; }
                Vector3 uphill = Vector3.ProjectOnPlane(Vector3.up, n);
                if (uphill.sqrMagnitude < 0.01f) uphill = Quaternion.Euler(0f, _turn * 90f + site.YawDeg, 0f) * Vector3.forward;   // a flat roof: along the building
                plan.Rotation = Quaternion.LookRotation(uphill.normalized, n);
                plan.Position = h.point + n * 0.004f;
                bool snapped = TrySnapRoof(site, n, ref plan);
                plan.Reason = CheckRoof(site, plan.Position, ped, snapped);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
        }

        private static string s_roofLog;
        public const float RoofTurnDeg = 22.5f;   // R turns a thing standing on a roof by this much (Shift + R: the other way)

        /// <summary>
        /// R with the cursor on a dish, yagi or access point that already stands on a roof turns it where it is (Shift + R the other way), whatever is in hand:
        /// an antenna is aimed after it is up. True when the key was for that.
        /// </summary>
        private static bool TurnMounted(Camera cam, Vector2 pointer)
        {
            if (cam == null || AttachedObject.All.Count == 0) return false;
            AttachedObject a = AttachedObject.UnderRay(cam.ScreenPointToRay(pointer), 1000f);
            if (a == null || a.Surface != "roof" || !RoofMount(a.ItemId)) return false;
            var kb = UnityEngine.InputSystem.Keyboard.current;
            bool reverse = kb != null && kb.shiftKey.isPressed;
            a.transform.Rotate(Vector3.up, reverse ? -RoofTurnDeg : RoofTurnDeg, Space.World);
            return true;
        }

        /// <summary>True for an item that stands on the ground but may also be put up on a roof (properties.roof_mount: a dish, a yagi, an access point).</summary>
        public static bool RoofMount(string itemId)
        {
            AssetCatalogItem it = HudBindings.GetCatalogItem(itemId);
            return it != null && it.roof_mount;
        }

        /// <summary>True when the first thing under the cursor is the roof of a finished building.</summary>
        public static bool OverRoof(Camera cam, Vector2 pointer)
        {
            if (cam == null) return false;
            foreach (RaycastHit h in Homesteader.UI.HoverTarget.SortedHits(cam, pointer))
            {
                if (h.collider == null || h.collider.GetComponentInParent<PedController>() != null || h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                return site != null && site.Finished && h.normal.y >= 0.3f && (h.point.y > site.CeilingY() + 0.15f || RoofNamed(h.collider, site));
            }
            return false;
        }

        /// <summary>True when a left click with this item in hand is for putting it up on the roof under the cursor (so the ground placement leaves the click alone).</summary>
        public static bool TakesRoofClick(string itemId, Camera cam, Vector2 pointer) { return RoofMount(itemId) && OverRoof(cam, pointer); }

        /// <summary>
        /// A thing that STANDS on the roof (a dish, a yagi, an access point): upright whatever the slope, its foot on the roof under the cursor, turned freely with R
        /// (RoofTurnDeg a press) so an antenna can be aimed. Put up from the ground like a roof rack: only the distance to the building counts.
        /// </summary>
        private Plan PlanRoofUpright(Camera cam, Vector2 pointer, PedController ped)
        {
            var plan = new Plan();
            foreach (RaycastHit h in Homesteader.UI.HoverTarget.SortedHits(cam, pointer))
            {
                if (h.collider == null || h.collider.GetComponentInParent<PedController>() != null || h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null) return plan;
                plan.Site = site;
                plan.Position = h.point;
                plan.Rotation = Quaternion.Euler(0f, _turn * RoofTurnDeg + site.YawDeg, 0f);
                bool onRoof = h.normal.y >= 0.3f && (h.point.y > site.CeilingY() + 0.15f || RoofNamed(h.collider, site));
                if (!onRoof) { plan.Reason = "Aim at the roof."; return plan; }
                plan.Reason = CheckRoof(site, plan.Position, ped);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
        }

        private static bool RoofNamed(Collider c, ConstructionSite site)
        {
            for (Transform t = c.transform; t != null && t != site.transform; t = t.parent)
                if (t.name.IndexOf("Roof", System.StringComparison.OrdinalIgnoreCase) >= 0) return true;
            return false;
        }

        private const float RackGap = 0.05f;   // between two racks: their panels sit edge to edge with this much air

        /// <summary>A roof rack aimed near another one on the same roof snaps edge to edge to it (same rotation, a hair apart) so the panels make a neat block. True when it did.</summary>
        private bool TrySnapRoof(ConstructionSite site, Vector3 normal, ref Plan plan)
        {
            if (string.IsNullOrEmpty(HeldAttachItem())) return false;
            AttachedObject nearest = null;
            float nd = 3f;
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != site || a.Surface != "roof" || a.GetComponent<BoxCollider>() == null) continue;
                if (Vector3.Dot(a.transform.up, normal) < 0.95f) continue;   // on another slope
                float d = (a.transform.position - plan.Position).magnitude;
                if (d < nd) { nd = d; nearest = a; }
            }
            if (nearest == null) return false;
            BoxCollider bc = nearest.GetComponent<BoxCollider>();
            Vector3 sc = nearest.transform.lossyScale;
            float wn = bc.size.x * Mathf.Abs(sc.x), dn = bc.size.z * Mathf.Abs(sc.z);
            float w = _local.size.x, d2 = _local.size.z;
            AssetCatalogItem theirInfo = HudBindings.GetCatalogItem(nearest.ItemId), myInfo = HudBindings.GetCatalogItem(ConstructionSite.HeldItem());
            if (theirInfo != null) { wn = Mathf.Max(wn, theirInfo.panel_width_m); dn = Mathf.Max(dn, theirInfo.panel_depth_m); }   // the panel is wider than the rack under it: space by the panel
            if (myInfo != null) { w = Mathf.Max(w, myInfo.panel_width_m); d2 = Mathf.Max(d2, myInfo.panel_depth_m); }
            Transform t = nearest.transform;
            Vector3[] offsets =
            {
                t.right * (wn * 0.5f + w * 0.5f + RackGap), -t.right * (wn * 0.5f + w * 0.5f + RackGap),
                t.forward * (dn * 0.5f + d2 * 0.5f + RackGap), -t.forward * (dn * 0.5f + d2 * 0.5f + RackGap),
            };
            Vector3 best = default;
            float bd = float.MaxValue;
            foreach (Vector3 o in offsets)
            {
                Vector3 c = t.position + o;
                float dist = (c - plan.Position).sqrMagnitude;
                if (dist < bd) { bd = dist; best = c; }
            }
            if (bd > 1.8f * 1.8f) return false;
            plan.Position = best;
            plan.Rotation = t.rotation;
            return true;
        }

        private string HeldAttachItem()
        {
            return ItemRegistry.TryGet(ConstructionSite.HeldItem(), out ItemRegistry.ItemInfo hi) ? hi.AttachItem : null;
        }

        private string CheckRoof(ConstructionSite site, Vector3 point, PedController ped, bool snapped = false)
        {
            if (!site.Finished) return "Finish building it first.";
            if (ped != null && site.DistanceOutside(ped.transform.position) > RoofReach) return "Too far: move closer to the building.";
            float radius = snapped ? 0.35f * Mathf.Min(_local.size.x, _local.size.z) : Mathf.Max(MinApart, 0.5f * Mathf.Max(_local.size.x, _local.size.z));   // a snapped rack touches its neighbour on purpose
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != site || a.Surface != "roof") continue;
                if ((a.transform.position - point).magnitude < radius) return "Too close to another one.";
            }
            return null;
        }

        private Plan PlanCeiling(Camera cam, Vector2 pointer, ItemRegistry.ItemInfo info, PedController ped)
        {
            // You cannot see a ceiling from above, so the light is aimed at the FLOOR: it goes up to the ceiling over the spot the cursor is on,
            // and a line from the floor spot to the light shows where it will hang.
            var plan = new Plan();
            Ray ray = cam.ScreenPointToRay(pointer);
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                if (h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null) return plan;                          // the first thing hit is not a building
                if (h.normal.y < 0.5f) continue;                        // a wall: look past it to the floor behind it
                plan.Site = site;
                Vector3 fp = h.point;
                fp.x = Mathf.Round(fp.x / Snap) * Snap;
                fp.z = Mathf.Round(fp.z / Snap) * Snap;
                float ceiling = site.CeilingY();
                plan.Rotation = Quaternion.Euler(0f, _turn * 90f + site.YawDeg, 0f);
                plan.Position = new Vector3(fp.x, ceiling - _local.size.y, fp.z);   // hangs from the ceiling: the top of the item touches it
                plan.GuideFrom = fp;
                plan.HasGuide = true;
                plan.Reason = !site.IsInsideWalls(fp) ? "Hang it inside the building." : Check(site, info, new Vector3(fp.x, ceiling, fp.z), Vector3.down, Vector3.right, null, ped, false);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
        }

        /// <summary>Why it cannot be mounted at this spot, or null when it can.</summary>
        private string Check(ConstructionSite site, ItemRegistry.ItemInfo info, Vector3 point, Vector3 normal, Vector3 tangent, Collider wall, PedController ped, bool isWall)
        {
            if (!site.Finished) return "Finish building it first.";
            if (info.ProvidesPower)   // one breaker box to a building: a second would be a second feed into the same system
                foreach (AttachedObject other in AttachedObject.All)
                    if (other != null && other.Site == site && other.ProvidesPower) return "This building already has a breaker box (" + HudBindings.GetItemName(other.ItemId) + "): take it down first.";
            if (ped != null && new Vector2(point.x - ped.transform.position.x, point.z - ped.transform.position.z).magnitude > Reach) return "Too far: move closer.";
            if (isWall)
            {
                // on a door? (the leaf of the front door or a barn door is not a wall)
                for (Transform t = wall != null ? wall.transform : null; t != null && t != site.transform; t = t.parent)
                    if (t.name.StartsWith("Door")) return "Not on a door.";
                    else if (t.name.StartsWith("WindowGlass") || t.name.StartsWith("WindowFrame")) return "Not on a window.";
                bool inside = site.IsInsideWalls(point + normal * 0.15f);
                if (info.AttachSide == "exterior" && inside) return "This goes on the OUTSIDE of a building.";
                if (info.AttachSide == "interior" && !inside) return "This goes on the INSIDE of a building.";
                float floor = site.transform.position.y;
                float ceiling = site.CeilingY();
                if (point.y < floor + 0.5f) return "Too low.";
                if (point.y > ceiling - 0.25f) return "Too high.";
            }
            else
            {
                if (ped != null && !site.IsInsideWalls(ped.transform.position)) return "Step inside to hang a light.";
            }
            foreach (AttachedObject a in AttachedObject.All)
            {
                if (a == null || a.Site != site || a.Surface != info.AttachSurface) continue;
                if (isWall && IsUpper(info) && IsUpper(a.ItemId))
                {
                    // wall cabinets sit edge to edge: only overlapping is refused
                    if (Mathf.Abs(Vector3.Dot(a.transform.position - point, normal)) < 0.12f && Mathf.Abs(a.transform.position.y - point.y) < 0.3f && AlongRange(a.transform, tangent, out float alo, out float ahi))
                    {
                        float mlo = Vector3.Dot(point, tangent) + _local.center.x - _local.size.x * 0.5f, mhi = mlo + _local.size.x;
                        if (Mathf.Min(mhi, ahi) - Mathf.Max(mlo, alo) > 0.02f) return "Too close to another one.";
                    }
                    continue;
                }
                if ((a.transform.position - point).magnitude < MinApart && !(isWall && Mathf.Abs(a.transform.position.y - point.y) > 0.6f)) return "Too close to another one.";
            }
            return null;
        }

        // ------------------------------------------------------------------ a chimney kit

        private GameObject _chimGhost;
        private string _chimKey;
        private ChimneyPlan _chimPlan;
        private float _chimPlanTime;
        private Vector2 _chimPlanPointer;
        private string _chimKeyHeld;

        /// <summary>The preview of a chimney on the wall under the cursor (blue = it can go there, red = not), and the second click or Enter that builds it.</summary>
        private void UpdateChimney(string held, Camera cam, Vector2 pointer, PedController ped)
        {
            // the plan casts a few dozen rays: worked out again only when the cursor has moved or a fifth of a second has passed, not every frame
            if (_chimKeyHeld != held || Time.unscaledTime - _chimPlanTime > 0.2f || (pointer - _chimPlanPointer).sqrMagnitude > 16f)
            {
                _chimPlan = ChimneyPlanner.Plan(cam, pointer, held, ped);
                _chimPlanTime = Time.unscaledTime;
                _chimPlanPointer = pointer;
                _chimKeyHeld = held;
            }
            ChimneyPlan plan = _chimPlan;
            if (plan.Site == null && plan.Reason == null) { HideChimneyGhost(); return; }   // the cursor is not over a building
            if (plan.Origin != Vector3.zero)
            {
                string key = plan.Spec.Brick + ":" + plan.Spec.Thickness.ToString("0.00") + ":" + plan.Spec.Bottom.ToString("0.0") + ":" + plan.Spec.Top.ToString("0.0");
                if (_chimGhost == null || key != _chimKey)
                {
                    if (_chimGhost != null) Destroy(_chimGhost);
                    _chimGhost = ChimneyBuilder.Build(plan.Spec, false, out _, out _);
                    _chimGhost.name = "ChimneyGhost";
                    _chimKey = key;
                }
                _chimGhost.SetActive(true);
                _chimGhost.transform.SetPositionAndRotation(plan.Origin, plan.Rotation);
                GhostVisual.Apply(_chimGhost, plan.Valid ? ValidTint : InvalidTint, GhostAlpha);
            }
            else HideChimneyGhost();
            bool confirm = Enter() || (LeftClicked() && Time.frameCount != _startFrame);
            if (!confirm) return;
            if (!plan.Valid) { ToastNotificationSystem.ShowWarning("Can't build it here", plan.Reason); return; }
            HudState state = HudState.Active;
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance?.RefreshToolbar();
            PlacedChimney.Spawn(plan.Site, held, plan.Origin, plan.Rotation, plan.Spec);
            _placing = false;
            HideChimneyGhost();
        }

        private void HideChimneyGhost() { if (_chimGhost != null) _chimGhost.SetActive(false); }

        private static void Mount(string itemId, ItemRegistry.ItemInfo info, Plan plan)
        {
            HudState state = HudState.Active;
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance?.RefreshToolbar();
            AttachedObject a = AttachedObject.Spawn(itemId, info, plan.Site, plan.Position, plan.Rotation, plan.Thickness);
            if (a != null && IsUpper(itemId) && !float.IsNaN(plan.UpperBottom)) a.SetBottom(plan.UpperBottom);   // the real bottom of what was built, on the standard line
            if (a != null && IsUpper(itemId))   // (measured: every wall cabinet should read the same bottom and top)
            {
                Bounds wb = default; bool any = false;
                foreach (Renderer r in a.GetComponentsInChildren<Renderer>(true)) { if (!any) { wb = r.bounds; any = true; } else wb.Encapsulate(r.bounds); }
                if (any) Dbg.Log("[UpperCab] " + itemId + " bottom " + wb.min.y.ToString("0.000") + " top " + wb.max.y.ToString("0.000") + " floor " + plan.Site.transform.position.y.ToString("0.000"));
            }
            if (a != null && info.ProvidesPower)
            {
                if (a.Exterior) ToastNotificationSystem.ShowInfo("Not wired yet", "Wire an inverter to this panel (wire cutters, AC wire) to bring the building electricity.");
                else ToastNotificationSystem.ShowWarning("No power", "A breaker box only brings electricity when it is mounted on the OUTSIDE of the building.");
            }
        }

        // ------------------------------------------------------------------ the preview

        private bool EnsureGhost(string itemId, ItemRegistry.ItemInfo info)
        {
            if (_ghost != null && _ghostId == itemId) return true;
            DestroyGhost();
            Homesteader.Modding.GlbTemplate glb = info.Prefab.GetComponent<Homesteader.Modding.GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                if (glb.Failed || !glb.Ready) return false;
            }
            _ghost = Instantiate(info.Prefab);
            _ghost.name = "AttachGhost_" + itemId;
            _ghost.SetActive(true);
            foreach (Collider c in _ghost.GetComponentsInChildren<Collider>(true)) Destroy(c);
            _ghost.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            // the model's size in its own space (it stands at the origin, unturned, as it was just made)
            Bounds b = new Bounds(Vector3.zero, Vector3.zero);
            bool any = false;
            foreach (Renderer r in _ghost.GetComponentsInChildren<Renderer>(true))
            {
                if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds);
            }
            _local = any ? b : new Bounds(Vector3.one * 0.1f, Vector3.one * 0.2f);
            _ghostId = itemId;
            return true;
        }

        private LineRenderer _guide;

        /// <summary>A thin line from the floor spot under the cursor up to a ceiling light, so you can see where it will hang.</summary>
        private void ShowGuide(Plan plan)
        {
            if (!plan.HasGuide) { if (_guide != null) _guide.enabled = false; return; }
            if (_guide == null)
            {
                var go = new GameObject("AttachGuide");
                go.transform.SetParent(transform, false);
                _guide = go.AddComponent<LineRenderer>();
                _guide.positionCount = 2;
                _guide.startWidth = _guide.endWidth = 0.02f;
                _guide.numCapVertices = 2;
                _guide.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                _guide.receiveShadows = false;
                _guide.material = new Material(Shader.Find("Sprites/Default"));
            }
            Color c = plan.Valid ? ValidTint : InvalidTint;
            _guide.startColor = new Color(c.r, c.g, c.b, 0.9f);
            _guide.endColor = new Color(c.r, c.g, c.b, 0.25f);
            _guide.SetPosition(0, plan.GuideFrom + Vector3.up * 0.02f);
            _guide.SetPosition(1, plan.Position + Vector3.up * _local.size.y);
            _guide.enabled = true;
        }

        private void HideGhost() { HideChimneyGhost(); if (_ghost != null) _ghost.SetActive(false); if (_guide != null) _guide.enabled = false; }
        private void DestroyGhost() { if (_chimGhost != null) Destroy(_chimGhost); _chimGhost = null; if (_ghost != null) Destroy(_ghost); _ghost = null; _ghostId = null; if (_guide != null) _guide.enabled = false; }
        private void OnDisable() { DestroyGhost(); }

        // ------------------------------------------------------------------ input

        private static string HeldId()
        {
            HudState s = HudState.Active;
            if (s == null || s.SelectedSlot < 0 || s.SelectedSlot >= s.Toolbar.Count) return null;
            ToolbarSlotData slot = s.Toolbar[s.SelectedSlot];
            return !string.IsNullOrEmpty(slot.IconId) && slot.Count > 0 ? slot.IconId : null;
        }

        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;
            return FindAnyObjectByType<Camera>();
        }

        private static Vector2 Pointer() { return Mouse.current != null ? Mouse.current.position.ReadValue() : Vector2.zero; }
        private static bool LeftClicked() { return Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame; }
        private static bool Escape() { return Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame; }
        private static bool Enter() { Keyboard k = Keyboard.current; return k != null && (k.enterKey.wasPressedThisFrame || k.numpadEnterKey.wasPressedThisFrame); }
    }
}
