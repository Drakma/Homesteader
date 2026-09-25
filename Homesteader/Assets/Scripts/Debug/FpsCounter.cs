using UnityEngine;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// A simple FPS counter drawn in the lower-left corner via IMGUI (OnGUI), so it needs no
    /// scene wiring or UXML changes. Bootstraps itself on scene load. Smoothed over ~0.5s so the
    /// number doesn't flicker every single frame.
    /// </summary>
    public sealed class FpsCounter : MonoBehaviour
    {
        private float _accumTime;
        private int _accumFrames;
        private float _fps;
        private GUIStyle _style;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<FpsCounter>() != null) return;
            var go = new GameObject("FpsCounter");
            DontDestroyOnLoad(go);
            go.AddComponent<FpsCounter>();
        }

        private void Update()
        {
            _accumTime += Time.unscaledDeltaTime;
            _accumFrames++;
            if (_accumTime >= 0.5f)
            {
                _fps = _accumFrames / _accumTime;
                _accumTime = 0f;
                _accumFrames = 0;
            }
        }

        private IsometricLockedCamera _isoCam;
        private GUIStyle _zoomStyle;

        private void OnGUI()
        {
            if (_style == null)
            {
                _style = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 20,
                    fontStyle = FontStyle.Bold,
                    normal = { textColor = _fps >= 45f ? Color.green : (_fps >= 25f ? Color.yellow : Color.red) }
                };
            }
            _style.normal.textColor = _fps >= 45f ? Color.green : (_fps >= 25f ? Color.yellow : Color.red);

            if (_zoomStyle == null)
            {
                _zoomStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 20,
                    fontStyle = FontStyle.Bold,
                    normal = { textColor = Color.white }
                };
            }

            const float w = 140f, h = 30f, margin = 12f;
            var rect = new Rect(margin, Screen.height - h - margin, w, h);
            GUI.Box(rect, GUIContent.none);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 4f, w - 16f, h - 8f), $"{_fps:F0} FPS", _style);

            // Zoom level, right of the FPS box: the isometric camera's orthographic
            // size, the same value Ctrl+ScrollWheel adjusts in IsometricLockedCamera.
            if (_isoCam == null) _isoCam = FindAnyObjectByType<IsometricLockedCamera>();
            if (_isoCam != null)
            {
                var zoomCam = _isoCam.GetComponent<Camera>();
                if (zoomCam != null)
                {
                    var zoomRect = new Rect(rect.xMax + 8f, rect.y, w, h);
                    GUI.Box(zoomRect, GUIContent.none);
                    GUI.Label(new Rect(zoomRect.x + 8f, zoomRect.y + 4f, w - 16f, h - 8f),
                        $"Zoom {zoomCam.orthographicSize:F1}", _zoomStyle);
                }
            }
        }
    }
}
