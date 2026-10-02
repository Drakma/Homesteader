// SteadifyApp.cs - "Steadify" phone app: a Spotify-style music player controlling AudioManager's
// music playlist (real CC0/CC-BY tracks loaded from Resources/Audio/Music).
// Wired into PhoneController (tile, view, back button) the same way GigsApp is.

using System.Collections.Generic;
using Homesteader.Audio;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class SteadifyApp
    {
        private readonly VisualElement _albumArt;
        private readonly Label _albumArtGlyph;
        private readonly Label _trackTitle;
        private readonly Label _trackMeta;
        private readonly Label _timeElapsed;
        private readonly Label _timeTotal;
        private readonly Slider _seekSlider;
        private readonly Slider _volumeSlider;
        private readonly Label _volumeValue;
        private readonly Button _shuffleBtn;
        private readonly Button _prevBtn;
        private readonly Button _playPauseBtn;
        private readonly Button _nextBtn;
        private readonly Button _repeatBtn;
        private readonly VisualElement _playlistContainer;
        private readonly DropdownField _playlistSelector;

        private bool _draggingSeek;

        private void EndSeekDrag()
        {
            if (!_draggingSeek) return;
            _draggingSeek = false;
            AudioManager.Instance?.MusicSeek01(_seekSlider.value);
        }
        private bool _suppressEvents;

        public SteadifyApp(VisualElement root)
        {
            _albumArt = root.Q<VisualElement>("SteadifyAlbumArt");
            _albumArtGlyph = _albumArt?.Q<Label>(className: "steadify-album-art-glyph");
            _trackTitle = root.Q<Label>("SteadifyTrackTitle");
            _trackMeta = root.Q<Label>("SteadifyTrackMeta");
            _timeElapsed = root.Q<Label>("SteadifyTimeElapsed");
            _timeTotal = root.Q<Label>("SteadifyTimeTotal");
            _seekSlider = root.Q<Slider>("SteadifySeekSlider");
            _volumeSlider = root.Q<Slider>("SteadifyVolumeSlider");
            _volumeValue = root.Q<Label>("SteadifyVolumeValue");
            _shuffleBtn = root.Q<Button>("SteadifyShuffleBtn");
            _prevBtn = root.Q<Button>("SteadifyPrevBtn");
            _playPauseBtn = root.Q<Button>("SteadifyPlayPauseBtn");
            _nextBtn = root.Q<Button>("SteadifyNextBtn");
            _repeatBtn = root.Q<Button>("SteadifyRepeatBtn");
            _playlistContainer = root.Q<VisualElement>("SteadifyPlaylistContainer");
            _playlistSelector = root.Q<DropdownField>("SteadifyPlaylistSelector");
            PopupStyles.Ensure(root);   // the dropdown list is built outside the document and needs its own style sheet

            var audio = AudioManager.Instance;
            if (audio != null)
            {
                audio.MusicStateChanged += Refresh;
                audio.PlaylistChanged += OnPlaylistChanged;
            }

            // Populate the playlist dropdown with available playlists.
            if (_playlistSelector != null && audio != null)
            {
                var names = audio.PlaylistNames;
                var choices = new List<string>();
                foreach (var n in names)
                    choices.Add(AudioManager.PrettyPlaylistName(n));
                _playlistSelector.choices = choices;
                if (audio.CurrentPlaylistIndex >= 0 && audio.CurrentPlaylistIndex < choices.Count)
                    _playlistSelector.SetValueWithoutNotify(choices[audio.CurrentPlaylistIndex]);

                _playlistSelector.RegisterValueChangedCallback(evt =>
                {
                    if (_suppressEvents) return;
                    var a = AudioManager.Instance;
                    if (a == null) return;
                    string rawName = FindRawName(a, evt.newValue);
                    for (int i = 0; i < a.PlaylistNames.Count; i++)
                    {
                        if (a.PlaylistNames[i] == rawName) { a.MusicSetPlaylist(i); break; }
                    }
                });
            }

            _prevBtn?.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicPrevious());
            _nextBtn?.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicNext());
            _playPauseBtn?.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicTogglePlayPause());
            _shuffleBtn?.RegisterCallback<ClickEvent>(evt =>
            {
                var a = AudioManager.Instance;
                if (a != null) a.MusicSetShuffle(!a.ShuffleEnabled);
            });
            _repeatBtn?.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicCycleRepeatMode());
            root.Q<Button>("SteadifyPopoutBtn")?.RegisterCallback<ClickEvent>(evt => SteadifyMiniPlayer.Toggle(root));
            root.Q<Button>("SteadifyShuffleAllBtn")?.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicShuffleAll());

            if (_seekSlider != null)
            {
                // Trickle-down: the slider's own drag handling consumes the pointer events before they bubble up, which left
                // _draggingSeek false and let the per-frame tick snap the handle back to the playback position mid-drag.
                _seekSlider.RegisterCallback<PointerDownEvent>(evt => _draggingSeek = true, TrickleDown.TrickleDown);
                _seekSlider.RegisterCallback<PointerUpEvent>(evt => EndSeekDrag(), TrickleDown.TrickleDown);
                _seekSlider.RegisterCallback<PointerCaptureOutEvent>(evt => EndSeekDrag(), TrickleDown.TrickleDown);
                _seekSlider.RegisterValueChangedCallback(evt =>
                {
                    if (_suppressEvents) return;
                    // Programmatic updates use SetValueWithoutNotify, so a change event is the player moving the handle
                    // (dragging or clicking the bar): move the music with it, and show the new time.
                    float total = AudioManager.Instance?.TrackLengthSeconds ?? 0f;
                    if (_timeElapsed != null) _timeElapsed.text = FormatTime(evt.newValue * total);
                    AudioManager.Instance?.MusicSeek01(evt.newValue);
                });
            }

            _volumeSlider?.RegisterValueChangedCallback(evt =>
            {
                if (_suppressEvents) return;
                AudioManager.Instance?.MusicSetVolume01(evt.newValue / 100f);
                if (_volumeValue != null) _volumeValue.text = Mathf.RoundToInt(evt.newValue) + "%";
            });
        }

        private void OnPlaylistChanged()
        {
            var audio = AudioManager.Instance;
            if (audio == null || _playlistSelector == null) return;

            _suppressEvents = true;
            var choices = _playlistSelector.choices;
            if (audio.CurrentPlaylistIndex >= 0 && audio.CurrentPlaylistIndex < choices.Count)
                _playlistSelector.SetValueWithoutNotify(choices[audio.CurrentPlaylistIndex]);
            _suppressEvents = false;
            Refresh();
        }

        private static string FindRawName(AudioManager audio, string prettyName)
        {
            for (int i = 0; i < audio.PlaylistNames.Count; i++)
                if (AudioManager.PrettyPlaylistName(audio.PlaylistNames[i]) == prettyName)
                    return audio.PlaylistNames[i];
            return "";
        }

        /// <summary>
        /// The cheap per-frame update (PhoneController.Tick): the seek bar, the times and the play button. Everything
        /// else is rebuilt only when something changed (<see cref="Refresh"/>). This used to call Refresh every frame,
        /// which cleared and rebuilt the whole playlist (a row of labels and images per track) sixty times a second.
        /// </summary>
        public void RefreshTransport()
        {
            var audio = AudioManager.Instance;
            if (audio == null) return;

            _suppressEvents = true;
            if (!_draggingSeek && _seekSlider != null) _seekSlider.SetValueWithoutNotify(audio.TrackPosition01);
            if (_timeElapsed != null && !_draggingSeek) SetTextIfChanged(_timeElapsed, FormatTime(audio.TrackTimeSeconds));
            if (_timeTotal != null) SetTextIfChanged(_timeTotal, FormatTime(audio.TrackLengthSeconds));
            if (_playPauseBtn != null) SetTextIfChanged(_playPauseBtn, audio.IsMusicPlaying ? "⏸" : "▶");
            _suppressEvents = false;
        }

        private static void SetTextIfChanged(TextElement el, string text)
        {
            if (el.text != text) el.text = text;
        }

        private string _playlistSignature;

        public void Refresh()
        {
            var audio = AudioManager.Instance;
            if (audio == null) return;

            _suppressEvents = true;

            if (_trackTitle != null) _trackTitle.text = audio.CurrentTrackName;
            if (_trackMeta != null) _trackMeta.text = audio.MusicPlaylist.Count > 0
                ? $"Track {audio.CurrentTrackIndex + 1} of {audio.MusicPlaylist.Count}"
                : "No tracks found";

            // Art belongs to the playlist (Resources/Audio/Covers/<playlist>.png), never to a track; no cover = the plain note glyph.
            Texture2D playlistCover = SteadifyAlbumArt.ForPlaylist(audio.CurrentPlaylistName);
            if (_albumArt != null)
            {
                _albumArt.style.backgroundImage = playlistCover != null ? new StyleBackground(playlistCover) : new StyleBackground(StyleKeyword.None);
                _albumArt.style.unityBackgroundImageTintColor = Color.white;
                if (_albumArtGlyph != null) _albumArtGlyph.style.display = playlistCover != null ? DisplayStyle.None : DisplayStyle.Flex;
            }

            if (_playPauseBtn != null) _playPauseBtn.text = audio.IsMusicPlaying ? "⏸" : "▶";

            if (!_draggingSeek && _seekSlider != null) _seekSlider.SetValueWithoutNotify(audio.TrackPosition01);
            if (_timeElapsed != null && !_draggingSeek) _timeElapsed.text = FormatTime(audio.TrackTimeSeconds);
            if (_timeTotal != null) _timeTotal.text = FormatTime(audio.TrackLengthSeconds);

            if (_volumeSlider != null) _volumeSlider.SetValueWithoutNotify(audio.MusicVolume01 * 100f);
            if (_volumeValue != null) _volumeValue.text = Mathf.RoundToInt(audio.MusicVolume01 * 100f) + "%";

            if (_shuffleBtn != null) _shuffleBtn.EnableInClassList("steadify-transport-btn--active", audio.ShuffleEnabled);
            if (_repeatBtn != null)
            {
                _repeatBtn.EnableInClassList("steadify-transport-btn--active", audio.CurrentRepeatMode != AudioManager.RepeatMode.Off);
                _repeatBtn.text = audio.CurrentRepeatMode == AudioManager.RepeatMode.One ? "" : "";
            }

            // Rebuild the playlist rows only when what they show has changed.
            string signature = audio.CurrentPlaylistIndex + "|" + audio.CurrentTrackIndex + "|" + audio.IsMusicPlaying + "|" + audio.MusicPlaylist.Count;
            if (signature != _playlistSignature)
            {
                _playlistSignature = signature;
                RefreshPlaylist(audio);
            }

            _suppressEvents = false;
        }

        private void RefreshPlaylist(AudioManager audio)
        {
            if (_playlistContainer == null) return;
            _playlistContainer.Clear();

            IReadOnlyList<AudioClip> tracks = audio.MusicPlaylist;
            if (tracks.Count == 0)
            {
                var none = new Label("No music tracks found in Resources/Audio/Music.");
                none.AddToClassList("store-empty-search-label");
                _playlistContainer.Add(none);
                return;
            }

            for (int i = 0; i < tracks.Count; i++)
            {
                _playlistContainer.Add(BuildTrackRow(audio, i));
            }
        }

        private VisualElement BuildTrackRow(AudioManager audio, int index)
        {
            bool isCurrent = index == audio.CurrentTrackIndex;

            var row = new VisualElement();
            row.AddToClassList("steadify-track-row");
            if (isCurrent) row.AddToClassList("steadify-track-row--active");

            string rowTrackName = TrackDisplayName(audio, index);
            // No per-track art: a small play / pause marker on the current track, blank space on the rest so the titles line up.
            var marker = new Label(isCurrent ? (audio.IsMusicPlaying ? "▶" : "⏸") : "");
            marker.AddToClassList("steadify-track-row-glyph");
            row.Add(marker);

            var info = new VisualElement();
            info.AddToClassList("steadify-track-row-info");

            var title = new Label(rowTrackName);
            title.AddToClassList("steadify-track-row-title");
            info.Add(title);

            var sub = new Label(isCurrent ? (audio.IsMusicPlaying ? "Now Playing" : "Paused") : "");
            sub.AddToClassList("steadify-track-row-sub");
            info.Add(sub);

            row.Add(info);

            row.RegisterCallback<ClickEvent>(evt => AudioManager.Instance?.MusicPlayTrackAt(index));
            return row;
        }

        private static string TrackDisplayName(AudioManager audio, int index)
        {
            var tracks = audio.MusicPlaylist;
            if (index < 0 || index >= tracks.Count || tracks[index] == null) return "Unknown Track";
            string n = AudioManager.StripTrackPrefix(tracks[index].name);
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < n.Length; i++)
            {
                if (i > 0 && char.IsUpper(n[i]) && !char.IsUpper(n[i - 1])) sb.Append(' ');
                sb.Append(n[i] == '_' ? ' ' : n[i]);
            }
            return sb.ToString().Trim();
        }

        private static string FormatTime(float seconds)
        {
            if (seconds < 0f || float.IsNaN(seconds)) seconds = 0f;
            int total = Mathf.FloorToInt(seconds);
            int m = total / 60;
            int s = total % 60;
            return $"{m}:{s:00}";
        }
    }
}
