// SherpaOnnxNative.cs - P/Invoke binding to sherpa-onnx's C API (sherpa-onnx-c-api.dll, with onnxruntime.dll beside it
// in Assets/Plugins/x86_64). Struct layouts mirror sherpa-onnx/c-api/c-api.h at v1.13.8 exactly; every model family's
// config is present even though only Kokoro is filled, because the native side reads the whole struct by offset.
// Fetch the libraries with: python tools/fetch_tts_runtime.py

using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Homesteader.Radio.Tts
{
    internal static class SherpaOnnxNative
    {
        private const string Lib = "sherpa-onnx-c-api";

        [StructLayout(LayoutKind.Sequential)]
        public struct VitsModelConfig
        {
            public IntPtr model, lexicon, tokens, data_dir;
            public float noise_scale, noise_scale_w, length_scale;
            public IntPtr dict_dir;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct MatchaModelConfig
        {
            public IntPtr acoustic_model, vocoder, lexicon, tokens, data_dir;
            public float noise_scale, length_scale;
            public IntPtr dict_dir;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct KokoroModelConfig
        {
            public IntPtr model, voices, tokens, data_dir;
            public float length_scale;
            public IntPtr dict_dir, lexicon, lang;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct KittenModelConfig
        {
            public IntPtr model, voices, tokens, data_dir;
            public float length_scale;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct ZipvoiceModelConfig
        {
            public IntPtr tokens, encoder, decoder, vocoder, data_dir, lexicon;
            public float feat_scale, t_shift, target_rms, guidance_scale;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct PocketModelConfig
        {
            public IntPtr lm_flow, lm_main, encoder, decoder, text_conditioner, vocab_json, token_scores_json;
            public int voice_embedding_cache_capacity;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SupertonicModelConfig
        {
            public IntPtr duration_predictor, text_encoder, vector_estimator, vocoder, tts_json, unicode_indexer, voice_style;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct OfflineTtsModelConfig
        {
            public VitsModelConfig vits;
            public int num_threads;
            public int debug;
            public IntPtr provider;
            public MatchaModelConfig matcha;
            public KokoroModelConfig kokoro;
            public KittenModelConfig kitten;
            public ZipvoiceModelConfig zipvoice;
            public PocketModelConfig pocket;
            public SupertonicModelConfig supertonic;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct OfflineTtsConfig
        {
            public OfflineTtsModelConfig model;
            public IntPtr rule_fsts;
            public int max_num_sentences;
            public IntPtr rule_fars;
            public float silence_scale;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct GeneratedAudio
        {
            public IntPtr samples;   // const float*
            public int n;
            public int sample_rate;
        }

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern IntPtr SherpaOnnxCreateOfflineTts(ref OfflineTtsConfig config);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern void SherpaOnnxDestroyOfflineTts(IntPtr tts);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern int SherpaOnnxOfflineTtsSampleRate(IntPtr tts);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern int SherpaOnnxOfflineTtsNumSpeakers(IntPtr tts);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern IntPtr SherpaOnnxOfflineTtsGenerate(IntPtr tts, IntPtr utf8Text, int sid, float speed);

        [DllImport(Lib, CallingConvention = CallingConvention.Cdecl)]
        public static extern void SherpaOnnxDestroyOfflineTtsGeneratedAudio(IntPtr audio);

        /// <summary>Allocates a NUL-terminated UTF-8 copy of s (sherpa-onnx reads UTF-8, not the ANSI code page). Free with Marshal.FreeHGlobal.</summary>
        public static IntPtr Utf8(string s)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(s ?? "");
            IntPtr p = Marshal.AllocHGlobal(bytes.Length + 1);
            Marshal.Copy(bytes, 0, p, bytes.Length);
            Marshal.WriteByte(p, bytes.Length, 0);
            return p;
        }
    }
}
