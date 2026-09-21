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
        Money,
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

        public Resource() { }
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

    public enum UnitSystem
    {
        Metric,
        Imperial,
    }

    [Serializable]
    public class HudState
    {
        public UnitSystem Units = UnitSystem.Metric;

        public const float LitersToGallons = 0.264172f;
        public const float GallonsToLiters = 3.785412f;
        public const float MegajoulesToKilowattHours = 1f / 3.6f;
        public const float KilowattHoursToMegajoules = 3.6f;
        public const float MetersToFeet = 3.28084f;
        public const float FeetToMeters = 0.3048f;
        public const float MetersToInches = 39.3701f;

        // Vitals - signed scale (-100..+100), start at +100 (full health, full stamina, etc.).
        public Dictionary<VitalId, Vital> Vitals = new Dictionary<VitalId, Vital>
        {
            { VitalId.Wellness, new Vital(VitalId.Wellness, 100) },
            { VitalId.Stamina,  new Vital(VitalId.Stamina,  100) },
            { VitalId.Thirst,   new Vital(VitalId.Thirst,   100) },
            { VitalId.Hunger,   new Vital(VitalId.Hunger,   100) },
        };

        // Resources - a new game starts with nothing: every resource at 0.
        // Units are kept so the HUD labels still format correctly once the
        // player acquires something.
        public Dictionary<ResourceId, Resource> Resources = new Dictionary<ResourceId, Resource>
        {
            { ResourceId.Water,       new Resource(ResourceId.Water, 0f, "L") },
            { ResourceId.Electricity, new Resource(ResourceId.Electricity, 0f, "MJ") },
            { ResourceId.Bandwidth,   new Resource(ResourceId.Bandwidth, 0f, "Mbps") },
            { ResourceId.Fuel,        new Resource(
                ResourceId.Fuel, "L",
                new Dictionary<string, float>
                {
                    { "gasoline", 0f },
                    { "diesel",   0f },
                    { "kerosene", 0f },
                    { "propane",  0f },
                })
            },
            { ResourceId.Money,       new Resource(ResourceId.Money, 0f, "$") },
        };

        // Bank Loan Debt
        public float LoanDebt = 0f;
        public const float LoanInterestRate = 0.035f; // 3.5% APR

        public float Money
        {
            get => Resources.TryGetValue(ResourceId.Money, out var r) ? r.Amount : 0f;
            set
            {
                if (Resources.TryGetValue(ResourceId.Money, out var r))
                {
                    r.Amount = Mathf.Max(0f, value);
                }
                else
                {
                    Resources[ResourceId.Money] = new Resource(ResourceId.Money, Mathf.Max(0f, value), "$");
                }
            }
        }

        public bool SpendMoney(float amount)
        {
            if (amount <= 0f) return true;
            if (Money >= amount)
            {
                Money -= amount;
                return true;
            }
            return false;
        }

        public void AddMoney(float amount)
        {
            if (amount > 0f)
            {
                Money += amount;
            }
        }

        public void TakeLoan(float principal)
        {
            if (principal <= 0f) return;
            LoanDebt += principal;
            AddMoney(principal);
        }

        public bool RepayLoan(float amount)
        {
            if (amount <= 0f || LoanDebt <= 0f) return false;
            float payAmount = Mathf.Min(amount, LoanDebt);
            if (SpendMoney(payAmount))
            {
                LoanDebt -= payAmount;
                return true;
            }
            return false;
        }

        // Toolbar - 10 slots, all empty at the start of a new game. No slots
        // are pre-filled and no quantities are shown; the player collects
        // everything themselves. HeldAssetId is empty until the first pick-up.
        public const int ToolbarSize = 10;
        public List<ToolbarSlotData> Toolbar = new List<ToolbarSlotData>();

        public int SelectedSlot = 0;
        public string HeldAssetId = string.Empty;

        public HudState()
        {
            RebuildEmptyToolbar();
        }

        private void RebuildEmptyToolbar()
        {
            Toolbar.Clear();
            for (int i = 0; i < ToolbarSize; i++)
            {
                Toolbar.Add(ToolbarSlotData.Empty());
            }
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

        public void SetVitalPercent(VitalId id, int percent)
        {
            percent = Mathf.Clamp(percent, 0, 100);
            int signedValue = (percent * 2) - 100;
            Vitals[id] = new Vital(id, signedValue);
        }

        public void SetVitalValue(VitalId id, int value)
        {
            value = Mathf.Clamp(value, -100, 100);
            Vitals[id] = new Vital(id, value);
        }

        public int GetVitalValue(VitalId id)
        {
            if (Vitals.TryGetValue(id, out var v))
            {
                return v.Value;
            }
            return 0;
        }

        public void ResetVitalsToNeutral()
        {
            SetVitalValue(VitalId.Wellness, 0);
            SetVitalValue(VitalId.Stamina, 0);
            SetVitalValue(VitalId.Thirst, 0);
            SetVitalValue(VitalId.Hunger, 0);
        }

        public void MaxAllVitals()
        {
            SetVitalValue(VitalId.Wellness, 100);
            SetVitalValue(VitalId.Stamina, 100);
            SetVitalValue(VitalId.Thirst, 100);
            SetVitalValue(VitalId.Hunger, 100);
        }

        /// <summary>
        /// Reset to the state a brand-new game starts in: every resource at
        /// zero, no debt, all vitals at +100, and an empty toolbar.
        /// </summary>
        public void ResetResourcesToDefault()
        {
            ResetToNewGameDefaults();
        }

        public void ResetToNewGameDefaults()
        {
            SetResourceAmount(ResourceId.Water, 0f);
            SetResourceAmount(ResourceId.Electricity, 0f);
            SetResourceAmount(ResourceId.Bandwidth, 0f);
            SetResourceAmount(ResourceId.Fuel, 0f);
            if (Resources.TryGetValue(ResourceId.Fuel, out var fuel) && fuel.Subspecies != null)
            {
                foreach (var key in new List<string>(fuel.Subspecies.Keys))
                {
                    fuel.Subspecies[key] = 0f;
                }
            }
            Money = 0f;
            LoanDebt = 0.0f;

            MaxAllVitals();
            RebuildEmptyToolbar();
            SelectedSlot = 0;
            HeldAssetId = string.Empty;
        }

        public void UpdateResource(Resource r)
        {
            Resources[r.Id] = r;
        }

        public float GetResourceAmount(ResourceId id)
        {
            if (Resources.TryGetValue(id, out var r))
            {
                return r.Amount;
            }
            return 0f;
        }

        public float Water => GetResourceAmount(ResourceId.Water);
        public float Electricity => GetResourceAmount(ResourceId.Electricity);
        public float Bandwidth => GetResourceAmount(ResourceId.Bandwidth);
        public float Fuel => GetResourceAmount(ResourceId.Fuel);

        public float WaterDisplay => (Units == UnitSystem.Imperial) ? Water * LitersToGallons : Water;
        public string WaterUnit => (Units == UnitSystem.Imperial) ? "gal" : "L";

        public float ElectricityDisplay => (Units == UnitSystem.Imperial) ? Electricity * MegajoulesToKilowattHours : Electricity;
        public string ElectricityUnit => (Units == UnitSystem.Imperial) ? "kWh" : "MJ";

        public float FuelDisplay => (Units == UnitSystem.Imperial) ? Fuel * LitersToGallons : Fuel;
        public string FuelUnit => (Units == UnitSystem.Imperial) ? "gal" : "L";

        public void SetWaterFromDisplay(float displayValue)
        {
            float liters = (Units == UnitSystem.Imperial) ? displayValue * GallonsToLiters : displayValue;
            SetResourceAmount(ResourceId.Water, liters);
        }

        public void SetElectricityFromDisplay(float displayValue)
        {
            float mj = (Units == UnitSystem.Imperial) ? displayValue * KilowattHoursToMegajoules : displayValue;
            SetResourceAmount(ResourceId.Electricity, mj);
        }

        public void SetFuelFromDisplay(float displayValue)
        {
            float liters = (Units == UnitSystem.Imperial) ? displayValue * GallonsToLiters : displayValue;
            SetResourceAmount(ResourceId.Fuel, liters);
        }

        public string FormatWater()
        {
            return $"{WaterDisplay:0.#} {WaterUnit}";
        }

        public string FormatElectricity()
        {
            return $"{ElectricityDisplay:0.00} {ElectricityUnit}";
        }

        public string FormatFuel()
        {
            return $"{FuelDisplay:0.#} {FuelUnit}";
        }

        public string FormatBandwidth()
        {
            return $"{Bandwidth:0.#} Mbps";
        }

        public string FormatMoney()
        {
            return $"{Money:N0}";
        }

        public static string FormatLength(float meters, UnitSystem system)
        {
            if (system == UnitSystem.Imperial)
            {
                float totalInches = meters * MetersToInches;
                int feet = Mathf.FloorToInt(totalInches / 12f);
                int inches = Mathf.RoundToInt(totalInches % 12f);
                if (inches == 12) { feet++; inches = 0; }
                if (feet == 0) return $"{inches} in";
                if (inches == 0) return $"{feet} ft";
                return $"{feet} ft {inches} in";
            }
            if (meters < 1f)
            {
                return $"{Mathf.RoundToInt(meters * 100f)} cm";
            }
            return $"{meters:0.##} m";
        }

        public string FormatDistance(float meters)
        {
            return FormatLength(meters, Units);
        }

        public void SetResourceAmount(ResourceId id, float amount)
        {
            amount = Mathf.Max(0f, amount);
            if (Resources.TryGetValue(id, out var r))
            {
                r.Amount = amount;
            }
            else
            {
                Resources[id] = new Resource(id, amount, "");
            }
        }

        public void ClearDebt()
        {
            LoanDebt = 0f;
        }

        public void SelectSlot(int idx)
        {
            idx = Mathf.Clamp(idx, 0, Toolbar.Count - 1);
            SelectedSlot = idx;
            var slot = Toolbar[idx];
            HeldAssetId = slot.IconId ?? string.Empty;
        }

        public void EnsureToolbarSlots()
        {
            while (Toolbar.Count < ToolbarSize)
            {
                Toolbar.Add(ToolbarSlotData.Empty());
            }
        }

        /// <summary>
        /// Adds item(s) to the toolbar according to stacking rules:
        /// 1. Tries to merge into existing slots containing the same item (up to maxStack).
        /// 2. If remainder remains, places into the first available empty slot(s) (up to maxStack per slot).
        /// Returns the number of items successfully added.
        /// </summary>
        public int AddItemToToolbar(string itemId, int countToAdd, int maxStack = 64)
        {
            if (string.IsNullOrEmpty(itemId) || countToAdd <= 0) return 0;
            if (maxStack <= 0) maxStack = 64;

            EnsureToolbarSlots();

            int remaining = countToAdd;

            // Pass 1: Fill existing matching slots that are not yet full
            for (int i = 0; i < ToolbarSize && remaining > 0; i++)
            {
                var slot = Toolbar[i];
                if (slot.IconId == itemId && slot.Count > 0 && slot.Count < maxStack)
                {
                    int space = maxStack - slot.Count;
                    int take = Mathf.Min(space, remaining);
                    slot.Count += take;
                    remaining -= take;
                    Toolbar[i] = slot;
                }
            }

            // Pass 2: Fill empty slots
            for (int i = 0; i < ToolbarSize && remaining > 0; i++)
            {
                var slot = Toolbar[i];
                if (string.IsNullOrEmpty(slot.IconId) || slot.Count == 0)
                {
                    int take = Mathf.Min(maxStack, remaining);
                    slot.IconId = itemId;
                    slot.Count = take;
                    remaining -= take;
                    Toolbar[i] = slot;
                }
            }

            // Refresh held asset id if selected slot changed
            if (SelectedSlot >= 0 && SelectedSlot < Toolbar.Count)
            {
                HeldAssetId = Toolbar[SelectedSlot].IconId ?? string.Empty;
            }

            return countToAdd - remaining;
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
            if (unit == "$")
            {
                return amount.ToString("N0");
            }
            if (amount >= 1000f)
            {
                float k = amount / 1000f;
                return k.ToString("0.00") + "k " + unit;
            }
            return amount.ToString("0.##") + " " + unit;
        }
    }
}
