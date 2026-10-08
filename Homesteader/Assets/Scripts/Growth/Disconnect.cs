using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The safety disconnect (wire_role disconnect, docs/WIRING.md): a switch wired into a run, AC or DC. On (the handle up) it carries the current like a bus bar;
    /// off (the handle down) the run is cut there: what is past it gets nothing (<see cref="WireNetwork"/> treats its links as cut). A right click throws it
    /// (not with wire cutters or the pipe wrench in hand: they wire). The state is saved with the mounted object.
    /// </summary>
    public sealed class Disconnect : MonoBehaviour
    {
        private const float Reach = 4f;
        private const float OffAngle = 150f;   // the handle swings down through the front

        private Transform _handle;
        private Quaternion _up;
        private float _angle;

        /// <summary>A right click; true when it threw a disconnect.</summary>
        public static bool TryRightClick(Camera cam, Vector2 pointer, Transform player)
        {
            if (WireTool.JoinToolHeld()) return false;
            WireNode n = WireTool.NodeUnderCursor(cam, pointer);
            if (n != null && n.Tripped)
            {
                if (player != null && Vector3.Distance(player.position, n.transform.position) > Reach)
                {
                    ToastNotificationSystem.ShowInfo("Too far", "Move closer to reset it.");
                    return true;
                }
                WireNetwork.Reset(n);   // a tripped breaker, inverter, controller, battery, bus bar or generator comes back (warm)
                return true;
            }
            if (n == null || n.Role != WireRole.Disconnect) return false;
            if (player != null && Vector3.Distance(player.position, n.transform.position) > Reach)
            {
                ToastNotificationSystem.ShowInfo("Too far", "Move closer to the disconnect.");
                return true;
            }
            n.SwitchOff = !n.SwitchOff;
            Show(n);
            WireNetwork.Redraw();
            return true;
        }

        /// <summary>Puts the handle where the switch is (a throw, or a loaded game).</summary>
        public static void Show(WireNode n)
        {
            if (n == null) return;
            Disconnect d = n.GetComponent<Disconnect>();
            if (d == null) d = n.gameObject.AddComponent<Disconnect>();
            d.enabled = true;
        }

        private void Update()
        {
            WireNode n = GetComponent<WireNode>();
            if (n == null) return;
            if (_handle == null)
            {
                foreach (Transform t in GetComponentsInChildren<Transform>(true)) if (t.name == "Handle") { _handle = t; break; }
                if (_handle == null) return;   // the model may still be loading
                _up = _handle.localRotation;
                _angle = n.SwitchOff ? OffAngle : 0f;
            }
            float want = n.SwitchOff ? OffAngle : 0f;
            _angle = Mathf.MoveTowards(_angle, want, 600f * Time.unscaledDeltaTime);
            _handle.localRotation = _up * Quaternion.Euler(_angle, 0f, 0f);
            if (Mathf.Approximately(_angle, want)) enabled = false;
        }
    }
}
