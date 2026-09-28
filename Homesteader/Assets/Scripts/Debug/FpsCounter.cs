using UnityEngine;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// Formerly drew an FPS counter and zoom level in the bottom-left corner via IMGUI.
    /// That functionality has been replaced by <see cref="StatsOverlay"/> (F12 to toggle),
    /// which shows FPS, zoom, grid state, RAM, draw calls, and more in a compact stack.
    /// This class is kept only so existing scene references don't break; it no longer
    /// renders anything.
    /// </summary>
    public sealed class FpsCounter : MonoBehaviour
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<FpsCounter>() != null) return;
            var go = new GameObject("FpsCounter");
            DontDestroyOnLoad(go);
            go.AddComponent<FpsCounter>();
        }
    }
}
