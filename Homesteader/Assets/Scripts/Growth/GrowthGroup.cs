using System;
using System.Collections.Generic;
using System.IO;
using Homesteader.Modding;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>One lifecycle stage of a growth group (mirrors growth.stages[]).</summary>
    public sealed class GrowthStage
    {
        public int Stage;
        public string Name;
        /// <summary>Inclusive lower / exclusive upper age bound, in GAME DAYS.</summary>
        public float AgeMin;
        public float AgeMax;
        public string Resource;
        public string Model;
        /// <summary>Resolved through the mod asset resolver; null when no prefab was generated.</summary>
        public GameObject Prefab;
    }

    /// <summary>
    /// A group's growth.rules block (growth_group.schema.json). Trees and crops
    /// only. Every field has the schema's default, so a missing block means
    /// "no restriction / cannot fail".
    /// </summary>
    public sealed class GrowthRules
    {
        // yield
        public string YieldItemId;
        public int YieldAmount;
        public int HarvestStage;      // 0 = final stage
        public bool Regrows;
        public int RegrowStage;

        // planting
        public readonly List<string> Seasons = new List<string>();   // spring/summer/fall/winter/year_round
        public readonly List<string> Biomes = new List<string>();    // empty = any biome
        public float? MinTempC;
        public float? MaxTempC;
        public bool IndoorOk;

        // needs
        public float WaterIntervalDays;   // 0 = none
        public bool FertilizerRequired;

        // failure
        public string OutOfSeason = "pause";        // pause | wither | die
        public bool FrostKills;
        public float DroughtDaysBeforeWither;
        public string WitherBehavior = "stall";     // stall | regress_one_stage | die

        public bool YearRound => Seasons.Count == 0 || Seasons.Contains("year_round");

        public static GrowthRules Parse(ModJsonValue r)
        {
            var rules = new GrowthRules();
            if (r == null || r.IsNull) return rules;

            ModJsonValue y = r.Get("yield");
            rules.YieldItemId = y.Get("item_id").AsString();
            rules.YieldAmount = y.Get("amount").AsInt(0);
            rules.HarvestStage = y.Get("harvest_stage").AsInt(0);
            rules.Regrows = y.Get("regrows").AsBool(false);
            rules.RegrowStage = y.Get("regrow_stage").AsInt(0);

            ModJsonValue p = r.Get("planting");
            rules.Seasons.AddRange(p.Get("seasons").AsStringList());
            rules.Biomes.AddRange(p.Get("biomes").AsStringList());
            if (p.Has("min_temp_c")) rules.MinTempC = p.Get("min_temp_c").AsFloat();
            if (p.Has("max_temp_c")) rules.MaxTempC = p.Get("max_temp_c").AsFloat();
            rules.IndoorOk = p.Get("indoor_ok").AsBool(false);

            ModJsonValue n = r.Get("needs");
            rules.WaterIntervalDays = n.Get("water_interval_days").AsFloat(0f);
            rules.FertilizerRequired = n.Get("fertilizer_required").AsBool(false);

            ModJsonValue f = r.Get("failure");
            rules.OutOfSeason = f.Get("out_of_season").AsString("pause");
            rules.FrostKills = f.Get("frost_kills").AsBool(false);
            rules.DroughtDaysBeforeWither = f.Get("drought_days_before_wither").AsFloat(0f);
            rules.WitherBehavior = f.Get("wither_behavior").AsString("stall");
            return rules;
        }
    }

    /// <summary>
    /// A growth group loaded from a mod: the scheme (stages + ages) and the
    /// rules. Built by GrowthGroup.TryParse from the group manifest, which is
    /// authoritative for both.
    /// </summary>
    public sealed class GrowthGroup
    {
        public string Id;
        public string Namespace = "core";
        public string Name;
        public string GrowthType;     // tree | crop | animal | percent | generic
        public string Species;
        public float MaxAgeDays;
        public readonly List<GrowthStage> Stages = new List<GrowthStage>();
        public GrowthRules Rules = new GrowthRules();

        public string QualifiedId => $"{Namespace}:{Id}";

        /// <summary>Only trees and crops have planting rules and can be planted.</summary>
        public bool IsPlantable => GrowthType == "tree" || GrowthType == "crop";

        /// <summary>The stage whose age window contains <paramref name="ageDays"/> (clamped to first/last).</summary>
        public GrowthStage StageForAge(float ageDays)
        {
            if (Stages.Count == 0) return null;
            foreach (GrowthStage s in Stages)
                if (ageDays >= s.AgeMin && ageDays < s.AgeMax) return s;
            return ageDays < Stages[0].AgeMin ? Stages[0] : Stages[Stages.Count - 1];
        }

        /// <summary>
        /// Parses a group manifest (is_growable: true + a growth block). Returns
        /// false for anything else. <paramref name="groupDir"/> is the folder the
        /// manifest lives in; stage resource folders are resolved relative to it.
        /// Stage prefabs are resolved through <paramref name="resolver"/> when given.
        /// </summary>
        public static bool TryParse(
            ModInfo mod, string groupDir, ModJsonValue root, string ns,
            IModAssetResolver resolver, out GrowthGroup group, Action<string> warn = null)
        {
            group = null;
            if (!root.Get("is_growable").AsBool(false)) return false;

            ModJsonValue g = root.Get("growth");
            if (g == null || g.IsNull || !g.IsObject) return false;

            string id = root.Get("id").AsString();
            if (string.IsNullOrEmpty(id)) return false;

            float toDays = DaysPerUnit(g.Get("time_unit").AsString("days"));

            var result = new GrowthGroup
            {
                Id = id,
                Namespace = ns,
                Name = root.Get("name").AsString(id),
                GrowthType = g.Get("growth_type").AsString("generic"),
                Species = g.Get("species").AsString(id),
                MaxAgeDays = g.Get("max_age").AsFloat(0f) * toDays,
            };

            foreach (ModJsonValue s in g.Get("stages").Items)
            {
                var stage = new GrowthStage
                {
                    Stage = s.Get("stage").AsInt(result.Stages.Count + 1),
                    Name = s.Get("name").AsString("stage"),
                    AgeMin = s.Get("age_min").AsFloat(0f) * toDays,
                    AgeMax = s.Get("age_max").AsFloat(0f) * toDays,
                    Resource = s.Get("resource").AsString(),
                    Model = s.Get("model").AsString(),
                };
                stage.Prefab = ResolveStagePrefab(mod, groupDir, stage, resolver, warn);
                result.Stages.Add(stage);
            }
            result.Stages.Sort((a, b) => a.Stage.CompareTo(b.Stage));

            if (result.IsPlantable)
                result.Rules = GrowthRules.Parse(g.Get("rules"));

            group = result;
            return true;
        }

        private static float DaysPerUnit(string unit)
        {
            switch ((unit ?? "days").ToLowerInvariant())
            {
                case "hours": return 1f / 24f;
                case "minutes": return 1f / 1440f;
                default: return 1f;   // days (and 'percent', which is not time-based)
            }
        }

        /// <summary>
        /// A stage folder holds that stage's own manifest (id + models[]), which is
        /// what the prefab generator builds "prefabs/&lt;stage id&gt;.prefab" from.
        /// Hand that manifest to the normal asset resolver.
        /// </summary>
        private static GameObject ResolveStagePrefab(
            ModInfo mod, string groupDir, GrowthStage stage, IModAssetResolver resolver, Action<string> warn)
        {
            if (resolver == null || string.IsNullOrEmpty(stage.Resource) || string.IsNullOrEmpty(groupDir))
                return null;

            string dir = Path.Combine(groupDir, stage.Resource.Replace('/', Path.DirectorySeparatorChar));
            if (!Directory.Exists(dir)) return null;

            foreach (string json in Directory.GetFiles(dir, "*.json"))
            {
                if (!ModJson.TryParse(File.ReadAllText(json), out ModJsonValue stageRoot, out _))
                    continue;
                if (string.IsNullOrEmpty(stageRoot.Get("id").AsString()))
                    continue;
                if (resolver.TryResolvePrefab(mod, stageRoot, out GameObject prefab))
                    return prefab;
            }

            warn?.Invoke($"No prefab for stage {stage.Stage} ({stage.Name}) at '{stage.Resource}'.");
            return null;
        }
    }

    /// <summary>What an item does on right-click (the manifest's use.right_click block).</summary>
    public sealed class UseBehavior
    {
        public const string PlantGrowthGroup = "plant_growth_group";

        public string ItemId;
        public string Namespace = "core";
        public string Action;
        /// <summary>For plant_growth_group: the growth group's id.</summary>
        public string GroupId;

        public static bool TryParse(ModJsonValue root, string ns, out UseBehavior behavior)
        {
            behavior = null;
            ModJsonValue rc = root.Get("use").Get("right_click");
            if (rc == null || rc.IsNull || !rc.IsObject) return false;

            string action = rc.Get("action").AsString();
            string itemId = root.Get("id").AsString();
            if (string.IsNullOrEmpty(action) || string.IsNullOrEmpty(itemId)) return false;

            behavior = new UseBehavior
            {
                ItemId = itemId,
                Namespace = ns,
                Action = action,
                GroupId = rc.Get("group").AsString(),
            };
            return true;
        }
    }

    /// <summary>
    /// Everything mods have contributed at runtime: growth groups and item use
    /// behaviours. ModLoader is the only writer (merge rules stay in one file);
    /// gameplay code only reads.
    /// </summary>
    public static class GrowthRegistry
    {
        private static readonly Dictionary<string, GrowthGroup> groups =
            new Dictionary<string, GrowthGroup>(StringComparer.OrdinalIgnoreCase);
        private static readonly Dictionary<string, UseBehavior> uses =
            new Dictionary<string, UseBehavior>(StringComparer.OrdinalIgnoreCase);

        public static IEnumerable<GrowthGroup> Groups => groups.Values;

        public static void Clear()
        {
            groups.Clear();
            uses.Clear();
        }

        /// <summary>First registration of a qualified id wins; returns false for a duplicate.</summary>
        public static bool Register(GrowthGroup group)
        {
            if (group == null || groups.ContainsKey(group.QualifiedId)) return false;
            groups[group.QualifiedId] = group;
            return true;
        }

        public static bool Register(UseBehavior use)
        {
            if (use == null) return false;
            string key = $"{use.Namespace}:{use.ItemId}";
            if (uses.ContainsKey(key)) return false;
            uses[key] = use;
            return true;
        }

        /// <summary>The right-click behaviour of a toolbar item id, from any namespace.</summary>
        public static bool TryGetUse(string itemId, out UseBehavior use)
        {
            foreach (UseBehavior u in uses.Values)
            {
                if (string.Equals(u.ItemId, itemId, StringComparison.OrdinalIgnoreCase))
                {
                    use = u;
                    return true;
                }
            }
            use = null;
            return false;
        }

        /// <summary>Looks a group up by id, preferring the item's own namespace.</summary>
        public static bool TryGetGroup(string groupId, string preferredNamespace, out GrowthGroup group)
        {
            if (groups.TryGetValue($"{preferredNamespace}:{groupId}", out group)) return true;
            foreach (GrowthGroup g in groups.Values)
            {
                if (string.Equals(g.Id, groupId, StringComparison.OrdinalIgnoreCase))
                {
                    group = g;
                    return true;
                }
            }
            group = null;
            return false;
        }
    }
}
