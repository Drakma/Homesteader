// SteadifyLocalPanel.cs - the Local tab of the Steadify phone app (markup: SteadifyLocalPane in PhoneUI.uxml). Shows and
// controls whatever the PC is playing (Spotify, a browser, a video player) through LocalMedia: cover, title, artist, time
// and previous / play-pause / next. Owned by SteadifyApp, which also flips between the Music, Radio and Local panes.

using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class SteadifyLocalPanel
    {
        private const float PollSeconds = 0.25f;

        private readonly VisualElement _pane;
        private readonly DropdownField _source;
        private readonly System.Collections.Generic.List<string> _sourceIds = new System.Collections.Generic.List<string>();
        private string _sourceSignature;
        private bool _suppress;
        private readonly VisualElement _art;
        private readonly Label _artGlyph;
        private readonly Label _title;
        private readonly Label _status;
        private readonly Label _time;
        private readonly VisualElement _progressFill;
        private readonly Button _prevBtn;
        private readonly Button _playPauseBtn;
        private readonly Button _nextBtn;

        private float _nextPoll;

        public SteadifyLocalPanel(VisualElement root)
        {
            _pane = root.Q<VisualElement>("SteadifyLocalPane");
            _source = root.Q<DropdownField>("SteadifyLocalSource");
            _art = root.Q<VisualElement>("SteadifyLocalArt");
            _artGlyph = _art?.Q<Label>(className: "steadify-album-art-glyph");
            _title = root.Q<Label>("SteadifyLocalTitle");
            _status = root.Q<Label>("SteadifyLocalStatus");
            _time = root.Q<Label>("SteadifyLocalTime");
            _progressFill = root.Q<VisualElement>("SteadifyLocalProgressFill");
            _prevBtn = root.Q<Button>("SteadifyLocalPrevBtn");
            _playPauseBtn = root.Q<Button>("SteadifyLocalPlayPauseBtn");
            _nextBtn = root.Q<Button>("SteadifyLocalNextBtn");
            if (_pane == null) return;

            _source?.RegisterValueChangedCallback(evt =>
            {
                if (_suppress) return;
                int i = _source.index;
                if (i >= 0 && i < _sourceIds.Count) { LocalMedia.Select(_sourceIds[i]); _nextPoll = 0f; }
            });

            _prevBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt => { LocalMedia.Previous(); _nextPoll = 0f; });
            _nextBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt => { LocalMedia.Next(); _nextPoll = 0f; });
            _playPauseBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt => { LocalMedia.PlayPause(); _nextPoll = Time.unscaledTime + 0.3f; });
        }

        public void SetVisible(bool visible)
        {
            _pane?.EnableInClassList("steadify-local-pane--hidden", !visible);
            if (visible) { _nextPoll = 0f; Tick(); }
        }

        public void Tick()
        {
            if (_pane == null || Time.unscaledTime < _nextPoll) return;
            _nextPoll = Time.unscaledTime + PollSeconds;

            LocalMedia.Snapshot s = LocalMedia.Read();
            RefreshSources();
            switch (s.State)
            {
                case LocalMedia.State.Playing:
                case LocalMedia.State.Paused:
                    Set(_title, s.Title);
                    Set(_status, string.IsNullOrEmpty(s.Artist) ? s.Album : s.Artist);
                    Set(_playPauseBtn, s.State == LocalMedia.State.Playing ? "⏸" : "▶");
                    break;
                case LocalMedia.State.None:
                    Set(_title, "Nothing is playing");
                    Set(_status, "Start a song or video on this PC.");
                    Set(_playPauseBtn, "▶");
                    break;
                default:
                    Set(_title, "Not available");
                    Set(_status, LocalMedia.Supported ? "Local media info needs the helper: run tools/build_local_media_helper.ps1" : "Local media control works on Windows only.");
                    Set(_playPauseBtn, "▶");
                    break;
            }

            bool hasLength = s.Length > 1f && (s.State == LocalMedia.State.Playing || s.State == LocalMedia.State.Paused);
            Set(_time, hasLength ? LocalMedia.FormatTime(s.Position) + " / " + LocalMedia.FormatTime(s.Length) : "");
            if (_progressFill != null) _progressFill.style.width = Length.Percent(hasLength ? Mathf.Clamp01(s.Position / s.Length) * 100f : 0f);

            Texture2D cover = LocalMedia.Art(s);
            if (_art != null)
            {
                _art.style.backgroundImage = cover != null ? new StyleBackground(cover) : new StyleBackground(StyleKeyword.None);
                _art.style.unityBackgroundImageTintColor = Color.white;
                if (_artGlyph != null) _artGlyph.style.display = cover != null ? DisplayStyle.None : DisplayStyle.Flex;
            }
        }

        /// <summary>"Automatic" plus one entry per program that has a media session; rebuilt only when that set changes.</summary>
        private void RefreshSources()
        {
            if (_source == null) return;
            LocalMedia.Source[] list = LocalMedia.Sources();
            string selected = LocalMedia.SelectedApp;
            string signature = selected + "|";
            foreach (LocalMedia.Source x in list) signature += x.app + ";";
            if (signature == _sourceSignature) return;
            _sourceSignature = signature;

            _sourceIds.Clear();
            var choices = new System.Collections.Generic.List<string>();
            _sourceIds.Add(""); choices.Add("Automatic");
            bool found = selected == "";
            foreach (LocalMedia.Source x in list)
            {
                _sourceIds.Add(x.app);
                choices.Add(LocalMedia.FriendlyName(x.app));
                if (x.app == selected) found = true;
            }
            if (!found)   // the chosen program closed: keep it listed so the choice stays visible
            {
                _sourceIds.Add(selected);
                choices.Add(LocalMedia.FriendlyName(selected) + " (closed)");
            }
            _suppress = true;
            _source.choices = choices;
            _source.index = Mathf.Max(0, _sourceIds.IndexOf(selected));
            _suppress = false;
        }

        private static void Set(TextElement el, string text)
        {
            if (el != null && el.text != text) el.text = text;
        }
    }
}
