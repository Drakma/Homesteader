using UnityEngine;

namespace Homesteader.Generation
{
    public static class BiomeNoise
    {
        /// <summary>
        /// 2D Simplex-style fractal noise with domain warping to guarantee amorphous, non-square contours.
        /// Warping frequency calibrated for 500m x 500m compact playable world map.
        /// </summary>
        public static float FractalNoise2D(float x, float z, float frequency, int octaves, float persistence, int seed)
        {
            float total = 0f;
            float freq = frequency;
            float amp = 1f;
            float maxAmp = 0f;

            // Fractional seed offsets eliminate Perlin integer lattice alignment and grid artifacts
            float seedX = (seed % 997) * 1.371f + 13.17f;
            float seedZ = (seed % 991) * 1.733f + 47.23f;

            // Multi-scale domain warping tailored for 500m map scale
            float warpX = Mathf.PerlinNoise((x * 0.006f) + seedX, (z * 0.006f) + 17.31f) * 35f;
            float warpZ = Mathf.PerlinNoise((x * 0.006f) + 31.73f, (z * 0.006f) + seedZ) * 35f;

            float wx = x + warpX;
            float wz = z + warpZ;

            for (int i = 0; i < octaves; i++)
            {
                float nx = (wx * freq) + seedX * 0.431f;
                float nz = (wz * freq) + seedZ * 0.587f;
                float val = Mathf.PerlinNoise(nx, nz);
                total += val * amp;
                maxAmp += amp;
                freq *= 2.0f;
                amp *= persistence;
            }

            return total / maxAmp;
        }

        /// <summary>
        /// High frequency dither noise used to organically blend biome edges and avoid sharp polygonal steps.
        /// </summary>
        public static float DitherNoise(float x, float z, float frequency = 0.35f)
        {
            return (Mathf.PerlinNoise(x * frequency, z * frequency) - 0.5f);
        }
    }
}
