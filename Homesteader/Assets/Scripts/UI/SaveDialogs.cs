using System;
using System.Collections.Generic;
using System.IO;
using Homesteader.Save;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// The dialogs of the save system, built in code on the welcome menu's panel: the name of a new game, the list of saves to load (a picture of
    /// the game, the name, when it was saved, the file size, the in-game day and the world seed; the list is every file in the Saves folder,
    /// autosaves included), and the autosave settings (how often, how many are kept) added to the Settings dialog. See docs/SAVE_GAME.md.
    /// </summary>
    public sealed class SaveDialogs
    {
        private readonly VisualElement _parent;
        private VisualElement _newDialog, _loadDialog;
        private TextField _nameField;
        private Label _newHint;
        private ScrollView _list;
        private Label _loadInfo;
        private Button _loadBtn, _deleteBtn;
        private SaveSlots.Entry _selected;
        private bool _hasSelection;
        private VisualElement _selectedRow;
        private readonly List<Texture2D> _thumbs = new List<Texture2D>();
        private Action<string> _onNew;
        private Action<SaveSlots.Entry> _onLoad;

        public SaveDialogs(VisualElement parent)
        {
            _parent = parent;
            BuildNew();
            BuildLoad();
        }

        // ------------------------------------------------------------------ new game

        private void BuildNew()
        {
            _newDialog = Dialog("NewGameDialog");
            VisualElement card = Card(_newDialog, "NEW GAME", "save-card--narrow");
            card.Add(new Label("Name your game. Its saves go in the Saves folder next to the game, as Name and Name-autosave.1, .2 and so on.") { name = "NewGameHint" }.With("settings-hint"));
            _nameField = new TextField("Save name") { value = "Homestead", maxLength = 40 };
            _nameField.AddToClassList("save-field");
            _nameField.RegisterValueChangedCallback(e => UpdateNewHint());
            card.Add(_nameField);
            _newHint = new Label("").With("settings-hint");
            card.Add(_newHint);
            VisualElement row = Footer(card);
            Button start = Btn("Start", true);
            start.clicked += () =>
            {
                string name = SaveSlots.Sanitize(_nameField.value);
                HideNew();
                _onNew?.Invoke(name);
            };
            Button cancel = Btn("Cancel", false);
            cancel.clicked += HideNew;
            row.Add(start);
            row.Add(cancel);
        }

        /// <summary>Closes the name dialog and lets go of the keyboard: a text field that keeps the focus stops the character walking (HudBindings.KeyboardCaptured).</summary>
        private void HideNew()
        {
            _nameField.Blur();
            _newDialog.style.display = DisplayStyle.None;
        }

        private void UpdateNewHint()
        {
            string wanted = SaveSlots.Sanitize(_nameField.value);
            string unique = SaveSlots.UniqueName(wanted);
            _newHint.text = unique == wanted ? "Will be saved as \"" + wanted + "\"." : "\"" + wanted + "\" is taken: it will be saved as \"" + unique + "\".";
        }

        public void ShowNew(Action<string> onStart)
        {
            _onNew = onStart;
            _nameField.SetValueWithoutNotify("Homestead");
            UpdateNewHint();
            _newDialog.style.display = DisplayStyle.Flex;
            _nameField.Focus();
        }

        // ------------------------------------------------------------------ load

        private void BuildLoad()
        {
            _loadDialog = Dialog("LoadGameDialog");
            VisualElement card = Card(_loadDialog, "LOAD GAME", "save-card--wide");
            _list = new ScrollView(ScrollViewMode.Vertical);
            _list.AddToClassList("save-list");
            card.Add(_list);
            _loadInfo = new Label("").With("settings-hint");
            card.Add(_loadInfo);
            VisualElement row = Footer(card);
            _loadBtn = Btn("Load", true);
            _loadBtn.clicked += LoadSelected;
            _deleteBtn = Btn("Delete", false);
            _deleteBtn.clicked += DeleteSelected;
            Button close = Btn("Close", false);
            close.clicked += HideLoad;
            row.Add(_loadBtn);
            row.Add(_deleteBtn);
            row.Add(close);
        }

        public void ShowLoad(Action<SaveSlots.Entry> onLoad)
        {
            _onLoad = onLoad;
            Refill();
            _loadDialog.style.display = DisplayStyle.Flex;
        }

        private void HideLoad()
        {
            _loadDialog.style.display = DisplayStyle.None;
            ReleaseThumbs();
        }

        private void ReleaseThumbs()
        {
            foreach (Texture2D t in _thumbs) if (t != null) UnityEngine.Object.Destroy(t);
            _thumbs.Clear();
        }

        private void Refill()
        {
            ReleaseThumbs();
            _list.Clear();
            _hasSelection = false;
            _selectedRow = null;
            List<SaveSlots.Entry> all = SaveSlots.List();
            if (all.Count == 0)
            {
                _list.Add(new Label("No saves yet. Start a game: it autosaves, and the Save button or F9 saves it by name.").With("settings-hint"));
            }
            foreach (SaveSlots.Entry entry in all)
            {
                SaveSlots.Entry e = entry;
                var row = new VisualElement();
                row.AddToClassList("save-row");
                var pic = new VisualElement();
                pic.AddToClassList("save-thumb");
                if (File.Exists(e.ThumbPath))
                {
                    try
                    {
                        var tex = new Texture2D(2, 2, TextureFormat.RGB24, false);
                        if (tex.LoadImage(File.ReadAllBytes(e.ThumbPath))) { _thumbs.Add(tex); pic.style.backgroundImage = new StyleBackground(tex); }
                        else UnityEngine.Object.Destroy(tex);
                    }
                    catch (Exception) { }
                }
                row.Add(pic);
                var text = new VisualElement();
                text.AddToClassList("save-text");
                var name = new Label(e.Label);
                name.AddToClassList("save-name");
                if (e.IsAutosave) name.AddToClassList("save-name--auto");
                text.Add(name);
                text.Add(new Label(e.Saved.ToString("yyyy-MM-dd  HH:mm") + "   -   " + SaveSlots.SizeText(e.Bytes)).With("save-meta"));
                text.Add(new Label("Day " + e.Day + " of the year   -   world " + e.Seed).With("save-meta"));
                row.Add(text);
                row.RegisterCallback<ClickEvent>(ev =>
                {
                    Select(e, row);
                    if (ev.clickCount >= 2) LoadSelected();
                });
                _list.Add(row);
            }
            if (all.Count > 0) Select(all[0], _list.contentContainer[0]);
            UpdateButtons();
        }

        private void Select(SaveSlots.Entry e, VisualElement row)
        {
            _selectedRow?.RemoveFromClassList("save-row--selected");
            _selected = e;
            _hasSelection = true;
            _selectedRow = row;
            row.AddToClassList("save-row--selected");
            _loadInfo.text = e.Path;
            UpdateButtons();
        }

        private void UpdateButtons()
        {
            _loadBtn.SetEnabled(_hasSelection);
            _deleteBtn.SetEnabled(_hasSelection);
        }

        private void LoadSelected()
        {
            if (!_hasSelection) return;
            SaveSlots.Entry e = _selected;
            HideLoad();
            _onLoad?.Invoke(e);
        }

        private void DeleteSelected()
        {
            if (!_hasSelection) return;
            SaveSlots.Delete(_selected);
            Refill();
        }

        // ------------------------------------------------------------------ settings

        /// <summary>Adds the autosave settings to the General page of the Settings dialog.</summary>
        public static void AddAutosaveSettings(VisualElement page)
        {
            if (page == null || page.Q<SliderInt>("AutosaveMinutes") != null) return;
            var title = new Label("Saving").With("settings-section-title");
            // sliders like the other settings: label on the left, a value label on the right (the built-in input box renders black in the runtime theme)
            SliderInt Make(string name, string label, int low, int high, int value, string tip, Action<int> set, Func<int, string> show)
            {
                var sl = new SliderInt(label, low, high) { name = name, value = Mathf.Clamp(value, low, high), showInputField = false, tooltip = tip };
                sl.AddToClassList("hs-slider");
                var val = new Label(show(sl.value)) { pickingMode = PickingMode.Ignore };
                val.AddToClassList("hs-slider-value");
                sl.RegisterValueChangedCallback(e => { set(e.newValue); val.text = show(e.newValue); });
                sl.Add(val);
                return sl;
            }
            SliderInt minutes = Make("AutosaveMinutes", "Autosave every", 1, 60, SaveSlots.AutosaveMinutes,
                "How often the game saves by itself (1 to 60 minutes).", v => SaveSlots.AutosaveMinutes = v, v => v + " min");
            SliderInt keep = Make("AutosaveKeep", "Autosaves kept", 1, 20, SaveSlots.AutosaveKeep,
                "How many autosaves are kept (1 to 20). Name-autosave.1 is the newest; the oldest rolls off.", v => SaveSlots.AutosaveKeep = v, v => v.ToString());
            var hint = new Label("Autosaves are named Name-autosave.1, .2, .3 ... (1 is the newest). All saves are in the Saves folder next to the game.").With("settings-hint");
            VisualElement container = page is ScrollView sv ? sv.contentContainer : page;
            // before the "Defaults" section, when there is one
            int at = container.childCount;
            for (int i = 0; i < container.childCount; i++)
                if (container[i] is Label l && l.text == "Defaults") { at = i; break; }
            container.Insert(at, hint);
            container.Insert(at, keep);
            container.Insert(at, minutes);
            container.Insert(at, title);
        }

        // ------------------------------------------------------------------ building blocks

        private VisualElement Dialog(string name)
        {
            var d = new VisualElement { name = name };
            d.AddToClassList("settings-dialog");
            d.style.display = DisplayStyle.None;
            _parent.Add(d);
            return d;
        }

        private static VisualElement Card(VisualElement dialog, string title, string sizeClass)
        {
            var card = new VisualElement();
            card.AddToClassList("settings-card");
            card.AddToClassList(sizeClass);
            var edge = new VisualElement();
            edge.AddToClassList("hs-accent-edge");
            edge.pickingMode = PickingMode.Ignore;
            card.Add(edge);
            card.Add(new Label(title).With("settings-title"));
            dialog.Add(card);
            return card;
        }

        private static VisualElement Footer(VisualElement card)
        {
            var row = new VisualElement();
            row.AddToClassList("save-footer");
            card.Add(row);
            return row;
        }

        private static Button Btn(string text, bool primary)
        {
            var b = new Button { text = text };
            b.AddToClassList("welcome-btn");
            if (primary) b.AddToClassList("welcome-btn--primary");
            b.AddToClassList("save-footer-btn");
            return b;
        }
    }

    internal static class SaveDialogExtensions
    {
        /// <summary>Adds a style class and returns the element, so labels can be created and classed in one expression.</summary>
        public static T With<T>(this T e, string cls) where T : VisualElement
        {
            e.AddToClassList(cls);
            return e;
        }
    }
}
