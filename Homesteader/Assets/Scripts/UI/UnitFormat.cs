using UnityEngine;

namespace Homesteader.UI
{
    /// <summary>
    /// The one place numbers with units are written for the player. Everything in the game is stored in metric (metres, kilograms, liters,
    /// square metres); whenever one is SHOWN it goes through here, so the Metric / Imperial setting (HudState.Units) changes it everywhere:
    /// lengths in feet and inches, areas in square feet, weights in pounds, volumes in gallons. New UI text with a unit uses these.
    /// </summary>
    public static class UnitFormat
    {
        public const float KilogramsToPounds = 2.20462f;
        public const float SquareMetersToSquareFeet = 10.7639f;

        private static bool Imperial
        {
            get { HudState hud = HudState.Active; return hud != null && hud.Units == UnitSystem.Imperial; }
        }

        /// <summary>A length: "1.5 m" or "4 ft 11 in" (small ones in cm or inches).</summary>
        public static string Length(float meters) { return HudState.FormatLength(meters, Imperial ? UnitSystem.Imperial : UnitSystem.Metric); }

        /// <summary>A longer distance, without the inches: "45.6 m" or "150 ft".</summary>
        public static string Distance(float meters)
        {
            return Imperial ? $"{meters * HudState.MetersToFeet:0} ft" : $"{meters:0.#} m";
        }

        /// <summary>An area: "123.4 m2" or "1,328 sq ft".</summary>
        public static string Area(float squareMeters)
        {
            return Imperial ? $"{squareMeters * SquareMetersToSquareFeet:N0} sq ft" : $"{squareMeters:0.#} m2";
        }

        /// <summary>A weight: "2.5 kg" or "5.5 lb".</summary>
        public static string Weight(float kilograms, string format = "0.0")
        {
            return Imperial ? $"{(kilograms * KilogramsToPounds).ToString(format)} lb" : $"{kilograms.ToString(format)} kg";
        }

        /// <summary>A weight for a name: no needless decimals ("9 kg", "0.5 kg", "20 lb"): whole numbers from 10 up and in pounds from 10 lb up.</summary>
        public static string WeightLabel(float kilograms)
        {
            float v = Imperial ? kilograms * KilogramsToPounds : kilograms;
            string num = v >= 10f ? Mathf.Round(v).ToString("0") : (Mathf.Abs(v - Mathf.Round(v)) < 0.05f ? Mathf.Round(v).ToString("0") : v.ToString("0.#"));
            return num + (Imperial ? " lb" : " kg");
        }

        /// <summary>Two weights as "used / capacity unit": "12.5 / 40.0 kg" or "27.6 / 88.2 lb".</summary>
        public static string WeightPair(float used, float capacity)
        {
            return Imperial ? $"{used * KilogramsToPounds:0.0} / {capacity * KilogramsToPounds:0.0} lb" : $"{used:0.0} / {capacity:0.0} kg";
        }

        /// <summary>A bulk volume (piles of sand, gravel, dirt): "0.25 m3" or "0.33 yd3" (cubic yards).</summary>
        public static string BulkVolume(float cubicMeters)
        {
            return Imperial ? $"{cubicMeters * 1.30795f:0.##} yd3" : $"{cubicMeters:0.###} m3";
        }

        /// <summary>A liquid volume: "5 L" or "1.3 gal".</summary>
        public static string Volume(float liters)
        {
            return Imperial ? $"{liters * HudState.LitersToGallons:0.#} gal" : $"{liters:0.#} L";
        }
    }
}
