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
            public Quaternion Rotation;
            public Vector3 GuideFrom;      // a ceiling item: the floor spot the cursor is on (a line rises from it to the item)
            public bool HasGuide;
        }

        private void Update()
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null || HudBindings.KeyboardCaptured) { HideGhost(); return; }

            string held = HeldId();
            if (string.IsNullOrEmpty(held) || !ItemRegistry.TryGet(held, out ItemRegistry.ItemInfo info) || string.IsNullOrEmpty(info.AttachSurface) || info.Prefab == null)
            {
                _placing = false;
                HideGhost();
                return;
            }
            if (_placing && held != _placingId) _placing = false;
            if (_placing && Escape()) _placing = false;
            var ped = FindAnyObjectByType<PedController>();
            if (_placing && ped != null && (ped.transform.position - _startPed).sqrMagnitude > 0.0025f) _placing = false;   // walked away

            Camera cam = GameCamera();
            Vector2 pointer = Pointer();
            if (!_placing)
            {
                HideGhost();
                if (cam != null && LeftClicked() && !hud.IsPointerOverUI(pointer))
                {
                    _placing = true;
                    _placingId = held;
                    _startFrame = Time.frameCount;
                    _startPed = ped != null ? ped.transform.position : Vector3.zero;
                }
                if (!_placing) return;
            }
            if (cam == null || hud.IsPointerOverUI(pointer)) { HideGhost(); return; }
            if (!EnsureGhost(held, info)) return;

            if (info.AttachSurface == "ceiling" && Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PlaceRotate)) _turn++;

            Plan plan = info.AttachSurface == "ceiling" ? PlanCeiling(cam, pointer, info, ped) : PlanWall(cam, pointer, info, ped);
            if (plan.Site == null && plan.Reason == null) { HideGhost(); return; }   // the cursor is not over a building
            _ghost.SetActive(true);
            _ghost.transform.SetPositionAndRotation(plan.Position, plan.Rotation);
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

        private Plan PlanWall(Camera cam, Vector2 pointer, ItemRegistry.ItemInfo info, PedController ped)
        {
            var plan = new Plan();
            Ray ray = cam.ScreenPointToRay(pointer);
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                ConstructionSite site = h.collider.GetComponentInParent<ConstructionSite>();
                if (site == null) return plan;   // the first thing hit is not a building: nothing to mount on
                plan.Site = site;
                // A wall is made of layers (cladding, sheathing, logs, siding boards, the inside finish) and the cursor ray may reach any of them, with
                // normals that tilt on a log or a board edge. So the wall plane comes from the BUILDING: the face of its footprint nearest the point
                // (a building's walls are square to it), the side from the way the surface that was hit faces. The surface to sit on is then found by
                // looking at the wall straight on, from outside (or inside) at the cursor's spot: the first thing met there is the outermost layer.
                Vector3 hp = h.point;
                Quaternion siteRot = site.transform.rotation;
                Vector3 lp = Quaternion.Inverse(siteRot) * (hp - site.transform.position);
                Rect wr = site.WallRect();                                        // the walls' rectangle (a porch is outside it, though inside the footprint)
                float dLeft = Mathf.Abs(lp.x - wr.xMin), dRight = Mathf.Abs(wr.xMax - lp.x), dBack = Mathf.Abs(lp.z - wr.yMin), dFront = Mathf.Abs(wr.yMax - lp.z);
                float edgeDist = Mathf.Min(Mathf.Min(dLeft, dRight), Mathf.Min(dBack, dFront));
                Vector3 nLocal = edgeDist == dLeft ? Vector3.left : edgeDist == dRight ? Vector3.right : edgeDist == dBack ? Vector3.back : Vector3.forward;
                Vector3 nOut = siteRot * nLocal;
                float facing = Vector3.Dot(h.normal, nOut);
                bool inRect = lp.x > wr.xMin + 0.02f && lp.x < wr.xMax - 0.02f && lp.z > wr.yMin + 0.02f && lp.z < wr.yMax - 0.02f;
                bool outerSurface = Mathf.Abs(facing) > 0.2f ? facing > 0f : !inRect || edgeDist < 0.06f;
                Vector3 n = outerSurface ? nOut : -nOut;                           // out of the wall, on the side that was aimed at

                // along the wall and up it in small steps, flat on the wall
                Vector3 p = hp;
                p.x = Mathf.Round(p.x / Snap) * Snap;
                p.y = Mathf.Round(p.y / Snap) * Snap;
                p.z = Mathf.Round(p.z / Snap) * Snap;
                p -= n * Vector3.Dot(p - hp, n);                                   // the rounding moved it along the normal too: back onto the plane
                Collider surface = h.collider;
                RaycastHit[] probe = Physics.RaycastAll(p + n * 0.6f, -n, 1.3f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
                System.Array.Sort(probe, (x, y) => x.distance.CompareTo(y.distance));
                foreach (RaycastHit ph in probe)
                {
                    if (ph.collider.GetComponentInParent<ConstructionSite>() != site) continue;
                    if (ph.collider.GetComponentInParent<AttachedObject>() != null) continue;
                    p = new Vector3(ph.point.x, p.y, ph.point.z) ;
                    surface = ph.collider;
                    break;
                }
                Vector3 tangent = Vector3.Cross(Vector3.up, n);
                plan.Rotation = Quaternion.LookRotation(n, Vector3.up);   // measured in the game: a wall model occupies z = 0 .. +depth, so +z points out of the wall
                plan.Position = p + n * 0.003f - Vector3.up * (_local.size.y * 0.5f);   // the pivot is the bottom of the item
                plan.Reason = Check(site, info, p, n, tangent, surface, ped, true);
                plan.Valid = plan.Reason == null;
                return plan;
            }
            return plan;
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
        private static string Check(ConstructionSite site, ItemRegistry.ItemInfo info, Vector3 point, Vector3 normal, Vector3 tangent, Collider wall, PedController ped, bool isWall)
        {
            if (!site.Finished) return "Finish building it first.";
            if (ped != null && new Vector2(point.x - ped.transform.position.x, point.z - ped.transform.position.z).magnitude > Reach) return "Too far: move closer.";
            if (isWall)
            {
                // on a door? (the leaf of the front door or a barn door is not a wall)
                for (Transform t = wall != null ? wall.transform : null; t != null && t != site.transform; t = t.parent)
                    if (t.name.StartsWith("Door")) return "Not on a door.";
                    else if (t.name == "WindowGlass") return "Not on a window.";
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
                if ((a.transform.position - point).magnitude < MinApart && !(isWall && Mathf.Abs(a.transform.position.y - point.y) > 0.6f)) return "Too close to another one.";
            }
            return null;
        }

        private static void Mount(string itemId, ItemRegistry.ItemInfo info, Plan plan)
        {
            HudState state = HudState.Active;
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance?.RefreshToolbar();
            AttachedObject a = AttachedObject.Spawn(itemId, info, plan.Site, plan.Position, plan.Rotation);
            if (a != null && info.ProvidesPower)
            {
                if (a.Exterior) ToastNotificationSystem.ShowInfo("Power connected", "The building has electricity now.");
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

        private void HideGhost() { if (_ghost != null) _ghost.SetActive(false); if (_guide != null) _guide.enabled = false; }
        private void DestroyGhost() { if (_ghost != null) Destroy(_ghost); _ghost = null; _ghostId = null; if (_guide != null) _guide.enabled = false; }
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
