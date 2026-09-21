using UnityEngine;

public class OcclusionFader : MonoBehaviour
{
    public Transform target;
    public GameObject[] fadeableStructures;
    [Range(0f, 1f)] public float fadedAlpha = 0.3f;
    public Color ghostTint = new Color(0.5f, 0.5f, 0.5f, 1f);
    public float fadeDuration = 0.6f;

    private Material[] materials;
    private Color[] baseColors;
    private float[] progress; // 0 = fully real/opaque, 1 = fully ghost/faded
    private Renderer[][] allRenderers;

    void Start()
    {
        if (fadeableStructures == null || fadeableStructures.Length == 0)
        {
            // Nothing to fade; disable the script so we don't repeatedly
            // hit NRE in Update() too. Designers can attach objects in
            // the inspector to enable occlusion fading on a structure.
            enabled = false;
            return;
        }
        int n = fadeableStructures.Length;
        materials = new Material[n];
        baseColors = new Color[n];
        progress = new float[n];
        allRenderers = new Renderer[n][];

        for (int i = 0; i < n; i++)
        {
            if (fadeableStructures[i] == null) continue;
            var renderers = fadeableStructures[i].GetComponentsInChildren<Renderer>();
            allRenderers[i] = renderers;
            if (renderers.Length == 0) continue;

            var instance = new Material(renderers[0].sharedMaterial);
            baseColors[i] = instance.GetColor("_BaseColor");
            materials[i] = instance;
            foreach (var r in renderers)
            {
                var mats = new Material[r.sharedMaterials.Length];
                for (int m = 0; m < mats.Length; m++) mats[m] = instance;
                r.sharedMaterials = mats;
            }
        }
    }

    void SetOpaque(Material m)
    {
        m.SetFloat("_Surface", 0f);
        m.SetOverrideTag("RenderType", "Opaque");
        m.SetInt("_ZWrite", 1);
        m.DisableKeyword("_ALPHABLEND_ON");
        m.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.renderQueue = -1;
    }

    void SetTransparent(Material m)
    {
        m.SetFloat("_Surface", 1f);
        m.SetOverrideTag("RenderType", "Transparent");
        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        m.SetInt("_ZWrite", 1); // keep depth writes on to avoid self-overlap gaps on complex geometry (e.g. roof ridges)
        m.DisableKeyword("_ALPHATEST_ON");
        m.EnableKeyword("_ALPHABLEND_ON");
        m.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
    }

    void Update()
    {
        if (target == null || materials == null || fadeableStructures == null) return;

        Vector3 origin = transform.position;
        Vector3 targetPoint = target.position + Vector3.up * 1f;
        Vector3 dir = targetPoint - origin;
        float dist = dir.magnitude;
        dir.Normalize();

        var hits = Physics.RaycastAll(origin, dir, dist);

        for (int i = 0; i < fadeableStructures.Length; i++)
        {
            if (materials[i] == null) continue;
            bool occluding = false;
            foreach (var hit in hits)
            {
                if (hit.collider.gameObject == fadeableStructures[i])
                {
                    occluding = true;
                    break;
                }
            }

            float target01 = occluding ? 1f : 0f;
            bool wasFullyReal = progress[i] <= 0.001f;
            progress[i] = Mathf.MoveTowards(progress[i], target01, Time.deltaTime / fadeDuration);
            bool nowFullyReal = progress[i] <= 0.001f;

            if (wasFullyReal && !nowFullyReal) SetTransparent(materials[i]);
            else if (!wasFullyReal && nowFullyReal) SetOpaque(materials[i]);

            Color from = baseColors[i];
            Color to = new Color(ghostTint.r, ghostTint.g, ghostTint.b, fadedAlpha);
            Color blended = Color.Lerp(from, to, progress[i]);
            materials[i].SetColor("_BaseColor", blended);

            var shadowMode = progress[i] > 0.01f ? UnityEngine.Rendering.ShadowCastingMode.Off : UnityEngine.Rendering.ShadowCastingMode.On;
            foreach (var r in allRenderers[i])
            {
                if (r.shadowCastingMode != shadowMode) r.shadowCastingMode = shadowMode;
            }
        }
    }
}
