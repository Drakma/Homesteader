using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;
using Homesteader.UI;

namespace Homesteader.Audio
{
    /// <summary>
    /// Central audio hub. Bootstraps itself on scene load (same pattern as WailaPanel/StatsOverlay/
    /// GraphicsSettingsPanel) and wires the Settings dialog's Audio sliders (WelcomeMenu.uxml) to real
    /// volume control - those sliders existed nowhere in the actual UI tree before this; HudBindings had
    /// dead fields (_masterVolumeSlider/_musicVolumeSlider) pointing at an unused example file.
    ///
    /// Footsteps/UI SFX are generated in code at startup and stay that way until real SFX clips are
    /// recorded. Music is different: real CC0/CC-BY tracks now live in Resources/Audio/Music (see
    /// CREDITS.md next to them) and are loaded automatically in Awake, on top of whatever is assigned
    /// to <see cref="musicTracks"/> in the inspector - so dropping more .ogg/.wav files in that folder
    /// is all a track addition ever needs. Playback is a real playlist (next/previous/shuffle/repeat)
    /// driven by the in-game phone's "Steadify" app (see UI/Phone/SteadifyApp.cs).
    /// </summary>
    public sealed class AudioManager : MonoBehaviour
    {
        public static AudioManager Instance { get; private set; }

        public enum RepeatMode { Off, All, One }

        [Header("Music (auto-loaded from Resources/Audio/Music subfolders; anything assigned here is added too)")]
        [SerializeField] private AudioClip[] musicTracks;
        private const string MusicResourcesFolder = "Audio/Music";

        // Subfolder-based playlists. Key = subfolder name (e.g. "AcousticFolk"), value = ordered clip list.
        // The root-level clips (old OpenGameArt tracks) go into a "Default" playlist so they're never lost.
        private readonly List<string> _playlistNames = new List<string>();
        private readonly Dictionary<string, List<AudioClip>> _playlists = new Dictionary<string, List<AudioClip>>();
        private int _currentPlaylistIndex;
        private const string DefaultPlaylistName = "Default";
        private const string AllSongsPlaylistName = "AllSongs";   // shown as "All Songs"
        private const string PlaylistPrefKey = "Homesteader.Audio.Playlist";
        private const string TrackPrefKey = "Homesteader.Audio.Track";          // clip name of the track that was playing
        private const string TrackTimePrefKey = "Homesteader.Audio.TrackTime";  // seconds into it
        private float _nextMusicSave;
        private float _lastMusicTime;     // how far into the track it was when last heard playing
        private bool _appPaused;          // the application or window is paused / unfocused

        private List<AudioClip> _playlist => _playlists.TryGetValue(CurrentPlaylistName, out var pl) ? pl : _emptyList;
        private static readonly List<AudioClip> _emptyList = new List<AudioClip>();

        private int _currentTrack = -1;
        private bool _musicPlaying;
        private RepeatMode _repeatMode = RepeatMode.All;
        private bool _shuffle;
        private readonly List<int> _shuffleHistory = new List<int>();
        private System.Random _rng = new System.Random();

        /// <summary>Fired whenever the current track, play/pause state, shuffle or repeat mode changes -
        /// the Steadify phone app subscribes to this to keep its UI in sync without polling every frame.</summary>
        public event Action MusicStateChanged;

        /// <summary>Fired when the playlist itself changes (user picks a different playlist in Steadify).</summary>
        public event Action PlaylistChanged;

        [Header("Footsteps (assign per-surface clips later; falls back to a procedural tick)")]
        [SerializeField] private AudioClip[] footstepGrass;
        [SerializeField] private AudioClip[] footstepDirt;
        [SerializeField] private AudioClip[] footstepGravel;
        [SerializeField] private AudioClip[] footstepSnow;
        [SerializeField] private AudioClip[] footstepWood;

        [Header("UI (assign real clicks later; falls back to a procedural beep)")]
        [SerializeField] private AudioClip uiClickClip;
        [SerializeField] private AudioClip uiConfirmClip;
        [SerializeField] private AudioClip uiErrorClip;

        public enum FootstepSurface { Grass, Dirt, Gravel, Snow, Wood }
        public enum UiSound { Click, Confirm, Error }

