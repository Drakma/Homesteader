using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader
{
    /// <summary>
    /// Faint glowing outline on whatever world object is under the cursor
    /// (trees, animals, structures, items). Rendering is a screen-space effect
    /// (see OutlineRendererFeature.cs): this component's only job is to move the
    /// hovered object's renderers onto the Outline layer so that feature picks
    /// them up, and move them back when the hover ends. Nothing here touches
    /// materials or geometry, so it works on any glTFast-loaded GLB unmodified.
    ///
    /// Bootstraps itself after the scene loads, so no scene edit is needed.
    /// </summary>
    public sealed class HoverOutline : MonoBehaviour
    {
        private const string OutlineLayerName = "Outline";
        // OutlineRendererFeature selects layer 8 by number (1 << 8). The layer does not need a NAME to work, so if the
        // project has no layer called "Outline" (Unity's layer names are easy to lose) layer 8 is used directly.
        private const int OutlineLayerNumber = 8;

        private Transform currentHover;
        private readonly List<(Transform t, int layer)> savedLayers = new();
        private int outlineLayer = -1;
        private bool outlineToggledOn = true; // F4 toggle

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<HoverOutline>() != null) return;
            new GameObject("HoverOutline").AddComponent<HoverOutline>();
        }

        private void Awake()
        {
            outlineLayer = ResolveLayer();
        }

        private static int ResolveLayer()
        {
            int named = LayerMask.NameToLayer(OutlineLayerName);
            return named >= 0 ? named : OutlineLayerNumber;
        }

        private void Update()
        {

            bool f4Pressed;
#if ENABLE_INPUT_SYSTEM
            f4Pressed = UnityEngine.InputSystem.Keyboard.current != null
                && UnityEngine.InputSystem.Keyboard.current.f4Key.wasPressedThisFrame;
#else
            f4Pressed = Input.GetKeyDown(KeyCode.F4);
#endif
            if (f4Pressed)
            {
                outlineToggledOn = !outlineToggledOn;
                ToastNotificationSystem.ShowInfo("Hover outline",
                    outlineLayer < 0 ? "Unavailable: the 'Outline' layer is missing (Project Settings > Tags and Layers)"
                                     : (outlineToggledOn ? "On" : "Off"));
            }
            if (outlineLayer < 0) return;

            if (!outlineToggledOn)
            {
                SetHover(null);
                return;
            }

            if (!TryGetPointerPos(out Vector2 screenPos))
            {
                SetHover(null);
                return;
            }

            HudBindings hud = HudBindings.Instance;
            if (hud != null && (HudBindings.KeyboardCaptured || hud.IsPointerOverUI(screenPos)))
            {
                SetHover(null);
                return;
            }

            Camera cam = GameCamera();
            if (cam == null)
            {
                SetHover(null);
                return;
            }

            // Trees/structures/animals have colliders and hit normally. Crops and dropped
            // items deliberately disable theirs (walk-through by design - see
            // PlantedGrowth.ShowModel / WorldItem.TryShow), so they never show up in a
            // physics raycast; fall back to nearest-on-the-ground-plane for those.
            if (TryHoverableHit(cam, screenPos, out RaycastHit hit))
            {
                SetHover(HoverRoot(hit.collider));
                return;
            }

            Transform nearby = TryFindNearbyCropOrItem(cam, screenPos);
            SetHover(nearby);
        }

        /// <summary>
        /// Whether anything is currently outlined. OutlineRendererFeature checks
        /// this to skip its passes entirely on the (vast majority of) frames
        /// where nothing is hovered, instead of running 3 fullscreen shader
        /// passes for nothing every single frame.
        /// </summary>
        public static bool AnyHovered { get; private set; }

        /// <summary>The currently hovered object's root transform (see HoverRoot), or null. Same
        /// target the outline itself uses - WailaPanel reads this instead of re-raycasting.</summary>
        public static Transform Current { get; private set; }

        private void SetHover(Transform next)
        {
            if (next == currentHover) return;

            RestoreLayers();
            currentHover = next;
            AnyHovered = currentHover != null;
            Current = currentHover;
            if (currentHover == null) return;

            foreach (Renderer r in currentHover.GetComponentsInChildren<Renderer>(true))
            {
                savedLayers.Add((r.transform, r.gameObject.layer));
                r.gameObject.layer = outlineLayer;
            }
        }

        private void RestoreLayers()
        {
            foreach ((Transform t, int layer) in savedLayers)
                if (t != null) t.gameObject.layer = layer;
            savedLayers.Clear();
        }

        private void OnDisable()
        {
            RestoreLayers();
            AnyHovered = false;
            Current = null;
        }

        /// <summary>
        /// A collider added by GlbAssetResolver sits on the same GameObject as its
        /// MeshFilter, which for a multi-part model is a leaf part, not the whole
        /// instance - walk up to the GlbTemplate clone's root (present on every
        /// spawned instance, since Instantiate() clones the template's own
        /// component too) so the ENTIRE object outlines, not just one submesh.
        /// Falls back to the collider's own transform for anything that isn't a
        /// GLB instance (e.g. a plain scene prop).
        /// </summary>
        private static Transform HoverRoot(Collider c)
        {
            GlbTemplate tpl = c.GetComponentInParent<GlbTemplate>();
            return tpl != null ? tpl.transform : c.transform;
        }

        /// <summary>The first non-ground, non-player thing under the cursor.</summary>
        private static bool TryHoverableHit(Camera cam, Vector2 screenPos, out RaycastHit result)
        {
            result = default;
            RaycastHit[] hits = Physics.RaycastAll(cam.ScreenPointToRay(screenPos), 1000f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));

            foreach (RaycastHit h in hits)
            {
                if (IsGround(h.collider)) continue;
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                result = h;
                return true;
            }
            return false;
        }

        /// <summary>Matches PlantingValidator's ground check: terrain or the flat scene "Ground".</summary>
        private static bool IsGround(Collider c)
        {
            return c is TerrainCollider || c.gameObject.name == "Ground";
        }

        /// <summary>
        /// Nearest tracked crop or dropped item to wherever the mouse ray hits the ground
        /// plane, within a small radius. Same technique WailaPanel uses for the same
        /// reason: PlantedGrowth/WorldItem colliders are off, so physics can't see them.
        /// </summary>
        private static Transform TryFindNearbyCropOrItem(Camera cam, Vector2 screenPos)
        {
            var groundPlane = new Plane(Vector3.up, Vector3.zero);
            Ray ray = cam.ScreenPointToRay(screenPos);
            if (!groundPlane.Raycast(ray, out float enter)) return null;
            Vector3 hit = ray.GetPoint(enter);

            const float radius = 0.6f;
            float bestDistSq = radius * radius;
            Transform best = null;

            foreach (PlantedGrowth g in PlantedGrowth.All)
            {
                if (g == null) continue;
                float d = (g.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; best = g.transform; }
            }
            if (best != null) return best;

            foreach (WorldItem it in WorldItem.All)
            {
                if (it == null) continue;
                float d = (it.transform.position - hit).sqrMagnitude;
                if (d < bestDistSq) { bestDistSq = d; best = it.transform; }
            }
            return best;
        }

        private static Camera GameCamera()
        {
            Camera cam = Camera.main;
            if (cam != null) return cam;

            var iso = FindAnyObjectByType<IsometricLockedCamera>();
            if (iso != null && iso.TryGetComponent(out cam)) return cam;

            return FindAnyObjectByType<Camera>();
        }

        private static bool TryGetPointerPos(out Vector2 pos)
        {
#if ENABLE_INPUT_SYSTEM
            Mouse m = Mouse.current;
            if (m == null) { pos = default; return false; }
            pos = m.position.ReadValue();
            return true;
#else
            pos = Input.mousePosition;
            return true;
#endif
        }
    }
}
