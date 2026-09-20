// HudState.cs - runtime state for the Homesteader HUD.
//
// Ported from assets/hud_kit/runtime/state.py to C#. Used by
// HudBindings to drive the live HUD labels (time, vitals, resources,
// held asset, toolbar slot selection).
//
// The Python source kept the dataclasses plain; we use serialized
// structs here so a HudState can be field-edited in the inspector
// if we later move it to a ScriptableObject.
//
// HudState is *not* a MonoBehaviour - it's plain C# data that lives
// behind a singleton accessor (HudState.Active) so bindings can read
// the same instance regardless of scene lifecycle. The HudBindings
// MonoBehaviour writes state changes and reads snapshots every frame.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.UI
{
    public enum VitalId
    {
        Wellness,
        Stamina,
        Thirst,
        Hunger,
    }

    [Serializable]
    public struct Vital
    {
        public VitalId Id;
        // value is signed (-100..+100). Negative = need, zero = balanced,
        // positive = surplus. The Python source used the same convention.
        public int Value;

        public Vital(VitalId id, int value)
        {
            Id = id;
            Value = value;
        }
    }

    [Serializable]
    public struct ToolbarSlotData
    {
        public string IconId;     // matches an asset_id from the catalog; "" = empty
        public int Count;        // 0 = empty slot

        public static ToolbarSlotData Empty()
        {
            return new ToolbarSlotData { IconId = string.Empty, Count = 0 };
        }
    }

    public enum ResourceId
    {
        Water,
        Electricity,
        Bandwidth,
        Fuel,
    }

    [Serializable]
    public class Resource
    {
        public ResourceId Id;
        public float Amount;
        public string Unit;
        // For Fuel, this looks like { "gasoline": 12.5, "diesel": 0.0, ... }.
        // For other resources the dict stays empty.
        public Dictionary<string, float> Subspecies = new Dictionary<string, float>();

        public Resource() {}
        public Resource(ResourceId id, float amount, string unit)
        {
            Id = id;
            Amount = amount;
            Unit = unit ?? string.Empty;
        }

        public Resource(ResourceId id, string unit, Dictionary<string, float> subspecies)
        {
            Id = id;
            Amount = 0f;
            Unit = unit ?? string.Empty;
            Subspecies = subspecies ?? new Dictionary<string, float>();
        }

        // Total amount; if subspecies are filled (compound resource like fuel),
        // sum them; otherwise return Amount.
        public float Total
        {
            get
            {
                if (Subspecies != null && Subspecies.Count > 0)
                {
                    float sum = 0f;
                    foreach (var v in Subspecies.Values) sum += v;
                    return sum;
                }
                return Amount;
            }
        }
    }

    [Serializable]
    public class HudState
    {
        // Vitals - default values match the Python source defaults.
        public Dictionary<VitalId, Vital> Vitals = new Dictionary<VitalId, Vital>
        {
            { VitalId.Wellness, new Vital(VitalId.Wellness, 50) },
            { VitalId.Stamina,  new Vital(VitalId.Stamina,   30) },
            { VitalId.Thirst,   new Vital(VitalId.Thirst,    10) },
            { VitalId.Hunger,   new Vital(VitalId.Hunger,   -20) },
        };

        // Resources - defaults match assets/hud_kit/runtime/state.py.
        public Dictionary<ResourceId, Resource> Resources = new Dictionary<ResourceId, Resource>
        {
            { ResourceId.Water,       new Resource(ResourceId.Water, 120.5f, "L") },
            { ResourceId.Electricity, new Resource(ResourceId.Electricity, 2400.0f, "Wh") },
            { ResourceId.Bandwidth,   new Resource(ResourceId.Bandwidth, 24.5f, "Mbps") },
            { ResourceId.Fuel,        new Resource(
                ResourceId.Fuel, "L",
                new Dictionary<string, float>
                {
                    { "gasoline", 12.5f },
                    { "diesel",   3.0f },
                    { "kerosene", 0.5f },
                    { "propane", 0.0f },
                })
            },
        };

        // Toolbar - 10 slots, 4 symbolically populated to match the stock
        // example: wooden_axe, fishing_rod, apple x4, log_oak x12, cooked_fish x2.
        // The rest stay empty.
        public const int ToolbarSize = 10;
        public List<ToolbarSlotData> Toolbar = new List<ToolbarSlotData>();

        public int SelectedSlot = 0;
        public string HeldAssetId = "wooden_axe";

        public HudState()
        {
            RebuildDefaultToolbar();
        }

        private void RebuildDefaultToolbar()
        {
            Toolbar.Clear();
            Toolbar.Add(new ToolbarSlotData { IconId = "wooden_axe",   Count = 1 });
            Toolbar.Add(ToolbarSlotData.Empty());
            Toolbar.Add(new ToolbarSlotData { IconId = "fishing_rod",  Count = 1 });
            Toolbar.Add(ToolbarSlotData.Empty());
            Toolbar.Add(new ToolbarSlotData { IconId = "apple",        Count = 4 });
            Toolbar.Add(ToolbarSlotData.Empty());
            Toolbar.Add(new ToolbarSlotData { IconId = "log_oak",      Count = 12 });
            Toolbar.Add(ToolbarSlotData.Empty());
            Toolbar.Add(new ToolbarSlotData { IconId = "cooked_fish",  Count = 2 });
            Toolbar.Add(ToolbarSlotData.Empty());
        }

        // Singleton accessor. The static instance stays alive across the
        // lifetime of the game process so MonoBehaviour-public bindings can
        // share state without a [SerializeField] round-trip every scene.
        private static HudState s_active;
        public static HudState Active
        {
            get
            {
                if (s_active == null) s_active = new HudState();
                return s_active;
            }
        }

        public void UpdateVital(Vital v)
        {
            Vitals[v.Id] = v;
        }

        public void UpdateResource(Resource r)
        {
            Resources[r.Id] = r;
        }

        public void SelectSlot(int idx)
        {
            idx = Mathf.Clamp(idx, 0, Toolbar.Count - 1);
            SelectedSlot = idx;
            var slot = Toolbar[idx];
            HeldAssetId = slot.IconId ?? string.Empty;
        }

        // Format a vital Value as a percent string for HUD labels.
        // The Python source convention was to display the level as 0..100
        // (centered around 0). We offset by +100 so the raw -100..+100
        // range scales to 0..200.
        public static string FormatVitalPercent(int value)
        {
            int pct = Mathf.Clamp(value + 100, 0, 200) / 2;
            return pct.ToString() + "%";
        }

        // Format a resource value as a "120 L" / "2.40k Wh" string.
        // 4 digits and up are rendered with a k-suffix.
        public static string FormatResourceAmount(float amount, string unit)
        {
            if (amount >= 1000f)
            {
                float k = amount / 1000f;
                return k.ToString("0.00") + "k " + unit;
            }
            return amount.ToString("0.##") + " " + unit;
        }
}
}
