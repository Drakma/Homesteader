// ToastNotificationSystem.cs - Dropdown Toast Notifications for Homesteader.
//
// ToastNotificationSystem.cs - Dropdown Toast Notifications for Homesteader.
//
// Features:
// - Mounts into ToastContainer underneath the top Header band.
// - Smooth dropdown animation as if dropping down from behind the header.
// - Newer toasts insert at the top and cleanly push older toasts downward.
// - Duration calculation: Minimum 5.0 seconds base, plus dynamic reading time
//   scaling with message length (~0.045s per character).
// - Paused game rule: If the game is Paused, toast countdown timers FREEZE and toasts
//   stay permanently until the game is unpaused.
// - Speed / Pause toasts: Speed changes and Pause/Resume trigger dedicated feedback toasts.
// - Type variants: Info (blue), Success (green), Warning (yellow/amber), Error (red).
// - Click to dismiss early.
// - Static API: ToastNotificationSystem.Show("Title", "Message", type);

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    public enum ToastType
    {
        Info,
        Success,
        Warning,
        Error,
        Severe
    }

    public sealed class ToastNotificationSystem : MonoBehaviour
    {
        private static ToastNotificationSystem s_instance;
        public static ToastNotificationSystem Instance => s_instance;

        private VisualElement _container;

        private sealed class ActiveToast
        {
            public VisualElement Element;
            public float RemainingDuration;
            public bool IsExiting;
            public bool IsPersistent;
        }

        private readonly List<ActiveToast> _activeToasts = new List<ActiveToast>();

        private void Awake()
        {
            if (s_instance != null && s_instance != this)
            {
                Destroy(gameObject);
                return;
            }
            s_instance = this;
        }

        public void BindContainer(VisualElement container)
        {
            _container = container;
            if (_container != null)
            {
                _container.Clear();
                _activeToasts.Clear();
            }
        }

        private void Update()
        {
            // Toast Lifetime countdown:
            // "if the game is Pause, the toast should stay until unpaused"
            bool isPaused = (TimeSystem.Instance.CurrentSpeed == HomesteaderSpeed.Pause);
            if (isPaused)
            {
                // Freeze countdown entirely while paused
                return;
            }

            float dt = Time.deltaTime;
            for (int i = _activeToasts.Count - 1; i >= 0; i--)
            {
                var toast = _activeToasts[i];
                if (toast.IsExiting || toast.IsPersistent) continue;

                toast.RemainingDuration -= dt;
                if (toast.RemainingDuration <= 0f)
                {
                    DismissToast(toast);
                }
            }
        }

        /// <summary>
        /// Displays a toast notification that drops down from behind the header.
        /// Duration is automatically computed: min 5.0 seconds, scaling with message length.
        /// </summary>
        public static void Show(string title, string message, ToastType type = ToastType.Info)
        {
            if (s_instance != null)
            {
                s_instance.CreateToast(title, message, type);
            }
            else
            {
                Debug.Log($"[Toast - {type}] {title}: {message}");
            }
        }

        public static void ShowInfo(string title, string message) => Show(title, message, ToastType.Info);
        public static void ShowSuccess(string title, string message) => Show(title, message, ToastType.Success);
        public static void ShowWarning(string title, string message) => Show(title, message, ToastType.Warning);
        public static void ShowError(string title, string message) => Show(title, message, ToastType.Error);
        public static void ShowSevere(string title, string message) => Show(title, message, ToastType.Severe);

        private void CreateToast(string title, string message, ToastType type)
        {
            if (_container == null)
            {
                var doc = FindAnyObjectByType<UIDocument>();
                if (doc != null && doc.rootVisualElement != null)
                {
                    BindContainer(doc.rootVisualElement.Q<VisualElement>("ToastContainer"));
                }
            }

            if (_container == null)
            {
                Debug.LogWarning($"[ToastNotificationSystem] Cannot show toast '{title}' - ToastContainer not found in UIDocument.");
                return;
            }

            // Duration calculation: Minimum 5.0s, plus 0.045s per character of title + message
            int charCount = (title?.Length ?? 0) + (message?.Length ?? 0);
            float duration = Mathf.Max(5.0f, 5.0f + (charCount * 0.045f));

            var toastElem = new VisualElement();
            toastElem.AddToClassList("toast-item");
            toastElem.AddToClassList("toast-item--entering");

            string typeClass;
            string iconGlyph;
            switch (type)
            {
                case ToastType.Success:
                    typeClass = "toast-item--success";
                    iconGlyph = "✓";
                    break;
                case ToastType.Warning:
                    typeClass = "toast-item--warning";
                    iconGlyph = "⚠";
                    break;
                case ToastType.Error:
                    typeClass = "toast-item--error";
                    iconGlyph = "✕";
                    break;
                case ToastType.Severe:
                    typeClass = "toast-item--severe";
                    iconGlyph = "!";
                    break;
                case ToastType.Info:
                default:
                    typeClass = "toast-item--info";
                    iconGlyph = "ℹ";
                    break;
            }
            toastElem.AddToClassList(typeClass);

            // Icon element
            var icon = new Label(iconGlyph);
            icon.AddToClassList("toast-icon");
            toastElem.Add(icon);

            // Content column
            var content = new VisualElement();
            content.AddToClassList("toast-content");

            if (!string.IsNullOrEmpty(title))
            {
                var titleLabel = new Label(title);
                titleLabel.AddToClassList("toast-title");
                content.Add(titleLabel);
            }

            if (!string.IsNullOrEmpty(message))
            {
                var msgLabel = new Label(message);
                msgLabel.AddToClassList("toast-message");
                content.Add(msgLabel);
            }
            toastElem.Add(content);

            var activeToast = new ActiveToast
            {
                Element = toastElem,
                RemainingDuration = duration,
                IsExiting = false,
                IsPersistent = (type == ToastType.Severe)
            };

            // Click to dismiss early (or dismiss severe toast)
            toastElem.RegisterCallback<ClickEvent>(evt =>
            {
                DismissToast(activeToast);
            });

            // Insert at index 0 (top of container).
            // Visual Elements in UI Toolkit flex-column layout will naturally push older children downward!
            _container.Insert(0, toastElem);
            _activeToasts.Insert(0, activeToast);

            // Trigger drop-down transition on next UI frame
            toastElem.schedule.Execute(() =>
            {
                toastElem.RemoveFromClassList("toast-item--entering");
            }).StartingIn(20);
        }

        private void DismissToast(ActiveToast toast)
        {
            if (toast == null || toast.IsExiting) return;
            toast.IsExiting = true;

            if (toast.Element != null)
            {
                toast.Element.AddToClassList("toast-item--exiting");

                // Remove from hierarchy after transition completes (0.35s)
                toast.Element.schedule.Execute(() =>
                {
                    if (toast.Element.parent != null)
                    {
                        toast.Element.parent.Remove(toast.Element);
                    }
                    _activeToasts.Remove(toast);
                }).StartingIn(360);
            }
            else
            {
                _activeToasts.Remove(toast);
            }
        }
    }
}
