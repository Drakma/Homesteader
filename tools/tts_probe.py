"""Probe the installed Kokoro voice runtime outside Unity (ctypes against sherpa-onnx-c-api.dll).

    python tools/tts_probe.py "Text to speak" --voice 3 --out scratch/probe.wav [--lang en-us] [--no-lexicon] [--debug]

Mirrors the struct layout in Assets/Scripts/Radio/Tts/SherpaOnnxNative.cs (sherpa-onnx v1.13.8), so it also serves
as a layout check: if this script produces good audio and Unity does not, the C# binding is wrong, not the model.
"""
from __future__ import annotations

import argparse
import ctypes as C
import os
import struct
import sys
import time
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(ROOT, "Homesteader", "Assets", "Plugins", "x86_64")
MODEL_ROOT = os.path.join(ROOT, "Homesteader", "Assets", "StreamingAssets", "Tts")
KNOWN = ("kokoro-multi-lang-v1_0", "kokoro-multi-lang-v1_1", "kokoro-en-v0_19", "kokoro-int8-en-v0_19")

cstr = C.c_char_p


class Vits(C.Structure):
    _fields_ = [("model", cstr), ("lexicon", cstr), ("tokens", cstr), ("data_dir", cstr),
                ("noise_scale", C.c_float), ("noise_scale_w", C.c_float), ("length_scale", C.c_float), ("dict_dir", cstr)]


class Matcha(C.Structure):
    _fields_ = [("acoustic_model", cstr), ("vocoder", cstr), ("lexicon", cstr), ("tokens", cstr), ("data_dir", cstr),
                ("noise_scale", C.c_float), ("length_scale", C.c_float), ("dict_dir", cstr)]


class Kokoro(C.Structure):
    _fields_ = [("model", cstr), ("voices", cstr), ("tokens", cstr), ("data_dir", cstr), ("length_scale", C.c_float),
                ("dict_dir", cstr), ("lexicon", cstr), ("lang", cstr)]


class Kitten(C.Structure):
    _fields_ = [("model", cstr), ("voices", cstr), ("tokens", cstr), ("data_dir", cstr), ("length_scale", C.c_float)]


class Zipvoice(C.Structure):
    _fields_ = [("tokens", cstr), ("encoder", cstr), ("decoder", cstr), ("vocoder", cstr), ("data_dir", cstr), ("lexicon", cstr),
                ("feat_scale", C.c_float), ("t_shift", C.c_float), ("target_rms", C.c_float), ("guidance_scale", C.c_float)]


class Pocket(C.Structure):
    _fields_ = [("lm_flow", cstr), ("lm_main", cstr), ("encoder", cstr), ("decoder", cstr), ("text_conditioner", cstr),
                ("vocab_json", cstr), ("token_scores_json", cstr), ("voice_embedding_cache_capacity", C.c_int32)]


class Supertonic(C.Structure):
    _fields_ = [("duration_predictor", cstr), ("text_encoder", cstr), ("vector_estimator", cstr), ("vocoder", cstr),
                ("tts_json", cstr), ("unicode_indexer", cstr), ("voice_style", cstr)]


class ModelConfig(C.Structure):
    _fields_ = [("vits", Vits), ("num_threads", C.c_int32), ("debug", C.c_int32), ("provider", cstr), ("matcha", Matcha),
                ("kokoro", Kokoro), ("kitten", Kitten), ("zipvoice", Zipvoice), ("pocket", Pocket), ("supertonic", Supertonic)]


class TtsConfig(C.Structure):
    _fields_ = [("model", ModelConfig), ("rule_fsts", cstr), ("max_num_sentences", C.c_int32), ("rule_fars", cstr),
                ("silence_scale", C.c_float)]


class GeneratedAudio(C.Structure):
    _fields_ = [("samples", C.POINTER(C.c_float)), ("n", C.c_int32), ("sample_rate", C.c_int32)]


