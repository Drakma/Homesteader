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

        /// <summary>
        /// Animals: what an animal becomes when it reaches this stage (female 80% / male 20%), each with its own model in the stage's folder. Empty = no
        /// split (baby and yearling are sexless). The stage's own Model is the default.
        /// </summary>
        public readonly List<GrowthSex> Sexes = new List<GrowthSex>();

        /// <summary>The sex an animal reaching this stage becomes, for a roll of 0..1 (null when the stage has no split): the chances run in the order they are listed.</summary>
        public GrowthSex PickSex(float roll01)
        {
            float at = roll01 * 100f, sum = 0f;
            foreach (GrowthSex s in Sexes)
            {
                sum += s.ChancePct;
                if (at < sum) return s;
            }
            return Sexes.Count > 0 ? Sexes[Sexes.Count - 1] : null;
        }

        /// <summary>The same roll from a stable seed (an animal's id), so it keeps its sex across a reload.</summary>
        public GrowthSex PickSex(int seed)
        {
            return PickSex(new System.Random(seed).Next(0, 10000) / 10000f);
        }
    }

    /// <summary>One of the sexes an animal can become at a stage (stage `sexes`): its chance, and its model.</summary>
    public sealed class GrowthSex
    {
        public string Sex;          // female | male
        public float ChancePct;
        public string Model;
        public string Icon;
        public GameObject Prefab;   // resolved from the stage's resource folder; null when no prefab was generated
        public bool IsMale => Sex == "male";
    }

    /// <summary>A withered / dead version of a plant (failure.withered / failure.dead): a model like a stage.</summary>
    public sealed class GrowthVariant
    {
        public string Resource;
        public string Model;
        public string Icon;
        /// <summary>Resolved through the mod asset resolver; null when no prefab was generated.</summary>
        public GameObject Prefab;

        public static GrowthVariant Parse(ModJsonValue v)
        {
            string resource = v.Get("resource").AsString();
            string model = v.Get("model").AsString();
            if (string.IsNullOrEmpty(resource) || string.IsNullOrEmpty(model)) return null;
            return new GrowthVariant { Resource = resource, Model = model, Icon = v.Get("icon").AsString() };
        }
    }

    /// <summary>
    /// A group's growth.rules block (growth_group.schema.json). Trees and crops
    /// only. Every field has the schema's default, so a missing block means
    /// "no restriction / cannot fail".
    /// </summary>
    /// <summary>One drop: an item and a whole-number range rolled each time it is given.</summary>
    public sealed class GrowthDrop
    {
        public string ItemId;
        public int Min = 1;
        public int Max = 1;

        public int Roll()
        {
            int lo = Mathf.Max(1, Min);
            int hi = Mathf.Max(lo, Max);
            return UnityEngine.Random.Range(lo, hi + 1);   // the int overload's upper bound is exclusive
        }

        public static List<GrowthDrop> ParseList(ModJsonValue v)
        {
            var list = new List<GrowthDrop>();
            if (v == null || v.IsNull) return list;
            foreach (ModJsonValue d in v.Items)
            {
                string id = d.Get("item_id").AsString();
                if (string.IsNullOrEmpty(id)) continue;
                int min = d.Get("amount_min").AsInt(1);
                list.Add(new GrowthDrop { ItemId = id, Min = min, Max = d.Get("amount_max").AsInt(min) });
            }
            return list;
        }

        /// <summary>Puts every drop on the toolbar. Returns false when something did not fit (the rest still went in).</summary>
        public static bool Give(IEnumerable<GrowthDrop> drops)
        {
            bool allFit = true;
            foreach (GrowthDrop d in drops)
            {
                int amount = d.Roll();
                int added = Homesteader.UI.HudState.Active.AddItemToToolbar(d.ItemId, amount, Homesteader.UI.HudBindings.GetMaxStack(d.ItemId));
                if (added < amount) allFit = false;
            }
            if (Homesteader.UI.HudBindings.Instance != null) Homesteader.UI.HudBindings.Instance.RefreshToolbar();
            return allFit;
        }
    }

    public sealed class GrowthRules
    {
        // yield
        public string YieldItemId;
        /// <summary>More than one yield: further drops given on every harvest, on top of YieldItemId.</summary>
        public readonly List<GrowthDrop> YieldExtras = new List<GrowthDrop>();

        // fruit (trees): picking, separate from the harvest / felling above
        public bool Fruiting;
        public int FruitStage;                 // 0 = the final stage
        public float FruitRegrowDays = 30f;
        /// <summary>What picks the fruit: item ids / "#tags", comma separated, any ONE in the active slot (see GrowthRegistry.ToolMatches); empty = by hand.</summary>
        public string FruitTool = "";
        public readonly List<GrowthDrop> FruitDrops = new List<GrowthDrop>();
        public int YieldAmountMin;
        public int YieldAmountMax;

        /// <summary>A random WHOLE number from YieldAmountMin to YieldAmountMax, both inclusive.</summary>
        public int RollYield()
        {
            int lo = Mathf.Max(1, YieldAmountMin);
            int hi = Mathf.Max(lo, YieldAmountMax);
            return UnityEngine.Random.Range(lo, hi + 1);   // the int overload's upper bound is exclusive
        }
        public int HarvestStage;      // 0 = final stage
        public bool Regrows;
        public int RegrowStage;
        /// <summary>Item id or "#tag" of what harvests it; empty = by hand.</summary>
        public string YieldTool;
        /// <summary>Trees: the stump left standing after the tree is harvested (null = the tree is removed).</summary>
        public GrowthVariant Stump;

        // planting
        /// <summary>The item that plants this group (a seed / sapling); empty = nothing plants it.</summary>
        public string PlantItemId;
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
        public GrowthVariant Withered;              // shown while withering (null = keep the current stage)
        public GrowthVariant Dead;                  // shown once dead (null = the plant is removed)

        public bool YearRound => Seasons.Count == 0 || Seasons.Contains("year_round");

        public static GrowthRules Parse(ModJsonValue r)
        {
            var rules = new GrowthRules();
            if (r == null || r.IsNull) return rules;

            ModJsonValue y = r.Get("yield");
            rules.YieldItemId = y.Get("item_id").AsString();
            // amount_min / amount_max; the legacy single "amount" is used for both.
            int legacyAmount = y.Get("amount").AsInt(0);
            rules.YieldAmountMin = y.Get("amount_min").AsInt(legacyAmount);
            rules.YieldAmountMax = y.Get("amount_max").AsInt(rules.YieldAmountMin);
            rules.HarvestStage = y.Get("harvest_stage").AsInt(0);
            rules.Regrows = y.Get("regrows").AsBool(false);
            rules.RegrowStage = y.Get("regrow_stage").AsInt(0);
            // Harvest tools: "tools" (a list, any ONE of them works) or the legacy single "tool". Kept as one comma-separated
            // spec so every consumer asks GrowthRegistry.ToolMatches, which understands the list.
            var toolList = new List<string>(y.Get("tools").AsStringList());
            if (toolList.Count == 0 && !string.IsNullOrEmpty(y.Get("tool").AsString())) toolList.Add(y.Get("tool").AsString());
            rules.YieldTool = string.Join(",", toolList);
            rules.Stump = GrowthVariant.Parse(y.Get("stump"));
            rules.YieldExtras.AddRange(GrowthDrop.ParseList(y.Get("extras")));

            ModJsonValue fr = r.Get("fruit");
            rules.Fruiting = fr.Get("is_fruiting").AsBool(false);
            if (rules.Fruiting)
            {
                rules.FruitStage = fr.Get("fruit_stage").AsInt(0);
                rules.FruitRegrowDays = Mathf.Max(1f, fr.Get("regrow_days").AsFloat(30f));
                rules.FruitTool = string.Join(",", new List<string>(fr.Get("tools").AsStringList()));
                rules.FruitDrops.AddRange(GrowthDrop.ParseList(fr.Get("drops")));
            }

            ModJsonValue p = r.Get("planting");
            rules.PlantItemId = p.Get("item_id").AsString();
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
            rules.Withered = GrowthVariant.Parse(f.Get("withered"));
            rules.Dead = GrowthVariant.Parse(f.Get("dead"));
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
                foreach (ModJsonValue sx in s.Get("sexes").Items)
                {
                    var sex = new GrowthSex { Sex = sx.Get("sex").AsString("female"), ChancePct = sx.Get("chance_pct").AsFloat(0f), Model = sx.Get("model").AsString(), Icon = sx.Get("icon").AsString() };
                    if (string.IsNullOrEmpty(sex.Model)) continue;
                    var asStage = new GrowthStage { Stage = stage.Stage, Name = sex.Sex, Resource = stage.Resource, Model = sex.Model };
                    sex.Prefab = ResolveStagePrefab(mod, groupDir, asStage, resolver, warn);
                    stage.Sexes.Add(sex);
                }
                result.Stages.Add(stage);
            }
            result.Stages.Sort((a, b) => a.Stage.CompareTo(b.Stage));

            if (result.IsPlantable)
            {
                result.Rules = GrowthRules.Parse(g.Get("rules"));

                // Withered / dead versions are resource folders just like stages.
                foreach (GrowthVariant variant in new[] { result.Rules.Withered, result.Rules.Dead, result.Rules.Stump })
                {
                    if (variant == null) continue;
                    string variantName = variant == result.Rules.Withered ? "withered" : variant == result.Rules.Dead ? "dead" : "stump";
                    var asStage = new GrowthStage { Stage = 0, Name = variantName, Resource = variant.Resource, Model = variant.Model };
                    variant.Prefab = ResolveStagePrefab(mod, groupDir, asStage, resolver, warn);
                }
            }

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

    /// <summary>
    /// Everything mods have contributed at runtime: growth groups (which own what
    /// plants them) and the tag registry. ModLoader is the only writer (merge rules stay in one file);
    /// gameplay code only reads.
    /// </summary>
    public static class GrowthRegistry
    {
        private static readonly Dictionary<string, GrowthGroup> groups =
            new Dictionary<string, GrowthGroup>(StringComparer.OrdinalIgnoreCase);
        // Item id -> the group it plants (from each group's rules.planting.item_id).
        private static readonly Dictionary<string, GrowthGroup> plantItems =
            new Dictionary<string, GrowthGroup>(StringComparer.OrdinalIgnoreCase);

        public static IEnumerable<GrowthGroup> Groups => groups.Values;

        // Tag registry ("#tag" -> member item ids), union-merged from every mod's tags.json.
        private static readonly Dictionary<string, HashSet<string>> tags =
            new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);

        // Equivalencies inside a tag: what each member is worth in the tag's units (default 1) and the unit word (see material_tags.json tag_values).
        private static readonly Dictionary<string, Dictionary<string, float>> tagValues =
            new Dictionary<string, Dictionary<string, float>>(StringComparer.OrdinalIgnoreCase);
        private static readonly Dictionary<string, string> tagUnits = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        public static void Clear()
        {
            groups.Clear();
            plantItems.Clear();
            tags.Clear();
            tagValues.Clear();
            tagUnits.Clear();
        }

        /// <summary>Sets what members of a tag are worth (1 large bundle = 20, 1 small = 10, a stud = 1 ...) and the unit word.</summary>
        public static void RegisterTagValues(string name, string unit, IDictionary<string, float> values)
        {
            if (string.IsNullOrEmpty(name)) return;
            if (!string.IsNullOrEmpty(unit)) tagUnits[name] = unit;
            if (values == null) return;
            if (!tagValues.TryGetValue(name, out Dictionary<string, float> map))
                tagValues[name] = map = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
            foreach (var kv in values) if (kv.Value > 0f) map[kv.Key] = kv.Value;
        }

        /// <summary>What one of this item counts for against a recipe spec: its value in the "#tag" (default 1), or 1 for a plain item id.</summary>
        public static float UnitValue(string spec, string itemId)
        {
            if (string.IsNullOrEmpty(spec) || spec[0] != '#') return 1f;
            return tagValues.TryGetValue(spec.Substring(1), out Dictionary<string, float> map) && map.TryGetValue(itemId, out float v) ? v : 1f;
        }

        /// <summary>The unit word of a "#tag" (for example "studs"), or null.</summary>
        public static string UnitName(string spec)
        {
            return !string.IsNullOrEmpty(spec) && spec[0] == '#' && tagUnits.TryGetValue(spec.Substring(1), out string u) ? u : null;
        }

        /// <summary>Adds members to a tag, creating it if needed (union, so mods can share one registry).</summary>
        public static void RegisterTag(string name, IEnumerable<string> members)
        {
            if (string.IsNullOrEmpty(name) || members == null) return;
            if (!tags.TryGetValue(name, out HashSet<string> set))
                tags[name] = set = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (string m in members)
                if (!string.IsNullOrEmpty(m)) set.Add(m);
        }

        /// <summary>
        /// True when <paramref name="itemId"/> satisfies a tool spec: the spec is that exact item id,
        /// or "#tag" and the item is a member of the tag.
        /// </summary>
        /// <summary>Every item id a tool spec accepts (a comma list of item ids and #tags, tags expanded), in a stable order.</summary>
        public static List<string> ToolItems(string toolSpec)
        {
            var result = new List<string>();
            if (string.IsNullOrEmpty(toolSpec)) return result;
            foreach (string one in toolSpec.Split(','))
            {
                string spec = one.Trim();
                if (spec.Length == 0) continue;
                if (spec[0] != '#') { if (!result.Contains(spec)) result.Add(spec); continue; }
                if (!tags.TryGetValue(spec.Substring(1), out HashSet<string> members)) continue;
                var sorted = new List<string>(members);
                sorted.Sort(StringComparer.OrdinalIgnoreCase);
                foreach (string id in sorted) if (!result.Contains(id)) result.Add(id);
            }
            return result;
        }

        public static bool ToolMatches(string toolSpec, string itemId)
        {
            if (string.IsNullOrEmpty(toolSpec) || string.IsNullOrEmpty(itemId)) return false;
            if (toolSpec.IndexOf(',') >= 0)
            {
                // A list of tools: any one of them (an item id or a #tag) is enough.
                foreach (string one in toolSpec.Split(','))
                    if (ToolMatches(one.Trim(), itemId)) return true;
                return false;
            }
            if (toolSpec[0] != '#')
                return string.Equals(toolSpec, itemId, StringComparison.OrdinalIgnoreCase);
            return tags.TryGetValue(toolSpec.Substring(1), out HashSet<string> members) && members.Contains(itemId);
        }

        /// <summary>First registration of a qualified id wins; returns false for a duplicate.</summary>
        public static bool Register(GrowthGroup group)
        {
            if (group == null || groups.ContainsKey(group.QualifiedId)) return false;
            groups[group.QualifiedId] = group;
            // First group to claim a planting item keeps it (the asset kit forbids duplicates).
            string item = group.Rules?.PlantItemId;
            if (!string.IsNullOrEmpty(item) && !plantItems.ContainsKey(item))
                plantItems[item] = group;
            return true;
        }

        /// <summary>The group a toolbar item plants, if any group names it as its planting item.</summary>
        public static bool TryGetGroupPlantedBy(string itemId, out GrowthGroup group)
        {
            group = null;
            return !string.IsNullOrEmpty(itemId) && plantItems.TryGetValue(itemId, out group);
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
