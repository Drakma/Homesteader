using UnityEngine;

/// <summary>
/// Bakes a "basin" map from the terrain heightmap so puddles collect in low ground first
/// (and dry out there last). Each texel is 0..1: 1 = a hollow or valley floor that catches
/// water, 0 = a crest or high ground that sheds it. The terrain shader lowers the puddle
/// threshold where this is high, so as it rains the water appears in the hollows, then
/// spreads outward and uphill as the level rises, and retreats back into the hollows as
/// the ground dries.
///
/// Concavity is the height difference to a blurred neighbourhood mean (a hollow is lower than
/// its surroundings), mixed with plain elevation so broad valleys also fill first.
/// Generated once, as soon as the terrain has real relief.
/// </summary>
[DisallowMultipleComponent]
public sealed class PuddleBasinMap : MonoBehaviour
{
    [Tooltip("Blur radius in metres used to decide what counts as 'lower than its surroundings'.")]
    public float neighbourhoodMetres = 14f;

    [Tooltip("Weight of concavity vs raw elevation (1 = concavity only).")]
    [Range(0f, 1f)] public float concavityWeight = 0.7f;

    private static readonly int BasinTexId = Shader.PropertyToID("_PuddleBasinTex");
    private static readonly int BasinRectId = Shader.PropertyToID("_PuddleBasinRect");

    private Texture2D _tex;
    private bool _done;
    private float _nextTry;

    private void Update()
    {
        if (_done || Time.time < _nextTry) return;
        _nextTry = Time.time + 1f;
        TryBuild();
    }

    private void OnDestroy()
    {
        if (_tex != null) Destroy(_tex);
        Shader.SetGlobalVector(BasinRectId, Vector4.zero);
    }

    private void TryBuild()
    {
        var terrain = Terrain.activeTerrain;
        if (terrain == null || terrain.terrainData == null) return;

        var td = terrain.terrainData;
        int hres = td.heightmapResolution;
        float[,] hm = td.GetHeights(0, 0, hres, hres);

        // Wait until the generator has actually shaped the terrain.
        float hmin = float.MaxValue, hmax = float.MinValue;
        for (int y = 0; y < hres; y += 8)
            for (int x = 0; x < hres; x += 8)
            {
                float v = hm[y, x];
                if (v < hmin) hmin = v;
                if (v > hmax) hmax = v;
            }
        if (hmax - hmin < 1e-4f) return;

        Vector3 size = td.size;
        int n = 256; // 256 x 256 over the terrain (about 2 m per texel at 500 m)
        float[] h = new float[n * n];
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float fx = x / (float)(n - 1) * (hres - 1);
                float fy = y / (float)(n - 1) * (hres - 1);
                h[y * n + x] = hm[Mathf.Clamp(Mathf.RoundToInt(fy), 0, hres - 1),
                                   Mathf.Clamp(Mathf.RoundToInt(fx), 0, hres - 1)] * size.y; // metres
            }

        float texelMetres = size.x / (n - 1);
        int r = Mathf.Max(1, Mathf.RoundToInt(neighbourhoodMetres / texelMetres));
        float[] mean = BoxBlur(h, n, r);

        float[] conc = new float[n * n];
        float[] concPos = new float[n * n];
        int count = 0;
        for (int i = 0; i < conc.Length; i++)
        {
            conc[i] = mean[i] - h[i]; // positive in hollows
            if (conc[i] > 0f) concPos[count++] = conc[i];
        }
        System.Array.Sort(concPos, 0, count);
        float scale = count > 0 ? Mathf.Max(0.05f, concPos[Mathf.Min(count - 1, (int)(count * 0.95f))]) : 1f;

        float heightRange = Mathf.Max(0.01f, (hmax - hmin) * size.y);
        float hLow = hmin * size.y;

        var pixels = new Color32[n * n];
        for (int i = 0; i < pixels.Length; i++)
        {
            float c = Mathf.Clamp01(conc[i] / scale);
            float low = 1f - Mathf.Clamp01((h[i] - hLow) / heightRange);
            byte b = (byte)Mathf.RoundToInt(Mathf.Clamp01(concavityWeight * c + (1f - concavityWeight) * low) * 255f);
            pixels[i] = new Color32(b, b, b, 255);
        }

        _tex = new Texture2D(n, n, TextureFormat.R8, false, true)
        {
            name = "PuddleBasinMap",
            wrapMode = TextureWrapMode.Clamp,
            filterMode = FilterMode.Bilinear
        };
        _tex.SetPixels32(pixels);
        _tex.Apply(false, false);

        Vector3 p = terrain.transform.position;
        Shader.SetGlobalTexture(BasinTexId, _tex);
        Shader.SetGlobalVector(BasinRectId, new Vector4(p.x, p.z, 1f / size.x, 1f / size.z));
        _done = true;
    }

    // Separable box blur with clamped edges.
    private static float[] BoxBlur(float[] src, int n, int r)
    {
        float[] tmp = new float[src.Length];
        float[] dst = new float[src.Length];
        float inv = 1f / (2 * r + 1);

        for (int y = 0; y < n; y++)
        {
            float sum = 0f;
            for (int k = -r; k <= r; k++) sum += src[y * n + Mathf.Clamp(k, 0, n - 1)];
            for (int x = 0; x < n; x++)
            {
                tmp[y * n + x] = sum * inv;
                sum += src[y * n + Mathf.Clamp(x + r + 1, 0, n - 1)] - src[y * n + Mathf.Clamp(x - r, 0, n - 1)];
            }
        }
        for (int x = 0; x < n; x++)
        {
            float sum = 0f;
            for (int k = -r; k <= r; k++) sum += tmp[Mathf.Clamp(k, 0, n - 1) * n + x];
            for (int y = 0; y < n; y++)
            {
                dst[y * n + x] = sum * inv;
                sum += tmp[Mathf.Clamp(y + r + 1, 0, n - 1) * n + x] - tmp[Mathf.Clamp(y - r, 0, n - 1) * n + x];
            }
        }
        return dst;
    }
}
