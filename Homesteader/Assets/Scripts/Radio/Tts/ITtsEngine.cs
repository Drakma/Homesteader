// ITtsEngine.cs - the text-to-speech engine behind the radio. One implementation today: KokoroTtsEngine (local,
// offline, sherpa-onnx). Synthesize is called from RadioPlayer's worker thread, never from the main thread.

using System;

namespace Homesteader.Radio.Tts
{
    public interface ITtsEngine : IDisposable
    {
        bool IsReady { get; }
        int SampleRate { get; }
        int NumVoices { get; }
        string Name { get; }

        /// <summary>Mono samples in [-1, 1] at SampleRate, or null when synthesis failed. Thread: worker only.</summary>
        float[] Synthesize(string text, int voice, float speed);
    }
}
