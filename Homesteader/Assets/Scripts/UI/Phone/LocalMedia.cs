// LocalMedia.cs - what the PC is playing, from the Windows System Media Transport Controls (the same source as the volume
// flyout), through StreamingAssets/LocalMedia/LocalMediaHelper.exe (tools/build_local_media_helper.ps1). The helper prints
// a JSON line twice a second and takes commands on stdin. Without the helper (or off Windows) the transport buttons fall
// back to the Windows media keys and there is no track info.

using System.Diagnostics;
using System.IO;
using UnityEngine;

namespace Homesteader.UI
{
    public static class LocalMedia
    {
        public enum State { Unavailable, None, Paused, Playing }

        public struct Snapshot
        {
            public State State;
            public string Title, Artist, Album, App, ArtPath;
            public float Position, Length;   // seconds; Length <= 0 when unknown or live
            public bool CanSeek;
        }

        [System.Serializable]
        public class Source
        {
            public string app, title;
        }

        [System.Serializable]
        private class Line
        {
            public bool ok;
            public bool active;
            public string app, title, artist, album, art;
            public bool playing, canSeek;
            public float pos, len;
            public Source[] sessions;
        }

        private const byte VK_MEDIA_NEXT_TRACK = 0xB0;
        private const byte VK_MEDIA_PREV_TRACK = 0xB1;
        private const byte VK_MEDIA_PLAY_PAUSE = 0xB3;
        private const uint KEYEVENTF_EXTENDEDKEY = 0x1;
        private const uint KEYEVENTF_KEYUP = 0x2;

#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern void keybd_event(byte vk, byte scan, uint flags, System.UIntPtr extra);
#endif

        private const string SourceKey = "steadify_local_source";

        private static Process _proc;
        private static readonly object Lock = new object();
        private static Line _latest;
        private static float _latestAt;
        private static bool _startFailed;

        private static Texture2D _art;
        private static string _artPath = "";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            Stop();
            _startFailed = false;
            Application.quitting -= Stop;
            Application.quitting += Stop;
        }

        public static bool Supported
        {
            get
            {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
                return true;
#else
                return false;
#endif
            }
        }

        /// <summary>True when the helper is running, so the track and its cover are known.</summary>
        public static bool HasInfo => EnsureStarted();

        private static string HelperPath => Path.Combine(Application.streamingAssetsPath, "LocalMedia", "LocalMediaHelper.exe");

        private static bool EnsureStarted()
        {
            if (!Supported) return false;
            if (_proc != null && !_proc.HasExited) return true;
            if (_startFailed) return false;
            try
            {
                if (!File.Exists(HelperPath)) { _startFailed = true; return false; }
                var info = new ProcessStartInfo(HelperPath)
                {
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                };
                _proc = Process.Start(info);
                _proc.OutputDataReceived += (s, e) => OnLine(e.Data);
                _proc.BeginOutputReadLine();
                string saved = PlayerPrefs.GetString(SourceKey, "");
                if (saved != "") _proc.StandardInput.WriteLine("select " + saved);
                return true;
            }
            catch
            {
                _startFailed = true;
                _proc = null;
                return false;
            }
        }

        private static void OnLine(string data)
        {
            if (string.IsNullOrEmpty(data)) return;
            try
            {
                Line l = JsonUtility.FromJson<Line>(data);
                lock (Lock) { _latest = l; }
            }
            catch { }
        }

        public static void Stop()
        {
            try { if (_proc != null && !_proc.HasExited) { _proc.StandardInput.Close(); _proc.Kill(); } } catch { }
            _proc = null;
            lock (Lock) { _latest = null; }
        }