def model_dir() -> str:
    for name in KNOWN:
        d = os.path.join(MODEL_ROOT, name)
        if os.path.exists(os.path.join(d, "voices.bin")):
            return d
    raise SystemExit("no Kokoro model installed under " + MODEL_ROOT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--voice", type=int, default=0)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(ROOT, "scratch", "tts_probe.wav"))
    ap.add_argument("--lang", default="", help="kokoro.lang override, e.g. en-us (empty = model default)")
    ap.add_argument("--no-lexicon", action="store_true")
    ap.add_argument("--no-dict", action="store_true")
    ap.add_argument("--max-sentences", type=int, default=1)
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--unity-paths", action="store_true", help="use forward slashes up to StreamingAssets like Unity does")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()

    os.add_dll_directory(PLUGIN_DIR)
    lib = C.CDLL(os.path.join(PLUGIN_DIR, "sherpa-onnx-c-api.dll"))
    lib.SherpaOnnxCreateOfflineTts.restype = C.c_void_p
    lib.SherpaOnnxCreateOfflineTts.argtypes = [C.POINTER(TtsConfig)]
    lib.SherpaOnnxDestroyOfflineTts.argtypes = [C.c_void_p]
    lib.SherpaOnnxOfflineTtsSampleRate.argtypes = [C.c_void_p]
    lib.SherpaOnnxOfflineTtsNumSpeakers.argtypes = [C.c_void_p]
    lib.SherpaOnnxOfflineTtsGenerate.restype = C.POINTER(GeneratedAudio)
    lib.SherpaOnnxOfflineTtsGenerate.argtypes = [C.c_void_p, cstr, C.c_int32, C.c_float]
    lib.SherpaOnnxDestroyOfflineTtsGeneratedAudio.argtypes = [C.POINTER(GeneratedAudio)]

    md = model_dir()
    if a.unity_paths:
        md = md.replace(os.sep, "/").replace("/Tts/", os.sep + "Tts" + os.sep)
    print("model:", md)
    onnx = os.path.join(md, "model.int8.onnx")
    if not os.path.exists(onnx):
        onnx = os.path.join(md, "model.onnx")
    lex = [] if a.no_lexicon else [os.path.join(md, f) for f in ("lexicon-us-en.txt", "lexicon-zh.txt") if os.path.exists(os.path.join(md, f))]
    dict_dir = "" if a.no_dict or not os.path.isdir(os.path.join(md, "dict")) else os.path.join(md, "dict")
    print("lexicon:", ",".join(lex) or "(none)", "| dict:", dict_dir or "(none)", "| lang:", a.lang or "(model default)")

    enc = lambda s: s.encode("utf-8")
    cfg = TtsConfig()
    cfg.model.num_threads = a.threads
    cfg.model.debug = 1 if a.debug else 0
    cfg.model.provider = enc("cpu")
    cfg.model.kokoro.model = enc(onnx)
    cfg.model.kokoro.voices = enc(os.path.join(md, "voices.bin"))
    cfg.model.kokoro.tokens = enc(os.path.join(md, "tokens.txt"))
    cfg.model.kokoro.data_dir = enc(os.path.join(md, "espeak-ng-data"))
    cfg.model.kokoro.length_scale = 1.0
    cfg.model.kokoro.dict_dir = enc(dict_dir)
    cfg.model.kokoro.lexicon = enc(",".join(lex))
    cfg.model.kokoro.lang = enc(a.lang)
    cfg.rule_fsts = enc("")
    cfg.rule_fars = enc("")
    cfg.max_num_sentences = a.max_sentences
    cfg.silence_scale = 0.2

    t0 = time.time()
    tts = lib.SherpaOnnxCreateOfflineTts(C.byref(cfg))
    if not tts:
        raise SystemExit("SherpaOnnxCreateOfflineTts returned null")
    print(f"loaded in {time.time() - t0:.2f}s; rate={lib.SherpaOnnxOfflineTtsSampleRate(tts)} voices={lib.SherpaOnnxOfflineTtsNumSpeakers(tts)}")

    t0 = time.time()
    audio = lib.SherpaOnnxOfflineTtsGenerate(tts, enc(a.text), a.voice, a.speed)
    if not audio:
        raise SystemExit("generate returned null")
    ga = audio.contents
    n, rate = ga.n, ga.sample_rate
    samples = [ga.samples[i] for i in range(n)]
    lib.SherpaOnnxDestroyOfflineTtsGeneratedAudio(audio)
    lib.SherpaOnnxDestroyOfflineTts(tts)
    print(f"generated {n} samples = {n / rate:.2f}s in {time.time() - t0:.2f}s")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
