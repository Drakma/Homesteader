using System.Collections.Generic;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Something mounted on a building's wall or ceiling (properties.attach_surface of its manifest): a breaker box, a wall sconce, a ceiling light.
    /// It is a child of the building's site, so it goes where the building goes, and it is saved with the building (GameSave.attached).
    /// An item with properties.provides_power (the outdoor breaker box) mounted on the OUTSIDE of a building brings electricity to that building:
    /// lights that need power (light "requires_power") stay dark in a building that has none. See docs/ATTACHED_ITEMS.md.
    /// </summary>
    public sealed class AttachedObject : MonoBehaviour
    {
        public static readonly List<AttachedObject> All = new List<AttachedObject>();

        public string ItemId { get; private set; }
        public ConstructionSite Site { get; private set; }
        public string Surface { get; private set; }        // wall | ceiling
        /// <summary>
        /// A wall item on the outside of the building. Worked out against the building's REAL walls: mounted from a save while the building's model was still loading, the walls
        /// were not known yet and the footprint (which includes a porch) stood in for them, so a panel on an outside wall counted as inside and the building had no power.
        /// It is re-measured (a few times a second at most) until the model's walls are there.
        /// </summary>
        public bool Exterior
        {
            get
            {
                if (Surface != "wall" || Site == null) return _exterior;
                // an item whose manifest says which side it goes on (a breaker box: exterior) was only ACCEPTED on that side (AttachController.Check), so it is on it: measuring
                // again with a slightly different probe put a panel on a porch building's wall "inside" and the building lost its power
                if (_side == "exterior") return true;
                if (_side == "interior") return false;
                Transform root = Site.VisualRoot;
                if (root != null && (_exteriorFor != root || Time.unscaledTime >= _exteriorNext) && Time.unscaledTime >= _exteriorNext)
                {
                    _exteriorNext = Time.unscaledTime + (_exteriorFor == root ? 5f : 0.5f);
                    _exterior = !Site.IsInsideWalls(Site.transform.TransformPoint(_exteriorProbe));
                    if (Site.WallsKnown) _exteriorFor = root;
                }
                return _exterior;
            }
            private set { _exterior = value; }
        }
        private string _side = "either";   // the manifest's attach_side
        private bool _exterior;
        private Transform _exteriorFor;
        private float _exteriorNext;
        private Vector3 _exteriorProbe;   // the point 0.1 m off the mounting face, in the building's own space
        public bool ProvidesPower { get; private set; }
        public float Thickness { get; private set; }       // a through-the-wall item: the wall's thickness it spans

        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { All.Clear(); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void HookPower()
        {
            // Lights that need power ask here. Only attached things are gated: any other light that "requires power" keeps working as before.
            LightEmitter.PowerCheck = (id, pos, watts) =>
            {
                AttachedObject a = Nearest(pos, 0.75f);
                return a == null || a.Site == null || HasPower(a.Site);
            };
            LightEmitter.PowerRatio = (id, pos, watts) =>
            {
                AttachedObject a = Nearest(pos, 0.75f);
                return a == null || a.Site == null ? 1f : WireNetwork.SupplyRatio(a.Site);   // a building's lights run on the building's own power only (a portable generator is not connected to structures)
            };
            LightEmitter.SiteOf = pos => { AttachedObject a = Nearest(pos, 0.75f); return a != null ? a.Site : null; };
        }

        private static readonly Dictionary<ConstructionSite, string> s_noPowerLogged = new Dictionary<ConstructionSite, string>();
        private static void LogNoPower(ConstructionSite site, string why)
        {
            if (s_noPowerLogged.TryGetValue(site, out string last) && last == why) return;
            s_noPowerLogged[site] = why;
            Dbg.Log("[Power] " + site.Name() + " has no power: " + why);   // (once per change: why a building with a breaker box still reads as unpowered)
        }

        /// <summary>True while a power-providing item is mounted on the outside of this building.</summary>
        public static bool HasPower(ConstructionSite site)
        {
            if (site == null) return false;
            if (WireNetwork.OnGenerator(site)) return true;   // switched over to its standby generator by its lockout box
            int boxes = 0;
            foreach (AttachedObject b in All) if (b != null && b.Site == site && b.ProvidesPower) boxes++;
            if (boxes > 1) LogNoPower(site, "it has " + boxes + " breaker boxes (one to a building: take the extra ones down)");   // (a save from before the one-box rule)
            foreach (AttachedObject a in All)
            {
                if (a == null || a.Site != site || !a.ProvidesPower) continue;
                if (!a.Exterior) { LogNoPower(site, a.ItemId + " is mounted on the INSIDE (a breaker box only brings power from the outside of the building)"); continue; }
                WireNode node = a.GetComponent<WireNode>();
                if (node == null || WireNetwork.IsEnergized(node)) return true;   // an AC panel brings power only while an inverter with a complete chain is wired to it
                LogNoPower(site, a.ItemId + " is outside but not energized: no inverter with a complete chain is wired to it");
            }
            return false;
        }

        private static AttachedObject Nearest(Vector3 pos, float within)
        {
            AttachedObject best = null;
            float bestD = within * within;
            foreach (AttachedObject a in All)
            {
                if (a == null) continue;
                float d = (a.transform.position - pos).sqrMagnitude;
                if (d < bestD) { bestD = d; best = a; }
            }
            return best;
        }

        // ------------------------------------------------------------------ through the wall

        public const float DefaultWall = 0.25f;     // the sleeve of the model is this long as it comes; it is scaled to the wall

        /// <summary>
        /// A wire entry: its model has a node "Plate" (the face plate, standing on the side it was aimed at, its front towards +z) and a node "Pipe" (a sleeve DefaultWall long going
        /// into the wall, towards -z). This lengthens the pipe to the wall's thickness and makes a second plate (PlateFar) on the OTHER side, turned to face the other way, so the
        /// item shows and can be clicked from both sides. Safe to call again with a new thickness (the ghost does, every frame).
        /// </summary>
        public static void ApplyThrough(GameObject root, float thickness)
        {
            // glTFast splits a multi-material model into sibling nodes (Plate, Plate_1, Plate_2 ...): the whole front plate is every one of them, the far plate is a copy of all of them
            var plates = new List<Transform>();
            Transform pipe = null, far = null;
            foreach (Transform c in root.GetComponentsInChildren<Transform>(true))
            {
                if (c.name == "PlateFar") far = c;
                else if (c.name.StartsWith("PlateFar")) continue;
                else if (c.name.StartsWith("Plate")) plates.Add(c);
                else if (c.name.StartsWith("Pipe")) pipe = c;
            }
            if (plates.Count == 0 || pipe == null) return;
            Transform plate = plates[0];
            if (far == null)
            {
                far = new GameObject("PlateFar").transform;
                far.SetParent(plate.parent, false);
                foreach (Transform p in plates)
                {
                    Transform copy = Instantiate(p.gameObject, far).transform;
                    copy.name = p.name;
                    copy.localPosition = p.localPosition;
                    copy.localRotation = p.localRotation;
                    copy.localScale = p.localScale;
                }
            }
            far.localPosition = plate.localPosition + plate.localRotation * new Vector3(0f, 0f, -(thickness + 0.02f));   // a little past the face so it never sits buried in it
            far.localRotation = plate.localRotation * Quaternion.Euler(0f, 180f, 0f);
            far.localScale = Vector3.one;
            pipe.localScale = new Vector3(pipe.localScale.x, pipe.localScale.y, (thickness + 0.02f) / DefaultWall);
        }

        /// <summary>
        /// How thick the wall is at a point on one of its faces: a ray from behind the wall back towards the point meets the wall's other face first (rays only hit the front of a
        /// face, so from behind it is the inner finish, the outermost layer on that side). The default when nothing is found.
        /// </summary>
        /// <summary>All layers: a wall hidden by the cutout is on the Ignore Raycast layer and must still count (a wall measured through it came out too thin).</summary>
        private const int WallLayers = ~0;

        public static float MeasureWall(ConstructionSite site, Vector3 point, Vector3 outNormal)
        {
            float best = 0f;
            // 1. from behind the wall towards the point: the first face met is the wall's other face
            RaycastHit[] hits = Physics.RaycastAll(point - outNormal * 0.7f, outNormal, 0.7f, WallLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (IsNotWall(h.collider, site)) continue;
                float t = Vector3.Dot(point - h.point, outNormal);
                if (t > 0.03f && t < 0.65f) { best = t; break; }
            }
            // 2. from the point into the wall, counting the BACK faces too: the last one met is the inside of the innermost layer (a layer without a front face on that side is missed by 1)
            bool old = Physics.queriesHitBackfaces;
            Physics.queriesHitBackfaces = true;
            RaycastHit[] into = Physics.RaycastAll(point + outNormal * 0.02f, -outNormal, 0.7f, WallLayers, QueryTriggerInteraction.Ignore);
            Physics.queriesHitBackfaces = old;
            foreach (RaycastHit h in into)
            {
                if (IsNotWall(h.collider, site)) continue;
                float t = Vector3.Dot(point - h.point, outNormal);
                if (t > best && t < 0.65f) best = t;
            }
            return best > 0.03f ? Mathf.Max(best, 0.1f) : DefaultWall;
        }

        /// <summary>True when a bit of the building's wall (a collider or a wall part's model) is just outside the far plate: the plate is still inside the wall.</summary>
        private static bool FarPlateBuried(GameObject root, ConstructionSite site, float span)
        {
            // at the height of the MIDDLE of the plate, not of its foot: a jack or an inlet mounted low has its foot at the floor, and the floor is part of the building,
            // so the probe found "wall" however far the plate was pushed and the far plate ended 0.6 m into the room
            float mid = 0.06f;
            foreach (Renderer pr in root.GetComponentsInChildren<Renderer>(true))
                if (pr.name.StartsWith("Plate") || (pr.transform.parent != null && pr.transform.parent.name.StartsWith("Plate") && !pr.transform.parent.name.StartsWith("PlateFar")))
                { mid = Mathf.Max(0.04f, pr.bounds.center.y - root.transform.position.y); break; }
            Vector3 probe = root.transform.position + Vector3.up * mid - root.transform.forward * (span + 0.02f + 0.05f);
            foreach (Collider c in Physics.OverlapSphere(probe, 0.03f, WallLayers, QueryTriggerInteraction.Ignore))
                if (!IsNotWall(c, site)) return true;
            Transform vr = site.VisualRoot;
            if (vr != null)
                foreach (Renderer r in vr.GetComponentsInChildren<Renderer>(true))
                {
                    string n = r.name;
                    for (Transform t = r.transform.parent; t != null && t != vr.parent && !n.StartsWith("Wall"); t = t.parent) n = t.name;
                    if (!n.StartsWith("Wall_")) continue;
                    // only a part that is a slab of wall here: a wall part with a gable out at the porch's edge (a front wall) has a box metres deep, which held the
                    // probe however far the plate was pushed, so the far plate ended 0.6 m into the room
                    Vector3 f = root.transform.forward;
                    if (Mathf.Abs(f.x) * r.bounds.size.x + Mathf.Abs(f.z) * r.bounds.size.z > 0.5f) continue;
                    if (r.bounds.Contains(probe)) return true;
                }
            return false;
        }

        private static bool IsNotWall(Collider c, ConstructionSite site)
        {
            return c.GetComponentInParent<PedController>() != null || c.GetComponentInParent<AttachedObject>() != null || c.GetComponentInParent<PlacedObject>() != null
                   || c.GetComponentInParent<ConstructionSite>() != site;
        }

        // ------------------------------------------------------------------ making one

        /// <summary>Mounts a new one at a world position and rotation (a fresh placement or a restored save).</summary>
        public static AttachedObject Spawn(string itemId, ItemRegistry.ItemInfo info, ConstructionSite site, Vector3 worldPos, Quaternion worldRot, float thickness = 0f)
        {
            if (info == null || info.Prefab == null || site == null) return null;
            GameObject obj = Instantiate(info.Prefab, site.transform);
            obj.name = "Attached_" + itemId;
            obj.SetActive(true);
            obj.transform.SetPositionAndRotation(worldPos, worldRot);
            if (info.AttachThrough)
            {
                // (a save from before the probe was fixed holds a plate pushed 0.6 m into the room: measured again)
                if (thickness > 0.45f) thickness = MeasureWall(site, worldPos, worldRot * Vector3.forward);
                float span = thickness > 0.02f ? thickness : DefaultWall;
                float firstSpan = span;
                ApplyThrough(obj, span);   // the other side's plate and the sleeve through the wall, before the colliders are made
                // the measurement can come out short (a wall of several layers): push the far plate out until nothing of the building is in front of it
                for (int step = 0; span < Mathf.Min(0.6f, firstSpan + 0.15f) && FarPlateBuried(obj, site, span); step++) { span += 0.03f; ApplyThrough(obj, span); }   // (a wall is never mis-measured by more than a layer or two)
                thickness = span;
                bool both = false;
                foreach (Transform c in obj.GetComponentsInChildren<Transform>(true)) if (c.name == "PlateFar") both = true;
                Dbg.Log("[WallEntry] " + itemId + " goes through a wall " + span.ToString("0.00") + " m thick; second plate " + (both ? "made" : "NOT made (no Plate / Pipe nodes in the model)"));
            }
            // Walk-through: a small thing on a wall must not catch the character; its colliders are triggers (a ray that asks for triggers still finds it, to pick it up).
            // One trigger box over the whole model replaces its mesh colliders: a detailed model (a bus bar with its studs, a heat sink) is too complex to cook as a convex mesh, so it got
            // no collider at all and could not be clicked (a ray that asks for triggers still finds the box, to pick it up or to wire it).
            foreach (Collider old in obj.GetComponentsInChildren<Collider>(true)) Destroy(old);
            {
                bool any = false;
                Bounds lb = default;
                foreach (Renderer r in obj.GetComponentsInChildren<Renderer>(true))
                {
                    Bounds wb = r.bounds;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 corner = wb.center + new Vector3((i & 1) == 0 ? -wb.extents.x : wb.extents.x, (i & 2) == 0 ? -wb.extents.y : wb.extents.y, (i & 4) == 0 ? -wb.extents.z : wb.extents.z);
                        Vector3 local = obj.transform.InverseTransformPoint(corner);
                        if (!any) { lb = new Bounds(local, Vector3.zero); any = true; } else lb.Encapsulate(local);
                    }
                }
                if (any)
                {
                    var box = obj.AddComponent<BoxCollider>();
                    box.isTrigger = true;
                    box.center = lb.center;
                    box.size = Vector3.Max(lb.size, new Vector3(0.03f, 0.03f, 0.03f));
                }
            }
            var a = obj.AddComponent<AttachedObject>();
            a.ItemId = itemId;
            a.Site = site;
            a.Surface = string.IsNullOrEmpty(info.AttachSurface) ? "roof" : info.AttachSurface;   // (a ground item that was put up on a roof: properties.roof_mount)
            a.ProvidesPower = info.ProvidesPower;
            a.Thickness = info.AttachThrough ? (thickness > 0.02f ? thickness : DefaultWall) : 0f;
            a._side = string.IsNullOrEmpty(info.AttachSide) ? "either" : info.AttachSide;
            a._exteriorProbe = site.transform.InverseTransformPoint(worldPos + worldRot * Vector3.forward * 0.1f);
            a.Exterior = info.AttachSurface == "wall" && !site.IsInsideWalls(worldPos + worldRot * Vector3.forward * 0.1f);   // (a first guess: Exterior measures again once the building's walls are known)
            WireNode.Attach(obj, itemId);        // a device the solar chain wires together
            LightEmitter.Attach(obj, itemId, info.Lights);
            NetRack.AttachIfRack(a);             // a wall rack: routers and switches slide into it
            if (Shelf.AttachIfShelf(a) == null && itemId.Contains("shelf")) Debug.LogWarning("[Shelf] " + itemId + " was mounted but the catalog does not mark it as a shelf (properties.shelf)");   // a wall shelf: things stand on it
            return a;
        }

        // ------------------------------------------------------------------ taking one down

        /// <summary>A right click on an attached item (within reach) takes it down into the toolbar. True when the click was for one.</summary>
        /// <summary>The mounted item under the ray when it is nearer than <paramref name="maxDistance"/> (the first solid thing), else null. Other triggers are looked past.</summary>
        public static AttachedObject UnderRay(Ray ray, float maxDistance)
        {
            if (All.Count == 0) return null;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.distance > maxDistance) break;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                AttachedObject a = h.collider.GetComponentInParent<AttachedObject>();
                if (a != null) return a;
            }
            return null;
        }

        /// <summary>True when the first thing under the ray is a mounted object (a light, a breaker box) that a right click would take down. Acts on nothing.</summary>
        public static bool IsUnderRay(Ray ray)
        {
            if (All.Count == 0) return false;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                bool mine = h.collider.GetComponentInParent<AttachedObject>() != null;
                if (!mine && h.collider.isTrigger) continue;   // the click box of something else (a light, a zone): look past it
                return mine;
            }
            return false;
        }

        /// <summary>
        /// A right click on a mounted rack (a roof mount) with the item it takes in hand (its manifest's attach_item, a solar panel): the panel is fitted and the rack
        /// becomes the rack with its panel (attach_result), where it stands. From the ground: only the distance to the building counts. False when the click is not for that.
        /// </summary>
        public static bool TryFitAtRay(Ray ray, Vector3 playerPos)
        {
            string held = ConstructionSite.HeldItem();
            if (string.IsNullOrEmpty(held) || All.Count == 0) return false;
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                AttachedObject a = h.collider.GetComponentInParent<AttachedObject>();
                if (a == null && h.collider.isTrigger) continue;   // a click box or zone that is not a mounted item: look past it
                if (a == null) return false;   // something else is in front
                if (!ItemRegistry.TryGet(a.ItemId, out ItemRegistry.ItemInfo mount) || string.IsNullOrEmpty(mount.AttachItem) || mount.AttachItem != held) return false;
                if (a.GetComponent<MountedPanel>() != null) return false;   // it has its panel
                if (a.Site != null && a.Site.DistanceOutside(playerPos) > 6f)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to the building.");
                    return true;
                }
                HudState hud = HudState.Active;
                if (hud == null || !hud.ConsumeFromSelectedSlot(1)) return true;
                HudBindings.Instance?.RefreshToolbar();
                MountedPanel.Fit(a.gameObject, a.ItemId, held);
                return true;
            }
            return false;
        }

        /// <summary>True while a wrench is in the active slot and Shift is held: what takes a mounted item (on a wall, a ceiling or a roof) down.</summary>
        public static bool WrenchRemoval()
        {
            string held = ConstructionSite.HeldItem();
            bool wrench = held == "tool_wrench_adjustable" || held == "tool_wrench_pipe";
            return wrench && UnityEngine.InputSystem.Keyboard.current != null && UnityEngine.InputSystem.Keyboard.current.shiftKey.isPressed;
        }

        /// <summary>A wrench (adjustable or pipe) is in the active slot, Shift or not: what takes up a placed item that is bolted down (properties.wrench_remove).</summary>
        public static bool WrenchInHand()
        {
            string held = ConstructionSite.HeldItem();
            return held == "tool_wrench_adjustable" || held == "tool_wrench_pipe";
        }

        public static bool TryPickUpAtRay(Ray ray, Vector3 playerPos)
        {
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                AttachedObject a = h.collider.GetComponentInParent<AttachedObject>();
                if (a == null && h.collider.isTrigger) continue;   // a click box or zone that is not a mounted item: look past it
                if (a == null) return false;   // something else is in front
                if (!WrenchRemoval())
                {
                    ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(a.ItemId), "Take it down with a wrench: Shift + right click.");
                    return true;
                }
                if (new Vector2(a.transform.position.x - playerPos.x, a.transform.position.z - playerPos.z).magnitude > 4f)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to take it down.");
                    return true;
                }
                NetRack rackOn = a.GetComponent<NetRack>();
                if (rackOn != null && rackOn.Items.Count > 0)
                {
                    ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(a.ItemId), "Take what is in the rack out first.");
                    return true;
                }
                Shelf shelf = a.GetComponent<Shelf>();
                if (shelf != null && shelf.Items.Count > 0)
                {
                    ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(a.ItemId), "Take what is on the shelf off first.");
                    return true;
                }
                HudState hud = HudState.Active;
                if (hud == null) return false;
                if (hud.AddItemToToolbar(a.ItemId, 1, HudBindings.GetMaxStack(a.ItemId)) < 1)
                {
                    ToastNotificationSystem.ShowWarning("Toolbar full", "No room to take it down.");
                    return true;
                }
                string panelOn = MountedPanel.PanelOn(a.gameObject);
                if (panelOn != null) hud.AddItemToToolbar(panelOn, 1, HudBindings.GetMaxStack(panelOn));   // the panel comes down with its rack
                HudBindings.Instance?.RefreshToolbar();
                bool hadPower = a.ProvidesPower;
                Destroy(a.gameObject);
                if (hadPower) ToastNotificationSystem.ShowInfo("Power", "The building has no electricity now.");
                return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ saving

        /// <summary>The mounted objects in the order <see cref="Capture"/> saves them (the wiring refers to them by their place in it).</summary>
        public static List<AttachedObject> CaptureOrder()
        {
            var list = new List<AttachedObject>();
            foreach (AttachedObject a in All)
            {
                if (a == null || a.Site == null) continue;
                if (ConstructionSite.All.IndexOf(a.Site) < 0) continue;
                list.Add(a);
            }
            return list;
        }

        public static List<GameSave.SavedAttached> Capture()
        {
            var list = new List<GameSave.SavedAttached>();
            foreach (AttachedObject a in CaptureOrder())
            {
                int idx = ConstructionSite.All.IndexOf(a.Site);
                Transform t = a.transform;
                Shelf shelf = a.GetComponent<Shelf>();
                List<string> shelfIds = null, shelfLiquids = null;
                List<float> shelfX = null, shelfUsed = null;
                if (shelf != null && shelf.Items.Count > 0)
                {
                    shelfIds = new List<string>(); shelfLiquids = new List<string>(); shelfX = new List<float>(); shelfUsed = new List<float>();
                    foreach (Shelf.Held h in shelf.Items) { shelfIds.Add(h.ItemId); shelfX.Add(h.X); shelfUsed.Add(h.WireUsed); shelfLiquids.Add(h.LiquidId ?? ""); }
                }
                NetRack rackIn = a.GetComponent<NetRack>();
                if (rackIn != null && rackIn.Items.Count > 0) shelfIds = new List<string>(rackIn.Items);   // a rack: what is in it, bottom unit first
                list.Add(new GameSave.SavedAttached { shelfIds = shelfIds, shelfX = shelfX, shelfUsed = shelfUsed, shelfLiquids = shelfLiquids, itemId = a.ItemId, siteIndex = idx, localPosition = a.Site.transform.InverseTransformPoint(t.position), localRotation = Quaternion.Inverse(a.Site.transform.rotation) * t.rotation, thickness = a.Thickness, panelId = MountedPanel.PanelOn(a.gameObject), chargeWh = a.GetComponent<WireNode>() != null ? a.GetComponent<WireNode>().ChargeWh : 0f, switchOff = a.GetComponent<WireNode>() != null && a.GetComponent<WireNode>().SwitchOff });
            }
            return list;
        }
    }
}
