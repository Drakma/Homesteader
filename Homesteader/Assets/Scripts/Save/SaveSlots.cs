using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Homesteader.Save
{
    /// <summary>
    /// Where saves live and how they are named. Every save goes in the Saves folder next to the game (the Unity project folder in the editor):
    ///   Saves/Name.json                 the save made with the Save button or F9 (one per game name, overwritten)
    ///   Saves/Name-autosave.1.json      the newest autosave; .2 is the one before it, and so on up to the number kept (the oldest rolls off)
    ///   Saves/Name.world                the generated ground of that game (WorldSnapshot), shared by its saves
    /// Name is the name given when the game was started (New Game asks for it). Settings: autosave interval (minutes) and autosaves kept.
    /// </summary>
    public static class SaveSlots
    {
        public const string AutoTag = "-autosave.";
        private const string MinutesKey = "Homesteader.AutosaveMinutes", KeepKey = "Homesteader.AutosaveKeep";

        public static string Dir
        {
            get
            {
                string root = Directory.GetParent(Application.dataPath).FullName;
                string dir = Path.Combine(root, "Saves");
                if (!Directory.Exists(dir)) { Directory.CreateDirectory(dir); MigrateOld(dir); }
                return dir;
            }
        }

        /// <summary>The name of the game being played (what its saves are called).</summary>
        public static string CurrentName = "Homestead";

        /// <summary>The latest picture of the game (a small JPEG), taken now and then while playing (GameSaveManager). Saved beside each save.</summary>
        public static byte[] Thumbnail;

        public static string ThumbPath(string jsonPath) { return Path.ChangeExtension(jsonPath, ".jpg"); }

        public static void WriteThumb(string jsonPath)
        {
            try { if (Thumbnail != null) File.WriteAllBytes(ThumbPath(jsonPath), Thumbnail); }
            catch (Exception e) { Debug.LogWarning("[Save] could not write the picture: " + e.Message); }
        }

        /// <summary>A save the player picked in the Load list: the next scene load reads it instead of the newest one.</summary>
        public static string PendingLoadPath;

        private static int s_minutes = -1, s_keep = -1;

        public static int AutosaveMinutes
        {
            get { if (s_minutes < 0) s_minutes = Mathf.Clamp(PlayerPrefs.GetInt(MinutesKey, 5), 1, 120); return s_minutes; }
            set { s_minutes = Mathf.Clamp(value, 1, 120); PlayerPrefs.SetInt(MinutesKey, s_minutes); PlayerPrefs.Save(); }
        }

        public static int AutosaveKeep
        {
            get { if (s_keep < 0) s_keep = Mathf.Clamp(PlayerPrefs.GetInt(KeepKey, 5), 1, 50); return s_keep; }
            set { s_keep = Mathf.Clamp(value, 1, 50); PlayerPrefs.SetInt(KeepKey, s_keep); PlayerPrefs.Save(); }
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { s_minutes = s_keep = -1; PendingLoadPath = null; CurrentName = "Homestead"; }

        // ------------------------------------------------------------------ names

        public static string Sanitize(string name)
        {
            if (string.IsNullOrWhiteSpace(name)) return "Homestead";
            var sb = new System.Text.StringBuilder();
            char[] bad = Path.GetInvalidFileNameChars();
            foreach (char c in name.Trim()) if (Array.IndexOf(bad, c) < 0 && c != '.') sb.Append(c);
            string s = sb.ToString().Trim();
            if (s.Length > 40) s = s.Substring(0, 40).Trim();
            return s.Length == 0 ? "Homestead" : s;
        }

        public static string ManualPath(string name) { return Path.Combine(Dir, Sanitize(name) + ".json"); }
        public static string AutoPath(string name, int index) { return Path.Combine(Dir, Sanitize(name) + AutoTag + index + ".json"); }
        public static string WorldPath(string name) { return Path.Combine(Dir, Sanitize(name) + ".world"); }

        /// <summary>A name no existing game uses: the wanted one, or with " 2", " 3" ... after it.</summary>
        public static string UniqueName(string wanted)
        {
            string baseName = Sanitize(wanted);
            string name = baseName;
            for (int n = 2; GameExists(name); n++) name = baseName + " " + n;
            return name;
        }

        public static bool GameExists(string name)
        {
            foreach (Entry e in List()) if (string.Equals(e.GameName, name, StringComparison.OrdinalIgnoreCase)) return true;
            return File.Exists(WorldPath(name));
        }

        // ------------------------------------------------------------------ the list

        public struct Entry
        {
            public string Path;
            public string GameName;
            public bool IsAutosave;
            public int Index;            // autosaves: 1 = newest
            public DateTime Saved;       // local time
            public long Bytes;
            public int Seed;
            public int Day;              // in-game day of the year
            public string ThumbPath { get { return SaveSlots.ThumbPath(Path); } }
            public string Label { get { return IsAutosave ? GameName + " - autosave " + Index : GameName; } }
        }

        [Serializable]
        private class Header { public int version; public string savedAtUtc; public int worldSeed; public int dayOfYear; public string gameName; }

        /// <summary>Every save in the folder, newest first.</summary>
        public static List<Entry> List()
        {
            var list = new List<Entry>();
            string dir = Dir;
            foreach (string path in Directory.GetFiles(dir, "*.json"))
            {
                string file = System.IO.Path.GetFileNameWithoutExtension(path);
                if (file.EndsWith(".tmp", StringComparison.OrdinalIgnoreCase)) continue;
                var e = new Entry { Path = path, GameName = file, Bytes = new FileInfo(path).Length, Saved = File.GetLastWriteTime(path) };
                int k = file.LastIndexOf(AutoTag, StringComparison.Ordinal);
                if (k > 0 && int.TryParse(file.Substring(k + AutoTag.Length), out int idx)) { e.IsAutosave = true; e.Index = idx; e.GameName = file.Substring(0, k); }
                try
                {
                    var h = JsonUtility.FromJson<Header>(File.ReadAllText(path));
                    if (h != null)
                    {
                        e.Seed = h.worldSeed;
                        e.Day = h.dayOfYear;
                        if (!string.IsNullOrEmpty(h.gameName)) e.GameName = h.gameName;
                        if (DateTime.TryParse(h.savedAtUtc, null, System.Globalization.DateTimeStyles.RoundtripKind, out DateTime t)) e.Saved = t.ToLocalTime();
                    }
                }
                catch (Exception) { /* an unreadable file is still listed, with its file date */ }
                list.Add(e);
            }
            list.Sort((a, b) => b.Saved.CompareTo(a.Saved));
            return list;
        }

        public static bool Any { get { return List().Count > 0; } }

        /// <summary>
        /// The save the next load reads: the one picked in the Load list, else the newest. Also makes its game the current one (so its world
        /// snapshot and its autosaves are found). Null when there are no saves.
        /// </summary>
        public static string ResolveLoadPath()
        {
            string path = PendingLoadPath;
            if (path != null && !File.Exists(path)) path = null;
            if (path == null)
            {
                List<Entry> all = List();
                if (all.Count == 0) return null;
                path = all[0].Path;
            }
            foreach (Entry e in List())
                if (e.Path == path) { CurrentName = e.GameName; break; }
            return path;
        }

        // ------------------------------------------------------------------ autosave rolling

        /// <summary>Makes room for a new autosave: .1 becomes .2, .2 becomes .3 ... and whatever would pass the number kept is deleted.</summary>
        public static void RollAutosaves(string name)
        {
            int keep = AutosaveKeep;
            // anything beyond the number kept (the setting may have been lowered) goes
            for (int i = keep; i < keep + 60; i++)
            {
                string old = AutoPath(name, i);
                if (File.Exists(old)) File.Delete(old);
                if (File.Exists(ThumbPath(old))) File.Delete(ThumbPath(old));
            }
            for (int i = keep - 1; i >= 1; i--)
            {
                string from = AutoPath(name, i), to = AutoPath(name, i + 1);
                if (!File.Exists(from)) continue;
                if (File.Exists(to)) File.Delete(to);
                File.Move(from, to);
                if (File.Exists(ThumbPath(to))) File.Delete(ThumbPath(to));
                if (File.Exists(ThumbPath(from))) File.Move(ThumbPath(from), ThumbPath(to));
            }
        }

        /// <summary>Deletes a save. When it was the last one of its game, the game's world file goes too.</summary>
        public static void Delete(Entry e)
        {
            try { if (File.Exists(e.Path)) File.Delete(e.Path); if (File.Exists(e.ThumbPath)) File.Delete(e.ThumbPath); }
            catch (Exception ex) { Debug.LogWarning("[Save] could not delete " + e.Path + ": " + ex.Message); return; }
            foreach (Entry other in List())
                if (string.Equals(other.GameName, e.GameName, StringComparison.OrdinalIgnoreCase)) return;
            string world = WorldPath(e.GameName);
            try { if (File.Exists(world)) File.Delete(world); } catch (Exception) { }
        }

        /// <summary>"1.4 MB", "312 KB".</summary>
        public static string SizeText(long bytes)
        {
            if (bytes >= 1024 * 1024) return (bytes / 1048576.0).ToString("0.0") + " MB";
            return Mathf.Max(1, Mathf.RoundToInt(bytes / 1024f)) + " KB";
        }

        // ------------------------------------------------------------------ the old single save

        /// <summary>Saves made before the Saves folder existed (one autosave.json and world.snapshot in the data folder) are copied in once, as the game "Homestead".</summary>
        private static void MigrateOld(string dir)
        {
            try
            {
                string old = Path.Combine(Application.persistentDataPath, "Saves");
                string oldSave = Path.Combine(old, "autosave.json"), oldWorld = Path.Combine(old, "world.snapshot");
                if (File.Exists(oldSave)) File.Copy(oldSave, Path.Combine(dir, "Homestead.json"), false);
                if (File.Exists(oldWorld)) File.Copy(oldWorld, Path.Combine(dir, "Homestead.world"), false);
                if (File.Exists(oldSave)) Debug.Log("[Save] the earlier save was copied into the Saves folder as 'Homestead'.");
            }
            catch (Exception e) { Debug.LogWarning("[Save] could not copy the earlier save: " + e.Message); }
        }
    }
}
