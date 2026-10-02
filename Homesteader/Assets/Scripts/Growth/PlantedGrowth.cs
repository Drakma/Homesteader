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

        // ---- picking fruit (kit: growth.rules.fruit) - the tree stays; only its fruit goes, and comes back
        /// <summary>The game day (VegetationSeasons.GrowthDay) the fruit is back after a pick; 0 = not picked.</summary>
        public float FruitPickedUntil { get; private set; }

        /// <summary>Bit i set = fruit i has been picked (fruit comes off one at a time; they all return FruitPickedUntil).</summary>
        public uint FruitGone { get; private set; }

        private int FruitTotal => Homesteader.World.ForestTrees.PlantFruitLayout(Group.Id, out _, out _, out int total, out _) ? total : 1;

        /// <summary>How many fruit are still on the tree.</summary>
        public int FruitLeft
        {
            get
            {
                uint left = Homesteader.World.ForestTrees.FullFruitMask(FruitTotal) & ~FruitGone;
                int n = 0;
                for (; left != 0; left &= left - 1) n++;
                return n;
            }
        }

        private Mesh ownFruitMesh;   // a copy of the tree's mesh with the picked fruit hidden (the species mesh is shared and is never edited)

        /// <summary>The stage number from which this tree bears fruit (the kit's fruit_stage, default the last stage).</summary>
        public int FruitStageNumber
        {
            get
            {
                if (Group.Rules.FruitStage > 0) return Group.Rules.FruitStage;
                return Group.Stages.Count > 0 ? Group.Stages[Group.Stages.Count - 1].Stage : 1;
            }
        }

        /// <summary>True while the fruit is on the tree: a fruiting tree at its fruiting stage that has not just been picked.</summary>
        public bool FruitOn
        {
            get
            {
                return Group != null && Group.Rules.Fruiting && CurrentStage != null && CurrentStage.Stage >= FruitStageNumber && FruitLeft > 0;
            }
        }

        /// <summary>Ripe fruit that can be picked by hand now.</summary>
        public bool CanPickFruit => State == PlantState.Alive && Group.Rules.FruitDrops.Count > 0 && FruitOn;

        /// <summary>Picks the fruit: the drops go to the toolbar (first free slot), the tree stays and shows its no-fruit look until the fruit regrows.</summary>
        public bool PickFruit(string heldId = null, Transform picker = null)
        {
            if (!CanPickFruit) return false;
            if (FruitPickAnimator.Busy) return true;   // the player's hand is still on the last one
            string need = Group.Rules.FruitTool;
            if (!string.IsNullOrEmpty(need) && !GrowthRegistry.ToolMatches(need, heldId))
            {
                ToastNotificationSystem.ShowWarning("Need a tool", "You need the right tool in your active slot to pick this fruit.");
                return false;
            }
            // One fruit at a time: a random one of those still on the tree comes off.
            int total = FruitTotal;
            uint left = Homesteader.World.ForestTrees.FullFruitMask(total) & ~FruitGone;
            int leftCount = FruitLeft;
            if (leftCount <= 0) return false;
            int nth = Random.Range(0, leftCount), bit = 0;
            for (int seen = -1; bit < 32; bit++)
                if ((left & (1u << bit)) != 0 && ++seen == nth) break;

            void TakeOffTree()
            {
                FruitGone |= 1u << bit;
                FruitPickedUntil = Homesteader.World.VegetationSeasons.GrowthDay + Group.Rules.FruitRegrowDays;   // the missing fruit is all back this long after the latest pick
                ShowStageModel();
            }

            void IntoBasket()
            {
                if (!GrowthDrop.Give(Group.Rules.FruitDrops)) ToastNotificationSystem.ShowWarning("Toolbar full", "The fruit didn't fit and was lost.");
            }

            // The left hand reaches up for it, the fruit comes off, the hand bends in to the right hand (the basket) and it lands in the toolbar.
            if (picker != null && model != null && Homesteader.World.ForestTrees.PlantFruitLayout(Group.Id, out _, out _, out _, out Color fruitColor))
            {
                Vector3 fruitPos = model.transform.TransformPoint(Homesteader.World.ForestTrees.PlantFruitCentre(Group.Id, bit));
                if (FruitPickAnimator.TryBegin(picker, fruitPos, fruitColor, TakeOffTree, IntoBasket)) return true;
            }
            TakeOffTree();
            IntoBasket();
            return true;
        }

        /// <summary>Puts a saved pick back (loading a game).</summary>
        public void RestoreFruit(float pickedUntil, uint goneMask = uint.MaxValue)
        {
            FruitPickedUntil = pickedUntil;
            // an older save has no mask: everything on the tree counted as picked
            FruitGone = goneMask == uint.MaxValue ? Homesteader.World.ForestTrees.FullFruitMask(FruitTotal) : goneMask;
            ShowStageModel();
        }
        private float nextConditionCheck;
        private bool growthAllowed = true;

        /// <summary>Plants <paramref name="group"/> at a point, at age 0.</summary>
        public static PlantedGrowth Plant(GrowthGroup group, Vector3 position, Transform parent = null)
        {
            var go = new GameObject($"Planted_{group.Id}");
            // Grid-aligned: crops keep their rows straight; trees turn in 90-degree steps for variety.
            float yaw = group.GrowthType == "tree" ? 90f * Random.Range(0, 4) : 0f;
            // Snap to the terrain surface (just above, not 3 m above).
            position = Homesteader.Generation.TerrainHeightDetector.PlaceOnGround(position);
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
                // A fruiting tree with no harvest stage of its own is cut down from its mature stage (the one before the fruiting
                // stage), not only once it is bearing fruit.
                if (Group.Rules.Fruiting && FruitStageNumber > 1) return FruitStageNumber - 1;
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

        /// <summary>
        /// A planted tree chopped down: the tree falls like a generated one, everything it yields lies on the ground (see
        /// ForestTrees.FellPlanted) and a stump stays in its place for good.
        /// </summary>
        public void Fell(Vector3 fromPlayer)
        {
            GrowthRules rules = Group.Rules;
            var extras = new List<string>();
            foreach (GrowthDrop d in rules.YieldExtras)
            {
                int n = d.Roll();
                for (int i = 0; i < n; i++) extras.Add(d.ItemId);
            }
            Transform felled = model != null ? model.transform : null;
            StumpRadius = Homesteader.World.ForestTrees.MeasureTrunkRadius(felled, transform.position);
            model = null;   // the falling copy now owns it
            Homesteader.World.ForestTrees.FellPlanted(felled, transform.position, transform.position - fromPlayer, rules.YieldItemId, rules.RollYield(), extras);
            State = PlantState.Stump;
            ShowStump();
        }

        /// <summary>The trunk radius the felled tree had, so its stump is as wide (0 = unknown). Saved with the plant.</summary>
        public float StumpRadius;

        private bool chopping;

        /// <summary>
        /// One click starts the chopping: the ped swings the axe for as many swings as a full-grown tree takes (a thock and chips
        /// each), then the tree falls (see <see cref="Fell"/>). Walking away stops it.
        /// </summary>
        public void StartChop(PedController ped)
        {
            if (chopping || State == PlantState.Stump) return;
            StartCoroutine(ChopRoutine(ped));
        }

        private IEnumerator ChopRoutine(PedController ped)
        {
            chopping = true;
            string clip = Homesteader.World.ForestTrees.ChopClip;
            bool animated = ped != null && ped.BeginWork(clip, transform.position);
            int hits = Homesteader.World.ForestTrees.FullTreeHits;
            for (int i = 0; i < hits; i++)
            {
                yield return new WaitForSeconds(Homesteader.World.ForestTrees.SwingSeconds);
                if (ped != null && animated && !ped.WorkPhase(clip, out _, out _)) { chopping = false; yield break; }   // walked away
                Homesteader.World.ForestTrees.ChopEffects(transform.position, ped != null ? ped.transform.position : transform.position - Vector3.forward);
            }
            if (ped != null && animated) ped.EndWork(clip);
            chopping = false;
            Fell(ped != null ? ped.transform.position : transform.position - Vector3.forward);
        }

        /// <summary>The kit's stump model when it has one, otherwise a stump built in code like a forest tree's.</summary>
        private void ShowStump()
        {
            GrowthVariant stump = Group.Rules.Stump;
            if (stump != null && stump.Prefab != null) ShowModel(stump.Prefab);
            else Homesteader.World.ForestTrees.BuildPlantedStump(Group.Id, transform, StumpRadius);
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
            if (FruitPickedUntil > 0f && Homesteader.World.VegetationSeasons.GrowthDay >= FruitPickedUntil)
            {
                FruitPickedUntil = 0f;   // the fruit has regrown
                FruitGone = 0;
                if (State == PlantState.Alive) ShowStageModel();
            }

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
            ShowStageModel();
        }

        /// <summary>Shows the current stage's model; a fruiting tree whose fruit was just picked shows the stage before (no fruit).</summary>
        private void ShowStageModel()
        {
            GrowthStage stage = CurrentStage;
            if (stage == null) return;
            if (Group.Rules.Fruiting && stage.Stage >= FruitStageNumber && !FruitOn)
            {
                int i = Group.Stages.IndexOf(stage);
                if (i > 0 && Group.Stages[i - 1].Prefab != null) stage = Group.Stages[i - 1];
            }
            if (stage.Prefab == null) return;
            ShowModel(stage.Prefab);
            // some of the fruit is picked but not all: this tree gets its own copy of the mesh with those fruit hidden
            if (Group.Rules.Fruiting && stage.Stage >= FruitStageNumber && FruitOn && FruitGone != 0) HidePickedFruit();
        }

        private void HidePickedFruit()
        {
            if (model == null) return;
            var mf = model.GetComponentInChildren<MeshFilter>();
            if (mf == null || mf.sharedMesh == null || !Homesteader.World.ForestTrees.PlantFruitLayout(Group.Id, out int first, out int per, out int total, out _)) return;
            Mesh copy = Instantiate(mf.sharedMesh);
            Vector3[] verts = copy.vertices;
            for (int f = 0; f < total; f++)
            {
                if ((FruitGone & (1u << f)) == 0) continue;
                for (int k = 0; k < per; k++)
                {
                    int i = first + f * per + k;
                    if (i < verts.Length) verts[i] = Vector3.zero;
                }
            }
            copy.vertices = verts;
            copy.RecalculateBounds();
            mf.sharedMesh = copy;
            if (ownFruitMesh != null) Destroy(ownFruitMesh);
            ownFruitMesh = copy;
        }

        private void OnDestroy()
        {
            if (ownFruitMesh != null) Destroy(ownFruitMesh);
        }

        /// <summary>Puts the plant back in the state it was saved in (dead / stump are permanent; withered re-evaluates).</summary>
        public void RestoreState(PlantState saved, float stumpRadius = 0f)
        {
            if (stumpRadius > 0f) StumpRadius = stumpRadius;
            if (Group == null) return;
            if (saved == PlantState.Dead && Group.Rules.Dead != null && Group.Rules.Dead.Prefab != null)
            {
                State = PlantState.Dead;
                ShowModel(Group.Rules.Dead.Prefab);
            }
            else if (saved == PlantState.Stump)
            {
                State = PlantState.Stump;
                if (model != null) { Destroy(model); model = null; }
                ShowStump();
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
