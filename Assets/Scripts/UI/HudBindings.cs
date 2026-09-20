// HudBindings.cs - drive HUD label values from HudState + TimeSystem.
//
// Each frame this MonoBehaviour:
//   1. ticks the TimeSystem by Time.deltaTime
//   2. reads HudState.Active for vitals / resources / held asset
//   3. matches known Label / VisualElement / Button names in the
//      live UXML tree and writes values into them
//
// It also handles speed chip clicks (button names below) and the
// selected-toolbar-slot class toggling.
//
// The bindings look for these names in the active UIDocument.
//
//   Time:           SeasonLabel, DayLabel, ClockLabel
//   Resources:      ResourceWaterLabel, ResourceElectricityLabel,
//                   ResourceBandwidthLabel, ResourceFuelLabel
//   Vitals (kit):   VitalWellnessLabel, VitalStaminaLabel,
//                   VitalThirstLabel, VitalHungerLabel
//   Held asset:     HoldingLabel, HeldNameLabel, HeldCountLabel
//   Toolbar slots:  ToolbarSlot0..ToolbarSlot9 (VisualElement)
//   Speed chips:    SpeedPause, Speed1X, Speed3X, Speed5X, Speed9X
//                   (Button - their clicked events drive TimeSystem.SetSpeed)
//
// Items not present are silently skipped so the bindings stay
// defensive against missing UXML chunks.

