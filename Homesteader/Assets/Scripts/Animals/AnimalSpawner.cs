using System.Collections;
using System.IO;
using Homesteader.Animation;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.Animals
{
    /// <summary>
    /// Spawns a rigged animal (a GLB with its clips) and gives it a brain from the mod-loaded AI definitions.
    /// Gameplay code calls Spawn(); the F2 / F3 hotkeys are development helpers.
    /// </summary>
    public sealed class AnimalSpawner : MonoBehaviour
    {
        [Header("Dev spawn (F5) / debug labels (F6)")]
        public string devItemId = "animal_dog_labrador";
        public string devSpecies = "dog";
        [Tooltip("Path under StreamingAssets to the rigged GLB that carries the clips.")]
        public string devModelPath = "Animals/animal_dog_labrador/SKM_Animal_Dog_Labrador_anims.glb";

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || Homesteader.UI.HudBindings.KeyboardCaptured) return;

            if (kb.f5Key.wasPressedThisFrame)
            {
                GameObject player = GameObject.FindWithTag("Player");
                Vector3 at = player != null ? player.transform.position + player.transform.forward * 3f : Vector3.zero;
                Spawn(devItemId, devSpecies, devModelPath, at);
            }
            if (kb.f6Key.wasPressedThisFrame) AnimalBrain.ShowDebug = !AnimalBrain.ShowDebug;
        }

        /// <summary>Creates the animal at a world position. Returns the root object (the model loads asynchronously).</summary>
        public static GameObject Spawn(string itemId, string species, string streamingRelativeModel, Vector3 position)
        {
            AnimalAIDefinition def = AnimalAIRegistry.FindFor(itemId, species);
            if (def == null)
                Debug.LogWarning($"[AnimalSpawner] no animal_ai definition applies to '{itemId}' / species '{species}'. It will stand still.");

            string modelPath = Path.Combine(Application.streamingAssetsPath, streamingRelativeModel);
            if (!File.Exists(modelPath))
            {
                Debug.LogWarning($"[AnimalSpawner] model not found: {modelPath}");
                return null;
            }

            position.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(position);
            var root = new GameObject("Animal_" + itemId);
            root.transform.position = position;
            root.transform.rotation = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);

            var model = new GameObject("Model");
            model.transform.SetParent(root.transform, false);
            var clips = model.AddComponent<GlbClipPlayer>();
            clips.LoadCharacter(modelPath, null, null);

            var host = root.AddComponent<AnimalSpawnHost>();
            host.StartCoroutine(host.Finish(root, model, clips, def, species));
            return root;
        }
    }

    /// <summary>Waits for the GLB to finish loading, sits it on the ground, then starts the brain.</summary>
    public sealed class AnimalSpawnHost : MonoBehaviour
    {
        public IEnumerator Finish(GameObject root, GameObject model, GlbClipPlayer clips, AnimalAIDefinition def, string species)
        {
            float timeout = Time.time + 15f;
            while (!clips.IsReady && clips.LoadError == null && Time.time < timeout) yield return null;
            if (!clips.IsReady) { Debug.LogWarning("[AnimalSpawner] animal failed to load: " + clips.LoadError); yield break; }

            // The model's origin is not at its feet: lift it so the lowest point touches the ground.
            var renderers = model.GetComponentsInChildren<Renderer>();
            if (renderers.Length > 0)
            {
                Bounds b = renderers[0].bounds;
                for (int i = 1; i < renderers.Length; i++) b.Encapsulate(renderers[i].bounds);
                model.transform.localPosition += Vector3.up * (root.transform.position.y - b.min.y);
            }

            if (def != null)
            {
                var brain = root.AddComponent<AnimalBrain>();
                brain.Initialize(def, species, clips);
            }
            Destroy(this);
        }
    }
}
