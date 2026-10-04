using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using UnityEngine;

namespace Homesteader.Generation
{
    /// <summary>
    /// What world generation produced, kept so a saved game does not have to regenerate its ground: the heightmap, the biome map, the water
    /// features (river, branches, ponds) and the road line. Written beside the save (Saves/Name.world) the first time the world is saved, and
    /// read back at the start of the next run: the generator then uses these instead of evaluating its noise functions, so a change to the
    /// generator's code, the mods or the rules can never move the ground a save was made on. Everything else (water mask, distance fields,
    /// the road mask, trees) is still derived from these at load. See docs/SAVE_GAME.md.
    /// </summary>
    public sealed class WorldSnapshot
    {
        public const int Version = 1;
        private const int Magic = 0x57534E50;   // "WSNP"

        public int Seed;
        public int HeightRes, MapRes;
        public float SizeX, SizeZ, SizeY;
        public float[,] Heights;                 // [z, x], 0..1 of the terrain height, as generated (before any building ground grading)
        public byte[] Modes;                     // MapRes * MapRes biome mode ids
        public byte[] Rgb;                       // MapRes * MapRes * 3 biome tint
        public List<float[]> Rivers = new List<float[]>();   // main river first, then the branches: start xy, end xy, half width, meander amp / freq / phase
        public List<float[]> Ponds = new List<float[]>();    // centre xy, radius, noise seed, irregularity
        public List<Vector2> Road = new List<Vector2>();
        public float RoadHalfWidth;

        public static string Path => Homesteader.Save.SaveSlots.WorldPath(Homesteader.Save.SaveSlots.CurrentName);   // one per game, beside its saves

        public static bool Exists => File.Exists(Path);

        public static void Delete()
        {
            try { if (File.Exists(Path)) File.Delete(Path); }
            catch (System.Exception e) { Debug.LogWarning("[WorldSnapshot] could not delete: " + e.Message); }
        }

        /// <summary>True when this snapshot was made for a world of these dimensions and seed.</summary>
        public bool Matches(int seed, int heightRes, int mapRes, float sx, float sz, float sy)
        {
            return Heights != null && Modes != null && Seed == seed && HeightRes == heightRes && MapRes == mapRes
                && Mathf.Approximately(SizeX, sx) && Mathf.Approximately(SizeZ, sz) && Mathf.Approximately(SizeY, sy);
        }

        public void Write()
        {
            Directory.CreateDirectory(System.IO.Path.GetDirectoryName(Path));
            string tmp = Path + ".tmp";
            using (FileStream fs = File.Create(tmp))
            using (var z = new DeflateStream(fs, System.IO.Compression.CompressionLevel.Fastest))
            using (var w = new BinaryWriter(z))
            {
                w.Write(Magic); w.Write(Version);
                w.Write(Seed); w.Write(HeightRes); w.Write(MapRes);
                w.Write(SizeX); w.Write(SizeZ); w.Write(SizeY);
                for (int zz = 0; zz < HeightRes; zz++)
                    for (int x = 0; x < HeightRes; x++) w.Write(Heights[zz, x]);
                w.Write(Modes);
                w.Write(Rgb);
                w.Write(Rivers.Count);
                foreach (float[] r in Rivers) { w.Write(r.Length); foreach (float f in r) w.Write(f); }
                w.Write(Ponds.Count);
                foreach (float[] p in Ponds) { w.Write(p.Length); foreach (float f in p) w.Write(f); }
                w.Write(RoadHalfWidth);
                w.Write(Road.Count);
                foreach (Vector2 p in Road) { w.Write(p.x); w.Write(p.y); }
            }
            if (File.Exists(Path)) File.Delete(Path);
            File.Move(tmp, Path);
        }

        /// <summary>The snapshot on disk, or null when there is none or it cannot be read.</summary>
        public static WorldSnapshot TryRead()
        {
            if (!File.Exists(Path)) return null;
            try
            {
                using (FileStream fs = File.OpenRead(Path))
                using (var z = new DeflateStream(fs, CompressionMode.Decompress))
                using (var r = new BinaryReader(z))
                {
                    if (r.ReadInt32() != Magic || r.ReadInt32() != Version) return null;
                    var s = new WorldSnapshot { Seed = r.ReadInt32(), HeightRes = r.ReadInt32(), MapRes = r.ReadInt32() };
                    s.SizeX = r.ReadSingle(); s.SizeZ = r.ReadSingle(); s.SizeY = r.ReadSingle();
                    if (s.HeightRes < 2 || s.HeightRes > 4097 || s.MapRes < 2 || s.MapRes > 8192) return null;
                    s.Heights = new float[s.HeightRes, s.HeightRes];
                    for (int zz = 0; zz < s.HeightRes; zz++)
                        for (int x = 0; x < s.HeightRes; x++) s.Heights[zz, x] = r.ReadSingle();
                    s.Modes = r.ReadBytes(s.MapRes * s.MapRes);
                    s.Rgb = r.ReadBytes(s.MapRes * s.MapRes * 3);
                    if (s.Modes.Length != s.MapRes * s.MapRes || s.Rgb.Length != s.MapRes * s.MapRes * 3) return null;
                    int n = r.ReadInt32();
                    for (int i = 0; i < n; i++) { int len = r.ReadInt32(); var f = new float[len]; for (int k = 0; k < len; k++) f[k] = r.ReadSingle(); s.Rivers.Add(f); }
                    n = r.ReadInt32();
                    for (int i = 0; i < n; i++) { int len = r.ReadInt32(); var f = new float[len]; for (int k = 0; k < len; k++) f[k] = r.ReadSingle(); s.Ponds.Add(f); }
                    s.RoadHalfWidth = r.ReadSingle();
                    n = r.ReadInt32();
                    for (int i = 0; i < n; i++) s.Road.Add(new Vector2(r.ReadSingle(), r.ReadSingle()));
                    return s;
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[WorldSnapshot] could not read the snapshot, the world will be regenerated: " + e.Message);
                return null;
            }
        }
    }
}
