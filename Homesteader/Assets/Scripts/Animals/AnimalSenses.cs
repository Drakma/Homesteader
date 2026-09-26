using System;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Animals
{
    /// <summary>
    /// Marks something an animal can sense and go to. Put it on a water trough, a food bowl, a
    /// shelter, a fence gate - anything - and give it tags. Animals register themselves as
    /// "animal" and "animal:&lt;species&gt;". The player is found through the "Player" Unity tag.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class AnimalTarget : MonoBehaviour
    {
        public List<string> tags = new List<string>();

        private static readonly List<AnimalTarget> all = new List<AnimalTarget>();
        public static IReadOnlyList<AnimalTarget> All => all;

        private void OnEnable() { if (!all.Contains(this)) all.Add(this); }
        private void OnDisable() { all.Remove(this); }

        public bool HasTag(string tag)
        {
            for (int i = 0; i < tags.Count; i++)
                if (string.Equals(tags[i], tag, StringComparison.OrdinalIgnoreCase)) return true;
            return false;
        }
    }

    public static class AnimalSenses
    {
        /// <summary>Nearest thing with this tag within maxDist (flat distance), ignoring `self`.</summary>
        public static Transform Nearest(Vector3 from, string tag, float maxDist, Transform self = null)
        {
            if (string.Equals(tag, "player", StringComparison.OrdinalIgnoreCase))
            {
                GameObject p = GameObject.FindWithTag("Player");
                if (p == null) return null;
                return Flat(from, p.transform.position) <= maxDist ? p.transform : null;
            }

            Transform best = null;
            float bestD = maxDist;
            IReadOnlyList<AnimalTarget> list = AnimalTarget.All;
            for (int i = 0; i < list.Count; i++)
            {
                AnimalTarget t = list[i];
                if (t == null || t.transform == self || !t.HasTag(tag)) continue;
                float d = Flat(from, t.transform.position);
                if (d <= bestD) { bestD = d; best = t.transform; }
            }
            return best;
        }

        public static float Flat(Vector3 a, Vector3 b)
        {
            float dx = a.x - b.x, dz = a.z - b.z;
            return Mathf.Sqrt(dx * dx + dz * dz);
        }
    }
}
