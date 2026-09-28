using UnityEngine;

namespace Homesteader.Generation
{
    public static class BiomeNoise
    {
        /// <summary>
        /// Hash-based value noise. Different seeds produce completely different patterns
        /// (unlike Perlin with small offsets, which just shifts the same features slightly).
        /// </summary>
        public static float FractalNoise2D(float x, float z, float frequency, int octaves, float persistence, int seed)
        {
            // Seed-based coordinate rotation so the noise grid doesn't align with world axes
            float angle = (seed % 360) * Mathf.Deg2Rad;
            float cos = Mathf.Cos(angle);
            float sin = Mathf.Sin(angle);
            float rx = x * cos - z * sin;
            float rz = x * sin + z * cos;

            // Seed-based frequency variation so different worlds have different feature scales
            float freqMul = 1.0f + (seed % 17) * 0.03f;

            float total = 0f;
            float freq = frequency * freqMul;
            float amp = 1f;
            float maxAmp = 0f;

            for (int i = 0; i < octaves; i++)
            {
                float val = ValueNoise2D(rx * freq + seed * 0.137f, rz * freq + seed * 0.589f, seed + i * 31);
                total += val * amp;
                maxAmp += amp;
                freq *= 2.0f;
                amp *= persistence;
            }

            return total / maxAmp;
        }

        /// <summary>
        /// Single-octave value noise with smoothstep interpolation. Returns [0,1].
        /// </summary>
        public static float ValueNoise2D(float x, float z, int seed)
        {
            int xi = Mathf.FloorToInt(x);
            int zi = Mathf.FloorToInt(z);
            float xf = x - xi;
            float zf = z - zi;

            float u = xf * xf * (3f - 2f * xf);
            float v = zf * zf * (3f - 2f * zf);

            float a = Hash01(xi, zi, seed);
            float b = Hash01(xi + 1, zi, seed);
            float c = Hash01(xi, zi + 1, seed);
            float d = Hash01(xi + 1, zi + 1, seed);

            return Mathf.Lerp(Mathf.Lerp(a, b, u), Mathf.Lerp(c, d, u), v);
        }

        /// <summary>
        /// Deterministic hash to [0,1] from integer coordinates + seed.
        /// </summary>
        public static float Hash01(int x, int z, int seed)
        {
            uint h = (uint)(seed * 374761393 + x * 668265263 + z * 2147483647);
            h = (h ^ (h >> 13)) * 1274126177u;
            h = h ^ (h >> 16);
            return (h & 0xFFFFFF) / (float)0xFFFFFF;
        }

        /// <summary>
        /// High frequency dither noise used to organically blend biome edges and avoid sharp polygonal steps.
        /// </summary>
        public static float DitherNoise(float x, float z, float frequency = 0.35f)
        {
            return (ValueNoise2D(x * frequency, z * frequency, 0) - 0.5f);
        }
    }
}
