// RadioSettings.cs - player settings for Steadify radio (Settings > Audio > Radio): which script writer builds
// the episodes (templated, free and offline; or Claude, written live from the day's facts through the Claude API),
// the API key and model for the Claude mode, and the last station tuned in. Stored in PlayerPrefs like the other
// settings; the key is kept on this machine only and never leaves it except in the request to api.anthropic.com.

using System;
using UnityEngine;

namespace Homesteader.Radio
{
    public static class RadioSettings
    {
        public enum ScriptMode { Templated = 0, Claude = 1 }

        private const string ModeKey = "Homesteader.Radio.ScriptMode";
        private const string ApiKeyKey = "Homesteader.Radio.ClaudeApiKey";
        private const string ModelKey = "Homesteader.Radio.ClaudeModel";
        private const string StationKey = "Homesteader.Radio.Station";

        public const string DefaultModel = "claude-opus-5-5";

        public static event Action Changed;

        public static ScriptMode Mode
        {
            get => (ScriptMode)PlayerPrefs.GetInt(ModeKey, (int)ScriptMode.Templated);
            set { PlayerPrefs.SetInt(ModeKey, (int)value); PlayerPrefs.Save(); Changed?.Invoke(); }
        }

        /// <summary>The key typed into Settings, else the ANTHROPIC_API_KEY environment variable, else "".</summary>
        public static string ApiKey
        {
            get
            {
                string k = PlayerPrefs.GetString(ApiKeyKey, "");
                if (string.IsNullOrEmpty(k)) k = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY") ?? "";
                return k.Trim();
            }
            set { PlayerPrefs.SetString(ApiKeyKey, (value ?? "").Trim()); PlayerPrefs.Save(); Changed?.Invoke(); }
        }

        public static bool HasApiKey => !string.IsNullOrEmpty(ApiKey);

        public static string Model
        {
            get { string m = PlayerPrefs.GetString(ModelKey, DefaultModel); return string.IsNullOrEmpty(m) ? DefaultModel : m; }
            set { PlayerPrefs.SetString(ModelKey, string.IsNullOrEmpty(value) ? DefaultModel : value.Trim()); PlayerPrefs.Save(); Changed?.Invoke(); }
        }

        public static string LastStation
        {
            get => PlayerPrefs.GetString(StationKey, "");
            set { PlayerPrefs.SetString(StationKey, value ?? ""); PlayerPrefs.Save(); }
        }

        /// <summary>The mode that will actually be used right now: Claude needs a key, otherwise episodes fall back to templated.</summary>
        public static ScriptMode EffectiveMode => Mode == ScriptMode.Claude && HasApiKey ? ScriptMode.Claude : ScriptMode.Templated;

        public static void ResetToDefaults()
        {
            PlayerPrefs.DeleteKey(ModeKey);
            PlayerPrefs.DeleteKey(ModelKey);
            PlayerPrefs.Save();
            Changed?.Invoke();
        }
    }
}
