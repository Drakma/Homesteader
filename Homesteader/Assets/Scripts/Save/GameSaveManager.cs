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
    /// The files are in the Saves folder next to the game (see SaveSlots.cs and docs/SAVE_GAME.md). Delete them to
    /// start a new game. Bootstraps itself; see docs/SAVE_GAME.md.
    /// </summary>
    public sealed class GameSaveManager : MonoBehaviour
    {
        public float autosaveSeconds = 30f;

        public static bool Restored { get; private set; }
        /// <summary>Real time (Time.realtimeSinceStartup) the load finished; the power alerts stay quiet for a few seconds after it while the grid settles.</summary>
        public static float RestoredAt { get; private set; }
        /// <summary>How far the load of a save has got (0 to 1) and what it is doing: the welcome menu's progress bar shows them.</summary>
        public static float LoadProgress { get; private set; }
        public static string LoadPhase { get; private set; } = "";
        private static void Step(float progress, string phase) { LoadProgress = progress; LoadPhase = phase; }
        private float nextSave;

        private static bool s_hooked;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { s_hooked = false; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            Restored = false;
            Step(0f, "Loading...");
            // New Game and Continue reload the scene after destroying the old manager. AfterSceneLoad only runs once when the
            // game starts, so without this hook nothing re-created the manager: no autosave, no save on quit, and the
            // placed objects and toolbar of that session were never written.
            if (!s_hooked)
            {
                s_hooked = true;
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) => { Restored = false; EnsureExists(); };
            }
            EnsureExists();
        }

        private static void EnsureExists()
        {
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
                             && (FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>() == null || FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>().Generated)
                             && PedController.Current != null
                             && HudBindings.Instance != null
                             && TimeSystem.Instance != null;
                if (ready) break;
                yield return null;
            }
            yield return new WaitForSecondsRealtime(1.0f);   // let the world settle (ground colliders, ped controller)

            string loadPath = SaveSlots.ResolveLoadPath();   // the save picked in the Load list, else the newest (also makes its game the current one)
            SaveSlots.PendingLoadPath = null;
            GameSave save = GameSave.ReadFrom(loadPath);
            if (save != null)
            {
                if (!string.IsNullOrEmpty(save.gameName)) SaveSlots.CurrentName = save.gameName;
                yield return ApplySave(save);
                // everything must be standing before the load screen goes: the buildings' models put up, the ground graded under them, the
                // objects set down onto the ground as it is now
                Step(0.85f, "Raising buildings...");
                float upUntil = Time.realtimeSinceStartup + 40f;
                while (ConstructionSite.AnyModelPending && Time.realtimeSinceStartup < upUntil) yield return null;
                yield return new WaitForSecondsRealtime(0.3f);
                Step(0.95f, "Settling objects...");
                PlacedObject.SettleOnGround();
                yield return null;
                PlacedObject.SettleOnGround();
                yield return PlacePedOnSurface(save.playerPosition);
                Step(1f, "Ready");
                Dbg.Log($"[Save] restored '{SaveSlots.CurrentName}' saved {save.savedAtUtc} ({save.plants.Count} plants, {save.placed.Count} placed) from {System.IO.Path.GetFileName(loadPath)}.");
            }
            else
            {
                Dbg.Log("[Save] no save found: new game. Autosave is on.");
            }

            // the music starts only now: the game is loaded and the saved state is known (a radio station tuned in means no music)
            if (Homesteader.Audio.AudioManager.Instance != null)
                Homesteader.Audio.AudioManager.Instance.StartMusicAfterLoad(save == null || (save.musicPlaying && string.IsNullOrEmpty(save.radioStation)));

            Restored = true;
            RestoredAt = Time.realtimeSinceStartup;
            s_lastAuto = Time.realtimeSinceStartup;
            StartCoroutine(ThumbnailLoop());
        }

        private void Update()
        {
            if (!Restored) return;
            // the interval is read every frame, so a change in Settings > General > Saving applies at once (it counts from the last autosave)
            if (Time.realtimeSinceStartup - s_lastAuto >= SaveSlots.AutosaveMinutes * 60f)
                SaveNow(true);
            if (SavePressed() && !HudBindings.KeyboardCaptured)
            {
                SaveNow(false);
                ToastNotificationSystem.ShowWarning("Game saved", "Saved as \"" + SaveSlots.CurrentName + "\".");
            }
        }

        private void OnApplicationPause(bool paused) { if (paused && Restored && Time.realtimeSinceStartup - s_lastSave > 30f) SaveNow(true); }   // (not on every focus change: it would roll the real autosaves away)
        private void OnApplicationQuit() { if (Restored) SaveNow(true); }

        private static bool SavePressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.f9Key.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.F9);
