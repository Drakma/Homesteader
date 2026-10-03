// KokoroTtsEngine.cs - local, offline text-to-speech with the Kokoro model through sherpa-onnx. Model files live in
// StreamingAssets/Tts/<model folder> (model.onnx, voices.bin, tokens.txt, espeak-ng-data/); the native libraries in
// Assets/Plugins/x86_64. Both are fetched by tools/fetch_tts_runtime.py and are not checked in (the model is 100 MB).
// When either is missing, TryCreate returns null and the radio shows the script as text instead of speaking it.

using System;
using System.IO;
using System.Runtime.InteropServices;
using UnityEngine;

namespace Homesteader.Radio.Tts
{
    public sealed class KokoroTtsEngine : ITtsEngine
    {
        /// <summary>Model folders we know, best first; the first one present under StreamingAssets/Tts is used.</summary>
        public static readonly string[] KnownModelFolders =
        {
            "kokoro-multi-lang-v1_0",      // Kokoro 1.0, fp32: 53 voices, 28 English (the recommended one)
            "kokoro-multi-lang-v1_1",      // Kokoro 1.1-zh, fp32: 103 voices, only 3 English (female)
            "kokoro-en-v0_19",             // Kokoro 0.19, fp32: 11 English voices
            "kokoro-int8-en-v0_19",        // Kokoro 0.19, int8: small download, thin sound
        };
        private static string s_modelRoot;
        private static string s_modelDir;
        private static int s_threads = 2;

        /// <summary>The folder name of the model in use (the first of KnownModelFolders that is installed).</summary>
        public static string ModelFolderName => Path.GetFileName(ModelDir);

        /// <summary>Call once on the main thread (RadioPlayer.Awake): Application.* and SystemInfo.* are main-thread only, and TryCreate runs on the worker.</summary>
        public static void PrimePaths()
        {
            s_modelRoot = Path.Combine(Application.streamingAssetsPath, "Tts");
            s_modelDir = null;   // re-pick the best installed model
            s_threads = Mathf.Clamp(SystemInfo.processorCount / 2, 1, 4);
        }

        public static string ModelRoot => s_modelRoot ?? Path.Combine(Application.streamingAssetsPath, "Tts");

        public static string ModelDir
        {
            get
            {
                if (s_modelDir != null) return s_modelDir;
                foreach (string name in KnownModelFolders)
                {
                    string dir = Path.Combine(ModelRoot, name);
                    if (File.Exists(Path.Combine(dir, "voices.bin"))) { s_modelDir = dir; return dir; }
                }
                return Path.Combine(ModelRoot, KnownModelFolders[0]);   // nothing installed: report the recommended one as missing
            }
        }

        /// <summary>Optional files the 1.x models ship: pronunciation lexicons (comma-joined for sherpa) and the jieba dictionary.</summary>
        /// <summary>Test hooks: when non-null they replace the auto-detected lexicon list / dict dir ("" = none).</summary>
        public static string LexiconOverride;
        public static string DictDirOverride;

        private static string LexiconList()
        {
            if (LexiconOverride != null) return LexiconOverride;
            var parts = new System.Collections.Generic.List<string>();
            foreach (string f in new[] { "lexicon-us-en.txt", "lexicon-zh.txt" })
            {
                string p = Path.Combine(ModelDir, f);
                if (File.Exists(p)) parts.Add(p);
            }
            return string.Join(",", parts);
        }

        private static string DictDir()
        {
            if (DictDirOverride != null) return DictDirOverride;
            string d = Path.Combine(ModelDir, "dict");
            return Directory.Exists(d) ? d : "";
        }

        /// <summary>Voice names by speaker id for kokoro-multi-lang-v1_0 (the recommended model); the station data's "voice" indexes this.</summary>
        public static readonly string[] VoiceNames =
        {
            "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
            "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa",
            "bf_alice", "bf_emma", "bf_isabella", "bf_lily", "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
        };

        private IntPtr _tts;
        // Process-wide: sherpa-onnx's espeak-ng frontend is a global singleton, so two engines (or two threads) must never phonemize at once.
        private static readonly object s_nativeLock = new object();

        public bool IsReady => _tts != IntPtr.Zero;
        public int SampleRate { get; private set; }
        public int NumVoices { get; private set; }
        public string Name => "Kokoro (sherpa-onnx, local)";

        /// <summary>Why the engine is unavailable, for the radio UI; "" when ready.</summary>
        public static string LastStatus { get; private set; } = "";

        /// <summary>The int8 build ships model.int8.onnx, the fp32 build model.onnx; take whichever is there.</summary>
        public static string ModelFile
        {
            get
            {
                string int8 = Path.Combine(ModelDir, "model.int8.onnx");
                return File.Exists(int8) ? int8 : Path.Combine(ModelDir, "model.onnx");
            }
        }

        public static bool ModelFilesPresent() =>
            File.Exists(ModelFile) &&
            File.Exists(Path.Combine(ModelDir, "voices.bin")) &&
            File.Exists(Path.Combine(ModelDir, "tokens.txt")) &&
            Directory.Exists(Path.Combine(ModelDir, "espeak-ng-data"));

