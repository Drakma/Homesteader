// RadioStationDefinition.cs - a Steadify radio station as mod data (content type "radio", assets/_radio/*.json,
// schema assets/_schemas/radio_station.schema.json). The templated script writer reads the sentence banks; the Claude
// script writer reads the persona and speaker styles. RadioRegistry holds every loaded station.

using System;
using System.Collections.Generic;
using Homesteader.Modding;

namespace Homesteader.Radio
{
    public sealed class RadioSpeaker
    {
        public string Id = "host";
        public string Name = "Host";
        public int Voice;             // speaker id in the TTS voices file
        public float Speed = 1f;
        public string Style = "";
    }

    public sealed class RadioStationDefinition
    {
        public string Id;
        public string Name;
        public string Tagline = "";
        public string Frequency = "";
        public string Format = "weather";
        public float EpisodeMinutes = 3f;
        public string Persona = "";
        public string ModId = "core";
        public readonly List<RadioSpeaker> Speakers = new List<RadioSpeaker>();
        public readonly List<string> Segments = new List<string>();
        public readonly Dictionary<string, List<string>> Lines = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        public readonly Dictionary<string, Dictionary<string, string>> Phrases = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);

        public RadioSpeaker FindSpeaker(string id)
        {
            foreach (RadioSpeaker s in Speakers)
                if (string.Equals(s.Id, id, StringComparison.OrdinalIgnoreCase)) return s;
            return Speakers.Count > 0 ? Speakers[0] : null;
        }

        public string Phrase(string table, string key, string fallback = "")
        {
            if (Phrases.TryGetValue(table, out var t) && t.TryGetValue(key, out string v)) return v;
            return fallback;
        }

        /// <summary>Parses one station file. Returns null (with errors) when the file is unusable.</summary>
        public static RadioStationDefinition FromJson(ModJsonValue root, string modId, List<string> errors)
        {
            if (root == null || !root.IsObject) { errors.Add("station file is not a JSON object"); return null; }
            var d = new RadioStationDefinition { ModId = modId ?? "core" };
            d.Id = root.RequireString("id", errors, "station");
            d.Name = root.Get("name").AsString(d.Id);
            d.Tagline = root.Get("tagline").AsString("");
            d.Frequency = root.Get("frequency").AsString("");
            d.Format = root.Get("format").AsString("weather");
            d.EpisodeMinutes = root.Get("episode_minutes").AsFloat(3f);
            d.Persona = root.Get("persona").AsString("");

            foreach (ModJsonValue s in root.Get("speakers").Items)
            {
                if (!s.IsObject) continue;
                d.Speakers.Add(new RadioSpeaker
                {
                    Id = s.Get("id").AsString("host"),
                    Name = s.Get("name").AsString("Host"),
                    Voice = s.Get("voice").AsInt(0),
                    Speed = s.Get("speed").AsFloat(1f),
                    Style = s.Get("style").AsString(""),
                });
            }
            if (d.Speakers.Count == 0) errors.Add($"station '{d.Id}' has no speakers");

            d.Segments.AddRange(root.Get("segments").AsStringList());
            if (d.Segments.Count == 0) errors.Add($"station '{d.Id}' has no segments");

            ModJsonValue lines = root.Get("lines");
            if (lines.IsObject)
                foreach (KeyValuePair<string, ModJsonValue> kv in lines.ObjectValue)
                    d.Lines[kv.Key] = kv.Value.AsStringList();

            ModJsonValue phrases = root.Get("phrases");
            if (phrases.IsObject)
            {
                foreach (KeyValuePair<string, ModJsonValue> kv in phrases.ObjectValue)
                {
                    if (!kv.Value.IsObject) continue;
                    var table = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                    foreach (KeyValuePair<string, ModJsonValue> p in kv.Value.ObjectValue)
                        table[p.Key] = p.Value.AsString("");
                    d.Phrases[kv.Key] = table;
                }
            }

            return string.IsNullOrEmpty(d.Id) ? null : d;
        }
    }

    /// <summary>Every radio station the mods loaded, in load order. Core stations win id collisions (the mod one is rejected).</summary>
    public static class RadioRegistry
    {
        private static readonly List<RadioStationDefinition> s_all = new List<RadioStationDefinition>();
        private static readonly Dictionary<string, RadioStationDefinition> s_byId = new Dictionary<string, RadioStationDefinition>(StringComparer.OrdinalIgnoreCase);

        public static IReadOnlyList<RadioStationDefinition> All => s_all;
        public static event Action Changed;

        public static void Clear()
        {
            s_all.Clear();
            s_byId.Clear();
            Changed?.Invoke();
        }

        public static bool TryGet(string id, out RadioStationDefinition def)
        {
            def = null;
            return !string.IsNullOrEmpty(id) && s_byId.TryGetValue(id, out def);
        }

        public static void LoadFromJson(ModJsonValue root, string modId, Action<string> warn)
        {
            var errors = new List<string>();
            RadioStationDefinition def = RadioStationDefinition.FromJson(root, modId, errors);
            foreach (string e in errors) warn?.Invoke(e);
            if (def == null) return;
            if (s_byId.TryGetValue(def.Id, out RadioStationDefinition existing))
            {
                warn?.Invoke($"radio station '{def.Id}' from '{modId}' collides with the one from '{existing.ModId}' and was skipped");
                return;
            }
            s_all.Add(def);
            s_byId[def.Id] = def;
            Changed?.Invoke();
        }
    }
}
