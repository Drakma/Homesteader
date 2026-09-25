// HudBindings.cs - drive HUD widgets from HudState + TimeSystem.
//
// Each frame this MonoBehaviour ticks the TimeSystem and writes
// state into the live UIDocument. The widgets are free-floating
// components under Resources/HUDTree/ - HudBindings uses the Q()
// query to find each label/visualElement by name.

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    [DefaultExecutionOrder(-80)]
    [RequireComponent(typeof(UIDocument))]
    public sealed class HudBindings : MonoBehaviour
    {
        [SerializeField] private bool _enableTimeUpdates = true;
        [SerializeField] private bool _enableResourceUpdates = true;
        [SerializeField] private bool _enableVitalUpdates = true;
        [SerializeField] private bool _enableToolbarUpdates = true;
        [SerializeField] private bool _ownsTimeSystem = true;

        [Tooltip("When true, write percent (0..100) to the label. " +
                 "Else write raw signed value as +N%/-N%.")]
        [SerializeField] private bool _vitalsNormalizedPercent = false;

        private UIDocument _doc;
        private VisualElement _root;

        private Label _timeLineLabel;
        private Label _speedStateLabel;
        private VisualElement _weatherIcon;
        private VisualElement _celestialIcon;
        private Label _seasonLabel;
        private Label _dayLabel;
        private Label _clockLabel;

        private static readonly Dictionary<string, Texture2D> s_celestialTextures = new Dictionary<string, Texture2D>();
        private static readonly Dictionary<string, Texture2D> s_weatherTextures = new Dictionary<string, Texture2D>();

        private static Texture2D GetCelestialTexture(string iconId)
        {
            if (string.IsNullOrEmpty(iconId)) return null;
            if (!s_celestialTextures.TryGetValue(iconId, out var tex) || tex == null)
            {
                tex = Resources.Load<Texture2D>("HUDTree/KitSprites/celestial/" + iconId);
                s_celestialTextures[iconId] = tex;
            }
            return tex;
        }

        private static Texture2D GetWeatherTexture(string iconId)
        {
            if (string.IsNullOrEmpty(iconId)) return null;
            if (!s_weatherTextures.TryGetValue(iconId, out var tex) || tex == null)
            {
                tex = Resources.Load<Texture2D>("HUDTree/KitSprites/weather/" + iconId);
                s_weatherTextures[iconId] = tex;
            }
            return tex;
        }

        private Label _resourceWater;
        private Label _resourceElectricity;
        private Label _resourceBandwidth;
        private Label _resourceFuel;
        private Label _resourceMoney;

        // Vital bar fill elements. width is set as Length(percent).
        private VisualElement _vitalWellnessFill;
        private VisualElement _vitalStaminaFill;
        private VisualElement _vitalThirstFill;
        private VisualElement _vitalHungerFill;
        // Vital percent labels
        private Label _vitalWellnessPct;
        private Label _vitalStaminaPct;
        private Label _vitalThirstPct;
        private Label _vitalHungerPct;

        // Toolbar
        private VisualElement[] _toolbarSlots = new VisualElement[10];
        private Label[] _toolbarSlotLabels = new Label[10];

        // Speed chips
        private Button _speedPause;
        private Button _speed1X;
        private Button _speed3X;
        private Button _speed5X;
        private Button _speed10X;
        private HomesteaderSpeed _lastActiveSpeed = HomesteaderSpeed.Speed1X;

        // Window & Modal Elements
        private VisualElement _windowShade;
        private VisualElement _settingsWindow;
        private Button _settingsBtn;
        private Button _settingsCloseBtn;
        private Button _settingsApplyBtn;
        private Button _settingsResetBtn;
        private Button _testModalBtn;
        private Slider _masterVolumeSlider;
        private Slider _musicVolumeSlider;
        private Toggle _fullscreenToggle;
        private Toggle _vsyncToggle;

        private VisualElement _confirmModal;
        private Label _modalTitle;
        private Label _modalMessage;
        private Button _modalCloseBtn;
        private Button _modalCancelBtn;
        private Button _modalConfirmBtn;
        private Button _modalThirdBtn;

        private System.Action _onModalConfirm;
        private System.Action _onModalCancel;
        private System.Action _onModalThird;

        // Celestial Timeline tape elements
        private VisualElement _timelineWell;
        private VisualElement _timelineTrack;
        private const float TimelinePixelsPer4Hours = 100f; // 100px per 4-hour interval (25px per hour)
        private const int TimelineIntervalCount = 8; // 8 intervals of 4-hours (-16h to +16h)
        private VisualElement[] _timelineCelestialIcons;
        private VisualElement[] _timelineMajorNodes;
        private static readonly Dictionary<string, Texture2D> s_celestialCache = new Dictionary<string, Texture2D>();

        // Weather Timeline tape elements
        private VisualElement _weatherTimelineWell;
        private VisualElement _weatherTimelineTrack;
        private Label _currentTempLabel;
        private VisualElement[] _weatherTimelineIcons;
        private VisualElement[] _weatherMajorNodes;
        private static readonly Dictionary<string, Texture2D> s_weatherCache = new Dictionary<string, Texture2D>();

        // In-game Smartphone
        private PhoneController _phone;
        private bool _wired;

        public static HudBindings Instance { get; private set; }

        public PhoneController Phone => _phone;
        public bool IsSettingsOpen => _settingsWindow != null && !_settingsWindow.ClassListContains("window--hidden");
        public bool IsModalOpen => _confirmModal != null && !_confirmModal.ClassListContains("modal--hidden");
        public bool IsAnyShadeOpen => _windowShade != null && !_windowShade.ClassListContains("window-shade--hidden");

        // Asset Spawner Window
        private VisualElement _assetSpawnerWindow;
        private Button _assetSpawnerCloseBtn;
        private Label _assetSpawnerCountBadge;
        private Label _assetSpawnerStatusLabel;
        private DropdownField _assetCategoryDropdown;
        private TextField _assetSearchInput;
        private VisualElement _assetGridContainer;
        private string _selectedAssetCategory = "all";
        private string _assetSearchQuery = "";
        private static AssetCatalogDatabase s_assetCatalog;
        private readonly List<string> _assetCategoryKeys = new List<string>();

        public bool IsAssetSpawnerOpen => _assetSpawnerWindow != null && !_assetSpawnerWindow.ClassListContains("asset-spawner-window--hidden");

        private static Texture2D _posFillTex;
        private static Texture2D _negFillTex;

        private static void EnsureGradients()
        {
            if (_posFillTex != null && _negFillTex != null) return;

            _posFillTex = Resources.Load<Texture2D>("HUDTree/Atlases/vital_fill_positive");
            _negFillTex = Resources.Load<Texture2D>("HUDTree/Atlases/vital_fill_negative");

            if (_posFillTex == null)
            {
                _posFillTex = CreateGradientTexture(new Color(1f, 0.835f, 0.31f), new Color(0.29f, 0.77f, 0.49f)); // Amber -> Green
            }
            if (_negFillTex == null)
            {
                _negFillTex = CreateGradientTexture(new Color(0.863f, 0.431f, 0.353f), new Color(1f, 0.835f, 0.31f)); // Red -> Amber
            }
        }

        private static Texture2D CreateGradientTexture(Color left, Color right)
        {
            var tex = new Texture2D(64, 1, TextureFormat.RGBA32, false)
            {
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear,
                hideFlags = HideFlags.HideAndDontSave
            };
            var colors = new Color[64];
            for (int i = 0; i < 64; i++)
            {
                float t = i / 63f;
                colors[i] = Color.Lerp(left, right, t);
            }
            tex.SetPixels(colors);
            tex.Apply();
            return tex;
        }

        private void Awake()
        {
            Instance = this;
            _doc = GetComponent<UIDocument>();
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        private void OnEnable()
        {
            ResolveReferences();
        }

        public void ResolveReferences()
        {
            if (_doc == null) _doc = GetComponent<UIDocument>();
            if (_doc == null) { return; }
            _root = _doc.rootVisualElement;
            if (_root == null) { return; }

            // Guard: ensure the tree is actually mounted by checking for key elements
            var windowShadeCheck = _root.Q<VisualElement>("WindowShade");
            if (windowShadeCheck == null)
            {
                _wired = false;
                return;
            }

            _timeLineLabel = Q<Label>("TimeLineLabel");
            _speedStateLabel = Q<Label>("SpeedStateLabel");
            _weatherIcon = Q<VisualElement>("WeatherIcon");
            _celestialIcon = Q<VisualElement>("CelestialIcon");
            _seasonLabel = Q<Label>("SeasonLabel");
            _dayLabel = Q<Label>("DayLabel");
            _clockLabel = Q<Label>("ClockLabel");
            _resourceWater = Q<Label>("ResourceWaterLabel");
            _resourceElectricity = Q<Label>("ResourceElectricityLabel");
            _resourceBandwidth = Q<Label>("ResourceBandwidthLabel");
            _resourceFuel = Q<Label>("ResourceFuelLabel");
            _resourceMoney = Q<Label>("ResourceMoneyLabel");

            _vitalWellnessFill = Q<VisualElement>("VitalWellnessFill");
            _vitalStaminaFill = Q<VisualElement>("VitalStaminaFill");
            _vitalThirstFill = Q<VisualElement>("VitalThirstFill");
            _vitalHungerFill = Q<VisualElement>("VitalHungerFill");
            _vitalWellnessPct = Q<Label>("VitalWellnessPct");
            _vitalStaminaPct = Q<Label>("VitalStaminaPct");
            _vitalThirstPct = Q<Label>("VitalThirstPct");
            _vitalHungerPct = Q<Label>("VitalHungerPct");

            for (int i = 0; i < _toolbarSlots.Length; i++)
            {
                _toolbarSlots[i] = Q<VisualElement>("ToolbarSlot" + i.ToString());
                _toolbarSlotLabels[i] = Q<Label>("ToolSlotLabel" + i.ToString());
                if (_toolbarSlots[i] != null)
                {
                    int slotIndex = i;
                    _toolbarSlots[i].RegisterCallback<ClickEvent>(evt =>
                    {
                        SelectToolbarSlot(slotIndex);
                    });
                }
            }

            _speedPause = Q<Button>("SpeedPause");
            _speed1X = Q<Button>("Speed1X");
            _speed3X = Q<Button>("Speed3X");
            _speed5X = Q<Button>("Speed5X");
            _speed10X = Q<Button>("Speed10X") ?? Q<Button>("Speed9X");

            if (_speed1X != null)
            {
                WireSpeedChips();
            }

            _windowShade = windowShadeCheck;
            _settingsWindow = Q<VisualElement>("SettingsWindow");
            _settingsBtn = Q<Button>("SettingsBtn");
            _settingsCloseBtn = Q<Button>("SettingsCloseBtn");
            _settingsApplyBtn = Q<Button>("SettingsApplyBtn");
            _settingsResetBtn = Q<Button>("SettingsResetBtn");
            _testModalBtn = Q<Button>("TestModalBtn");
            _masterVolumeSlider = Q<Slider>("MasterVolumeSlider");
            _musicVolumeSlider = Q<Slider>("MusicVolumeSlider");
            _fullscreenToggle = Q<Toggle>("FullscreenToggle");
            _vsyncToggle = Q<Toggle>("VsyncToggle");

            _confirmModal = Q<VisualElement>("ConfirmModal");
            _modalTitle = Q<Label>("ModalTitle");
            _modalMessage = Q<Label>("ModalMessage");
            _modalCloseBtn = Q<Button>("ModalCloseBtn");
            _modalCancelBtn = Q<Button>("ModalCancelBtn");
            _modalConfirmBtn = Q<Button>("ModalConfirmBtn");
            _modalThirdBtn = Q<Button>("ModalThirdBtn");

            WireWindowAndModal();

            // Toast Notification System initialization
            var toastContainer = Q<VisualElement>("ToastContainer");
            var toastSys = GetComponent<ToastNotificationSystem>();
            if (toastSys == null) toastSys = gameObject.AddComponent<ToastNotificationSystem>();
            if (toastContainer != null) toastSys.BindContainer(toastContainer);

            // Timeline Tapes initialization
            _timelineWell = Q<VisualElement>("TimelineWell");
            _timelineTrack = Q<VisualElement>("TimelineTrack");
            BuildTimelineTrack();

            _weatherTimelineWell = Q<VisualElement>("WeatherTimelineWell");
            _weatherTimelineTrack = Q<VisualElement>("WeatherTimelineTrack");
            _currentTempLabel = Q<Label>("CurrentTempLabel");
            BuildWeatherTimelineTrack();

            _phone = new PhoneController(_root,
                (title, message, onConfirm, onCancel) => ShowModal(title, message, onConfirm, onCancel));

            // Asset Spawner initialization
            _assetSpawnerWindow = Q<VisualElement>("AssetSpawnerWindow");
            _assetSpawnerCloseBtn = Q<Button>("AssetSpawnerCloseBtn");
            _assetSpawnerCountBadge = Q<Label>("AssetSpawnerCountBadge");
            _assetSpawnerStatusLabel = Q<Label>("AssetSpawnerStatusLabel");
            _assetCategoryDropdown = Q<DropdownField>("AssetCategoryDropdown");
            _assetSearchInput = Q<TextField>("AssetSearchInput");
            _assetGridContainer = Q<VisualElement>("AssetGridContainer");
            _assetGridContainer?.RegisterCallback<GeometryChangedEvent>(evt => LayoutAssetGrid());

            if (_assetSpawnerCloseBtn != null)
            {
                _assetSpawnerCloseBtn.clicked += CloseAssetSpawner;
            }

            if (_assetSearchInput != null)
            {
                _assetSearchInput.RegisterValueChangedCallback(evt =>
                {
                    _assetSearchQuery = evt.newValue != null ? evt.newValue.Trim() : "";
                    FilterAndDisplayAssets();
                });
            }

            if (_assetSpawnerWindow != null)
            {
                var spawnerHeader = _assetSpawnerWindow.Q<VisualElement>(className: "window-header");
                MakeDraggable(_assetSpawnerWindow, spawnerHeader);
                MakeResizable(_assetSpawnerWindow, _assetSpawnerWindow.Q<VisualElement>("AssetSpawnerResizeHandle"), new Vector2(480f, 360f));
            }

            _wired = true;
        }

        private T Q<T>(string name) where T : VisualElement
        {
            if (_root == null) { return null; }
            return _root.Q<T>(name);
        }

        private void WireSpeedChips()
        {
            if (_speedPause != null) _speedPause.clicked += TogglePausePlay;
            if (_speed1X != null) _speed1X.clicked += () => { _lastActiveSpeed = HomesteaderSpeed.Speed1X; TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed1X); UpdateSpeedChips(HomesteaderSpeed.Speed1X); };
            if (_speed3X != null) _speed3X.clicked += () => { _lastActiveSpeed = HomesteaderSpeed.Speed3X; TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed3X); UpdateSpeedChips(HomesteaderSpeed.Speed3X); };
            if (_speed5X != null) _speed5X.clicked += () => { _lastActiveSpeed = HomesteaderSpeed.Speed5X; TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed5X); UpdateSpeedChips(HomesteaderSpeed.Speed5X); };
            if (_speed10X != null) _speed10X.clicked += () => { _lastActiveSpeed = HomesteaderSpeed.Speed10X; TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed10X); UpdateSpeedChips(HomesteaderSpeed.Speed10X); };
        }

        private void WireWindowAndModal()
        {
            if (_settingsBtn != null) _settingsBtn.clicked += ToggleSettings;
            if (_settingsCloseBtn != null) _settingsCloseBtn.clicked += CloseSettings;
            if (_settingsApplyBtn != null) _settingsApplyBtn.clicked += CloseSettings;
            if (_settingsResetBtn != null)
            {
                _settingsResetBtn.clicked += () =>
                {
                    if (_masterVolumeSlider != null) _masterVolumeSlider.value = 80;
                    if (_musicVolumeSlider != null) _musicVolumeSlider.value = 65;
                    if (_fullscreenToggle != null) _fullscreenToggle.value = true;
                    if (_vsyncToggle != null) _vsyncToggle.value = true;
                };
            }
            if (_testModalBtn != null)
            {
                _testModalBtn.clicked += ShowExampleModal;
            }

            if (_modalCloseBtn != null) _modalCloseBtn.clicked += CloseModal;
            if (_modalCancelBtn != null)
            {
                _modalCancelBtn.clicked += () =>
                {
                    var cb = _onModalCancel;
                    CloseModal();
                    cb?.Invoke();
                };
            }
            if (_modalConfirmBtn != null)
            {
                _modalConfirmBtn.clicked += () =>
                {
                    var cb = _onModalConfirm;
                    CloseModal();
                    cb?.Invoke();
                };
            }
            if (_modalThirdBtn != null)
            {
                _modalThirdBtn.clicked += () =>
                {
                    var cb = _onModalThird;
                    CloseModal();
                    cb?.Invoke();
                };
            }

            // Click shade background outside window/modal to dismiss
            if (_windowShade != null)
            {
                _windowShade.RegisterCallback<ClickEvent>(evt =>
                {
                    if (evt.target == _windowShade)
                    {
                        if (IsModalOpen) CloseModal();
                        else if (IsSettingsOpen) CloseSettings();
                    }
                });
            }

            // Make windows draggable by their header
            if (_settingsWindow != null)
            {
                var settingsHeader = _settingsWindow.Q<VisualElement>(className: "window-header");
                MakeDraggable(_settingsWindow, settingsHeader);
            }

            if (_confirmModal != null)
            {
                var modalHeader = _confirmModal.Q<VisualElement>(className: "window-header");
                MakeDraggable(_confirmModal, modalHeader);
            }
        }

        private void MakeDraggable(VisualElement window, VisualElement header)
        {
            if (window == null || header == null) return;

            bool isDragging = false;
            Vector2 dragStartPointer = Vector2.zero;
            Vector3 dragStartPos = Vector3.zero;

            header.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.button != 0) return;

                // Ignore if clicked on a button or button's child (e.g. close button)
                if (evt.target is Button || (evt.target is VisualElement ve && ve.GetFirstAncestorOfType<Button>() != null))
                    return;

                isDragging = true;
                dragStartPointer = evt.position;
                var currentTranslate = window.resolvedStyle.translate;
                dragStartPos = new Vector3(currentTranslate.x, currentTranslate.y, 0f);
                header.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });

            header.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!isDragging || !header.HasPointerCapture(evt.pointerId)) return;

                Vector2 delta = (Vector2)evt.position - dragStartPointer;
                Vector3 newPos = dragStartPos + new Vector3(delta.x, delta.y, 0f);

                // Keep only a 40px grab area of the window on-screen so it can go anywhere without getting lost
                VisualElement parent = window.parent;
                if (parent != null && parent.resolvedStyle.width > 0)
                {
                    const float keep = 40f;
                    var cur = window.resolvedStyle.translate;
                    Rect wb = window.worldBound;
                    Rect pb = parent.worldBound;

                    float shiftX = newPos.x - cur.x;
                    float shiftY = newPos.y - cur.y;

                    float minShiftX = (pb.xMin + keep) - wb.xMax;
                    float maxShiftX = (pb.xMax - keep) - wb.xMin;
                    float minShiftY = pb.yMin - wb.yMin;
                    float maxShiftY = (pb.yMax - keep) - wb.yMin;

                    shiftX = Mathf.Clamp(shiftX, minShiftX, maxShiftX);
                    shiftY = Mathf.Clamp(shiftY, minShiftY, maxShiftY);

                    newPos.x = cur.x + shiftX;
                    newPos.y = cur.y + shiftY;
                }

                window.style.translate = new StyleTranslate(new Translate(new Length(newPos.x), new Length(newPos.y)));
                evt.StopPropagation();
            });

            header.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (isDragging && header.HasPointerCapture(evt.pointerId))
                {
                    isDragging = false;
                    header.ReleasePointer(evt.pointerId);
                    evt.StopPropagation();
                }
            });

            header.RegisterCallback<PointerCaptureOutEvent>(evt =>
            {
                isDragging = false;
            });
        }

        private void MakeResizable(VisualElement window, VisualElement handle, Vector2 minSize)
        {
            if (window == null || handle == null) return;

            bool isResizing = false;
            Vector2 startPointer = Vector2.zero;
            Vector2 startSize = Vector2.zero;

            handle.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.button != 0) return;

                isResizing = true;
                startPointer = evt.position;
                startSize = new Vector2(window.resolvedStyle.width, window.resolvedStyle.height);

                // Pin the current (possibly percent-based) translate in pixels so the top-left corner stays put.
                var t = window.resolvedStyle.translate;
                window.style.translate = new StyleTranslate(new Translate(new Length(t.x), new Length(t.y)));

                handle.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });

            handle.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!isResizing || !handle.HasPointerCapture(evt.pointerId)) return;

                Vector2 delta = (Vector2)evt.position - startPointer;
                float newW = Mathf.Max(minSize.x, startSize.x + delta.x);
                float newH = Mathf.Max(minSize.y, startSize.y + delta.y);

                VisualElement parent = window.parent;
                if (parent != null && parent.resolvedStyle.width > 0)
                {
                    var wb = window.worldBound;
                    var pb = parent.worldBound;
                    newW = Mathf.Min(newW, pb.xMax - wb.xMin);
                    newH = Mathf.Min(newH, pb.yMax - wb.yMin);
                    newW = Mathf.Max(minSize.x, newW);
                    newH = Mathf.Max(minSize.y, newH);
                }

                window.style.width = newW;
                window.style.height = newH;
                evt.StopPropagation();
            });

            handle.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (isResizing && handle.HasPointerCapture(evt.pointerId))
                {
                    isResizing = false;
                    handle.ReleasePointer(evt.pointerId);
                    evt.StopPropagation();
                }
            });

            handle.RegisterCallback<PointerCaptureOutEvent>(evt =>
            {
                isResizing = false;
            });
        }

        /// <summary>
        /// True while a HUD window is open or a text field has focus. Gameplay input
        /// (movement, camera, hotkeys) must not read the keyboard while this is true.
        /// </summary>
        public static bool KeyboardCaptured =>
            Instance != null && (Instance.IsModalOpen || Instance.IsSettingsOpen || Instance.IsAssetSpawnerOpen || Instance.IsTextInputFocused());

        private bool IsTextInputFocused()
        {
            for (var e = _root?.panel?.focusController?.focusedElement as VisualElement; e != null; e = e.parent)
                if (e is TextField || e is IntegerField || e is FloatField || e is LongField || e is DoubleField) return true;
            return false;
        }

        private bool BlurFocusedTextInput()
        {
            if (!IsTextInputFocused()) return false;
            (_root.panel.focusController.focusedElement as VisualElement)?.Blur();
            return true;
        }

        private void HandleShortcuts()
        {
#if ENABLE_INPUT_SYSTEM
            var kb = UnityEngine.InputSystem.Keyboard.current;
            bool phoneOpen = _phone != null && _phone.IsOpen;
            if (kb != null)
            {
                if (kb.escapeKey.wasPressedThisFrame)
                {
                    if (!BlurFocusedTextInput())
                    {
                        if (IsAssetSpawnerOpen) CloseAssetSpawner();
                        else if (IsModalOpen) CloseModal();
                        else if (IsSettingsOpen) CloseSettings();
                        else if (phoneOpen) _phone.Close();
                        else OpenSettings();
                    }
                }
                // A focused window / text field owns the keyboard: no hotkeys reach the game
                else if (KeyboardCaptured)
                {
                }
                else if (kb.tabKey.wasPressedThisFrame)
                {
                    _phone?.Toggle();
                }
                // Speed Control Shortcuts
                else
                {
                    if (kb.spaceKey.wasPressedThisFrame)
                    {
                        TogglePausePlay();
                    }
                    else if (kb.rightBracketKey.wasPressedThisFrame)
                    {
                        IncreaseSpeed();
                    }
                    else if (kb.leftBracketKey.wasPressedThisFrame)
                    {
                        DecreaseSpeed();
                    }
                    // Toolbar slot selection keys (1..0) - disabled when phone or asset spawner is open
                    else if (!phoneOpen && !IsAssetSpawnerOpen)
                    {
                        if (kb.digit1Key.wasPressedThisFrame || kb.numpad1Key.wasPressedThisFrame) SelectToolbarSlot(0);
                        else if (kb.digit2Key.wasPressedThisFrame || kb.numpad2Key.wasPressedThisFrame) SelectToolbarSlot(1);
                        else if (kb.digit3Key.wasPressedThisFrame || kb.numpad3Key.wasPressedThisFrame) SelectToolbarSlot(2);
                        else if (kb.digit4Key.wasPressedThisFrame || kb.numpad4Key.wasPressedThisFrame) SelectToolbarSlot(3);
                        else if (kb.digit5Key.wasPressedThisFrame || kb.numpad5Key.wasPressedThisFrame) SelectToolbarSlot(4);
                        else if (kb.digit6Key.wasPressedThisFrame || kb.numpad6Key.wasPressedThisFrame) SelectToolbarSlot(5);
                        else if (kb.digit7Key.wasPressedThisFrame || kb.numpad7Key.wasPressedThisFrame) SelectToolbarSlot(6);
                        else if (kb.digit8Key.wasPressedThisFrame || kb.numpad8Key.wasPressedThisFrame) SelectToolbarSlot(7);
                        else if (kb.digit9Key.wasPressedThisFrame || kb.numpad9Key.wasPressedThisFrame) SelectToolbarSlot(8);
                        else if (kb.digit0Key.wasPressedThisFrame || kb.numpad0Key.wasPressedThisFrame) SelectToolbarSlot(9);
                    }
                }
            }
#else
            bool phoneOpen = _phone != null && _phone.IsOpen;
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (!BlurFocusedTextInput())
                {
                    if (IsAssetSpawnerOpen) CloseAssetSpawner();
                    else if (IsModalOpen) CloseModal();
                    else if (IsSettingsOpen) CloseSettings();
                    else if (phoneOpen) _phone.Close();
                    else OpenSettings();
                }
            }
            else if (KeyboardCaptured)
            {
            }
            else if (Input.GetKeyDown(KeyCode.Tab))
            {
                _phone?.Toggle();
            }
            else
            {
                if (Input.GetKeyDown(KeyCode.Space))
                {
                    TogglePausePlay();
                }
                else if (Input.GetKeyDown(KeyCode.RightBracket))
                {
                    IncreaseSpeed();
                }
                else if (Input.GetKeyDown(KeyCode.LeftBracket))
                {
                    DecreaseSpeed();
                }
                // Toolbar slot selection keys (1..0) - disabled when phone or asset spawner is open
                else if (!phoneOpen && !IsAssetSpawnerOpen)
                {
                    if (Input.GetKeyDown(KeyCode.Alpha1) || Input.GetKeyDown(KeyCode.Keypad1)) SelectToolbarSlot(0);
                    else if (Input.GetKeyDown(KeyCode.Alpha2) || Input.GetKeyDown(KeyCode.Keypad2)) SelectToolbarSlot(1);
                    else if (Input.GetKeyDown(KeyCode.Alpha3) || Input.GetKeyDown(KeyCode.Keypad3)) SelectToolbarSlot(2);
                    else if (Input.GetKeyDown(KeyCode.Alpha4) || Input.GetKeyDown(KeyCode.Keypad4)) SelectToolbarSlot(3);
                    else if (Input.GetKeyDown(KeyCode.Alpha5) || Input.GetKeyDown(KeyCode.Keypad5)) SelectToolbarSlot(4);
                    else if (Input.GetKeyDown(KeyCode.Alpha6) || Input.GetKeyDown(KeyCode.Keypad6)) SelectToolbarSlot(5);
                    else if (Input.GetKeyDown(KeyCode.Alpha7) || Input.GetKeyDown(KeyCode.Keypad7)) SelectToolbarSlot(6);
                    else if (Input.GetKeyDown(KeyCode.Alpha8) || Input.GetKeyDown(KeyCode.Keypad8)) SelectToolbarSlot(7);
                    else if (Input.GetKeyDown(KeyCode.Alpha9) || Input.GetKeyDown(KeyCode.Keypad9)) SelectToolbarSlot(8);
                    else if (Input.GetKeyDown(KeyCode.Alpha0) || Input.GetKeyDown(KeyCode.Keypad0)) SelectToolbarSlot(9);
                }
            }
