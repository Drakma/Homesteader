using System.Diagnostics;

/// <summary>
/// Debug chatter. Calls compile away entirely (arguments are never evaluated) unless the HS_DEBUG_LOG scripting define is set, so
/// logging cannot cause frame spikes in normal play. Warnings and errors still go through UnityEngine.Debug.
/// </summary>
public static class Dbg
{
    [Conditional("HS_DEBUG_LOG")]
    public static void Log(object message) { UnityEngine.Debug.Log(message); }

    [Conditional("HS_DEBUG_LOG")]
    public static void Log(object message, UnityEngine.Object context) { UnityEngine.Debug.Log(message, context); }
}
