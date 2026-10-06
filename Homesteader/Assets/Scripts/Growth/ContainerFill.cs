using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Shows what is inside a PLACED open container (a crate, a basket) as simple blocks that rise as it fills: one slab per
    /// kind of item, each as tall as its share of the container's weight capacity, with the item's average colour on the
    /// sides and its icon tiled across the top. A few cubes and quads per container, built only when the contents change and
    /// only drawn near the player, so it costs next to nothing. A container's manifest turns it off with container.show_fill
    /// = false (closed boxes).
    /// </summary>
    public sealed class ContainerFillView : MonoBehaviour
    {
        private const int MaxSlabs = 4;

        private PlacedObject _placed;
        private Transform _root;
        private Bounds _inner;               // the opening, in the container's local space
        private bool _hasInner;
        private int _signature = int.MinValue;
        private bool _shown = true;
        private readonly List<GameObject> _slabs = new List<GameObject>();

        /// <summary>Adds the fill display to a placed container that wants one.</summary>
        public static void AttachIfContainer(PlacedObject placed)
        {
            if (placed == null || !ContainerRules.IsContainer(placed.ItemId)) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(placed.ItemId);
            if (info != null && !info.container_show_fill) return;
            if (placed.GetComponent<ContainerFillView>() != null) return;
            var view = placed.gameObject.AddComponent<ContainerFillView>();
            view._placed = placed;
            ContainerFillSystem.Register(view);
        }

        private void OnDestroy() => ContainerFillSystem.Unregister(this);

        /// <summary>Called a few times a second by the system: near = within drawing range of the player.</summary>
        internal void Tick(bool near)
        {
            if (_placed == null) return;
            if (!near)
            {
                if (_shown) { SetShown(false); }
                return;
            }
            if (!_shown) SetShown(true);
            EnsureBox();

            int sig = Signature(_placed.Contents);
            if (sig == _signature) return;
            if (Rebuild()) _signature = sig;   // not ready yet (the model is still loading): try again on the next tick
        }

        private bool _boxDone;

        /// <summary>
        /// A container with slots (a battery rack) is an open frame: a click between its posts would meet nothing. Once its model has loaded it gets one solid box over its whole
        /// volume, so the batteries can be slid in (a right click anywhere on it) and it can be picked.
        /// </summary>
        private void EnsureBox()
        {
            if (_boxDone) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(_placed.ItemId);
            if (info == null || info.container_slot_pitch_m <= 0f) { _boxDone = true; return; }
            bool any = false;
            Bounds b = default;
            foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name.StartsWith("Fill")) continue;
                Bounds mb = mf.sharedMesh.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = mb.center + new Vector3((i & 1) == 0 ? -mb.extents.x : mb.extents.x, (i & 2) == 0 ? -mb.extents.y : mb.extents.y, (i & 4) == 0 ? -mb.extents.z : mb.extents.z);
                    Vector3 local = transform.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { b = new Bounds(local, Vector3.zero); any = true; } else b.Encapsulate(local);
                }
            }
            if (!any) return;                       // the model has not loaded yet
            var box = gameObject.AddComponent<BoxCollider>();
            box.center = b.center;
            box.size = b.size;
            _boxDone = true;
        }

        private void SetShown(bool on)
        {
            _shown = on;
            foreach (GameObject g in _slabs) if (g != null) g.SetActive(on);
        }

        private static int Signature(List<ContainerStack> contents)
        {
            int h = 17;
            if (contents != null)
                foreach (ContainerStack c in contents) { h = h * 31 + (c.ItemId != null ? c.ItemId.GetHashCode() : 0); h = h * 31 + c.Count; }
            return h;
        }

        /// <summary>Draws the blocks for the current contents. False when the container's model has not loaded yet, so it can be tried again.</summary>
        private bool Rebuild()
        {
            foreach (GameObject g in _slabs) if (g != null) Destroy(g);
            _slabs.Clear();

            List<ContainerStack> contents = _placed.Contents;
            if (contents == null || contents.Count == 0) return true;
            if (!EnsureInner()) return false;

            AssetCatalogItem slotInfo = HudBindings.GetCatalogItem(_placed.ItemId);
            if (slotInfo != null && slotInfo.container_slot_pitch_m > 0f) return BuildModels(slotInfo);   // a rack: the real items, one above the other

            float capacity = ContainerRules.Capacity(_placed.ItemId);
            if (capacity <= 0f) return true;
            float floorY = _inner.min.y, height = _inner.size.y;
            if (height < 0.02f) return true;

            // Heaviest first, the rest folded into the last slab.
            var weights = new List<KeyValuePair<string, float>>();
            foreach (ContainerStack c in contents) weights.Add(new KeyValuePair<string, float>(c.ItemId, ContainerRules.WeightOf(c.ItemId) * c.Count));
            weights.Sort((a, b) => b.Value.CompareTo(a.Value));
            while (weights.Count > MaxSlabs)
            {
                var last = weights[weights.Count - 1];
                weights.RemoveAt(weights.Count - 1);
                weights[weights.Count - 1] = new KeyValuePair<string, float>(weights[weights.Count - 1].Key, weights[weights.Count - 1].Value + last.Value);
            }

            float y = floorY;
            foreach (var w in weights)
            {
                // Never thinner than a visible layer: a handful of light items in a big crate would otherwise be a sliver.
                float h = Mathf.Min(Mathf.Max(height * (w.Value / capacity), 0.04f), floorY + height - y);
                if (h < 0.004f) continue;
                BuildSlab(w.Key, y, h);
                y += h;
            }
            return true;
        }

        /// <summary>
        /// A container with slots (a battery rack): every item inside is drawn as its own model, one above the other, the first at the slot start, each a slot pitch above
        /// the one before, centred on the container. False while a model is still loading, so it is tried again.
        /// </summary>
        private bool BuildModels(AssetCatalogItem info)
        {
            float x = _inner.center.x, z = _inner.center.z;
            float baseY = GetComponentInChildren<Renderer>() != null ? ModelBottom() : 0f;
            int slot = 0;
            foreach (ContainerStack c in _placed.Contents)
            {
                if (c == null || c.Count <= 0 || !ItemRegistry.TryGet(c.ItemId, out ItemRegistry.ItemInfo item) || item.Prefab == null) continue;
                var glb = item.Prefab.GetComponent<Homesteader.Modding.GlbTemplate>();
                if (glb != null)
                {
                    glb.EnsureLoading();
                    if (glb.Failed) continue;
                    if (!glb.Ready) return false;
                }
                for (int i = 0; i < c.Count; i++, slot++)
                {
                    GameObject m = Instantiate(item.Prefab, transform);
                    m.name = "FillModel";
                    m.SetActive(true);
                    m.transform.localPosition = new Vector3(x, baseY + info.container_slot_start_m + slot * info.container_slot_pitch_m, z);
                    m.transform.localRotation = Quaternion.identity;
                    foreach (Collider col in m.GetComponentsInChildren<Collider>(true)) Destroy(col);
                    _slabs.Add(m);
                }
            }
            return true;
        }

        /// <summary>The lowest point of the container's own model in its local space.</summary>
        private float ModelBottom()
        {
            float bottom = float.MaxValue;
            foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name.StartsWith("Fill")) continue;
                Bounds mb = mf.sharedMesh.bounds;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = mb.center + new Vector3((i & 1) == 0 ? -mb.extents.x : mb.extents.x, (i & 2) == 0 ? -mb.extents.y : mb.extents.y, (i & 4) == 0 ? -mb.extents.z : mb.extents.z);
                    bottom = Mathf.Min(bottom, transform.InverseTransformPoint(mf.transform.TransformPoint(corner)).y);
                }
            }
            return bottom == float.MaxValue ? 0f : bottom;
        }

        private void BuildSlab(string itemId, float y, float h)
        {
            FillLook look = FillLook.For(itemId);
            Vector3 size = _inner.size;
            Vector3 centre = new Vector3(_inner.center.x, y + h * 0.5f, _inner.center.z);

            var body = new GameObject("FillSlab");
            body.transform.SetParent(transform, false);
            body.transform.localPosition = centre;
            body.transform.localScale = new Vector3(size.x, h, size.z);
            body.AddComponent<MeshFilter>().sharedMesh = FillLook.CubeMesh;
            var mr = body.AddComponent<MeshRenderer>();
            mr.sharedMaterial = look.SideMaterial;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _slabs.Add(body);

            var top = new GameObject("FillTop");
            top.transform.SetParent(transform, false);
            top.transform.localPosition = new Vector3(centre.x, y + h + 0.002f, centre.z);
            top.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);   // a quad faces -Z by default: lay it flat, facing up
            top.transform.localScale = new Vector3(size.x, size.z, 1f);
            top.AddComponent<MeshFilter>().sharedMesh = FillLook.QuadMesh;
            var tr = top.AddComponent<MeshRenderer>();
            tr.sharedMaterial = look.TopMaterial;
            tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var block = new MaterialPropertyBlock();
            block.SetVector("_BaseMap_ST", new Vector4(Mathf.Max(1f, size.x / 0.12f), Mathf.Max(1f, size.z / 0.12f), 0f, 0f));
            tr.SetPropertyBlock(block);
            _slabs.Add(top);
        }

        /// <summary>The opening of the container in its own local space, from its model's bounds minus the walls and the floor.</summary>
        private bool EnsureInner()
        {
            if (_hasInner) return true;
            bool any = false;
            Bounds b = default;
            foreach (MeshFilter mf in GetComponentsInChildren<MeshFilter>())
            {
                if (mf.sharedMesh == null || mf.name.StartsWith("Fill")) continue;
                Bounds mb = mf.sharedMesh.bounds;
                Vector3 e = mb.extents, c = mb.center;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 corner = c + new Vector3((i & 1) == 0 ? -e.x : e.x, (i & 2) == 0 ? -e.y : e.y, (i & 4) == 0 ? -e.z : e.z);
                    Vector3 local = transform.InverseTransformPoint(mf.transform.TransformPoint(corner));
                    if (!any) { b = new Bounds(local, Vector3.zero); any = true; }
                    else b.Encapsulate(local);
                }
            }
            if (!any) return false;   // the model has not loaded yet; try again next time
            float inset = Mathf.Max(0.025f, 0.06f * Mathf.Min(b.size.x, b.size.z));
            float floorThickness = 0.025f, rimGap = 0.02f;
            Vector3 min = new Vector3(b.min.x + inset, b.min.y + floorThickness, b.min.z + inset);
            Vector3 max = new Vector3(b.max.x - inset, b.max.y - rimGap, b.max.z - inset);
            AssetCatalogItem info = HudBindings.GetCatalogItem(_placed.ItemId);
            if (info != null && info.container_fill_region != null && info.container_fill_region.Length == 6)
            {
                // the manifest says where the opening is (fractions of the model's bounds): a wheelbarrow tub, not the whole barrow
                float[] r = info.container_fill_region;
                min = new Vector3(Mathf.Lerp(b.min.x, b.max.x, r[0]), Mathf.Lerp(b.min.y, b.max.y, r[2]), Mathf.Lerp(b.min.z, b.max.z, r[4]));
                max = new Vector3(Mathf.Lerp(b.min.x, b.max.x, r[1]), Mathf.Lerp(b.min.y, b.max.y, r[3]), Mathf.Lerp(b.min.z, b.max.z, r[5]));
            }
            if (max.x <= min.x || max.y <= min.y || max.z <= min.z) return false;
            _inner = new Bounds((min + max) * 0.5f, max - min);
            _hasInner = true;
            return true;
        }
    }

    /// <summary>Colours and materials for the fill of one kind of item (built once, shared by every container).</summary>
    internal sealed class FillLook
    {
        private static readonly Dictionary<string, FillLook> Cache = new Dictionary<string, FillLook>();
        private static Mesh _cube, _quad;

        public Material SideMaterial;
        public Material TopMaterial;

        public static Mesh CubeMesh { get { if (_cube == null) _cube = Primitive(PrimitiveType.Cube); return _cube; } }
        public static Mesh QuadMesh { get { if (_quad == null) _quad = Primitive(PrimitiveType.Quad); return _quad; } }

        private static Mesh Primitive(PrimitiveType type)
        {
            GameObject go = GameObject.CreatePrimitive(type);
            Mesh m = go.GetComponent<MeshFilter>().sharedMesh;
            Object.Destroy(go);
            return m;
        }

        public static FillLook For(string itemId)
        {
            if (Cache.TryGetValue(itemId, out FillLook look) && look.SideMaterial != null) return look;
            look = new FillLook();
            Texture2D icon = PhoneController.GetItemIcon(null, itemId);
            Color avg = icon != null ? Average(icon) : new Color(0.7f, 0.6f, 0.4f);
            Shader lit = Shader.Find("Universal Render Pipeline/Lit");

            look.SideMaterial = new Material(lit) { name = "FillSide_" + itemId };
            look.SideMaterial.SetColor("_BaseColor", avg * 0.9f);
            look.SideMaterial.SetFloat("_Smoothness", 0.15f);

            look.TopMaterial = new Material(lit) { name = "FillTop_" + itemId };
            look.TopMaterial.SetColor("_BaseColor", Color.white);
            look.TopMaterial.SetFloat("_Smoothness", 0.15f);
            Texture2D tile = icon != null ? Tile(icon, avg) : null;
            if (tile != null) look.TopMaterial.SetTexture("_BaseMap", tile);
            else look.TopMaterial.SetColor("_BaseColor", avg);
            Cache[itemId] = look;
            return look;
        }

        /// <summary>The average colour of the visible pixels of an icon (read through a small render texture, so it works on unreadable textures).</summary>
        private static Color Average(Texture2D icon)
        {
            Texture2D small = Shrink(icon, 8);
            Color32[] px = small.GetPixels32();
            float r = 0f, g = 0f, b = 0f, n = 0f;
            foreach (Color32 c in px)
            {
                if (c.a < 128) continue;
                r += c.r; g += c.g; b += c.b; n += 1f;
            }
            Object.Destroy(small);
            return n > 0f ? new Color(r / n / 255f, g / n / 255f, b / n / 255f, 1f) : new Color(0.7f, 0.6f, 0.4f);
        }

        /// <summary>The icon over its own average colour, opaque, so transparent corners do not show as black on the top face.</summary>
        private static Texture2D Tile(Texture2D icon, Color background)
        {
            Texture2D src = Shrink(icon, 64);
            Color32[] px = src.GetPixels32();
            for (int i = 0; i < px.Length; i++)
            {
                float a = px[i].a / 255f;
                px[i] = new Color32(
                    (byte)Mathf.RoundToInt(Mathf.Lerp(background.r * 255f, px[i].r, a)),
                    (byte)Mathf.RoundToInt(Mathf.Lerp(background.g * 255f, px[i].g, a)),
                    (byte)Mathf.RoundToInt(Mathf.Lerp(background.b * 255f, px[i].b, a)), 255);
            }
            src.SetPixels32(px);
            src.wrapMode = TextureWrapMode.Repeat;
            src.filterMode = FilterMode.Bilinear;
            src.Apply();
            return src;
        }

        private static Texture2D Shrink(Texture2D tex, int size)
        {
            RenderTexture rt = RenderTexture.GetTemporary(size, size, 0, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            Graphics.Blit(tex, rt);
            RenderTexture.active = rt;
            var result = new Texture2D(size, size, TextureFormat.RGBA32, false);
            result.ReadPixels(new Rect(0, 0, size, size), 0, 0);
            result.Apply();
            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(rt);
            return result;
        }
    }

    /// <summary>Refreshes every container's fill a few times a second, and hides the ones far from the player.</summary>
    internal sealed class ContainerFillSystem : MonoBehaviour
    {
        private const float DrawRange = 30f;
        private static readonly List<ContainerFillView> Views = new List<ContainerFillView>();
        private static ContainerFillSystem _instance;
        private float _next;
        private Transform _player;

        public static void Register(ContainerFillView v)
        {
            if (!Views.Contains(v)) Views.Add(v);
            if (_instance == null)
            {
                var go = new GameObject("ContainerFillSystem");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<ContainerFillSystem>();
            }
        }

        public static void Unregister(ContainerFillView v) => Views.Remove(v);

        private void Update()
        {
            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + 0.25f;
            if (_player == null)
            {
                var ped = PedController.Current;
                _player = ped != null ? ped.transform : null;
            }
            for (int i = Views.Count - 1; i >= 0; i--)
            {
                ContainerFillView v = Views[i];
                if (v == null) { Views.RemoveAt(i); continue; }
                bool near = _player == null || (v.transform.position - _player.position).sqrMagnitude <= DrawRange * DrawRange;
                v.Tick(near);
            }
        }
    }
}
