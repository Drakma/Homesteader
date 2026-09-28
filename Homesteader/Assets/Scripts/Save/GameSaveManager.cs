using System.Collections;
using System.Collections.Generic;
using Homesteader.Growth;
using Homesteader.Modding;
using Homesteader.UI;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.Save
{
    /// <summary>
    /// Saves the game as it goes and puts it back where it left off. On start it waits for the mods, terrain, player and HUD to
    /// exist, then restores the last save (time, player, toolbar, vitals, resources, plants, placed structures, dropped items).
    /// Only after that does it autosave (every <see cref="autosaveSeconds"/> real seconds, when Play stops or the app pauses
    /// or quits, and on F9), so a fresh world can never overwrite a save that has not been restored yet.
    ///
    /// The file is Application.persistentDataPath/Saves/autosave.json (previous good one: autosave.bak.json). Delete it to
    /// start a new game. Bootstraps itself; see docs/SAVE_GAME.md.
    /// </summary>
    public sealed class GameSaveManager : MonoBehaviour
    {
        public float autosaveSeconds = 30f;

        public static bool Restored { get; private set; }
        private float nextSave;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            Restored = false;
            if (FindAnyObjectByType<GameSaveManager>() != null) return;
            var go = new GameObject("GameSaveManager");
            DontDestroyOnLoad(go);
            go.AddComponent<GameSaveManager>();
        }

        private IEnumerator Start()
        {
            // Wait until everything a save refers to exists.
            float timeout = Time.realtimeSinceStartup + 60f;
            while (Time.realtimeSinceStartup < timeout)
            {
                bool ready = ModManager.Instance != null && ModManager.Instance.LoadComplete
                             && Terrain.activeTerrain != null
                             && FindAnyObjectByType<PedController>() != null
                             && HudBindings.Instance != null
                             && TimeSystem.Instance != null;
                if (ready) break;
                yield return null;
            }
            yield return new WaitForSecondsRealtime(1.0f);   // let the world settle (ground colliders, ped controller)

            GameSave save = GameSave.ReadFromDisk();
            if (save != null)
            {
                yield return ApplySave(save);
                Debug.Log($"[Save] restored the game saved {save.savedAtUtc} ({save.plants.Count} plants, {save.placed.Count} placed).");
            }
            else
            {
                Debug.Log("[Save] no save found: new game. Autosave is on.");
            }

            Restored = true;
            nextSave = Time.realtimeSinceStartup + autosaveSeconds;
        }

        private void Update()
        {
            if (!Restored) return;
            if (Time.realtimeSinceStartup >= nextSave)
            {
                SaveNow();
                nextSave = Time.realtimeSinceStartup + autosaveSeconds;
            }
            if (SavePressed() && !HudBindings.KeyboardCaptured)
            {
                SaveNow();
                ToastNotificationSystem.ShowWarning("Game saved", "Your progress is saved.");
            }
        }

        private void OnApplicationPause(bool paused) { if (paused && Restored) SaveNow(); }
        private void OnApplicationQuit() { if (Restored) SaveNow(); }

        private static bool SavePressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.f9Key.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.F9);
