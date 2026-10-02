using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// Dropdown popup lists are built at the root of the panel, outside every UIDocument, so the HUD style sheets never reach
    /// them (they came out as bare text on a see-through background). This puts PopupMenu.uss on the panel root, once.
    /// Call <see cref="Ensure"/> with any element of the document that has dropdowns.
    /// </summary>
    public static class PopupStyles
    {
        private static StyleSheet _sheet;

        public static void Ensure(VisualElement anyElement)
        {
            if (anyElement == null) return;
            if (anyElement.panel != null) { Apply(anyElement.panel.visualTree); return; }
            anyElement.RegisterCallback<AttachToPanelEvent>(e => Apply((e.target as VisualElement)?.panel?.visualTree));
        }

        private static void Apply(VisualElement root)
        {
            if (root == null) return;
            if (_sheet == null) _sheet = Resources.Load<StyleSheet>("HUDTree/PopupMenu");
            if (_sheet == null || root.styleSheets.Contains(_sheet)) return;
            root.styleSheets.Add(_sheet);
        }
    }
}