#endif

            // Mouse ScrollWheel toolbar slot cycling (when Ctrl is NOT held down, and game is NOT paused)
            bool isCtrl = false;
            float scrollDelta = 0f;
#if ENABLE_INPUT_SYSTEM
            var kbCurrent = UnityEngine.InputSystem.Keyboard.current;
            if (kbCurrent != null)
            {
                isCtrl = kbCurrent.leftCtrlKey.isPressed || kbCurrent.rightCtrlKey.isPressed;
            }
            var mouseCurrent = UnityEngine.InputSystem.Mouse.current;
            if (mouseCurrent != null)
            {
                scrollDelta = mouseCurrent.scroll.ReadValue().y;
            }
#else
            isCtrl = Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl);
            scrollDelta = Input.mouseScrollDelta.y;
#endif

            bool isPaused = TimeSystem.Instance != null && TimeSystem.Instance.IsPaused;
            if (!isPaused && !isCtrl && Mathf.Abs(scrollDelta) > 0.01f && !KeyboardCaptured && !phoneOpen)
            {
                int dir = scrollDelta > 0f ? -1 : 1;
                int current = HudState.Active.SelectedSlot;
                int next = (current + dir + HudState.ToolbarSize) % HudState.ToolbarSize;
                SelectToolbarSlot(next);
            }
        }

        /// <summary>True when the screen position is over a pickable HUD element (window, phone, toolbar).</summary>
        public bool IsPointerOverUI(Vector2 screenPos)
        {
            if (_root == null || _root.panel == null) return false;
            Vector2 panelPos = RuntimePanelUtils.ScreenToPanel(_root.panel, new Vector2(screenPos.x, Screen.height - screenPos.y));
            VisualElement picked = _root.panel.Pick(panelPos);
            // The full-screen containers (panel root, TemplateContainer, ScreenRoot) sit under
            // the whole game view and would otherwise count as "over the UI" everywhere.
            return picked != null
                && picked != _root
                && !(picked is TemplateContainer)
                && !picked.ClassListContains("screen-root");
        }

        /// <summary>Catalog max stack size for an item id (64 when unknown).</summary>
        public static int GetMaxStack(string itemId)
        {
            EnsureAssetCatalogLoaded();
            var item = s_assetCatalog?.items?.Find(i => i.id == itemId);
            return item != null && item.max_stack > 0 ? item.max_stack : 64;
        }

        /// <summary>Catalog display name for an item id (the id itself when unknown).</summary>
        public static string GetItemName(string itemId)
        {
            EnsureAssetCatalogLoaded();
            var item = s_assetCatalog?.items?.Find(i => i.id == itemId);
            return item != null && !string.IsNullOrEmpty(item.name) ? item.name : itemId;
        }

        public void SelectToolbarSlot(int slotIndex)
        {
            if (slotIndex >= 0 && slotIndex < HudState.ToolbarSize)
            {
                HudState.Active.SelectSlot(slotIndex);
                WriteToolbar(HudState.Active);
            }
        }

        private void TogglePausePlay()
        {
            if (TimeSystem.Instance.CurrentSpeed == HomesteaderSpeed.Pause)
            {
                var playSpeed = (_lastActiveSpeed != HomesteaderSpeed.Pause) ? _lastActiveSpeed : HomesteaderSpeed.Speed1X;
                TimeSystem.Instance.SetSpeed(playSpeed);
                ToastNotificationSystem.ShowInfo("Game Resumed", $"Simulation running at {SpeedToString(playSpeed)}.");
            }
            else
            {
                _lastActiveSpeed = TimeSystem.Instance.CurrentSpeed;
                TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Pause);
                ToastNotificationSystem.ShowWarning("Game Paused", "Simulation paused. Press Spacebar or toggle speed to resume.");
            }
        }

        private void IncreaseSpeed()
        {
            HomesteaderSpeed nextSpeed;
            if (TimeSystem.Instance.CurrentSpeed == HomesteaderSpeed.Pause)
            {
                nextSpeed = (_lastActiveSpeed != HomesteaderSpeed.Pause) ? _lastActiveSpeed : HomesteaderSpeed.Speed1X;
            }
            else
            {
                switch (TimeSystem.Instance.CurrentSpeed)
                {
                    case HomesteaderSpeed.Speed1X:
                        nextSpeed = HomesteaderSpeed.Speed3X;
                        break;
                    case HomesteaderSpeed.Speed3X:
                        nextSpeed = HomesteaderSpeed.Speed5X;
                        break;
                    case HomesteaderSpeed.Speed5X:
                    case HomesteaderSpeed.Speed10X:
                    default:
                        nextSpeed = HomesteaderSpeed.Speed10X;
                        break;
                }
            }
            _lastActiveSpeed = nextSpeed;
            TimeSystem.Instance.SetSpeed(nextSpeed);
            ToastNotificationSystem.ShowInfo("Speed Changed", $"Simulation speed increased to {SpeedToString(nextSpeed)}.");
        }

        private void DecreaseSpeed()
        {
            if (TimeSystem.Instance.CurrentSpeed == HomesteaderSpeed.Pause)
            {
                return;
            }

            HomesteaderSpeed nextSpeed;
            switch (TimeSystem.Instance.CurrentSpeed)
            {
                case HomesteaderSpeed.Speed10X:
                    nextSpeed = HomesteaderSpeed.Speed5X;
                    break;
                case HomesteaderSpeed.Speed5X:
                    nextSpeed = HomesteaderSpeed.Speed3X;
                    break;
                case HomesteaderSpeed.Speed3X:
                case HomesteaderSpeed.Speed1X:
                default:
                    nextSpeed = HomesteaderSpeed.Speed1X;
                    break;
            }
            _lastActiveSpeed = nextSpeed;
            TimeSystem.Instance.SetSpeed(nextSpeed);
            ToastNotificationSystem.ShowInfo("Speed Changed", $"Simulation speed set to {SpeedToString(nextSpeed)}.");
        }

        private static string SpeedToString(HomesteaderSpeed speed)
        {
            switch (speed)
            {
                case HomesteaderSpeed.Speed1X: return "1X (Normal)";
                case HomesteaderSpeed.Speed3X: return "3X (Fast)";
                case HomesteaderSpeed.Speed5X: return "5X (Faster)";
                case HomesteaderSpeed.Speed10X: return "10X (Maximum)";
                case HomesteaderSpeed.Pause: return "Paused";
                default: return "1X";
            }
        }

        public static string GetSpeedDisplayLabel(HomesteaderSpeed speed)
        {
            switch (speed)
            {
                case HomesteaderSpeed.Pause: return "Paused";
                case HomesteaderSpeed.Speed1X: return "1x";
                case HomesteaderSpeed.Speed3X: return "3x";
                case HomesteaderSpeed.Speed5X: return "5x";
                case HomesteaderSpeed.Speed10X: return "10x";
                default: return "1x";
            }
        }

        public void OpenSettings()
        {
            if (_windowShade == null || _settingsWindow == null) return;
            if (_confirmModal != null) _confirmModal.AddToClassList("modal--hidden");
            _settingsWindow.RemoveFromClassList("window--hidden");
            _windowShade.RemoveFromClassList("window-shade--hidden");
        }

        public void CloseSettings()
        {
            if (_settingsWindow != null) _settingsWindow.AddToClassList("window--hidden");
            if (!IsModalOpen && _windowShade != null)
            {
                _windowShade.AddToClassList("window-shade--hidden");
            }
        }

        public void ToggleSettings()
        {
            if (IsSettingsOpen) CloseSettings();
            else OpenSettings();
        }

        public void ShowModal(string title, string message, System.Action onConfirm = null, System.Action onCancel = null,
            string confirmLabel = "Confirm", string cancelLabel = "Cancel", string thirdLabel = null, System.Action onThird = null)
        {
            if (_windowShade == null || _confirmModal == null) return;

            _onModalConfirm = onConfirm;
            _onModalCancel = onCancel;
            _onModalThird = onThird;

            if (_modalTitle != null) _modalTitle.text = title;
            if (_modalMessage != null) _modalMessage.text = message;

            if (_modalConfirmBtn != null)
            {
                _modalConfirmBtn.text = confirmLabel;
                _modalConfirmBtn.style.display = string.IsNullOrEmpty(confirmLabel) ? DisplayStyle.None : DisplayStyle.Flex;
            }
            if (_modalCancelBtn != null)
            {
                _modalCancelBtn.text = cancelLabel;
                _modalCancelBtn.style.display = string.IsNullOrEmpty(cancelLabel) ? DisplayStyle.None : DisplayStyle.Flex;
            }
            if (_modalThirdBtn != null)
            {
                _modalThirdBtn.text = thirdLabel;
                _modalThirdBtn.style.display = string.IsNullOrEmpty(thirdLabel) ? DisplayStyle.None : DisplayStyle.Flex;
            }

            if (_settingsWindow != null) _settingsWindow.AddToClassList("window--hidden");
            _confirmModal.RemoveFromClassList("modal--hidden");
            _windowShade.RemoveFromClassList("window-shade--hidden");
        }

        public void ShowExampleModal()
        {
            ShowModal(
                title: "Confirm Action",
                message: "Are you sure you want to discard unsaved homestead progress?",
                onConfirm: () => Debug.Log("<color=green>[HUD Modal]</color> Discard confirmed!"),
                onCancel: () => Debug.Log("<color=yellow>[HUD Modal]</color> Discard cancelled.")
            );
        }

        public void CloseModal()
        {
            _onModalConfirm = null;
            _onModalCancel = null;
            _onModalThird = null;
            if (_confirmModal != null) _confirmModal.AddToClassList("modal--hidden");
            if (!IsSettingsOpen && _windowShade != null)
            {
                _windowShade.AddToClassList("window-shade--hidden");
            }
        }

        private static bool IsShiftHeld()
        {
#if ENABLE_INPUT_SYSTEM
            var kb = UnityEngine.InputSystem.Keyboard.current;
            if (kb != null) return kb.leftShiftKey.isPressed || kb.rightShiftKey.isPressed;
#endif
            return Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        }

        public void OpenAssetSpawner()
        {
            EnsureAssetCatalogLoaded();
            if (_assetSpawnerWindow == null) return;

            _assetSpawnerWindow.RemoveFromClassList("asset-spawner-window--hidden");

            BuildAssetCategoryDropdown();
            FilterAndDisplayAssets();
        }

        public void CloseAssetSpawner()
        {
            if (_assetSpawnerWindow != null)
            {
                _assetSpawnerWindow.AddToClassList("asset-spawner-window--hidden");
            }
        }

        public void ToggleAssetSpawner()
        {
            if (IsAssetSpawnerOpen) CloseAssetSpawner();
            else OpenAssetSpawner();
        }

        private static void EnsureAssetCatalogLoaded()
        {
            if (s_assetCatalog != null && s_assetCatalog.items != null && s_assetCatalog.items.Count > 0)
                return;

            var asset = Resources.Load<TextAsset>("AssetCatalog");
            if (asset != null && !string.IsNullOrEmpty(asset.text))
            {
                try
                {
                    s_assetCatalog = JsonUtility.FromJson<AssetCatalogDatabase>(asset.text);
                }
                catch (Exception ex)
                {
                    Debug.LogError("[HudBindings] Failed deserializing AssetCatalog.json: " + ex.Message);
                }
            }

            if (s_assetCatalog == null || s_assetCatalog.items == null)
            {
                s_assetCatalog = new AssetCatalogDatabase { items = new List<AssetCatalogItem>() };
            }
        }

        private void BuildAssetCategoryDropdown()
        {
            if (_assetCategoryDropdown == null) return;
            if (_assetCategoryKeys.Count > 0) return;

            EnsureAssetCatalogLoaded();

            var categories = new List<string> { "all" };
            if (s_assetCatalog != null && s_assetCatalog.items != null)
            {
                var distinctCats = s_assetCatalog.items
                    .Select(x => x.category)
                    .Where(x => !string.IsNullOrEmpty(x))
                    .Distinct()
                    .OrderBy(x => x);
                categories.AddRange(distinctCats);
            }

            var labels = new List<string>();
            foreach (var cat in categories)
            {
                _assetCategoryKeys.Add(cat);
                labels.Add(cat.Equals("all", StringComparison.OrdinalIgnoreCase)
                    ? "All Categories"
                    : char.ToUpper(cat[0]) + cat.Substring(1));
            }

            _assetCategoryDropdown.choices = labels;
            int selected = _assetCategoryKeys.FindIndex(k => string.Equals(k, _selectedAssetCategory, StringComparison.OrdinalIgnoreCase));
            _assetCategoryDropdown.SetValueWithoutNotify(labels[Mathf.Max(0, selected)]);

            _assetCategoryDropdown.RegisterValueChangedCallback(evt =>
            {
                int idx = _assetCategoryDropdown.index;
                if (idx < 0 || idx >= _assetCategoryKeys.Count) return;
                _selectedAssetCategory = _assetCategoryKeys[idx];
                FilterAndDisplayAssets();
            });
        }

        private const float AssetTileMinWidth = 100f;
        private const float AssetTileMargin = 3f;

        // Stretches tiles so each row fills the grid width evenly (no leftover gap on the right).
        private void LayoutAssetGrid()
        {
            if (_assetGridContainer == null) return;

            float avail = _assetGridContainer.contentRect.width;
            if (avail <= 0f || float.IsNaN(avail)) return;

            float cell = AssetTileMinWidth + AssetTileMargin * 2f;
            int cols = Mathf.Max(1, Mathf.FloorToInt(avail / cell));
            float tileWidth = Mathf.Floor(avail / cols - AssetTileMargin * 2f);

            foreach (var child in _assetGridContainer.Children())
            {
                if (child.ClassListContains("asset-tile")) child.style.width = tileWidth;
            }
        }

        private void FilterAndDisplayAssets()
        {
            if (_assetGridContainer == null) return;
            EnsureAssetCatalogLoaded();

            _assetGridContainer.Clear();

            if (s_assetCatalog == null || s_assetCatalog.items == null) return;

            var filtered = s_assetCatalog.items.Where(item =>
            {
                if (!_selectedAssetCategory.Equals("all", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(item.category, _selectedAssetCategory, StringComparison.OrdinalIgnoreCase))
                {
                    return false;
                }

                if (!string.IsNullOrEmpty(_assetSearchQuery))
                {
                    bool matchName = item.name != null && item.name.IndexOf(_assetSearchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchId = item.id != null && item.id.IndexOf(_assetSearchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    bool matchDesc = item.description != null && item.description.IndexOf(_assetSearchQuery, StringComparison.OrdinalIgnoreCase) >= 0;
                    if (!matchName && !matchId && !matchDesc) return false;
                }

                return true;
            }).ToList();

            if (_assetSpawnerCountBadge != null)
            {
                _assetSpawnerCountBadge.text = $"{filtered.Count} items";
            }
            if (_assetSpawnerStatusLabel != null)
            {
                _assetSpawnerStatusLabel.text = $"Showing {filtered.Count} of {s_assetCatalog.items.Count} items";
            }

            foreach (var item in filtered)
            {
                var tile = new VisualElement();
                tile.AddToClassList("asset-tile");
                tile.tooltip = $"{item.name} ({item.id})\nCategory: {item.category}\nMax Stack: {item.max_stack}\n\nClick: Add 1\nShift+Click: Add Stack ({item.max_stack})";

                var iconEl = new VisualElement();
                iconEl.AddToClassList("asset-tile-icon");
                iconEl.pickingMode = PickingMode.Ignore;
                Texture2D tex = PhoneController.GetItemIcon(item.icon, item.id);
                if (tex != null)
                {
                    iconEl.style.backgroundImage = new StyleBackground(tex);
                }
                tile.Add(iconEl);

                var nameLabel = new Label(item.name);
                nameLabel.AddToClassList("asset-tile-name");
                nameLabel.pickingMode = PickingMode.Ignore;
                tile.Add(nameLabel);

                if (item.max_stack > 1)
                {
                    var badge = new Label(item.max_stack.ToString());
                    badge.AddToClassList("asset-tile-badge");
                    badge.pickingMode = PickingMode.Ignore;
                    tile.Add(badge);
                }

                var currentItem = item;
                tile.RegisterCallback<ClickEvent>(evt =>
                {
                    bool isShift = evt.shiftKey || (evt.modifiers & EventModifiers.Shift) != 0 || IsShiftHeld();
                    int countToAdd = isShift ? Mathf.Max(1, currentItem.max_stack) : 1;
                    int added = HudState.Active.AddItemToToolbar(currentItem.id, countToAdd, Mathf.Max(1, currentItem.max_stack));
                    if (added > 0)
                    {
                        WriteToolbar(HudState.Active);
                        ToastNotificationSystem.ShowInfo("Added to Toolbar", $"Added {added}x {currentItem.name} to toolbar.");
                    }
                    else
                    {
                        ToastNotificationSystem.ShowWarning("Toolbar Full", $"Could not add {currentItem.name}. Toolbar slots are full!");
                    }
                });

                _assetGridContainer.Add(tile);
            }

            LayoutAssetGrid();
        }

        private void Update()
        {
            if (!_wired || _root == null || _windowShade == null || _windowShade.panel == null)
            {
                ResolveReferences();
                if (!_wired) return;
            }
            if (_ownsTimeSystem)
            {
                TimeSystem.Instance.Tick(Time.deltaTime);
            }

            HandleShortcuts();
            _phone?.Tick();
            JobBoard.Tick();

            var state = HudState.Active;
            if (_enableTimeUpdates) WriteTime();
            if (_enableResourceUpdates) WriteResources(state);
            if (_enableVitalUpdates) WriteVitals(state);
            if (_enableToolbarUpdates) WriteToolbar(state);
        }

        private void WriteTime()
        {
            var snap = TimeSystem.Instance.Snapshot();
            if (_timeLineLabel != null)
            {
                _timeLineLabel.text = $"{SeasonToString(snap.Season)}  {snap.MonthName} {snap.DayOfMonth}  {TimeSystem.Instance.GetWallClock()}";
            }
            if (_speedStateLabel != null)
            {
                _speedStateLabel.text = GetSpeedDisplayLabel(snap.Speed);
            }
            if (_seasonLabel != null) _seasonLabel.text = SeasonToString(snap.Season);
            if (_dayLabel != null) _dayLabel.text = $"{snap.MonthName} {snap.DayOfMonth}";
            if (_clockLabel != null) _clockLabel.text = TimeSystem.Instance.GetWallClock();

            UpdateTimelineTape(snap.MinuteOfDay);
            UpdateWeatherTimelineTape(snap.MinuteOfDay);
        }

        private void BuildWeatherTimelineTrack()
        {
            if (_weatherTimelineTrack == null) return;
            _weatherTimelineTrack.Clear();

            int totalNodes = (TimelineIntervalCount * 2) + 1; // 17 major nodes (-32h to +32h)
            _weatherMajorNodes = new VisualElement[totalNodes];
            _weatherTimelineIcons = new VisualElement[totalNodes];

            for (int i = 0; i < totalNodes; i++)
            {
                var node = new VisualElement();
                node.AddToClassList("weather-major-node");

                // 3 intermediate hourly ticks between 4-hour major intervals
                var tick1 = new VisualElement();
                tick1.AddToClassList("timeline-tick-hour1");
                node.Add(tick1);

                var tick2 = new VisualElement();
                tick2.AddToClassList("timeline-tick-hour2");
                node.Add(tick2);

                var tick3 = new VisualElement();
                tick3.AddToClassList("timeline-tick-hour3");
                node.Add(tick3);

                // Major 4-hour tick mark directly underneath
                var majorTick = new VisualElement();
                majorTick.AddToClassList("timeline-tick-major");
                node.Add(majorTick);

                // Weather Icon added after ticks so it renders on top
                var weatherIcon = new VisualElement();
                weatherIcon.AddToClassList("weather-timeline-icon");
                node.Add(weatherIcon);

                _weatherTimelineTrack.Add(node);
                _weatherMajorNodes[i] = node;
                _weatherTimelineIcons[i] = weatherIcon;
            }
        }

        private void UpdateWeatherTimelineTape(float currentMinuteOfDay)
        {
            if (_weatherTimelineTrack == null || _weatherTimelineIcons == null) return;

            // 4-hour blocks: 240 minutes per interval
            const float minutesPerInterval = 240f;
            float currentIntervalFloat = currentMinuteOfDay / minutesPerInterval;
            int baseInterval = Mathf.FloorToInt(currentIntervalFloat);
            float intervalFrac = (currentMinuteOfDay - (baseInterval * minutesPerInterval)) / minutesPerInterval;

            // Smooth track motion based on exact fraction within the 4-hour interval
            float trackOffset = -intervalFrac * TimelinePixelsPer4Hours;
            _weatherTimelineTrack.style.translate = new Translate(trackOffset, 0f, 0f);

            var timeSystem = TimeSystem.Instance;
            var snap = timeSystem.Snapshot();
            var units = HudState.Active.Units;
            var weather = snap.Weather;
            string weatherIconId = TimeSystem.GetWeatherIconId(weather);

            // Update live current temperature in the attached offset cell
            if (_currentTempLabel != null)
            {
                _currentTempLabel.text = TimeSystem.FormatTemperature(snap.TemperatureC, units);
            }

            // Update weather icon on each 4-hour node
            for (int i = 0; i < _weatherTimelineIcons.Length; i++)
            {
                int relInterval = i - TimelineIntervalCount;
                int targetHour = ((baseInterval + relInterval) * 4) % 24;
                if (targetHour < 0) targetHour += 24;

                // Load and cache weather icon
                if (!string.IsNullOrEmpty(weatherIconId))
                {
                    if (!s_weatherCache.TryGetValue(weatherIconId, out var tex) || tex == null)
                    {
                        tex = Resources.Load<Texture2D>("HUDTree/KitSprites/weather/" + weatherIconId);
                        s_weatherCache[weatherIconId] = tex;
                    }
                    if (tex != null)
                    {
                        _weatherTimelineIcons[i].style.backgroundImage = new StyleBackground(tex);
                        _weatherTimelineIcons[i].style.display = DisplayStyle.Flex;
                    }
                }

                // Center node prominence
                if (relInterval == 0)
                {
                    _weatherMajorNodes[i].style.opacity = 1.0f;
                }
                else
                {
                    _weatherMajorNodes[i].style.opacity = 0.82f;
                }
            }
        }

        private void BuildTimelineTrack()
        {
            if (_timelineTrack == null) return;
            _timelineTrack.Clear();

            int totalNodes = (TimelineIntervalCount * 2) + 1; // 17 major nodes (-32h to +32h)
            _timelineMajorNodes = new VisualElement[totalNodes];
            _timelineCelestialIcons = new VisualElement[totalNodes];

            for (int i = 0; i < totalNodes; i++)
            {
                var node = new VisualElement();
                node.AddToClassList("timeline-major-node");

                // 3 intermediate hourly ticks between 4-hour major intervals
                var tick1 = new VisualElement();
                tick1.AddToClassList("timeline-tick-hour1");
                node.Add(tick1);

                var tick2 = new VisualElement();
                tick2.AddToClassList("timeline-tick-hour2");
                node.Add(tick2);

                var tick3 = new VisualElement();
                tick3.AddToClassList("timeline-tick-hour3");
                node.Add(tick3);

                // Major 4-hour tick mark directly underneath the celestial icon
                var majorTick = new VisualElement();
                majorTick.AddToClassList("timeline-tick-major");
                node.Add(majorTick);

                // Celestial Icon (Sun / Moon state at this 4-hour mark) added after ticks so it renders on top
                var celestialIcon = new VisualElement();
                celestialIcon.AddToClassList("timeline-celestial-icon");
                node.Add(celestialIcon);

                _timelineTrack.Add(node);
                _timelineMajorNodes[i] = node;
                _timelineCelestialIcons[i] = celestialIcon;
            }
        }

        private void UpdateTimelineTape(float currentMinuteOfDay)
        {
            if (_timelineTrack == null || _timelineCelestialIcons == null) return;

            // 4-hour blocks: 240 minutes per interval
            const float minutesPerInterval = 240f;
            float currentIntervalFloat = currentMinuteOfDay / minutesPerInterval;
            int baseInterval = Mathf.FloorToInt(currentIntervalFloat);
            float intervalFrac = (currentMinuteOfDay - (baseInterval * minutesPerInterval)) / minutesPerInterval;

            // Smooth track motion based on exact fraction within the 4-hour interval
            float trackOffset = -intervalFrac * TimelinePixelsPer4Hours;
            _timelineTrack.style.translate = new Translate(trackOffset, 0f, 0f);

            var timeSystem = TimeSystem.Instance;

            // Update celestial sun/moon icons on each 4-hour node
            for (int i = 0; i < _timelineCelestialIcons.Length; i++)
            {
                int relInterval = i - TimelineIntervalCount;
                int targetHour = ((baseInterval + relInterval) * 4) % 24;
                if (targetHour < 0) targetHour += 24;

                float sampleMinute = targetHour * 60f;
                string celestialId = timeSystem.GetCelestialIconId(sampleMinute);

                if (!string.IsNullOrEmpty(celestialId))
                {
                    if (!s_celestialCache.TryGetValue(celestialId, out var tex) || tex == null)
                    {
                        tex = Resources.Load<Texture2D>("HUDTree/KitSprites/celestial/" + celestialId);
                        s_celestialCache[celestialId] = tex;
                    }
                    if (tex != null)
                    {
                        _timelineCelestialIcons[i].style.backgroundImage = new StyleBackground(tex);
                        _timelineCelestialIcons[i].style.display = DisplayStyle.Flex;
                    }
                }

                // Center node prominence
                if (relInterval == 0)
                {
                    _timelineMajorNodes[i].style.opacity = 1.0f;
                }
                else
                {
                    _timelineMajorNodes[i].style.opacity = 0.82f;
                }
            }
        }

        private void UpdateSpeedChips(HomesteaderSpeed currentSpeed)
        {
            bool isPaused = (currentSpeed == HomesteaderSpeed.Pause);

            // Toggle pause/play button icon & tooltip to show the opposite action:
            // When game is paused -> show PLAY icon (▶) to resume
            // When game is playing -> show PAUSE icon (II) to pause
            if (_speedPause != null)
            {
                if (isPaused)
                {
                    _speedPause.text = "▶";
                    _speedPause.tooltip = "Play (Spacebar)";
                    _speedPause.RemoveFromClassList("icon-pause");
                    if (!_speedPause.ClassListContains("icon-play"))
                    {
                        _speedPause.AddToClassList("icon-play");
                    }
                }
                else
                {
                    _speedPause.text = "II";
                    _speedPause.tooltip = "Pause (Spacebar)";
                    _speedPause.RemoveFromClassList("icon-play");
                    if (!_speedPause.ClassListContains("icon-pause"))
                    {
                        _speedPause.AddToClassList("icon-pause");
                    }
                }
            }

            SetChipActive(_speedPause, isPaused);
            SetChipActive(_speed1X, currentSpeed == HomesteaderSpeed.Speed1X);
            SetChipActive(_speed3X, currentSpeed == HomesteaderSpeed.Speed3X);
            SetChipActive(_speed5X, currentSpeed == HomesteaderSpeed.Speed5X);
            SetChipActive(_speed10X, currentSpeed == HomesteaderSpeed.Speed10X);
        }

        private static void SetChipActive(Button chip, bool active)
        {
            if (chip == null) { return; }
            const string activeClass = "speed-chip--active";
            if (active)
            {
                if (!chip.ClassListContains(activeClass))
                    chip.AddToClassList(activeClass);
            }
            else
            {
                if (chip.ClassListContains(activeClass))
                    chip.RemoveFromClassList(activeClass);
            }
        }

        private void WriteResources(HudState s)
        {
            if (_resourceWater != null)
            {
                _resourceWater.text = s.FormatWater();
            }
            if (_resourceElectricity != null)
            {
                _resourceElectricity.text = s.FormatElectricity();
            }
            if (_resourceBandwidth != null)
            {
                _resourceBandwidth.text = s.FormatBandwidth();
            }
            if (_resourceFuel != null)
            {
                _resourceFuel.text = s.FormatFuel();
            }
            if (_resourceMoney != null)
            {
                _resourceMoney.text = s.FormatMoney();
            }
        }

        private void WriteVitals(HudState s)
        {
            WriteOneVital(VitalId.Wellness,
                          _vitalWellnessFill, _vitalWellnessPct, s);
            WriteOneVital(VitalId.Stamina,
                          _vitalStaminaFill, _vitalStaminaPct, s);
            WriteOneVital(VitalId.Thirst,
                          _vitalThirstFill, _vitalThirstPct, s);
            WriteOneVital(VitalId.Hunger,
                          _vitalHungerFill, _vitalHungerPct, s);
        }

        private void WriteOneVital(VitalId id,
                                    VisualElement fill,
                                    Label pctLabel,
                                    HudState s)
        {
            if (!s.Vitals.ContainsKey(id)) return;
            EnsureGradients();

            int raw = Mathf.Clamp(s.Vitals[id].Value, -100, 100);
            const float halfWidth = 40f; // Center of 80px track

            if (fill != null)
            {
                if (raw > 0)
                {
                    fill.style.display = DisplayStyle.Flex;
                    fill.style.backgroundImage = new StyleBackground(_posFillTex);
                    float fillW = (raw / 100f) * halfWidth;
                    fill.style.left = halfWidth;
                    fill.style.width = fillW;
                }
                else if (raw < 0)
                {
                    fill.style.display = DisplayStyle.Flex;
                    fill.style.backgroundImage = new StyleBackground(_negFillTex);
                    float fillW = (-raw / 100f) * halfWidth;
                    fill.style.left = halfWidth - fillW;
                    fill.style.width = fillW;
                }
                else
                {
                    // 0 = neutral balance (center): no fill visible, only center marker
                    fill.style.display = DisplayStyle.None;
                    fill.style.left = halfWidth;
                    fill.style.width = 0f;
                }
            }

            if (pctLabel != null)
            {
                pctLabel.text = _vitalsNormalizedPercent
                    ? (Mathf.RoundToInt((raw + 100f) / 2f).ToString() + "%")
                    : (raw == 0 ? "0%" : (raw.ToString("+0;-0") + "%"));
            }
        }

        private void WriteToolbar(HudState s)
        {
            for (int i = 0; i < _toolbarSlots.Length; i++)
            {
                var slot = _toolbarSlots[i];
                if (slot == null) { continue; }
                if (i == s.SelectedSlot)
                {
                    if (!slot.ClassListContains("tool-slot--selected"))
                        slot.AddToClassList("tool-slot--selected");
                }
                else
                {
                    if (slot.ClassListContains("tool-slot--selected"))
                        slot.RemoveFromClassList("tool-slot--selected");
                }
                if (i < s.Toolbar.Count)
                {
                    var data = s.Toolbar[i];
                    var label = _toolbarSlotLabels[i];
                    if (label != null)
                    {
                        label.text = data.Count > 1
                            ? "x" + data.Count.ToString()
                            : "";
                    }

                    if (data.Count > 0 && !string.IsNullOrEmpty(data.IconId))
                    {
                        var tex = PhoneController.GetItemIcon(data.IconId + ".png", data.IconId);
                        slot.style.backgroundImage = tex != null ? new StyleBackground(tex) : null;
                    }
                    else
                    {
                        slot.style.backgroundImage = null;
                    }
                }
                else
                {
                    slot.style.backgroundImage = null;
                    var label = _toolbarSlotLabels[i];
                    if (label != null) label.text = "";
                }
            }
        }

        public void RefreshToolbar()
        {
            WriteToolbar(HudState.Active);
        }

        private static string SeasonToString(HomesteaderSeason s)
        {
            switch (s)
            {
                case HomesteaderSeason.Spring: return "Spring";
                case HomesteaderSeason.Summer: return "Summer";
                case HomesteaderSeason.Autumn: return "Autumn";
                case HomesteaderSeason.Winter: return "Winter";
                default: return "Summer";
            }
        }
    }

    [System.Serializable]
    public class AssetCatalogDatabase
    {
        public List<AssetCatalogItem> items;
    }

    [System.Serializable]
    public class AssetCatalogItem
    {
        public string id;
        public string name;
        public string category;
        public string description;
        public string icon;
        public int max_stack;
    }
}
