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
        public static bool IsContainer(string itemId) => Capacity(itemId) > 0f;

        public static float Capacity(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            return info != null ? info.container_capacity_kg : 0f;
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

        public static bool Accepts(string containerId, string itemId)
        {
            var c = HudBindings.GetCatalogItem(containerId);
            if (c == null || c.container_capacity_kg <= 0f || string.IsNullOrEmpty(itemId) || itemId == containerId) return false;
            if (IsContainer(itemId)) return false;   // no containers inside containers
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

        public static float Used(List<ContainerStack> contents)
        {
            float used = 0f;
            if (contents != null) foreach (ContainerStack s in contents) used += WeightOf(s.ItemId) * s.Count;
            return used;
        }

        /// <summary>How many more of this item fit in the container, by weight.</summary>
        public static int RoomFor(string containerId, List<ContainerStack> contents, string itemId)
        {
            if (!Accepts(containerId, itemId)) return 0;
            float free = Capacity(containerId) - Used(contents);
            return free <= 0f ? 0 : Mathf.FloorToInt((free + 1e-4f) / WeightOf(itemId));
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

        /// <summary>C: close the window if it is open, else open the placed container under the cursor, else the toolbar's container.</summary>
        public static void Toggle(VisualElement anyElementOnPanel)
        {
            if (_open != null) { _open.Close(); return; }
            PlacedObject world = Homesteader.Growth.PlacementController.PlacedUnderCursor();
            if (world != null && ContainerRules.IsContainer(world.ItemId))
            {
                var ped = UnityEngine.Object.FindAnyObjectByType<PedController>();
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
            _window.AddToClassList("container-panel");
            _window.style.position = Position.Absolute;
            _window.style.left = 80;
            _window.style.top = 130;

            var header = new VisualElement();
            header.AddToClassList("container-panel-header");
            header.tooltip = "Drag to move";
            _title = new Label("Container");
            _title.AddToClassList("container-panel-title");
            _title.pickingMode = PickingMode.Ignore;
            var close = new Button(Close) { text = "×", tooltip = "Close (C)" };
            close.AddToClassList("steadify-mini-close");
            header.Add(_title);
            header.Add(close);
            _window.Add(header);
            MakeDraggable(_window, header);

            var body = new VisualElement();
            body.AddToClassList("container-panel-body");
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

            var h1 = new Label("INSIDE");
            h1.AddToClassList("container-panel-heading");
            body.Add(h1);
            _contentsList = new VisualElement();
            body.Add(_contentsList);

            var h2 = new Label("PUT IN FROM THE TOOLBAR");
            h2.AddToClassList("container-panel-heading");
            body.Add(h2);
            _toolbarList = new VisualElement();
            body.Add(_toolbarList);

            _footer = new VisualElement();
            body.Add(_footer);
            if (source is WorldSource)
            {
                var pick = new Button(PickUp) { text = "Pick up", tooltip = "Pick this container up, with everything in it, into the toolbar (the top one of a stack)" };
                pick.AddToClassList("container-panel-btn");
                pick.style.marginTop = 8;
                pick.style.alignSelf = Align.FlexEnd;
                _footer.Add(pick);
            }

            VisualElement wallpaper = panelRoot.Q<VisualElement>("WelcomeWallpaper");
            if (wallpaper != null && wallpaper.parent == panelRoot) panelRoot.Insert(panelRoot.IndexOf(wallpaper), _window);
            else panelRoot.Add(_window);

            _tick = _window.schedule.Execute(Refresh).Every(250);
            Refresh();
        }

        public void Close()
        {
            _tick?.Pause();
            _window.RemoveFromHierarchy();
            if (_open == this) _open = null;
        }

        private void Refresh()
        {
            if (!_source.Valid) { Close(); return; }   // the container left the toolbar, or was picked up
            if (_source is WorldSource ws)
            {
                var ped = UnityEngine.Object.FindAnyObjectByType<PedController>();
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
            _capacityText.text = $"{used:0.0} / {cap:0.0} kg";
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
                if (i == _source.ToolbarSlot || t.Count <= 0 || string.IsNullOrEmpty(t.IconId) || !ContainerRules.Accepts(id, t.IconId)) continue;
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
            name.tooltip = $"{ContainerRules.WeightOf(itemId):0.##} kg each";
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
            _signature = "";
            Refresh();
        }

        /// <summary>World containers: pick the container up into a free toolbar slot, contents and all.</summary>
        private void PickUp()
        {
            if (!(_source is WorldSource ws) || ws.Placed == null) return;
            if (!ws.Placed.IsTopOfStack) { ToastNotificationSystem.ShowInfo("Container", "Pick up the one on top first."); return; }
            HudState hud = HudState.Active;
            hud.EnsureToolbarSlots();
            int free = -1;
            for (int i = 0; i < hud.Toolbar.Count; i++)
                if (hud.Toolbar[i].Count <= 0 || string.IsNullOrEmpty(hud.Toolbar[i].IconId)) { free = i; break; }
            if (free < 0) { ToastNotificationSystem.ShowInfo("Container", "No free toolbar slot."); return; }
            hud.Toolbar[free] = new ToolbarSlotData { IconId = ws.Placed.ItemId, Count = 1, Contents = new List<ContainerStack>(ws.Placed.Contents) };
            ws.Placed.Remove();
            hud.SelectSlot(hud.SelectedSlot);
            HudBindings.Instance?.RefreshToolbar();
            Close();
        }

        private static void MakeDraggable(VisualElement window, VisualElement handle)
        {
            bool dragging = false;
            Vector2 startPointer = Vector2.zero, startPos = Vector2.zero;
            handle.RegisterCallback<PointerDownEvent>(evt =>
            {
                if (evt.target is Button) return;
                dragging = true;
                startPointer = evt.position;
                startPos = new Vector2(window.resolvedStyle.left, window.resolvedStyle.top);
                handle.CapturePointer(evt.pointerId);
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerMoveEvent>(evt =>
            {
                if (!dragging) return;
                Vector2 p = startPos + ((Vector2)evt.position - startPointer);
                var parent = window.parent;
                float maxX = (parent != null ? parent.resolvedStyle.width : Screen.width) - window.resolvedStyle.width;
                float maxY = (parent != null ? parent.resolvedStyle.height : Screen.height) - window.resolvedStyle.height;
                window.style.left = Mathf.Clamp(p.x, 0f, Mathf.Max(0f, maxX));
                window.style.top = Mathf.Clamp(p.y, 0f, Mathf.Max(0f, maxY));
                evt.StopPropagation();
            });
            handle.RegisterCallback<PointerUpEvent>(evt =>
            {
                if (!dragging) return;
                dragging = false;
                handle.ReleasePointer(evt.pointerId);
                evt.StopPropagation();
            });
        }
    }
}
