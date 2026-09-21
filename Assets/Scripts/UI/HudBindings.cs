// HudBindings.cs - drive HUD widgets from HudState + TimeSystem.
//
// Each frame this MonoBehaviour ticks the TimeSystem and writes
// state into the live UIDocument. The widgets are free-floating
// components under Resources/HUDTree/ - HudBindings uses the Q()
// query to find each label/visualElement by name.

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
        [SerializeField] private bool _enableToolbarUpdates = true;
        [SerializeField] private bool _ownsTimeSystem = true;

        [Tooltip("When true, write percent (0..100) to the label. " +
                 "Else write raw signed value as +N%/-N%.")]
        [SerializeField] private bool _vitalsNormalizedPercent = true;

        private UIDocument _doc;
        private VisualElement _root;

        private Label _seasonLabel;
        private Label _dayLabel;
        private Label _clockLabel;

        private Label _resourceWater;
        private Label _resourceElectricity;
        private Label _resourceBandwidth;
        private Label _resourceFuel;

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

            _seasonLabel = Q<Label>("SeasonLabel");
            _dayLabel = Q<Label>("DayLabel");
            _clockLabel = Q<Label>("ClockLabel");
            _resourceWater = Q<Label>("ResourceWaterLabel");
            _resourceElectricity = Q<Label>("ResourceElectricityLabel");
            _resourceBandwidth = Q<Label>("ResourceBandwidthLabel");
            _resourceFuel = Q<Label>("ResourceFuelLabel");

            _vitalWellnessFill = Q<VisualElement>("VitalWellnessFill");
            _vitalStaminaFill  = Q<VisualElement>("VitalStaminaFill");
            _vitalThirstFill   = Q<VisualElement>("VitalThirstFill");
            _vitalHungerFill   = Q<VisualElement>("VitalHungerFill");
            _vitalWellnessPct = Q<Label>("VitalWellnessPct");
            _vitalStaminaPct  = Q<Label>("VitalStaminaPct");
            _vitalThirstPct   = Q<Label>("VitalThirstPct");
            _vitalHungerPct   = Q<Label>("VitalHungerPct");

            for (int i = 0; i < _toolbarSlots.Length; i++)
            {
                _toolbarSlots[i] = Q<VisualElement>("ToolbarSlot" + i.ToString());
                _toolbarSlotLabels[i] = Q<Label>("ToolSlotLabel" + i.ToString());
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
            int raw = s.Vitals[id].Value;
            // Signed scale -100..+100 maps to bar percent 0..100.
            int barPercent = Mathf.Clamp(raw + 100, 0, 200) / 2;
            if (fill != null)
            {
                fill.style.width = new StyleLength(
                    new Length(barPercent, LengthUnit.Percent));
            }
            if (pctLabel != null)
            {
                pctLabel.text = _vitalsNormalizedPercent
                    ? (barPercent.ToString() + "%")
                    : (raw.ToString("+0;-0") + "%");
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
