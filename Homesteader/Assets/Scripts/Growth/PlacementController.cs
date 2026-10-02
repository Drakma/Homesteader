using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Growth
{
    /// <summary>
    /// Placing structures and props. While the selected toolbar item is a placeable asset (its category is listed in
    /// the game rules' placement.categories: structures, electricity, water, ...), a translucent "shadow" copy of
    /// its model follows the grid square under the cursor. Squares within placement.reach_cells of the player
    /// (default 3) are valid (tinted blue), others are not (tinted red). R turns it by placement.rotate_step_deg
    /// (default 12.5 degrees, Shift+R turns the other way). A left click on a valid square consumes one item; the
    /// shadow fades to solid and stays until something removes it (<see cref="PlacedObject.Remove"/>).
    ///
    /// Bootstraps itself after the scene loads, so no scene edit is needed. Keys: docs/CONTROLS.md.
    /// </summary>
    public sealed class PlacementController : MonoBehaviour
    {
        private static readonly Color ValidTint = new Color(0.55f, 0.8f, 1f);
        private static readonly Color InvalidTint = new Color(1f, 0.35f, 0.3f);
        private const float GhostAlpha = 0.45f;

        private string ghostItemId;
        private GameObject ghost;
        private int rotationSteps;
        private Transform placedRoot;
        private string lastReason;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<PlacementController>() != null) return;
            // Survives the scene reload New Game / Continue does: [RuntimeInitializeOnLoadMethod(AfterSceneLoad)] runs
            // only once at startup, so a controller that is not persistent is gone after the first reload and never comes back.
            var go = new GameObject("PlacementController");
            DontDestroyOnLoad(go);
            go.AddComponent<PlacementController>();
        }

        private void Update()
        {
            HudBindings hud = HudBindings.Instance;
            if (hud == null || HudBindings.KeyboardCaptured) { HideGhost(); return; }

            string heldId = HeldItemId();
            if (!IsPlaceable(heldId) || !ItemRegistry.TryGet(heldId, out ItemRegistry.ItemInfo info)) { HideGhost(); return; }

            if (RotatePressed(out bool reverse))
                rotationSteps += reverse ? -1 : 1;

            Vector2 pointer = PointerPosition();
            Camera cam = GameCamera();
            if (cam == null || hud.IsPointerOverUI(pointer)) { HideGhost(); return; }

            if (!TryCursorPoint(cam, pointer, out Vector3 hitPoint)) { HideGhost(); return; }
            Vector3 cell = PlantingValidator.SnapToGrid(hitPoint);
            cell.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(cell);
            // Stackable containers: an identical container already standing here is built on, not refused.
            PlacedObject below = PlacedObject.At(cell);
            if (below != null && CanStack(below, heldId)) cell.y = below.transform.position.y + below.Height;

            if (!EnsureGhost(heldId, info)) return;   // model still loading

            var ped = FindAnyObjectByType<PedController>();
            bool valid = Validate(cell, ped != null ? ped.transform : null, out string reason);
            lastReason = reason;

            ghost.SetActive(true);
            ghost.transform.position = cell;
            ghost.transform.rotation = Quaternion.Euler(0f, rotationSteps * GameRules.Placement.RotateStepDeg, 0f);
            GhostVisual.Apply(ghost, valid ? ValidTint : InvalidTint, GhostAlpha);

            if (PlaceClicked())
            {
                if (!valid) { ToastNotificationSystem.ShowWarning("Can't place here", reason); return; }
                Place(heldId, info, cell, ghost.transform.rotation);
            }
        }

        // ------------------------------------------------------------------ placing

        private void Place(string itemId, ItemRegistry.ItemInfo info, Vector3 cell, Quaternion rotation)
        {
            HudState state = HudState.Active;
            // A container keeps what is in it when it is put down.
            List<ContainerStack> contents = state.SelectedSlot >= 0 && state.SelectedSlot < state.Toolbar.Count ? state.Toolbar[state.SelectedSlot].Contents : null;
            PlacedObject below = PlacedObject.At(cell);
            int level = below != null && CanStack(below, itemId) ? below.Level + 1 : 0;
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance.RefreshToolbar();

            SpawnPlaced(itemId, info, cell, rotationSteps * GameRules.Placement.RotateStepDeg, true, level, contents);
        }

        private static Transform s_placedRoot;

        /// <summary>
        /// Creates a placed object from a loaded model template. fade = true starts as the translucent shadow and
        /// fades to solid (a fresh placement); false is a solid object at once (restoring a save).
        /// </summary>
        public static PlacedObject SpawnPlaced(string itemId, ItemRegistry.ItemInfo info, Vector3 cell, float yawDeg, bool fade, int level = 0, List<ContainerStack> contents = null)
        {
            if (s_placedRoot == null) s_placedRoot = new GameObject("PlacedObjects").transform;
            // Snap to the terrain surface (just above, not 3 m above); a container stacked on another keeps the height it was given.
            if (level <= 0) cell = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(cell);
            GameObject obj = Instantiate(info.Prefab, s_placedRoot);
            obj.SetActive(true);                       // templates live inactive
            obj.transform.SetPositionAndRotation(cell, Quaternion.Euler(0f, yawDeg, 0f));
            var placed = obj.AddComponent<PlacedObject>();
            placed.Init(itemId, cell, yawDeg, level);
            if (contents != null) placed.Contents = new List<ContainerStack>(contents);
            LightEmitter.Attach(obj, itemId, info.Lights);   // its lights come on with the game clock
            if (fade)
            {
                GhostVisual.Apply(obj, ValidTint, GhostAlpha);
                placed.StartCoroutine(placed.FadeToSolid(ValidTint, GhostAlpha, 0.4f));
            }
            return placed;
        }

        /// <summary>An identical stackable container can be put on top of this one while the stack is under its limit.</summary>
        public static bool CanStack(PlacedObject below, string itemId)
        {
            return below != null && !string.IsNullOrEmpty(itemId) && below.ItemId == itemId && ContainerRules.StackingLimit(itemId) > below.Level + 1;
        }

        /// <summary>The placed object under the mouse pointer (a direct hit on its collider), or null.</summary>
        public static PlacedObject PlacedUnderCursor()
        {
            Camera cam = GameCamera();
            if (cam == null) return null;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(PointerPosition()), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                PlacedObject p = h.collider.GetComponentInParent<PlacedObject>();
                if (p != null) return p;
                return null;   // something else is in front
            }
            return null;
        }

        private bool Validate(Vector3 cell, Transform player, out string reason)
        {
            reason = null;
            if (!PlantingValidator.InReach(player, cell, GameRules.Placement.ReachCells))
            {
                reason = $"You can only place things within {GameRules.Placement.ReachCells} squares of you.";
                return false;
            }
            if (cell.y < WaterY() + 0.05f)
            {
                reason = "You can't build in water.";
                return false;
            }
            if (SlopeAt(cell) > GameRules.Planting.MaxSlopeDeg)
            {
                reason = "The ground is too steep here.";
                return false;
            }
            PlacedObject here = PlacedObject.At(cell);
            if (here != null && !CanStack(here, HeldItemId()))
            {
                reason = here.ItemId == HeldItemId() && ContainerRules.StackingLimit(here.ItemId) > 1 ? "That stack is as high as it goes." : "Something is already placed in that square.";
                return false;
            }
            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null) continue;
                Vector3 c = p.transform.position;
                float g = PlantingValidator.GridSizeM;
                if (Mathf.Floor(c.x / g) == Mathf.Floor(cell.x / g) && Mathf.Floor(c.z / g) == Mathf.Floor(cell.z / g))
                {
                    reason = "Something is growing in that square.";
                    return false;
                }
            }
            return true;
        }

        // ------------------------------------------------------------------ ghost

        /// <summary>Makes sure the shadow for this item exists; false while its GLB is still loading.</summary>
        private bool EnsureGhost(string itemId, ItemRegistry.ItemInfo info)
        {
            if (ghost != null && ghostItemId == itemId) return true;
            DestroyGhost();

            GlbTemplate glb = info.Prefab.GetComponent<GlbTemplate>();
            if (glb != null)
            {
                glb.EnsureLoading();
                if (glb.Failed) return false;
                if (!glb.Ready) return false;
            }

            ghost = Instantiate(info.Prefab);
            ghost.name = "PlacementGhost_" + itemId;
            ghost.SetActive(true);
            // The shadow is walk-through and never blocks the cursor ray.
            foreach (Collider c in ghost.GetComponentsInChildren<Collider>(true)) Destroy(c);
            ghostItemId = itemId;
            return true;
        }

        private void HideGhost()
        {
            if (ghost != null) ghost.SetActive(false);
        }

        private void DestroyGhost()
        {
            if (ghost != null) Destroy(ghost);
            ghost = null;
            ghostItemId = null;
        }

        private void OnDisable() => DestroyGhost();

        // ------------------------------------------------------------------ helpers

        private static string HeldItemId()
        {
            HudState state = HudState.Active;
            if (state == null || state.SelectedSlot < 0 || state.SelectedSlot >= state.Toolbar.Count) return null;
            ToolbarSlotData slot = state.Toolbar[state.SelectedSlot];
            return !string.IsNullOrEmpty(slot.IconId) && slot.Count > 0 ? slot.IconId : null;
        }

        /// <summary>A placeable asset: its category is in the placement rules, and it is not a seed that plants a group.</summary>
        public static bool IsPlaceable(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return false;
            if (!ItemRegistry.TryGet(itemId, out ItemRegistry.ItemInfo info)) return false;
            // Stackable containers (boxes) can be put down in the world whatever their category; other items follow the placement rules.
            if (!GameRules.Placement.Categories.Contains(info.Category ?? "") && ContainerRules.StackingLimit(itemId) <= 1) return false;
            return !GrowthRegistry.TryGetGroupPlantedBy(itemId, out _);
        }

        private Transform PlacedRoot()
        {
            if (placedRoot == null) placedRoot = new GameObject("PlacedObjects").transform;
            return placedRoot;
        }

        /// <summary>The ground point under the cursor, ignoring the player and the shadow itself.</summary>
        private static bool TryCursorPoint(Camera cam, Vector2 screenPos, out Vector3 point)
        {
            point = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                // Aim at the ground behind a placed object so its square (not the object's top) is picked.
                if (h.collider.GetComponentInParent<PlacedObject>() != null) continue;
                point = h.point;
                return true;
            }
            return false;
        }

        private static float GroundY(Vector3 p)
        {
            return Homesteader.Generation.TerrainHeightDetector.GetGroundY(p);
        }

        private static float SlopeAt(Vector3 p)
        {
            float h = GroundY(p);
            float dx = GroundY(p + Vector3.right) - h;
            float dz = GroundY(p + Vector3.forward) - h;
            return Mathf.Atan(Mathf.Sqrt(dx * dx + dz * dz)) * Mathf.Rad2Deg;
        }

        private static float WaterY()
        {
            return Homesteader.Generation.TerrainHeightDetector.GetWaterY();
        }

        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;
            var iso = FindAnyObjectByType<IsometricLockedCamera>();
            if (iso != null && iso.TryGetComponent(out cam)) return cam;
            return FindAnyObjectByType<Camera>();
        }

        private static Vector2 PointerPosition()
        {
#if ENABLE_INPUT_SYSTEM
            return Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
#else
            return Input.mousePosition;
#endif
        }

        private static bool PlaceClicked()
        {
#if ENABLE_INPUT_SYSTEM
            return Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame;
#else
            return Input.GetMouseButtonDown(0);
#endif
        }

        private static bool RotatePressed(out bool reverse)
        {
#if ENABLE_INPUT_SYSTEM
            Keyboard kb = Keyboard.current;
            reverse = kb != null && kb.shiftKey.isPressed;
            return Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PlaceRotate);
