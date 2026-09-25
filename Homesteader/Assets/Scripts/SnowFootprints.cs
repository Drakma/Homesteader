using UnityEngine;
using Homesteader;
using Homesteader.UI;

/// <summary>
/// Footprints in snow. Keeps a top-down R8 mask of the terrain and stamps a boot print each
/// time a foot bone PLANTS (goes from lifted to touching the ground), so the prints follow the
/// real walk/run animation instead of a stride timer. The terrain shader reads the mask
/// (_SnowFootprintTex / _SnowFootprintRect) and lets the ground show through where it is set.
/// The mask slowly fades, faster while it is snowing, so fresh snow covers old tracks.
/// Add to the player object; it finds the LeftFoot / RightFoot bones once the GLB has loaded.
/// </summary>
[DefaultExecutionOrder(100)]
public sealed class SnowFootprints : MonoBehaviour
{
    [Header("Mask")]
    [Tooltip("Mask resolution. 4096 over 500 m is ~0.12 m per pixel (16 MB, single channel).")]
    public int resolution = 4096;

    [Header("Print")]
    public Vector2 halfSizeMetres = new Vector2(0.055f, 0.14f); // boot ~0.11 x 0.28 m
    [Tooltip("Metres the print centre sits ahead of the ankle, toward the toes.")]
    public float forwardOffset = 0.07f;
    [Tooltip("Minimum snow coverage (0-1) before feet leave prints.")]
    public float minSnowCoverage = 0.2f;

    [Header("Foot plant detection")]
    [Tooltip("A foot counts as planted when within this many metres of its lowest observed height.")]
    public float plantTolerance = 0.035f;

    [Header("Refill")]
    public float fadeIntervalSnowing = 0.25f;  // real seconds per 1/255 step at 1x (about 1 minute; divided by the game speed)
    public float fadeIntervalIdle = 1.0f;      // ~4 minutes when it isn't snowing

    private class Foot
    {
        public Transform bone;
        public Transform toe;
        public float lowest = float.MaxValue;
        public bool planted;
    }

    private static readonly int SnowFootprintTexId = Shader.PropertyToID("_SnowFootprintTex");
    private static readonly int SnowFootprintRectId = Shader.PropertyToID("_SnowFootprintRect");

    [Header("Snow removal")]
    [Tooltip("Real seconds per 1/255 of regrowth on cleared areas at 1x game speed while it is snowing (about 5 minutes at 1.2). Cleared ground does not regrow when it is not snowing.")]
    public float clearedRegrowIntervalSnowing = 1.2f;  // ~5 real minutes at 1x, matching normal snowfall; halved in a blizzard

    private static readonly int SnowClearedTexId = Shader.PropertyToID("_SnowClearedTex");

    /// <summary>The active instance, for gameplay code (shovel, plow, vehicles) to call.</summary>
    public static SnowFootprints Instance { get; private set; }

    private RenderTexture _cleared;
    private float _nextClearedFade;
    private RenderTexture _mask;
    private Material _mat;
    private readonly Foot _left = new Foot();
    private readonly Foot _right = new Foot();
    private Vector2 _origin, _size;
    private float _nextFade;
    private float _nextBoneSearch;
    private PedController _ped;

    private void Start()
    {
        var shader = Shader.Find("Hidden/Homesteader/FootprintStamp");
        if (shader == null)
        {
            Debug.LogWarning("[SnowFootprints] Shader 'Hidden/Homesteader/FootprintStamp' not found; footprints disabled.");
            enabled = false;
            return;
        }
        _mat = new Material(shader);
        _ped = GetComponent<PedController>();
        Instance = this;
        CreateMask();
    }

    private void OnDestroy()
    {
        if (Instance == this) Instance = null;
        if (_mask != null) _mask.Release();
        if (_cleared != null) _cleared.Release();
        if (_mat != null) Destroy(_mat);
        Shader.SetGlobalTexture(SnowFootprintTexId, Texture2D.blackTexture);
        Shader.SetGlobalTexture(SnowClearedTexId, Texture2D.blackTexture);
    }

