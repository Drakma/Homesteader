using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The ground water under the world (docs/WELLS.md): for any spot, how deep a drilled well has to go to reach water and how much the aquifer there gives
    /// (liters an hour, the most any pump can draw from it). Both are smooth noise fields fixed by the world seed, so the same spot always answers the same, nothing
    /// is saved, and a player can look around for a shallow, generous spot by hovering a well blueprint. Low ground (near the water level) is a little shallower.
    /// </summary>
    public static class WaterTable
    {
        public const float MinDepthM = 8f, MaxDepthM = 85f;
        public const float MinYieldLph = 600f, MaxYieldLph = 4200f;

        private static int s_seed = int.MinValue;
        private static Vector2 s_offA, s_offB;

        private static void EnsureSeed()
        {
            var gen = Object.FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>();
            int seed = gen != null ? gen.worldSeed : 8462;
            if (seed == s_seed) return;
            s_seed = seed;
            var rng = new System.Random(seed ^ 0x5eed7a);
            s_offA = new Vector2((float)rng.NextDouble() * 9000f, (float)rng.NextDouble() * 9000f);
            s_offB = new Vector2((float)rng.NextDouble() * 9000f, (float)rng.NextDouble() * 9000f);
        }

        private static float Field(Vector3 p, Vector2 off, float scale)
        {
            float a = Mathf.PerlinNoise(p.x * scale + off.x, p.z * scale + off.y);
            float b = Mathf.PerlinNoise(p.x * scale * 2.7f + off.y, p.z * scale * 2.7f + off.x);
            return Mathf.Clamp01(a * 0.75f + b * 0.25f);
        }

        /// <summary>Metres down to water at this spot.</summary>
        public static float DepthM(Vector3 p)
        {
            EnsureSeed();
            float d = Mathf.Lerp(MinDepthM, MaxDepthM, Field(p, s_offA, 0.006f));
            float above = Homesteader.Generation.TerrainHeightDetector.GetGroundY(p) - Homesteader.Generation.TerrainHeightDetector.GetWaterY();
            d -= Mathf.Clamp(6f - above, 0f, 6f) * 2f;   // within a few metres of the water level the water is nearer
            return Mathf.Round(Mathf.Clamp(d, MinDepthM, MaxDepthM));
        }

        /// <summary>The most the aquifer at this spot gives, in liters an hour.</summary>
        public static float YieldLph(Vector3 p)
        {
            EnsureSeed();
            return Mathf.Round(Mathf.Lerp(MinYieldLph, MaxYieldLph, Field(p, s_offB, 0.011f)) / 50f) * 50f;
        }
    }
}
