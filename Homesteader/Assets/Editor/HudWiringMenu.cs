#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UIElements;

namespace Homesteader.UI.EditorTools
{
    /// <summary>
    /// Editor menu items that insert the HUD into the active scene and
    /// wire all the components so the runtime HUD shows on Play.
    ///
    /// Run from Unity's menu bar:
    ///   Tools > HUD > Install Into Active Scene
    ///
    /// Or wait for the editor to finish domain reload after this script
    /// is imported, and the HUD will be injected automatically.
    /// </summary>
    public static class HudWiringMenu
    {
        [InitializeOnLoadMethod]
        private static void AutoInstallAfterReload()
        {
            EditorApplication.delayCall += () =>
            {
                // Don't run during play mode — MarkSceneDirty throws otherwise.
                if (EditorApplication.isPlaying) return;
                Install();
            };
        }

        [MenuItem("Tools/HUD/Install Into Active Scene")]
        public static void Install()
        {
            var scene = SceneManager.GetActiveScene();
            if (!scene.IsValid())
            {
                Debug.LogError("[HudInstall] No active scene.");
                return;
            }
            EnsurePanelSettingsAsset();
            var hudAsset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(
                "Assets/Resources/HUDTree/HudUI.uxml");

            // Avoid stacking: if a HudRoot already exists, top up any
            // missing components (UIDocument, HudUIBuilder, HudBindings)
            // and select it. Useful after the bindings/UI C# files are
            // updated and the scene's prefab snapshot is stale.
            var existing = GameObject.Find("HudRoot");
            if (existing != null)
            {
                if (existing.GetComponent<UIDocument>() == null)
                {
                    existing.AddComponent<UIDocument>();
                }
                if (existing.GetComponent<HudUIBuilder>() == null)
                {
                    existing.AddComponent<HudUIBuilder>();
                }
                if (existing.GetComponent<HudBindings>() == null)
                {
                    existing.AddComponent<HudBindings>();
                }
                WireUI(existing, hudAsset);
                EditorSceneManager.MarkSceneDirty(scene);
                Selection.activeGameObject = existing;
                Debug.Log("[HudInstall] HudRoot already present, " +
                          "topped up missing components.");
                return;
            }

            var go = new GameObject("HudRoot");
            // Marker component Find() will reuse this.
            go.AddComponent<HudSceneBootstrap>();

            // Persist so the user doesn't need to re-add manually.
            Undo.RegisterCreatedObjectUndo(go, "Install HUD");
            EditorSceneManager.MarkSceneDirty(scene);
            Selection.activeGameObject = go;

            WireUI(go, hudAsset);

            Debug.Log("[HudInstall] HudRoot added with UIDocument + " +
                      "HudUIBuilder + HudBindings + HudSceneBootstrap. " +
                      "PanelSettings assigned.");
        }

        private static void WireUI(GameObject go, VisualTreeAsset hudAsset)
        {
            var panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>(
                "Assets/UI/PanelSettings.asset");
            var doc = go.GetComponent<UIDocument>();
            if (doc != null)
            {
                if (panelSettings != null) doc.panelSettings = panelSettings;
                if (hudAsset != null) doc.visualTreeAsset = hudAsset;
            }
        }

        public static void EnsurePanelSettingsAsset()
        {
            // Create at Assets/UI/PanelSettings.asset if missing.
            const string path = "Assets/UI/PanelSettings.asset";
            var existing = AssetDatabase.LoadAssetAtPath<PanelSettings>(path);
            if (existing != null)
            {
                return;
            }
            var asset = ScriptableObject.CreateInstance<PanelSettings>();
            asset.name = "HudPanelSettings";
            asset.scaleMode = PanelScaleMode.ConstantPixelSize;
            asset.themeStyleSheet = AssetDatabase.LoadAssetAtPath<UnityEngine.UIElements.ThemeStyleSheet>(
                "Packages/com.unity.ui/PackageResources/StyleSheets/Generated/DefaultRuntimeTheme.tss")
                ?? ScriptableObject.CreateInstance<UnityEngine.UIElements.ThemeStyleSheet>();
            AssetDatabase.CreateAsset(asset, path);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"[HudInstall] Created {path}");
        }
    }
}
#endif