        private const string MasterPrefKey = "Homesteader.Audio.Master";
        private const string MusicPrefKey = "Homesteader.Audio.Music";
        private const string SfxPrefKey = "Homesteader.Audio.Sfx";
        private const float DefaultMaster = 0.8f, DefaultMusic = 0.65f, DefaultSfx = 0.8f;

        private float masterVolume = DefaultMaster;
        private float musicVolume = DefaultMusic;
        private float sfxVolume = DefaultSfx;

        private AudioSource musicSource;
        private AudioSource windSource;
        private AudioSource rainSource;
        private AudioSource sfxSource2D;       // UI and anything without a world position
        private const int SfxVoicePoolSize = 8;
        private AudioSource[] sfxVoicePool;    // 3D one-shots (footsteps, tools, etc.) - simple round-robin
        private int nextSfxVoice;

        private Slider masterSlider, musicSlider, sfxSlider;
        private bool slidersWired;
        private bool applyingFromCode;

        // Procedurally generated, reused across the whole session - built once in Awake.
        private AudioClip windLoopClip;
        private AudioClip rainLoopClip;

        private float windTarget, rainTarget;
        private const float WeatherLerpSpeed = 0.5f; // volume units/sec

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<AudioManager>() != null) return;
            var go = new GameObject("AudioManager");
            DontDestroyOnLoad(go);
            go.AddComponent<AudioManager>();
        }

        private void Awake()
        {
            Instance = this;

            // musicSource is NOT looping - looping is handled per-track by Update()/AdvanceTrack() so a
            // finished track can honor shuffle/repeat and fire MusicStateChanged for the Steadify app.
            musicSource = CreateSource("MusicSource", loop: false, spatialBlend: 0f);
            windSource = CreateSource("WindSource", loop: true, spatialBlend: 0f);
            rainSource = CreateSource("RainSource", loop: true, spatialBlend: 0f);
            sfxSource2D = CreateSource("Sfx2DSource", loop: false, spatialBlend: 0f);

            sfxVoicePool = new AudioSource[SfxVoicePoolSize];
            for (int i = 0; i < SfxVoicePoolSize; i++)
                sfxVoicePool[i] = CreateSource("SfxVoice" + i, loop: false, spatialBlend: 1f);

            windLoopClip = ProceduralAudio.GenerateFilteredNoiseLoop(6f, cutoff: 0.05f, seed: 1001, gustLfo: true);
            rainLoopClip = ProceduralAudio.GenerateFilteredNoiseLoop(6f, cutoff: 0.35f, seed: 2002, gustLfo: false);
            windSource.clip = windLoopClip;
            rainSource.clip = rainLoopClip;
            windSource.volume = 0f;
            rainSource.volume = 0f;
            windSource.Play();
            rainSource.Play();

            BuildPlaylist();
            LoadVolumePrefs();
            ApplyVolumes();

            if (_playlist.Count > 0)
            {
                // Carry on where the last session stopped: same playlist (restored in BuildPlaylist), same track, same moment.
                _currentTrack = 0;
                float resumeAt = 0f;
                string savedTrack = PlayerPrefs.GetString(TrackPrefKey, "");
                if (!string.IsNullOrEmpty(savedTrack))
                {
                    for (int i = 0; i < _playlist.Count; i++)
                        if (_playlist[i] != null && _playlist[i].name == savedTrack)
                        {
                            _currentTrack = i;
                            resumeAt = PlayerPrefs.GetFloat(TrackTimePrefKey, 0f);
                            break;
                        }
                }
                // The track is made ready but NOT started: the music begins when the game has loaded and the saved state is known (StartMusicAfterLoad).
                musicSource.clip = _playlist[_currentTrack];
                _resumeAt = resumeAt > 1f && resumeAt < musicSource.clip.length - 3f ? resumeAt : 0f;
                _lastMusicTime = _resumeAt;
                _musicPlaying = false;
            }
        }

        private float _resumeAt;

        /// <summary>Called once the game is loaded (GameSaveManager): starts the prepared track where the last session stopped, or leaves it paused.</summary>
        public void StartMusicAfterLoad(bool play)
        {
            if (!play || _musicPlaying || _currentTrack < 0 || musicSource == null || musicSource.clip == null) return;
            musicSource.time = _resumeAt;
            musicSource.Play();
            _lastMusicTime = musicSource.time;
            _musicPlaying = true;
            MusicStateChanged?.Invoke();
        }

        /// <summary>Scans Resources/Audio/Music for subfolders and builds a separate playlist per subfolder.
        /// Root-level clips (old OpenGameArt tracks) go into a "Default" playlist. Inspector-assigned
        /// musicTracks are appended to the Default playlist. Each subfolder becomes its own playlist
        /// named after the folder (e.g. "AcousticFolk", "AmbientChill", "LoFiBeats").
        /// Subfolder names are read from Resources/Audio/Music/playlists.txt so it works in builds too.</summary>
        private void BuildPlaylist()
        {
            _playlists.Clear();
            _playlistNames.Clear();

            // Read subfolder names from playlists.txt (works at runtime and in editor).
            var subfolders = new List<string>();
            var txtAsset = Resources.Load<TextAsset>("Audio/Music/playlists");
            if (txtAsset != null)
            {
                foreach (var line in txtAsset.text.Split('\n', '\r'))
                {
                    string trimmed = line.Trim();
                    if (trimmed.Length > 0) subfolders.Add(trimmed);
                }
            }
#if UNITY_EDITOR
            // In the editor, also discover subfolders dynamically so new folders are picked up automatically.
            foreach (var guid in UnityEditor.AssetDatabase.FindAssets("t:AudioClip", new[] { "Assets/Resources/Audio/Music" }))
            {
                string path = UnityEditor.AssetDatabase.GUIDToAssetPath(guid);
                const string prefix = "Assets/Resources/Audio/Music/";
                if (path.StartsWith(prefix, System.StringComparison.OrdinalIgnoreCase))
                {
                    string relative = path.Substring(prefix.Length);
                    int slash = relative.IndexOf('/');
                    if (slash >= 0)
                    {
                        string folder = relative.Substring(0, slash);
                        if (!subfolders.Contains(folder)) subfolders.Add(folder);
                    }
                }
            }
#endif

            // Load each subfolder's clips into its own playlist.
            foreach (var folder in subfolders)
            {
                AudioClip[] clips = Resources.LoadAll<AudioClip>("Audio/Music/" + folder);
                // A folder listed in playlists.txt is a playlist even while it has no tracks yet (e.g. ClassicRock).
                var list = new List<AudioClip>();
                if (clips != null) foreach (var c in clips) if (c != null && !list.Contains(c)) list.Add(c);
                list.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
                _playlists[folder] = list;
                _playlistNames.Add(folder);
            }

            // Load root-level clips (directly in Audio/Music, not in a subfolder) into the Default playlist.
            // Resources.LoadAll is recursive, so we load everything and subtract the subfolder clips.
            AudioClip[] allClips = Resources.LoadAll<AudioClip>(MusicResourcesFolder);
            if (allClips != null && allClips.Length > 0)
            {
                var subfolderClips = new HashSet<AudioClip>();
                foreach (var kvp in _playlists)
                    foreach (var c in kvp.Value) subfolderClips.Add(c);

                var defaultList = new List<AudioClip>();
                foreach (var clip in allClips)
                {
                    if (clip == null || subfolderClips.Contains(clip)) continue;
                    if (!defaultList.Contains(clip)) defaultList.Add(clip);
                }

                // Append inspector-assigned tracks to the Default playlist.
                if (musicTracks != null)
                    foreach (var clip in musicTracks)
                        if (clip != null && !defaultList.Contains(clip)) defaultList.Add(clip);

                if (defaultList.Count > 0)
                {
                    defaultList.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
                    _playlists[DefaultPlaylistName] = defaultList;
                    _playlistNames.Add(DefaultPlaylistName);
                }
            }
            else if (musicTracks != null && musicTracks.Length > 0)
            {
                var defaultList = new List<AudioClip>();
                foreach (var clip in musicTracks)
                    if (clip != null && !defaultList.Contains(clip)) defaultList.Add(clip);
                if (defaultList.Count > 0)
                {
                    _playlists[DefaultPlaylistName] = defaultList;
                    _playlistNames.Add(DefaultPlaylistName);
                }
            }

            // Sort playlist names alphabetically, but keep Default first if it exists.
            _playlistNames.Sort((a, b) =>
            {
                if (a == DefaultPlaylistName) return -1;
                if (b == DefaultPlaylistName) return 1;
                return string.CompareOrdinal(a, b);
            });

            // "All Songs": every track from every playlist, once each. Shuffle All plays this one.
            var all = new List<AudioClip>();
            foreach (string n in _playlistNames)
                foreach (AudioClip c in _playlists[n]) if (!all.Contains(c)) all.Add(c);
            if (all.Count > 0)
            {
                _playlists[AllSongsPlaylistName] = all;
                _playlistNames.Add(AllSongsPlaylistName);
            }

            // Restore last-used playlist from prefs, or fall back to the first available.
            string saved = PlayerPrefs.GetString(PlaylistPrefKey, "");
            int savedIdx = _playlistNames.IndexOf(saved);
            _currentPlaylistIndex = savedIdx >= 0 ? savedIdx : 0;
        }

        private AudioSource CreateSource(string name, bool loop, float spatialBlend)
        {
            var child = new GameObject(name);
            child.transform.SetParent(transform, false);
            var src = child.AddComponent<AudioSource>();
            src.loop = loop;
            src.playOnAwake = false;
            src.spatialBlend = spatialBlend;
            if (spatialBlend > 0f)
            {
                src.rolloffMode = AudioRolloffMode.Linear;
                src.minDistance = 2f;
                src.maxDistance = 25f;
            }
            return src;
        }

        private float _nextSliderResolve;

        private void Update()
        {
            // The Settings sliders belong to a UI document that is rebuilt when a game is loaded (the scene reloads; this
            // manager survives it). Once the sliders we wired are gone from their panel, wire the new ones.
            if (slidersWired && (masterSlider == null || masterSlider.panel == null
                                 || musicSlider == null || musicSlider.panel == null
                                 || sfxSlider == null || sfxSlider.panel == null))
                slidersWired = false;
            // the scene scan in ResolveSliders is expensive: retry about once a second, not every frame
            if (!slidersWired && Time.unscaledTime >= _nextSliderResolve) { _nextSliderResolve = Time.unscaledTime + 1f; ResolveSliders(); }

            // Weather-driven ambience: read the same weather enum WeatherEffectsManager drives its particles
            // from, rather than adding new coupling to that class - independent, simple mapping.
            var ts = TimeSystem.Instance;
            if (ts != null)
            {
                switch (ts.Weather)
                {
                    case HomesteaderWeather.Rain: windTarget = 0.12f; rainTarget = 0.6f; break;
                    case HomesteaderWeather.Thunderstorm: windTarget = 0.45f; rainTarget = 1f; break;
                    case HomesteaderWeather.Snow: windTarget = 0.10f; rainTarget = 0f; break;
                    case HomesteaderWeather.Blizzard: windTarget = 0.8f; rainTarget = 0f; break;
                    case HomesteaderWeather.Wind: windTarget = 0.5f; rainTarget = 0f; break;
                    case HomesteaderWeather.Fog: windTarget = 0.06f; rainTarget = 0f; break;
                    default: windTarget = 0f; rainTarget = 0f; break;
                }
            }

            float dt = Time.unscaledDeltaTime;
            windSource.volume = Mathf.MoveTowards(windSource.volume, windTarget * sfxVolume * masterVolume, WeatherLerpSpeed * dt);
            rainSource.volume = Mathf.MoveTowards(rainSource.volume, rainTarget * sfxVolume * masterVolume, WeatherLerpSpeed * dt);

            // Remember the track and position (a few times a minute, and on quit) so the next session continues from here.
            if (_musicPlaying && Time.unscaledTime >= _nextMusicSave)
            {
                _nextMusicSave = Time.unscaledTime + 10f;
                SaveMusicPosition();
            }

            // A track finished on its own (not via Skip/Previous) - advance the playlist per repeat mode.
            // "Not playing" is NOT "finished": the source also reports not playing while the window has lost focus, the application is paused,
            // or the clip is still starting. Treating that as the end of the song started a new one every time the player went out of the game
            // and back in. A track has finished only when it ran to the end of its clip.
            if (musicSource.isPlaying) _lastMusicTime = musicSource.time;
            if (_musicPlaying && _currentTrack >= 0 && musicSource.clip != null && !musicSource.isPlaying)
            {
                bool ranOut = musicSource.clip.length - _lastMusicTime < 1.0f;
                if (ranOut)
                {
                    _lastMusicTime = 0f;
                    if (_repeatMode == RepeatMode.One) PlayTrack(_currentTrack);
                    else AdvanceTrack(+1, userInitiated: false);
                }
                else if (!_appPaused)
                {
                    // it should be playing: carry on from where it was (a pause by the engine is lifted; a stopped source is started again there)
                    musicSource.UnPause();
                    if (!musicSource.isPlaying)
                    {
                        float at = _lastMusicTime;
                        musicSource.Play();
                        musicSource.time = Mathf.Clamp(at, 0f, Mathf.Max(0f, musicSource.clip.length - 0.1f));
                    }
                }
            }
        }

        // ── Settings dialog wiring ──────────────────────────────────────────
        private void ResolveSliders()
        {
            // The sliders live in one of the scene's UI documents (the welcome/settings tree); look through all of them,
            // since the first document found is not necessarily the one that holds them.
            Slider master = null, music = null, sfx = null;
            foreach (var doc in FindObjectsByType<UIDocument>())
            {
                var root = doc.rootVisualElement;
                if (root == null) continue;
                master = root.Q<Slider>("AudioMasterSlider");
                music = root.Q<Slider>("AudioMusicSlider");
                sfx = root.Q<Slider>("AudioSfxSlider");
                if (master != null && music != null && sfx != null) break;
            }
            if (master == null || music == null || sfx == null || master.panel == null) return;

            masterSlider = master;
            musicSlider = music;
            sfxSlider = sfx;

            applyingFromCode = true;
            masterSlider.SetValueWithoutNotify(masterVolume * 100f);
            musicSlider.SetValueWithoutNotify(musicVolume * 100f);
            sfxSlider.SetValueWithoutNotify(sfxVolume * 100f);
            applyingFromCode = false;

            masterSlider.RegisterValueChangedCallback(evt => OnSliderChanged(MasterPrefKey, evt.newValue, v => masterVolume = v));
            musicSlider.RegisterValueChangedCallback(evt => OnSliderChanged(MusicPrefKey, evt.newValue, v => musicVolume = v));
            sfxSlider.RegisterValueChangedCallback(evt => OnSliderChanged(SfxPrefKey, evt.newValue, v => sfxVolume = v));

            slidersWired = true;
        }

        private void OnSliderChanged(string prefKey, float sliderValue0to100, System.Action<float> apply)
        {
            if (applyingFromCode) return;
            float v = Mathf.Clamp01(sliderValue0to100 / 100f);
            apply(v);
            PlayerPrefs.SetFloat(prefKey, v);
            PlayerPrefs.Save();
            ApplyVolumes();
        }

        private void LoadVolumePrefs()
        {
            masterVolume = PlayerPrefs.GetFloat(MasterPrefKey, DefaultMaster);
            musicVolume = PlayerPrefs.GetFloat(MusicPrefKey, DefaultMusic);
            sfxVolume = PlayerPrefs.GetFloat(SfxPrefKey, DefaultSfx);
        }

        /// <summary>Puts the three volume sliders back to their shipped defaults (used by Settings > Reset All).</summary>
        public void ResetVolumes()
        {
            masterVolume = DefaultMaster;
            musicVolume = DefaultMusic;
            sfxVolume = DefaultSfx;
            PlayerPrefs.SetFloat(MasterPrefKey, masterVolume);
            PlayerPrefs.SetFloat(MusicPrefKey, musicVolume);
            PlayerPrefs.SetFloat(SfxPrefKey, sfxVolume);
            PlayerPrefs.Save();

            applyingFromCode = true;
            masterSlider?.SetValueWithoutNotify(masterVolume * 100f);
            musicSlider?.SetValueWithoutNotify(musicVolume * 100f);
            sfxSlider?.SetValueWithoutNotify(sfxVolume * 100f);
            applyingFromCode = false;
            ApplyVolumes();
        }

        private void ApplyVolumes()
        {
            musicSource.volume = musicVolume * masterVolume;
            // wind/rain volumes are driven continuously in Update() against their weather targets
        }

        // ── Steadify (in-game phone music app) control API ─────────────────

        /// <summary>Read-only list of available playlist names (e.g. "Default", "AcousticFolk", "AmbientChill", "LoFiBeats").</summary>
        public IReadOnlyList<string> PlaylistNames => _playlistNames;
        /// <summary>Index of the currently active playlist.</summary>
        public int CurrentPlaylistIndex => _currentPlaylistIndex;
        /// <summary>Name of the currently active playlist.</summary>
        public string CurrentPlaylistName =>
            _currentPlaylistIndex >= 0 && _currentPlaylistIndex < _playlistNames.Count
                ? _playlistNames[_currentPlaylistIndex] : DefaultPlaylistName;

        /// <summary>Switches to a different playlist by index. Stops the current track and starts
        /// playing track 0 of the new playlist. Persists the choice to PlayerPrefs.</summary>
        public void MusicSetPlaylist(int index)
        {
            if (index < 0 || index >= _playlistNames.Count) return;
            if (index == _currentPlaylistIndex) return;
            _currentPlaylistIndex = index;
            PlayerPrefs.SetString(PlaylistPrefKey, _playlistNames[index]);
            PlayerPrefs.Save();
            _currentTrack = _playlist.Count > 0 ? 0 : -1;
            _shuffleHistory.Clear();
            if (_currentTrack >= 0)
            {
                musicSource.clip = _playlist[_currentTrack];
                musicSource.Play();
                _musicPlaying = true;
            }
            else
            {
                musicSource.Stop();
                _musicPlaying = false;
            }
            PlaylistChanged?.Invoke();
            MusicStateChanged?.Invoke();
        }

        /// <summary>Read-only track list for the Steadify app to render (title = file name, spaces restored).</summary>
        public IReadOnlyList<AudioClip> MusicPlaylist => _playlist;
        public int CurrentTrackIndex => _currentTrack;
        public bool IsMusicPlaying => _musicPlaying && _currentTrack >= 0;
        public bool ShuffleEnabled => _shuffle;
        public RepeatMode CurrentRepeatMode => _repeatMode;
        public float MusicVolume01 => musicVolume;
        /// <summary>The master slider (0..1); the radio multiplies its own volume by this and the music level.</summary>
        public float MasterVolume01 => masterVolume;
        public float TrackPosition01 => (musicSource.clip != null && musicSource.clip.length > 0f)
            ? Mathf.Clamp01(musicSource.time / musicSource.clip.length) : 0f;
        public float TrackTimeSeconds => musicSource.clip != null ? musicSource.time : 0f;
        public float TrackLengthSeconds => musicSource.clip != null ? musicSource.clip.length : 0f;
        public string CurrentTrackName => (_currentTrack >= 0 && _currentTrack < _playlist.Count)
            ? PrettyTrackName(_playlist[_currentTrack]) : "No Track";

        /// <summary>Drops the "Music_" prefix and any leading numbers, dashes, dots, spaces and underscores ("01_Neon_Hearts" -> "Neon_Hearts", "03 - Song" -> "Song").</summary>
        public static string StripTrackPrefix(string name)
        {
            string n = name ?? "";
            if (n.StartsWith("Music_")) n = n.Substring(6);
            int i = 0;
            while (i < n.Length && (char.IsDigit(n[i]) || n[i] == '-' || n[i] == '.' || n[i] == '_' || n[i] == ' ')) i++;
            return i < n.Length ? n.Substring(i) : n;   // a name that is all digits stays as it is
        }

        private static string PrettyTrackName(AudioClip clip)
        {
            string n = StripTrackPrefix(clip.name);
            // Insert spaces before capitals in a PascalCase name (AppleCider -> Apple Cider), leave others alone.
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < n.Length; i++)
            {
                if (i > 0 && char.IsUpper(n[i]) && !char.IsUpper(n[i - 1])) sb.Append(' ');
                sb.Append(n[i] == '_' ? ' ' : n[i]);
            }
            return sb.ToString().Trim();
        }

        /// <summary>Converts a raw playlist folder name (e.g. "AcousticFolk") into a display name (e.g. "Acoustic Folk").</summary>
        public static string PrettyPlaylistName(string raw)
        {
            if (raw == DefaultPlaylistName) return "Default";
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < raw.Length; i++)
            {
                if (i > 0 && char.IsUpper(raw[i]) && !char.IsUpper(raw[i - 1])) sb.Append(' ');
                sb.Append(raw[i]);
            }
            return sb.ToString().Trim();
        }

        /// <summary>Starts (or resumes) playback. If nothing has ever played, starts at track 0.</summary>
        public void MusicPlay()
        {
            if (_playlist.Count == 0) return;
            if (_currentTrack < 0) _currentTrack = 0;
            if (musicSource.clip != _playlist[_currentTrack]) musicSource.clip = _playlist[_currentTrack];
            musicSource.Play();
            _musicPlaying = true;
            MusicStateChanged?.Invoke();
        }

        public void MusicPause()
        {
            musicSource.Pause();
            _musicPlaying = false;
            MusicStateChanged?.Invoke();
        }

        public void MusicTogglePlayPause()
        {
            if (_musicPlaying) MusicPause(); else MusicPlay();
        }

        public void MusicNext() => AdvanceTrack(+1, userInitiated: true);

        public void MusicPrevious()
        {
            // If we're more than 3s into the track, "previous" restarts it (standard player behavior);
            // otherwise it actually goes back a track.
            if (musicSource.time > 3f) { PlayTrack(_currentTrack); return; }
            AdvanceTrack(-1, userInitiated: true);
        }

        /// <summary>Jumps straight to a specific playlist entry (used by the Steadify track list).</summary>
        public void MusicPlayTrackAt(int index)
        {
            if (index < 0 || index >= _playlist.Count) return;
            PlayTrack(index);
        }

        /// <summary>Shuffle All: switches to the All Songs playlist (every track in every playlist), turns shuffle on and starts a random track.</summary>
        public void MusicShuffleAll()
        {
            int idx = _playlistNames.IndexOf(AllSongsPlaylistName);
            if (idx < 0) return;
            if (idx != _currentPlaylistIndex)
            {
                _currentPlaylistIndex = idx;
                PlayerPrefs.SetString(PlaylistPrefKey, AllSongsPlaylistName);
                PlayerPrefs.Save();
                PlaylistChanged?.Invoke();
            }
            _shuffle = true;
            _shuffleHistory.Clear();
            if (_playlist.Count > 0) PlayTrack(_rng.Next(_playlist.Count));
            MusicStateChanged?.Invoke();
        }

        public void MusicSetShuffle(bool enabled)
        {
            _shuffle = enabled;
            _shuffleHistory.Clear();
            MusicStateChanged?.Invoke();
        }

        public void MusicCycleRepeatMode()
        {
            _repeatMode = _repeatMode switch
            {
                RepeatMode.Off => RepeatMode.All,
                RepeatMode.All => RepeatMode.One,
                _ => RepeatMode.Off,
            };
            MusicStateChanged?.Invoke();
        }

        /// <summary>Scrubs within the current track (0..1 across its length) - used by Steadify's seek bar.</summary>
        public void MusicSeek01(float t)
        {
            if (musicSource.clip == null) return;
            musicSource.time = Mathf.Clamp01(t) * musicSource.clip.length;
            MusicStateChanged?.Invoke();
        }

        /// <summary>Sets music volume directly (0..1), keeping it in sync with the Settings slider + PlayerPrefs.</summary>
        public void MusicSetVolume01(float v)
        {
            musicVolume = Mathf.Clamp01(v);
            PlayerPrefs.SetFloat(MusicPrefKey, musicVolume);
            PlayerPrefs.Save();
            applyingFromCode = true;
            musicSlider?.SetValueWithoutNotify(musicVolume * 100f);
            applyingFromCode = false;
            ApplyVolumes();
            MusicStateChanged?.Invoke();
        }

        private void SaveMusicPosition()
        {
            if (musicSource == null || musicSource.clip == null) return;
            PlayerPrefs.SetString(TrackPrefKey, musicSource.clip.name);
            PlayerPrefs.SetFloat(TrackTimePrefKey, musicSource.time);
            PlayerPrefs.Save();
        }

        private void OnApplicationQuit() => SaveMusicPosition();
        private void OnApplicationPause(bool paused) { _appPaused = paused; if (paused) SaveMusicPosition(); }
        private void OnApplicationFocus(bool focus) { _appPaused = !focus; }

        private void PlayTrack(int index)
        {
            if (index < 0 || index >= _playlist.Count) return;
            _currentTrack = index;
            musicSource.clip = _playlist[index];
            musicSource.Play();
            _lastMusicTime = 0f;
            _musicPlaying = true;
            SaveMusicPosition();
            MusicStateChanged?.Invoke();
        }

        private void AdvanceTrack(int direction, bool userInitiated)
        {
            if (_playlist.Count == 0) { _musicPlaying = false; return; }

            if (_playlist.Count == 1)
            {
                // Only one track: repeat it unless the user explicitly turned repeat off.
                if (_repeatMode == RepeatMode.Off && userInitiated == false) { _musicPlaying = false; MusicStateChanged?.Invoke(); return; }
                PlayTrack(0);
                return;
            }

            int next;
            if (_shuffle)
            {
                do { next = _rng.Next(_playlist.Count); } while (next == _currentTrack);
            }
            else
            {
                next = _currentTrack + direction;
                if (next >= _playlist.Count)
                {
                    if (_repeatMode == RepeatMode.Off) { _musicPlaying = false; MusicStateChanged?.Invoke(); return; }
                    next = 0;
                }
                else if (next < 0)
                {
                    next = _playlist.Count - 1;
                }
            }
            PlayTrack(next);
        }

        // ── Public playback API ─────────────────────────────────────────────

        /// <summary>Plays a UI sound. Uses the assigned clip if set, otherwise a procedural beep so menus
        /// have feedback today without waiting on real audio files.</summary>
        public void PlayUi(UiSound sound)
        {
            AudioClip clip = sound switch
            {
                UiSound.Confirm => uiConfirmClip,
                UiSound.Error => uiErrorClip,
                _ => uiClickClip,
            };
            if (clip == null)
            {
                float freq = sound switch { UiSound.Confirm => 880f, UiSound.Error => 220f, _ => 660f };
                clip = ProceduralAudio.GenerateBeep(freq, sound == UiSound.Error ? 0.16f : 0.07f);
            }
            sfxSource2D.PlayOneShot(clip, sfxVolume * masterVolume);
        }

        /// <summary>Plays a footstep at a world position for the given surface. Uses an assigned clip array
        /// if present (random pick + slight pitch variation), otherwise a procedural tick.</summary>
        public void PlayFootstep(Vector3 worldPos, FootstepSurface surface)
        {
            AudioClip[] clips = surface switch
            {
                FootstepSurface.Dirt => footstepDirt,
                FootstepSurface.Gravel => footstepGravel,
                FootstepSurface.Snow => footstepSnow,
                FootstepSurface.Wood => footstepWood,
                _ => footstepGrass,
            };

            AudioClip clip = (clips != null && clips.Length > 0) ? clips[UnityEngine.Random.Range(0, clips.Length)] : null;
            bool procedural = clip == null;
            // The synthetic tick sounds like a wood chop; stay silent until real footstep clips are assigned.
            if (procedural) return;

            var src = NextSfxVoice();
            src.transform.position = worldPos;
            src.pitch = UnityEngine.Random.Range(0.92f, 1.08f);
            src.volume = sfxVolume * masterVolume * (procedural ? 0.5f : 0.8f);
            src.clip = clip;
            src.Play();
        }

        /// <summary>General-purpose 3D one-shot (tool swings, placement thuds, animal calls, etc.) once real
        /// clips exist - no procedural fallback here since there's no generic "guess the sound" option.</summary>
        public void PlaySfxAt(AudioClip clip, Vector3 worldPos, float volumeScale = 1f)
        {
            if (clip == null) return;
            var src = NextSfxVoice();
            src.transform.position = worldPos;
            src.pitch = 1f;
            src.volume = sfxVolume * masterVolume * volumeScale;
            src.clip = clip;
            src.Play();
        }

        /// <summary>Non-positional one-shot for sounds the player causes: independent of where the listener is.</summary>
        public void PlaySfx2D(AudioClip clip, float volumeScale = 1f)
        {
            if (clip == null || sfxSource2D == null) return;
            sfxSource2D.PlayOneShot(clip, sfxVolume * masterVolume * volumeScale);
        }

        private AudioSource NextSfxVoice()
        {
            var src = sfxVoicePool[nextSfxVoice];
            nextSfxVoice = (nextSfxVoice + 1) % sfxVoicePool.Length;
            return src;
        }
    }
}
