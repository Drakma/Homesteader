using System.Collections;
using System.Collections.Generic;
using Homesteader.Generation;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A shovel (a container that accepts the #bulk shovelfuls) in the active slot digs sand out of sandy ground: a right click on sand (the beaches and the
    /// sand pit, biome_sand) takes one swing and puts one shovelful of sand on the shovel. The ground does not run out. The sand is then moved like any
    /// other shovelful: into a wheelbarrow, or tipped in a heap.
    /// </summary>
    public static class SandDigger
    {
        public const string SandScoop = "mat_scoop_sand";
        private const float ReachM = 3.5f;
        private const float SwingSeconds = 1.2f;

        /// <summary>True when the active slot holds a shovel (the #tool_shovel tag) that can carry sand.</summary>
        public static bool ShovelHeld()
        {
            string held = ConstructionSite.HeldItem();
            return !string.IsNullOrEmpty(held) && GrowthRegistry.ToolMatches("#tool_shovel", held) && ContainerRules.IsContainer(held);
        }

        /// <summary>The sandy ground under the cursor (not water, nothing standing on it), with the point to dig at.</summary>
        public static bool SandUnderCursor(Camera cam, Vector2 pointer, out Vector3 point)
        {
            point = default;
            if (cam == null) return false;
            Ray ray = cam.ScreenPointToRay(pointer);
            RaycastHit[] hits = Homesteader.UI.HoverTarget.SortedHits(cam, pointer);
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                if (h.collider.GetComponentInParent<Terrain>() == null) return false;   // something else is in front of the ground
                point = h.point;
                var gen = Tiller.GeneratorShared();
                if (gen == null) return false;
                Vector3 origin = gen.transform.position;
                float lx = point.x - origin.x, lz = point.z - origin.z;
                if (gen.IsWaterAt(lx, lz)) return false;
                BiomeData biome = gen.EvaluateBiomeAt(lx, lz);
                return biome != null && biome.id == "biome_sand";
            }
            return false;
        }

        /// <summary>Right click with a shovel on sand: one swing, one shovelful. False when the active slot is not a shovel or the ground is not sand.</summary>
        public static bool TryDig(Camera cam, Vector2 pointer, Transform player)
        {
            if (!ShovelHeld() || !SandUnderCursor(cam, pointer, out Vector3 at)) return false;
            if (player != null && new Vector2(player.position.x - at.x, player.position.z - at.z).magnitude > ReachM)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to dig.");
                return true;
            }
            // check the shovel can take it before swinging
            HudState hud = HudState.Active;
            if (hud == null) return true;
            hud.EnsureToolbarSlots();
            ToolbarSlotData slot = hud.Toolbar[hud.SelectedSlot];
            if (slot.Contents == null) slot.Contents = new List<ContainerStack>();
            string shovelName = HudBindings.GetItemName(slot.IconId);
            if (!ContainerRules.Accepts(slot.IconId, SandScoop, slot.Contents))
            {
                ToastNotificationSystem.ShowInfo(shovelName, shovelName + " already holds something else. Tip it out first.");
                return true;
            }
            if (ContainerRules.RoomFor(slot.IconId, slot.Contents, SandScoop) <= 0)
            {
                ToastNotificationSystem.ShowInfo(shovelName, shovelName + " is full.");
                return true;
            }
            var ped = player != null ? player.GetComponent<PedController>() : PedController.Current;
            if (ped == null) { Add(); return true; }
            ped.gameObject.AddComponent<DigJob>().Run(ped, at);
            return true;
        }

        private static void Add()
        {
            HudState hud = HudState.Active;
            if (hud == null) return;
            int index = hud.SelectedSlot;
            if (index < 0 || index >= hud.Toolbar.Count) return;
            ToolbarSlotData slot = hud.Toolbar[index];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId) || !ContainerRules.IsContainer(slot.IconId)) return;   // the shovel was put away during the swing
            if (slot.Contents == null) slot.Contents = new List<ContainerStack>();
            // one dig fills the shovel: as many shovelfuls as it has room for
            int dug = ContainerRules.Add(slot.IconId, slot.Contents, SandScoop, Mathf.Max(1, ContainerRules.RoomFor(slot.IconId, slot.Contents, SandScoop)));
            if (dug <= 0) return;
            hud.Toolbar[index] = slot;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
        }

        private sealed class DigJob : MonoBehaviour
        {
            public void Run(PedController ped, Vector3 at) { StartCoroutine(Go(ped, at)); }

            private IEnumerator Go(PedController ped, Vector3 at)
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
                if (!cancelled) Add();
                Destroy(this);
            }
        }
    }
}
