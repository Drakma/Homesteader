using UnityEngine;
using UnityEngine.UIElements;
using Homesteader;

namespace Homesteader.UI
{
    /// <summary>
    /// Entry point: place a single empty ``HudRoot`` GameObject in
    /// <c>SampleScene</c> with this component on it. The component
    /// attaches a <c>UIDocument</c>, locates or creates a
    /// <c>PanelSettings</c>, and attaches <c>HudUIBuilder</c>. Press
    /// play -> the HUD appears.
    ///
    /// This replaces the need to wire components manually in the
    /// inspector.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public sealed class HudSceneBootstrap : MonoBehaviour
    {
        [Tooltip("Optional override path to a PanelSettings asset. " +
                 "If empty, the script copies any HUDTree PanelSettings " +
                 "from Resources.")]
        [SerializeField] private PanelSettings _panelSettingsOverride;

        [Tooltip("Enable the kit-sourced chrome overlay (vitals, " +
                 "resources, decor) sourced from assets/hud_kit/. " +
                 "Disabled by default so we don't paint over an existing " +
                 "designed HUD until you opt in.")]
        [SerializeField] private bool _enableKitOverlay = false;

        private void Awake()
        {
            EnsureDocument();
            EnsureBuilder();
            EnsureDayNightCycle();
            EnsureWeatherEffects();
            EnsurePlayer();
        }

        private void EnsureDocument()
        {
            var doc = GetComponent<UIDocument>();
            if (doc == null)
            {
                doc = gameObject.AddComponent<UIDocument>();
            }

            if (_panelSettingsOverride != null)
            {
                doc.panelSettings = _panelSettingsOverride;
                return;
            }

            // If UIDocument already has a valid PanelSettings assigned, keep it.
            if (doc.panelSettings != null)
            {
                return;
            }

            // Look for user PanelSettings in Resources / project.
            var allPanels = Resources.FindObjectsOfTypeAll<PanelSettings>();
            foreach (var p in allPanels)
            {
                if (p != null && !p.name.Contains("RuntimeDebug"))
                {
                    doc.panelSettings = p;
                    return;
                }
            }

            // No PanelSettings available. Construct one in memory so
            // a Play session without manual wiring still shows the HUD.
            doc.panelSettings = ScriptableObject.CreateInstance<PanelSettings>();
            doc.panelSettings.name = "RuntimePanelSettings";
            doc.panelSettings.scaleMode = PanelScaleMode.ConstantPixelSize;
            doc.panelSettings.themeStyleSheet = ScriptableObject.CreateInstance<UnityEngine.UIElements.ThemeStyleSheet>();
        }

        private void EnsureBuilder()
        {
            var existing = GetComponent<HudUIBuilder>();
            if (existing == null)
            {
                existing = gameObject.AddComponent<HudUIBuilder>();
            }
#if UNITY_EDITOR
            if (_enableKitOverlay)
            {
                ApplyKitOverlayFlag(existing);
            }
#endif
            EnsureBindings();
        }

        private void EnsureBindings()
        {
            if (GetComponent<HudBindings>() == null)
            {
                gameObject.AddComponent<HudBindings>();
            }
        }

        private void EnsureDayNightCycle()
        {
            if (FindAnyObjectByType<DayNightCycle>() == null)
            {
                var dirLight = GameObject.Find("Directional Light");
                if (dirLight != null)
                {
                    dirLight.AddComponent<DayNightCycle>();
                }
                else
                {
                    gameObject.AddComponent<DayNightCycle>();
                }
            }
        }

        private void EnsureWeatherEffects()
        {
            if (FindAnyObjectByType<WeatherEffectsManager>() == null)
            {
                var go = new GameObject("WeatherEffects");
                go.AddComponent<WeatherEffectsManager>();
                DontDestroyOnLoad(go);
            }
        }

        private void EnsurePlayer()
        {
            var existingPed = FindAnyObjectByType<PedController>();
            GameObject playerObj = null;

            if (existingPed != null)
            {
                playerObj = existingPed.gameObject;
            }
            else
            {
                var existingPlayer = GameObject.FindWithTag("Player");
                if (existingPlayer != null)
                {
                    playerObj = existingPlayer;
                }
                else
                {
                    Vector3 spawnPos = Vector3.zero;
                    Quaternion spawnRot = Quaternion.Euler(0f, 180f, 0f);
                    var sp = GameObject.Find("SpawnPoint");
                    if (sp != null)
                    {
                        spawnPos = sp.transform.position;
                        spawnRot = sp.transform.rotation * Quaternion.Euler(0f, 180f, 0f);
                    }

                    var modelPrefab = Resources.Load<GameObject>("Ped/SKM_Peds_Male_Farmer_Rigged");
                    if (modelPrefab != null)
                    {
                        playerObj = Instantiate(modelPrefab, spawnPos, spawnRot);
                        playerObj.name = "Player";
                    }
                    else
                    {
                        playerObj = new GameObject("Player");
                        playerObj.transform.position = spawnPos;
                        playerObj.transform.rotation = spawnRot;
                    }
                }
            }

            if (playerObj != null)
            {
                if (!playerObj.CompareTag("Player"))
                {
                    try { playerObj.tag = "Player"; } catch { }
                }

                var cc = playerObj.GetComponent<CharacterController>();
                if (cc == null)
                {
                    cc = playerObj.AddComponent<CharacterController>();
                    cc.height = 1.8f;
                    cc.center = new Vector3(0f, 0.9f, 0f);
                    cc.radius = 0.35f;
                    cc.stepOffset = 0.3f;
                    cc.slopeLimit = 45f;
                }

                var ped = playerObj.GetComponent<PedController>();
                if (ped == null)
                {
                    ped = playerObj.AddComponent<PedController>();
                }

                var anim = playerObj.GetComponentInChildren<Animator>();
                if (anim == null)
                {
                    anim = playerObj.AddComponent<Animator>();
                    Debug.Log("[HudSceneBootstrap] Added Animator to playerObj");
                }
                anim.applyRootMotion = false;
                anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;

                var animCtrl = Resources.Load<RuntimeAnimatorController>("Ped/PedAnimatorController");
                if (animCtrl != null)
                {
                    if (animCtrl.animationClips != null)
                    {
                        foreach (var clip in animCtrl.animationClips)
                        {
                            clip.wrapMode = WrapMode.Loop;
                        }
                    }
                    anim.runtimeAnimatorController = animCtrl;
                    Debug.Log($"[HudSceneBootstrap] Assigned runtimeAnimatorController: {animCtrl.name}");
                }
                else
                {
                    Debug.LogError("[HudSceneBootstrap] Failed to load Ped/PedAnimatorController from Resources!");
                }

                var isoCam = FindAnyObjectByType<IsometricLockedCamera>();
                if (isoCam != null && isoCam.target == null)
                {
                    isoCam.target = playerObj.transform;
                }
            }
        }

#if UNITY_EDITOR
        private void ApplyKitOverlayFlag(HudUIBuilder target)
        {
            var so = new UnityEditor.SerializedObject(target);
            var prop = so.FindProperty("_enableKitOverlay");
            if (prop != null)
            {
                prop.boolValue = true;
                so.ApplyModifiedProperties();
            }
        }
#endif
    }
}