#else
            reverse = Input.GetKey(KeyCode.LeftShift);
            return Input.GetKeyDown(KeyCode.R);
#endif
        }
    }

    /// <summary>A structure or prop the player placed. Permanent: it stays until something calls <see cref="Remove"/>.</summary>
    public sealed class PlacedObject : MonoBehaviour
    {
        // Each grid square holds a stack of placed objects, bottom first (one object unless it is a stackable container).
        private static readonly Dictionary<Vector2Int, List<PlacedObject>> stacks = new Dictionary<Vector2Int, List<PlacedObject>>();
        public static IEnumerable<PlacedObject> All
        {
            get
            {
                var all = new List<PlacedObject>();
                foreach (List<PlacedObject> l in stacks.Values) all.AddRange(l);
                return all;
            }
        }

        public string ItemId { get; private set; }
        public float YawDeg { get; private set; }
        public int Level { get; private set; }         // 0 = on the ground, 1 = on top of one box, ...
        public float Height { get; private set; }      // the model's height in metres (what the next one in a stack sits on)
        public List<ContainerStack> Contents = new List<ContainerStack>();   // what a placed container holds
        private Vector2Int cell;

        public bool IsTopOfStack => stacks.TryGetValue(cell, out List<PlacedObject> l) && l.Count > 0 && l[l.Count - 1] == this;

        public void Init(string itemId, Vector3 position, float yawDeg, int level = 0)
        {
            ItemId = itemId;
            YawDeg = yawDeg;
            Level = level;
            cell = CellOf(position);
            if (!stacks.TryGetValue(cell, out List<PlacedObject> list)) { list = new List<PlacedObject>(); stacks[cell] = list; }
            list.Add(this);
            list.Sort((a, b) => a.Level.CompareTo(b.Level));

            var renderers = GetComponentsInChildren<Renderer>();
            if (renderers.Length > 0)
            {
                Bounds b = renderers[0].bounds;
                for (int i = 1; i < renderers.Length; i++) b.Encapsulate(renderers[i].bounds);
                Height = b.size.y;
            }
        }

        /// <summary>The placed object on top of the stack in the grid square containing the point, if any.</summary>
        public static PlacedObject At(Vector3 point)
        {
            return stacks.TryGetValue(CellOf(point), out List<PlacedObject> l) && l.Count > 0 && l[l.Count - 1] != null ? l[l.Count - 1] : null;
        }

        /// <summary>Takes it out of the world and frees its square (call from a demolish tool / any gameplay rule).</summary>
        public void Remove()
        {
            Unregister();
            Destroy(gameObject);
        }

        private void OnDestroy() => Unregister();

        private void Unregister()
        {
            if (!stacks.TryGetValue(cell, out List<PlacedObject> list)) return;
            list.Remove(this);
            list.RemoveAll(p => p == null);
            if (list.Count == 0) stacks.Remove(cell);
        }

        private static Vector2Int CellOf(Vector3 p)
        {
            float g = PlantingValidator.GridSizeM;
            return new Vector2Int(Mathf.FloorToInt(p.x / g), Mathf.FloorToInt(p.z / g));
        }

        /// <summary>Raises the shadow's opacity to solid, then puts the real materials back.</summary>
        public System.Collections.IEnumerator FadeToSolid(Color tint, float fromAlpha, float seconds)
        {
            for (float t = 0f; t < seconds; t += Time.deltaTime)
            {
                GhostVisual.Apply(gameObject, Color.Lerp(tint, Color.white, t / seconds), Mathf.Lerp(fromAlpha, 1f, t / seconds));
                yield return null;
            }
            GhostVisual.Restore(gameObject);
        }
    }

    /// <summary>Turns a model translucent and tinted (an unlit copy of each material keeping its texture), and back.</summary>
    public static class GhostVisual
    {
        private sealed class Originals : MonoBehaviour
        {
            public readonly Dictionary<Renderer, Material[]> Shared = new Dictionary<Renderer, Material[]>();
            public readonly List<Material> Made = new List<Material>();
        }

        public static void Apply(GameObject go, Color tint, float alpha)
        {
            Originals o = go.GetComponent<Originals>();
            if (o == null)
            {
                o = go.AddComponent<Originals>();
                Shader sh = Shader.Find("Universal Render Pipeline/Unlit");
                foreach (Renderer r in go.GetComponentsInChildren<Renderer>(true))
                {
                    if (r is ParticleSystemRenderer) continue;
                    Material[] src = r.sharedMaterials;
                    o.Shared[r] = src;
                    var made = new Material[src.Length];
                    for (int i = 0; i < src.Length; i++)
                    {
                        var m = new Material(sh) { name = "Ghost" };
                        Texture tex = src[i] != null && src[i].HasProperty("_BaseMap") ? src[i].GetTexture("_BaseMap")
                                    : src[i] != null ? src[i].mainTexture : null;
                        if (tex != null) m.SetTexture("_BaseMap", tex);
                        m.SetFloat("_Surface", 1f);
                        m.SetFloat("_Blend", 0f);
                        m.SetFloat("_ZWrite", 0f);
                        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                        m.SetOverrideTag("RenderType", "Transparent");
                        m.renderQueue = 3000;
                        made[i] = m;
                        o.Made.Add(m);
                    }
                    r.sharedMaterials = made;
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                }
            }
            var c = new Color(tint.r, tint.g, tint.b, alpha);
            foreach (Material m in o.Made) m.SetColor("_BaseColor", c);
        }

        public static void Restore(GameObject go)
        {
            Originals o = go.GetComponent<Originals>();
            if (o == null) return;
            foreach (var kv in o.Shared)
            {
                if (kv.Key == null) continue;
                kv.Key.sharedMaterials = kv.Value;
                kv.Key.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            }
            foreach (Material m in o.Made) if (m != null) Object.Destroy(m);
            Object.Destroy(o);
        }
    }
}
