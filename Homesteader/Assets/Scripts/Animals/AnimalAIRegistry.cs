using System;
using System.Collections.Generic;
using Homesteader.Modding;
using UnityEngine;

namespace Homesteader.Animals
{
    /// <summary>All animal AI definitions loaded from mods. Later mods override earlier ones by id.</summary>
    public static class AnimalAIRegistry
    {
        private static readonly Dictionary<string, AnimalAIDefinition> byId =
            new Dictionary<string, AnimalAIDefinition>(StringComparer.OrdinalIgnoreCase);

        // Raw definitions stay in byId; the inheritance-resolved versions are built lazily and cached.
        private static readonly Dictionary<string, AnimalAIDefinition> resolved =
            new Dictionary<string, AnimalAIDefinition>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Every non-template definition, inheritance applied.</summary>
        public static IEnumerable<AnimalAIDefinition> All
        {
            get
            {
                foreach (string id in new List<string>(byId.Keys))
                {
                    AnimalAIDefinition d = Get(id);
                    if (d != null && !d.Abstract) yield return d;
                }
            }
        }

        public static void Clear() { byId.Clear(); resolved.Clear(); }

        public static void Register(AnimalAIDefinition def)
        {
            if (def == null) return;
            byId[def.Id] = def;
            resolved.Clear();
        }

        /// <summary>The definition with its `extends` chain merged in, or null.</summary>
        public static AnimalAIDefinition Get(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            if (resolved.TryGetValue(id, out var done)) return done;
            if (!byId.ContainsKey(id)) return null;
            AnimalAIDefinition r = Resolve(id, new HashSet<string>(StringComparer.OrdinalIgnoreCase));
            resolved[id] = r;
            if (r != null) AnimalAIParser.CrossCheck(r, m => Debug.LogWarning("[AnimalAI] " + m));
            return r;
        }

        /// <summary>Merges parents (in `extends` order) under the definition: the child overrides needs / animation
        /// slots / senses / movement keys by name, and behaviours by id (`disabled` removes one).</summary>
        private static AnimalAIDefinition Resolve(string id, HashSet<string> chain)
        {
            if (!byId.TryGetValue(id, out AnimalAIDefinition raw)) return null;
            if (!chain.Add(id)) { Debug.LogWarning($"[AnimalAI] '{id}': circular \"extends\" chain"); return null; }

            var outp = new AnimalAIDefinition
            {
                Id = raw.Id, SourceMod = raw.SourceMod, Abstract = raw.Abstract,
                Extends = raw.Extends, AppliesTo = raw.AppliesTo, Tags = new List<string>(), RawSenses = raw.RawSenses, RawMovement = raw.RawMovement,
            };
            var behaviors = new List<BehaviorDef>();

            void Overlay(AnimalAIDefinition src, bool isResolved)
            {
                outp.SenseLayers.AddRange(isResolved ? src.SenseLayers : new List<ModJsonValue> { src.RawSenses ?? ModJsonValue.Null });
                outp.MovementLayers.AddRange(isResolved ? src.MovementLayers : new List<ModJsonValue> { src.RawMovement ?? ModJsonValue.Null });
                foreach (string t in src.Tags) if (!outp.Tags.Contains(t)) outp.Tags.Add(t);
                foreach (var kv in src.Needs) outp.Needs[kv.Key] = kv.Value;
                foreach (var kv in src.Animations) outp.Animations[kv.Key] = kv.Value;
                foreach (BehaviorDef b in src.Behaviors)
                {
                    int at = behaviors.FindIndex(x => string.Equals(x.Id, b.Id, StringComparison.OrdinalIgnoreCase));
                    if (b.Disabled) { if (at >= 0) behaviors.RemoveAt(at); continue; }
                    if (at >= 0) behaviors[at] = b; else behaviors.Add(b);
                }
            }

            foreach (string parentId in raw.Extends)
            {
                if (!byId.ContainsKey(parentId)) { Debug.LogWarning($"[AnimalAI] '{id}' extends unknown '{parentId}'"); continue; }
                AnimalAIDefinition parent = Resolve(parentId, new HashSet<string>(chain, StringComparer.OrdinalIgnoreCase));
                if (parent != null) Overlay(parent, true);
            }
            Overlay(raw, false);
            foreach (ModJsonValue l in outp.SenseLayers) AnimalAIParser.ApplySenses(outp.Senses, l);
            foreach (ModJsonValue l in outp.MovementLayers) AnimalAIParser.ApplyMovement(outp.Movement, l);
            outp.Behaviors = behaviors;
            return outp;
        }

        /// <summary>The definition whose applies_to matches this animal: an exact item id first, then a wildcard
        /// pattern ("*_cow", "animal_cat_*"), then "species:x".</summary>
        public static AnimalAIDefinition FindFor(string itemId, string species)
        {
            AnimalAIDefinition wildcardMatch = null, speciesMatch = null;
            foreach (AnimalAIDefinition d in All)
            {
                foreach (string a in d.AppliesTo)
                {
                    if (!string.IsNullOrEmpty(itemId) && string.Equals(a, itemId, StringComparison.OrdinalIgnoreCase)) return d;
                    if (!string.IsNullOrEmpty(itemId) && a.IndexOf('*') >= 0 && GlobMatch(a, itemId)) wildcardMatch = wildcardMatch ?? d;
                    if (!string.IsNullOrEmpty(species) &&
                        string.Equals(a, "species:" + species, StringComparison.OrdinalIgnoreCase)) speciesMatch = d;
                }
            }
            return wildcardMatch ?? speciesMatch;
        }

        /// <summary>'*' matches any run of characters; everything else is literal, case-insensitive.</summary>
        private static bool GlobMatch(string pattern, string text)
        {
            string[] parts = pattern.Split('*');
            int pos = 0;
            for (int i = 0; i < parts.Length; i++)
            {
                if (parts[i].Length == 0) continue;
                int at = text.IndexOf(parts[i], pos, StringComparison.OrdinalIgnoreCase);
                if (at < 0 || (i == 0 && at != 0)) return false;
                pos = at + parts[i].Length;
            }
            return parts[parts.Length - 1].Length == 0 || text.EndsWith(parts[parts.Length - 1], StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>Parses one animal_ai JSON document from a mod and registers it.</summary>
        public static void LoadFromJson(ModJsonValue root, string modId, Action<string> warn)
        {
            // A file may hold one definition or {"definitions": [ ... ]}.
            if (root.Has("definitions"))
            {
                foreach (ModJsonValue d in root.Get("definitions").Items) LoadOne(d, modId, warn);
                return;
            }
            LoadOne(root, modId, warn);
        }

        private static void LoadOne(ModJsonValue root, string modId, Action<string> warn)
        {
            AnimalAIDefinition def = AnimalAIParser.Parse(root, modId, warn);
            if (def == null) return;
            if (byId.TryGetValue(def.Id, out AnimalAIDefinition old))
                Debug.Log($"[AnimalAI] '{def.Id}' from mod '{modId}' replaces the one from '{old.SourceMod}'.");
            Register(def);
        }
    }
}