        /// <summary>The latest reading. Cheap: parsing happens on the helper's output thread.</summary>
        public static Snapshot Read()
        {
            var snap = new Snapshot { State = State.Unavailable, Title = "", Artist = "", Album = "", App = "", ArtPath = "" };
            if (!EnsureStarted()) return snap;
            Line l;
            lock (Lock) { l = _latest; }
            if (l == null || !l.ok) { snap.State = State.None; return snap; }
            if (!l.active || string.IsNullOrEmpty(l.title)) { snap.State = State.None; return snap; }
            snap.State = l.playing ? State.Playing : State.Paused;
            snap.Title = l.title; snap.Artist = l.artist ?? ""; snap.Album = l.album ?? ""; snap.App = l.app ?? "";
            snap.ArtPath = l.art ?? "";
            snap.Position = l.pos; snap.Length = l.len; snap.CanSeek = l.canSeek;
            return snap;
        }

        /// <summary>The cover for a snapshot, loaded once per file; null when there is none.</summary>
        public static Texture2D Art(Snapshot s)
        {
            if (s.ArtPath == _artPath) return _art;
            if (_art != null) Object.Destroy(_art);
            _art = null;
            _artPath = s.ArtPath;
            if (string.IsNullOrEmpty(_artPath)) return null;
            try
            {
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
                if (tex.LoadImage(File.ReadAllBytes(_artPath))) _art = tex;
                else Object.Destroy(tex);
            }
            catch { }
            return _art;
        }

        /// <summary>The app chosen to control; empty = whatever Windows treats as current.</summary>
        public static string SelectedApp => PlayerPrefs.GetString(SourceKey, "");

        /// <summary>Programs that currently have a media session (one per app; a browser is one entry, not one per tab).</summary>
        public static Source[] Sources()
        {
            if (!EnsureStarted()) return new Source[0];
            lock (Lock) { return _latest?.sessions ?? new Source[0]; }
        }

        public static void Select(string app)
        {
            PlayerPrefs.SetString(SourceKey, app ?? "");
            if (!EnsureStarted()) return;
            try { _proc.StandardInput.WriteLine("select " + (app ?? "")); } catch { }
        }

        /// <summary>A readable name for a session id: "Spotify.exe" is Spotify, "Microsoft.ZuneMusic_8wekyb3d8bbwe!App" is ZuneMusic.</summary>
        public static string FriendlyName(string app)
        {
            if (string.IsNullOrEmpty(app)) return "Unknown";
            string n = app;
            int bang = n.LastIndexOf('!');
            if (bang >= 0 && bang < n.Length - 1) n = n.Substring(bang + 1);
            int us = n.IndexOf('_');
            if (us > 0) n = n.Substring(0, us);
            if (n.EndsWith(".exe", System.StringComparison.OrdinalIgnoreCase)) n = n.Substring(0, n.Length - 4);
            int dot = n.LastIndexOf('.');
            if (dot >= 0 && dot < n.Length - 1) n = n.Substring(dot + 1);
            return n.Length > 0 ? char.ToUpperInvariant(n[0]) + n.Substring(1) : app;
        }

        public static void PlayPause() => Send("toggle", VK_MEDIA_PLAY_PAUSE);
        public static void Next() => Send("next", VK_MEDIA_NEXT_TRACK);
        public static void Previous() => Send("prev", VK_MEDIA_PREV_TRACK);

        public static void Seek(float seconds)
        {
            if (!EnsureStarted()) return;
            try { _proc.StandardInput.WriteLine("seek " + seconds.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture)); } catch { }
        }

        private static void Send(string command, byte fallbackKey)
        {
            if (EnsureStarted())
            {
                try { _proc.StandardInput.WriteLine(command); return; } catch { }
            }
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
            keybd_event(fallbackKey, 0, KEYEVENTF_EXTENDEDKEY, System.UIntPtr.Zero);
            keybd_event(fallbackKey, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, System.UIntPtr.Zero);
#endif
        }

        public static string FormatTime(float seconds)
        {
            if (seconds < 0f || float.IsNaN(seconds)) seconds = 0f;
            int total = Mathf.FloorToInt(seconds);
            return $"{total / 60}:{total % 60:00}";
        }
    }
}
