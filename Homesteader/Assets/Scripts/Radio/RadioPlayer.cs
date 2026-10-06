// RadioPlayer.cs - the radio behind Steadify's Radio tab. Tune a station and it: gathers today's facts, writes the
// episode (templated, or Claude when that mode is on and has a key), speaks each line with the local Kokoro voice on a
// worker thread a few lines ahead of playback, and plays them through its own AudioSource at the music volume. When
// the episode ends it waits a moment and starts again (a new episode once the game day has turned), so the station is
// always on air. Episodes and their audio are cached under <persistentDataPath>/Radio so a replay or a reload is
// instant and a Claude episode is paid for once. Without the voice pack the transcript still scrolls, silently.
// Saved state: GameSave.radioStation / radioLine / radioPaused (GameSaveManager Capture / ApplySave).

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using Homesteader.Audio;
using Homesteader.Radio.Tts;
using UnityEngine;

namespace Homesteader.Radio
{
    public sealed class RadioPlayer : MonoBehaviour
    {
        public enum RadioState { Off, Writing, Synthesizing, Playing, Paused, Failed }

        public static RadioPlayer Instance { get; private set; }

        public RadioStationDefinition Station { get; private set; }
        public RadioEpisode Episode { get; private set; }
        public RadioState State { get; private set; } = RadioState.Off;
        public int LineIndex { get; private set; } = -1;
        public string StatusText { get; private set; } = "";
        public string LastError { get; private set; } = "";
        public bool IsOn => State != RadioState.Off && State != RadioState.Failed;
        public bool VoiceAvailable => _engine != null && _engine.IsReady;
        public string VoiceStatus => VoiceAvailable ? _engine.Name : KokoroTtsEngine.LastStatus;
        public float Progress01 => Episode == null || Episode.lines.Count == 0 ? 0f : Mathf.Clamp01((LineIndex + (_source.isPlaying && _source.clip != null ? _source.time / _source.clip.length : 0f)) / Episode.lines.Count);

        /// <summary>Fired whenever the station, episode, state or current line changes (the Steadify radio tab listens).</summary>
        public event Action Changed;

        private AudioSource _source;
        private ITtsEngine _engine;
        private bool _engineTried;
        private Thread _worker;
        private readonly AutoResetEvent _wake = new AutoResetEvent(false);
        private volatile bool _quit;

        private sealed class Job { public int Serial; public int Line; public string Text; public int Voice; public float Speed; public string WavPath; }
        private readonly ConcurrentQueue<Job> _jobs = new ConcurrentQueue<Job>();
        private readonly ConcurrentQueue<(int serial, int line, float[] samples, int rate)> _results = new ConcurrentQueue<(int, int, float[], int)>();
        private readonly Dictionary<int, AudioClip> _clips = new Dictionary<int, AudioClip>();
        private readonly HashSet<int> _requested = new HashSet<int>();
        private readonly HashSet<int> _failed = new HashSet<int>();     // lines the voice could not render; skipped, never retried
        private int _serial;                // bumps on every Tune/Stop so stale worker results are dropped
        private int _episodeDay = -1;
        private float _gapUntil;             // realtime at which the next line may start
        private float _textOnlyUntil;        // without a voice: when the transcript advances
        private Coroutine _writing;
        private int _pendingStartLine;

        private const float LineGapSeconds = 0.45f;
        private const float EpisodeGapSeconds = 4f;
        private const int LinesAhead = 3;

