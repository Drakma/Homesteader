using System.Collections;
using System.Collections.Generic;
using Homesteader.Modding;
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

        public enum PlantState { Alive, Withered, Dead, Stump }
        /// <summary>Alive, withering (out of season with a wither rule), dead (permanent) or a stump (a harvested tree, permanent).</summary>
        public PlantState State { get; private set; } = PlantState.Alive;

        private GameObject model;
        private float lastClockDay;
        private float nextConditionCheck;
        private bool growthAllowed = true;

        /// <summary>Plants <paramref name="group"/> at a point, at age 0.</summary>
        public static PlantedGrowth Plant(GrowthGroup group, Vector3 position, Transform parent = null)
        {
            var go = new GameObject($"Planted_{group.Id}");
            // Grid-aligned: crops keep their rows straight; trees turn in 90-degree steps for variety.
            float yaw = group.GrowthType == "tree" ? 90f * Random.Range(0, 4) : 0f;
            go.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, yaw, 0f));
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

        /// <summary>Stage number at which this plant can be harvested (the last stage unless the rules say otherwise).</summary>
        public int HarvestStageNumber
        {
            get
            {
                if (Group.Rules.HarvestStage > 0) return Group.Rules.HarvestStage;
                return Group.Stages.Count > 0 ? Group.Stages[Group.Stages.Count - 1].Stage : 1;
            }
        }

        /// <summary>True once the plant has reached its harvest stage.</summary>
        public bool IsReady => CurrentStage != null && CurrentStage.Stage >= HarvestStageNumber;

        /// <summary>Ready AND alive: a withered or dead plant cannot be harvested.</summary>
        public bool CanHarvest => State == PlantState.Alive && IsReady;

        /// <summary>Re-checks season/temperature now (normally twice a second), e.g. after loading a save.</summary>
        public void RefreshConditions()
        {
            if (State != PlantState.Dead && State != PlantState.Stump && Group != null) EvaluateConditions();
        }

        /// <summary>Sets the plant's age directly (e.g. loading a save) and shows the matching stage.</summary>
        public void SetAgeDays(float ageDays)
        {
            AgeDays = Mathf.Clamp(ageDays, 0f, Group.MaxAgeDays);
            GrowthStage stage = Group.StageForAge(AgeDays);
            if (stage != CurrentStage) SetStage(stage);
        }

        /// <summary>
        /// Called after a successful harvest: perennials drop back to their regrow stage and keep
        /// growing; everything else is removed.
        /// </summary>
        public void Harvested()
        {
            GrowthRules rules = Group.Rules;
            if (rules.Regrows && rules.RegrowStage > 0)
            {
                GrowthStage back = Group.Stages.Find(s => s.Stage == rules.RegrowStage);
                if (back != null)
                {
                    SetAgeDays(back.AgeMin);
                    return;
                }
            }

            // A harvested tree leaves its stump behind for good; anything else is removed.
            GrowthVariant stump = rules.Stump;
            if (stump != null && stump.Prefab != null)
            {
                State = PlantState.Stump;
                ShowModel(stump.Prefab);
                return;
            }
            Destroy(gameObject);
        }

        private void OnEnable() => All.Add(this);
        private void OnDisable() => All.Remove(this);

        private void Update()
        {
            if (Group == null) return;

            if (State == PlantState.Dead || State == PlantState.Stump) return;   // permanent states

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
                return false;   // dead (or removed): nothing more to grow
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

            // Out of season with a wither rule: show the withered version until conditions return.
            SetWithered(!growthAllowed && rules.OutOfSeason == "wither");
            return true;
        }

        /// <summary>Swaps to / from the withered model. No-op without a withered version or once dead.</summary>
        private void SetWithered(bool withered)
        {
            if (State == PlantState.Dead) return;
            GrowthVariant variant = Group.Rules.Withered;

            if (withered && State == PlantState.Alive)
            {
                State = PlantState.Withered;
                if (variant != null && variant.Prefab != null) ShowModel(variant.Prefab);
            }
            else if (!withered && State == PlantState.Withered)
            {
                State = PlantState.Alive;
                if (variant != null && variant.Prefab != null) SetStage(CurrentStage);   // back to the stage model
            }
        }

        private void Die(string cause)
        {
            ToastNotificationSystem.ShowWarning(
                $"{Group.Name} died", $"Your {Group.Name.ToLowerInvariant()} was killed by {cause}.");

            // A dead version stays in the world for good; without one the plant is simply removed.
            GrowthVariant dead = Group.Rules.Dead;
            if (dead != null && dead.Prefab != null)
            {
                State = PlantState.Dead;
                ShowModel(dead.Prefab);
                return;
            }
            Destroy(gameObject);
        }

        private IEnumerator ShowWhenReady(GameObject prefab, GlbTemplate glb)
        {
            while (!glb.Ready && !glb.Failed) yield return null;
            if (glb.Failed || pendingPrefab != prefab) yield break;   // failed, or the plant moved on to another model
            ShowModel(prefab);
        }

        private void SetStage(GrowthStage stage)
        {
            CurrentStage = stage;
            if (stage == null || stage.Prefab == null) return;
            ShowModel(stage.Prefab);
        }

        /// <summary>Puts the plant back in the state it was saved in (dead / stump are permanent; withered re-evaluates).</summary>
        public void RestoreState(PlantState saved)
        {
            if (Group == null) return;
            if (saved == PlantState.Dead && Group.Rules.Dead != null && Group.Rules.Dead.Prefab != null)
            {
                State = PlantState.Dead;
                ShowModel(Group.Rules.Dead.Prefab);
            }
            else if (saved == PlantState.Stump && Group.Rules.Stump != null && Group.Rules.Stump.Prefab != null)
            {
                State = PlantState.Stump;
                ShowModel(Group.Rules.Stump.Prefab);
            }
            else if (saved == PlantState.Withered)
            {
                RefreshConditions();
            }
        }

        private GameObject pendingPrefab;

        /// <summary>Replaces the visible model (a stage, or the withered / dead version).</summary>
        private void ShowModel(GameObject prefab)
        {
            // A GLB model is a lazily loaded template: start its load and show it once it is ready.
            GlbTemplate glb = prefab != null ? prefab.GetComponent<GlbTemplate>() : null;
            if (glb != null && !glb.Ready)
            {
                glb.EnsureLoading();
                if (glb.Failed) return;
                pendingPrefab = prefab;
                StartCoroutine(ShowWhenReady(prefab, glb));
                return;
            }
            pendingPrefab = null;
            if (model != null) Destroy(model);

            model = Instantiate(prefab, transform);
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;

            // Crops are walk-through: the player and clicks pass straight through them.
            // (Trees stay solid.) Disabling is immediate, unlike Destroy.
            if (Group.GrowthType == "crop")
                foreach (Collider c in model.GetComponentsInChildren<Collider>(true))
                    c.enabled = false;
        }
    }
}
