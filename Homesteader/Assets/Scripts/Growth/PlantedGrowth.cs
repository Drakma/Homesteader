using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A planted growth group in the world. Owns the plant's age, advances it as
    /// game days pass (only while its planting rules allow growth), and swaps the
    /// visible stage model when the age crosses into the next stage's window.
    /// </summary>
    public sealed class PlantedGrowth : MonoBehaviour
    {
        public static readonly List<PlantedGrowth> All = new List<PlantedGrowth>();

        public GrowthGroup Group { get; private set; }
        /// <summary>Accumulated growing age in game days (does not advance while paused by rules).</summary>
        public float AgeDays { get; private set; }
        public GrowthStage CurrentStage { get; private set; }

        private GameObject model;
        private float lastClockDay;
        private float nextConditionCheck;
        private bool growthAllowed = true;

        /// <summary>Plants <paramref name="group"/> at a point, at age 0.</summary>
        public static PlantedGrowth Plant(GrowthGroup group, Vector3 position, Transform parent = null)
        {
            var go = new GameObject($"Planted_{group.Id}");
            go.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, Random.Range(0f, 360f), 0f));
            if (parent != null) go.transform.SetParent(parent, true);

            var planted = go.AddComponent<PlantedGrowth>();
            planted.Group = group;
            planted.lastClockDay = ClockDay();
            planted.SetStage(group.StageForAge(0f));
            return planted;
        }

        private static float ClockDay()
        {
            TimeSystem t = TimeSystem.Instance;
            return t.DayOfYear + t.MinuteOfDay / TimeConstants.CycleGameMinutes;
        }

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        private void Update()
        {
            if (Group == null) return;

            float clock = ClockDay();
            float dt = clock - lastClockDay;
            lastClockDay = clock;
            if (dt <= 0f) return;   // paused, or the clock was set backwards

            // The season/temperature rules are cheap but not free; re-check twice a second.
            if (Time.unscaledTime >= nextConditionCheck)
            {
                nextConditionCheck = Time.unscaledTime + 0.5f;
                if (!EvaluateConditions()) return;   // plant was destroyed
            }

            if (!growthAllowed) return;

            AgeDays = Mathf.Min(AgeDays + dt, Group.MaxAgeDays);
            GrowthStage stage = Group.StageForAge(AgeDays);
            if (stage != CurrentStage) SetStage(stage);
        }

        /// <summary>
        /// Applies the group's failure rules. Returns false if the plant died and
        /// was destroyed. Growth only pauses ("pause"/"wither" stall it) - dying
        /// requires an explicit die rule, so a bad week never silently deletes a crop.
        /// </summary>
        private bool EvaluateConditions()
        {
            GrowthRules rules = Group.Rules;
            if (rules.IndoorOk) { growthAllowed = true; return true; }

            TimeSystem t = TimeSystem.Instance;
            HudTimeState snap = t.Snapshot();

            if (rules.FrostKills && snap.TemperatureC <= 0f)
            {
                Die("frost");
                return false;
            }

            bool inSeason = PlantingValidator.SeasonAllowed(rules, snap.Season, out _);
            bool tempOk = (!rules.MinTempC.HasValue || snap.TemperatureC >= rules.MinTempC.Value)
                       && (!rules.MaxTempC.HasValue || snap.TemperatureC <= rules.MaxTempC.Value);

            if (!inSeason && rules.OutOfSeason == "die")
            {
                Die("the season change");
                return false;
            }

            growthAllowed = inSeason && tempOk;
            return true;
        }

        private void Die(string cause)
        {
            ToastNotificationSystem.ShowWarning(
                $"{Group.Name} died", $"Your {Group.Name.ToLowerInvariant()} was killed by {cause}.");
            Destroy(gameObject);
        }

        private void SetStage(GrowthStage stage)
        {
            CurrentStage = stage;
            if (model != null) Destroy(model);
            if (stage == null || stage.Prefab == null) return;

            model = Instantiate(stage.Prefab, transform);
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;
        }
    }
}
