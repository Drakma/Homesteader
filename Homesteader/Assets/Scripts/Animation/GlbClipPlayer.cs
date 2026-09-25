using System;
using System.Collections.Generic;
using System.IO;
using GLTFast;
using UnityEngine;

namespace Homesteader.Animation
{
    /// <summary>
    /// No-bake animation for rigged .glb characters.
    ///
    /// Why this exists: a .glb is imported by glTFast, not by Unity's ModelImporter, so the
    /// clips it produces are "legacy" AnimationClips. Mecanim's AnimatorController REFUSES
    /// legacy clips ("must reimport as a Generic or Humanoid animation clip"), and there is no
    /// runtime API to give a clip an animation type. That is an engine boundary, not a policy
    /// choice: Mecanim animation requires a build-time bake step.
    ///
    /// The legacy Animation component has no such restriction. It plays AnimationClips whose
    /// binding paths match its own transform hierarchy, which is exactly what glTFast produces
    /// (verified: 267 bindings on the old farmer's Walk clip, paths like
    /// "Skinned Mesh 0/root/pelvis/spine_01", matching the instantiated hierarchy verbatim).
    ///
    /// So this component gives a mod-shipped GLB clip playback with NO bake step, NO prefab,
    /// and NO Unity Editor involvement. A modder drops in a .glb carrying Idle/Walk/Run plus
    /// any action clips they like, and everything in the file is playable by name.
    ///
    /// The trade-off, stated honestly: no Humanoid retargeting. A clip only fits the skeleton
    /// it was authored for, which is fine for mods because a mod ships its own model and its
    /// own clips together.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class GlbClipPlayer : MonoBehaviour
    {
        [Header("Clip names the game looks for")]
        [Tooltip("Played when the character is at rest.")]
        public string idleClip = "Idle";

        [Tooltip("Played while walking.")]
        public string walkClip = "Walk";

        [Tooltip("Played while running.")]
        public string runClip = "Run";

        [Tooltip("Preferred names for the carry variant, tried in order.")]
        public string[] carryClipCandidates = { "Walk_Carry", "Carry", "WalkCarry" };

        [Header("Blending")]
        [Tooltip("Seconds to crossfade between locomotion clips.")]
        public float crossFadeSeconds = 0.2f;

        [Tooltip("Speed value (0-1) at or above which the run clip is used.")]
        public float runThreshold = 0.75f;

        [Header("Status (read-only)")]
        [SerializeField] private string[] availableClips = Array.Empty<string>();
        [SerializeField] private string currentClip = "<none>";
        [SerializeField] private bool isReady;
        [SerializeField] private string loadError;

        /// <summary>All clips found in the loaded model, by name.</summary>
        private readonly Dictionary<string, AnimationClip> clips =
            new Dictionary<string, AnimationClip>(StringComparer.OrdinalIgnoreCase);

        // Fully qualified as UnityEngine.Animation: this file lives in namespace
        // Homesteader.Animation, so a bare `Animation` resolves to the NAMESPACE,
        // not the component (error CS0118).
        private UnityEngine.Animation legacyAnimation;
        private string loadPath;

        /// <summary>True once clips are registered and playback is possible.</summary>
        public bool IsReady => isReady;

        /// <summary>Null unless the load failed; carries the reason.</summary>
        public string LoadError => loadError;

        /// <summary>Clip names present in the loaded model.</summary>
        public IReadOnlyList<string> AvailableClips => availableClips;

        /// <summary>Name of the clip currently playing.</summary>
        public string CurrentClip => currentClip;

        /// <summary>Raised once clips are registered (successfully or not).</summary>
        public event Action Ready;

        /// <summary>
        /// Loads a rigged .glb from disk and registers every clip inside it.
        /// The file is read at runtime from the mod folder: no prefab, no import step.
        /// </summary>
        public async void LoadFrom(string glbPath)
        {
            if (string.IsNullOrWhiteSpace(glbPath))
            {
                Fail("no path given");
                return;
            }
            if (!File.Exists(glbPath))
            {
                Fail("file not found: " + glbPath);
                return;
            }

            loadPath = glbPath;
            var gltf = new GltfImport();
            try
            {
                if (!await gltf.Load(File.ReadAllBytes(glbPath), new Uri(glbPath)))
                {
                    Fail("glTFast could not parse: " + glbPath);
                    return;
                }
                if (!await gltf.InstantiateMainSceneAsync(transform))
                {
                    Fail("glTFast could not instantiate: " + glbPath);
                    return;
                }
            }
            catch (Exception e)
            {
                Fail(e.Message);
                return;
            }

            // Declared above the try so it is still in scope here: the clips are read
            // from the importer after the scene has been instantiated.
            RegisterClipsFromImport(gltf);
        }

        /// <summary>
        /// Loads a rigged character .glb and registers its clips, plus the clips found in
        /// extra .glb files that share the same skeleton (e.g. separate walk/run exports).
        /// renames maps a substring of a source clip name to the name gameplay code uses
        /// (e.g. "walking" -> "Walk"), so Meshy/Mesh2Motion clip names need no editing.
        /// </summary>
        public async void LoadCharacter(string modelPath, string[] extraClipFiles,
                                        IReadOnlyDictionary<string, string> renames)
        {
            if (string.IsNullOrWhiteSpace(modelPath) || !File.Exists(modelPath))
            {
                Fail("file not found: " + modelPath);
                return;
            }

            loadPath = modelPath;
            var all = new List<AnimationClip>();
            try
            {
                var gltf = new GltfImport();
                if (!await gltf.Load(File.ReadAllBytes(modelPath), new Uri(modelPath)) ||
                    !await gltf.InstantiateMainSceneAsync(transform))
                {
                    Fail("glTFast could not load: " + modelPath);
                    return;
                }
                var own = gltf.GetAnimationClips();
                if (own != null) all.AddRange(own);

                if (extraClipFiles != null)
                {
                    foreach (string extra in extraClipFiles)
                    {
                        if (!File.Exists(extra)) continue;
                        var g = new GltfImport();
                        if (!await g.Load(File.ReadAllBytes(extra), new Uri(extra))) continue;
                        var more = g.GetAnimationClips();
                        if (more != null) all.AddRange(more);
                    }
                }
            }
            catch (Exception e)
            {
                Fail(e.Message);
                return;
            }

            if (renames != null)
            {
                foreach (AnimationClip clip in all)
                {
                    foreach (KeyValuePair<string, string> kv in renames)
                    {
                        if (clip.name.IndexOf(kv.Key, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            clip.name = kv.Value;
                            break;
                        }
                    }
                }
            }
            RegisterClips(all);
        }

        /// <summary>
        /// Registers AnimationClips that are already in memory (e.g. the ones Unity surfaces
        /// from a .glb asset in Resources). Used when the model came from Resources rather
        /// than a file on disk.
        /// </summary>
        public void RegisterClips(IEnumerable<AnimationClip> source)
        {
            clips.Clear();
            if (source != null)
            {
                foreach (AnimationClip clip in source)
                {
                    if (clip == null || string.IsNullOrEmpty(clip.name)) continue;
                    clip.legacy = true;               // required by the legacy Animation component
                    clip.wrapMode = WrapMode.Loop;
                    clips[clip.name] = clip;
                }
            }
            FinishSetup();
        }

        /// <summary>
        /// Registers the clips glTFast produced for this model. Called after a successful
        /// load; the clips' binding paths match the instantiated hierarchy, which is what
        /// the legacy Animation component requires.
        /// </summary>
        private void RegisterClipsFromImport(GltfImport gltf)
        {
            RegisterClips(gltf.GetAnimationClips());
        }

        private void FinishSetup()
        {
            availableClips = new string[clips.Count];
            clips.Keys.CopyTo(availableClips, 0);

            if (clips.Count == 0)
            {
                Fail("model contains no animation clips");
                return;
            }

            legacyAnimation = GetComponent<UnityEngine.Animation>();
            if (legacyAnimation == null)
                legacyAnimation = gameObject.AddComponent<UnityEngine.Animation>();

            foreach (KeyValuePair<string, AnimationClip> kv in clips)
            {
                legacyAnimation.AddClip(kv.Value, kv.Key);
            }
            legacyAnimation.playAutomatically = false;
            legacyAnimation.cullingType = UnityEngine.AnimationCullingType.AlwaysAnimate;

            isReady = true;
            loadError = null;
            PlayIdle();
            Ready?.Invoke();
        }

        private void Fail(string reason)
        {
            loadError = reason;
            isReady = false;
            Debug.LogWarning($"[GlbClipPlayer] {reason}" + (string.IsNullOrEmpty(loadPath)
                ? "" : $" (path: {loadPath})"));
            Ready?.Invoke();
        }

        /// <summary>
        /// Drives locomotion from a 0-1 speed value, matching the convention PedController
        /// already uses for its Animator path. carrying selects the carry clip when present.
        /// </summary>
        public void SetLocomotion(float speed01, bool carrying = false)
        {
            if (!isReady) return;

            string desired;
            if (speed01 <= 0.01f)
            {
                desired = FirstAvailable(idleClip, walkClip);
            }
            else if (speed01 >= runThreshold)
            {
                desired = FirstAvailable(runClip, walkClip);
            }
            else if (carrying)
            {
                desired = FirstAvailable(carryClipCandidates) ?? FirstAvailable(walkClip, idleClip);
            }
            else
            {
                desired = FirstAvailable(walkClip, runClip);
            }
            Play(desired);
        }

        /// <summary>
        /// Plays a named clip once or looping. This is the hook gameplay code uses for
        /// actions: ped.PlayAction("Chop"), PlayAction("Hoe"), and so on. Any clip a mod
        /// shipped in its .glb is addressable by name, so authors are not limited to
        /// walk/run.
        /// </summary>
        /// <returns>True if the clip existed and started playing.</returns>
        public bool PlayAction(string clipName, bool loop = false)
        {
            if (!isReady || string.IsNullOrEmpty(clipName)) return false;
            if (!clips.TryGetValue(clipName, out AnimationClip clip)) return false;

            clip.wrapMode = loop ? WrapMode.Loop : WrapMode.Once;
            if (!loop && legacyAnimation.GetClip(clipName) == null)
                legacyAnimation.AddClip(clip, clipName);

            Play(clipName);
            return true;
        }

        /// <summary>Crossfades to a clip by name, if it exists.</summary>
        public bool Play(string clipName)
        {
            if (!isReady || string.IsNullOrEmpty(clipName)) return false;
            if (legacyAnimation == null || legacyAnimation.GetClip(clipName) == null) return false;
            if (currentClip == clipName && legacyAnimation.IsPlaying(clipName)) return true;

            legacyAnimation.CrossFade(clipName, crossFadeSeconds, UnityEngine.PlayMode.StopSameLayer);
            currentClip = clipName;
            return true;
        }

        /// <summary>True if the loaded model carries a clip by this name.</summary>
        public bool HasClip(string clipName) =>
            !string.IsNullOrEmpty(clipName) && clips.ContainsKey(clipName);

        /// <summary>Returns the first clip name that exists, or null.</summary>
        public string FirstAvailable(params string[] candidates)
        {
            if (candidates == null) return null;
            foreach (string c in candidates)
                if (HasClip(c)) return c;
            return null;
        }

        private void PlayIdle()
        {
            string idle = FirstAvailable(idleClip, walkClip, runClip);
            if (idle != null) Play(idle);
        }
    }
}