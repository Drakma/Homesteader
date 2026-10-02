using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>Small UI Toolkit event helpers.</summary>
    public static class UiEvents
    {
        /// <summary>Stops an event here and keeps the panel's default handling (for example moving keyboard focus) from running. Replaces the obsolete EventBase.PreventDefault.</summary>
        public static void Swallow(EventBase evt)
        {
            evt.StopPropagation();
            (evt.target as VisualElement)?.panel?.focusController?.IgnoreEvent(evt);
        }
    }
}
