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

        /// <summary>The HUD's UI Toolkit root (null until the HUD is built); extra HUD elements such as the map attach here.</summary>
        public VisualElement Root => _root;

        private Label _timeLineLabel;
        private Label _speedStateLabel;
        private VisualElement _weatherIcon;
        private VisualElement _celestialIcon;
        private Label _seasonLabel;
        private VisualElement _seasonIcon;
        private static readonly Dictionary<string, Texture2D> s_seasonTextures = new Dictionary<string, Texture2D>();
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
        private Label _activeItemHint;
        private VisualElement _activeItemHintRow;

        // Speed chips
        private Button _speedPause;
        private Button _speed1X;
        private Button _speed3X;
        private Button _speed5X;
        private Button _speed10X;
        private HomesteaderSpeed _lastActiveSpeed = HomesteaderSpeed.Speed1X;

        // Window & Modal Elements
        private VisualElement _windowShade;
        private Button _testModalBtn;

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
        private DropdownField _builtCategoryDropdown;   // the dropdown the category list was built into

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

            // The UIDocument's TemplateContainer is a full-screen overlay that sits
            // on top of the minimap in child order. Its inner ScreenRoot already
            // has picking-mode="Ignore", but the TemplateContainer wrapper itself
            // defaults to Position, which swallows pointer/wheel events over the
            // entire screen. Set it to Ignore so events fall through to the
            // minimap and other siblings; the actual interactive HUD elements are
            // children of ScreenRoot and still receive events through their own
            // pickingMode.
            for (int i = 0; i < _root.childCount; i++)
            {
              if (_root[i] is TemplateContainer tc)
                  tc.pickingMode = PickingMode.Ignore;
            }

            // WASD / arrows are walking keys, not UI navigation. The default UI input module turns them
            // into NavigationMoveEvents that move keyboard focus, which can land on a TextField (for
            // example inside the phone) and make KeyboardCaptured true - the character then stops until
            // focus moves on. Cancel navigation moves everywhere except while a text field is being typed in.
            _root.RegisterCallback<NavigationMoveEvent>(evt =>
            {
                if (IsTextInputFocused()) return;
                UiEvents.Swallow(evt);
            }, TrickleDown.TrickleDown);
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
            _seasonIcon = Q<VisualElement>("SeasonIcon");
            _dayLabel = Q<Label>("DayLabel");
            _clockLabel = Q<Label>("ClockLabel");
            _resourceWater = Q<Label>("ResourceWaterLabel");
            _resourceElectricity = Q<Label>("ResourceElectricityLabel");
            _resourceBandwidth = Q<Label>("ResourceBandwidthLabel");
            _resourceFuel = Q<Label>("ResourceFuelLabel");
            _resourceMoney = Q<Label>("ResourceMoneyLabel");
            SetUpResourceTips();

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
                    _toolbarSlots[i].Clickable().RegisterCallback<ClickEvent>(evt =>
                    {
                        if (_toolbarDragEnded) { _toolbarDragEnded = false; return; }   // the click that ends a drag is not a selection
                        SelectToolbarSlot(slotIndex);
                    });
                    WireToolbarDrag(_toolbarSlots[i], slotIndex);
                }
            }

            // Hint above the toolbar: the real name of the item in the active slot.
            var toolbarRow = Q<VisualElement>("ToolbarSlots");
            if (toolbarRow != null && toolbarRow.parent != null)
            {
                _activeItemHintRow = new VisualElement { name = "ActiveItemHintRow", pickingMode = PickingMode.Ignore };
                _activeItemHintRow.AddToClassList("active-item-hint-row");
                _activeItemHint = new Label { name = "ActiveItemHint", pickingMode = PickingMode.Ignore };
                _activeItemHint.AddToClassList("active-item-hint");
                _activeItemHint.style.display = DisplayStyle.None;   // shown by WriteToolbar once an item is active
                _activeItemHintRow.Add(_activeItemHint);
                toolbarRow.parent.Add(_activeItemHintRow);
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
            _testModalBtn = Q<Button>("TestModalBtn");

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

            // Wind indicator on the left of the weather timeline.
            _windSpeedLabel = Q<Label>("WindSpeedLabel");
            _windDirLabel = Q<Label>("WindDirLabel");
            var windHolder = Q<VisualElement>("WindArrowHolder");
            if (windHolder != null)
            {
                windHolder.Clear();
                _windArrow = new WindArrowElement();
                _windArrow.style.width = 14;
                _windArrow.style.height = 14;
                windHolder.Add(_windArrow);
            }

            _phone = new PhoneController(_root,
                (title, message, onConfirm, onCancel) => ShowModal(title, message, onConfirm, onCancel));

            // Asset Spawner initialization
            _assetSpawnerWindow = Q<VisualElement>("AssetSpawnerWindow");
            _assetSpawnerCloseBtn = Q<Button>("AssetSpawnerCloseBtn");
            _assetSpawnerCountBadge = Q<Label>("AssetSpawnerCountBadge");
            _assetSpawnerStatusLabel = Q<Label>("AssetSpawnerStatusLabel");
            _assetCategoryDropdown = Q<DropdownField>("AssetCategoryDropdown");
            if (_assetCategoryDropdown != null) PopupStyles.Ensure(_assetCategoryDropdown);   // its list is built at the panel root
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
                WindowPositions.MakeDraggable(_assetSpawnerWindow, spawnerHeader, "asset_spawner");
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
                    }
                });
            }

            // Make windows draggable by their header
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
        /// <summary>The frame in which Esc closed something (a text field's focus, a window, the phone); the welcome menu leaves that Esc alone.</summary>
        public static int EscapeHandledFrame = -1;

        /// <summary>True while the phone is up (the first person view frees the mouse for it).</summary>
        public bool IsPhoneOpen => _phone != null && _phone.IsOpen;

        public static bool KeyboardCaptured =>
            Instance != null && (Instance.IsModalOpen || Instance.IsAssetSpawnerOpen || Instance.IsTextInputFocused());

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
            // Block all input while the loading modal is shown.
            if (WelcomeMenuController.IsLoading) return;

