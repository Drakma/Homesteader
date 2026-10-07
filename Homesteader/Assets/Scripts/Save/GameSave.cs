using System;
using System.Collections.Generic;
using System.IO;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Save
{
    /// <summary>
    /// The saved state of the game. Plain serializable data (JsonUtility): no references into the scene, so a save is
    /// a small readable JSON file in the Saves folder (see SaveSlots). GameSaveManager captures and applies it.
    /// </summary>
    [Serializable]
    public sealed class GameSave
    {
        public const int CurrentVersion = 1;
        public int version = CurrentVersion;
        public string savedAtUtc;
        public string gameName;                  // what the game is called (its saves are Name.json and Name-autosave.N.json)
        public int worldSeed;

        // time
        public int dayOfYear;
        public float minuteOfDay;
        public int speed;
        public bool weatherOverridden;
        public int weather;

        // player
        public Vector3 playerPosition;
        public float playerYaw;
        public float cameraYaw;                  // the yaw the camera is turning to (a half-turned view is saved as where it ends up)
        public bool cameraPanned;                // the view was panned off the player (right-drag)
        public Vector3 cameraFocal;              // where the panned view was looking
        public float cameraOrthoSize;

        // HUD state
        public List<SavedSlot> toolbar = new List<SavedSlot>();
        public int selectedSlot;
        public List<SavedVital> vitals = new List<SavedVital>();
        public List<SavedResource> resources = new List<SavedResource>();
        public float loanDebt;
        public string netPlan;                   // the internet subscription (NetPlan.cs): the plan held ("" = none)
        public int netPlanDaysLeft;              // and the days of its paid month still to run

        // world
        public List<SavedPlant> plants = new List<SavedPlant>();
        public List<SavedPlaced> placed = new List<SavedPlaced>();
        public List<SavedDrop> drops = new List<SavedDrop>();
        public List<Homesteader.World.DeliveryService.Order> deliveries = new List<Homesteader.World.DeliveryService.Order>();   // phone orders waiting for the delivery van
        public List<SavedLot> lots = new List<SavedLot>();          // lots the player laid (LotRun)
        public List<SavedPath> paths = new List<SavedPath>();      // paths and roads the player laid (PathRun)
        public List<SavedFence> fences = new List<SavedFence>();   // fences the player built (FenceRun)
        public List<SavedWire> wires = new List<SavedWire>();   // the wiring between devices (see Wiring.cs)
        public List<SavedAttached> attached = new List<SavedAttached>();   // breaker boxes and lights mounted on buildings (AttachedObject)
        public List<SavedSite> sites = new List<SavedSite>();   // structures under construction (and finished ones): see ConstructionSite
        public float forestGrowthDay;   // the furthest game day trees have grown to (never decreases)
        public List<Vector3> pickedBushes = new List<Vector3>();   // x, z, game day the berries are back, of berry bushes that were picked
        public List<int> pickedBushMasks = new List<int>();        // per pickedBushes entry: which berries are gone (bit mask)
        public List<int> pickedTreeMasks = new List<int>();   // per pickedTrees entry: which fruit is gone (bit mask; fruit is picked one at a time)
        public List<Vector3> pickedTrees = new List<Vector3>();   // x, z, game day the fruit is back, of procedural fruit trees that were picked
        public List<Vector2> removedStumps = new List<Vector2>();   // x, z of the forest stumps a chainsaw took out (the tree stays felled)
        public List<Vector2> fellTrees = new List<Vector2>();   // x, z of every procedural forest tree the player has chopped down
        public List<Homesteader.World.PlantedBushData> plantedBushes = new List<Homesteader.World.PlantedBushData>();   // berry bushes planted by the player
        public List<Vector2Int> tilledAlongZ = new List<Vector2Int>();   // the tilled squares whose rows run along Z (the others run along X)
        public List<Vector2Int> tilledCells = new List<Vector2Int>();   // grid squares of ground tilled into farmland with a hoe
        public List<Vector2> brokenRocks = new List<Vector2>();   // x, z of scattered rocks broken with a pickaxe
        public List<Vector2> dugBushes = new List<Vector2>();   // berry bushes dug up with a shovel (x, z)
        public bool musicPlaying = true;   // Steadify music was playing (older saves: yes)
        public bool miniPlayerOpen;     // the Steadify pop-out player: whether it is showing, and where on the screen
        public float miniPlayerX = 40f, miniPlayerY = 90f;   // legacy: positions now live in `windows`
        public List<SavedWindow> windows = new List<SavedWindow>();   // where each movable window was left
        public List<Vector2> deadTrees = new List<Vector2>();   // x, z of trees killed by lightning
        public string radioStation = "";   // Steadify radio: the station tuned in ("" = off), the line reached and whether it was paused
        public int radioLine;
        public bool radioPaused;

        [Serializable] public struct SavedWindow { public string id; public float x, y; }
        [Serializable] public struct SavedSlot { public string iconId; public int count; public float wireUsed; public List<string> contentIds; public List<int> contentCounts; public List<string> choices; public string liquidId; }
        [Serializable] public struct SavedVital { public int id; public int value; }
        [Serializable]
        public struct SavedResource
        {
            public int id;
            public float amount;
            public List<string> subKeys;
            public List<float> subValues;
        }
        [Serializable]
        public struct SavedPlant
        {
            public string group;        // qualified group id
            public Vector3 position;
            public float yaw;
            public float ageDays;
            public int state;           // PlantedGrowth.PlantState
            public float stumpRadius;   // a stump keeps the trunk radius of the tree felled
            public int fruitGoneMask;       // which fruit of a planted fruit tree is picked (bit mask; 0 with fruitPickedUntil > 0 = an older save: all picked)
            public float fruitPickedUntil;   // game day a picked fruit tree's fruit is back (0 = not picked)
        }
        [Serializable] public struct SavedPlaced { public string itemId; public Vector3 position; public float yawDeg; public int level; public float wireUsed; public string panelId; public float chargeWh; public float waterL; public float rawL; public float tempC; public List<string> contentIds; public List<int> contentCounts; public string paintId; public string liquidId; public string sawLog; public bool lightOff; }
        [Serializable] public struct SavedWire { public int aKind, aIndex, bKind, bIndex; public string kind, wireItem; public float length; }   // kind 0 = an entry of placed[], 1 = an entry of attached[], 2 = a work site (a wind turbine)
        [Serializable] public struct SavedAttached { public string itemId; public int siteIndex; public Vector3 localPosition; public Quaternion localRotation; public float thickness; public string panelId; public float chargeWh; public bool switchOff; public bool lightOff; public List<string> shelfIds; public List<float> shelfX; public List<float> shelfUsed; public List<string> shelfLiquids; }   // shelf*: what stands on a wall shelf (Shelf.cs), parallel lists; in the building's own space; siteIndex = its place in the saved sites
        [Serializable] public struct SavedSite { public string structureId; public Vector3 position; public float yawDeg; public int stage; public bool doorOpen; public List<string> looks; public float fuelMinutes; public bool fireLit; public List<string> wallPaints; public List<string> openDoors; public List<string> contentIds; public List<int> contentCounts; public List<string> choices; public string pumpId; public string fittedPanel; public float sewageL; public float sludgeL; }   // sewageL / sludgeL: a septic tank's liquid and solids, a leach field's liquid (docs/SEPTIC.md)
        [Serializable] public struct SavedGate { public int segment; public float s; public float width; public string itemId; public string style; public bool open; }
        [Serializable] public struct SavedLot { public string style, itemId; public List<Vector3> points; }
        [Serializable] public struct SavedPath { public string kind, style, itemId; public float width, metresPerItem, built; public List<Vector3> points; }
        [Serializable] public struct SavedFence
        {
            public string style, panelItem, postItem;
            public float panelLength, height;
            public bool closed;
            public bool partial;          // saved while the ped was still building it
            public int builtPanels;
            public List<Vector3> posts;
            public List<SavedGate> gates;
        }
        [Serializable] public struct SavedDrop { public string itemId; public Vector3 position; public bool hasYaw; public float yawDeg; }

        // ------------------------------------------------------------------ file

        public static string SaveDir => SaveSlots.Dir;

        /// <summary>True when there is at least one save in the Saves folder.</summary>
        public static bool Exists => SaveSlots.Any;

        /// <summary>Writes the save to a file (through a temporary file, so a crash never leaves half a save).</summary>
        public void WriteTo(string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            savedAtUtc = DateTime.UtcNow.ToString("o");
            string tmp = path + ".tmp";
            File.WriteAllText(tmp, JsonUtility.ToJson(this, true));
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmp, path);
        }

        /// <summary>Reads a save file. Null when it is missing or unreadable.</summary>
        public static GameSave ReadFrom(string path)
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return null;
            try
            {
                var s = JsonUtility.FromJson<GameSave>(File.ReadAllText(path));
                if (s != null && s.version <= CurrentVersion) return s;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Save] could not read {path}: {e.Message}");
            }
            return null;
        }
    }
}