    private void CreateMask()
    {
        var terrain = Terrain.activeTerrain;
        if (terrain != null)
        {
            _origin = new Vector2(terrain.transform.position.x, terrain.transform.position.z);
            _size = new Vector2(terrain.terrainData.size.x, terrain.terrainData.size.z);
        }
        else
        {
            _origin = new Vector2(-250f, -250f);
            _size = new Vector2(500f, 500f);
        }

        _mask = new RenderTexture(resolution, resolution, 0, RenderTextureFormat.R8, RenderTextureReadWrite.Linear)
        {
            name = "SnowFootprintMask",
            wrapMode = TextureWrapMode.Clamp,
            filterMode = FilterMode.Bilinear
        };
        _mask.Create();
        var prev = RenderTexture.active;
        RenderTexture.active = _mask;
        GL.Clear(false, true, Color.black);
        RenderTexture.active = prev;

        _cleared = new RenderTexture(resolution, resolution, 0, RenderTextureFormat.R8, RenderTextureReadWrite.Linear)
        {
            name = "SnowClearedMask",
            wrapMode = TextureWrapMode.Clamp,
            filterMode = FilterMode.Bilinear
        };
        _cleared.Create();
        RenderTexture.active = _cleared;
        GL.Clear(false, true, Color.black);
        RenderTexture.active = prev;

        Shader.SetGlobalTexture(SnowClearedTexId, _cleared);
        Shader.SetGlobalTexture(SnowFootprintTexId, _mask);
        Shader.SetGlobalVector(SnowFootprintRectId, new Vector4(_origin.x, _origin.y, 1f / _size.x, 1f / _size.y));
    }

