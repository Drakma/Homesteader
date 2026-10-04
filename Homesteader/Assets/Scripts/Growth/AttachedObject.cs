using System.Collections.Generic;
using Homesteader.Save;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Something mounted on a building's wall or ceiling (properties.attach_surface of its manifest): a breaker box, a wall sconce, a ceiling light.
    /// It is a child of the building's site, so it goes where the building goes, and it is saved with the building (GameSave.attached).
    /// An item with properties.provides_power (the outdoor breaker box) mounted on the OUTSIDE of a building brings electricity to that building:
    /// lights that need power (light "requires_power") stay dark in a building that has none. See docs/ATTACHED_ITEMS.md.
    /// </summary>
    public sealed class AttachedObject : MonoBehaviour
    {
        public static readonly List<AttachedObject> All = new List<AttachedObject>();

        public string ItemId { get; private set; }
        public ConstructionSite Site { get; private set; }
        public string Surface { get; private set; }        // wall | ceiling
        public bool Exterior { get; private set; }         // a wall item on the outside of the building
        public bool ProvidesPower { get; private set; }

        private void OnEnable() { if (!All.Contains(this)) All.Add(this); }
        private void OnDisable() { All.Remove(this); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { All.Clear(); }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void HookPower()
        {
            // Lights that need power ask here. Only attached things are gated: any other light that "requires power" keeps working as before.
            LightEmitter.PowerCheck = (id, pos, watts) =>
            {
                AttachedObject a = Nearest(pos, 0.75f);
                return a == null || a.Site == null || HasPower(a.Site);
            };
        }

        /// <summary>True while a power-providing item is mounted on the outside of this building.</summary>
        public static bool HasPower(ConstructionSite site)
        {
            if (site == null) return false;
            foreach (AttachedObject a in All)
                if (a != null && a.Site == site && a.ProvidesPower && a.Exterior) return true;
            return false;
        }

        private static AttachedObject Nearest(Vector3 pos, float within)
        {
            AttachedObject best = null;
            float bestD = within * within;
            foreach (AttachedObject a in All)
            {
                if (a == null) continue;
                float d = (a.transform.position - pos).sqrMagnitude;
                if (d < bestD) { bestD = d; best = a; }
            }
            return best;
        }

        // ------------------------------------------------------------------ making one

        /// <summary>Mounts a new one at a world position and rotation (a fresh placement or a restored save).</summary>
        public static AttachedObject Spawn(string itemId, ItemRegistry.ItemInfo info, ConstructionSite site, Vector3 worldPos, Quaternion worldRot)
        {
            if (info == null || info.Prefab == null || site == null) return null;
            GameObject obj = Instantiate(info.Prefab, site.transform);
            obj.name = "Attached_" + itemId;
            obj.SetActive(true);
            obj.transform.SetPositionAndRotation(worldPos, worldRot);
            // Walk-through: a small thing on a wall must not catch the character; its colliders are triggers (a ray that asks for triggers still finds it, to pick it up).
            foreach (MeshCollider mc in obj.GetComponentsInChildren<MeshCollider>(true)) { mc.convex = true; mc.isTrigger = true; }
            var a = obj.AddComponent<AttachedObject>();
            a.ItemId = itemId;
            a.Site = site;
            a.Surface = info.AttachSurface;
            a.ProvidesPower = info.ProvidesPower;
            a.Exterior = info.AttachSurface == "wall" && !site.IsInsideWalls(worldPos + worldRot * Vector3.forward * 0.1f);
            LightEmitter.Attach(obj, itemId, info.Lights);
            return a;
        }

        // ------------------------------------------------------------------ taking one down

        /// <summary>A right click on an attached item (within reach) takes it down into the toolbar. True when the click was for one.</summary>
        public static bool TryPickUpAtRay(Ray ray, Vector3 playerPos)
        {
            RaycastHit[] hits = Physics.RaycastAll(ray, 1000f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null) continue;
                AttachedObject a = h.collider.GetComponentInParent<AttachedObject>();
                if (a == null) return false;   // something else is in front
                if (new Vector2(a.transform.position.x - playerPos.x, a.transform.position.z - playerPos.z).magnitude > 4f)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to take it down.");
                    return true;
                }
                HudState hud = HudState.Active;
                if (hud == null) return false;
                if (hud.AddItemToToolbar(a.ItemId, 1, HudBindings.GetMaxStack(a.ItemId)) < 1)
                {
                    ToastNotificationSystem.ShowWarning("Toolbar full", "No room to take it down.");
                    return true;
                }
                HudBindings.Instance?.RefreshToolbar();
                bool hadPower = a.ProvidesPower;
                Destroy(a.gameObject);
                if (hadPower) ToastNotificationSystem.ShowInfo("Power", "The building has no electricity now.");
                return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ saving

        public static List<GameSave.SavedAttached> Capture()
        {
            var list = new List<GameSave.SavedAttached>();
            foreach (AttachedObject a in All)
            {
                if (a == null || a.Site == null) continue;
                int idx = ConstructionSite.All.IndexOf(a.Site);
                if (idx < 0) continue;
                Transform t = a.transform;
                list.Add(new GameSave.SavedAttached { itemId = a.ItemId, siteIndex = idx, localPosition = a.Site.transform.InverseTransformPoint(t.position), localRotation = Quaternion.Inverse(a.Site.transform.rotation) * t.rotation });
            }
            return list;
        }
    }
}
