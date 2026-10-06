using System.Collections;
using Homesteader.UI;
using Homesteader.World;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The pickaxe on stones. With a pickaxe (the #tool_pickaxe tag) in the active slot, a right click on a stone breaks it into aggregate: gravel
    /// shovelfuls dropped as piles. A stone is a scattered rock of the world (<see cref="WorldRocks"/>) or a stone item lying on the ground (the #stone tag).
    /// The yield goes with the stone's weight: a quarter of it comes out as aggregate, at 4 kg a shovelful (the rest is dust), at least one shovelful, at most
    /// one large pile.
    /// </summary>
    public static class StoneBreaker
    {
        public const string AggregateScoop = "mat_scoop_gravel";
        private const float YieldShare = 0.25f;
        private const int MaxScoops = 150;
        private const float ReachM = 3.5f;
        private const float SwingSeconds = 1.4f;

        public static bool PickaxeHeld()
        {
            string held = ConstructionSite.HeldItem();
            return !string.IsNullOrEmpty(held) && GrowthRegistry.HeldToolMatches("#tool_pickaxe", held);
        }

        public static bool IsStoneItem(string itemId) => GrowthRegistry.ToolMatches("#stone", itemId);

        /// <summary>The stone under the cursor: a stone item lying on the ground, or a rock of the world.</summary>
        public static bool StoneUnderCursor(Camera cam, Vector2 pointer, out WorldItem item, out WorldRock rock)
        {
            item = null; rock = null;
            if (cam == null) return false;
            WorldItem lying = WorldItem.UnderCursor(cam, pointer);
            if (lying != null && IsStoneItem(lying.ItemId)) { item = lying; return true; }
            if (lying != null) return false;   // some other item is under the cursor: it is that one the click is for
            rock = WorldRocks.TryPick(cam.ScreenPointToRay(pointer));
            return rock != null;
        }

        /// <summary>The shovelfuls of aggregate a stone of this weight gives.</summary>
        public static int ScoopsFor(float weightKg)
        {
            float scoopKg = ContainerRules.WeightOf(AggregateScoop);
            return Mathf.Clamp(Mathf.RoundToInt(weightKg * YieldShare / scoopKg), 1, MaxScoops);
        }

        /// <summary>Right click with a pickaxe: starts breaking the stone under the cursor. False when the active slot is not a pickaxe or nothing breakable is there.</summary>
        public static bool TryBreak(Camera cam, Vector2 pointer, Transform player)
        {
            if (!PickaxeHeld()) return false;
            if (!StoneUnderCursor(cam, pointer, out WorldItem item, out WorldRock rock)) return false;
            Vector3 at = item != null ? item.transform.position : rock.Position;
            if (player != null && (new Vector2(player.position.x - at.x, player.position.z - at.z)).magnitude > ReachM + (rock != null ? rock.Radius : 0f))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the stone.");
                return true;
            }
            var ped = player != null ? player.GetComponent<PedController>() : PedController.Current;
            if (ped == null) { Finish(item, rock, at, player); return true; }
            var job = ped.gameObject.AddComponent<BreakJob>();
            job.Run(ped, item, rock, at);
            return true;
        }

        internal static void Finish(WorldItem item, WorldRock rock, Vector3 at, Transform player)
        {
            float weight;
            if (item != null)
            {
                weight = ContainerRules.WeightOf(item.ItemId);
                Object.Destroy(item.gameObject);
            }
            else
            {
                if (rock.IsBroken) return;
                weight = rock.WeightKg;
                WorldRocks.Break(rock);
            }
            int scoops = ScoopsFor(weight);
            Vector3 along = player != null ? (player.position - at).normalized : Vector3.back;
            along.y = 0f;
            if (along.sqrMagnitude < 0.01f) along = Vector3.back;
            PileService.AddAt(AggregateScoop, scoops, at + along.normalized * 0.4f, Random.Range(0f, 360f));   // onto a gravel pile there, or a new one
        }

        /// <summary>The swing: the ped works at the stone for a moment (any movement key stops it), then the stone breaks.</summary>
        private sealed class BreakJob : MonoBehaviour
        {
            public void Run(PedController ped, WorldItem item, WorldRock rock, Vector3 at) { StartCoroutine(Go(ped, item, rock, at)); }

            private IEnumerator Go(PedController ped, WorldItem item, WorldRock rock, Vector3 at)
            {
                bool animated = ped.BeginWork("Dig", at);
                float end = Time.time + SwingSeconds;
                bool cancelled = false;
                while (Time.time < end)
                {
                    if (ped.ManualInput) { cancelled = true; break; }
                    yield return null;
                }
                if (animated) ped.EndWork("Dig");
                if (!cancelled && (item != null || rock != null)) Finish(item, rock, at, ped.transform);
                Destroy(this);
            }
        }
    }
}