        // ------------------------------------------------------------------ bootstrap

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (Instance != null) return;
            var go = new GameObject("RadioPlayer");
            DontDestroyOnLoad(go);
            go.AddComponent<RadioPlayer>();
        }

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            _source = gameObject.AddComponent<AudioSource>();
            _source.playOnAwake = false;
            _source.loop = false;
            _source.spatialBlend = 0f;
            KokoroTtsEngine.PrimePaths();
            var audio = AudioManager.Instance;
            if (audio != null) audio.MusicStateChanged += OnMusicStateChanged;
        }

        private void OnDestroy()
        {
            _quit = true;
            _wake.Set();
            var audio = AudioManager.Instance;
            if (audio != null) audio.MusicStateChanged -= OnMusicStateChanged;
            _engine?.Dispose();
            _engine = null;
            if (Instance == this) Instance = null;
        }

        private void OnMusicStateChanged()
        {
            // Music and radio share the one set of speakers: starting a track turns the radio off.
            var audio = AudioManager.Instance;
            if (audio != null && audio.IsMusicPlaying && IsOn) Stop(silent: true);
        }

        // ------------------------------------------------------------------ control

        public void Tune(string stationId, int startLine = 0, bool paused = false)
        {
            if (!RadioRegistry.TryGet(stationId, out RadioStationDefinition def))
            {
                Fail($"No station '{stationId}' is loaded.");
                return;
            }
            Tune(def, startLine, paused);
        }

        public void Tune(RadioStationDefinition def, int startLine = 0, bool paused = false)
        {
            ResetPlayback();
            Station = def;
            RadioSettings.LastStation = def.Id;
            AudioManager.Instance?.MusicPause();
            _pendingStartLine = Mathf.Max(0, startLine);
            BuildEpisode();
            if (paused) State = RadioState.Paused;
            Changed?.Invoke();
        }

        public void Stop(bool silent = false)
        {
            ResetPlayback();
            Station = null;
            Episode = null;
            State = RadioState.Off;
            StatusText = "";
            Changed?.Invoke();
        }

        public void TogglePause()
        {
            if (State == RadioState.Playing)
            {
                _source.Pause();
                State = RadioState.Paused;
                Changed?.Invoke();
            }
            else if (State == RadioState.Paused)
            {
                AudioManager.Instance?.MusicPause();
                if (_source.clip != null && _source.time > 0f) _source.UnPause();
                State = RadioState.Playing;
                Changed?.Invoke();
            }
        }

        /// <summary>Jumps to a line of the current episode (the transcript rows are clickable).</summary>
        public void SeekToLine(int line)
        {
            if (Episode == null) return;
            line = Mathf.Clamp(line, 0, Episode.lines.Count - 1);
            _source.Stop();
            _source.clip = null;
            LineIndex = line - 1;
            _gapUntil = 0f;
            QueueAhead();
            if (State == RadioState.Paused) State = RadioState.Playing;
            Changed?.Invoke();
        }

        /// <summary>Throws today's cached episode away and writes it again (Settings or the station data changed).</summary>
        public void Rewrite()
        {
            if (Station == null) return;
            string dir = EpisodeDir(Station, RadioScriptContext.Gather(), RadioSettings.EffectiveMode);
            try { if (Directory.Exists(dir)) Directory.Delete(dir, true); } catch (Exception e) { Debug.LogWarning("[Radio] could not clear cache: " + e.Message); }
            Tune(Station);
        }

        private void ResetPlayback()
        {
            _serial++;
            if (_writing != null) { StopCoroutine(_writing); _writing = null; }
            while (_jobs.TryDequeue(out _)) { }
            while (_results.TryDequeue(out _)) { }
            foreach (AudioClip c in _clips.Values) if (c != null) Destroy(c);
            _clips.Clear();
            _requested.Clear();
            _failed.Clear();
            _source.Stop();
            _source.clip = null;
            LineIndex = -1;
            LastError = "";
        }

        private void Fail(string message)
        {
            LastError = message;
            StatusText = message;
            State = RadioState.Failed;
            Debug.LogWarning("[Radio] " + message);
            Changed?.Invoke();
        }

        // ------------------------------------------------------------------ episode

        private void BuildEpisode()
        {
            RadioScriptContext ctx = RadioScriptContext.Gather();
            RadioSettings.ScriptMode mode = RadioSettings.EffectiveMode;
            _episodeDay = ctx.DayOfYear;
            Episode = null;

            RadioEpisode cached = LoadCachedEpisode(Station, ctx, mode);
            if (cached != null) { StartEpisode(cached); return; }

            if (mode == RadioSettings.ScriptMode.Claude)
            {
                State = RadioState.Writing;
                StatusText = "Writing today's episode with Claude...";
                Changed?.Invoke();
                int serial = _serial;
                _writing = StartCoroutine(ClaudeScriptWriter.Write(Station, ctx,
                    ep =>
                    {
                        if (serial != _serial) return;
                        _writing = null;
                        SaveEpisode(ep, EpisodeDir(Station, ctx, mode));
                        StartEpisode(ep);
                    },
                    err =>
                    {
                        if (serial != _serial) return;
                        _writing = null;
                        LastError = err;
                        Debug.LogWarning("[Radio] Claude script failed, using the templated writer: " + err);
                        Homesteader.UI.ToastNotificationSystem.ShowWarning("Radio", "Claude could not write today's episode. Using the almanac's own script.");
                        RadioEpisode ep = RadioScriptWriter.Write(Station, ctx);
                        StartEpisode(ep);   // not cached under the Claude key, so the next tune-in tries Claude again
                    }));
                return;
            }

            RadioEpisode templated = RadioScriptWriter.Write(Station, ctx);
            SaveEpisode(templated, EpisodeDir(Station, ctx, mode));
            StartEpisode(templated);
        }

        private void StartEpisode(RadioEpisode ep)
        {
            Episode = ep;
            LineIndex = Mathf.Clamp(_pendingStartLine, 0, Mathf.Max(0, ep.lines.Count)) - 1;
            _pendingStartLine = 0;
            EnsureEngine();
            State = State == RadioState.Paused ? RadioState.Paused : (VoiceAvailable ? RadioState.Synthesizing : RadioState.Playing);
            StatusText = VoiceAvailable ? "Warming up the voice..." : KokoroTtsEngine.LastStatus;
            _gapUntil = 0f;
            _textOnlyUntil = 0f;
            QueueAhead();
            Changed?.Invoke();
        }

        private static string EpisodeDir(RadioStationDefinition station, RadioScriptContext ctx, RadioSettings.ScriptMode mode)
        {
            string units = ctx.Imperial ? "imp" : "met";
            // the voice model is part of the key: clips from another model must not be replayed
            return Path.Combine(Application.persistentDataPath, "Radio", station.Id, $"{ctx.WorldSeed}_{ctx.DayOfYear}_{mode.ToString().ToLowerInvariant()}_{units}_{KokoroTtsEngine.ModelFolderName}");
        }

        private static RadioEpisode LoadCachedEpisode(RadioStationDefinition station, RadioScriptContext ctx, RadioSettings.ScriptMode mode)
        {
            string path = Path.Combine(EpisodeDir(station, ctx, mode), "episode.json");
            if (!File.Exists(path)) return null;
            try
            {
                var ep = JsonUtility.FromJson<RadioEpisode>(File.ReadAllText(path));
                return ep != null && ep.lines != null && ep.lines.Count > 0 ? ep : null;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Radio] cached episode unreadable: " + e.Message);
                return null;
            }
        }

        private static void SaveEpisode(RadioEpisode ep, string dir)
        {
            try
            {
                Directory.CreateDirectory(dir);
                File.WriteAllText(Path.Combine(dir, "episode.json"), JsonUtility.ToJson(ep, true));
            }
            catch (Exception e) { Debug.LogWarning("[Radio] could not cache episode: " + e.Message); }
        }

        private string CurrentEpisodeDir()
        {
            if (Station == null || Episode == null) return null;
            string units = Homesteader.UI.HudState.Active.Units == Homesteader.UI.UnitSystem.Imperial ? "imp" : "met";
            return Path.Combine(Application.persistentDataPath, "Radio", Station.Id, $"{Episode.worldSeed}_{Episode.dayOfYear}_{Episode.source}_{units}_{KokoroTtsEngine.ModelFolderName}");
        }

        // ------------------------------------------------------------------ voice

        private void EnsureEngine()
        {
            if (_engineTried) return;
            _engineTried = true;
            _engine = KokoroTtsEngine.TryCreate();
            if (_engine == null) Dbg.Log("[Radio] no voice: " + KokoroTtsEngine.LastStatus);
            if (_worker == null)
            {
                _worker = new Thread(WorkerLoop) { IsBackground = true, Name = "RadioTts", Priority = System.Threading.ThreadPriority.BelowNormal };
                _worker.Start();
            }
        }

        /// <summary>Queues synthesis for the next few lines after the one playing.</summary>
        private void QueueAhead()
        {
            if (Episode == null || !VoiceAvailable) return;
            string dir = CurrentEpisodeDir();
            for (int i = Mathf.Max(0, LineIndex + 1); i < Episode.lines.Count && i <= LineIndex + LinesAhead; i++)
            {
                if (_clips.ContainsKey(i) || _requested.Contains(i) || _failed.Contains(i)) continue;
                RadioLine l = Episode.lines[i];
                RadioSpeaker s = Station.FindSpeaker(l.speaker);
                _requested.Add(i);
                _jobs.Enqueue(new Job
                {
                    Serial = _serial, Line = i, Text = l.text,
                    Voice = s != null ? s.Voice : 0, Speed = s != null ? s.Speed : 1f,
                    WavPath = dir != null ? Path.Combine(dir, $"line_{i:000}.wav") : null,
                });
            }
            _wake.Set();
        }

        private void WorkerLoop()
        {
            while (!_quit)
            {
                if (!_jobs.TryDequeue(out Job job)) { _wake.WaitOne(250); continue; }
                if (job.Serial != _serial) continue;
                float[] samples = null; int rate = 0;
                try
                {
                    if (job.WavPath != null && File.Exists(job.WavPath)) samples = RadioWav.Read(job.WavPath, out rate);
                    if (samples == null && _engine != null)
                    {
                        samples = _engine.Synthesize(job.Text, job.Voice, job.Speed);
                        rate = _engine.SampleRate;
                        if (samples != null && job.WavPath != null) RadioWav.Write(job.WavPath, samples, rate);
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning("[Radio] synthesis failed for line " + job.Line + ": " + e.Message);
                }
                _results.Enqueue((job.Serial, job.Line, samples, rate));
            }
        }

        // ------------------------------------------------------------------ playback

        private void Update()
        {
            // worker results -> clips (main thread only)
            while (_results.TryDequeue(out var r))
            {
                if (r.serial != _serial) continue;
                if (r.samples == null || r.samples.Length == 0 || r.rate <= 0) { _requested.Remove(r.line); _failed.Add(r.line); continue; }
                var clip = AudioClip.Create($"radio_{r.line}", r.samples.Length, 1, r.rate, false);
                clip.SetData(r.samples, 0);
                _clips[r.line] = clip;
            }

            if (!IsOn || Episode == null) return;

            var audio = AudioManager.Instance;
            if (audio != null) _source.volume = audio.MusicVolume01 * audio.MasterVolume01;

            if (State == RadioState.Paused || State == RadioState.Writing) return;
            if (_source.isPlaying) return;
            if (Time.unscaledTime < _gapUntil) return;

            int next = LineIndex + 1;
            if (next >= Episode.lines.Count)
            {
                // off the end: a short break, then the next episode (new day) or the same one again
                _gapUntil = Time.unscaledTime + EpisodeGapSeconds;
                LineIndex = -1;
                _source.clip = null;
                if (Homesteader.UI.TimeSystem.Instance.DayOfYear != _episodeDay) { ResetPlayback(); BuildEpisode(); }
                else QueueAhead();
                Changed?.Invoke();
                return;
            }

            if (!VoiceAvailable)
            {
                // no voice: let the transcript advance at reading speed
                if (Time.unscaledTime < _textOnlyUntil) return;
                LineIndex = next;
                int words = Episode.lines[next].text.Split(' ').Length;
                _textOnlyUntil = Time.unscaledTime + Mathf.Max(1.5f, words / 2.6f);
                State = RadioState.Playing;
                StatusText = KokoroTtsEngine.LastStatus;
                Changed?.Invoke();
                return;
            }

            if (_clips.TryGetValue(next, out AudioClip c) && c != null)
            {
                LineIndex = next;
                _source.clip = c;
                _source.Play();
                _gapUntil = Time.unscaledTime + c.length + LineGapSeconds;
                State = RadioState.Playing;
                StatusText = "On air";
                QueueAhead();
                Changed?.Invoke();
            }
            else if (_failed.Contains(next))
            {
                // synthesis failed for this line: skip it rather than stall the broadcast
                LineIndex = next;
                QueueAhead();
            }
            else
            {
                if (!_requested.Contains(next)) QueueAhead();
                if (State != RadioState.Synthesizing)
                {
                    State = RadioState.Synthesizing;
                    StatusText = "Buffering...";
                    Changed?.Invoke();
                }
            }
        }

        // ------------------------------------------------------------------ save

        public struct Saved { public string station; public int line; public bool paused; }

        public static Saved Capture()
        {
            var p = Instance;
            if (p == null || !p.IsOn || p.Station == null) return new Saved { station = "", line = 0, paused = false };
            return new Saved { station = p.Station.Id, line = Mathf.Max(0, p.LineIndex), paused = p.State == RadioState.Paused };
        }

        public static void Restore(Saved s)
        {
            var p = Instance;
            if (p == null) return;
            if (string.IsNullOrEmpty(s.station)) { if (p.IsOn) p.Stop(silent: true); return; }
            p.Tune(s.station, s.line, s.paused);
        }
    }

    /// <summary>16-bit mono PCM WAV read/write for the episode cache. Tiny on purpose; no streaming, no extra chunks.</summary>
    internal static class RadioWav
    {
        public static void Write(string path, float[] samples, int rate)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
            using (var w = new BinaryWriter(fs))
            {
                int dataBytes = samples.Length * 2;
                w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + dataBytes);
                w.Write(System.Text.Encoding.ASCII.GetBytes("WAVE"));
                w.Write(System.Text.Encoding.ASCII.GetBytes("fmt ")); w.Write(16); w.Write((short)1); w.Write((short)1);
                w.Write(rate); w.Write(rate * 2); w.Write((short)2); w.Write((short)16);
                w.Write(System.Text.Encoding.ASCII.GetBytes("data")); w.Write(dataBytes);
                for (int i = 0; i < samples.Length; i++)
                    w.Write((short)Mathf.RoundToInt(Mathf.Clamp(samples[i], -1f, 1f) * 32767f));
            }
        }

        public static float[] Read(string path, out int rate)
        {
            rate = 0;
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read))
            using (var r = new BinaryReader(fs))
            {
                if (new string(r.ReadChars(4)) != "RIFF") return null;
                r.ReadInt32();
                if (new string(r.ReadChars(4)) != "WAVE") return null;
                short channels = 1, bits = 16;
                while (fs.Position + 8 <= fs.Length)
                {
                    string id = new string(r.ReadChars(4));
                    int size = r.ReadInt32();
                    if (id == "fmt ")
                    {
                        r.ReadInt16(); channels = r.ReadInt16(); rate = r.ReadInt32(); r.ReadInt32(); r.ReadInt16(); bits = r.ReadInt16();
                        if (size > 16) r.ReadBytes(size - 16);
                    }
                    else if (id == "data")
                    {
                        if (channels != 1 || bits != 16) return null;
                        int n = size / 2;
                        var samples = new float[n];
                        for (int i = 0; i < n; i++) samples[i] = r.ReadInt16() / 32768f;
                        return samples;
                    }
                    else r.ReadBytes(size);
                }
            }
            return null;
        }
    }
}
