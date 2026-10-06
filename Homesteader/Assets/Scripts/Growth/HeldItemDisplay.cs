using UnityEngine;
using Homesteader.Animation;
using Homesteader.UI;

namespace Homesteader.Growth
{
    /// <summary>
    /// Shows the tool in the active toolbar slot at the player's right hand: its icon on a small camera-facing quad that
    /// rides the hand bone, so it follows every animation (walk, chop ...). Only tools are shown.
    /// </summary>
    public sealed class HeldItemDisplay : MonoBehaviour
    {
        private const float IconSize = 0.4f;                                         // metres on screen
        private const float TurnOutDegrees = 45f;   // swings the head out, away from the body (negative turns it in)
        private const float PalmOffset = 0.09f;   // metres from the wrist bone, continuing along the forearm (the palm)
        private const float InwardOffset = 0.04f;   // metres from the outside of the hand toward the body (into the palm)
        private static readonly Vector2 GripShift = new Vector2(0.09f, 0.09f);       // metres: how far the icon centre sits up and toward the head from the hand
        // Things carried by a handle on top (the fruit basket) hang below the hand instead of being gripped at the foot of the icon.
        private const string BasketId = "tool_fruit_basket";
        private static readonly Vector2 BasketShift = new Vector2(0f, -0.15f);
        private const float BasketIconSize = 0.34f;
        private Vector2 _shift = new Vector2(0.09f, 0.09f);

        private Transform _quad;
        private Transform _hand;
        private Transform _body;
        private Quaternion _gripRotation;   // slab orientation relative to the hand bone
        private string _item;
        private float _nextCheck;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<HeldItemDisplay>() != null) return;
            var go = new GameObject("HeldItemDisplay");
            DontDestroyOnLoad(go);
            go.AddComponent<HeldItemDisplay>();
        }

        private static string ActiveToolId()
        {
            HudState s = HudState.Active;
            if (s == null || s.SelectedSlot < 0 || s.SelectedSlot >= s.Toolbar.Count) return null;
            ToolbarSlotData slot = s.Toolbar[s.SelectedSlot];
            if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId)) return null;
            return slot.IconId.StartsWith("tool_") ? slot.IconId : null;
        }

        private void Update()
        {
            if (Time.unscaledTime < _nextCheck) return;
            _nextCheck = Time.unscaledTime + 0.1f;

            string want = ActiveToolId();
            if (want == _item && (_quad != null || want == null)) return;

            if (_quad != null) Destroy(_quad.gameObject);
            _quad = null;
            _hand = null;
            _item = null;
            if (want == null) return;

            var player = PedController.Current;
            var clips = player != null ? player.GetComponentInChildren<GlbClipPlayer>() : null;
            Transform hand = clips != null ? clips.FindBone("RightHand") : null;
            if (hand == null) return;                                   // character still loading: try again next tick

            Texture2D icon = PhoneController.GetItemIcon(want + ".png", want);
            _item = want;
            if (icon == null) return;

            bool basket = want == BasketId;
            _shift = basket ? BasketShift : GripShift;
            GameObject go = SpriteSlab.Create(want, basket ? BasketIconSize : IconSize);
            if (go == null) return;
            go.name = "Held_" + want;
            _quad = go.transform;      // not parented to the bone (its scale is 0.01): it is moved onto the hand every frame
            _hand = hand;
            // Start from "flat face out to the character's right side" (the ped transform faces backwards, modelRotationOffset 180) and lock
            // that pose to the hand bone as it is now (arm hanging), so the tool follows the arm from here on.
            Quaternion start = Quaternion.AngleAxis(basket ? 0f : TurnOutDegrees, Vector3.up) * Quaternion.LookRotation(-player.transform.right, Vector3.up);
            _gripRotation = Quaternion.Inverse(hand.rotation) * start;
            _body = player.transform;
            Place();
        }

        private void LateUpdate()
        {
            if (_quad != null) Place();
        }

        /// <summary>Puts the slab in the palm. Its orientation is fixed relative to the hand bone, so it tilts and swings with the arm.</summary>
        private void Place()
        {
            if (_hand == null) { Destroy(_quad.gameObject); _quad = null; return; }
            _quad.rotation = _hand.rotation * _gripRotation;
            // The icon draws the head top-right and the handle bottom-left: the handle end sits in the palm, which is a little
            // beyond the wrist bone along the fingers.
            // The hand bone has no finger bones and its own axes do not run along the fingers: the fingers continue the forearm's line.
            Vector3 along = _hand.parent != null ? (_hand.position - _hand.parent.position).normalized : Vector3.down;
            Vector3 inward = _body != null ? _body.position - _hand.position : Vector3.zero;
            inward.y = 0f;
            Vector3 palm = _hand.position + along * PalmOffset + inward.normalized * InwardOffset;
            _quad.position = palm + _quad.right * _shift.x + _quad.up * _shift.y;
        }
    }
}
