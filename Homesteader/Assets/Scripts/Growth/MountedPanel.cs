using UnityEngine;
using Homesteader.Modding;
using Homesteader.UI;

namespace Homesteader.Growth
{
    /// <summary>
    /// A solar panel fitted on a mount (a roof or a ground rack). The panel stays its own item: fitting consumes one, its own model is placed on the rack at the pose the mount's
    /// manifest gives (panel_offset_m up, panel_tilt_deg about the X axis), and taking the mount down returns both.
    /// </summary>
    public sealed class MountedPanel : MonoBehaviour
    {
        public string PanelItemId { get; private set; }

        /// <summary>Fits <paramref name="panelId"/> on the mount object. False when it already has one or the panel has no model.</summary>
        public static bool Fit(GameObject mount, string mountId, string panelId)
        {
            if (mount == null || mount.GetComponent<MountedPanel>() != null) return false;
            if (!ItemRegistry.TryGet(panelId, out ItemRegistry.ItemInfo panel) || panel.Prefab == null) return false;
            var mp = mount.AddComponent<MountedPanel>();
            mp.PanelItemId = panelId;
            mp.StartCoroutine(mp.Build(mountId, panel.Prefab));
            return true;
        }

        /// <summary>The panel's model is loaded from its file the first time it is asked for: wait for it, then put it on the rack (a copy made before it arrives would be empty).</summary>
        private System.Collections.IEnumerator Build(string mountId, GameObject prefab)
        {
            GlbTemplate tpl = prefab.GetComponent<GlbTemplate>();
            if (tpl != null)
            {
                tpl.EnsureLoading();
                float until = Time.realtimeSinceStartup + 15f;
                while (!tpl.Ready && !tpl.Failed && Time.realtimeSinceStartup < until) yield return null;
                if (!tpl.Ready) yield break;
            }
            GameObject model = Place(transform, mountId, prefab, "FittedPanel");
            AddPickBox(model, true);   // a trigger: a solid box over a ground rack's panel could be walked up
            PlacedObject po = GetComponent<PlacedObject>();
            if (po != null) NoClimb.AttachIfGroundRack(po);   // now the panel is on, the wall around it covers it
        }

        /// <summary>
        /// The panel's own colliders are removed (it must not block), so the rack's box was all there was to click, and the rack is narrower than its panel: the visible panel could not be
        /// hovered, wired or taken down except over the rack. One box over the whole panel (a trigger on a mounted rack, solid on a ground rack) makes the panel itself the target.
        /// </summary>
        private static void AddPickBox(GameObject model, bool trigger)
        {
            if (model == null) return;
            bool any = false;
            Bounds lb = default;
            foreach (Renderer r in model.GetComponentsInChildren<Renderer>())
            {
                Bounds wb = r.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = wb.center + new Vector3((i & 1) == 0 ? -wb.extents.x : wb.extents.x, (i & 2) == 0 ? -wb.extents.y : wb.extents.y, (i & 4) == 0 ? -wb.extents.z : wb.extents.z);
                    Vector3 local = model.transform.InverseTransformPoint(corner);
                    if (!any) { lb = new Bounds(local, Vector3.zero); any = true; } else lb.Encapsulate(local);
                }
            }
            if (!any) return;
            var box = model.AddComponent<BoxCollider>();
            box.isTrigger = trigger;
            box.center = lb.center;
            box.size = Vector3.Max(lb.size, new Vector3(0.05f, 0.05f, 0.05f));
        }

        // ------------------------------------------------------------------ the preview

        private static GameObject s_preview;
        private static Transform s_previewMount;

        /// <summary>With a panel in hand and the cursor over a mount that takes it, the panel shows on the rack where it would go; it goes away when the cursor leaves or the item changes.</summary>
        private sealed class Previewer : MonoBehaviour
        {
            private float _next;

            private void Update()
            {
                if (Time.unscaledTime < _next) return;
                _next = Time.unscaledTime + 0.1f;   // ten times a second is plenty for a preview
                GameObject mount = null;
                string held = ConstructionSite.HeldItem();
                Camera cam = HoverTarget.GameCamera();
                if (!string.IsNullOrEmpty(held) && cam != null && !HudBindings.KeyboardCaptured)
                {
                    Vector2 pointer = UnityEngine.InputSystem.Mouse.current != null ? UnityEngine.InputSystem.Mouse.current.position.ReadValue() : Vector2.zero;
                    PlacedObject placed = PlacementController.PlacedUnderCursor();
                    GameObject cand = placed != null ? placed.gameObject : null;
                    if (cand == null)
                    {
                        RaycastHit[] hits = HoverTarget.SortedHits(cam, pointer);
                        float max = hits.Length > 0 ? hits[0].distance : float.MaxValue;
                        AttachedObject a = AttachedObject.UnderRay(cam.ScreenPointToRay(pointer), max);
                        if (a != null) cand = a.gameObject;
                    }
                    if (cand != null && cand.GetComponent<MountedPanel>() == null)
                    {
                        string mountId = cand.GetComponent<AttachedObject>() != null ? cand.GetComponent<AttachedObject>().ItemId : (cand.GetComponent<PlacedObject>() != null ? cand.GetComponent<PlacedObject>().ItemId : null);
                        if (mountId != null && ItemRegistry.TryGet(mountId, out ItemRegistry.ItemInfo mi) && mi.AttachItem == held) mount = cand;
                    }
                }
                if (mount == null) { Clear(); return; }
                if (s_preview != null && s_previewMount == mount.transform) return;
                Clear();
                string id = mount.GetComponent<AttachedObject>() != null ? mount.GetComponent<AttachedObject>().ItemId : mount.GetComponent<PlacedObject>().ItemId;
                if (!ItemRegistry.TryGet(held, out ItemRegistry.ItemInfo panel) || panel.Prefab == null) return;
                GlbTemplate tpl = panel.Prefab.GetComponent<GlbTemplate>();
                if (tpl != null && !tpl.Ready) { tpl.EnsureLoading(); return; }   // still loading: tried again next frame
                s_preview = Place(mount.transform, id, panel.Prefab, "PanelPreview");
                s_previewMount = mount.transform;
            }

            private static void Clear()
            {
                if (s_preview != null) Destroy(s_preview);
                s_preview = null;
                s_previewMount = null;
            }
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<Previewer>() != null) return;
            var go = new GameObject("MountedPanelPreview");
            DontDestroyOnLoad(go);
            go.AddComponent<Previewer>();
        }

        /// <summary>The panel model on a mount at the pose its manifest gives.</summary>
        private static GameObject Place(Transform mount, string mountId, GameObject prefab, string name)
        {
            AssetCatalogItem m = HudBindings.GetCatalogItem(mountId);
            GameObject model = Instantiate(prefab, mount);
            model.name = name;
            model.SetActive(true);
            foreach (Collider c in model.GetComponentsInChildren<Collider>(true)) Destroy(c);
            // the model's own rotation and scale stay (the loader mirrors the model with a negative scale; resetting it turns the panel inside out and it vanishes)
            Quaternion own = model.transform.localRotation;
            model.transform.localPosition = new Vector3(0f, m != null ? m.panel_offset_m : 0f, 0f);
            model.transform.localRotation = Quaternion.Euler(m != null ? m.panel_tilt_deg : 0f, 0f, 0f) * own;
            return model;
        }

        /// <summary>The panel a mount holds (null for none), for taking down and saving.</summary>
        public static string PanelOn(GameObject mount)
        {
            MountedPanel mp = mount != null ? mount.GetComponent<MountedPanel>() : null;
            return mp != null ? mp.PanelItemId : null;
        }
    }
}