#endif
        }

        /// <summary>
        /// Takes away everything the player made in the world being left: placed objects, dropped items, construction sites, plants,
        /// and any delivery order or van. New Game generates the new world in place (no scene reload), so without this the old
        /// world's objects stayed standing in the new one.
        /// </summary>
        public static void ClearPlayerMadeWorld()
        {
            foreach (PlacedObject o in PlacedObject.All) if (o != null) o.Remove();
            foreach (WorldItem w in new List<WorldItem>(WorldItem.All)) if (w != null) Object.Destroy(w.gameObject);
            WireNetwork.Clear();
            ConstructionSite.Clear();
            FenceRun.Clear();
            PathRun.Clear();
            LotRun.Clear();
            foreach (PlantedGrowth p in new List<PlantedGrowth>(PlantedGrowth.All))
            {
                if (p == null) continue;
                PlantedGrowth.All.Remove(p);
                Object.Destroy(p.gameObject);
            }
            Homesteader.World.DeliveryService.Reset();
        }

        /// <summary>
        /// Saves the game. An autosave goes to Name-autosave.1 after rolling the older ones up (the oldest past the number kept is deleted); a
        /// manual save (the Save button, F9) goes to Name. Each gets the latest picture of the game beside it.
        /// </summary>
        private static float s_lastSave = -1000f, s_lastAuto;

        public static void SaveNow(bool autosave = false)
        {
            s_lastSave = Time.realtimeSinceStartup;
            if (autosave) s_lastAuto = s_lastSave;
            try
            {
                GameSave save = Capture();
                save.gameName = SaveSlots.CurrentName;
                string path;
                if (autosave) { SaveSlots.RollAutosaves(SaveSlots.CurrentName); path = SaveSlots.AutoPath(SaveSlots.CurrentName, 1); }
                else path = SaveSlots.ManualPath(SaveSlots.CurrentName);
                save.WriteTo(path);
                SaveSlots.WriteThumb(path);
            }
            catch (System.Exception e) { Debug.LogWarning("[Save] could not save: " + e.Message); }
            SaveWorldSnapshot();
        }

        /// <summary>
        /// Takes a small picture of the game every 45 seconds while it is being played (a screen read-back stalls the frame for a moment, so not oftener) (not while a menu covers it), the one saved beside a save and
        /// shown in the Load list.
        /// </summary>
        private IEnumerator ThumbnailLoop()
        {
            while (true)
            {
                yield return new WaitForSecondsRealtime(SaveSlots.Thumbnail == null ? 5f : 45f);
                if (!Restored || Homesteader.UI.WelcomeMenuController.MenuOpen || Homesteader.UI.WelcomeMenuController.IsLoading) continue;
                yield return new WaitForEndOfFrame();
                Texture2D shot = null;
                try { shot = ScreenCapture.CaptureScreenshotAsTexture(); }
                catch (System.Exception) { }
                if (shot == null) continue;
                const int w = 384, h = 216;
                var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
                Graphics.Blit(shot, rt);
                RenderTexture prev = RenderTexture.active;
                RenderTexture.active = rt;
                var small = new Texture2D(w, h, TextureFormat.RGB24, false);
                small.ReadPixels(new Rect(0, 0, w, h), 0, 0);
                small.Apply();
                RenderTexture.active = prev;
                RenderTexture.ReleaseTemporary(rt);
                SaveSlots.Thumbnail = small.EncodeToJPG(80);
                Destroy(shot);
                Destroy(small);
            }
        }

        /// <summary>Writes the generated ground beside the save, once per world (it never changes while the world exists), so the next run does not regenerate it.</summary>
        private static void SaveWorldSnapshot()
        {
            try
            {
                var gen = FindAnyObjectByType<Homesteader.Generation.HomesteaderTerrainGenerator>();
                if (gen == null || gen.LastGenerated == null || (!gen.SnapshotDirty && Homesteader.Generation.WorldSnapshot.Exists)) return;
                gen.LastGenerated.Write();
                gen.MarkSnapshotSaved();
                Dbg.Log("[Save] the generated world was saved (world.snapshot).");
            }
            catch (System.Exception e) { Debug.LogWarning("[Save] could not save the world snapshot: " + e.Message); }
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
            // a game paused by the menu (it pauses the clock while it is open) must not be saved as paused: it would load with time stopped and the player unable to walk
            s.speed = t.CurrentSpeed == HomesteaderSpeed.Pause ? (int)HomesteaderSpeed.Speed1X : (int)t.CurrentSpeed;
            s.weatherOverridden = t.IsWeatherOverridden;
            s.weather = (int)t.Weather;

            var ped = PedController.Current;
            if (ped != null)
            {
                s.playerPosition = ped.transform.position;
                s.playerYaw = ped.transform.eulerAngles.y;
            }
            var cam = IsometricLockedCamera.Current;
            if (cam != null)
            {
                s.cameraYaw = cam.TargetYaw;
                s.cameraPanned = cam.IsPanned;
                s.cameraFocal = cam.FocalPoint;
                var c = cam.GetComponent<Camera>();
                if (c != null) s.cameraOrthoSize = c.orthographicSize;
            }

            HudState hud = HudState.Active;
            foreach (ToolbarSlotData slot in hud.Toolbar)
            {
                var saved = new GameSave.SavedSlot { iconId = slot.IconId ?? "", count = slot.Count, wireUsed = slot.WireUsed, liquidId = slot.LiquidId };
                if (slot.Contents != null && slot.Contents.Count > 0)
                {
                    saved.contentIds = new List<string>();
                    saved.contentCounts = new List<int>();
                    saved.contentUsed = new List<float>();
                    saved.contentLiquid = new List<string>();
                    saved.contentStored = new List<float>();
                    foreach (ContainerStack c in slot.Contents) { saved.contentIds.Add(c.ItemId); saved.contentCounts.Add(c.Count); saved.contentUsed.Add(c.Used); saved.contentLiquid.Add(c.Liquid ?? ""); saved.contentStored.Add(c.Stored); }
                }
                s.toolbar.Add(saved);
            }
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
            s.netPlan = NetPlan.CurrentId;
            s.netPlanDaysLeft = NetPlan.DaysLeft;

            foreach (PlantedGrowth p in PlantedGrowth.All)
            {
                if (p == null || p.Group == null) continue;
                s.plants.Add(new GameSave.SavedPlant
                {
                    group = p.Group.QualifiedId, position = p.transform.position, yaw = p.transform.eulerAngles.y,
                    ageDays = p.AgeDays, state = (int)p.State, stumpRadius = p.StumpRadius, fruitPickedUntil = p.FruitPickedUntil, fruitGoneMask = (int)p.FruitGone,
                });
            }
            var placedIndex = new Dictionary<GameObject, int>();
            foreach (PlacedObject o in PlacedObject.All)
            {
                if (o == null) continue;
                placedIndex[o.gameObject] = s.placed.Count;   // the wiring refers to placed objects by their place in this list
                var sp = new GameSave.SavedPlaced { mirrored = o.Mirrored, lightOff = o.GetComponentInChildren<LightEmitter>(true) != null && o.GetComponentInChildren<LightEmitter>(true).SwitchedOff, itemId = o.ItemId, position = o.transform.position, yawDeg = o.YawDeg, level = o.Level, paintId = o.PaintId, liquidId = o.LiquidId, sawLog = o.SawLog, wireUsed = o.WireUsed, panelId = MountedPanel.PanelOn(o.gameObject), chargeWh = o.GetComponent<WireNode>() != null ? o.GetComponent<WireNode>().ChargeWh : 0f, waterL = o.GetComponent<WireNode>() != null ? o.GetComponent<WireNode>().WaterL : 0f, rawL = o.GetComponent<WireNode>() != null ? o.GetComponent<WireNode>().RawL : 0f, tempC = o.GetComponent<WireNode>() != null ? o.GetComponent<WireNode>().TempC : 12f };
                if (o.Contents != null && o.Contents.Count > 0)
                {
                    sp.contentIds = new List<string>();
                    sp.contentCounts = new List<int>();
                    sp.contentUsed = new List<float>();
                    sp.contentLiquid = new List<string>();
                    sp.contentStored = new List<float>();
                    foreach (ContainerStack c in o.Contents) { sp.contentIds.Add(c.ItemId); sp.contentCounts.Add(c.Count); sp.contentUsed.Add(c.Used); sp.contentLiquid.Add(c.Liquid ?? ""); sp.contentStored.Add(c.Stored); }
                }
                s.placed.Add(sp);
            }
            s.attached = AttachedObject.Capture();
            s.chimneys = PlacedChimney.CaptureAll();
            var attachedIndex = new Dictionary<GameObject, int>();
            List<AttachedObject> attachedOrder = AttachedObject.CaptureOrder();
            for (int ai = 0; ai < attachedOrder.Count; ai++) attachedIndex[attachedOrder[ai].gameObject] = ai;
            s.wires = WireNetwork.Capture(placedIndex, attachedIndex);
            s.trips = WireNetwork.CaptureTrips(placedIndex, attachedIndex);
            foreach (WorldItem w in WorldItem.All)
                if (w != null) s.drops.Add(new GameSave.SavedDrop { itemId = w.ItemId, position = w.transform.position, hasYaw = w.FixedYaw, yawDeg = w.Yaw });
            s.deliveries = Homesteader.World.DeliveryService.SavedOrders();
            s.trashLastDay = Homesteader.World.TrashService.LastDay;
            foreach (ConstructionSite cs in ConstructionSite.All)
                if (cs != null) s.sites.Add(new GameSave.SavedSite { structureId = cs.StructureId, position = cs.transform.position, yawDeg = cs.YawDeg, stage = cs.Stage, doorOpen = cs.DoorOpen, looks = new List<string>(cs.LookItems), fuelMinutes = cs.FuelMinutes, fireLit = cs.FireLit, wallPaints = cs.WallPaintList(), windowStates = cs.WindowStateList(), openDoors = cs.OpenDoorList(), contentIds = cs.Contents.ConvertAll(c => c.ItemId), contentCounts = cs.Contents.ConvertAll(c => c.Count), choices = cs.ChoiceList(), pumpId = cs.PumpId, fittedPanel = cs.FittedPanel, sewageL = cs.GetComponent<WireNode>() != null ? cs.GetComponent<WireNode>().SewageL : 0f, sludgeL = cs.GetComponent<WireNode>() != null ? cs.GetComponent<WireNode>().SludgeL : 0f });
            foreach (LotRun lr in LotRun.All)
                if (lr != null) s.lots.Add(new GameSave.SavedLot { style = lr.Style, itemId = lr.ItemId, points = new List<Vector3>(lr.Points) });
            foreach (PathRun pr in PathRun.All)
            {
                if (pr == null) continue;
                s.paths.Add(new GameSave.SavedPath { kind = pr.Kind, style = pr.Style, itemId = pr.ItemId, width = pr.Width, metresPerItem = pr.MetresPerItem,
                                                     built = pr.Built, points = new List<Vector3>(pr.Points) });
            }
            foreach (FenceRun f in FenceRun.All)
            {
                if (f == null) continue;
                var sf = new GameSave.SavedFence { style = f.Style, panelItem = f.PanelItemId, postItem = f.PostItemId, panelLength = f.PanelLength, height = f.Height,
                                                   closed = f.Closed, partial = f.Limit != int.MaxValue, builtPanels = f.Limit, posts = new List<Vector3>(f.Posts), gates = new List<GameSave.SavedGate>() };
                foreach (FenceRun.Gate g in f.Gates)
                    sf.gates.Add(new GameSave.SavedGate { segment = g.Segment, s = g.S, width = g.Width, itemId = g.ItemId, style = g.Style, open = g.Open });
                s.fences.Add(sf);
            }
            s.fellTrees = Homesteader.World.ForestTrees.SavedFelled();
            s.removedStumps = Homesteader.World.ForestTrees.SavedRemovedStumps();
            s.deadTrees = Homesteader.World.ForestTrees.SavedDead();
            s.pickedTrees = Homesteader.World.ForestTrees.SavedPicked();
            s.savedMeals = Homesteader.Kitchen.SavedMeals.Capture();
            s.pickedTreeMasks = Homesteader.World.ForestTrees.SavedPickedMasks();
            s.pickedBushes = Homesteader.World.BerryBushes.SavedPicked();
            s.pickedBushMasks = Homesteader.World.BerryBushes.SavedPickedMasks();
            s.dugBushes = Homesteader.World.BerryBushes.SavedDug();
            s.brokenRocks = Homesteader.World.WorldRocks.SavedBroken();
            s.tilledCells = Homesteader.World.FarmlandSoil.Saved();
            s.tilledAlongZ = Homesteader.World.FarmlandSoil.SavedAlongZ();
            s.mowedCells = Homesteader.World.LawnSoil.Saved();
            s.mowedAlongZ = Homesteader.World.LawnSoil.SavedAlongZ();
            s.plantedBushes = Homesteader.World.BerryBushes.SavedPlanted();
            s.forestGrowthDay = Homesteader.World.VegetationSeasons.GrowthDay;
            s.miniPlayerOpen = Homesteader.UI.SteadifyMiniPlayer.IsOpen;
            s.musicPlaying = Homesteader.Audio.AudioManager.Instance != null && Homesteader.Audio.AudioManager.Instance.IsMusicPlaying;
            s.windows = Homesteader.UI.WindowPositions.Capture();
            Homesteader.Radio.RadioPlayer.Saved radio = Homesteader.Radio.RadioPlayer.Capture();
            s.radioStation = radio.station; s.radioLine = radio.line; s.radioPaused = radio.paused;
            return s;
        }

        // ------------------------------------------------------------------ apply

        /// <summary>
        /// Stands the player on whatever is under the saved spot NOW: a house floor, a porch or the ground. The controller was held off during the load, so the player cannot have fallen
        /// through a floor that was not built yet. A ray from above finds the top surface (the ped's own colliders and triggers are skipped); the ground is the fallback.
        /// </summary>
        private IEnumerator PlacePedOnSurface(Vector3 saved)
        {
            var ped = PedController.Current;
            if (ped == null) yield break;
            var cc = ped.GetComponent<CharacterController>();
            yield return null;   // a frame for the last colliders to register
            Vector3 p = saved;
            float y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(p);
            RaycastHit[] hits = Physics.RaycastAll(new Vector3(p.x, Mathf.Max(saved.y, y) + 6f, p.z), Vector3.down, 40f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            float best = float.MinValue;
            foreach (RaycastHit h in hits)
            {
                if (h.collider.transform.IsChildOf(ped.transform)) continue;
                if (h.point.y > best && h.point.y <= Mathf.Max(saved.y, y) + 1.5f) best = h.point.y;   // the highest surface at or just above where the player was (not a roof)
            }
            if (best > y) y = best;
            p.y = y + 0.05f;
            if (cc != null) cc.enabled = false;
            ped.transform.position = p;
            if (cc != null) cc.enabled = true;
        }

        private IEnumerator ApplySave(GameSave s)
        {
            Step(0.02f, "Restoring the world...");
            // time
            TimeSystem t = TimeSystem.Instance;
            t.SetDayOfYear(s.dayOfYear);
            t.SetMinuteOfDay(s.minuteOfDay);
            if (s.weatherOverridden) t.SetWeather((HomesteaderWeather)s.weather, true);
            // saves made while the menu had paused the clock (earlier versions) come back running, not frozen
            t.SetSpeed((HomesteaderSpeed)s.speed == HomesteaderSpeed.Pause ? HomesteaderSpeed.Speed1X : (HomesteaderSpeed)s.speed);

            // HUD state
            HudState hud = HudState.Active;
            hud.Toolbar.Clear();
            for (int i = 0; i < HudState.ToolbarSize; i++)
            {
                if (i >= s.toolbar.Count) { hud.Toolbar.Add(ToolbarSlotData.Empty()); continue; }
                var slot = new ToolbarSlotData { IconId = s.toolbar[i].iconId, Count = s.toolbar[i].count, WireUsed = s.toolbar[i].wireUsed, LiquidId = s.toolbar[i].liquidId };
                if (s.toolbar[i].contentIds != null && s.toolbar[i].contentCounts != null)
                {
                    slot.Contents = new List<ContainerStack>();
                    for (int c = 0; c < s.toolbar[i].contentIds.Count && c < s.toolbar[i].contentCounts.Count; c++)
                        slot.Contents.Add(new ContainerStack { ItemId = s.toolbar[i].contentIds[c], Count = s.toolbar[i].contentCounts[c], Used = s.toolbar[i].contentUsed != null && c < s.toolbar[i].contentUsed.Count ? s.toolbar[i].contentUsed[c] : 0f, Liquid = s.toolbar[i].contentLiquid != null && c < s.toolbar[i].contentLiquid.Count ? s.toolbar[i].contentLiquid[c] : "", Stored = s.toolbar[i].contentStored != null && c < s.toolbar[i].contentStored.Count ? s.toolbar[i].contentStored[c] : 0f });
                }
                hud.Toolbar.Add(slot);
            }
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
            NetPlan.Restore(s.netPlan, s.netPlanDaysLeft);
            HudBindings.Instance.RefreshToolbar();

            // player + camera
            var ped = PedController.Current;
            if (ped != null)
            {
                var cc = ped.GetComponent<CharacterController>();
                if (cc != null) cc.enabled = false;             // a CharacterController ignores direct position changes
                Vector3 ppos = s.playerPosition;
                ppos.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(ppos);
                ped.transform.SetPositionAndRotation(ppos, Quaternion.Euler(0f, s.playerYaw, 0f));
                // the controller stays OFF until the buildings are up (PlacePedOnSurface): enabled now it would drop through the floor of a house that does not exist yet
            }
            var cam = IsometricLockedCamera.Current;
            if (cam != null)
            {
                cam.RestoreView(s.cameraYaw, s.cameraOrthoSize, s.cameraPanned, s.cameraFocal);
            }

            // chopped forest trees (the forest itself is regenerated from the seed)
            Homesteader.World.VegetationSeasons.RestoreGrowthDay(s.forestGrowthDay);
            Homesteader.World.ForestTrees.ApplyFelled(s.fellTrees);
            Homesteader.World.ForestTrees.ApplyRemovedStumps(s.removedStumps);
            Homesteader.World.ForestTrees.ApplyDead(s.deadTrees);
            Homesteader.World.ForestTrees.ApplyPicked(s.pickedTrees, s.pickedTreeMasks);
            Homesteader.Kitchen.SavedMeals.Apply(s.savedMeals);
            Homesteader.World.BerryBushes.ClearPlanted();
            Homesteader.World.BerryBushes.ApplyPlanted(s.plantedBushes);   // before the picked and dug spots are applied: they may be on these
            Homesteader.World.BerryBushes.ApplyPicked(s.pickedBushes, s.pickedBushMasks);
            Homesteader.World.BerryBushes.ApplyDug(s.dugBushes);
            Homesteader.World.WorldRocks.ApplyBroken(s.brokenRocks);
            Homesteader.World.FarmlandSoil.ApplySaved(s.tilledCells, s.tilledAlongZ);
            Homesteader.World.LawnSoil.ApplySaved(s.mowedCells, s.mowedAlongZ);
            Homesteader.UI.WindowPositions.Restore(s.windows);
            Homesteader.UI.SteadifyMiniPlayer.Restore(s.miniPlayerOpen);
            Homesteader.Radio.RadioPlayer.Restore(new Homesteader.Radio.RadioPlayer.Saved { station = s.radioStation, line = s.radioLine, paused = s.radioPaused });

            ClearPlayerMadeWorld();   // whatever is standing belongs to the world being left; the save puts back exactly its own

            // plants: the ones standing now belong to the world being left (or to a stale session); the save puts back exactly its own
            foreach (PlantedGrowth old in new List<PlantedGrowth>(PlantedGrowth.All))
            {
                if (old == null) continue;
                PlantedGrowth.All.Remove(old);   // now, so nothing below (or this frame) still sees it; OnDisable would only do it at the end of the frame
                Object.Destroy(old.gameObject);
            }
            var groups = new Dictionary<string, GrowthGroup>(System.StringComparer.OrdinalIgnoreCase);
            foreach (GrowthGroup g in GrowthRegistry.Groups) groups[g.QualifiedId] = g;
            Transform plantedRoot = (GameObject.Find("PlantedGrowth") ?? new GameObject("PlantedGrowth")).transform;
            foreach (var sp in s.plants)
            {
                if (!groups.TryGetValue(sp.group, out GrowthGroup group)) { Debug.LogWarning($"[Save] plant group '{sp.group}' no longer exists; skipped."); continue; }
                PlantedGrowth p = PlantedGrowth.Plant(group, sp.position, plantedRoot);
                p.transform.rotation = Quaternion.Euler(0f, sp.yaw, 0f);
                p.SetAgeDays(sp.ageDays);
                p.RestoreState((PlantedGrowth.PlantState)sp.state, sp.stumpRadius);
                if (sp.fruitPickedUntil > 0f) p.RestoreFruit(sp.fruitPickedUntil, sp.fruitGoneMask == 0 ? uint.MaxValue : (uint)sp.fruitGoneMask);
            }

            // placed structures / props: their models load lazily, so wait for each template
            Step(0.2f, "Placing objects...");
            int placedDone = 0;
            var restoredPlaced = new Dictionary<int, PlacedObject>();
            foreach (var so in s.placed)
            {
                int placedIdx = placedDone;
                Step(0.2f + 0.45f * (placedDone++ / (float)System.Math.Max(1, s.placed.Count)), "Placing objects...");
                if (!ItemRegistry.TryGet(so.itemId, out ItemRegistry.ItemInfo info)) { Debug.LogWarning($"[Save] placed item '{so.itemId}' is not loaded; skipped."); continue; }
                GlbTemplate glb = info.Prefab != null ? info.Prefab.GetComponent<GlbTemplate>() : null;
                if (glb != null)
                {
                    glb.EnsureLoading();
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!glb.Ready && !glb.Failed && Time.realtimeSinceStartup < until) yield return null;
                    if (!glb.Ready) continue;
                }
                List<ContainerStack> contents = null;
                if (so.contentIds != null && so.contentCounts != null)
                {
                    contents = new List<ContainerStack>();
                    for (int c = 0; c < so.contentIds.Count && c < so.contentCounts.Count; c++)
                        contents.Add(new ContainerStack { ItemId = so.contentIds[c], Count = so.contentCounts[c], Used = so.contentUsed != null && c < so.contentUsed.Count ? so.contentUsed[c] : 0f, Liquid = so.contentLiquid != null && c < so.contentLiquid.Count ? so.contentLiquid[c] : "", Stored = so.contentStored != null && c < so.contentStored.Count ? so.contentStored[c] : 0f });
                }
                PlacedObject restored = PlacementController.SpawnPlaced(so.itemId, info, so.position, so.yawDeg, false, so.level, contents, so.mirrored);
                if (restored != null && !string.IsNullOrEmpty(so.paintId)) restored.ApplyPaint(so.paintId);   // a painted door
                if (restored != null && !string.IsNullOrEmpty(so.sawLog)) restored.SawLog = so.sawLog;   // the log on a sawmill's track (Sawmill shows it once its model is there)
                if (restored != null && !string.IsNullOrEmpty(so.liquidId)) { restored.LiquidId = so.liquidId; TankSticker.Show(restored, so.liquidId); }   // what a tank holds
                if (restored != null) { restored.WireUsed = so.wireUsed; if (so.lightOff && restored.GetComponentInChildren<LightEmitter>(true) != null) restored.GetComponentInChildren<LightEmitter>(true).SwitchedOff = true; if (!string.IsNullOrEmpty(so.panelId)) MountedPanel.Fit(restored.gameObject, so.itemId, so.panelId); if (so.chargeWh > 0f && restored.GetComponent<WireNode>() != null) restored.GetComponent<WireNode>().ChargeWh = so.chargeWh; if (so.waterL > 0f && restored.GetComponent<WireNode>() != null) { WireNode tank = restored.GetComponent<WireNode>(); tank.WaterL = so.waterL; tank.RawL = so.rawL; tank.TempC = so.tempC > 0f ? so.tempC : 12f; } restoredPlaced[placedIdx] = restored; }
            }

            Homesteader.World.DeliveryService.RestoreOrders(s.deliveries);
            Homesteader.World.TrashService.Restore(s.trashLastDay);

            // structures under construction
            Step(0.65f, "Building structures...");
            ConstructionSite.Clear();
            foreach (var cs in s.sites)
            {
                ConstructionSite site = ConstructionSite.Create(cs.structureId, cs.position, cs.yawDeg, cs.stage);
                if (site != null) { site.SetDoor(cs.doorOpen); site.SetLooks(cs.looks); site.SetWallPaints(cs.wallPaints); site.SetWindowStates(cs.windowStates); site.SetOpenDoors(cs.openDoors); site.SetChoices(cs.choices); site.FuelMinutes = cs.fuelMinutes; site.FireLit = cs.fireLit; site.PumpId = cs.pumpId; if (!string.IsNullOrEmpty(cs.fittedPanel)) site.FitPanel(cs.fittedPanel); if ((cs.sewageL > 0f || cs.sludgeL > 0f) && site.GetComponent<WireNode>() != null) { site.GetComponent<WireNode>().SewageL = cs.sewageL; site.GetComponent<WireNode>().SludgeL = cs.sludgeL; } if (cs.contentIds != null) for (int ci = 0; ci < cs.contentIds.Count && ci < (cs.contentCounts?.Count ?? 0); ci++) site.Contents.Add(new Homesteader.UI.ContainerStack { ItemId = cs.contentIds[ci], Count = cs.contentCounts[ci] }); }   // before the model loads, or on it at once when it is already showing
            }

            // what is mounted on them (breaker boxes, lights): the sites exist now, in the order they were saved
            var restoredAttached = new Dictionary<int, AttachedObject>();
            int attachedCounter = 0;
            foreach (GameSave.SavedAttached sa in s.attached)
            {
                int attachedIdx = attachedCounter++;
                if (sa.siteIndex < 0 || sa.siteIndex >= ConstructionSite.All.Count || !ItemRegistry.TryGet(sa.itemId, out ItemRegistry.ItemInfo ai)) continue;
                ConstructionSite host = ConstructionSite.All[sa.siteIndex];
                if (host == null) continue;
                GlbTemplate aglb = ai.Prefab != null ? ai.Prefab.GetComponent<GlbTemplate>() : null;   // its model loads lazily: an instance made before that is empty
                if (aglb != null)
                {
                    aglb.EnsureLoading();
                    float aUntil = Time.realtimeSinceStartup + 20f;
                    while (!aglb.Ready && !aglb.Failed && Time.realtimeSinceStartup < aUntil) yield return null;
                    if (!aglb.Ready) continue;
                }
                if (host == null) continue;
                AttachedObject restoredA = AttachedObject.Spawn(sa.itemId, ai, host, host.transform.TransformPoint(sa.localPosition), host.transform.rotation * sa.localRotation, sa.thickness);
                if (restoredA != null && restoredA.Contents != null && sa.contentIds != null)   // what a mounted cabinet held
                    for (int c = 0; c < sa.contentIds.Count; c++)
                        restoredA.Contents.Add(new ContainerStack { ItemId = sa.contentIds[c], Count = sa.contentCounts[c], Used = sa.contentUsed != null && c < sa.contentUsed.Count ? sa.contentUsed[c] : 0f, Liquid = sa.contentLiquid != null && c < sa.contentLiquid.Count ? sa.contentLiquid[c] : "", Stored = sa.contentStored != null && c < sa.contentStored.Count ? sa.contentStored[c] : 0f });
                if (restoredA != null && restoredA.GetComponent<NetRack>() != null) restoredA.GetComponent<NetRack>().Restore(sa.shelfIds);   // what was in a rack
                if (restoredA != null && restoredA.GetComponent<Shelf>() != null) restoredA.GetComponent<Shelf>().Restore(sa.shelfIds, sa.shelfX, sa.shelfUsed, sa.shelfLiquids);   // what stood on a shelf
                if (restoredA != null) { restoredAttached[attachedIdx] = restoredA; if (sa.lightOff && restoredA.GetComponentInChildren<LightEmitter>(true) != null) restoredA.GetComponentInChildren<LightEmitter>(true).SwitchedOff = true; if (!string.IsNullOrEmpty(sa.panelId)) MountedPanel.Fit(restoredA.gameObject, sa.itemId, sa.panelId); if (sa.chargeWh > 0f && restoredA.GetComponent<WireNode>() != null) restoredA.GetComponent<WireNode>().ChargeWh = sa.chargeWh; if (sa.switchOff && restoredA.GetComponent<WireNode>() != null) { restoredA.GetComponent<WireNode>().SwitchOff = true; Disconnect.Show(restoredA.GetComponent<WireNode>()); } }
            }
            PlacedChimney.RestoreAll(s.chimneys);   // the chimneys on the buildings (their sites exist now)
            WireNetwork.Restore(s.wires, restoredPlaced, restoredAttached);   // the wires between them
            WireNetwork.RestoreTrips(s.trips, restoredPlaced, restoredAttached);   // the parts that had tripped

            // paths and roads
            Step(0.72f, "Laying paths and fences...");
            foreach (GameSave.SavedPath sp in s.paths)
                if (sp.points != null && sp.points.Count >= 2) PathRun.Create(sp.kind, sp.style, sp.itemId, sp.width, sp.metresPerItem, sp.points, sp.built).ClearGround();

            // lots
            foreach (GameSave.SavedLot sl in s.lots)
                if (sl.points != null && sl.points.Count >= 3)
                {
                    LotRun.Create(sl.style, sl.itemId, sl.points);
                    Homesteader.World.SiteClearing.ClearPolygon(sl.points);   // the world's grass, flowers and clutter grow back on a loaded game: clear them under the lot again
                }

            // fences
            foreach (GameSave.SavedFence sf in s.fences)
            {
                var gates = new List<FenceRun.Gate>();
                if (sf.gates != null)
                    foreach (GameSave.SavedGate g in sf.gates)
                        gates.Add(new FenceRun.Gate { Segment = g.segment, S = g.s, Width = g.width, ItemId = g.itemId, Style = g.style, Open = g.open });
                if (sf.posts != null && sf.posts.Count >= 2)
                {
                    FenceRun fr = FenceRun.Create(sf.style, sf.panelItem, sf.postItem, sf.panelLength, sf.height, sf.posts, sf.closed, gates);
                    if (sf.partial) { fr.Limit = sf.builtPanels; fr.Rebuild(); }
                }
            }

            // dropped items
            Step(0.8f, "Dropping items...");
            foreach (var d in s.drops) WorldItem.TryDrop(d.itemId, d.position, d.hasYaw ? d.yawDeg : (float?)null);
        }
    }
}
