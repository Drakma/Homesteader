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
            new GameObject("PlacementController").AddComponent<PlacementController>();
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
            cell.y = GroundY(cell);

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
            if (!state.ConsumeFromSelectedSlot(1)) return;
            HudBindings.Instance.RefreshToolbar();

            SpawnPlaced(itemId, info, cell, rotationSteps * GameRules.Placement.RotateStepDeg, true);
        }

        private static Transform s_placedRoot;

        /// <summary>
        /// Creates a placed object from a loaded model template. fade = true starts as the translucent shadow and
        /// fades to solid (a fresh placement); false is a solid object at once (restoring a save).
        /// </summary>
        public static PlacedObject SpawnPlaced(string itemId, ItemRegistry.ItemInfo info, Vector3 cell, float yawDeg, bool fade)
        {
            if (s_placedRoot == null) s_placedRoot = new GameObject("PlacedObjects").transform;
            GameObject obj = Instantiate(info.Prefab, s_placedRoot);
            obj.SetActive(true);                       // templates live inactive
            obj.transform.SetPositionAndRotation(cell, Quaternion.Euler(0f, yawDeg, 0f));
            var placed = obj.AddComponent<PlacedObject>();
            placed.Init(itemId, cell, yawDeg);
            LightEmitter.Attach(obj, itemId, info.Lights);   // its lights come on with the game clock
            if (fade)
            {
                GhostVisual.Apply(obj, ValidTint, GhostAlpha);
                placed.StartCoroutine(placed.FadeToSolid(ValidTint, GhostAlpha, 0.4f));
            }
            return placed;
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
            if (PlacedObject.At(cell) != null)
            {
                reason = "Something is already placed in that square.";
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
            if (!GameRules.Placement.Categories.Contains(info.Category ?? "")) return false;
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
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, ~0, QueryTriggerInteraction.Ignore);
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
            Terrain t = Terrain.activeTerrain;
            if (t != null) return t.SampleHeight(p) + t.transform.position.y;
            return Physics.Raycast(p + Vector3.up * 50f, Vector3.down, out RaycastHit hit, 200f) ? hit.point.y : p.y;
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
            Terrain t = Terrain.activeTerrain;
            return HomesteaderTerrainGenerator.WaterLevel + (t != null ? t.transform.position.y : 0f);
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
            return kb != null && kb.rKey.wasPressedThisFrame;
#else
            reverse = Input.GetKey(KeyCode.LeftShift);
            return Input.GetKeyDown(KeyCode.R);
#endif
        }
    }

    /// <summary>A structure or prop the player placed. Permanent: it stays until something calls <see cref="Remove"/>.</summary>
    public sealed class PlacedObject : MonoBehaviour
    {
        private static readonly Dictionary<Vector2Int, PlacedObject> cells = new Dictionary<Vector2Int, PlacedObject>();
        public static IEnumerable<PlacedObject> All => cells.Values;

        public string ItemId { get; private set; }
        public float YawDeg { get; private set; }
        private Vector2Int cell;

        public void Init(string itemId, Vector3 position, float yawDeg)
        {
            ItemId = itemId;
            YawDeg = yawDeg;
            cell = CellOf(position);
            cells[cell] = this;
        }

        /// <summary>The placed object standing in the grid square containing the point, if any.</summary>
        public static PlacedObject At(Vector3 point)
        {
            return cells.TryGetValue(CellOf(point), out PlacedObject p) && p != null ? p : null;
        }

        /// <summary>Takes it out of the world and frees its square (call from a demolish tool / any gameplay rule).</summary>
        public void Remove()
        {
            if (cells.TryGetValue(cell, out PlacedObject p) && p == this) cells.Remove(cell);
            Destroy(gameObject);
        }

        private void OnDestroy()
        {
            if (cells.TryGetValue(cell, out PlacedObject p) && p == this) cells.Remove(cell);
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
