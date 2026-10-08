using System;
using System.Collections.Generic;

namespace Homesteader.Kitchen
{
    /// <summary>A meal the player built at the Meal Builder and kept: up to four foods on a plate, a bowl of soup / stew / salad and a drink. Made again with one click while the kitchen has the foods (docs/COOKING.md).</summary>
    [Serializable]
    public sealed class SavedMeal
    {
        public string Name;
        public List<string> Foods = new List<string>();   // food item ids, in plate order (an id twice = two of it)
        public string Drink = "";                         // a liquid id ("" = no drink)
        public string Bowl = "";                          // a soup, stew or salad food id ("" = no bowl)
    }

    /// <summary>The saved meals of this game. They go in the save file (GameSave.savedMeals).</summary>
    public static class SavedMeals
    {
        public static readonly List<SavedMeal> All = new List<SavedMeal>();

        public static void Clear() { All.Clear(); }

        /// <summary>Keeps a meal under a name; a meal already saved under that name is replaced.</summary>
        public static SavedMeal Save(string name, List<string> foods, string drink, string bowl = "")
        {
            name = string.IsNullOrWhiteSpace(name) ? "Meal " + (All.Count + 1) : name.Trim();
            All.RemoveAll(m => string.Equals(m.Name, name, StringComparison.OrdinalIgnoreCase));
            var meal = new SavedMeal { Name = name, Foods = new List<string>(foods), Drink = drink ?? "", Bowl = bowl ?? "" };
            All.Add(meal);
            return meal;
        }

        public static void Remove(SavedMeal meal) { All.Remove(meal); }

        public static List<Homesteader.Save.GameSave.SavedMealData> Capture()
        {
            var list = new List<Homesteader.Save.GameSave.SavedMealData>();
            foreach (SavedMeal m in All) list.Add(new Homesteader.Save.GameSave.SavedMealData { name = m.Name, foods = new List<string>(m.Foods), drink = m.Drink ?? "", bowl = m.Bowl ?? "" });
            return list;
        }

        public static void Apply(List<Homesteader.Save.GameSave.SavedMealData> saved)
        {
            All.Clear();
            if (saved == null) return;
            foreach (Homesteader.Save.GameSave.SavedMealData d in saved)
                All.Add(new SavedMeal { Name = d.name, Foods = d.foods != null ? new List<string>(d.foods) : new List<string>(), Drink = d.drink ?? "", Bowl = d.bowl ?? "" });
        }
    }
}
