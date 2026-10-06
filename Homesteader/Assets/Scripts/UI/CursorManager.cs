using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// Applies the cursor set built by tools/build_pointers.py.
    ///
    /// WHY THIS EXISTS: Unity's Cursor.SetCursor takes a Texture2D plus a
    /// hotspot, and the hotspot is authored per-image (a tool cursor needs to
    /// click at its blade, not its centre). Keeping that data in cursors.json
    /// rather than hard-coded here means the art can be rebuilt without
    /// touching C#.
    ///
    /// TEXTURE IMPORT: the PNGs must be readable at runtime, so each is imported
    /// as a Texture2D with Read/Write enabled and no compression. A sprite
    /// import setting would give a Sprite, not the Texture2D that
    /// Cursor.SetCursor requires.
    ///
    /// Hotspot coordinates in cursors.json are pixels from the top-left of the
    /// image, which matches Unity's convention (origin top-left), so no flip is
    /// applied. Note Unity's y axis points up in world space but Cursor.SetCursor
    /// expects top-left origin like a screen-space texture, hence no conversion.
    /// </summary>
    public sealed class CursorManager : MonoBehaviour
    {
        public enum CursorVariant
        {
            Mono,   // black outline, white interior
            Color,  // category-coloured interiors
            Amber   // HUD accent gradient with a bevel (3D look)
        }

        [Serializable]
        public sealed class CursorDef
        {
            public string category;
            public string mono;
            public string color;
            public string amber;
            public int[] size;
            public int[] hotspot;
            public string hotspot_mode;
            public string hotspot_note;
            public string source_glyph;
        }

        // JsonUtility CANNOT deserialize into a Dictionary, and Unity's analyzer
        // warns (UAC1015) because a dictionary field is silently skipped by the
        // serialization backend - which would leave `cursors` empty at runtime
        // with no error. So the JSON is parsed with a List of key/def pairs
        // instead, which JsonUtility does handle.
        [Serializable]
        public sealed class CursorEntry
        {
            public string name;
            public CursorDef def;
        }

        [Serializable]
        private sealed class CursorListWrapper
        {
            public List<CursorEntry> cursors;
        }

        [Header("Source")]
        [Tooltip("Folder holding cursors.json plus the mono/ and color/ PNGs. " +
                 "Relative to StreamingAssets unless absolute.")]
        [SerializeField] private string cursorRoot = "HudKit/cursors";

        [Tooltip("Which art variant to apply at runtime.")]
        [SerializeField] private CursorVariant variant = CursorVariant.Amber;

        [Tooltip("Fall back to the OS cursor if the set fails to load.")]
        [SerializeField] private bool fallBackToHardwareCursor = true;

        [Tooltip("On-screen size of a cursor in pixels. The art is authored at 128 px and is scaled down to this on load " +
                 "(hotspots scale with it); a 128 px cursor would cover a toolbar slot.")]
        [SerializeField, Range(24, 128)] private int displaySize = 40;

        public const string Arrow = "cursor_arrow";
        public const string Finger = "cursor_finger_point";
        public const string HandOpen = "cursor_hand_open";
        public const string Shears = "cursor_shears";
        public const string WireCutters = "cursor_wire_cutters";
        public const string FuelNozzle = "cursor_fuel_nozzle";
        public const string Hammer = "cursor_hammer";
        public const string Axe = "cursor_axe";
        public const string Pickaxe = "cursor_pickaxe";
        public const string Mattock = "cursor_mattock";
        public const string Shovel = "cursor_shovel";
        public const string ShovelPour = "cursor_shovel_pour";
        public const string Basket = "cursor_egg_basket";

        public static CursorManager Instance { get; private set; }

        /// <summary>Created at startup so the game always runs with the kit cursor, no scene object needed.</summary>
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<CursorManager>() != null) return;
            var go = new GameObject("CursorManager");
            DontDestroyOnLoad(go);
            go.AddComponent<CursorManager>();
            go.AddComponent<CursorHints>();
        }

        // Loaded textures, keyed by cursor name, so switching state does not
        // re-read a PNG every time the player moves the mouse.
        private readonly Dictionary<string, Texture2D> textures =
            new Dictionary<string, Texture2D>(StringComparer.OrdinalIgnoreCase);

        private readonly Dictionary<string, Vector2> hotspots =
            new Dictionary<string, Vector2>(StringComparer.OrdinalIgnoreCase);

        private readonly Dictionary<string, CursorMode> modes =
            new Dictionary<string, CursorMode>(StringComparer.OrdinalIgnoreCase);

        private string current;

        /// <summary>Names discovered in cursors.json, for validation and tooling.</summary>
        public IReadOnlyCollection<string> AvailableCursors => hotspots.Keys;

        public string CurrentCursor => current;

        private void Awake()
        {
            Instance = this;
            // The Settings toggle (Graphics > Colorized Mouse Cursors) decides between the amber and the black-and-white set.
            variant = GraphicsOptions.ColorizedCursorsOn() ? CursorVariant.Amber : CursorVariant.Mono;
            if (!LoadManifest())
            {
                if (fallBackToHardwareCursor)
                {
                    Debug.LogWarning(
                        "[CursorManager] Cursor set could not be loaded; keeping the " +
                        "hardware cursor. Check that cursors.json and the PNG folders " +
                        "exist under StreamingAssets/" + cursorRoot + ".");
                }
                enabled = false;
            }
        }

        /// <summary>
        /// Reads cursors.json and preloads every texture. Returns false if the
        /// manifest is missing or empty, so the caller can keep the OS cursor
        /// rather than shipping an invisible one.
        /// </summary>
        private bool LoadManifest()
        {
            string root = cursorRoot;
            if (!Path.IsPathRooted(root))
            {
                root = Path.Combine(Application.streamingAssetsPath, cursorRoot);
            }

            string manifestPath = Path.Combine(root, "cursors.json");
            if (!File.Exists(manifestPath))
            {
                Debug.LogWarning("[CursorManager] missing manifest: " + manifestPath);
                return false;
            }

            CursorListWrapper doc;
            try
            {
                // Read the list-form manifest (cursors_array.json). The object-form
                // cursors.json cannot be bound by JsonUtility, which has no
                // Dictionary support - see tools/build_pointers.py, which writes
                // both shapes from one source.
                string listPath = Path.Combine(root, "cursors_array.json");
                string json = File.ReadAllText(
                    File.Exists(listPath) ? listPath : manifestPath);
                doc = JsonUtility.FromJson<CursorListWrapper>(json);
            }
            catch (Exception e)
            {
                Debug.LogWarning("[CursorManager] could not parse cursors.json: " + e.Message);
                return false;
            }

            if (doc?.cursors == null || doc.cursors.Count == 0)
            {
                Debug.LogWarning("[CursorManager] cursors.json contained no cursors.");
                return false;
            }


            foreach (CursorEntry entry in doc.cursors)
            {
                CursorDef def = entry.def;
                if (def == null) continue;
                string rel = variant == CursorVariant.Color ? def.color
                           : variant == CursorVariant.Amber ? def.amber
                           : def.mono;
                if (string.IsNullOrEmpty(rel)) rel = def.mono;   // an older manifest without this variant
                if (string.IsNullOrEmpty(rel)) continue;

                string pngPath = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
                Texture2D tex = LoadTexture(pngPath, displaySize);
                if (tex == null)
                {
                    // A missing texture is not fatal for the whole set: the other
                    // cursors still work, and the fallback keeps this one usable.
                    Debug.LogWarning("[CursorManager] missing texture for '" +
                                     entry.name + "': " + pngPath);
                    continue;
                }

                textures[entry.name] = tex;

                if (def.hotspot != null && def.hotspot.Length >= 2)
                {
                    // The hotspot was measured on the 128 px source, so it shrinks with the art.
                    int srcSize = def.size != null && def.size.Length >= 1 && def.size[0] > 0 ? def.size[0] : 128;
                    float k = (float)tex.width / srcSize;
                    hotspots[entry.name] = new Vector2(def.hotspot[0] * k, def.hotspot[1] * k);
                }
                else
                {
                    hotspots[entry.name] = new Vector2(tex.width * 0.5f, tex.height * 0.5f);
                }

                // Software mode so the hotspot is honoured exactly; hardware mode
                // lets the OS clamp hotspots to its own limits.
                modes[entry.name] = CursorMode.ForceSoftware;
            }

            return textures.Count > 0;
        }

        private static Texture2D LoadTexture(string path, int size)
        {
            if (!File.Exists(path))
            {
                return null;
            }

            byte[] bytes = File.ReadAllBytes(path);
            // 128x128 RGBA, no mipmaps, linear: the exact shape of the source
            // art. Uncompressed because a cursor is tiny and compression
            // artifacts show as fringing around the silhouette.
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            if (!tex.LoadImage(bytes))
            {
                Destroy(tex);
                return null;
            }
            tex.filterMode = FilterMode.Bilinear;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.name = Path.GetFileNameWithoutExtension(path);
            if (size > 0 && size < tex.width)
            {
                Texture2D small = Downscale(tex, size);
                Destroy(tex);
                tex = small;
            }
            return tex;
        }

        /// <summary>
        /// Box-filtered resample on the CPU (a cursor is read once, so speed does not matter). Colour is weighted by
        /// alpha while averaging so the transparent canvas does not bleed dark fringes into the edge of the glyph.
        /// </summary>
        private static Texture2D Downscale(Texture2D src, int size)
        {
            int sw = src.width, sh = src.height;
            Color32[] px = src.GetPixels32();
            var dst = new Texture2D(size, size, TextureFormat.RGBA32, false, true)
            {
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp,
                name = src.name
            };
            var outPx = new Color32[size * size];
            float sx = (float)sw / size, sy = (float)sh / size;
            for (int y = 0; y < size; y++)
            {
                int y0 = Mathf.FloorToInt(y * sy), y1 = Mathf.Min(sh, Mathf.CeilToInt((y + 1) * sy));
                for (int x = 0; x < size; x++)
                {
                    int x0 = Mathf.FloorToInt(x * sx), x1 = Mathf.Min(sw, Mathf.CeilToInt((x + 1) * sx));
                    float r = 0, g = 0, b = 0, a = 0; int n = 0;
                    for (int yy = y0; yy < y1; yy++)
                    for (int xx = x0; xx < x1; xx++)
                    {
                        Color32 c = px[yy * sw + xx];
                        float ca = c.a / 255f;
                        r += c.r * ca; g += c.g * ca; b += c.b * ca; a += ca; n++;
                    }
                    if (n == 0 || a <= 0f) { outPx[y * size + x] = new Color32(0, 0, 0, 0); continue; }
                    outPx[y * size + x] = new Color32(
                        (byte)Mathf.Clamp(Mathf.RoundToInt(r / a), 0, 255),
                        (byte)Mathf.Clamp(Mathf.RoundToInt(g / a), 0, 255),
                        (byte)Mathf.Clamp(Mathf.RoundToInt(b / a), 0, 255),
                        (byte)Mathf.Clamp(Mathf.RoundToInt(a / n * 255f), 0, 255));
                }
            }
            dst.SetPixels32(outPx);
            dst.Apply(false, false);
            return dst;
        }

        /// <summary>
        /// Apply a cursor by the name used in cursors.json, e.g. "cursor_axe".
        /// Unknown names are ignored with a warning rather than throwing, since
        /// cursor changes are driven by gameplay state that may reference art
        /// that has not been rebuilt yet.
        /// </summary>
        public void SetCursor(string name)
        {
            if (string.IsNullOrEmpty(name) || name == current)
            {
                return;
            }

            if (!textures.TryGetValue(name, out Texture2D tex))
            {
                Debug.LogWarning("[CursorManager] unknown cursor '" + name + "'.");
                return;
            }

            Cursor.SetCursor(tex, hotspots[name], modes[name]);
            current = name;
        }

        public void SetVariant(CursorVariant v)
        {
            if (v == variant) return;
            variant = v;

            ReleaseTextures();
            if (LoadManifest())
            {
                // Re-apply the same cursor against the new art.
                string previous = current;
                current = null;
                if (!string.IsNullOrEmpty(previous))
                {
                    SetCursor(previous);
                }
            }
        }

        /// <summary>Hand control back to the operating system cursor.</summary>
        public void ResetToSystemCursor()
        {
            Cursor.SetCursor(null, Vector2.zero, CursorMode.Auto);
            current = null;
        }

        private void ReleaseTextures()
        {
            foreach (KeyValuePair<string, Texture2D> kv in textures)
            {
                if (kv.Value != null) Destroy(kv.Value);
            }
            textures.Clear();
            hotspots.Clear();
            modes.Clear();
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
            ReleaseTextures();
        }
    }
}
