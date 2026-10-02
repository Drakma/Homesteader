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
    /// a small readable JSON file at <see cref="SavePath"/>. GameSaveManager captures and applies it.
    /// </summary>
    [Serializable]
    public sealed class GameSave
    {
        public const int CurrentVersion = 1;
        public int version = CurrentVersion;
        public string savedAtUtc;
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
        public float cameraYaw;
        public float cameraOrthoSize;

        // HUD state
        public List<SavedSlot> toolbar = new List<SavedSlot>();
        public int selectedSlot;
        public List<SavedVital> vitals = new List<SavedVital>();
        public List<SavedResource> resources = new List<SavedResource>();
        public float loanDebt;

        // world
        public List<SavedPlant> plants = new List<SavedPlant>();
        public List<SavedPlaced> placed = new List<SavedPlaced>();
        public List<SavedDrop> drops = new List<SavedDrop>();
        public List<Homesteader.World.DeliveryService.Order> deliveries = new List<Homesteader.World.DeliveryService.Order>();   // phone orders waiting for the delivery van
        public List<SavedSite> sites = new List<SavedSite>();   // structures under construction (and finished ones): see ConstructionSite
        public float forestGrowthDay;   // the furthest game day trees have grown to (never decreases)
        public List<Vector3> pickedBushes = new List<Vector3>();   // x, z, game day the berries are back, of berry bushes that were picked
        public List<int> pickedBushMasks = new List<int>();        // per pickedBushes entry: which berries are gone (bit mask)
        public List<int> pickedTreeMasks = new List<int>();   // per pickedTrees entry: which fruit is gone (bit mask; fruit is picked one at a time)
        public List<Vector3> pickedTrees = new List<Vector3>();   // x, z, game day the fruit is back, of procedural fruit trees that were picked
        public List<Vector2> fellTrees = new List<Vector2>();   // x, z of every procedural forest tree the player has chopped down
        public bool miniPlayerOpen;     // the Steadify pop-out player: whether it is showing, and where on the screen
        public float miniPlayerX = 40f, miniPlayerY = 90f;   // legacy: positions now live in `windows`
        public List<SavedWindow> windows = new List<SavedWindow>();   // where each movable window was left
        public List<Vector2> deadTrees = new List<Vector2>();   // x, z of trees killed by lightning

        [Serializable] public struct SavedWindow { public string id; public float x, y; }
        [Serializable] public struct SavedSlot { public string iconId; public int count; public List<string> contentIds; public List<int> contentCounts; }
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
        [Serializable] public struct SavedPlaced { public string itemId; public Vector3 position; public float yawDeg; public int level; public List<string> contentIds; public List<int> contentCounts; }
        [Serializable] public struct SavedSite { public string structureId; public Vector3 position; public float yawDeg; public int stage; public bool doorOpen; public List<string> looks; }
        [Serializable] public struct SavedDrop { public string itemId; public Vector3 position; public bool hasYaw; public float yawDeg; }

        // ------------------------------------------------------------------ file

        public static string SaveDir => Path.Combine(Application.persistentDataPath, "Saves");
        public static string SavePath => Path.Combine(SaveDir, "autosave.json");
        public static string BackupPath => Path.Combine(SaveDir, "autosave.bak.json");

        public static bool Exists => File.Exists(SavePath);

        public void WriteToDisk()
        {
            Directory.CreateDirectory(SaveDir);
            savedAtUtc = DateTime.UtcNow.ToString("o");
            string tmp = SavePath + ".tmp";
            File.WriteAllText(tmp, JsonUtility.ToJson(this, true));
            if (File.Exists(SavePath)) File.Copy(SavePath, BackupPath, true);   // the previous good save
            if (File.Exists(SavePath)) File.Delete(SavePath);
            File.Move(tmp, SavePath);
        }

        /// <summary>Reads the save, falling back to the backup if the main file is unreadable. Null when there is none.</summary>
        public static GameSave ReadFromDisk()
        {
            foreach (string path in new[] { SavePath, BackupPath })
            {
                if (!File.Exists(path)) continue;
                try
                {
                    var s = JsonUtility.FromJson<GameSave>(File.ReadAllText(path));
                    if (s != null && s.version <= CurrentVersion) return s;
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[Save] could not read {path}: {e.Message}");
                }
            }
            return null;
        }

        public static void Delete()
        {
            foreach (string path in new[] { SavePath, BackupPath })
                if (File.Exists(path)) File.Delete(path);
        }
    }
}