#endif
        }

        public static void SaveNow()
        {
            try { Capture().WriteToDisk(); }
            catch (System.Exception e) { Debug.LogWarning("[Save] could not save: " + e.Message); }
        }

        // ------------------------------------------------------------------ capture

        public static GameSave Capture()
        {
            var s = new GameSave();
            var gen = FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>();
            if (gen != null) s.worldSeed = gen.worldSeed;

            TimeSystem t = TimeSystem.Instance;
            s.dayOfYear = t.DayOfYear;
            s.minuteOfDay = t.MinuteOfDay;
            s.speed = (int)t.CurrentSpeed;
            s.weatherOverridden = t.IsWeatherOverridden;
            s.weather = (int)t.Weather;

            var ped = FindAnyObjectByType<PedController>();
            if (ped != null)
            {
                s.playerPosition = ped.transform.position;
                s.playerYaw = ped.transform.eulerAngles.y;
            }
            var cam = FindAnyObjectByType<IsometricLockedCamera>();
            if (cam != null)
            {
                s.cameraYaw = cam.yawDegrees;
                var c = cam.GetComponent<Camera>();
                if (c != null) s.cameraOrthoSize = c.orthographicSize;
            }

            HudState hud = HudState.Active;
            foreach (ToolbarSlotData slot in hud.Toolbar)
                s.toolbar.Add(new GameSave.SavedSlot { iconId = slot.IconId ?? "", count = slot.Count });
            s.selectedSlot = hud.SelectedSlot;
            foreach (var kv in hud.Vitals)
                s.vitals.Add(new GameSave.SavedVital { id = (int)kv.Key, value = kv.Value.Value });
            foreach (var kv in hud.Resources)
            {
                var r = new GameSave.SavedResource { id = (int)kv.Key, amount = kv.Value.Amount, subKeys = new List<string>(), subValues = new List<float>() };
                if (kv.Value.Subspecies != null)
                    foreach (var sub in kv.Value.Subspecies) { r.subKeys.Add(sub.Key); r.subValues.Add(sub.Value); }
                s.resources.Add(r);
            }
            s.loanDebt = hud.LoanDebt;

            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null || p.Group == null) continue;
                s.plants.Add(new GameSave.SavedPlant
                {
                    group = p.Group.QualifiedId, position = p.transform.position, yaw = p.transform.eulerAngles.y,
                    ageDays = p.AgeDays, state = (int)p.State,
                });
            }
            foreach (PlacedObject o in PlacedObject.All)
                if (o != null) s.placed.Add(new GameSave.SavedPlaced { itemId = o.ItemId, position = o.transform.position, yawDeg = o.YawDeg });
            foreach (WorldItem w in WorldItem.All)
                if (w != null) s.drops.Add(new GameSave.SavedDrop { itemId = w.ItemId, position = w.transform.position });
            return s;
        }

        // ------------------------------------------------------------------ apply

        private IEnumerator ApplySave(GameSave s)
        {
            // time
            TimeSystem t = TimeSystem.Instance;
            t.SetDayOfYear(s.dayOfYear);
            t.SetMinuteOfDay(s.minuteOfDay);
            if (s.weatherOverridden) t.SetWeather((HomesteaderWeather)s.weather, true);
            t.SetSpeed((HomesteaderSpeed)s.speed);

            // HUD state
            HudState hud = HudState.Active;
            hud.Toolbar.Clear();
            for (int i = 0; i < HudState.ToolbarSize; i++)
                hud.Toolbar.Add(i < s.toolbar.Count
                    ? new ToolbarSlotData { IconId = s.toolbar[i].iconId, Count = s.toolbar[i].count }
                    : ToolbarSlotData.Empty());
            hud.SelectedSlot = Mathf.Clamp(s.selectedSlot, 0, HudState.ToolbarSize - 1);
            foreach (var v in s.vitals) hud.SetVitalValue((VitalId)v.id, v.value);
            foreach (var r in s.resources)
            {
                var id = (ResourceId)r.id;
                hud.SetResourceAmount(id, r.amount);
                if (r.subKeys != null && hud.Resources.TryGetValue(id, out Resource res) && res.Subspecies != null)
                    for (int i = 0; i < r.subKeys.Count && i < r.subValues.Count; i++) res.Subspecies[r.subKeys[i]] = r.subValues[i];
            }
            hud.LoanDebt = s.loanDebt;
            HudBindings.Instance.RefreshToolbar();

            // player + camera
            var ped = FindAnyObjectByType<PedController>();
            if (ped != null)
            {
                var cc = ped.GetComponent<CharacterController>();
                if (cc != null) cc.enabled = false;             // a CharacterController ignores direct position changes
                Vector3 ppos = s.playerPosition;
                ppos.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(ppos);
                ped.transform.SetPositionAndRotation(ppos, Quaternion.Euler(0f, s.playerYaw, 0f));
                if (cc != null) cc.enabled = true;
            }
            var cam = FindAnyObjectByType<IsometricLockedCamera>();
            if (cam != null)
            {
                cam.yawDegrees = s.cameraYaw;
                var c = cam.GetComponent<Camera>();
                if (c != null && s.cameraOrthoSize > 0f) c.orthographicSize = s.cameraOrthoSize;
            }

            // plants
            var groups = new Dictionary<string, GrowthGroup>(System.StringComparer.OrdinalIgnoreCase);
            foreach (GrowthGroup g in GrowthRegistry.Groups) groups[g.QualifiedId] = g;
            Transform plantedRoot = (GameObject.Find("PlantedGrowth") ?? new GameObject("PlantedGrowth")).transform;
            foreach (var sp in s.plants)
            {
                if (!groups.TryGetValue(sp.group, out GrowthGroup group)) { Debug.LogWarning($"[Save] plant group '{sp.group}' no longer exists; skipped."); continue; }
                PlantedGrowth p = PlantedGrowth.Plant(group, sp.position, plantedRoot);
                p.transform.rotation = Quaternion.Euler(0f, sp.yaw, 0f);
                p.SetAgeDays(sp.ageDays);
                p.RestoreState((PlantedGrowth.PlantState)sp.state);
            }

            // placed structures / props: their models load lazily, so wait for each template
            foreach (var so in s.placed)
            {
                if (!ItemRegistry.TryGet(so.itemId, out ItemRegistry.ItemInfo info)) { Debug.LogWarning($"[Save] placed item '{so.itemId}' is not loaded; skipped."); continue; }
                GlbTemplate glb = info.Prefab != null ? info.Prefab.GetComponent<GlbTemplate>() : null;
                if (glb != null)
                {
                    glb.EnsureLoading();
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
                    if (!glb.Ready) continue;
                }
                PlacementController.SpawnPlaced(so.itemId, info, so.position, so.yawDeg, false);
            }

            // dropped items
            foreach (var d in s.drops) WorldItem.TryDrop(d.itemId, d.position);
        }
    }
}
