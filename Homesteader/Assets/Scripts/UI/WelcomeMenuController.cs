using System.Collections;
using System.IO;
using Homesteader.Generation;
using Homesteader.Save;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// The Welcome / Main Menu. Shows a full-screen overlay on game start with
    /// New Game, Continue, Save, Load, Settings, and Exit buttons. Uses the
    /// same dark-slate + copper palette and HomesteaderHUD font as the in-game
    /// HUD so it looks like it belongs.
    ///
    /// Flow:
    ///   - On start the menu is shown and the simulation is paused.
    ///   - "New Game" deletes the autosave, picks a new random world seed, and
    ///     reloads the active scene so the terrain regenerates from scratch.
    ///   - "Continue" dismisses the menu and lets GameSaveManager auto-load
    ///     the last save (the default flow).
    ///   - "Save" writes the current game to disk via GameSaveManager.SaveNow().
    ///   - "Load" reads the save from disk and applies it via GameSaveManager.
    ///   - "Settings" opens a sub-panel with volume / fullscreen / vsync.
    ///   - "Exit" quits the application (or stops play in the editor).
    ///
    /// Bootstraps itself on scene load, same pattern as WailaPanel / MiniMap.
    /// </summary>
    public sealed class WelcomeMenuController : MonoBehaviour
    {
        private VisualElement _root;
        private VisualElement _menuRoot;
        private TemplateContainer _tree;
        private VisualElement _wallpaper;
        private Texture2D _bgTexture;
        private Label _statusLabel;

        // Progress bar elements (inside the card, below Exit)
        private VisualElement _loadingSection;
        private Label _loadingPhase;
        private VisualElement _loadingBarFill;
        private Label _loadingPct;

        private Button _newGameBtn;
        private Button _continueBtn;
        private Button _saveBtn;
        private Button _loadBtn;
        private Button _settingsBtn;
        private Button _exitBtn;

        // Settings dialog elements
        private VisualElement _settingsDialog;
        private IntegerField _zoomMaxField;
        private Toggle _zoomLockToggle;
        private Button _settingsCloseBtn;

        private bool _isVisible;
        private bool _isNewGamePending;  // true after New Game is clicked, before scene reload
        private bool _isLoading;         // true while loading modal is shown; blocks input
    public static bool IsLoading => _isLoadingStatic;
    private static bool _isLoadingStatic;
        private bool _skipShowOnLoad;     // true after Continue/Load, skip menu on scene reload

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<WelcomeMenuController>() != null) return;
            var go = new GameObject("WelcomeMenu");
            DontDestroyOnLoad(go);
            go.AddComponent<WelcomeMenuController>();
        }

        private void Start()
        {
            // Wait one frame for the HUD UIDocument to exist, then attach.
            StartCoroutine(InitWhenReady());
        }

        private IEnumerator InitWhenReady()
        {
            float timeout = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < timeout)
            {
                var doc = FindAnyObjectByType<UIDocument>();
                if (doc != null && doc.rootVisualElement != null)
                {
                    // Wait for the HUD tree to be mounted (HudUIBuilder runs at -90).
                    var screenRoot = doc.rootVisualElement.Q<VisualElement>(className: "screen-root");
                    if (screenRoot != null || doc.rootVisualElement.childCount > 0)
                    {
                        break;
                    }
                }
                yield return null;
            }

            Build();
            Show();
        }

        private IEnumerator InitWhenReadyHidden()
        {
            float timeout = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < timeout)
            {
                var doc = FindAnyObjectByType<UIDocument>();
                if (doc != null && doc.rootVisualElement != null)
                {
                    var screenRoot = doc.rootVisualElement.Q<VisualElement>(className: "screen-root");
                    if (screenRoot != null || doc.rootVisualElement.childCount > 0)
                    {
                        break;
                    }
                }
                yield return null;
            }

            Build();
            _isLoading = true;
            _isLoadingStatic = true;
            Hide(); // LoadingModal is a sibling, so Hide() won't hide it.
            // Show the wallpaper behind the loading modal (Build() creates it hidden).
            if (_wallpaper != null)
            {
                _wallpaper.RemoveFromClassList("welcome--hidden");
                _wallpaper.style.display = DisplayStyle.Flex;
                _wallpaper.style.opacity = 1f;
            }
            ShowLoading();
            UpdateLoadingProgress(0f, "Loading world...");

            // Wait for terrain generator to exist and finish generating.
            timeout = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < timeout)
            {
                var gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                if (gen != null && !gen.IsGenerating) break;
                yield return null;
            }

            // Wait for grass to finish propagating (grass = 85-100% of bar).
            UpdateLoadingProgress(0.85f, "Growing grass...");
            yield return StartCoroutine(WaitForGrassWithProgress(0.85f, 1f));

            HideLoading();
            _isLoading = false;
            _isLoadingStatic = false;
            yield return StartCoroutine(FadeInGame());
            ResumeGame();
        }

        private void Build()
        {
            var doc = FindAnyObjectByType<UIDocument>();
            if (doc == null || doc.rootVisualElement == null)
            {
                Debug.LogError("[WelcomeMenu] No UIDocument found in scene.");
                return;
            }

            _root = doc.rootVisualElement;

            var uxml = Resources.Load<VisualTreeAsset>("HUDTree/WelcomeMenu");
            if (uxml == null)
            {
                Debug.LogError("[WelcomeMenu] Could not load HUDTree/WelcomeMenu.uxml from Resources.");
                return;
            }

            var tree = uxml.CloneTree();
            tree.style.position = Position.Absolute;
            tree.style.left = 0;
            tree.style.top = 0;
            tree.style.right = 0;
            tree.style.bottom = 0;
            tree.style.width = new StyleLength(Length.Percent(100));
            tree.style.height = new StyleLength(Length.Percent(100));

            // Create a dedicated wallpaper element that sits between the HUD (already
            // in _root) and the welcome card tree. Z-order in UIToolkit is child order:
            // HUD children (added first) → wallpaper → welcome card tree (added last, on top).
            _wallpaper = new VisualElement { name = "WelcomeWallpaper" };
            _wallpaper.style.position = Position.Absolute;
            _wallpaper.style.left = 0;
            _wallpaper.style.top = 0;
            _wallpaper.style.right = 0;
            _wallpaper.style.bottom = 0;
            _wallpaper.AddToClassList("welcome--hidden");
            _wallpaper.style.display = DisplayStyle.None;

            var bg = Resources.Load<Texture2D>("HUDTree/WelcomeBackground");
            if (bg != null)
            {
                _bgTexture = bg;
                _wallpaper.style.backgroundImage = new StyleBackground(bg);
                // Cover: fill the whole element, preserving aspect ratio (crops overflow
                // rather than stretching). Contain/ScaleToFit would letterbox instead.
                _wallpaper.style.backgroundSize = new StyleBackgroundSize(
                    new BackgroundSize(BackgroundSizeType.Cover));
                _wallpaper.style.backgroundRepeat = new StyleBackgroundRepeat(
                    new BackgroundRepeat(Repeat.NoRepeat, Repeat.NoRepeat));
            }

            _root.Add(_wallpaper);
            _root.Add(tree);
            _tree = tree;

            // Also load the USS as a sibling sheet (in case it wasn't picked up via the UXML <Style> tag).
            var uss = Resources.Load<StyleSheet>("HUDTree/WelcomeMenu");
            if (uss != null && !_root.styleSheets.Contains(uss))
            {
                _root.styleSheets.Add(uss);
            }

            // Resolve elements
            _menuRoot = _root.Q<VisualElement>("WelcomeMenuRoot");
            _statusLabel = _root.Q<Label>("WelcomeStatus");

            // Loading modal (separate from welcome card)
            _loadingSection = _root.Q<VisualElement>("LoadingModal");
            _loadingPhase = _root.Q<Label>("LoadingPhase");
            _loadingBarFill = _root.Q<VisualElement>("LoadingBarFill");
            _loadingPct = _root.Q<Label>("LoadingPct");

            _newGameBtn = _root.Q<Button>("NewGameBtn");
            _continueBtn = _root.Q<Button>("ContinueBtn");
            _saveBtn = _root.Q<Button>("SaveBtn");
            _loadBtn = _root.Q<Button>("LoadBtn");
            _settingsBtn = _root.Q<Button>("SettingsBtn");
            _exitBtn = _root.Q<Button>("ExitBtn");

            // Settings dialog
            _settingsDialog = _root.Q<VisualElement>("SettingsDialog");
            _zoomMaxField = _root.Q<IntegerField>("ZoomMaxLevel");
            _zoomLockToggle = _root.Q<Toggle>("ZoomLockToggle");
            _settingsCloseBtn = _root.Q<Button>("SettingsCloseBtn");

            // Wire buttons
            _newGameBtn.clicked += OnNewGame;
            _continueBtn.clicked += OnContinue;
            _saveBtn.clicked += OnSave;
            _loadBtn.clicked += OnLoad;
            _settingsBtn.clicked += OnSettings;
            _exitBtn.clicked += OnExit;
            _settingsCloseBtn.clicked += OnSettingsClose;

            // Update the Continue button state
            UpdateContinueButton();
        }

        private void UpdateContinueButton()
        {
            if (_continueBtn == null) return;
            bool hasSave = GameSave.Exists;
            _continueBtn.SetEnabled(hasSave);
            _continueBtn.text = hasSave ? "Continue" : "Continue (No Save)";
        }

        // ------------------------------------------------------------------ show / hide

        public void Show()
        {
            Show(withBackground: true);
        }

        public void Show(bool withBackground)
        {
            if (_menuRoot == null) return;
            _menuRoot.RemoveFromClassList("welcome--hidden");
            _menuRoot.style.display = DisplayStyle.Flex;
            // Restore the TemplateContainer so the menu is interactive.
            if (_tree != null)
            {
                _tree.style.display = DisplayStyle.Flex;
                _tree.pickingMode = PickingMode.Position;
            }
            // Toggle the wallpaper element (sits between HUD and welcome card)
            if (_wallpaper != null)
            {
                if (withBackground)
                {
                    _wallpaper.RemoveFromClassList("welcome--hidden");
                    _wallpaper.style.display = DisplayStyle.Flex;
                }
                else
                {
                    _wallpaper.AddToClassList("welcome--hidden");
                    _wallpaper.style.display = DisplayStyle.None;
                }
            }
            _isVisible = true;
            PauseGame();
            UpdateContinueButton();
            SetStatus("");
        }

        public void Hide()
        {
            if (_menuRoot == null) return;
            _menuRoot.AddToClassList("welcome--hidden");
            _menuRoot.style.display = DisplayStyle.None;
            // Hide the wallpaper too so it doesn't linger — but keep it
            // visible during loading so it sits behind the loading modal.
            if (_wallpaper != null && !_isLoading)
            {
                _wallpaper.AddToClassList("welcome--hidden");
                _wallpaper.style.display = DisplayStyle.None;
            }
            // Don't hide the TemplateContainer itself — LoadingModal is a
            // sibling of WelcomeMenuRoot inside the same tree, and hiding the
            // tree would hide the loading modal too. Instead, make the tree
            // non-interactive so it doesn't swallow pointer/wheel events.
            if (_tree != null)
            {
                _tree.pickingMode = PickingMode.Ignore;
            }
            _isVisible = false;
            ResumeGame();
        }

        public bool IsVisible => _isVisible;

        // ------------------------------------------------------------------ progress bar

        private void ShowLoading()
        {
            if (_loadingSection != null)
                _loadingSection.RemoveFromClassList("loading--hidden");
        }

        private void HideLoading()
        {
            if (_loadingSection != null)
                _loadingSection.AddToClassList("loading--hidden");
        }

        private void UpdateLoadingProgress(float progress, string phase)
        {
            if (_loadingBarFill != null)
                _loadingBarFill.style.width = new StyleLength(new Length(progress * 100f, LengthUnit.Percent));
            if (_loadingPct != null)
                _loadingPct.text = Mathf.RoundToInt(progress * 100f) + "%";
            if (_loadingPhase != null && !string.IsNullOrEmpty(phase))
                _loadingPhase.text = phase;
        }

        // ------------------------------------------------------------------ pause

        private void PauseGame()
        {
            if (TimeSystem.Instance != null)
            {
                TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Pause);
            }
        }

        private void ResumeGame()
        {
            if (TimeSystem.Instance != null && TimeSystem.Instance.CurrentSpeed == HomesteaderSpeed.Pause)
            {
                TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed1X);
            }
        }

        // ------------------------------------------------------------------ button handlers

        private void OnNewGame()
        {
            Debug.Log("[WelcomeMenu] OnNewGame clicked!");
            SetStatus("Starting new game...");

            // Delete any existing save so the new world starts fresh.
            if (GameSave.Exists)
            {
                GameSave.Delete();
                Debug.Log("[WelcomeMenu] Save deleted for new game.");
            }

            // Pick a new random world seed. Use System.Random with a time-based
            // seed because Unity's Random has already been reseeded to the
            // current worldSeed by GenerateTerrain, making Random.Range
            // deterministic (same value every time New Game is clicked).
            var seedRng = new System.Random(System.DateTime.Now.GetHashCode());
            int newSeed = seedRng.Next(1, 999999);
            Debug.Log($"[WelcomeMenu] New world seed: {newSeed}");

            // Keep the welcome card visible and show the progress bar.
            // Generate terrain in-place (no scene reload) so the card
            // never disappears/reappears.
            StartCoroutine(GenerateNewWorldInPlace(newSeed));
        }

        private void OnContinue()
        {
            if (!GameSave.Exists)
            {
                SetStatus("No save found. Start a New Game instead.");
                return;
            }
            SetStatus("Loading...");
            _isNewGamePending = false;
            _skipShowOnLoad = true;
            ReloadScene();
        }

        private void OnSave()
        {
            // Can only save if the game has started (GameSaveManager is ready)
            if (!GameSaveManager.Restored)
            {
                SetStatus("Game not ready yet. Wait a moment and try again.");
                return;
            }
            try
            {
                GameSaveManager.SaveNow();
                SetStatus("Game saved.");
                Debug.Log("[WelcomeMenu] Game saved via Welcome Menu.");
            }
            catch (System.Exception e)
            {
                SetStatus("Save failed: " + e.Message);
                Debug.LogWarning("[WelcomeMenu] Save failed: " + e.Message);
            }
        }

        private void OnLoad()
        {
            if (!GameSave.Exists)
            {
                SetStatus("No save found.");
                return;
            }
            SetStatus("Loading...");
            // Reload the scene; GameSaveManager will auto-load the save on start.
            _isNewGamePending = false;
            _skipShowOnLoad = true;
            ReloadScene();
        }

        private void OnSettings()
        {
            if (_settingsDialog == null) return;

            // Load current values from PlayerPrefs into the dialog fields
            bool locked = PlayerPrefs.GetInt("ZoomLockEnabled", 0) == 1;
            int maxLevel = PlayerPrefs.GetInt("ZoomMaxLevel", 15);
            _zoomLockToggle.value = locked;
            _zoomMaxField.value = maxLevel;

            // Show the dialog
            _settingsDialog.RemoveFromClassList("settings--hidden");
            _settingsDialog.style.display = DisplayStyle.Flex;
        }

        private void OnSettingsClose()
        {
            if (_settingsDialog == null) return;

            // Save values to PlayerPrefs
            bool locked = _zoomLockToggle.value;
            int maxLevel = _zoomMaxField.value;
            PlayerPrefs.SetInt("ZoomLockEnabled", locked ? 1 : 0);
            PlayerPrefs.SetInt("ZoomMaxLevel", Mathf.Clamp(maxLevel, 1, 100));
            PlayerPrefs.Save();

            // Notify the camera to pick up the new setting
            var cam = FindAnyObjectByType<IsometricLockedCamera>();
            if (cam != null) cam.ApplyZoomSettings();

            // Hide the dialog
            _settingsDialog.AddToClassList("settings--hidden");
            _settingsDialog.style.display = DisplayStyle.None;

            SetStatus(locked
                ? $"Zoom locked to max level {Mathf.Clamp(maxLevel, 1, 100)}."
                : "Zoom limit removed.");
        }

        private void OnExit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        // ------------------------------------------------------------------ new game (in-place, no scene reload)

        /// <summary>
        /// Generates a new world without reloading the scene. The welcome card
        /// stays visible with a progress bar the entire time. After terrain
        /// generation completes, the wallpaper and welcome card are hidden and
        /// the player character is placed at the centre of the map.
        /// </summary>
        private IEnumerator GenerateNewWorldInPlace(int newSeed)
        {
            // Find the existing terrain generator (created by TerrainGeneratorBootstrap).
            var generator = FindAnyObjectByType<HomesteaderTerrainGenerator>();
            if (generator == null)
            {
                Debug.LogWarning("[WelcomeMenu] No terrain generator found for New Game!");
                SetStatus("Error: No terrain generator found.");
                yield break;
            }

            // Apply the new seed and invalidate cached seed-dependent values.
            generator.worldSeed = newSeed;
            generator.InvalidateSeedCache();
            Debug.Log($"[WelcomeMenu] Terrain seed set to {newSeed}.");

            // Close the welcome menu (LoadingModal is now a sibling, so Hide() won't hide it).
            _isLoading = true;
            _isLoadingStatic = true;
            Hide();
            ShowLoading();
            UpdateLoadingProgress(0f, "Generating terrain...");

            // Run async terrain generation with progress updates (terrain = 0-85% of bar).
            yield return StartCoroutine(RunAsyncGeneration(generator, 0.85f));

            // --- Terrain is done. Now place the character in the starter zone. ---
            Homesteader.Land.LandOwnershipSystem.ResetToDefaults();
            Vector2 starterCenter = Homesteader.Land.LandOwnershipSystem.TileCenter(
                Homesteader.Land.LandOwnershipSystem.StarterX,
                Homesteader.Land.LandOwnershipSystem.StarterZ);
            Vector3 spawnPos = FindAccessibleSpawnPoint(starterCenter);

            var ped = FindAnyObjectByType<PedController>();
            if (ped != null)
            {
                var cc = ped.GetComponent<CharacterController>();
                if (cc != null) cc.enabled = false;
                ped.transform.position = spawnPos;
                ped.transform.rotation = Quaternion.Euler(0f, ped.modelRotationOffset, 0f);
                if (cc != null) cc.enabled = true;
                Debug.Log($"[WelcomeMenu] Player placed at: ({spawnPos.x}, {spawnPos.y:F2}, {spawnPos.z})");
            }

            CreateLandBoundaries();
            TimeSystem.Instance.ResetToNewGameDefaults();
            HudState.Active.ResetToNewGameDefaults();

            // Wait for grass to finish propagating (grass = 85-100% of bar).
            UpdateLoadingProgress(0.85f, "Growing grass...");
            yield return StartCoroutine(WaitForGrassWithProgress(0.85f, 1f));

            // Hide the loading modal and fade in the game.
            HideLoading();
            _isLoading = false;
            _isLoadingStatic = false;
            yield return StartCoroutine(FadeInGame());
            ResumeGame();
            Debug.Log("[WelcomeMenu] New game ready.");
        }

        // ------------------------------------------------------------------ land spawn

        /// <summary>
        /// Finds an accessible spawn point within the starter zone by spiralling outward
        /// from the tile centre. Checks that the ground is not water and that there's
        /// no collider (tree, rock) within a 1.5m radius.
        /// </summary>
        private Vector3 FindAccessibleSpawnPoint(Vector2 tileCenter)
        {
            float surfaceY = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(tileCenter.x, tileCenter.y);

            // Try the centre first
            if (IsAccessibleSpot(tileCenter.x, tileCenter.y))
                return new Vector3(tileCenter.x, surfaceY, tileCenter.y);

            // Spiral outward in 2m steps, up to 40m radius
            for (int radius = 2; radius <= 40; radius += 2)
            {
                int steps = Mathf.Max(8, radius * 4);
                for (int i = 0; i < steps; i++)
                {
                    float angle = (i / (float)steps) * Mathf.PI * 2f;
                    float x = tileCenter.x + Mathf.Cos(angle) * radius;
                    float z = tileCenter.y + Mathf.Sin(angle) * radius;
                    if (IsAccessibleSpot(x, z))
                    {
                        float y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(x, z);
                        return new Vector3(x, y, z);
                    }
                }
            }

            // Fallback: just use the centre even if not ideal
            Debug.LogWarning("[WelcomeMenu] No ideal spawn point found in starter zone, using centre.");
            return new Vector3(tileCenter.x, surfaceY, tileCenter.y);
        }

        /// <summary>Checks if a world position is on solid ground (not water, not blocked by objects).</summary>
        private static bool IsAccessibleSpot(float x, float z)
        {
            // Check for water — sample the terrain generator's biome
            var gen = FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>();
            if (gen != null)
            {
                Vector3 origin = gen.transform.position;
                float localX = x - origin.x;
                float localZ = z - origin.z;
                if (localX >= 0f && localX <= gen.terrainSizeX && localZ >= 0f && localZ <= gen.terrainSizeZ)
                {
                    var biome = gen.EvaluateBiomeAt(localX, localZ);
                    if (biome != null)
                    {
                        string bn = biome.name.ToLowerInvariant();
                        if (bn.Contains("water") || bn.Contains("river") || bn.Contains("pond") || bn.Contains("lake"))
                            return false;
                    }
                }
            }

            // Check for nearby colliders (trees, rocks, etc.) within 1.5m
            var checkPos = new Vector3(x, Homesteader.Generation.TerrainHeightDetector.GetGroundY(x, z) + 1f, z);
            var hits = Physics.OverlapSphere(checkPos, 1.5f);
            foreach (var h in hits)
            {
                // Ignore the terrain itself and the player
                if (h is UnityEngine.TerrainCollider) continue;
                if (h.GetComponent<PedController>() != null) continue;
                // Any other collider means this spot is blocked
                return false;
            }

            return true;
        }

        /// <summary>Creates or refreshes the LandBoundaryController in the scene.</summary>
        private static void CreateLandBoundaries()
        {
            var existing = FindAnyObjectByType<Homesteader.Land.LandBoundaryController>();
            if (existing == null)
            {
                var go = new GameObject("LandBoundaries");
                existing = go.AddComponent<Homesteader.Land.LandBoundaryController>();
            }
            existing.RebuildBoundaries();
            Debug.Log("[WelcomeMenu] Land boundaries rebuilt.");
        }

        // ------------------------------------------------------------------ scene reload

        private void ReloadScene()
        {
            // Apply the new world seed to the terrain generator before reload
            // so it picks it up on the next scene load.
            int newSeed = PlayerPrefs.GetInt("Homesteader.NewWorldSeed", 0);
            if (newSeed > 0)
            {
                var gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                if (gen != null)
                {
                    gen.worldSeed = newSeed;
                    Debug.Log($"[WelcomeMenu] Applied new world seed {newSeed} to terrain generator.");
                }
            }

            // Destroy the old GameSaveManager so a fresh one is created on
            // scene reload. GameSaveManager is DontDestroyOnLoad, so without
            // this its Start() coroutine (which loads the save) would never
            // re-run and the old Restored=true state would persist.
            var oldSaveMgr = FindAnyObjectByType<GameSaveManager>();
            if (oldSaveMgr != null)
            {
                Destroy(oldSaveMgr.gameObject);
                Debug.Log("[WelcomeMenu] Destroyed old GameSaveManager for scene reload.");
            }

            // Also destroy the old WelcomeMenuController's visual tree so it
            // doesn't stack up across reloads. The DontDestroyOnLoad GO persists
            // but the UIDocument it attached to is in the old scene.
            if (_tree != null && _tree.parent != null)
            {
                _tree.parent.Remove(_tree);
            }
            _tree = null;
            _menuRoot = null;
            _loadingSection = null;

            Hide();
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
        }

        // ------------------------------------------------------------------ status

        private void SetStatus(string text)
        {
            if (_statusLabel != null)
            {
                _statusLabel.text = text;
            }
        }

        // ------------------------------------------------------------------ update

        private void Update()
        {
            if (_root == null) return;

            bool escPressed =
#if ENABLE_INPUT_SYSTEM
                UnityEngine.InputSystem.Keyboard.current != null &&
                UnityEngine.InputSystem.Keyboard.current.escapeKey.wasPressedThisFrame;
#else
                Input.GetKeyDown(KeyCode.Escape);
#endif
            if (!escPressed) return;

            // Esc while the Controls page is waiting for a key press cancels that rebind (handled there) and
            // must not also close the menu.
            if (Homesteader.Controls.KeyBindings.IsRebinding) return;

            if (_isVisible)
            {
                Hide();
            }
            else
            {
                // Re-open the welcome menu mid-game, but without the
                // startup background image.
                if (!HudBindings.KeyboardCaptured)
                {
                    Show(withBackground: false);
                }
            }
        }

        // ------------------------------------------------------------------ apply seed after scene reload

        // After a scene reload, TerrainGeneratorBootstrap creates a fresh
        // HomesteaderTerrainGenerator. We need to set its seed before it
        // generates. This runs on the new instance after reload.
        private void OnEnable()
        {
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private void OnDisable()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            Debug.Log($"[WelcomeMenu] OnSceneLoaded: scene={scene.name}, isNewGamePending={_isNewGamePending}, skipShowOnLoad={_skipShowOnLoad}");

            if (_isNewGamePending)
            {
                int newSeed = PlayerPrefs.GetInt("Homesteader.NewWorldSeed", 0);
                Debug.Log($"[WelcomeMenu] New game seed from PlayerPrefs: {newSeed}");
                if (newSeed > 0)
                {
                    StartCoroutine(ApplyNewSeedAfterTerrainReady(newSeed));
                }
                _isNewGamePending = false;
            }

            if (_skipShowOnLoad)
            {
                // Continue/Load: don't re-show the menu, just rebuild the UI
                // so it's ready if the user opens it later, then hide it.
                _skipShowOnLoad = false;
                StartCoroutine(InitWhenReadyHidden());
                return;
            }

            // Rebuild the menu UI on the new scene's UIDocument
            StartCoroutine(InitWhenReady());
        }

        private IEnumerator ApplyNewSeedAfterTerrainReady(int newSeed)
        {
            // Wait for the terrain generator to exist
            float timeout = Time.realtimeSinceStartup + 30f;
            while (Time.realtimeSinceStartup < timeout)
            {
                var gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                if (gen != null) break;
                yield return null;
            }

            var generator = FindAnyObjectByType<HomesteaderTerrainGenerator>();
            Debug.Log($"[WelcomeMenu] ApplyNewSeed: generator found = {generator != null}");
            if (generator != null)
            {
                generator.worldSeed = newSeed;
                generator.InvalidateSeedCache();
                Debug.Log($"[WelcomeMenu] Terrain seed set to {newSeed}, waiting for menu UI rebuild...");

                // Clear the pending seed so the bootstrap generates normally
                // on future scene loads (Continue/Load).
                PlayerPrefs.DeleteKey("Homesteader.NewWorldSeed");
                PlayerPrefs.Save();

                // Wait for the menu UI to be rebuilt (InitWhenReady runs in
                // parallel and re-resolves _loadingSection etc.). Without this
                // the progress bar is null and never appears.
                timeout = Time.realtimeSinceStartup + 30f;
                while (Time.realtimeSinceStartup < timeout)
                {
                    if (_loadingSection != null && _menuRoot != null) break;
                    yield return null;
                }
                Debug.Log($"[WelcomeMenu] Menu UI ready: _loadingSection={_loadingSection != null}, _menuRoot={_menuRoot != null}");

                // Show the loading modal, then run async generation.
                _isLoading = true;
            _isLoadingStatic = true;
                Hide(); // LoadingModal is a sibling, so Hide() won't hide it.
                ShowLoading();
                UpdateLoadingProgress(0f, "Generating terrain...");

                Debug.Log("[WelcomeMenu] Starting async terrain generation...");
                yield return StartCoroutine(RunAsyncGeneration(generator, 0.85f));

                // Wait for grass to finish propagating (grass = 85-100% of bar).
                UpdateLoadingProgress(0.85f, "Growing grass...");
                yield return StartCoroutine(WaitForGrassWithProgress(0.85f, 1f));

                HideLoading();
                _isLoading = false;
            _isLoadingStatic = false;
                yield return StartCoroutine(FadeInGame());
                ResumeGame();
            }
            else
            {
                Debug.LogWarning("[WelcomeMenu] No terrain generator found after scene reload!");
                HudState.Active.ResetToNewGameDefaults();
                Show();
            }
        }

        private IEnumerator FadeInGame()
        {
            // The game view is already visible. Fade the wallpaper OUT over 0.5s
            // so the game is revealed underneath.
            if (_wallpaper != null)
            {
                _wallpaper.style.display = DisplayStyle.Flex;
                _wallpaper.style.opacity = 1f;
                _wallpaper.RemoveFromClassList("welcome--hidden");
                float elapsed = 0f;
                const float duration = 0.5f;
                while (elapsed < duration)
                {
                    elapsed += Time.unscaledDeltaTime;
                    _wallpaper.style.opacity = 1f - Mathf.Clamp01(elapsed / duration);
                    yield return null;
                }
                _wallpaper.style.opacity = 0f;
                _wallpaper.style.display = DisplayStyle.None;
                _wallpaper.AddToClassList("welcome--hidden");
            }
            else
            {
                yield return null;
            }
        }

        private IEnumerator WaitForGrass()
        {
            float timeout = Time.realtimeSinceStartup + 60f;
            while (Time.realtimeSinceStartup < timeout)
            {
                var grass = FindAnyObjectByType<Homesteader.Grass.GrassRenderer>();
                if (grass == null || !grass.IsGenerating) break;
                yield return null;
            }
        }

        /// <summary>
        /// Waits for grass to finish, updating the progress bar from startProgress
        /// to endProgress. Since grass doesn't report granular progress, we ease
        /// the bar toward endProgress based on elapsed time.
        /// </summary>
        private IEnumerator WaitForGrassWithProgress(float startProgress, float endProgress)
        {
            float timeout = Time.realtimeSinceStartup + 60f;
            float startTime = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup < timeout)
            {
                var grass = FindAnyObjectByType<Homesteader.Grass.GrassRenderer>();
                if (grass == null || !grass.IsGenerating) break;

                // Ease the bar toward endProgress — faster at the start, slowing
                // as it approaches the end, so it never reaches 100% before grass
                // is actually done.
                float elapsed = Time.realtimeSinceStartup - startTime;
                float t = Mathf.Clamp01(elapsed / 10f);
                float eased = 1f - Mathf.Pow(1f - t, 2f); // ease-out quad
                float progress = Mathf.Lerp(startProgress, endProgress, eased * 0.9f);
                UpdateLoadingProgress(progress, "Growing grass...");
                yield return null;
            }
            UpdateLoadingProgress(endProgress, "Growing grass...");
        }

        private IEnumerator RunAsyncGeneration(HomesteaderTerrainGenerator generator, float maxProgress = 1f)
        {
            // Start the async generation coroutine on the generator's MonoBehaviour
            Debug.Log($"[WelcomeMenu] RunAsyncGeneration: generator.IsGenerating={generator.IsGenerating}, generator.GenerationProgress={generator.GenerationProgress}");
            var routine = StartCoroutine(generator.GenerateTerrainAsync());

            // Give the coroutine one frame to set IsGenerating = true
            yield return null;
            Debug.Log($"[WelcomeMenu] After first yield: generator.IsGenerating={generator.IsGenerating}");

            // Poll progress each frame until generation completes.
            // Scale terrain progress (0-1) into the bar range (0-maxProgress).
            while (generator.IsGenerating)
            {
                UpdateLoadingProgress(generator.GenerationProgress * maxProgress, generator.GenerationPhase);
                yield return null;
            }

            Debug.Log($"[WelcomeMenu] Generation complete: progress={generator.GenerationProgress}");

            // Final update
            UpdateLoadingProgress(maxProgress, "Done!");
            // Use WaitForSecondsRealtime because the game is paused (timeScale=0)
            // during the welcome menu — regular WaitForSeconds would never fire.
            yield return new WaitForSecondsRealtime(0.3f);

            // Note: Hide() and HUD reset are now handled by the caller
            // (GenerateNewWorldInPlace) so it can also place the character.
        }
    }
}
