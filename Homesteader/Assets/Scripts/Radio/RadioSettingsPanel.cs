// RadioSettingsPanel.cs - wires the Radio section of Settings > Audio (WelcomeMenu.uxml): the script writer dropdown,
// the Claude API key and model fields, and a line saying whether the local voice pack is installed. Called from
// SettingsDialogController.ResolveReferences; values go straight into RadioSettings (PlayerPrefs).

using Homesteader.Radio.Tts;
using UnityEngine.UIElements;

namespace Homesteader.Radio
{
    public static class RadioSettingsPanel
    {
        private static DropdownField s_mode;
        private static TextField s_key;
        private static TextField s_model;
        private static Label s_voice;
        private static bool s_applying;

        private static readonly string[] ModeNames = { "Almanac (free, offline)", "Claude (live, needs API key)" };

        public static void Wire(VisualElement root)
        {
            if (root == null) return;
            s_mode = root.Q<DropdownField>("RadioScriptMode");
            s_key = root.Q<TextField>("RadioApiKey");
            s_model = root.Q<TextField>("RadioModel");
            s_voice = root.Q<Label>("RadioVoiceStatus");
            if (s_mode == null) return;

            s_mode.choices = new System.Collections.Generic.List<string>(ModeNames);
            s_mode.RegisterValueChangedCallback(evt =>
            {
                if (s_applying) return;
                int idx = s_mode.choices.IndexOf(evt.newValue);
                RadioSettings.Mode = idx == 1 ? RadioSettings.ScriptMode.Claude : RadioSettings.ScriptMode.Templated;
                Refresh();
            });

            if (s_key != null)
            {
                s_key.isPasswordField = true;
                s_key.RegisterCallback<FocusOutEvent>(evt => { if (!s_applying) { RadioSettings.ApiKey = s_key.value; Refresh(); } });
            }
            if (s_model != null)
                s_model.RegisterCallback<FocusOutEvent>(evt => { if (!s_applying) { RadioSettings.Model = s_model.value; } });

            Refresh();
        }

        public static void Refresh()
        {
            if (s_mode == null) return;
            s_applying = true;
            s_mode.SetValueWithoutNotify(ModeNames[RadioSettings.Mode == RadioSettings.ScriptMode.Claude ? 1 : 0]);
            if (s_key != null) s_key.SetValueWithoutNotify(UnityEngine.PlayerPrefs.GetString("Homesteader.Radio.ClaudeApiKey", ""));
            if (s_model != null) s_model.SetValueWithoutNotify(RadioSettings.Model);
            if (s_voice != null)
            {
                string voice = KokoroTtsEngine.ModelFilesPresent()
                    ? "Voice pack: installed (Kokoro, runs locally)."
                    : "Voice pack: not installed. Episodes show as text until you run: python tools/fetch_tts_runtime.py";
                string claude = RadioSettings.Mode == RadioSettings.ScriptMode.Claude && !RadioSettings.HasApiKey
                    ? " No API key set, so episodes fall back to the almanac writer."
                    : "";
                s_voice.text = voice + claude;
            }
            s_applying = false;
        }
    }
}
