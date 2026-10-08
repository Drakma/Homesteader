using System.Collections.Generic;
using System.Text;
using Homesteader.Growth;
using Homesteader.UI;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.Kitchen
{
    /// <summary>
    /// The Meal Builder (the Meals List's "Meal Builder" button): a plate with room for four foods, a bowl for one soup, stew or salad and a glass for one drink. Click a food in the kitchen to put it on the plate (its icon sits on the
    /// plate), click a drink to fill the glass, click a food on the plate or the glass to take it off again. Make serves it (a Plated Meal, a Bowl of Food and a filled Drinking Glass go on the counter);
    /// Save keeps it under a name, and a saved meal is made again with one click while the kitchen has what it needs. docs/COOKING.md.
    /// </summary>
    public sealed class MealBuilderPanel
    {
        private static MealBuilderPanel _open;
        public static bool IsOpen => _open != null;

        public static bool CloseOpen()
        {
            if (_open == null) return false;
            _open.Close();
            return true;
        }

        /// <summary>Opens the builder for the kitchen around <paramref name="center"/>.</summary>
        public static void Open(Vector3 center)
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
            MealBuilder.Warm();   // the plate, bowl and glass models load now, ready for Make
            _open = new MealBuilderPanel(root, center);
        }

        private readonly Vector3 _center;
        private readonly VisualElement _window;
        private readonly VisualElement _plate;
        private readonly VisualElement _bowlSlot, _drinkSlot;
        private readonly VisualElement _foodsList, _bowlsList, _drinksList, _savedList;
        private readonly Label _status;
        private readonly Button _makeButton;
        private readonly TextField _name;
        private IVisualElementScheduledItem _tick;
        private string _signature = "";
        private KitchenScan _scan;
        private readonly List<string> _foods = new List<string>();   // on the plate
        private string _drink = "";                                  // in the glass
        private string _bowl = "";                                   // in the bowl: a soup, stew or salad

        private MealBuilderPanel(VisualElement panelRoot, Vector3 center)
        {
            _center = center;
            _window = new VisualElement { name = "MealBuilderPanel" };
            _window.AddToClassList("window");
            _window.AddToClassList("container-panel");
            _window.style.minWidth = 520;   // wide enough for the plate's four round places, the bowl and the glass in one row
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            _window.Add(edge);
            _window.style.position = Position.Absolute;

            var header = new VisualElement();
            header.AddToClassList("window-header");
            header.tooltip = "Drag to move";
            var title = new Label("Meal Builder");
            title.AddToClassList("window-title");
            title.pickingMode = PickingMode.Ignore;
            var close = new Button(Close) { text = "X", tooltip = "Close (Esc)" };
            close.AddToClassList("hs-close");
            header.Add(title);
            header.Add(close);
            _window.Add(header);
            WindowPositions.MakeDraggable(_window, header, "mealbuilder");

            var body = new VisualElement();
            body.AddToClassList("window-body");
            _window.Add(body);

            var h0 = new Label("YOUR PLATE");
            h0.AddToClassList("window-section-title");
            body.Add(h0);
            var table = new VisualElement();
            table.style.flexDirection = FlexDirection.Row;
            table.style.alignItems = Align.Center;
            body.Add(table);
            // the plate: a white dish with a blue rim and four places for the foods' icons
            _plate = new VisualElement();
            _plate.style.flexDirection = FlexDirection.Row;
            _plate.style.flexShrink = 0;   // never squeeze the four round places into ovals
            _plate.style.alignItems = Align.Center;
            _plate.style.paddingLeft = _plate.style.paddingRight = 14;
            _plate.style.paddingTop = _plate.style.paddingBottom = 10;
            _plate.style.backgroundColor = new Color(0.95f, 0.95f, 0.92f);
            _plate.style.borderTopLeftRadius = _plate.style.borderTopRightRadius = _plate.style.borderBottomLeftRadius = _plate.style.borderBottomRightRadius = 48;
            _plate.style.borderTopWidth = _plate.style.borderBottomWidth = _plate.style.borderLeftWidth = _plate.style.borderRightWidth = 4;
            _plate.style.borderTopColor = _plate.style.borderBottomColor = _plate.style.borderLeftColor = _plate.style.borderRightColor = new Color(0.18f, 0.35f, 0.72f);
            table.Add(_plate);
            _bowlSlot = new VisualElement();
            _bowlSlot.style.marginLeft = 14;
            _bowlSlot.style.flexShrink = 0;
            table.Add(_bowlSlot);
            _drinkSlot = new VisualElement();
            _drinkSlot.style.marginLeft = 14;
            _drinkSlot.style.flexShrink = 0;
            table.Add(_drinkSlot);

            var nameRow = new VisualElement();
            nameRow.style.flexDirection = FlexDirection.Row;
            nameRow.style.alignItems = Align.Center;
            nameRow.style.marginTop = 10;
            body.Add(nameRow);
            _name = new TextField { value = "", tooltip = "Name the meal to save it" };
            _name.style.flexGrow = 1;
            _name.style.height = 28;
            VisualElement input = _name.Q(className: "unity-base-text-field__input");
            if (input != null)
            {
                input.style.justifyContent = Justify.Center;
                input.style.unityTextAlign = TextAnchor.MiddleLeft;
                input.style.paddingTop = input.style.paddingBottom = 0;
            }
            nameRow.Add(_name);
            _makeButton = MakeButton("Make", "Make this meal: foods the kitchen does not have are cooked first (the ped walks from appliance to appliance), then it is served on the counter: a Plated Meal, a Bowl of Food and a glass", MakeNow, true);
            nameRow.Add(_makeButton);
            nameRow.Add(MakeButton("Save", "Keep this meal under the name, to make it again with one click", SaveNow, false));
            nameRow.Add(MakeButton("Clear", "Take everything off the plate", () => { _foods.Clear(); _drink = ""; _bowl = ""; _signature = ""; Refresh(); }, false));
            _status = new Label("");
            _status.AddToClassList("container-panel-hint");
            body.Add(_status);

            var h1 = new Label("FOODS IN THE KITCHEN");
            h1.AddToClassList("window-section-title");
            body.Add(h1);
            _foodsList = new VisualElement();
            body.Add(_foodsList);
            var hb = new Label("SOUPS, STEWS AND SALADS");
            hb.AddToClassList("window-section-title");
            body.Add(hb);
            _bowlsList = new VisualElement();
            body.Add(_bowlsList);
            var h2 = new Label("DRINKS");
            h2.AddToClassList("window-section-title");
            body.Add(h2);
            _drinksList = new VisualElement();
            body.Add(_drinksList);
            var h3 = new Label("SAVED MEALS");
            h3.AddToClassList("window-section-title");
            body.Add(h3);
            _savedList = new VisualElement();
            body.Add(_savedList);

            VisualElement wallpaper = panelRoot.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == panelRoot) panelRoot.Insert(panelRoot.IndexOf(wallpaper), _window);
            else panelRoot.Add(_window);
            WindowPositions.Place(_window, "mealbuilder");

            _tick = _window.schedule.Execute(Refresh).Every(250);
            Refresh();
        }

        public void Close()
        {
            _tick?.Pause();
            WindowPositions.Remember(_window, "mealbuilder");
            _window.RemoveFromHierarchy();
            if (_open == this) _open = null;
        }

        private static Button MakeButton(string text, string tip, System.Action onClick, bool primary)
        {
            var b = new Button(onClick) { text = text, tooltip = tip };
            b.AddToClassList("hs-btn");
            if (primary) b.AddToClassList("hs-btn--primary");
            b.style.marginLeft = 6;
            return b;
        }

        private static void SetIcon(VisualElement e, string itemId)
        {
            var tex = PhoneController.GetItemIcon(itemId + ".png", itemId);
            e.style.backgroundImage = tex != null ? new StyleBackground(tex) : new StyleBackground();
        }

        private static VisualElement Slot(string itemId, string tip, System.Action onClick, bool round)
        {
            var b = new Button(onClick) { tooltip = tip };
            b.style.width = b.style.height = 56;
            b.style.flexShrink = 0;
            b.style.minWidth = b.style.minHeight = 56;
            b.style.marginLeft = b.style.marginRight = 3;
            b.style.paddingLeft = b.style.paddingRight = b.style.paddingTop = b.style.paddingBottom = 0;
            b.style.backgroundColor = new Color(0.86f, 0.86f, 0.82f);
            b.style.borderTopLeftRadius = b.style.borderTopRightRadius = b.style.borderBottomLeftRadius = b.style.borderBottomRightRadius = round ? 28 : 8;
            b.style.unityBackgroundScaleMode = ScaleMode.ScaleToFit;
            if (!string.IsNullOrEmpty(itemId)) SetIcon(b, itemId);
            else b.text = "+";
            return b;
        }

        private void Refresh()
        {
            var ped = PedController.Current;
            if (ped != null && !PlantingValidator.InReach(ped.transform, _center, GameRules.Placement.ReachCells + 2)) { Close(); return; }
            _scan = KitchenScan.At(_center);

            var sig = new StringBuilder();
            foreach (string f in _foods) sig.Append(f).Append(',');
            sig.Append('|').Append(_drink).Append('|').Append(_bowl).Append(KitchenCook.Busy).Append(KitchenCook.Status).Append('#');
            foreach (KeyValuePair<string, int> kv in _scan.Stock) sig.Append(kv.Key).Append('x').Append(kv.Value).Append(';');
            foreach (DrinkSource d in _scan.Drinks) sig.Append(d.Liquid).Append(d.Total.ToString("0.##")).Append(';');
            foreach (KeyValuePair<string, int> kv in _scan.Empties) sig.Append(kv.Key).Append('e').Append(kv.Value).Append(';');
            foreach (SavedMeal m in SavedMeals.All) sig.Append(m.Name).Append(string.Join(",", m.Foods)).Append(m.Drink).Append(m.Bowl).Append(';');
            if (sig.ToString() == _signature) return;
            _signature = sig.ToString();

            // the plate and the glass
            _plate.Clear();
            for (int i = 0; i < MealBuilder.MaxFoods; i++)
            {
                int at = i;
                string food = i < _foods.Count ? _foods[i] : "";
                _plate.Add(Slot(food, food.Length > 0 ? HudBindings.GetItemName(food) + ": click to take it off the plate" : "An empty place on the plate", () => { if (at < _foods.Count) { _foods.RemoveAt(at); _signature = ""; Refresh(); } }, true));
            }
            _bowlSlot.Clear();
            _bowlSlot.Add(Slot(_bowl, _bowl.Length > 0 ? HudBindings.GetItemName(_bowl) + ": click to empty the bowl" : "The bowl: pick a soup, stew or salad below", () => { _bowl = ""; _signature = ""; Refresh(); }, true));
            _drinkSlot.Clear();
            _drinkSlot.Add(Slot(_drink.Length > 0 ? MealBuilder.Glass : "", _drink.Length > 0 ? HudBindings.GetItemName(_drink) + ": click to empty the glass" : "The glass: pick a drink below", () => { _drink = ""; _signature = ""; Refresh(); }, false));
            string why = MealBuilder.Missing(_foods, _drink, _scan, _bowl);
            _status.text = KitchenCook.Busy ? KitchenCook.Status : (why ?? "Ready: foods the kitchen has not got are cooked first.");
            _makeButton.SetEnabled(why == null && !KitchenCook.Busy);

            // the foods the kitchen has, less what is already on the plate
            _foodsList.Clear();
            var onPlate = new Dictionary<string, int>();
            foreach (string f in _foods) { onPlate.TryGetValue(f, out int n); onPlate[f] = n + 1; }
            bool anyFood = false;
            foreach (string food in MealBuilder.Candidates(_scan))
            {
                onPlate.TryGetValue(food, out int used);
                int left = MealBuilder.Stocked(_scan, food) - used;
                var test = new List<string>(_foods) { food };
                bool can = _foods.Count < MealBuilder.MaxFoods && MealPlanner.PlanFoods(test, "", _scan, false).Ok;
                if (left <= 0 && !can && !(_foods.Count >= MealBuilder.MaxFoods)) continue;   // not there and not cookable (with the plate as it is)
                anyFood = true;
                string id = food;
                string label = HudBindings.GetItemName(id) + (left > 1 ? "  x" + left : (left > 0 ? "" : "  (cook it)"));
                _foodsList.Add(Row(id, label, "Add", () =>
                {
                    if (_foods.Count >= MealBuilder.MaxFoods) { return; }
                    _foods.Add(id); _signature = ""; Refresh();
                }, can));
            }
            if (!anyFood) _foodsList.Add(Hint("Nothing to put on the plate: stock the kitchen with food or with ingredients and the appliances to cook them."));

            _bowlsList.Clear();
            bool anyBowl = false;
            foreach (string dish in MealBuilder.Candidates(_scan, true))
            {
                int have = MealBuilder.Stocked(_scan, dish) - (dish == _bowl ? 1 : 0);
                bool can = dish != _bowl && MealPlanner.PlanFoods(new List<string>(), "", _scan, false, dish).Ok;
                if (have <= 0 && !can && dish != _bowl) continue;
                anyBowl = true;
                string id = dish;
                string label = HudBindings.GetItemName(id) + (have > 1 ? "  x" + have : (have > 0 ? "" : "  (cook it)"));
                _bowlsList.Add(Row(id, label, id == _bowl ? "In bowl" : "Add", () => { _bowl = id; _signature = ""; Refresh(); }, id != _bowl));
            }
            if (!anyBowl) _bowlsList.Add(Hint("No soup, stew or salad: stock the kitchen with one, or with its ingredients, a Soup Bowl and the appliance to cook it."));

            _drinksList.Clear();
            bool anyDrink = false;
            foreach (KeyValuePair<string, float> d in MealBuilder.Drinks(_scan))
            {
                anyDrink = true;
                string liquid = d.Key;
                _drinksList.Add(Row(liquid, HudBindings.GetItemName(liquid) + "  (" + UnitFormat.Volume(d.Value) + ")", liquid == _drink ? "In glass" : "Pour", () => { _drink = liquid; _signature = ""; Refresh(); }, liquid != _drink));
            }
            if (!anyDrink) _drinksList.Add(Hint("No drink is stocked: fill a bottle at the juicer, or keep a jug of milk or water."));

            _savedList.Clear();
            if (SavedMeals.All.Count == 0) _savedList.Add(Hint("Nothing saved yet. Build a meal, name it and press Save."));
            foreach (SavedMeal saved in new List<SavedMeal>(SavedMeals.All)) _savedList.Add(SavedRow(saved));
        }

        private static Label Hint(string text)
        {
            var l = new Label(text);
            l.AddToClassList("container-panel-hint");
            return l;
        }

        private static VisualElement Row(string itemId, string text, string action, System.Action onClick, bool enabled)
        {
            var row = new VisualElement();
            row.AddToClassList("container-panel-row");
            var icon = new VisualElement();
            icon.AddToClassList("container-panel-icon");
            SetIcon(icon, itemId);
            row.Add(icon);
            var name = new Label(text);
            name.AddToClassList("container-panel-row-name");
            row.Add(name);
            var b = new Button(onClick) { text = action };
            b.AddToClassList("container-panel-btn");
            b.SetEnabled(enabled);
            row.Add(b);
            return row;
        }

        private VisualElement SavedRow(SavedMeal saved)
        {
            var row = new VisualElement();
            row.AddToClassList("container-panel-row");
            // the foods' icons in a small strip, so a saved meal can be told at a glance
            var strip = new VisualElement();
            strip.style.flexDirection = FlexDirection.Row;
            strip.style.width = 4 * 22 + 44;
            foreach (string f in saved.Foods)
            {
                var ic = new VisualElement();
                ic.style.width = ic.style.height = 20;
                ic.style.unityBackgroundScaleMode = ScaleMode.ScaleToFit;
                SetIcon(ic, f);
                strip.Add(ic);
            }
            if (!string.IsNullOrEmpty(saved.Bowl))
            {
                var ic = new VisualElement();
                ic.style.width = ic.style.height = 20;
                ic.style.unityBackgroundScaleMode = ScaleMode.ScaleToFit;
                SetIcon(ic, saved.Bowl);
                strip.Add(ic);
            }
            if (!string.IsNullOrEmpty(saved.Drink))
            {
                var ic = new VisualElement();
                ic.style.width = ic.style.height = 20;
                ic.style.unityBackgroundScaleMode = ScaleMode.ScaleToFit;
                SetIcon(ic, saved.Drink);
                strip.Add(ic);
            }
            row.Add(strip);
            string why = MealBuilder.Missing(saved.Foods, saved.Drink, _scan, saved.Bowl);
            var name = new Label(saved.Name);
            name.AddToClassList("container-panel-row-name");
            name.tooltip = DescribeMeal(saved) + (why != null ? "\n" + why : "");
            row.Add(name);
            SavedMeal s = saved;
            var make = new Button(() => MakeSaved(s)) { text = "Make", tooltip = why ?? "Make this meal again" };
            make.AddToClassList("container-panel-btn");
            make.SetEnabled(why == null && !KitchenCook.Busy);
            row.Add(make);
            var load = new Button(() => { _foods.Clear(); _foods.AddRange(s.Foods); _drink = s.Drink ?? ""; _bowl = s.Bowl ?? ""; _name.value = s.Name; _signature = ""; Refresh(); }) { text = "Load", tooltip = "Put it on the plate to change it" };
            load.AddToClassList("container-panel-btn");
            row.Add(load);
            var del = new Button(() => { SavedMeals.Remove(s); _signature = ""; Refresh(); }) { text = "X", tooltip = "Forget this saved meal" };
            del.AddToClassList("container-panel-btn");
            row.Add(del);
            return row;
        }

        private static string DescribeMeal(SavedMeal m)
        {
            var parts = new List<string>();
            foreach (string f in m.Foods) parts.Add(HudBindings.GetItemName(f));
            if (!string.IsNullOrEmpty(m.Bowl)) parts.Add(HudBindings.GetItemName(m.Bowl));
            if (!string.IsNullOrEmpty(m.Drink)) parts.Add(HudBindings.GetItemName(m.Drink));
            return string.Join(", ", parts);
        }

        private void MakeNow() { if (Cook("Meal Builder", new List<string>(_foods), _drink, _bowl)) Close(); }

        private void MakeSaved(SavedMeal saved) { if (Cook(saved.Name, new List<string>(saved.Foods), saved.Drink ?? "", saved.Bowl ?? "")) Close(); }

        /// <summary>Plans the meal on the kitchen as it is, walks the ped through the cookings it needs (none: it is served at once), then serves it. False when it could not start (the window stays open).</summary>
        private bool Cook(string title, List<string> foods, string drink, string bowl)
        {
            if (KitchenCook.Busy) return false;
            _scan = KitchenScan.At(_center);   // the stock may have changed since the list was drawn
            MealPlan plan = MealPlanner.PlanFoods(foods, drink, _scan, true, bowl);
            if (!plan.Ok) { ToastNotificationSystem.ShowInfo(title, plan.Why); return false; }
            KitchenCook.Begin(plan.Steps, _center,
                () =>
                {
                    if (!MealBuilder.Make(foods, drink, KitchenScan.At(_center), out string why, bowl)) ToastNotificationSystem.ShowInfo(title, why);
                    _signature = "";
                },
                msg => { ToastNotificationSystem.ShowInfo(title, msg); _signature = ""; });
            _signature = "";
            return true;
        }

        private void SaveNow()
        {
            if (_foods.Count == 0 && string.IsNullOrEmpty(_drink) && string.IsNullOrEmpty(_bowl)) { _status.text = "Put something on the plate first."; return; }
            SavedMeals.Save(_name.value, _foods, _drink, _bowl);
            _name.value = "";
            _signature = "";
            Refresh();
        }
    }
}