        public static KokoroTtsEngine TryCreate()
        {
            if (!ModelFilesPresent())
            {
                LastStatus = "Voice pack not installed. Run: python tools/fetch_tts_runtime.py";
                return null;
            }
            var engine = new KokoroTtsEngine();
            try
            {
                lock (s_nativeLock) engine.Initialise();
            }
            catch (DllNotFoundException)
            {
                LastStatus = "sherpa-onnx-c-api.dll not found in Assets/Plugins/x86_64. Run: python tools/fetch_tts_runtime.py";
                return null;
            }
            catch (Exception e)
            {
                LastStatus = "Voice engine failed to start: " + e.Message;
                Debug.LogWarning("[Radio] " + LastStatus);
                return null;
            }
            if (!engine.IsReady)
            {
                LastStatus = "Voice engine could not load the Kokoro model (see the Unity log).";
                return null;
            }
            LastStatus = "";
            return engine;
        }

        private void Initialise()
        {
            var cfg = new SherpaOnnxNative.OfflineTtsConfig();
            cfg.model.num_threads = s_threads;
            cfg.model.debug = 0;
            cfg.max_num_sentences = 1;      // one sentence per native call keeps each chunk short
            cfg.silence_scale = 0.2f;

            // Length scales default to 0 in a zeroed struct; sherpa treats a non-positive value as 1.0 for Kokoro, but set it explicitly.
            cfg.model.kokoro.length_scale = 1f;
            cfg.model.vits.length_scale = 1f; cfg.model.vits.noise_scale = 0.667f; cfg.model.vits.noise_scale_w = 0.8f;
            cfg.model.matcha.length_scale = 1f; cfg.model.matcha.noise_scale = 0.667f;
            cfg.model.kitten.length_scale = 1f;
            cfg.model.zipvoice.feat_scale = 0.1f; cfg.model.zipvoice.t_shift = 0.5f; cfg.model.zipvoice.target_rms = 0.1f; cfg.model.zipvoice.guidance_scale = 1f;

            IntPtr provider = SherpaOnnxNative.Utf8("cpu");
            IntPtr model = SherpaOnnxNative.Utf8(ModelFile);
            IntPtr voices = SherpaOnnxNative.Utf8(Path.Combine(ModelDir, "voices.bin"));
            IntPtr tokens = SherpaOnnxNative.Utf8(Path.Combine(ModelDir, "tokens.txt"));
            IntPtr dataDir = SherpaOnnxNative.Utf8(Path.Combine(ModelDir, "espeak-ng-data"));
            IntPtr lexicon = SherpaOnnxNative.Utf8(LexiconList());
            IntPtr dictDir = SherpaOnnxNative.Utf8(DictDir());
            IntPtr empty = SherpaOnnxNative.Utf8("");
            try
            {
                cfg.model.provider = provider;
                cfg.model.kokoro.model = model;
                cfg.model.kokoro.voices = voices;
                cfg.model.kokoro.tokens = tokens;
                cfg.model.kokoro.data_dir = dataDir;
                cfg.model.kokoro.dict_dir = dictDir;
                cfg.model.kokoro.lexicon = lexicon;
                cfg.model.kokoro.lang = empty;
                // every other string pointer stays IntPtr.Zero; the C API treats null as ""
                cfg.rule_fsts = empty;
                cfg.rule_fars = empty;

                _tts = SherpaOnnxNative.SherpaOnnxCreateOfflineTts(ref cfg);
            }
            finally
            {
                Marshal.FreeHGlobal(provider); Marshal.FreeHGlobal(model); Marshal.FreeHGlobal(voices);
                Marshal.FreeHGlobal(tokens); Marshal.FreeHGlobal(dataDir); Marshal.FreeHGlobal(empty);
                Marshal.FreeHGlobal(lexicon); Marshal.FreeHGlobal(dictDir);
            }

            if (_tts != IntPtr.Zero)
            {
                SampleRate = SherpaOnnxNative.SherpaOnnxOfflineTtsSampleRate(_tts);
                NumVoices = SherpaOnnxNative.SherpaOnnxOfflineTtsNumSpeakers(_tts);
            }
        }

        public float[] Synthesize(string text, int voice, float speed)
        {
            if (!IsReady || string.IsNullOrWhiteSpace(text)) return null;
            if (NumVoices > 0) voice = Mathf.Clamp(voice, 0, NumVoices - 1);
            speed = Mathf.Clamp(speed <= 0f ? 1f : speed, 0.5f, 2f);

            lock (s_nativeLock)   // one native call at a time, across every engine instance
            {
                IntPtr utf8 = SherpaOnnxNative.Utf8(text);
                IntPtr audio = IntPtr.Zero;
                try
                {
                    audio = SherpaOnnxNative.SherpaOnnxOfflineTtsGenerate(_tts, utf8, voice, speed);
                    if (audio == IntPtr.Zero) return null;
                    var ga = Marshal.PtrToStructure<SherpaOnnxNative.GeneratedAudio>(audio);
                    if (ga.n <= 0 || ga.samples == IntPtr.Zero) return null;
                    var samples = new float[ga.n];
                    Marshal.Copy(ga.samples, samples, 0, ga.n);
                    if (ga.sample_rate > 0) SampleRate = ga.sample_rate;
                    return samples;
                }
                finally
                {
                    if (audio != IntPtr.Zero) SherpaOnnxNative.SherpaOnnxDestroyOfflineTtsGeneratedAudio(audio);
                    Marshal.FreeHGlobal(utf8);
                }
            }
        }

        public void Dispose()
        {
            lock (s_nativeLock)
            {
                if (_tts != IntPtr.Zero)
                {
                    SherpaOnnxNative.SherpaOnnxDestroyOfflineTts(_tts);
                    _tts = IntPtr.Zero;
                }
            }
        }
    }
}
