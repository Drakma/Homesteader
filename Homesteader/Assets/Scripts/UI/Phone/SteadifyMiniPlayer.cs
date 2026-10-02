// SteadifyMiniPlayer.cs - the pop-out Steadify player: a small window with the cover, track info, elapsed time, glyph transport buttons and a
// vertical volume slider that floats over the game (drag it by its title bar) and controls the music while the phone is closed. Opened from the
// pop-out button next to "Shuffle All" in the Steadify app. One at a time; the same button (or the window's close button) closes it.
// Styles: PhoneUI.uss (steadify-mini-*).

using Homesteader.Audio;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class SteadifyMiniPlayer
    {
        private static SteadifyMiniPlayer _open;

        public static bool IsOpen => _open != null;

        // Where the player is shown from a save (the phone registers its root once it is built), and where it was last put.
        private static VisualElement _host;
        private static Vector2 _lastPos = new Vector2(40f, 90f);

        public static void SetHost(VisualElement anyElementOnPanel) { _host = anyElementOnPanel; }

        /// <summary>For the save: whether the mini player is open and where it sits.</summary>
        public static void Capture(out bool open, out float x, out float y)
        {
            open = _open != null;
            if (_open != null) _lastPos = new Vector2(_open._window.resolvedStyle.left, _open._window.resolvedStyle.top);
            x = _lastPos.x; y = _lastPos.y;
        }

        /// <summary>For loading a save: open (at the saved spot) or close the mini player to match.</summary>
        public static void Restore(bool open, float x, float y)
        {
            _lastPos = new Vector2(x, y);
            if (_open != null) _open.Close();
            if (open && _host != null) { Toggle(_host); }
        }

        /// <summary>Opens the mini player on the same panel as the given element, or closes it if it is already open.</summary>
        public static void Toggle(VisualElement anyElementOnPanel)
        {
            if (_open != null) { _open.Close(); return; }
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
        private readonly Label _elapsed;
        private readonly Slider _volume;
        private readonly Button _shuffle, _prev, _play, _next, _repeat;
        private IVisualElementScheduledItem _tick;
        private bool _suppress;

        private SteadifyMiniPlayer(VisualElement panelRoot)
        {
            _window = new VisualElement { name = "SteadifyMiniPlayer" };
            _window.AddToClassList("steadify-mini");
            _window.style.position = Position.Absolute;
            _window.style.left = _lastPos.x;
            _window.style.top = _lastPos.y;

            // Title bar: the drag handle.
            var header = new VisualElement();
            header.AddToClassList("steadify-mini-header");
            var headerTitle = new Label("STEADIFY");
            headerTitle.AddToClassList("steadify-mini-header-title");
            headerTitle.pickingMode = PickingMode.Ignore;
            header.tooltip = "Drag to move";
            var shuffleAll = new Button(() => AudioManager.Instance?.MusicShuffleAll()) { text = "SHUFFLE ALL", tooltip = "Shuffle All: play every song from every playlist in random order" };
            shuffleAll.AddToClassList("steadify-mini-shuffleall");
            var close = new Button(Close) { text = "\u00D7", tooltip = "Close the mini player" };
            close.AddToClassList("steadify-mini-close");
            header.Add(headerTitle);
            header.Add(shuffleAll);
            header.Add(close);
            _window.Add(header);
            MakeDraggable(_window, header);

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
            _lastPos = new Vector2(_window.resolvedStyle.left, _window.resolvedStyle.top);
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

        /// <summary>Drag a window by its title bar, kept inside the panel (same pattern as the HUD windows).</summary>
        private static void MakeDraggable(VisualElement window, VisualElement handle)
        {
            bool dragging = false;
            Vector2 startPointer = Vector2.zero, startPos = Vector2.zero;
            handle.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.target is Button) return;   // the close button is not part of the handle
                dragging = true;
                startPointer = evt.position;
                startPos = new Vector2(window.resolvedStyle.left, window.resolvedStyle.top);
                handle.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!dragging) return;
                Vector2 p = startPos + ((Vector2)evt.position - startPointer);
                var parent = window.parent;
                float maxX = (parent != null ? parent.resolvedStyle.width : Screen.width) - window.resolvedStyle.width;
                float maxY = (parent != null ? parent.resolvedStyle.height : Screen.height) - window.resolvedStyle.height;
                window.style.left = Mathf.Clamp(p.x, 0f, Mathf.Max(0f, maxX));
                window.style.top = Mathf.Clamp(p.y, 0f, Mathf.Max(0f, maxY));
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (!dragging) return;
                dragging = false;
                handle.ReleasePointer(evt.pointerId);
                evt.StopPropagation();
            });
        }
    }
}