    private static Transform FindBone(Transform root, string suffix)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
            if (t.name.EndsWith(suffix, System.StringComparison.OrdinalIgnoreCase)) return t;
        return null;
    }

    private void ResolveBones()
    {
        if (_left.bone != null && _right.bone != null) return;
        if (Time.time < _nextBoneSearch) return;
        _nextBoneSearch = Time.time + 1f; // the GLB loads asynchronously; keep looking until it is there
        _left.bone = FindBone(transform, "LeftFoot");
        _left.toe = FindBone(transform, "LeftToeBase");
        _right.bone = FindBone(transform, "RightFoot");
        _right.toe = FindBone(transform, "RightToeBase");
    }

    private void Update()
    {
        if (_mask == null || _mat == null) return;
        ResolveBones();

        var weather = WeatherEffectsManager.Instance;
        float snow = weather != null ? weather.SnowCoverage : 0f;
        bool moving = _ped != null && _ped.IsMoving;

        if (snow >= minSnowCoverage)
        {
            TrackFoot(_left, moving);
            TrackFoot(_right, moving);
        }

        if (Time.time >= _nextFade)
        {
            var w = TimeSystem.Instance != null ? TimeSystem.Instance.Weather : HomesteaderWeather.Sunny;
            bool snowingNow = w == HomesteaderWeather.Snow || w == HomesteaderWeather.Blizzard;
            _nextFade = Time.time + (snowingNow ? fadeIntervalSnowing : fadeIntervalIdle) / SpeedMult();
            _mat.SetFloat("_FadeAmount", 1f / 255f);
            Graphics.Blit(Texture2D.blackTexture, _mask, _mat, 2);
        }

        // Cleared ground only refills while it is actually snowing.
        if (Time.time >= _nextClearedFade)
        {
            var w2 = TimeSystem.Instance != null ? TimeSystem.Instance.Weather : HomesteaderWeather.Sunny;
            bool snowing = w2 == HomesteaderWeather.Snow || w2 == HomesteaderWeather.Blizzard;
            _nextClearedFade = Time.time + clearedRegrowIntervalSnowing * (w2 == HomesteaderWeather.Blizzard ? 0.4f : 1f) / SpeedMult();
            if (snowing)
            {
                _mat.SetFloat("_FadeAmount", 1f / 255f);
                Graphics.Blit(Texture2D.blackTexture, _cleared, _mat, 2);
            }
        }
    }

    // Game speed multiplier (1 at 1x, 3, 5, 10); never 0 so intervals stay finite while paused.
    private static float SpeedMult()
    {
        if (TimeSystem.Instance == null) return 1f;
        return Mathf.Max(0.25f, TimeSystem.SpeedToMultiplier(TimeSystem.Instance.CurrentSpeed));
    }

    // ---- Snow removal API ----
    // Call from tools and vehicles. Positions are world space (metres); only X/Z are used.

    /// <summary>Removes snow in a circle (for example a shovel scoop).</summary>
    public void ClearCircle(Vector3 worldPos, float radiusMetres)
    {
        ClearCapsule(worldPos, worldPos, radiusMetres);
    }

    /// <summary>Removes snow along a line with the given radius (a plow blade or vehicle track).
    /// Call every frame with the previous and current positions for a continuous swath.</summary>
    public void ClearCapsule(Vector3 worldA, Vector3 worldB, float radiusMetres)
    {
        if (_cleared == null || _mat == null) return;
        Vector2 a = ToUv(worldA), b = ToUv(worldB);
        _mat.SetVector("_SegA", new Vector4(a.x, a.y, 0f, 0f));
        _mat.SetVector("_SegB", new Vector4(b.x, b.y, 0f, 0f));
        _mat.SetVector("_CapsuleR", new Vector4(radiusMetres, 0f, 0f, 0f));
        _mat.SetVector("_WorldSize", new Vector4(_size.x, _size.y, 0f, 0f));
        Graphics.Blit(Texture2D.blackTexture, _cleared, _mat, 1);
    }

    /// <summary>Restores snow everywhere (a new day, or debugging).</summary>
    public void ResetCleared()
    {
        if (_cleared == null) return;
        var prev = RenderTexture.active;
        RenderTexture.active = _cleared;
        GL.Clear(false, true, Color.black);
        RenderTexture.active = prev;
    }

    private Vector2 ToUv(Vector3 world)
    {
        return new Vector2((world.x - _origin.x) / _size.x, (world.z - _origin.y) / _size.y);
    }

    private void TrackFoot(Foot foot, bool moving)
    {
        if (foot.bone == null) return;

        float h = foot.bone.position.y - transform.position.y;
        if (h < foot.lowest) foot.lowest = h;
        bool grounded = h <= foot.lowest + plantTolerance;

        if (grounded && !foot.planted && moving) Stamp(foot);
        foot.planted = grounded;
    }

    private void Stamp(Foot foot)
    {
        Vector3 p = foot.bone.position;
        Vector2 dir;
        if (foot.toe != null)
        {
            Vector3 d = foot.toe.position - p;
            dir = new Vector2(d.x, d.z);
        }
        else
        {
            dir = new Vector2(transform.forward.x, transform.forward.z);
        }
        if (dir.sqrMagnitude < 1e-6f) dir = new Vector2(transform.forward.x, transform.forward.z);
        dir.Normalize();

        Vector2 centre = new Vector2(p.x, p.z) + dir * forwardOffset;
        Vector2 uv = new Vector2((centre.x - _origin.x) / _size.x, (centre.y - _origin.y) / _size.y);
        if (uv.x < 0f || uv.x > 1f || uv.y < 0f || uv.y > 1f) return;

        _mat.SetVector("_StampCenter", new Vector4(uv.x, uv.y, 0f, 0f));
        _mat.SetVector("_StampDir", new Vector4(dir.x, dir.y, 0f, 0f));
        _mat.SetVector("_StampHalf", new Vector4(halfSizeMetres.x, halfSizeMetres.y, 0f, 0f));
        _mat.SetVector("_WorldSize", new Vector4(_size.x, _size.y, 0f, 0f));
        Graphics.Blit(Texture2D.blackTexture, _mask, _mat, 0);
    }
}