using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    [RequireComponent(typeof(UIDocument))]
    public sealed class HudBindings : MonoBehaviour
    {
        [SerializeField] private bool _enableTimeUpdates = true;
        [SerializeField] private bool _enableResourceUpdates = true;
        [SerializeField] private bool _enableVitalUpdates = true;
        [SerializeField] private bool _enableHeldAssetUpdates = true;
        [SerializeField] private bool _enableToolbarUpdates = true;

        [Tooltip("Ticking is on unless paused. Use the speed chips in the HUD " +
                 "to flip between Pause/1x/3x/5x/9x at runtime.")]
        [SerializeField] private bool _ownsTimeSystem = true;

        private UIDocument _doc;
        private VisualElement _root;

        private Label _seasonLabel;
        private Label _dayLabel;
        private Label _clockLabel;
        private Label _resourceWater;
        private Label _resourceElectricity;
        private Label _resourceBandwidth;
        private Label _resourceFuel;
        private Label _vitalWellness;
        private Label _vitalStamina;
        private Label _vitalThirst;
        private Label _vitalHunger;
        private Label _holdingLabel;
        private Label _heldNameLabel;
        private Label _heldCountLabel;
        private VisualElement[] _toolbarSlots = new VisualElement[10];
        private Button _speedPause;
        private Button _speed1X;
        private Button _speed3X;
        private Button _speed5X;
        private Button _speed9X;

        private bool _wired;

        private void Awake()
        {
            _doc = GetComponent<UIDocument>();
        }

        private void OnEnable()
        {
            ResolveReferences();
        }

        private void ResolveReferences()
        {
            if (_doc == null) _doc = GetComponent<UIDocument>();
            if (_doc == null) { return; }
            _root = _doc.rootVisualElement;
            if (_root == null) { return; }

            _seasonLabel   = Q<Label>("SeasonLabel");
            _dayLabel      = Q<Label>("DayLabel");
            _clockLabel    = Q<Label>("ClockLabel");
            _resourceWater       = Q<Label>("ResourceWaterLabel");
            _resourceElectricity = Q<Label>("ResourceElectricityLabel");
            _resourceBandwidth   = Q<Label>("ResourceBandwidthLabel");
            _resourceFuel        = Q<Label>("ResourceFuelLabel");
            _vitalWellness = Q<Label>("VitalWellnessLabel");
            _vitalStamina  = Q<Label>("VitalStaminaLabel");
            _vitalThirst   = Q<Label>("VitalThirstLabel");
            _vitalHunger   = Q<Label>("VitalHungerLabel");
            _holdingLabel  = Q<Label>("HoldingLabel");
            _heldNameLabel = Q<Label>("HeldNameLabel");
            _heldCountLabel = Q<Label>("HeldCountLabel");

            for (int i = 0; i < _toolbarSlots.Length; i++)
            {
                _toolbarSlots[i] = Q<VisualElement>("ToolbarSlot" + i.ToString());
            }

            _speedPause = Q<Button>("SpeedPause");
            _speed1X    = Q<Button>("Speed1X");
            _speed3X    = Q<Button>("Speed3X");
            _speed5X    = Q<Button>("Speed5X");
            _speed9X    = Q<Button>("Speed9X");

            WireSpeedChips();
            _wired = true;
        }

        private T Q<T>(string name) where T : VisualElement
        {
            if (_root == null) { return null; }
            return _root.Q<T>(name);
        }

        private void WireSpeedChips()
        {
            if (_speedPause != null) _speedPause.clicked += () => TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Pause);
            if (_speed1X != null) _speed1X.clicked += () => TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed1X);
            if (_speed3X != null) _speed3X.clicked += () => TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed3X);
            if (_speed5X != null) _speed5X.clicked += () => TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed5X);
            if (_speed9X != null) _speed9X.clicked += () => TimeSystem.Instance.SetSpeed(HomesteaderSpeed.Speed9X);
        }

        private void Update()
        {
            if (!_wired || _root == null)
            {
                ResolveReferences();
                return;
            }

            if (_ownsTimeSystem)
            {
                TimeSystem.Instance.Tick(Time.deltaTime);
            }

            var state = HudState.Active;

            if (_enableTimeUpdates) WriteTime();
            if (_enableResourceUpdates) WriteResources(state);
            if (_enableVitalUpdates) WriteVitals(state);
            if (_enableHeldAssetUpdates) WriteHeldAsset(state);
            if (_enableToolbarUpdates) WriteToolbar(state);
        }

        private void WriteTime()
        {
            var snap = TimeSystem.Instance.Snapshot();
            if (_seasonLabel != null) _seasonLabel.text = SeasonToString(snap.Season);
            if (_dayLabel != null) _dayLabel.text = "Day " + snap.DayOfYear.ToString();
            if (_clockLabel != null) _clockLabel.text = TimeSystem.Instance.GetWallClock();
        }

        private void WriteResources(HudState s)
        {
            if (_resourceWater != null && s.Resources.ContainsKey(ResourceId.Water))
            {
                var r = s.Resources[ResourceId.Water];
                _resourceWater.text = HudState.FormatResourceAmount(r.Amount, r.Unit);
            }
            if (_resourceElectricity != null && s.Resources.ContainsKey(ResourceId.Electricity))
            {
                var r = s.Resources[ResourceId.Electricity];
                _resourceElectricity.text = HudState.FormatResourceAmount(r.Amount, r.Unit);
            }
            if (_resourceBandwidth != null && s.Resources.ContainsKey(ResourceId.Bandwidth))
            {
                var r = s.Resources[ResourceId.Bandwidth];
                _resourceBandwidth.text = HudState.FormatResourceAmount(r.Amount, r.Unit);
            }
            if (_resourceFuel != null && s.Resources.ContainsKey(ResourceId.Fuel))
            {
                var r = s.Resources[ResourceId.Fuel];
                _resourceFuel.text = HudState.FormatResourceAmount(r.Total, r.Unit);
            }
        }

        private void WriteVitals(HudState s)
        {
            if (_vitalWellness != null && s.Vitals.ContainsKey(VitalId.Wellness))
                _vitalWellness.text = HudState.FormatVitalPercent(s.Vitals[VitalId.Wellness].Value);
            if (_vitalStamina != null && s.Vitals.ContainsKey(VitalId.Stamina))
                _vitalStamina.text = HudState.FormatVitalPercent(s.Vitals[VitalId.Stamina].Value);
            if (_vitalThirst != null && s.Vitals.ContainsKey(VitalId.Thirst))
                _vitalThirst.text = HudState.FormatVitalPercent(s.Vitals[VitalId.Thirst].Value);
            if (_vitalHunger != null && s.Vitals.ContainsKey(VitalId.Hunger))
                _vitalHunger.text = HudState.FormatVitalPercent(s.Vitals[VitalId.Hunger].Value);
        }

        private void WriteHeldAsset(HudState s)
        {
            if (_holdingLabel != null) _holdingLabel.text = "Holding";
            if (_heldNameLabel != null)
            {
                _heldNameLabel.text = string.IsNullOrEmpty(s.HeldAssetId)
                    ? "(nothing)" : s.HeldAssetId;
            }
            if (_heldCountLabel != null)
            {
                int slot = Mathf.Clamp(s.SelectedSlot, 0, s.Toolbar.Count - 1);
                var data = s.Toolbar[slot];
                _heldCountLabel.text = (data.Count > 1)
                    ? "x" + data.Count.ToString() : "";
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
            }
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
}
