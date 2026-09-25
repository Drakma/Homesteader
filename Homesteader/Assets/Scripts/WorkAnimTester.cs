using UnityEngine;
using UnityEngine.InputSystem;
using Homesteader.Animation;
using Homesteader.UI;

/// <summary>
/// Development-only hotkeys to preview the work animations on the player.
/// Press the key again (or move) to stop. Remove once gameplay code triggers the clips.
///
///   F5 chop   F6 dig   F7 hoe   F8 plant   F9 pet   F10 kneel   F11 sleep
///   F12 drag (upper body, layered over walking)     Insert = toggle two-arm carry walk
/// </summary>
public sealed class WorkAnimTester : MonoBehaviour
{
    private GlbClipPlayer _clips;
    private PedController _ped;
    private bool _drag;

    private void Update()
    {
        if (HudBindings.KeyboardCaptured) return;
        var kb = Keyboard.current;
        if (kb == null) return;

        if (_clips == null) _clips = GetComponentInChildren<GlbClipPlayer>();
        if (_ped == null) _ped = GetComponent<PedController>();
        if (_clips == null || !_clips.IsReady) return;

        if (kb.f5Key.wasPressedThisFrame) Toggle("Chop_Tree_RT");
        else if (kb.f6Key.wasPressedThisFrame) Toggle("Dig");
        else if (kb.f7Key.wasPressedThisFrame) Toggle("Hoe");
        else if (kb.f8Key.wasPressedThisFrame) Toggle("Farm_PlantSeed_RT");
        else if (kb.f9Key.wasPressedThisFrame) Toggle("Pet");
        else if (kb.f10Key.wasPressedThisFrame) Toggle("Fixing_Kneeling_RT");
        else if (kb.f11Key.wasPressedThisFrame) Toggle("Sleeping_RT");
        else if (kb.f12Key.wasPressedThisFrame)
        {
            _drag = !_drag;
            if (_drag) _clips.PlayUpperBody("Drag", "Spine");
            else _clips.StopUpperBody();
        }
        else if (kb.insertKey.wasPressedThisFrame && _ped != null)
        {
            _ped.Carrying = !_ped.Carrying;
        }
    }

    private void Toggle(string clip)
    {
        if (_clips.ActionActive && _clips.CurrentAction == clip)
        {
            _clips.EndAction();
            return;
        }
        if (!_clips.BeginAction(clip))
            Debug.LogWarning($"[WorkAnimTester] clip '{clip}' not found. Available: {string.Join(", ", _clips.AvailableClips)}");
    }
}
