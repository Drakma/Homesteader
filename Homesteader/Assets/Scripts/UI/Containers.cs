// Containers.cs - the storage / capacity / container scheme.
//
// An item is a container when its manifest declares properties.container_capacity_kg > 0 (and optionally container_accepts: categories, #tags or
// item ids; empty = anything). Capacity is WEIGHT: the sum of every stored item's weight_kg x count may not pass the capacity. A container sits in a
// toolbar slot and carries its own contents (ToolbarSlotData.Contents), or stands in the world as a placed object (PlacedObject.Contents). Picked-up
// items that a toolbar container accepts go into it first (see HudState.AddItemToToolbar); the C key opens the contents window (ContainerPanel) for
// the placed container under the cursor, or else for the container in the toolbar, to put items in and take them out.
// properties.container_stacking_limit lets identical placed containers stack on each other in the world, up to that many high (1 = they do not).

using System;
using System.Collections.Generic;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    [Serializable]
    public class ContainerStack
    {
        public string ItemId;
        public int Count;
    }

    public static class ContainerRules
    {
        /// <summary>A carried / placed container. A STRUCTURE blueprint with a container block (a grain silo) is not one: it is storage built into the structure.</summary>
        public static bool IsContainer(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.container_capacity_kg > 0f && !info.is_blueprint;
        }

        /// <summary>A single-use container (a cardboard box): a placed one goes away when it has been emptied.</summary>
        public static bool IsDisposable(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.container_disposable;
        }

        public static float Capacity(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null ? info.container_capacity_kg : 0f;
        }

        /// <summary>The most items the container holds in all, whatever they weigh (a battery rack's slots); 0 = limited by weight only.</summary>
        public static int MaxItems(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.container_max_items > 0 ? info.container_max_items : 0;
        }

        /// <summary>How many identical placed containers can be stacked in one grid square (1 = no stacking).</summary>
        public static int StackingLimit(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.container_stacking_limit > 1 ? info.container_stacking_limit : 1;
        }

        /// <summary>Weight of one of this item (a tiny floor, so a weightless item still takes some room).</summary>
        public static float WeightOf(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null && info.weight_kg > 0.001f ? info.weight_kg : 0.001f;
        }

        public static bool Accepts(string containerId, string itemId, List<ContainerStack> contents = null)
        {
            var c = HudBindings.GetCatalogItem(containerId);
            if (c == null || c.container_capacity_kg <= 0f || string.IsNullOrEmpty(itemId) || itemId == containerId) return false;
            if (IsContainer(itemId)) return false;   // no containers inside containers
            // A single-type container (a crate) takes only what it already holds, once it holds something.
            if (c.container_single_type && contents != null && contents.Exists(x => x.Count > 0 && x.ItemId != itemId)) return false;
            if (c.container_accepts == null || c.container_accepts.Count == 0) return true;
            var item = HudBindings.GetCatalogItem(itemId);
            foreach (string a in c.container_accepts)
            {
                if (string.IsNullOrEmpty(a)) continue;
                if (item != null && string.Equals(a, item.category, StringComparison.OrdinalIgnoreCase)) return true;
                if (GrowthRegistry.ToolMatches(a, itemId)) return true;
            }
            return false;
        }

        /// <summary>
        /// A copy that shares nothing with the original. A shallow copy (new List of the same stacks) made a held container and a
        /// placed one edit the SAME stack objects, so a transfer between them added and removed the same count and nothing changed.
        /// </summary>
        public static List<ContainerStack> Clone(List<ContainerStack> contents)
        {
            var copy = new List<ContainerStack>();
            if (contents != null) foreach (ContainerStack c in contents) copy.Add(new ContainerStack { ItemId = c.ItemId, Count = c.Count });
            return copy;
        }

        public static float Used(List<ContainerStack> contents)
        {
            float used = 0f;
            if (contents != null) foreach (ContainerStack s in contents) used += WeightOf(s.ItemId) * s.Count;
            return used;
        }

        /// <summary>How many more of this item fit in the container, by weight.</summary>
        public static int RoomFor(string containerId, List<ContainerStack> contents, string itemId)
        {
            if (!Accepts(containerId, itemId, contents)) return 0;
            float free = Capacity(containerId) - Used(contents);
            int room = free <= 0f ? 0 : Mathf.FloorToInt((free + 1e-4f) / WeightOf(itemId));
            int slots = MaxItems(containerId);
            if (slots > 0)
            {
                int held = 0;
                if (contents != null) foreach (ContainerStack c in contents) held += c.Count;
                room = Mathf.Min(room, Mathf.Max(0, slots - held));
            }
            return room;
        }

        /// <summary>Puts up to <paramref name="count"/> into the contents; returns how many went in.</summary>
        public static int Add(string containerId, List<ContainerStack> contents, string itemId, int count)
        {
            int n = Mathf.Min(count, RoomFor(containerId, contents, itemId));
            if (n <= 0) return 0;
            ContainerStack found = contents.Find(s => s.ItemId == itemId);
            if (found != null) found.Count += n;
            else contents.Add(new ContainerStack { ItemId = itemId, Count = n });
            return n;
        }

        /// <summary>Takes up to <paramref name="count"/> out of the contents; returns how many came out.</summary>
        public static int Remove(List<ContainerStack> contents, string itemId, int count)
        {
            ContainerStack found = contents?.Find(s => s.ItemId == itemId);
            if (found == null) return 0;
            int n = Mathf.Min(count, found.Count);
            found.Count -= n;
            if (found.Count <= 0) contents.Remove(found);
            return n;
        }
    }

    /// <summary>
    /// The contents window of one container: capacity bar, what is inside (click a row to take it out) and what in the toolbar it would accept (click
    /// a row to put it in). The container is either a toolbar slot or a placed container in the world (which can also be picked up from here).
    /// Toggled with the C key.
    /// </summary>
    public sealed class ContainerPanel
    {
        private static ContainerPanel _open;
        public static bool IsOpen => _open != null;

        /// <summary>Closes the contents window if one is open (Esc). True when there was one.</summary>
        public static bool CloseOpen()
        {
            if (_open == null) return false;
            _open.Close();
            return true;
        }

        /// <summary>C: close the window if it is open, else open the placed container under the cursor, else the toolbar's container.</summary>
        public static void Toggle(VisualElement anyElementOnPanel)
        {
            if (_open != null) { _open.Close(); return; }
            PlacedObject world = Homesteader.Growth.PlacementController.PlacedUnderCursor();
            if (world != null && ContainerRules.IsContainer(world.ItemId))
            {
                var ped = PedController.Current;
                if (ped != null && !PlantingValidator.InReach(ped.transform, world.transform.position, GameRules.Placement.ReachCells))
                {
                    ToastNotificationSystem.ShowInfo("Container", "That is too far away.");
                    return;
                }
                Open(anyElementOnPanel, new WorldSource(world));
                return;
            }
            int slot = FindContainerSlot();
            if (slot < 0) { ToastNotificationSystem.ShowInfo("Container", "No container in the toolbar, and none under the cursor."); return; }
            Open(anyElementOnPanel, new ToolbarSource(slot));
        }

        private static void Open(VisualElement anyElementOnPanel, Source source)
        {
            var top = anyElementOnPanel;
            var tree = top?.panel?.visualTree;
            if (top == null || tree == null) return;
            while (top.parent != null && top.parent != tree) top = top.parent;
            _open = new ContainerPanel(top, source);
        }

        /// <summary>The toolbar slot of the container to show: the active slot if it holds one, else the first container in the toolbar.</summary>
        private static int FindContainerSlot()
        {
            HudState hud = HudState.Active;
            hud.EnsureToolbarSlots();
            if (hud.SelectedSlot >= 0 && hud.SelectedSlot < hud.Toolbar.Count && hud.Toolbar[hud.SelectedSlot].Count == 1 && ContainerRules.IsContainer(hud.Toolbar[hud.SelectedSlot].IconId)) return hud.SelectedSlot;
            for (int i = 0; i < hud.Toolbar.Count; i++)
                if (hud.Toolbar[i].Count == 1 && ContainerRules.IsContainer(hud.Toolbar[i].IconId)) return i;
            return -1;
        }

        // ------------------------------------------------------------------ where the container lives

        private abstract class Source
        {
            public abstract bool Valid { get; }
            public abstract string ItemId { get; }
            public abstract List<ContainerStack> Contents { get; }
            public virtual int ToolbarSlot => -1;
        }

        private sealed class ToolbarSource : Source
        {
            private readonly int _slot;
            public ToolbarSource(int slot) { _slot = slot; }
            private ToolbarSlotData Data => HudState.Active.Toolbar[_slot];
            public override bool Valid => _slot < HudState.Active.Toolbar.Count && Data.Count == 1 && ContainerRules.IsContainer(Data.IconId);
            public override string ItemId => Data.IconId;
            public override int ToolbarSlot => _slot;
            public override List<ContainerStack> Contents
            {
                get
                {
                    ToolbarSlotData d = Data;
                    if (d.Contents == null) { d.Contents = new List<ContainerStack>(); HudState.Active.Toolbar[_slot] = d; }
                    return d.Contents;
                }
            }
        }

        private sealed class WorldSource : Source
        {
            public readonly PlacedObject Placed;
            public WorldSource(PlacedObject p) { Placed = p; }
            public override bool Valid => Placed != null;
            public override string ItemId => Placed.ItemId;
            public override List<ContainerStack> Contents => Placed.Contents;
        }

        // ------------------------------------------------------------------ the window

        private readonly Source _source;
        private readonly VisualElement _window;
        private readonly Label _title;
        private readonly Label _capacityText;
        private readonly VisualElement _barFill;
        private readonly VisualElement _contentsList;
        private readonly VisualElement _toolbarList;
        private readonly VisualElement _footer;
        private IVisualElementScheduledItem _tick;
        private string _signature = "";

        private ContainerPanel(VisualElement panelRoot, Source source)
        {
            _source = source;
            _window = new VisualElement { name = "ContainerPanel" };
            _window.AddToClassList("window");
            _window.AddToClassList("container-panel");
            var edge = new VisualElement { pickingMode = PickingMode.Ignore };
            edge.AddToClassList("hs-accent-edge");
            _window.Add(edge);
            _window.style.position = Position.Absolute;

            var header = new VisualElement();
            header.AddToClassList("window-header");
            header.tooltip = "Drag to move";
            _title = new Label("Container");
            _title.AddToClassList("window-title");
            _title.pickingMode = PickingMode.Ignore;
            var close = new Button(Close) { text = "X", tooltip = "Close (C)" };
            close.AddToClassList("hs-close");
            header.Add(_title);
            header.Add(close);
            _window.Add(header);
            WindowPositions.MakeDraggable(_window, header, "container");

            var body = new VisualElement();
            body.AddToClassList("window-body");
            _window.Add(body);

            _capacityText = new Label("");
            _capacityText.AddToClassList("container-panel-capacity");
            _capacityText.tooltip = "Weight held / the most it can hold";
            body.Add(_capacityText);
            var bar = new VisualElement();
            bar.AddToClassList("container-panel-bar");
            _barFill = new VisualElement();
            _barFill.AddToClassList("container-panel-bar-fill");
            bar.Add(_barFill);
            body.Add(bar);

            // Pick up sits ABOVE the lists, where it never moves. At the bottom it slid up under the pointer as rows were taken out, so
            // the click meant for the last "Take" picked the whole container up instead (it looked like the box vanished).
            _footer = new VisualElement();
            body.Add(_footer);
            if (source is WorldSource)
            {
                var pick = new Button(PickUp) { text = "Pick up", tooltip = "Pick this container up, with everything in it, into the toolbar (the top one of a stack)" };
                pick.AddToClassList("hs-btn");
                pick.AddToClassList("hs-btn--primary");
                pick.style.marginTop = 8;
                pick.style.alignSelf = Align.FlexEnd;
                _footer.Add(pick);
            }

            var h1 = new Label("INSIDE");
            h1.AddToClassList("window-section-title");
            body.Add(h1);
            _contentsList = new VisualElement();
            body.Add(_contentsList);

            var h2 = new Label("PUT IN FROM THE TOOLBAR");
            h2.AddToClassList("window-section-title");
            body.Add(h2);
            _toolbarList = new VisualElement();
            body.Add(_toolbarList);

            VisualElement wallpaper = panelRoot.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == panelRoot) panelRoot.Insert(panelRoot.IndexOf(wallpaper), _window);
            else panelRoot.Add(_window);
            WindowPositions.Place(_window, "container");   // centered the first time, then where it was left

            _tick = _window.schedule.Execute(Refresh).Every(250);
            Refresh();
        }

        public void Close()
        {
            _tick?.Pause();
            WindowPositions.Remember(_window, "container");
            _window.RemoveFromHierarchy();
            if (_open == this) _open = null;
        }

        private void Refresh()
        {
            if (!_source.Valid) { Close(); return; }   // the container left the toolbar, or was picked up
            if (_source is WorldSource ws)
            {
                var ped = PedController.Current;
                if (ped != null && !PlantingValidator.InReach(ped.transform, ws.Placed.transform.position, GameRules.Placement.ReachCells + 1)) { Close(); return; }
            }

            HudState hud = HudState.Active;
            string id = _source.ItemId;
            List<ContainerStack> contents = _source.Contents;

            // Rebuild the rows only when something changed.
            var sig = new System.Text.StringBuilder(id);
            foreach (ContainerStack s in contents) sig.Append('|').Append(s.ItemId).Append('x').Append(s.Count);
            sig.Append('#');
            for (int i = 0; i < hud.Toolbar.Count; i++) sig.Append(hud.Toolbar[i].IconId).Append(hud.Toolbar[i].Count).Append(',');
            if (sig.ToString() == _signature) return;
            _signature = sig.ToString();

            float cap = ContainerRules.Capacity(id), used = ContainerRules.Used(contents);
            _title.text = HudBindings.GetItemName(id);
            _capacityText.text = UnitFormat.WeightPair(used, cap);
            _barFill.style.width = Length.Percent(Mathf.Clamp01(cap > 0f ? used / cap : 0f) * 100f);
            _barFill.EnableInClassList("container-panel-bar-fill--full", used >= cap - 0.001f);

            _contentsList.Clear();
            if (contents.Count == 0) _contentsList.Add(Hint("Empty." + (_source is ToolbarSource ? " Picked-up items it accepts go in automatically." : "")));
            foreach (ContainerStack s in contents)
            {
                ContainerStack stack = s;
                _contentsList.Add(Row(stack.ItemId, stack.Count, "Take", () => TakeOut(stack.ItemId)));
            }

            _toolbarList.Clear();
            bool any = false;
            for (int i = 0; i < hud.Toolbar.Count; i++)
            {
                ToolbarSlotData t = hud.Toolbar[i];
                if (i == _source.ToolbarSlot || t.Count <= 0 || string.IsNullOrEmpty(t.IconId) || !ContainerRules.Accepts(id, t.IconId, _source.Contents)) continue;
                int slot = i;
                _toolbarList.Add(Row(t.IconId, t.Count, "Put in", () => PutIn(slot)));
                any = true;
            }
            if (!any) _toolbarList.Add(Hint("Nothing in the toolbar fits."));
        }

        private static Label Hint(string text)
        {
            var l = new Label(text);
            l.AddToClassList("container-panel-hint");
            return l;
        }

        private static VisualElement Row(string itemId, int count, string action, Action onClick)
        {
            var row = new VisualElement();
            row.AddToClassList("container-panel-row");
            var icon = new VisualElement();
            icon.AddToClassList("container-panel-icon");
            var tex = PhoneController.GetItemIcon(itemId + ".png", itemId);
            if (tex != null) icon.style.backgroundImage = new StyleBackground(tex);
            row.Add(icon);
            var name = new Label(HudBindings.GetItemName(itemId) + (count > 1 ? "  x" + count : ""));
            name.AddToClassList("container-panel-row-name");
            name.tooltip = UnitFormat.Weight(ContainerRules.WeightOf(itemId), "0.##") + " each";
            row.Add(name);
            var b = new Button(onClick) { text = action, tooltip = action == "Take" ? "Take all of these out into the toolbar" : "Put as many of these in as fit" };
            b.AddToClassList("container-panel-btn");
            row.Add(b);
            return row;
        }

        /// <summary>Moves a whole stack from the toolbar slot into the container, as much as fits by weight.</summary>
        private void PutIn(int fromSlot)
        {
            HudState hud = HudState.Active;
            if (!_source.Valid || fromSlot < 0 || fromSlot >= hud.Toolbar.Count) return;
            ToolbarSlotData from = hud.Toolbar[fromSlot];
            int moved = ContainerRules.Add(_source.ItemId, _source.Contents, from.IconId, from.Count);
            if (moved <= 0) { ToastNotificationSystem.ShowInfo("Container", HudBindings.GetItemName(_source.ItemId) + " is full."); return; }
            from.Count -= moved;
            if (from.Count <= 0) from = ToolbarSlotData.Empty();
            hud.Toolbar[fromSlot] = from;
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            _signature = "";
            Refresh();
        }

        /// <summary>Moves a whole stack out of the container into the toolbar (as much as the toolbar has room for).</summary>
        private void TakeOut(string itemId)
        {
            HudState hud = HudState.Active;
            if (!_source.Valid) return;
            ContainerStack s = _source.Contents.Find(x => x.ItemId == itemId);
            if (s == null) return;
            int added = hud.AddItemToToolbar(itemId, s.Count, HudBindings.GetMaxStack(itemId), useContainers: false);
            if (added <= 0) { ToastNotificationSystem.ShowInfo("Container", "The toolbar is full."); return; }
            ContainerRules.Remove(_source.Contents, itemId, added);
            HudBindings.Instance?.RefreshToolbar();
            // an emptied cardboard box on the ground goes away
            if (_source is WorldSource spent && spent.Placed != null && spent.Contents.Count == 0 && ContainerRules.IsDisposable(spent.Placed.ItemId))
            {
                spent.Placed.Remove();
                Close();
                return;
            }
            _signature = "";
            Refresh();
        }

        /// <summary>World containers: pick the container up into a free toolbar slot, contents and all.</summary>
        private void PickUp()
        {
            if (!(_source is WorldSource ws) || ws.Placed == null) return;
            HudState hud = HudState.Active;
            hud.EnsureToolbarSlots();
            int free = -1;
            for (int i = 0; i < hud.Toolbar.Count; i++)
                if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { free = i; break; }
            if (free < 0) { ToastNotificationSystem.ShowInfo("Container", "No free toolbar slot."); return; }
            hud.Toolbar[free] = new ToolbarSlotData { IconId = ws.Placed.ItemId, Count = 1, Contents = ContainerRules.Clone(ws.Placed.Contents) };
            ws.Placed.Remove();
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            Close();
        }

    }
}
