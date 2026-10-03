// SteadifyRadioPanel.cs - the Radio tab of the Steadify phone app (markup: SteadifyRadioPane in PhoneUI.uxml). Picks a
// station, tunes RadioPlayer in and out, pauses, asks for a rewrite, and shows the transcript with the line being
// spoken highlighted. Owned by SteadifyApp, which also flips between the Music and Radio panes.

using System.Collections.Generic;
using Homesteader.Radio;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public sealed class SteadifyRadioPanel
    {
        private readonly VisualElement _pane;
        private readonly DropdownField _station;
        private readonly Label _frequency;
        private readonly Label _title;
        private readonly Label _status;
        private readonly VisualElement _progressFill;
        private readonly Button _powerBtn;
        private readonly Button _pauseBtn;
        private readonly Button _rewriteBtn;
        private readonly Label _voice;
        private readonly ScrollView _scroll;
        private readonly VisualElement _transcript;

        private readonly List<VisualElement> _lineRows = new List<VisualElement>();
        private RadioEpisode _shownEpisode;
        private int _shownLine = -2;
        private bool _suppress;

        public SteadifyRadioPanel(VisualElement root)
        {
            _pane = root.Q<VisualElement>("SteadifyRadioPane");
            _station = root.Q<DropdownField>("SteadifyRadioStation");
            _frequency = root.Q<Label>("SteadifyRadioFrequency");
            _title = root.Q<Label>("SteadifyRadioTitle");
            _status = root.Q<Label>("SteadifyRadioStatus");
            _progressFill = root.Q<VisualElement>("SteadifyRadioProgressFill");
            _powerBtn = root.Q<Button>("SteadifyRadioPowerBtn");
            _pauseBtn = root.Q<Button>("SteadifyRadioPauseBtn");
            _rewriteBtn = root.Q<Button>("SteadifyRadioRewriteBtn");
            _voice = root.Q<Label>("SteadifyRadioVoice");
            _scroll = root.Q<ScrollView>("SteadifyRadioScroll");
            _transcript = root.Q<VisualElement>("SteadifyRadioTranscript");
            if (_pane == null) return;

            FillStations();
            RadioRegistry.Changed += FillStations;

            _station?.RegisterValueChangedCallback(evt =>
            {
                if (_suppress) return;
                RadioStationDefinition def = StationByName(evt.newValue);
                if (def != null && RadioPlayer.Instance != null) RadioPlayer.Instance.Tune(def);
            });

            _powerBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt =>
            {
                var p = RadioPlayer.Instance;
                if (p == null) return;
                if (p.IsOn) p.Stop();
                else
                {
                    RadioStationDefinition def = StationByName(_station != null ? _station.value : null) ?? FirstStation();
                    if (def != null) p.Tune(def);
                }
            });
            _pauseBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt => RadioPlayer.Instance?.TogglePause());
            _rewriteBtn?.Clickable()?.RegisterCallback<ClickEvent>(evt => RadioPlayer.Instance?.Rewrite());

            if (RadioPlayer.Instance != null) RadioPlayer.Instance.Changed += Refresh;
            Refresh();
        }

        public void SetVisible(bool visible)
        {
            _pane?.EnableInClassList("steadify-radio-pane--hidden", !visible);
            if (visible) Refresh();
        }

        // ------------------------------------------------------------------ stations

        private void FillStations()
        {
            if (_station == null) return;
            var names = new List<string>();
            foreach (RadioStationDefinition d in RadioRegistry.All) names.Add(DisplayName(d));
            if (names.Count == 0) names.Add("No stations loaded");
            _suppress = true;
            _station.choices = names;
            RadioStationDefinition current = RadioPlayer.Instance?.Station;
            if (current == null && RadioRegistry.TryGet(RadioSettings.LastStation, out RadioStationDefinition last)) current = last;
            _station.SetValueWithoutNotify(current != null ? DisplayName(current) : names[0]);
            _suppress = false;
        }

        private static string DisplayName(RadioStationDefinition d) =>
            string.IsNullOrEmpty(d.Frequency) ? d.Name : $"{d.Frequency}  {d.Name}";

        private static RadioStationDefinition StationByName(string display)
        {
            if (string.IsNullOrEmpty(display)) return null;
            foreach (RadioStationDefinition d in RadioRegistry.All)
                if (DisplayName(d) == display) return d;
            return null;
        }

        private static RadioStationDefinition FirstStation() => RadioRegistry.All.Count > 0 ? RadioRegistry.All[0] : null;

        // ------------------------------------------------------------------ refresh

        /// <summary>Cheap per-frame update (progress bar only); everything else redraws on RadioPlayer.Changed.</summary>
        public void Tick()
        {
            var p = RadioPlayer.Instance;
            if (p == null || _progressFill == null || _pane == null || _pane.ClassListContains("steadify-radio-pane--hidden")) return;
            _progressFill.style.width = Length.Percent(p.Progress01 * 100f);
        }

        public void Refresh()
        {
            var p = RadioPlayer.Instance;
            if (_pane == null) return;

            bool on = p != null && p.IsOn;
            RadioStationDefinition station = p?.Station;

            if (_frequency != null) _frequency.text = station != null ? station.Frequency : (FirstStation()?.Frequency ?? "");
            if (_title != null) _title.text = on ? (p.Episode != null ? p.Episode.title : station.Name) : "Radio off";
            if (_status != null)
            {
                string s;
                if (!on) s = p != null && p.State == RadioPlayer.RadioState.Failed ? p.LastError : "Pick a station and go on air.";
                else if (p.State == RadioPlayer.RadioState.Paused) s = "Paused";
                else if (p.Episode != null && p.LineIndex >= 0 && p.LineIndex < p.Episode.lines.Count)
                    s = (p.Episode.source == "claude" ? "Written live by Claude. " : "") + $"Line {p.LineIndex + 1} of {p.Episode.lines.Count}";
                else s = p.StatusText;
                _status.text = s;
            }
            if (_powerBtn != null) _powerBtn.text = on ? "Off" : "On Air";
            if (_pauseBtn != null)
            {
                _pauseBtn.SetEnabled(on);
                _pauseBtn.text = p != null && p.State == RadioPlayer.RadioState.Paused ? "▶" : "⏸";
            }
            if (_rewriteBtn != null) _rewriteBtn.SetEnabled(on);
            if (_voice != null && p != null)
            {
                bool hasVoice = p.VoiceAvailable;
                string mode = RadioSettings.EffectiveMode == RadioSettings.ScriptMode.Claude ? "Scripts: Claude" : "Scripts: almanac";
                _voice.text = hasVoice ? $"Voice: Kokoro (local). {mode}." : (on ? $"No voice installed, transcript only. {mode}." : "");
                _voice.EnableInClassList("steadify-radio-voice--warning", on && !hasVoice);
            }

            if (station != null && _station != null)
            {
                string want = DisplayName(station);
                if (_station.value != want) { _suppress = true; _station.SetValueWithoutNotify(want); _suppress = false; }
            }

            RefreshTranscript(p);
        }

        private void RefreshTranscript(RadioPlayer p)
        {
            if (_transcript == null) return;
            RadioEpisode ep = p?.Episode;
            int line = p != null ? p.LineIndex : -1;

            if (ep != _shownEpisode)
            {
                _shownEpisode = ep;
                _shownLine = -2;
                _transcript.Clear();
                _lineRows.Clear();
                if (ep == null)
                {
                    var none = new Label(p != null && p.State == RadioPlayer.RadioState.Writing ? p.StatusText : "Nothing on air.");
                    none.AddToClassList("store-empty-search-label");
                    _transcript.Add(none);
                    return;
                }
                for (int i = 0; i < ep.lines.Count; i++)
                {
                    RadioLine l = ep.lines[i];
                    RadioSpeaker sp = p.Station?.FindSpeaker(l.speaker);
                    var row = new VisualElement();
                    row.AddToClassList("steadify-radio-line");
                    var who = new Label(sp != null ? sp.Name : l.speaker);
                    who.AddToClassList("steadify-radio-line-speaker");
                    row.Add(who);
                    var text = new Label(l.text);
                    text.AddToClassList("steadify-radio-line-text");
                    row.Add(text);
                    int idx = i;
                    row.Clickable().RegisterCallback<ClickEvent>(evt => RadioPlayer.Instance?.SeekToLine(idx));
                    _transcript.Add(row);
                    _lineRows.Add(row);
                }
            }

            if (ep == null || line == _shownLine) return;
            _shownLine = line;
            for (int i = 0; i < _lineRows.Count; i++)
            {
                _lineRows[i].EnableInClassList("steadify-radio-line--active", i == line);
                _lineRows[i].EnableInClassList("steadify-radio-line--done", i < line);
            }
            if (line >= 0 && line < _lineRows.Count && _scroll != null) _scroll.ScrollTo(_lineRows[line]);
        }
    }
}
