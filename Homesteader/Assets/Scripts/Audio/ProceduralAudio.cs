using UnityEngine;

namespace Homesteader.Audio
{
    /// <summary>
    /// Generates simple sounds in code: sine-wave UI beeps, filtered-noise wind/rain loops, and footstep
    /// ticks. No audio files, no licensing questions - these are placeholders AudioManager falls back to
    /// whenever a real clip hasn't been assigned yet, so sound design can start today and get replaced
    /// piece by piece as real (e.g. Kenney CC0) clips come in, with no code changes required elsewhere.
    /// </summary>
    public static class ProceduralAudio
    {
        private const int SampleRate = 44100;

        /// <summary>A short sine-wave tone with a fast attack and exponential release, for UI feedback.</summary>
        public static AudioClip GenerateBeep(float frequencyHz, float durationSec)
        {
            int sampleCount = Mathf.Max(1, Mathf.RoundToInt(SampleRate * durationSec));
            var data = new float[sampleCount];
            const float attackSec = 0.006f;
            int attackSamples = Mathf.Min(sampleCount, Mathf.RoundToInt(SampleRate * attackSec));

            for (int i = 0; i < sampleCount; i++)
            {
                float t = (float)i / SampleRate;
                float wave = Mathf.Sin(2f * Mathf.PI * frequencyHz * t);

                float envelope;
                if (i < attackSamples)
                    envelope = (float)i / attackSamples;
                else
                    envelope = Mathf.Exp(-6f * (t - attackSec));

                data[i] = wave * envelope;
            }

            var clip = AudioClip.Create($"Beep_{frequencyHz:F0}Hz", sampleCount, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }

        /// <summary>A seamlessly-looping bed of low-passed white noise - "wind" with a low cutoff and an
        /// optional slow gusting LFO baked in, "rain" with a higher cutoff for a steadier hiss.</summary>
        public static AudioClip GenerateFilteredNoiseLoop(float durationSec, float cutoff, int seed, bool gustLfo)
        {
            int sampleCount = Mathf.RoundToInt(SampleRate * durationSec);
            var data = new float[sampleCount];
            var rng = new System.Random(seed);

            // One-pole low-pass filter over white noise: cutoff in (0,1], smaller = darker/rumblier.
            float prev = 0f;
            for (int i = 0; i < sampleCount; i++)
            {
                float white = (float)(rng.NextDouble() * 2.0 - 1.0);
                prev += cutoff * (white - prev);
                data[i] = prev;
            }

            // Crossfade the tail into the head so the loop point doesn't pop.
            int fadeSamples = Mathf.Min(sampleCount / 4, SampleRate); // up to 1s crossfade
            for (int i = 0; i < fadeSamples; i++)
            {
                float t = (float)i / fadeSamples;
                int tailIndex = sampleCount - fadeSamples + i;
                float blended = Mathf.Lerp(data[tailIndex], data[i], t);
                data[tailIndex] = blended;
            }

            // Normalize to a sane peak level (filtered noise has a fairly low natural amplitude).
            float peak = 0.0001f;
            for (int i = 0; i < sampleCount; i++) peak = Mathf.Max(peak, Mathf.Abs(data[i]));
            float norm = 0.6f / peak;

            if (gustLfo)
            {
                // Slow (~0.05-0.15Hz) amplitude wander so wind reads as gusting instead of a static hiss.
                float lfoFreq = 0.08f;
                float lfoPhase = (float)rng.NextDouble() * Mathf.PI * 2f;
                for (int i = 0; i < sampleCount; i++)
                {
                    float t = (float)i / SampleRate;
                    float lfo = 0.55f + 0.45f * Mathf.Sin(2f * Mathf.PI * lfoFreq * t + lfoPhase);
                    data[i] *= norm * lfo;
                }
            }
            else
            {
                for (int i = 0; i < sampleCount; i++) data[i] *= norm;
            }

            var clip = AudioClip.Create(gustLfo ? "ProceduralWind" : "ProceduralRain", sampleCount, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }

        /// <summary>A short burst of filtered noise with a fast decay, standing in for a footstep thud until
        /// real foley is assigned. Cutoff/duration vary a little by surface so they're not all identical.</summary>
        public static AudioClip GenerateFootstepTick(AudioManager.FootstepSurface surface)
        {
            float durationSec = surface == AudioManager.FootstepSurface.Snow ? 0.10f : 0.07f;
            float cutoff = surface switch
            {
                AudioManager.FootstepSurface.Gravel => 0.5f,
                AudioManager.FootstepSurface.Wood => 0.3f,
                AudioManager.FootstepSurface.Snow => 0.15f,
                AudioManager.FootstepSurface.Dirt => 0.25f,
                _ => 0.2f, // grass
            };

            int sampleCount = Mathf.RoundToInt(SampleRate * durationSec);
            var data = new float[sampleCount];
            var rng = new System.Random();
            float prev = 0f;
            for (int i = 0; i < sampleCount; i++)
            {
                float white = (float)(rng.NextDouble() * 2.0 - 1.0);
                prev += cutoff * (white - prev);
                float t = (float)i / sampleCount;
                float decay = Mathf.Exp(-9f * t);
                data[i] = prev * decay;
            }

            float peak = 0.0001f;
            for (int i = 0; i < sampleCount; i++) peak = Mathf.Max(peak, Mathf.Abs(data[i]));
            float norm = 0.8f / peak;
            for (int i = 0; i < sampleCount; i++) data[i] *= norm;

            var clip = AudioClip.Create("ProceduralFootstep_" + surface, sampleCount, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
