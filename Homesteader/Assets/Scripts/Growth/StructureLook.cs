using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// What a building looks like follows what it was built from. A construction material whose manifest sets look_target (a comma list of
    /// roof, walls, interior, floor, chimney, foundation) with a colour, smoothness and metallic value (properties.look_*, edited in the asset
    /// kit) gives those parts of the building that look when a stage is built from it: birch logs make white-cream log walls, a paint its
    /// colour on the inside walls, carpet or tile the floor, corrugated steel a silver roof, a brick or field stone the chimney.
    /// A foundation item also names a style (look_style: poured, block, brick, stilts): the stage models hold the slab in an object called
    /// "Foundation", and for any other style ConstructionSite hides it and shows the matching variant model instead.
    /// The models name their materials (cabin: Log, Roof, Interior, Floor, Masonry; house: Siding, Shingle, ShingleDark, ...; variants:
    /// FoundationFace), which is what gets recoloured. ConstructionSite remembers the item ids that set the looks (saved with the site).
    /// </summary>
    public static class StructureLook
    {
        /// <summary>True when the item sets the look of at least one part; its catalog entry comes back in item.</summary>
        public static bool TryLook(string itemId, out AssetCatalogItem item)
        {
            item = HudBindings.GetCatalogItem(itemId);
            return item != null && !string.IsNullOrEmpty(item.look_target);
        }

        public static bool Styles(AssetCatalogItem item, string part)
        {
            if (item == null || string.IsNullOrEmpty(item.look_target)) return false;
            foreach (string t in item.look_target.Split(',')) if (t.Trim() == part) return true;
            return false;
        }

        /// <summary>The item that decides a part's look (the last one in the list that styles it), or null.</summary>
        public static AssetCatalogItem For(List<string> ids, string part)
        {
            AssetCatalogItem found = null;
            if (ids == null) return null;
            foreach (string id in ids)
                if (TryLook(id, out AssetCatalogItem item) && Styles(item, part)) found = item;
            return found;
        }

        /// <summary>The foundation style the items ask for: "block", "brick" or "stilts" (null for the poured slab or when none says).</summary>
        public static string FoundationStyle(List<string> ids)
        {
            AssetCatalogItem item = For(ids, "foundation");
            if (item == null || string.IsNullOrEmpty(item.look_style) || item.look_style == "poured") return null;
            return item.look_style;
        }

        /// <summary>Recolours the materials of a model according to the looks of the given items.</summary>
        public static void Apply(Transform root, List<string> lookItemIds)
        {
            if (root == null) return;
            AssetCatalogItem roof = For(lookItemIds, "roof"), walls = For(lookItemIds, "walls"), interior = For(lookItemIds, "interior"),
                             floor = For(lookItemIds, "floor"), chimney = For(lookItemIds, "chimney"), foundation = For(lookItemIds, "foundation");

            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    string name = Plain(mats[i].name);
                    if (IsPaneledDoor(name) || name.StartsWith("Shutter"))
                    {
                        // a door slab or a shutter of a generated model: its grayscale panel / louvre picture. The picture only shades, so the material's colour (or the
                        // paint put on later, see Paint) still tints it.
                        var pm = new Material(mats[i]) { name = name };
                        SetPicture(pm, name.StartsWith("Shutter") ? ShutterTexture() : DoorPanelTexture());
                        mats[i] = pm;
                        changed = true;
                        continue;
                    }
                    if (name.StartsWith("FoundationFace") && foundation != null && foundation.look_style == "brick")
                    {
                        // a brick or stone foundation: the same brick or fieldstone picture as the chimney, tinted with the item's colour
                        Color fc = Color.white;
                        ColorUtility.TryParseHtmlString(foundation.look_color, out fc);
                        fc.a = 1f;
                        var fm = new Material(mats[i]) { name = name };
                        Set(fm, fc, foundation.look_smoothness, foundation.look_metallic);
                        SetPicture(fm, IsStone(foundation) ? StoneTexture() : BrickTexture());
                        mats[i] = fm;
                        changed = true;
                        continue;
                    }
                    if (name.StartsWith("Masonry"))
                    {
                        // the chimney: brick or fieldstone picture, tinted with the colour of the item it was built from (red brick when none was)
                        bool stone = chimney != null && IsStone(chimney);
                        Color mc = new Color(0.62f, 0.3f, 0.23f);
                        if (chimney != null) ColorUtility.TryParseHtmlString(chimney.look_color, out mc);
                        mc.a = 1f;
                        var mm = new Material(mats[i]) { name = name };
                        Set(mm, mc, chimney != null ? chimney.look_smoothness : 0.05f, chimney != null ? chimney.look_metallic : 0f);
                        SetPicture(mm, stone ? StoneTexture() : BrickTexture());
                        mats[i] = mm;
                        changed = true;
                        continue;
                    }
                    if (name.StartsWith("Floor") && floor != null && floor.id != null && floor.id.Contains("tile"))
                    {
                        // tiled floor: the floor's colour with grout lines between 25 cm tiles (the floor has UVs in metres)
                        Color tc = Color.white;
                        ColorUtility.TryParseHtmlString(floor.look_color, out tc);
                        tc.a = 1f;
                        var tm = new Material(mats[i]) { name = name };
                        Set(tm, tc, floor.look_smoothness, floor.look_metallic);
                        SetPicture(tm, TileTexture());
                        mats[i] = tm;
                        changed = true;
                        continue;
                    }
                    AssetCatalogItem look = null;
                    if (name.StartsWith("Roof") || name.StartsWith("Shingle")) look = roof;
                    else if (name.StartsWith("Log") || name.StartsWith("Siding")) look = walls;
                    else if (name.StartsWith("Interior")) look = interior;
                    else if (name.StartsWith("Floor")) look = floor;
                    else if (name.StartsWith("FoundationFace")) look = foundation;
                    if (look == null) continue;
                    var m = new Material(mats[i]) { name = name };
                    Color c = Color.white;
                    ColorUtility.TryParseHtmlString(look.look_color, out c);
                    if (name.Contains("Dark")) c *= 0.65f;
                    c.a = 1f;
                    Set(m, c, look.look_smoothness, look.look_metallic);
                    mats[i] = m;
                    changed = true;
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        /// <summary>
        /// Paints some materials of some renderers with one item's colour (a wall painted with a paint can): every material whose plain name
        /// satisfies `matches` gets its own recoloured copy, so other renderers sharing the original are not touched.
        /// </summary>
        public static void Paint(IEnumerable<Renderer> renderers, System.Func<string, bool> matches, AssetCatalogItem look)
        {
            if (look == null) return;
            Color c = Color.white;
            ColorUtility.TryParseHtmlString(look.look_color, out c);
            c.a = 1f;
            foreach (Renderer r in renderers)
            {
                if (r == null) continue;
                Material[] mats = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null) continue;
                    string name = Plain(mats[i].name);
                    if (!matches(name)) continue;
                    var m = new Material(mats[i]) { name = name };
                    Set(m, name.Contains("Dark") ? c * 0.65f : name.Contains("Panel") && !IsPaneledDoor(name) ? c * 0.85f : c, look.look_smoothness, look.look_metallic);
                    if (IsPaneledDoor(name)) SetPicture(m, DoorPanelTexture());           // paint keeps the panels: the picture shades, the paint tints
                    else if (name.StartsWith("Shutter")) SetPicture(m, ShutterTexture());
                    mats[i] = m;
                    changed = true;
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        // ------------------------------------------------------------------ brick and stone pictures

        /// <summary>Fieldstone and anything else with "stone" in its id is laid as rough stone; every other masonry item is brick.</summary>
        private static bool IsStone(AssetCatalogItem item) { return item != null && item.id != null && item.id.Contains("stone"); }

        private static Texture2D s_brick, s_stone, s_doorPanels, s_shutter;

        /// <summary>A door slab of a generated model ("DoorPaneled"): flat geometry with UVs 0..1 across the leaf, the panels are a picture (DoorPanelTexture).</summary>
        private static bool IsPaneledDoor(string plainName) { return plainName.StartsWith("DoorPaneled"); }

        private static void SetPicture(Material m, Texture2D tex)
        {
            if (m.HasProperty("baseColorTexture")) m.SetTexture("baseColorTexture", tex);
            if (m.HasProperty("_BaseMap")) m.SetTexture("_BaseMap", tex);
        }

        private static float Hash(int a, int b)
        {
            unchecked
            {
                uint h = (uint)(a * 374761393 + b * 668265263);
                h = (h ^ (h >> 13)) * 1274126177u;
                return ((h ^ (h >> 16)) & 0xFFFF) / 65535f;
            }
        }

        /// <summary>
        /// A grayscale panelled door across the whole leaf (u across, v up): a flat stile-and-rail colour, a dark groove round each of four panels, and each
        /// panel a little lighter on its top and left edges and darker on its bottom and right ones, so they read as raised. Multiplied by the leaf's colour,
        /// so a painted door keeps its panels.
        /// </summary>
        private static Texture2D DoorPanelTexture()
        {
            if (s_doorPanels != null) return s_doorPanels;
            const int N = 256;
            float[] cols = { 0.105f, 0.455f, 0.545f, 0.895f };
            float[] rows = { 0.066f, 0.465f, 0.535f, 0.934f };           // two equal panels, the same rail above as below
            const float groove = 0.016f, bevel = 0.035f;
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
            {
                float v = (y + 0.5f) / N;
                for (int x = 0; x < N; x++)
                {
                    float u = (x + 0.5f) / N;
                    float g = 0.86f;                                               // stiles and rails
                    for (int ci = 0; ci < 4; ci += 2)
                        for (int ri = 0; ri < 4; ri += 2)
                        {
                            float du0 = u - cols[ci], du1 = cols[ci + 1] - u, dv0 = v - rows[ri], dv1 = rows[ri + 1] - v;
                            float inside = Mathf.Min(Mathf.Min(du0, du1), Mathf.Min(dv0, dv1));
                            if (inside > 0f)
                            {
                                float lit = Mathf.Clamp01(Mathf.Min(du0, dv1) / bevel), shade = Mathf.Clamp01(Mathf.Min(du1, dv0) / bevel);   // top and left light, bottom and right dark
                                float edge = Mathf.Lerp(0.62f, 1f, Mathf.Min(lit, 1f)) * Mathf.Lerp(0.78f, 1f, shade);
                                g = Mathf.Lerp(0.97f * edge, 0.97f, Mathf.Clamp01(inside / bevel));
                            }
                            else if (inside > -groove) g = Mathf.Min(g, 0.42f);       // the groove round the panel
                        }
                    px[y * N + x] = new Color(g, g, g, 1f);
                }
            }
            s_doorPanels = MakeTexture("DoorPanels", px, N);
            return s_doorPanels;
        }

        /// <summary>
        /// Grayscale louvred shutter across the whole slab (u across, v up): a frame round the edge and 22 slats inside, each slat light on its upper face and shadowed under
        /// the one above, with a dark gap between. Multiplied by the shutter's colour, so a painted shutter keeps its louvres.
        /// </summary>
        private static Texture2D ShutterTexture()
        {
            if (s_shutter != null) return s_shutter;
            const int N = 256, slats = 22;
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
            {
                float v = (y + 0.5f) / N;
                for (int x = 0; x < N; x++)
                {
                    float u = (x + 0.5f) / N;
                    float g = 0.88f;                                              // the frame
                    if (u > 0.12f && u < 0.88f && v > 0.05f && v < 0.95f)
                    {
                        float s = Mathf.Repeat(v * slats, 1f);
                        g = s < 0.14f ? 0.45f : Mathf.Lerp(0.98f, 0.7f, (s - 0.14f) / 0.86f);   // the gap under a slat, then its face dimming downwards
                    }
                    else if ((u > 0.105f && u < 0.12f && v > 0.035f && v < 0.965f) || (u > 0.88f && u < 0.895f && v > 0.035f && v < 0.965f)
                             || (v > 0.035f && v < 0.05f && u > 0.105f && u < 0.895f) || (v > 0.95f && v < 0.965f && u > 0.105f && u < 0.895f)) g = 0.55f;   // a thin groove between the frame and the louvres
                    px[y * N + x] = new Color(g, g, g, 1f);
                }
            }
            s_shutter = MakeTexture("ShutterLouvres", px, N);
            return s_shutter;
        }

        /// <summary>One metre of brickwork (the chimney's UVs are metres): sixteen level courses of 25 cm bricks, every other course shifted half a brick, light mortar between.</summary>
        private static Texture2D BrickTexture()
        {
            if (s_brick != null) return s_brick;
            const int N = 256, courseH = 16, brickW = 64, mortar = 2;   // 16 courses of 16 px fill the 256 px tile exactly: a course height that does not divide it left a double mortar line at every metre
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
            {
                int row = y / courseH;
                int shift = (row % 2) * (brickW / 2);
                for (int x = 0; x < N; x++)
                {
                    int bx = (x + shift) % brickW, by = y % courseH;
                    int brick = (x + shift) / brickW;
                    bool joint = bx < mortar || by < mortar;
                    float g;
                    if (joint) g = 0.92f + (Hash(x, y) - 0.5f) * 0.06f;
                    else g = 0.62f + Hash(brick, row) * 0.28f + (Hash(x * 7, y * 3) - 0.5f) * 0.07f;   // each brick its own shade, a little grain
                    px[y * N + x] = new Color(g, g * 0.985f, g * 0.97f, 1f);
                }
            }
            s_brick = MakeTexture("BrickWork", px, N);
            return s_brick;
        }

        /// <summary>One metre of rough fieldstone: irregular stones (a jittered grid of points, each pixel belongs to the nearest one) with dark gaps and a rounded shading.</summary>
        private static Texture2D StoneTexture()
        {
            if (s_stone != null) return s_stone;
            const int N = 256, G = 6;
            var pts = new Vector2[G * G];
            for (int j = 0; j < G; j++)
                for (int i = 0; i < G; i++)
                    pts[j * G + i] = new Vector2((i + 0.15f + 0.7f * Hash(i * 3, j * 5)) / G, (j + 0.15f + 0.7f * Hash(i * 7 + 1, j * 11 + 2)) / G);
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
            {
                for (int x = 0; x < N; x++)
                {
                    Vector2 p = new Vector2((x + 0.5f) / N, (y + 0.5f) / N);
                    int ci = Mathf.FloorToInt(p.x * G), cj = Mathf.FloorToInt(p.y * G);
                    float d1 = 9f, d2 = 9f;
                    int best = 0;
                    for (int dj = -1; dj <= 1; dj++)
                        for (int di = -1; di <= 1; di++)
                        {
                            int ni = ci + di, nj = cj + dj;
                            int wi = ((ni % G) + G) % G, wj = ((nj % G) + G) % G;                       // the cell wrapped round the tile
                            Vector2 q = pts[wj * G + wi] + new Vector2((ni - wi) / (float)G, (nj - wj) / (float)G);   // its point, moved to where the wrap puts it
                            float d = (q - p).magnitude;
                            if (d < d1) { d2 = d1; d1 = d; best = wj * G + wi; }
                            else if (d < d2) d2 = d;
                        }
                    float edge = (d2 - d1) * N;                       // pixels from the border between two stones
                    float stoneShade = 0.55f + Hash(best, 17) * 0.4f;
                    float round = Mathf.Clamp01(edge / 14f);          // lit in the middle of each stone, darker toward its edge
                    float g = stoneShade * (0.7f + 0.3f * round) + (Hash(x * 5, y * 9) - 0.5f) * 0.08f;
                    if (edge < 3f) g = 0.28f + Hash(x, y) * 0.06f;    // the gap between stones
                    g = Mathf.Clamp01(g);
                    px[y * N + x] = new Color(g, g * 0.99f, g * 0.97f, 1f);
                }
            }
            s_stone = MakeTexture("StoneWork", px, N);
            return s_stone;
        }

        private static Texture2D s_tile;

        /// <summary>One metre of floor tile: 4 x 4 tiles of 25 cm, each a touch lighter or darker, with a dark grout line between them. White with grey grout, so the item's colour tints it.</summary>
        private static Texture2D TileTexture()
        {
            if (s_tile != null) return s_tile;
            const int N = 256, T = 64, grout = 3;
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
            {
                for (int x = 0; x < N; x++)
                {
                    int tx = x % T, ty = y % T;
                    bool joint = tx < grout || ty < grout;
                    float g = joint ? 0.42f + (Hash(x, y) - 0.5f) * 0.04f : 0.94f - Hash(x / T, y / T) * 0.1f + (Hash(x * 3, y * 5) - 0.5f) * 0.025f;
                    px[y * N + x] = new Color(g, g, g, 1f);
                }
            }
            s_tile = MakeTexture("FloorTile", px, N);
            return s_tile;
        }

        private static Texture2D MakeTexture(string name, Color[] px, int n)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGB24, true) { name = name, wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.DontSave };
            tex.SetPixels(px);
            tex.Apply(true);
            return tex;
        }

        /// <summary>A door item's paintable materials: its slab, panels, edges and trim ("Door..."), not its knob and hinges ("DoorHardware") or its glass.</summary>
        public static bool DoorPaintable(string plainName) { return plainName.StartsWith("Door") && !plainName.StartsWith("DoorHardware"); }

        /// <summary>True when any of the renderers has a material whose plain name satisfies `matches`.</summary>
        public static bool HasMaterial(IEnumerable<Renderer> renderers, System.Func<string, bool> matches)
        {
            foreach (Renderer r in renderers)
            {
                if (r == null) continue;
                foreach (Material m in r.sharedMaterials) if (m != null && matches(Plain(m.name))) return true;
            }
            return false;
        }

        private static string Plain(string name)
        {
            int k = name.IndexOf(" (Instance)", System.StringComparison.Ordinal);
            return k >= 0 ? name.Substring(0, k) : name;
        }

        // glTFast's shader graph names its properties like glTF (baseColorFactor ...); a plain URP Lit material uses _BaseColor ...
        private static void Set(Material m, Color colour, float smoothness, float metallic)
        {
            if (m.HasProperty("baseColorFactor")) m.SetColor("baseColorFactor", colour);
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", colour);
            if (m.HasProperty("baseColorTexture")) m.SetTexture("baseColorTexture", null);   // a flat colour: the picture would tint it
            if (m.HasProperty("_BaseMap")) m.SetTexture("_BaseMap", null);
            if (m.HasProperty("metallicFactor")) m.SetFloat("metallicFactor", metallic);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", metallic);
            if (m.HasProperty("roughnessFactor")) m.SetFloat("roughnessFactor", 1f - smoothness);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", smoothness);
        }
    }
}
