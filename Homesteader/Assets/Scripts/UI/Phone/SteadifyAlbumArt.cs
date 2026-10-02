// SteadifyAlbumArt.cs - Procedurally generates simple cover-art thumbnails for Steadify tracks.
//
// The free CC0/CC-BY tracks used by AudioManager come as audio-only files with no bundled
// cover art (typical for community OpenGameArt music submissions). Rather than pay for image
// generation, this draws small deterministic "album art" textures in code at runtime, using
// the same zero-cost procedural approach as ProceduralAudio.cs. Each track name hashes to a
// stable palette + abstract sound-wave pattern, so the same track always gets the same art
// for the whole session, and no external assets or licensing are involved.

using UnityEngine;
using System.Collections.Generic;

namespace Homesteader.UI
{
    public static class SteadifyAlbumArt
    {
        private static readonly Dictionary<string, Texture2D> _cache = new Dictionary<string, Texture2D>();

        // Homesteader's copper/slate palette pairs - background, then accent.
        private static readonly (Color bg, Color accent)[] Palettes =
        {
            (new Color32(43, 52, 66, 255), new Color32(246, 157, 75, 255)),   // slate + copper
            (new Color32(58, 74, 62, 255), new Color32(168, 209, 128, 255)),  // deep green + leaf
            (new Color32(60, 46, 66, 255), new Color32(198, 145, 226, 255)),  // plum + lilac
            (new Color32(38, 58, 74, 255), new Color32(110, 197, 219, 255)),  // teal + sky
            (new Color32(74, 52, 40, 255), new Color32(230, 178, 110, 255)),  // wood + wheat
        };

        /// <summary>The cover picture for a playlist (Resources/Audio/Covers/&lt;playlist folder&gt;.png), or null if it has none.</summary>
        public static Texture2D ForPlaylist(string playlistName)
        {
            if (string.IsNullOrEmpty(playlistName)) return null;
            string key = "playlist:" + playlistName;
            if (_cache.TryGetValue(key, out var t)) return t;
            t = Resources.Load<Texture2D>("Audio/Covers/" + playlistName);
            _cache[key] = t;
            return t;
        }

        /// <summary>
        /// Returns a cached, deterministically-generated cover texture for the given track name.
        /// Same name always yields the same image within this process.
        /// </summary>
        public static Texture2D GetOrCreate(string trackName, int size = 256)
        {
            if (string.IsNullOrEmpty(trackName)) trackName = "Unknown";
            if (_cache.TryGetValue(trackName, out var existing) && existing != null) return existing;

            var tex = Generate(trackName, size);
            _cache[trackName] = tex;
            return tex;
        }

        private static Texture2D Generate(string trackName, int size)
        {
            int seed = 0;
            unchecked
            {
                foreach (char c in trackName) seed = seed * 31 + c;
            }
            var rng = new System.Random(seed);

            var (bg, accent) = Palettes[System.Math.Abs(seed) % Palettes.Length];
            // Slight per-track jitter so palette repeats don't look identical.
            bg = Jitter(bg, rng, 0.05f);
            accent = Jitter(accent, rng, 0.08f);

            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;

            var pixels = new Color32[size * size];
            float cx = size * 0.5f;
            float cy = size * 0.5f;
            float maxDist = Mathf.Sqrt(cx * cx + cy * cy);

            // Pick a simple abstract motif: concentric "sound ring" bands + a soft diagonal sheen.
            int bandCount = 3 + rng.Next(0, 3);
            float bandWidth = maxDist / (bandCount * 2f);
            float ringOffset = (float)rng.NextDouble() * bandWidth;

            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float dx = x - cx;
                    float dy = y - cy;
                    float dist = Mathf.Sqrt(dx * dx + dy * dy);

                    // Base vertical gradient (background).
                    float t = (float)y / size;
                    Color c = Color.Lerp(bg, Color.Lerp(bg, Color.black, 0.25f), t);

                    // Concentric bands using the accent colour, fading with distance from center.
                    float ringPhase = (dist + ringOffset) % (bandWidth * 2f);
                    if (ringPhase < bandWidth)
                    {
                        float fade = 1f - Mathf.Clamp01(dist / maxDist);
                        float bandAlpha = Mathf.SmoothStep(0f, 1f, 1f - (ringPhase / bandWidth)) * fade * 0.9f;
                        c = Color.Lerp(c, accent, bandAlpha);
                    }

                    // Soft diagonal sheen for a bit of depth.
                    float sheen = Mathf.Clamp01(((x + y) / (float)(size * 2)) - 0.3f) * 0.15f;
                    c = Color.Lerp(c, Color.white, sheen);

                    pixels[y * size + x] = c;
                }
            }

            tex.SetPixels32(pixels);
            tex.Apply(false, false);
            return tex;
        }

        private static Color Jitter(Color c, System.Random rng, float amount)
        {
            float J() => ((float)rng.NextDouble() * 2f - 1f) * amount;
            return new Color(
                Mathf.Clamp01(c.r + J()),
                Mathf.Clamp01(c.g + J()),
                Mathf.Clamp01(c.b + J()),
                c.a);
        }
    }
}
