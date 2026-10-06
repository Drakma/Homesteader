using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Piles of bulk material GROW as it is added. A pile holds a number of shovelfuls (0.005 m3 each); which of the pile items it is (tiny, small, medium, large:
    /// the stages of the material's equivalency) follows from how many it holds, up to the largest (150). Adding or taking shovelfuls swaps the model to the stage
    /// that fits, and the model is scaled between stages (<see cref="PileVisual"/>). What does not fit in a full pile starts another pile next to it.
    /// A pile with no contents is a whole pile of its stage (what is bought or dropped from the toolbar); a part-filled one lists its shovelfuls as contents.
    /// </summary>
    public static class PileService
    {
        private const float MergeRadius = 1.25f;    // shovelfuls added within this of a pile of the same material go onto it
        private const float SpotClearance = 1.1f;   // a new pile keeps this far from other piles

        /// <summary>The stages of a material: (pile item id, shovelfuls when full), smallest first.</summary>
        public static List<KeyValuePair<string, int>> Stages(string scoopId) => GrowthRegistry.PilesOfScoop(scoopId);

        public static int MaxScoops(string scoopId)
        {
            List<KeyValuePair<string, int>> s = Stages(scoopId);
            return s.Count > 0 ? s[s.Count - 1].Value : 0;
        }

        /// <summary>The smallest stage that holds this many shovelfuls (the largest when none does).</summary>
        public static KeyValuePair<string, int> StageFor(string scoopId, int scoops)
        {
            List<KeyValuePair<string, int>> s = Stages(scoopId);
            foreach (var st in s) if (st.Value >= scoops) return st;
            return s.Count > 0 ? s[s.Count - 1] : default;
        }

        /// <summary>How many shovelfuls a pile holds (a whole pile of its stage when it has no contents).</summary>
        public static int ScoopsIn(PlacedObject pile, out string scoopId)
        {
            scoopId = null;
            if (pile == null || !GrowthRegistry.BulkOf(pile.ItemId, out scoopId, out int full)) return 0;
            int left = 0;
            if (pile.Contents != null) foreach (ContainerStack c in pile.Contents) left += c.Count;
            return left > 0 ? left : full;
        }

        /// <summary>The scale of a pile's model: its stage's own size when full, shrinking towards about half as it empties (the stage below takes over).</summary>
        public static float ScaleOf(PlacedObject pile)
        {
            int n = ScoopsIn(pile, out _);
            if (!GrowthRegistry.BulkOf(pile.ItemId, out _, out int full) || full <= 0 || n >= full) return 1f;
            return Mathf.Clamp(Mathf.Pow(n / (float)full, 1f / 3f), 0.55f, 1f);
        }

        /// <summary>Makes a pile hold exactly this many shovelfuls: its model changes to the stage that fits. At 0 the pile is gone. Returns the pile (a new object when the stage changed).</summary>
        public static PlacedObject SetScoops(PlacedObject pile, int scoops)
        {
            if (pile == null) return null;
            if (!GrowthRegistry.BulkOf(pile.ItemId, out string scoopId, out _)) return pile;
            if (scoops <= 0) { pile.Remove(); return null; }
            scoops = Mathf.Min(scoops, MaxScoops(scoopId));
            KeyValuePair<string, int> want = StageFor(scoopId, scoops);
            if (want.Key == pile.ItemId)
            {
                pile.Contents = scoops >= want.Value ? new List<ContainerStack>() : new List<ContainerStack> { new ContainerStack { ItemId = scoopId, Count = scoops } };
                return pile;
            }
            Vector3 pos = pile.transform.position;
            float yaw = pile.YawDeg;
            pile.Remove();
            return WheelbarrowPush.SpawnPileAt(want.Key, scoopId, scoops, pos, yaw);
        }

        /// <summary>Adds shovelfuls to a pile, up to its largest stage. Returns how many did not fit.</summary>
        public static int AddTo(PlacedObject pile, int scoops)
        {
            int cur = ScoopsIn(pile, out string scoopId);
            if (scoopId == null) return scoops;
            int take = Mathf.Min(scoops, Mathf.Max(0, MaxScoops(scoopId) - cur));
            if (take > 0) SetScoops(pile, cur + take);
            return scoops - take;
        }

        private static bool NearOtherPile(Vector3 at, float within)
        {
            foreach (PlacedObject o in PlacedObject.All)
                if (o != null && GrowthRegistry.BulkOf(o.ItemId, out _, out _) && (new Vector2(o.transform.position.x - at.x, o.transform.position.z - at.z)).magnitude < within) return true;
            return false;
        }

        /// <summary>
        /// Puts shovelfuls of a material on the ground at a point: onto a pile of that material already there (growing it), else as a new tiny pile that grows with
        /// the rest; what a full pile cannot take starts another pile next to it. Returns how many shovelfuls were placed.
        /// </summary>
        public static int AddAt(string scoopId, int scoops, Vector3 at, float yaw)
        {
            int remaining = scoops;
            // piles of this material close by, nearest first
            var near = new List<PlacedObject>();
            foreach (PlacedObject o in PlacedObject.All)
                if (o != null && GrowthRegistry.BulkOf(o.ItemId, out string sc, out _) && sc == scoopId && (new Vector2(o.transform.position.x - at.x, o.transform.position.z - at.z)).magnitude <= MergeRadius) near.Add(o);
            near.Sort((a, b) => (a.transform.position - at).sqrMagnitude.CompareTo((b.transform.position - at).sqrMagnitude));
            foreach (PlacedObject o in near)
            {
                if (remaining <= 0) break;
                if (o == null) continue;
                remaining = AddTo(o, remaining);
            }
            int max = MaxScoops(scoopId);
            if (max <= 0) return scoops - remaining;
            int guard = 0;
            while (remaining > 0 && guard++ < 24)
            {
                Vector3 spot = at;
                if (near.Count > 0 || NearOtherPile(at, SpotClearance))
                {
                    bool found = false;
                    for (float r = 1.3f; r < 5f && !found; r += 0.4f)
                        for (int k = 0; k < 8 && !found; k++)
                        {
                            float a = (k * 45f + (guard * 17f)) * Mathf.Deg2Rad;
                            Vector3 c = at + new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * r;
                            if (!NearOtherPile(c, SpotClearance)) { spot = c; found = true; }
                        }
                }
                int chunk = Mathf.Min(remaining, max);
                KeyValuePair<string, int> stage = StageFor(scoopId, chunk);
                if (WheelbarrowPush.SpawnPileAt(stage.Key, scoopId, chunk, spot, yaw) == null) break;
                remaining -= chunk;
                near.Clear();    // the next one is a new pile beside this one
            }
            return scoops - remaining;
        }

        /// <summary>A right click on a pile with a loaded shovel: everything on the shovel goes onto the pile (what does not fit is left on the shovel).</summary>
        public static bool TryPourOnto(PlacedObject pile)
        {
            if (!GrowthRegistry.BulkOf(pile.ItemId, out string scoopId, out _)) return false;
            HudState hud = HudState.Active;
            if (hud == null) return false;
            hud.EnsureToolbarSlots();
            int index = hud.SelectedSlot;
            if (index < 0 || index >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[index];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId) || !ContainerRules.IsContainer(slot.IconId) || slot.Contents == null) return false;
            ContainerStack mine = slot.Contents.Find(c => c.ItemId == scoopId && c.Count > 0);
            if (mine == null) return false;   // an empty shovel (or other material) takes from the pile instead
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, pile.transform.position, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the pile.");
                return true;
            }
            int before = mine.Count;
            int left = AddTo(pile, before);
            ContainerRules.Remove(slot.Contents, scoopId, before - left);
            hud.Toolbar[index] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            if (left > 0) ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(pile.ItemId), "The pile is full: start another beside it.");
            return true;
        }

        /// <summary>The active slot is a shovel (a container) with some bulk material on it.</summary>
        public static bool LoadedBulkShovel()
        {
            HudState hud = HudState.Active;
            if (hud == null || hud.SelectedSlot < 0 || hud.SelectedSlot >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId) || !ContainerRules.IsContainer(slot.IconId) || slot.Contents == null) return false;
            foreach (ContainerStack st in slot.Contents)
                if (st.Count > 0 && GrowthRegistry.ToolMatches("#bulk", st.ItemId)) return true;
            return false;
        }

        /// <summary>A right click on open ground with a loaded shovel: empties it there, onto a pile of the material close by or as a new one.</summary>
        public static bool TryPourOnGround(Camera cam, Vector2 pointer, Transform player)
        {
            if (cam == null) return false;
            HudState hud = HudState.Active;
            if (hud == null) return false;
            hud.EnsureToolbarSlots();
            int index = hud.SelectedSlot;
            if (index < 0 || index >= hud.Toolbar.Count) return false;
            ToolbarSlotData slot = hud.Toolbar[index];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId) || !ContainerRules.IsContainer(slot.IconId) || slot.Contents == null || slot.Contents.Count == 0) return false;
            if (!Tiller.GroundUnderCursor(cam, pointer, out Vector3 at)) return false;
            if (player != null && new Vector2(player.position.x - at.x, player.position.z - at.z).magnitude > 3.5f)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to empty it there.");
                return true;
            }
            foreach (ContainerStack st in new List<ContainerStack>(slot.Contents))
            {
                if (!GrowthRegistry.ToolMatches("#bulk", st.ItemId) || st.Count <= 0) continue;
                int placed = AddAt(st.ItemId, st.Count, at, Random.Range(0f, 360f));
                if (placed <= 0)
                {
                    List<KeyValuePair<string, int>> stages = Stages(st.ItemId);
                    string first = stages.Count > 0 ? stages[0].Key : "(none)";
                    Debug.LogWarning("[Piles] could not place " + st.Count + " x " + st.ItemId + ": " + stages.Count + " pile stage(s), first " + first
                        + ", registered " + (ItemRegistry.TryGet(first, out ItemRegistry.ItemInfo fi) && fi.Prefab != null));
                    ToastNotificationSystem.ShowInfo(HudBindings.GetItemName(st.ItemId), "Can't make a pile here.");
                }
                ContainerRules.Remove(slot.Contents, st.ItemId, placed);
            }
            hud.Toolbar[index] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            return true;
        }
    }
}
