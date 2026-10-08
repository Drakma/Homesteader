using System.Collections.Generic;
using System.Text;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// The Meals List: a right click on any kitchen object opens it, and it lists ONLY the meals the kitchen can make right now (the appliances they need
    /// stand in the kitchen and the ingredients are stocked in its containers and shelves). "Make" takes the ingredients out and puts the result in the toolbar.
    /// The kitchen is the same room, or within <see cref="KitchenScan.Radius"/> m of the object that was clicked. docs/COOKING.md.
    /// </summary>
    public sealed class MealsPanel
    {
        private static MealsPanel _open;
        public static bool IsOpen => _open != null;

        /// <summary>Esc: closes the list if it is open. True when there was one.</summary>
        public static bool CloseOpen()
        {
            if (_open == null) return false;
            _open.Close();
            return true;
        }

        /// <summary>True for the one thing a right click opens the list from: a placed cutting board (the Meals List and its Meal Builder). Shift + right click picks it up.</summary>
        public static bool IsKitchenObject(string itemId)
        {
            return !string.IsNullOrEmpty(itemId) && itemId.StartsWith("kitchen_cutting_board");
        }

        /// <summary>Opens the list for the kitchen around <paramref name="center"/> (the clicked object), after the reach check.</summary>
        public static void Open(Vector3 center, string clickedItemId)
        {
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, center, GameRules.Placement.ReachCells))
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the kitchen.");
                return;
            }
            VisualElement root = HudBindings.Instance != null ? HudBindings.Instance.Root : null;
            if (root == null) return;
            if (_open != null) _open.Close();
            _open = new MealsPanel(root, center, clickedItemId);
        }

        private readonly Vector3 _center;
        private readonly VisualElement _window;
        private readonly Label _title;
        private readonly VisualElement _list;
        private IVisualElementScheduledItem _tick;
        private string _signature = "";
        private KitchenScan _scan;
        private readonly List<MealDef> _meals = new List<MealDef>();

        private MealsPanel(VisualElement panelRoot, Vector3 center, string clickedItemId)
        {
            _center = center;
            _window = new VisualElement { name = "MealsPanel" };
            _window.AddToClassList("window");
            _window.AddToClassList("container-panel");
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            _window.Add(edge);
            _window.style.position = Position.Absolute;

            var header = new VisualElement();
            header.AddToClassList("window-header");
            header.tooltip = "Drag to move";
            _title = new Label("Meals List");
            _title.AddToClassList("window-title");
            _title.pickingMode = PickingMode.Ignore;
            var close = new Button(Close) { text = "X", tooltip = "Close (Esc)" };
            close.AddToClassList("hs-close");
            var builder = new Button(() => MealBuilderPanel.Open(_center)) { text = "Meal Builder", tooltip = "Put up to four foods on a plate and pour a drink; save the meal to make it again" };
            builder.AddToClassList("hs-btn");
            header.Add(_title);
            header.Add(builder);
            header.Add(close);
            _window.Add(header);
            WindowPositions.MakeDraggable(_window, header, "meals");

            var body = new VisualElement();
            body.AddToClassList("window-body");
            _window.Add(body);
            var sub = new Label("What this kitchen can make with what is stocked in it");
            sub.AddToClassList("container-panel-hint");
            body.Add(sub);
            _list = new VisualElement();
            body.Add(_list);

            VisualElement wallpaper = panelRoot.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == panelRoot) panelRoot.Insert(panelRoot.IndexOf(wallpaper), _window);
            else panelRoot.Add(_window);
            WindowPositions.Place(_window, "meals");

            _tick = _window.schedule.Execute(Refresh).Every(250);
            Refresh();
        }

        public void Close()
        {
            _tick?.Pause();
            WindowPositions.Remember(_window, "meals");
            _window.RemoveFromHierarchy();
            if (_open == this) _open = null;
        }

        private void Refresh()
        {
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, _center, GameRules.Placement.ReachCells + 2)) { Close(); return; }

            _scan = KitchenScan.At(_center);
            _meals.Clear();
            _meals.AddRange(MealMaker.Makeable(_scan));

            var sig = new StringBuilder();
            foreach (MealDef m in _meals) sig.Append(m.Id).Append(',');
            sig.Append('#').Append(_scan.Appliances.Count);
            foreach (KeyValuePair<string, int> kv in _scan.Stock) sig.Append(kv.Key).Append('x').Append(kv.Value).Append(';');
            if (sig.ToString() == _signature) return;
            _signature = sig.ToString();

            _list.Clear();
            if (_meals.Count == 0)
            {
                _list.Add(Hint("Nothing can be made with what this kitchen has."));
                _list.Add(Hint("Stock the cabinets, pantry, fridge and shelves with ingredients, and stand the appliance a meal needs (oven, grill, stove, grain mill) in the kitchen."));
                return;
            }
            string group = null;
            foreach (MealDef meal in _meals)
            {
                if (meal.Group != group)
                {
                    group = meal.Group;
                    var h = new Label(group.ToUpperInvariant());
                    h.AddToClassList("window-section-title");
                    _list.Add(h);
                }
                _list.Add(Row(meal));
            }
        }

        private VisualElement Row(MealDef meal)
        {
            var row = new VisualElement();
            row.AddToClassList("container-panel-row");
            var icon = new VisualElement();
            icon.AddToClassList("container-panel-icon");
            var tex = PhoneController.GetItemIcon(meal.ResultId + ".png", meal.ResultId);
            if (tex != null) icon.style.backgroundImage = new StyleBackground(tex);
            row.Add(icon);
            var name = new Label(MealMaker.NameOf(meal) + (meal.ResultQty > 1 ? "  x" + meal.ResultQty : ""));
            name.AddToClassList("container-panel-row-name");
            name.tooltip = Uses(meal);
            row.Add(name);
            MealDef m = meal;
            var b = new Button(() => Make(m)) { text = "Make", tooltip = Uses(meal) };
            b.AddToClassList("container-panel-btn");
            row.Add(b);
            return row;
        }

        private void Make(MealDef meal)
        {
            if (KitchenCook.Busy) return;
            _scan = KitchenScan.At(_center);   // the stock may have changed since the list was drawn
            if (MealMaker.Plan(meal, _scan) == null) { ToastNotificationSystem.ShowInfo(MealMaker.NameOf(meal), "The kitchen no longer has what it takes."); return; }
            var step = new PlanStep { Meal = meal, Batches = 1 };
            _scan.FindAppliance(meal.Appliances, out step.Appliance, out step.ApplianceId);
            // the ped walks to the appliance and works at it, then the meal is made (what it takes leaves the kitchen only then)
            KitchenCook.Begin(new List<PlanStep> { step }, _center,
                () =>
                {
                    if (!MealMaker.Make(meal, KitchenScan.At(_center), out string why)) ToastNotificationSystem.ShowInfo(MealMaker.NameOf(meal), why);
                    _signature = "";
                },
                msg => { ToastNotificationSystem.ShowInfo(MealMaker.NameOf(meal), msg); _signature = ""; });
            _signature = "";
            Refresh();
        }

        /// <summary>"Uses: Flour, Yeast, Salt" (the ingredients the meal would take now).</summary>
        private string Uses(MealDef meal)
        {
            Dictionary<string, int> plan = MealMaker.Plan(meal, _scan);
            if (plan == null) return "";
            var parts = new List<string>();
            foreach (KeyValuePair<string, int> kv in plan) parts.Add(HudBindings.GetItemName(kv.Key) + (kv.Value > 1 ? " x" + kv.Value : ""));
            if (meal.ResultContainer != null) parts.Add("an empty " + HudBindings.GetItemName(meal.ResultContainer));
            return "Uses: " + string.Join(", ", parts);
        }

        private static Label Hint(string text)
        {
            var l = new Label(text);
            l.AddToClassList("container-panel-hint");
            return l;
        }
    }
}
