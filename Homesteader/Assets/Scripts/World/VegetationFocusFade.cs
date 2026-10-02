using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.World
{
    /// <summary>
    /// Fades the SMALL plants (flowers, grass tufts, cattails, bed debris, scree) away with distance from the CENTRE OF THE VIEW, not from the
    /// player, so panning the camera keeps the plants around wherever you are looking. Beyond the fade the plants shrink to nothing in the
    /// Vegetation shader (_VegFocus), and the chunk meshes that hold only such plants are switched off entirely, which is the saving: a
    /// zoomed-out view no longer draws every tuft across the whole window.
    /// Trees and anything that casts a shadow are not touched.
    /// </summary>
    public sealed class VegetationFocusFade : MonoBehaviour
    {
        /// <summary>Metres from the view centre where the small plants start to shrink, and where they are gone.</summary>
        public const float ReferenceRange = 46f;       // the outer fade distance at scale 1
        public static float RangeScale = 1f;           // the graphics preset's small_plant_range / ReferenceRange (GraphicsOptions)
        public static float FadeInnerMetres => 34f * RangeScale;
        public static float FadeOuterMetres => ReferenceRange * RangeScale;

        private static readonly int FocusId = Shader.PropertyToID("_VegFocus");
        private static readonly int FadeFlagId = Shader.PropertyToID("_FocusFade");

        private readonly List<MeshRenderer> _smallChunks = new List<MeshRenderer>();
        private float _next;
        private Camera _cam;

        private void Start()
        {
            // The chunk meshes with no shadow casting hold only the small plants (see ProceduralVegetation.Combine, "_ns").
            var usedByBig = new HashSet<Material>();
            var small = new List<MeshRenderer>();
            foreach (MeshRenderer r in GetComponentsInChildren<MeshRenderer>(true))
            {
                if (r.gameObject.name.StartsWith("VegChunk_") && r.gameObject.name.EndsWith("_ns")) small.Add(r);
                else foreach (Material m in r.sharedMaterials) if (m != null) usedByBig.Add(m);
            }
            _smallChunks.AddRange(small);

            // Only materials used by small plants alone fade (the rock materials are shared with the big, shadow-casting boulders).
            foreach (MeshRenderer r in small)
                foreach (Material m in r.sharedMaterials)
                    if (m != null && !usedByBig.Contains(m) && m.HasProperty(FadeFlagId)) m.SetFloat(FadeFlagId, 1f);

            Update();
        }

        private void OnDisable()
        {
            // Put everything back (leaving the scene, or this component being removed).
            Shader.SetGlobalVector(FocusId, new Vector4(0f, 0f, 1e9f, 1e9f + 1f));
            foreach (MeshRenderer r in _smallChunks) if (r != null) r.enabled = true;
        }

        private void Update()
        {
            if (Time.unscaledTime < _next) return;
            _next = Time.unscaledTime + 0.1f;

            if (_cam == null) _cam = Camera.main;
            if (_cam == null) return;

            // The ground point at the middle of the window.
            Ray ray = _cam.ViewportPointToRay(new Vector3(0.5f, 0.5f, 0f));
            Vector3 focus;
            var ground = new Plane(Vector3.up, new Vector3(0f, 0.3f, 0f));
            if (ground.Raycast(ray, out float enter)) focus = ray.GetPoint(enter);
            else return;

            Shader.SetGlobalVector(FocusId, new Vector4(focus.x, focus.z, FadeInnerMetres, FadeOuterMetres));

            // Switch off the small-plant chunks that are entirely past the fade.
            var focus2 = new Vector2(focus.x, focus.z);
            for (int i = 0; i < _smallChunks.Count; i++)
            {
                MeshRenderer r = _smallChunks[i];
                if (r == null) continue;
                Bounds b = r.bounds;
                float dx = Mathf.Max(b.min.x - focus2.x, 0f, focus2.x - b.max.x);
                float dz = Mathf.Max(b.min.z - focus2.y, 0f, focus2.y - b.max.z);
                bool inRange = dx * dx + dz * dz < FadeOuterMetres * FadeOuterMetres;
                if (r.enabled != inRange) r.enabled = inRange;
            }
        }
    }
}
