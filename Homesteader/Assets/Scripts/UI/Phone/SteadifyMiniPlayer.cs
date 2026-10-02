// SteadifyMiniPlayer.cs - the pop-out Steadify player: a small window with the cover, track info, elapsed time, glyph transport buttons and a
// vertical volume slider that floats over the game (drag it by its title bar) and controls the music while the phone is closed. Opened from the
// pop-out button next to "Shuffle All" in the Steadify app. One at a time; the same button (or the window's close button) closes it.
// Styles: PhoneUI.uss (steadify-mini-*).

using System.Collections.Generic;
using Homesteader.Audio;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class SteadifyMiniPlayer
    {
        private static SteadifyMiniPlayer _open;
        private const string WindowId = "steadify_mini";

        // Enter Play Mode keeps statics between plays: forget the last play's window and phone root, or Restore and Toggle talk to a dead panel.
        [UnityEngine.RuntimeInitializeOnLoadMethod(UnityEngine.RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { _open = null; _host = null; _wanted = false; }

        // Whether the player should be showing. It follows the player's own open / close, NOT the window itself: when the game quits or a
        // load rebuilds the HUD the window is already gone, and reading it then saved "closed" and lost the mini player every time.
        private static bool _wanted;

        public static bool IsOpen
        {
            get
            {
                if (_open != null && _open._window.panel != null) return _wanted = true;
                return _wanted;
            }
        }

        /// <summary>A mini player whose window left the panel (the HUD was rebuilt by New Game or a load) is not open any more; without this the first click only "closed" the stale one.</summary>
        private static void DropStale()
        {
            if (_open != null && _open._window.panel == null) _open.Close();   // also unsubscribes its audio events
        }

        // Where the player is shown from a save (the phone registers its root once it is built), and where it was last put.
        private static VisualElement _host;

        public static void SetHost(VisualElement anyElementOnPanel)
        {
            _host = anyElementOnPanel;
            if (_wanted && _open == null) Toggle(_host);   // a save asked for it before the phone existed
        }

        /// <summary>For loading a save: open (at the saved spot) or close the mini player to match.</summary>
        public static void Restore(bool open)
        {
            DropStale();
            if (_open != null) _open.Close();
            _wanted = open;
            if (open && _host != null && _host.panel != null) Toggle(_host);   // otherwise SetHost opens it when the phone is built
        }

        /// <summary>Opens the mini player on the same panel as the given element, or closes it if it is already open.</summary>
        public static void Toggle(VisualElement anyElementOnPanel)
        {
            DropStale();
            if (_open != null) { _wanted = false; _open.Close(); return; }
            _wanted = true;
            // Added under the HUD document's own root (not the panel's), so the HUD style sheets (PhoneUI.uss) apply to it.
            var top = anyElementOnPanel;
            var tree = top?.panel?.visualTree;
            if (top == null || tree == null) return;
            while (top.parent != null && top.parent != tree) top = top.parent;
            _open = new SteadifyMiniPlayer(top);
        }

        private readonly VisualElement _window;
        private readonly VisualElement _art;
        private readonly Label _artGlyph;
        private readonly Label _title;
        private readonly Label _meta;
        private readonly DropdownField _playlist;
        private readonly Label _elapsed;
        private readonly Slider _volume;
        private readonly Button _shuffle, _prev, _play, _next, _repeat;
        private IVisualElementScheduledItem _tick;
        private bool _suppress;

        private SteadifyMiniPlayer(VisualElement panelRoot)
        {
            _window = new VisualElement { name = "SteadifyMiniPlayer" };
            _window.AddToClassList("window");
            _window.AddToClassList("steadify-mini");
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            _window.Add(edge);
            _window.style.position = Position.Absolute;

            // Title bar: the drag handle.
            var header = new VisualElement();
            header.AddToClassList("window-header");
            header.AddToClassList("steadify-mini-header");
            var headerTitle = new Label("STEADIFY");
            headerTitle.AddToClassList("window-title");
            headerTitle.AddToClassList("steadify-mini-header-title");
            headerTitle.pickingMode = PickingMode.Ignore;
            header.tooltip = "Drag to move";
            _playlist = new DropdownField();
            _playlist.AddToClassList("hs-dropdown");
            _playlist.AddToClassList("steadify-mini-playlist");
            _playlist.tooltip = "Choose a playlist (All Songs plays everything)";
            var names = new List<string>();
            if (AudioManager.Instance != null)
                foreach (string n in AudioManager.Instance.PlaylistNames) names.Add(AudioManager.PrettyPlaylistName(n));
            _playlist.choices = names;
            _playlist.RegisterValueChangedCallback(evt =>
            {
                if (_suppress) return;
                var a = AudioManager.Instance;
                int index = _playlist.index;
                if (a != null && index >= 0) a.MusicSetPlaylist(index);
            });
            var close = new Button(Close) { text = "X", tooltip = "Close the mini player" };
            close.AddToClassList("hs-close");
            header.Add(headerTitle);
            header.Add(_playlist);
            header.Add(close);
            _window.Add(header);
            WindowPositions.MakeDraggable(_window, header, WindowId);

            var body = new VisualElement();
            body.AddToClassList("steadify-mini-body");
            _window.Add(body);

            // Album art fills the whole left side; to its right the playlist name on top, the song in the middle and the controls at the bottom.
            _art = new VisualElement();
            _art.AddToClassList("steadify-mini-art");
            _art.tooltip = "Playlist cover";
            _artGlyph = new Label("\u266B");
            _artGlyph.AddToClassList("steadify-album-art-glyph");
            _artGlyph.AddToClassList("steadify-mini-art-glyph");
            _artGlyph.pickingMode = PickingMode.Ignore;
            _art.Add(_artGlyph);
            body.Add(_art);

            var mid = new VisualElement();
            mid.AddToClassList("steadify-mini-mid");
            body.Add(mid);

            _meta = new Label("");
            _meta.AddToClassList("steadify-mini-meta");
            _meta.tooltip = "Current playlist and track number";
            mid.Add(_meta);

            var songBox = new VisualElement();
            songBox.AddToClassList("steadify-mini-songbox");
            _title = new Label("No Track");
            _title.AddToClassList("steadify-mini-title");
            _title.tooltip = "Current song";
            songBox.Add(_title);
            mid.Add(songBox);

            var row = new VisualElement();
            row.AddToClassList("steadify-mini-row");
            _elapsed = new Label("0:00");
            _elapsed.AddToClassList("steadify-mini-time");
            _elapsed.tooltip = "Time left in this song";
            row.Add(_elapsed);
            _shuffle = MakeButton("\uE000", "Shuffle: random order within this playlist", () => { var a = AudioManager.Instance; if (a != null) a.MusicSetShuffle(!a.ShuffleEnabled); });
            _prev = MakeButton("\u23EE", "Previous track", () => AudioManager.Instance?.MusicPrevious());
            _play = MakeButton("\u25B6", "Play / pause", () => AudioManager.Instance?.MusicTogglePlayPause());
            _next = MakeButton("\u23ED", "Next track", () => AudioManager.Instance?.MusicNext());
            _repeat = MakeButton("\uE001", "Repeat: off, all, or one track", () => AudioManager.Instance?.MusicCycleRepeatMode());
            row.Add(_shuffle); row.Add(_prev); row.Add(_play); row.Add(_next); row.Add(_repeat);
            mid.Add(row);

            // Right: the volume, a vertical slider (bottom = quiet, top = loud).
            _volume = new Slider(0f, 100f, SliderDirection.Vertical);
            _volume.AddToClassList("steadify-mini-volume");
            _volume.tooltip = "Music volume";
            body.Add(_volume);
            _volume.RegisterValueChangedCallback(evt =>
            {
                if (_suppress) return;
                AudioManager.Instance?.MusicSetVolume01(evt.newValue / 100f);
            });

            // Under the welcome wallpaper and menu (they are the last children of the HUD root), so the main menu and loading screen cover it.
            VisualElement wallpaper = panelRoot.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == panelRoot) panelRoot.Insert(panelRoot.IndexOf(wallpaper), _window);
            else panelRoot.Add(_window);
            WindowPositions.Place(_window, WindowId);   // centered the first time, then where it was left
            PopupStyles.Ensure(_window);
            var audio = AudioManager.Instance;
            if (audio != null) { audio.MusicStateChanged += Refresh; audio.PlaylistChanged += Refresh; }
            _tick = _window.schedule.Execute(RefreshTransport).Every(200);
            Refresh();
        }

        /// <summary>A glyph-only button: grey at rest, white on hover, orange while it is on.</summary>
        private static Button MakeButton(string glyph, string tip, System.Action onClick)
        {
            var b = new Button(onClick) { text = glyph, tooltip = tip };
            b.AddToClassList("steadify-mini-btn");
            return b;
        }

        public void Close()
        {
            var audio = AudioManager.Instance;
            if (audio != null) { audio.MusicStateChanged -= Refresh; audio.PlaylistChanged -= Refresh; }
            WindowPositions.Remember(_window, WindowId);
            _tick?.Pause();
            _window.RemoveFromHierarchy();
            if (_open == this) _open = null;
        }

        /// <summary>Everything that changes with the track, the playlist, shuffle or repeat.</summary>
        private void Refresh()
        {
            var audio = AudioManager.Instance;
            if (audio == null || _window.panel == null) return;
            _suppress = true;

            _title.text = audio.CurrentTrackName;
            string playlist = AudioManager.PrettyPlaylistName(audio.CurrentPlaylistName);
            _meta.text = audio.MusicPlaylist.Count > 0 ? $"{playlist}  {audio.CurrentTrackIndex + 1}/{audio.MusicPlaylist.Count}" : playlist;
            if (audio.CurrentPlaylistIndex >= 0 && audio.CurrentPlaylistIndex < _playlist.choices.Count)
                _playlist.SetValueWithoutNotify(_playlist.choices[audio.CurrentPlaylistIndex]);

            Texture2D cover = SteadifyAlbumArt.ForPlaylist(audio.CurrentPlaylistName);
            _art.style.backgroundImage = cover != null ? new StyleBackground(cover) : new StyleBackground(StyleKeyword.None);
            _artGlyph.style.display = cover != null ? DisplayStyle.None : DisplayStyle.Flex;

            _shuffle.EnableInClassList("steadify-mini-btn--on", audio.ShuffleEnabled);
            _repeat.EnableInClassList("steadify-mini-btn--on", audio.CurrentRepeatMode != AudioManager.RepeatMode.Off);
            _repeat.text = audio.CurrentRepeatMode == AudioManager.RepeatMode.One ? "" : "";
            _volume.SetValueWithoutNotify(audio.MusicVolume01 * 100f);

            _suppress = false;
            RefreshTransport();
        }

        /// <summary>The cheap part, five times a second: the time left and the play button.</summary>
        private void RefreshTransport()
        {
            var audio = AudioManager.Instance;
            if (audio == null) return;
            SetText(_elapsed, "-" + FormatTime(Mathf.Max(0f, audio.TrackLengthSeconds - audio.TrackTimeSeconds)));
            SetText(_play, audio.IsMusicPlaying ? "⏸" : "▶");
            _play.EnableInClassList("steadify-mini-btn--on", audio.IsMusicPlaying);
        }

        private static void SetText(TextElement el, string text) { if (el.text != text) el.text = text; }

        private static string FormatTime(float seconds)
        {
            if (seconds < 0f || float.IsNaN(seconds)) seconds = 0f;
            int total = Mathf.FloorToInt(seconds);
            return $"{total / 60}:{total % 60:00}";
        }

    }
}