#if ENABLE_INPUT_SYSTEM
            var kb = UnityEngine.InputSystem.Keyboard.current;
            bool phoneOpen = _phone != null && _phone.IsOpen;
            if (kb != null)
            {
                if (kb.escapeKey.wasPressedThisFrame)
                {
                    EscapeHandledFrame = Time.frameCount;   // the welcome menu (which also listens to Esc) must not open on top of this
                    if (!BlurFocusedTextInput())
                    {
                        if (IsAssetSpawnerOpen) CloseAssetSpawner();
                        else if (IsModalOpen) CloseModal();
                        else if (ContainerPanel.CloseOpen()) { }
                        else if (Homesteader.Kitchen.MealBuilderPanel.CloseOpen()) { }
                        else if (Homesteader.Kitchen.MealsPanel.CloseOpen()) { }
                        else if (Homesteader.Growth.FenceBuilder.CancelPlan()) { }
                        else if (Homesteader.Growth.PathBuilder.CancelPlan()) { }
                        else if (Homesteader.Growth.LotBuilder.CancelPlan()) { }
                        else if (Homesteader.Growth.AreaTidy.Cancel()) { }
                        else if (phoneOpen) _phone.Close();
                        else EscapeHandledFrame = -1;   // nothing to close: Esc is the welcome menu's
                    }
                }
                // A focused window / text field owns the keyboard: no hotkeys reach the game
                else if (KeyboardCaptured)
                {
                }
                else if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.TogglePhone))
                {
                    _phone?.Toggle();
                }
                else if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.ToggleContainer) && !phoneOpen)
                {
                    ContainerPanel.Toggle(_root);
                }
                // Speed Control Shortcuts (rebindable in Settings > Controls)
                else
                {
                    if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PauseTime))
                    {
                        TogglePausePlay();
                    }
                    else if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.SpeedUp))
                    {
                        IncreaseSpeed();
                    }
                    else if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.SpeedDown))
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
                        // Delete: empty the active slot (the items are removed, not dropped)
                        else if (kb.deleteKey.wasPressedThisFrame) DeleteSelectedSlotItems();
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
                    else if (phoneOpen) _phone.Close();
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
                if (Input.GetKeyDown(KeyCode.Delete) && !phoneOpen && !IsAssetSpawnerOpen)
                {
                    DeleteSelectedSlotItems();
                }
                else if (Input.GetKeyDown(KeyCode.Space))
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
            if (!isPaused && !isCtrl && Mathf.Abs(scrollDelta) > 0.01f && !KeyboardCaptured && !phoneOpen && !MiniMap.PointerOver)
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

        /// <summary>Every catalog entry (the phone builds its shops from this).</summary>
        public static List<AssetCatalogItem> CatalogItems
        {
            get
            {
                EnsureAssetCatalogLoaded();
                return s_assetCatalog?.items ?? new List<AssetCatalogItem>();
            }
        }

        /// <summary>The catalog entry for an item id, or null.</summary>
        public static AssetCatalogItem GetCatalogItem(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return null;
            EnsureAssetCatalogLoaded();
            List<AssetCatalogItem> items = s_assetCatalog?.items;
            if (items == null) return null;
            // an index by id (the first of an id wins, like List.Find): this is asked per placed object per frame (PalletDeck, KitchenRun, ContainerRules ...), and the catalog has thousands of items
            if (s_catalogIndex == null || s_indexFor != items || s_indexCount != items.Count)
            {
                s_catalogIndex = new Dictionary<string, AssetCatalogItem>(items.Count);
                foreach (AssetCatalogItem it in items) if (it != null && !string.IsNullOrEmpty(it.id)) s_catalogIndex.TryAdd(it.id, it);
                s_indexFor = items;
                s_indexCount = items.Count;
            }
            return s_catalogIndex.TryGetValue(itemId, out AssetCatalogItem found) ? found : null;
        }

        private static Dictionary<string, AssetCatalogItem> s_catalogIndex;
        private static List<AssetCatalogItem> s_indexFor;
        private static int s_indexCount;

        /// <summary>How many uses one of the item holds (a seed packet: 20); 1 for everything else.</summary>
        public static int UsesPerItem(string itemId)
        {
            AssetCatalogItem item = GetCatalogItem(itemId);
            return item != null && item.uses_per_item > 1 ? item.uses_per_item : 1;
        }

        /// <summary>Catalog max stack size for an item id (64 when unknown).</summary>
        public static int GetMaxStack(string itemId)
        {
            EnsureAssetCatalogLoaded();
            var item = GetCatalogItem(itemId);
            return item != null && item.max_stack > 0 ? item.max_stack : 64;
        }

        /// <summary>Catalog display name for an item id (the id itself when unknown).</summary>
        /// <summary>
        /// The name the player SEES: the stored plain name plus what is generated from the item's data. A pack shows its quantity with an x, then its weight, "Cement Bag Pallet x10 (200 lb)";
        /// a material or packaged good shows its weight in the player's units, "Cement Bag (20 lb)"; anything else is just the name.
        /// Used in the stores, the active slot's description, WAILA and the construction lists.
        /// </summary>
        public static string GetDisplayName(string itemId)
        {
            EnsureAssetCatalogLoaded();
            var item = GetCatalogItem(itemId);
            if (item == null || string.IsNullOrEmpty(item.name)) return itemId;
            string shown = item.name;
            if (item.pack_quantity > 1) shown += " x" + item.pack_quantity;   // a pack shows how many it holds, then its weight
            if (item.max_power_w > 0f)                                         // a power source or regulator shows its rated power, "Standby Generator (10 kW)"
                shown += " (" + (item.max_power_w >= 1000f ? (Mathf.Round(item.max_power_w / 100f) / 10f).ToString("0.#") + " kW" : Mathf.RoundToInt(item.max_power_w) + " W") + ")";
            if (item.max_current_a > 0f) shown += " (" + item.max_current_a.ToString("0.#") + " A)";   // a breaker, fuse or disconnect shows its rated current, "DC Circuit Breaker (32 A)"
            if (item.liquid_capacity_l > 0f) shown += " (" + UnitFormat.Volume(item.liquid_capacity_l) + ")";   // a liquid container shows how many liters it holds
            else if (item.display_weight && item.weight_kg > 0f) shown += " (" + UnitFormat.WeightLabel(item.weight_kg) + ")";
            return shown;
        }

        public static string GetItemName(string itemId)
        {
            EnsureAssetCatalogLoaded();
            var item = GetCatalogItem(itemId);
            return item != null && !string.IsNullOrEmpty(item.name) ? item.name : itemId;
        }

        // ------------------------------------------------------------------ dragging items between toolbar slots

        private VisualElement _dragGhost;
        private int _dragFrom = -1;
        private Vector2 _dragStart;
        private bool _dragging, _toolbarDragEnded;
        private const float DragThreshold = 6f;

        /// <summary>Press on a slot that holds something, move past a few pixels and a copy of its icon follows the pointer; let go over another slot and the two swap.</summary>
        private void WireToolbarDrag(VisualElement slot, int index)
        {
            slot.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.button != 0) return;
                _toolbarDragEnded = false;
                HudState hs = HudState.Active;
                if (hs == null || index >= hs.Toolbar.Count || hs.Toolbar[index].Count <= 0 || string.IsNullOrEmpty(hs.Toolbar[index].IconId)) return;
                _dragFrom = index;
                _dragStart = evt.position;
                _dragging = false;
                slot.CapturePointer(evt.pointerId);
            });
            slot.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (_dragFrom != index || !slot.HasPointerCapture(evt.pointerId)) return;
                if (!_dragging)
                {
                    if (((Vector2)evt.position - _dragStart).magnitude < DragThreshold) return;
                    _dragging = true;
                    HudState hs = HudState.Active;
                    ToolbarSlotData d = hs.Toolbar[index];
                    _dragGhost = new VisualElement { pickingMode = PickingMode.Ignore };
                    _dragGhost.style.position = Position.Absolute;
                    _dragGhost.style.width = 56;
                    _dragGhost.style.height = 56;
                    _dragGhost.style.opacity = 0.85f;
                    var tex = PhoneController.GetItemIcon(d.IconId + ".png", d.IconId);
                    if (tex != null) _dragGhost.style.backgroundImage = new StyleBackground(tex);
                    (_root ?? slot.panel.visualTree).Add(_dragGhost);
                    slot.AddToClassList("tool-slot--dragging");
                }
                Vector2 local = _dragGhost.parent.WorldToLocal(evt.position);
                _dragGhost.style.left = local.x - 28;
                _dragGhost.style.top = local.y - 28;
            });
            slot.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (_dragFrom != index) return;
                if (slot.HasPointerCapture(evt.pointerId)) slot.ReleasePointer(evt.pointerId);
                bool wasDragging = _dragging;
                _dragFrom = -1;
                _dragging = false;
                slot.RemoveFromClassList("tool-slot--dragging");
                if (_dragGhost != null) { _dragGhost.RemoveFromHierarchy(); _dragGhost = null; }
                if (!wasDragging) return;
                _toolbarDragEnded = true;
                for (int j = 0; j < _toolbarSlots.Length; j++)
                {
                    if (j == index || _toolbarSlots[j] == null || !_toolbarSlots[j].worldBound.Contains(evt.position)) continue;
                    if (!TryDropIntoContainerSlot(index, j)) SwapToolbarSlots(index, j);   // dropped on a sack, basket or toolbox: it goes in (when it takes it); on anything else the two swap
                    break;
                }
            });
            slot.RegisterCallback<PointerCaptureOutEvent>(evt =>
            {
                if (_dragFrom != index) return;   // the capture was taken away (a menu opened): drop the drag without swapping
                _dragFrom = -1;
                _dragging = false;
                slot.RemoveFromClassList("tool-slot--dragging");
                if (_dragGhost != null) { _dragGhost.RemoveFromHierarchy(); _dragGhost = null; }
            });
        }

        /// <summary>
        /// A slot dragged onto a slot that holds a CONTAINER (a sack, a basket, a toolbox): the items go into it, as many as it takes by weight and only what it accepts (its manifest's
        /// container.accepts); the rest stays where it was. True when the drop was for the container (also when it was refused: the toast says why), false when the target is not a
        /// container or the dragged thing is itself one (then the two slots swap as usual).
        /// </summary>
        private bool TryDropIntoContainerSlot(int from, int to)
        {
            HudState hs = HudState.Active;
            hs.EnsureToolbarSlots();
            if (from < 0 || to < 0 || from >= hs.Toolbar.Count || to >= hs.Toolbar.Count) return false;
            ToolbarSlotData src = hs.Toolbar[from], box = hs.Toolbar[to];
            if (src.Count <= 0 || string.IsNullOrEmpty(src.IconId) || box.Count <= 0 || string.IsNullOrEmpty(box.IconId)) return false;
            if (!ContainerRules.IsContainer(box.IconId) || ContainerRules.IsContainer(src.IconId)) return false;
            if (box.Contents == null) box.Contents = new List<ContainerStack>();
            string boxName = GetItemName(box.IconId), itemName = GetItemName(src.IconId);
            if (!ContainerRules.Accepts(box.IconId, src.IconId, box.Contents)) { ToastNotificationSystem.ShowInfo(boxName, boxName + " does not take " + itemName + "."); return true; }
            bool liquidState = LiquidRules.IsLiquidContainer(src.IconId) && (!string.IsNullOrEmpty(src.LiquidId) || Mathf.Abs(src.WireUsed) > 0.0001f);   // a filled or part-used jar goes in with what it holds
            if (!liquidState && Mathf.Abs(src.WireUsed) > 0.0001f) { ToastNotificationSystem.ShowInfo(boxName, "A part-used " + itemName + " cannot go in: it would lose what is used."); return true; }
            int moved;
            if (liquidState)
            {
                moved = ContainerRules.AddWithState(box.IconId, box.Contents, src.IconId, src.LiquidId, src.WireUsed);
                if (moved > 0) { src.WireUsed = 0f; src.LiquidId = ""; }
            }
            else moved = ContainerRules.Add(box.IconId, box.Contents, src.IconId, src.Count);
            if (moved <= 0) { ToastNotificationSystem.ShowInfo(boxName, boxName + " is full."); return true; }
            src.Count -= moved;
            hs.Toolbar[from] = src.Count > 0 ? src : ToolbarSlotData.Empty();
            hs.Toolbar[to] = box;
            WriteToolbar(hs);
            return true;
        }

        private void SwapToolbarSlots(int a, int b)
        {
            HudState hs = HudState.Active;
            hs.EnsureToolbarSlots();
            if (a < 0 || b < 0 || a >= hs.Toolbar.Count || b >= hs.Toolbar.Count) return;
            ToolbarSlotData tmp = hs.Toolbar[a];
            hs.Toolbar[a] = hs.Toolbar[b];
            hs.Toolbar[b] = tmp;
            // the active slot follows the item it held
            int selected = hs.SelectedSlot == a ? b : hs.SelectedSlot == b ? a : hs.SelectedSlot;
            hs.SelectSlot(selected);
            WriteToolbar(hs);
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
            }
            else
            {
                _lastActiveSpeed = TimeSystem.Instance.CurrentSpeed;
                TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Pause);
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

            _confirmModal.RemoveFromClassList("modal--hidden");
            _windowShade.RemoveFromClassList("window-shade--hidden");
        }

        public void ShowExampleModal()
        {
            ShowModal(
                title: "Confirm Action",
                message: "Are you sure you want to discard unsaved homestead progress?",
                onConfirm: () => Dbg.Log("<color=green>[HUD Modal]</color> Discard confirmed!"),
                onCancel: () => Dbg.Log("<color=yellow>[HUD Modal]</color> Discard cancelled.")
            );
        }

        public void CloseModal()
        {
            _onModalConfirm = null;
            _onModalCancel = null;
            _onModalThird = null;
            if (_confirmModal != null) _confirmModal.AddToClassList("modal--hidden");
            if (_windowShade != null)
            {
                _windowShade.AddToClassList("window-shade--hidden");
            }
        }

        private static void DropAssetInFront(string itemId, int count)
        {
            var ped = PedController.Current;
            if (ped == null) return;
            Vector3 facing = Quaternion.Euler(0f, ped.transform.eulerAngles.y - ped.modelRotationOffset, 0f) * Vector3.forward;
            Vector3 front = ped.transform.position + facing * 1.5f;
            int dropped = 0;
            for (int i = 0; i < count; i++)
                if (i == 0 && Homesteader.Growth.WheelbarrowPush.TryDropPlaced(itemId, front)) dropped++;   // a wheelbarrow is put down standing
                else if (Homesteader.Growth.WorldItem.TryDrop(itemId, front)) dropped++;
            if (dropped <= 0) ToastNotificationSystem.ShowWarning("Can't drop", "That asset has no model or icon to drop.");
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
            WindowPositions.Place(_assetSpawnerWindow, "asset_spawner");   // centered the first time, then where it was left

            BuildAssetCategoryDropdown();
            FilterAndDisplayAssets();
        }

        public void CloseAssetSpawner()
        {
            if (_assetSpawnerWindow != null)
            {
                WindowPositions.Remember(_assetSpawnerWindow, "asset_spawner");
                _assetSpawnerWindow.AddToClassList("asset-spawner-window--hidden");
            }
        }

        public void ToggleAssetSpawner()
        {
            if (IsAssetSpawnerOpen) CloseAssetSpawner();
            else OpenAssetSpawner();
        }

        /// <summary>
        /// With "Reload Domain" off in Enter Play Mode, statics survive between plays: the catalog read in an earlier play (before
        /// the kit regenerated AssetCatalog.json) would be used again. Read it afresh at the start of every play.
        /// </summary>
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetCatalogCache() { s_assetCatalog = null; }

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
            // built once per dropdown: when the HUD's elements are made again (a new dropdown) it is filled again, never left empty
            if (_assetCategoryKeys.Count > 0 && _builtCategoryDropdown == _assetCategoryDropdown && _assetCategoryDropdown.choices != null && _assetCategoryDropdown.choices.Count() > 0) return;
            _assetCategoryKeys.Clear();
            _builtCategoryDropdown = _assetCategoryDropdown;

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

                var nameLabel = new Label(GetDisplayName(item.id));   // the full name and its quantity / weight / capacity
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
                tile.Clickable().RegisterCallback<ClickEvent>(evt =>
                {
                    bool isShift = evt.shiftKey || (evt.modifiers & EventModifiers.Shift) != 0 || IsShiftHeld();
                    int countToAdd = isShift ? Mathf.Max(1, currentItem.max_stack) : 1;
                    if (evt.altKey || (evt.modifiers & EventModifiers.Alt) != 0)
                    {
                        // Alt+Click: one straight onto the ground in front of the player (Alt+Shift+Click: ten)
                        DropAssetInFront(currentItem.id, isShift ? 10 : 1);
                        return;
                    }
                    // Straight into a toolbar slot, never into a container on the toolbar: with a toolbox there, a spawned tool used to vanish into it.
                    int added = HudState.Active.AddItemToToolbar(currentItem.id, countToAdd, Mathf.Max(1, currentItem.max_stack), useContainers: false);
                    if (added > 0)
                    {
                        WriteToolbar(HudState.Active);
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
            UpdateWindIndicator();
            // The labels, bars and toolbar are rewritten a few times a second, not every frame (every write formats strings and dirties the layout);
            // actions that change the toolbar call RefreshToolbar themselves.
            float now = Time.unscaledTime;
            if (_enableTimeUpdates && now >= _nextTimeWrite) { _nextTimeWrite = now + 0.1f; WriteTime(); }
            if (_enableResourceUpdates && now >= _nextResourceWrite) { _nextResourceWrite = now + 0.25f; WriteResources(state); }
            if (_enableVitalUpdates && now >= _nextVitalWrite) { _nextVitalWrite = now + 0.25f; WriteVitals(state); }
            if (_enableToolbarUpdates && now >= _nextToolbarWrite) { _nextToolbarWrite = now + 0.05f; WriteToolbar(state); }
        }

        private float _nextTimeWrite, _nextResourceWrite, _nextVitalWrite, _nextToolbarWrite;

        // ------------------------------------------------------------------ wind indicator

        private Label _windSpeedLabel;
        private Label _windDirLabel;
        private WindArrowElement _windArrow;
        private int _windShownMph = -1;
        private string _windShownDir;
        private Camera _windCam;
        private static readonly string[] CompassPoints = { "N", "NE", "E", "SE", "S", "SW", "W", "NW" };

        /// <summary>Wind arrow (points where the wind blows, relative to the screen so it matches the grass and the rain),
        /// speed in mph and the compass point the wind comes FROM, like a forecast.</summary>
        private void UpdateWindIndicator()
        {
            if (_windArrow == null) return;
            var weather = WeatherEffectsManager.Instance;
            if (weather == null) return;

            float mps = weather.WindSpeedMps;
            int mph = Mathf.RoundToInt(mps * 2.23694f);
            bool calm = mph < 1;

            if (_windCam == null) _windCam = Camera.main;
            float yaw = _windCam != null ? _windCam.transform.eulerAngles.y : 0f;

            // Heading the wind blows toward, clockwise from +Z (north); then relative to where the camera looks.
            Vector2 dir = weather.WindDirection;
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            _windArrow.style.rotate = new Rotate(new Angle(heading - yaw, AngleUnit.Degree));
            _windArrow.SetStrength(calm ? 0f : Mathf.Clamp01(mps / Mathf.Max(1f, weather.WindStormSpeedMps)) * 0.8f + 0.2f);

            float from = Mathf.Repeat(heading + 180f, 360f);
            string point = CompassPoints[Mathf.RoundToInt(from / 45f) % 8];
            string dirText = calm ? "" : point;
            if (mph == _windShownMph && dirText == _windShownDir) return;
            _windShownMph = mph;
            _windShownDir = dirText;
            if (_windSpeedLabel != null) _windSpeedLabel.text = calm ? "Calm" : mph + " mph";
            if (_windDirLabel != null) _windDirLabel.text = dirText;
        }

        private void WriteTime()
        {
            var snap = TimeSystem.Instance.Snapshot();
            if (_timeLineLabel != null)
            {
                _timeLineLabel.text = $"{snap.MonthName} {snap.DayOfMonth}  {TimeSystem.Instance.GetWallClock()}";
            }
            if (_speedStateLabel != null)
            {
                _speedStateLabel.text = GetSpeedDisplayLabel(snap.Speed);
            }
            if (_seasonLabel != null) _seasonLabel.text = SeasonToString(snap.Season);
            if (_seasonIcon != null)
            {
                string seasonKey = SeasonToString(snap.Season).ToLowerInvariant();
                if (!s_seasonTextures.TryGetValue(seasonKey, out var seasonTex) || seasonTex == null)
                {
                    seasonTex = Resources.Load<Texture2D>("HUDTree/KitSprites/seasons/season_" + seasonKey);
                    s_seasonTextures[seasonKey] = seasonTex;
                }
                if (seasonTex != null) _seasonIcon.style.backgroundImage = new StyleBackground(seasonTex);
            }
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

        // ------------------------------------------------------------------ the resource breakdowns on hover

        private VisualElement _resTip;
        private Label _resTipText;
        // ------------------------------------------------------------------ a choice window (the sawmill asks what lumber to cut)

        private VisualElement _choice;
        public bool ChoiceMenuOpen { get { return _choice != null && _choice.parent != null; } }

        /// <summary>
        /// A "pick from a list" window beside the world, built to the design system's per-window checklist (docs/UI_DESIGN_SYSTEM.md section 10): the window chrome (<c>window</c>,
        /// the accent edge, a 36 px header with the amber title and the shared <c>hs-close</c>), a body with a gauge (label medium 13, an 8 px bar), a hint (italic 11 muted), the
        /// section title (<c>window-section-title</c>: bold amber 13) and list rows 40 px high (the item's icon, its name in medium 13, hover = <c>--c-raised</c>) each with one
        /// <c>hs-btn</c> (30 px, centred text). A disabled button says why in its tooltip. Floating and draggable, it does not block the game: X, Escape (the caller) or
        /// walking away closes it, and it remembers where it was left. The <c>choice-*</c> classes (HudUI.uss) are layout and the row hover only.
        /// </summary>
        public void ShowChoiceMenu(string title, string gaugeText, float gaugeFraction, string hint, string section, List<ChoiceOption> options, System.Action<int> onPick)
        {
            CloseChoiceMenu();
            if (_root == null) return;
            var window = new VisualElement { name = "ChoiceWindow" };
            window.AddToClassList("window");
            window.AddToClassList("choice-window");
            window.style.position = Position.Absolute;
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            window.Add(edge);
            var header = new VisualElement();
            header.AddToClassList("window-header");
            header.tooltip = "Drag to move";
            var heading = new Label(title) { pickingMode = PickingMode.Ignore };
            heading.AddToClassList("window-title");
            var close = new Button(CloseChoiceMenu) { text = "X", tooltip = "Close (Escape)" };
            close.AddToClassList("hs-close");
            header.Add(heading);
            header.Add(close);
            window.Add(header);
            WindowPositions.MakeDraggable(window, header, "choice");
            var body = new VisualElement();
            body.AddToClassList("window-body");
            window.Add(body);
            if (!string.IsNullOrEmpty(gaugeText))
            {
                var cap = new Label(gaugeText);
                cap.AddToClassList("choice-gauge");
                body.Add(cap);
                var bar = new VisualElement();
                bar.AddToClassList("choice-bar");
                var fill = new VisualElement();
                fill.AddToClassList("choice-bar-fill");
                fill.style.width = new Length(Mathf.Clamp01(gaugeFraction) * 100f, LengthUnit.Percent);
                bar.Add(fill);
                body.Add(bar);
            }
            if (!string.IsNullOrEmpty(hint))
            {
                var note = new Label(hint);
                note.AddToClassList("choice-hint");
                body.Add(note);
            }
            if (!string.IsNullOrEmpty(section))
            {
                var h = new Label(section);
                h.AddToClassList("window-section-title");
                body.Add(h);
            }
            for (int k = 0; k < options.Count; k++)
            {
                int index = k;
                ChoiceOption opt = options[k];
                var row = new VisualElement();
                row.AddToClassList("choice-row");
                var icon = new VisualElement { pickingMode = PickingMode.Ignore };
                icon.AddToClassList("choice-icon");
                Texture2D tex = string.IsNullOrEmpty(opt.IconId) ? null : PhoneController.GetItemIcon(opt.IconId + ".png", opt.IconId);
                if (tex != null) icon.style.backgroundImage = new StyleBackground(tex);
                row.Add(icon);
                var name = new Label(opt.Label) { pickingMode = PickingMode.Ignore };
                name.AddToClassList("choice-name");
                row.Add(name);
                var b = new Button(() => { if (!opt.Enabled) return; CloseChoiceMenu(); onPick?.Invoke(index); }) { text = opt.Action ?? "Choose" };
                b.AddToClassList("hs-btn");
                b.AddToClassList("choice-btn");
                b.SetEnabled(opt.Enabled);
                if (!opt.Enabled && !string.IsNullOrEmpty(opt.WhyNot)) { row.tooltip = opt.WhyNot; b.tooltip = opt.WhyNot; }   // a disabled control says why
                row.Add(b);
                body.Add(row);
            }
            VisualElement wallpaper = _root.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == _root) _root.Insert(_root.IndexOf(wallpaper), window);
            else _root.Add(window);
            WindowPositions.Place(window, "choice");   // centred the first time, then where it was left
            _choice = window;
        }

        public void CloseChoiceMenu()
        {
            if (_choice == null) return;
            WindowPositions.Remember(_choice, "choice");
            _choice.RemoveFromHierarchy();
            _choice = null;
        }

        /// <summary>One row of <see cref="ShowChoiceMenu"/>: the item whose icon it shows, its text, the button's label, whether it can be pressed and, when not, why.</summary>
        public struct ChoiceOption
        {
            public string Label, IconId, Action, WhyNot;
            public bool Enabled;
            public ChoiceOption(string label, string iconId, string action = "Choose", bool enabled = true, string whyNot = null) { Label = label; IconId = iconId; Action = action; Enabled = enabled; WhyNot = whyNot; }
        }

        private string _resTipFor;   // "water", "fuel" or "bandwidth" while the pointer is over that resource

        /// <summary>Hovering the water or the fuel (icon or amount) shows what it is made of: potable / non-potable water; gasoline, diesel, propane.</summary>
        private void SetUpResourceTips()
        {
            if (_root == null) return;
            _resTip = new VisualElement { name = "ResourceTip", pickingMode = PickingMode.Ignore };
            _resTip.style.position = Position.Absolute;
            _resTip.style.backgroundColor = new Color(0.07f, 0.086f, 0.114f, 0.94f);
            _resTip.style.borderTopLeftRadius = _resTip.style.borderTopRightRadius = _resTip.style.borderBottomLeftRadius = _resTip.style.borderBottomRightRadius = 4;
            _resTip.style.paddingLeft = _resTip.style.paddingRight = 10;
            _resTip.style.paddingTop = _resTip.style.paddingBottom = 6;
            _resTip.style.display = DisplayStyle.None;
            _resTipText = new Label { pickingMode = PickingMode.Ignore };
            _resTipText.AddToClassList("resource-amount");
            _resTipText.style.fontSize = 15;
            _resTipText.style.whiteSpace = WhiteSpace.Normal;
            _resTip.Add(_resTipText);
            _root.Add(_resTip);
            Hook(_resourceWater, "water");
            Hook(_resourceFuel, "fuel");
            Hook(_resourceBandwidth, "bandwidth");
            Hook(_resourceElectricity, "electricity");
        }

        private void Hook(Label amount, string what)
        {
            VisualElement row = amount != null ? amount.parent : null;   // the icon and the amount together
            if (row == null) return;
            row.RegisterCallback<PointerEnterEvent>(_ => { _resTipFor = what; FillResourceTip(); PlaceResourceTip(row); });
            row.RegisterCallback<PointerLeaveEvent>(_ => { if (_resTipFor == what) { _resTipFor = null; _resTip.style.display = DisplayStyle.None; } });
        }

        private void PlaceResourceTip(VisualElement row)
        {
            _resTip.style.display = DisplayStyle.Flex;
            Rect r = row.worldBound;
            Vector2 local = _root.WorldToLocal(new Vector2(r.xMin, r.yMax + 4f));
            _resTip.style.left = Mathf.Max(4f, Mathf.Min(local.x, _root.layout.width - 230f));
            _resTip.style.top = local.y;
        }

        private void FillResourceTip()
        {
            if (_resTip == null || _resTipFor == null) return;
            if (_resTipFor == "electricity")
            {
                // the five things drawing the most power, most first
                var top = Homesteader.Growth.WireNetwork.TopLoads(5, out float total);
                var sb = new System.Text.StringBuilder();
                sb.Append("Drawing: ").Append(Homesteader.Growth.SolarSun.Power(total));
                if (top.Count == 0) sb.Append("\nNothing is drawing power");
                foreach (var u in top) sb.Append("\n").Append(u.Key).Append(": ").Append(Homesteader.Growth.SolarSun.Power(u.Value));
                _resTipText.text = sb.ToString();
            }
            else if (_resTipFor == "bandwidth")
            {
                // the five devices using the most, most first
                var sb = new System.Text.StringBuilder();
                sb.Append("In use: ").Append(ResViewData.Mbps(Homesteader.Growth.Net.UsedMbps)).Append(" of ").Append(ResViewData.Mbps(Homesteader.Growth.Net.TotalMbps));
                var top = Homesteader.Growth.Net.TopUsers(5);
                if (top.Count == 0) sb.Append("\nNothing is using it");
                foreach (var u in top) sb.Append('\n').Append(u.Key).Append(": ").Append(ResViewData.Mbps(u.Value));
                _resTipText.text = sb.ToString();
            }
            else if (_resTipFor == "water")
                _resTipText.text = "Potable: " + UnitFormat.Volume(Homesteader.Growth.WireNetwork.PotableL) + "\nNon-potable: " + UnitFormat.Volume(Homesteader.Growth.WireNetwork.RawWaterL);
            else
                _resTipText.text = "Gasoline: " + UnitFormat.Volume(Homesteader.Growth.WireNetwork.GasolineL) + "\nDiesel: " + UnitFormat.Volume(Homesteader.Growth.WireNetwork.DieselL)
                                 + "\nPropane: " + UnitFormat.Volume(Homesteader.Growth.WireNetwork.PropaneL);
        }

        private void WriteResources(HudState s)
        {
            FillResourceTip();   // the breakdown keeps up while it is shown
            if (_resourceWater != null)
            {
                s.SetResourceAmount(ResourceId.Water, Homesteader.Growth.WireNetwork.PotableL);   // the HUD shows the potable water stored (clean water in tanks and containers)
                _resourceWater.text = s.FormatWater();
            }
            if (_resourceElectricity != null)
            {
                s.SetResourceAmount(ResourceId.Electricity, Homesteader.Growth.WireNetwork.TotalStoredWh() * 0.0036f);   // the HUD shows what the batteries hold (1 Wh = 0.0036 MJ)
                _resourceElectricity.text = s.FormatElectricity();
            }
            if (_resourceBandwidth != null)
            {
                Connectivity.PhoneInUse = _phone != null && _phone.IsOpen;
                Connectivity.Refresh();   // keeps the phone's link (and what it takes of the bandwidth) up to date while the phone is away
                s.SetResourceAmount(ResourceId.Bandwidth, Homesteader.Growth.Net.AvailableMbps);   // what the dish brings in now (the weather takes some), less what the cameras and TVs use
                _resourceBandwidth.text = s.FormatBandwidth();
            }
            if (_resourceFuel != null)
            {
                s.SetResourceAmount(ResourceId.Fuel, Homesteader.Growth.WireNetwork.FuelL);   // gasoline and diesel stored in tanks, drums and cans
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
            const float halfWidth = 37f; // Center of 74px track

            if (fill != null)
            {
                if (raw > 0)
                {
                    fill.style.display = DisplayStyle.Flex;
                    fill.style.backgroundImage = StyleKeyword.None;
                    fill.style.backgroundColor = new Color(69f / 255f, 209f / 255f, 192f / 255f, 1f); // Precision teal
                    float fillW = (raw / 100f) * halfWidth;
                    fill.style.left = halfWidth;
                    fill.style.width = fillW;
                }
                else if (raw < 0)
                {
                    fill.style.display = DisplayStyle.Flex;
                    fill.style.backgroundImage = StyleKeyword.None;
                    fill.style.backgroundColor = new Color(229f / 255f, 72f / 255f, 77f / 255f, 1f); // Precision ember
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

        private static void SetSlotIcon(VisualElement slot, Texture2D tex)
        {
            var icon = slot.Q<VisualElement>(className: "tool-slot-icon");
            if (icon == null) return;
            icon.style.backgroundImage = tex != null ? new StyleBackground(tex) : new StyleBackground();
        }

        private void WriteToolbar(HudState s)
        {
            if (_activeItemHint != null)
            {
                string hint = "";
                if (s.SelectedSlot >= 0 && s.SelectedSlot < s.Toolbar.Count)
                {
                    var active = s.Toolbar[s.SelectedSlot];
                    if (active.Count > 0 && !string.IsNullOrEmpty(active.IconId))
                    {
                        hint = GetDisplayName(active.IconId) + $"  x{active.Count}";
                        if (ContainerRules.IsContainer(active.IconId))
                            hint += $"  ({UnitFormat.WeightPair(ContainerRules.Used(active.Contents), ContainerRules.Capacity(active.IconId))})";
                    }
                }
                _activeItemHint.text = hint;
                _activeItemHint.style.display = hint.Length > 0 ? DisplayStyle.Flex : DisplayStyle.None;
            }

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
                bool blueprint = i < s.Toolbar.Count && s.Toolbar[i].Count > 0 && Blueprints.IsBlueprint(s.Toolbar[i].IconId);
                if (blueprint != slot.ClassListContains("tool-slot--blueprint")) slot.EnableInClassList("tool-slot--blueprint", blueprint);
                if (i < s.Toolbar.Count)
                {
                    var data = s.Toolbar[i];
                    var label = _toolbarSlotLabels[i];
                    if (label != null)
                    {
                        int per = data.Count > 0 ? UsesPerItem(data.IconId) : 1;
                        label.text = per > 1
                            ? (data.Count > 1 ? "x" + data.Count + "  " : "") + HudState.UsesLeft(data, per)   // a seed packet: the seeds left, and how many packets
                            : data.Count > 1
                                ? "x" + data.Count.ToString()
                                : "";
                    }

                    if (data.Count > 0 && !string.IsNullOrEmpty(data.IconId))
                    {
                        var tex = PhoneController.GetItemIcon(data.IconId + ".png", data.IconId);
                        SetSlotIcon(slot, tex);
                    }
                    else
                    {
                        SetSlotIcon(slot, null);
                    }
                }
                else
                {
                    SetSlotIcon(slot, null);
                    var label = _toolbarSlotLabels[i];
                    if (label != null) label.text = "";
                }
            }
        }

        /// <summary>The Delete key: removes whatever is in the active toolbar slot.</summary>
        private void DeleteSelectedSlotItems()
        {
            HudState hs = HudState.Active;
            if (hs != null && hs.SelectedSlot >= 0 && hs.SelectedSlot < hs.Toolbar.Count && Blueprints.IsBlueprint(hs.Toolbar[hs.SelectedSlot].IconId))
            {
                ToastNotificationSystem.ShowInfo("Blueprint", "A blueprint is yours for good and cannot be removed.");
                return;
            }
            ToolbarSlotData? removed = HudState.Active.ClearSelectedSlot();
            if (removed == null) return;
            RefreshToolbar();
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

    /// <summary>One shop's listing of an item (properties.stores in the manifest): the shop id, the chip label, how it is counted, its price.</summary>
    [System.Serializable]
    public class StoreListing
    {
        public string store;
        public string category;
        public string unit;
        public float price;
    }

    /// <summary>
    /// One node of a stage's materials (see tools/recipe_format.py). A LINE: this many of this item, #tag or ~equivalency (item_id, quantity).
    /// A SECTION (items is set): mode "all" needs every child, mode "any" needs ANY ONE child in full; uses / not_uses make it conditional
    /// (it only applies when an earlier line was paid with an item matching the spec, or was not).
    /// </summary>
    [System.Serializable]
    public class ConstructionLine
    {
        public string item_id;
        public float quantity = 1;
        public float per_depth_m;                // a well: the line needs quantity + per_depth_m x the well's depth
        public string section;
        public string mode;
        public string uses;
        public string not_uses;
        public List<ConstructionLine> items;
        public bool IsSection => items != null && items.Count > 0;
    }

    [System.Serializable]
    public class ConstructionToolGroup { public List<string> tools; }

    /// <summary>One stage of a structure under construction (foundation, framing, walls, complete): what it takes and how big it is.</summary>
    [System.Serializable]
    public class ConstructionStageData
    {
        public string name;
        public string item_id;                         // the stage's own item (its model, when it has one)
        public float width, depth, height;             // metres
        public List<ConstructionLine> recipe;          // materials consumed to build this stage (an item id or a #tag)
        public List<string> build_clips;               // the ped's work clips while this stage is built, one after the other (Dig, Hoe, Push_RT, Fixing_Kneeling_RT ...); empty = the default
        public string build_motion;                    // how the stage's model moves while it is built: tilt_up (the node Mast is raised), lift (the node Yaw is hoisted), spin_up (the node Rotor is fitted and spun up); empty = none
        public List<ConstructionToolGroup> tool_groups; // the player needs ANY ONE tool of EACH group in the toolbar; tools are not consumed
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
        public int uses_per_item;                                   // how many uses ONE item holds (a seed packet: 20 seeds); 0 = one. The slot's WireUsed counts the uses taken from the one on top
        public float weight_kg;
        public float build_speed;                  // tools: 1 = the baseline build time, below 1 slower (a hammer), above 1 faster (0 = not set = 1)
        public int pack_quantity;                  // a stack / pallet / case / bundle of N: shown as "Name (N)"
        public bool display_weight;                // materials and packaged goods: shown as "Name (9 kg)"
        public bool support_surface;                                // a placed one carries items on top (a pallet, see PalletDeck.cs)
        public string deck_heights;                                 // a shelving unit: the height of each shelf's top face in metres, lowest first, comma separated
        public string look_target;                                  // comma list of roof, walls, interior, floor, chimney, foundation: what it styles as a construction material (StructureLook.cs)
        public string look_style;                                   // a foundation item: poured, block, brick or stilts
        public string fence_style;                                  // wood or wire: a fence material (FenceBuilder.cs)
        public float fence_panel_m, fence_height_m;
        public string fence_post_item;                              // the post one of these fences is built on
        public bool is_blueprint;                                   // bought once, starts a build, never used up (Blueprints.cs)
        public string path_material_item;                           // the material a path or road blueprint lays (taken per path_m_per_item metres)
        public string path_kind;                                    // path or road: a surface laid as a curved route (PathBuilder.cs)
        public float path_width_m, path_m_per_item;
        public string path_style;
        public string lot_style;                                    // dirt, gravel, asphalt or concrete: a lot blueprint (LotBuilder.cs)
        public string lot_material_item;                            // the material a lot blueprint lays
        public float lot_m2_per_item;
        public string lot_binder_item;                              // a lot that is a MIX (asphalt: aggregate + bitumen): the second material, an item id or a ~equivalency
        public float lot_binder_m2_per_item;                        // square metres one unit of the binder covers                               // square metres one item of it covers
        public float gate_width_m;                                  // > 0: a gate
        public string gate_style;
        public float hunger_restore, thirst_restore, stamina_restore, wellness_modifier;   // food and drink: what eating one (or drinking 0.25 L of a liquid) gives the vitals (Kitchen/Consumption.cs)
        public string leaves_item;                                  // what is left when it is eaten (a soup leaves its bowl, a plated meal its plate)
        public float burn_minutes;                                  // > 0: fireplace fuel that burns this many game minutes (Fireplace.cs)
        public bool lights_fires;                                   // a lighter: right click a fireplace with it to light it
        public string look_color;                                   // #RRGGBB
        public float look_smoothness, look_metallic;
        public List<StoreListing> store_listings;                   // the phone shops that sell it (null = not for sale)
        public List<ConstructionStageData> construction_stages;   // a structure built in stages (see ConstructionSite.cs)
        public float liquid_capacity_l;            // > 0: holds one liquid by volume (see Liquids.cs)
        public List<string> liquid_accepts;        // liquid ids or #tags it takes; empty = any liquid
        public string liquid_color;                // a liquid item: its fluid colour as #RRGGBB
        public float liquid_opacity_pct;           // a liquid item: 100 = fully opaque (milk), about 70 for fuels
        public bool liquid_flammable;
        public string liquid_filled_with;          // a liquid container sold full: the liquid in it (TankSticker.cs names it on a tank)
        public float liquid_filled_l;
        public float container_capacity_kg;        // > 0: this item is a container (see Containers.cs)
        public int container_stacking_limit;       // identical placed containers stack this high in the world (1 / 0 = they do not)
        public List<string> fruiting_tools;        // the 'fruiting' add-on schema: what picks it (tools / #tags), what one fruit gives, days to regrow
        public List<string> fruiting_drops;
        public float fruiting_regrow_days;
        public bool container_disposable;    // a placed one disappears when its last item is taken out (cardboard boxes)
        public bool container_single_type;   // takes only one kind of item at a time (crates)
        public float[] container_fill_region;   // xmin, xmax, ymin, ymax, zmin, zmax as fractions of the model bounds (a container whose opening is only part of the model: a wheelbarrow tub)
        public string wire_role;                 // solar_panel | wall_entry | dc_breaker | mppt | battery | inverter | ac_panel | busbar: a device the solar chain wires together (Wiring.cs)
        public string wire_kind;                 // a coil or spool of wire: dc_indoor | dc_outdoor | ac
        public bool pressurized;                 // a pressure tank (or a water heater): the taps draw from it with no pump running
        public float heater_w;                   // a water heater: its element's watts
        public string filter_stage;              // a water filter: sediment | carbon | uv
        public float flow_lph;                   // a well pump: liters an hour it lifts
        public bool is_well;                     // a drilled well structure (docs/WELLS.md)
        public float sewage_capacity_l;          // a septic tank structure: the liters it holds (docs/SEPTIC.md)
        public float leach_lpd;                  // a leach field: liters a game day that soak away
        public float leach_storage_l;            // a leach field: liters its trenches hold
        public float base_value;                 // what the item is worth (properties.base_value): the Market pays a share of it
        public float water_per_use_l;            // a fixture (sink, toilet, shower, washer): liters one use takes and sends down the drain
        public float fuel_lpm;                   // a standby generator: liters of fuel a minute at full load (category_fields.fuel_consumption_l_per_min)
        public string attach_item;               // what fits on it (a well: its sub panel)
        public float water_capacity_l;           // a water tank: how much a well's pipe can fill it with
        public float power_draw_w;               // a corded electric tool: watts it draws while building (it needs a generator at the site)
        public float power_radius_tiles;         // a portable generator: it powers everything that needs electricity this many tiles round it
        public float panel_width_m, panel_depth_m;   // a solar mount: its panel seen from above
        public float panel_offset_m;             // a solar mount: how far up its panel sits
        public float panel_tilt_deg;             // a solar mount: the panel's tilt about the X axis
        public float capacity_wh;                // a battery: energy capacity in watt-hours
        public float voltage_v;                  // a battery: nominal voltage
        public float wire_length_m;              // its length in metres
        public float max_power_w;                // electricity items: rated power in watts (a wind turbine's output, a battery's continuous power)
        public float max_current_a;              // breakers, fuses, disconnects: rated current in amps (shown in the name)
        public bool run_snap;                    // a kitchen run piece: snaps to its neighbours and the wall, filler strips (KitchenRun.cs)
        public bool shelf;                       // a wall shelf: things are stood on it (Shelf.cs)
        public bool sawmill;                     // a stationary sawmill: logs laid on its track are cut into lumber (Sawmill.cs)
        public bool roof_mount;                  // a ground item that may also be put up on a roof, upright, turned freely (a dish, a yagi, an access point)
        public int net_ports;                    // network gear: how many cables it takes (a router: its LAN ports)
        public bool poe;                         // ... and its ports give 15 W each over the cable
        public bool poe_powered;                 // a device that runs from its cable: it only goes on a PoE port (a camera, an access point, a yagi)
        public int rack_units;                   // a rackmount router or switch: the units it takes in a wall rack
        public int rack_capacity_u;              // a rack: the units it holds
        public float range_m;                    // internet gear: how far its radio reaches (Wi-Fi, a yagi link, a cellular booster)
        public float bandwidth_mbps;             // internet gear: its rated throughput
        public bool net_source;                  // ... and it brings the connection in by itself (a satellite dish, a directional antenna): its bandwidth is the homestead's
        public float bandwidth_usage_mbps;       // a device that uses the internet (a TV): what it takes
        public int container_max_items;          // > 0: at most this many items in all (a battery rack has this many slots), whatever their weight
        public float container_slot_pitch_m;     // > 0: the contents are drawn as the real item models, one above the other this far apart (a battery rack)
        public float container_slot_start_m;     // where the first slot stands: height above the bottom of the container's model
        public bool container_pushable;          // a push item (a wheelbarrow): grabbed and pushed, not picked up
        public bool container_show_fill = true;   // draw what is inside as blocks (open crates and baskets; closed boxes turn it off)
        public List<string> container_accepts;     // categories, #tags or item ids it accepts; empty = anything
    }
}
