using UnityEngine;

/// <summary>
/// Kitchen gestures driven by code over whatever the ped is already playing (the same way FruitPickAnimator does the picking): stirring at the stove, cranking the mill or the press,
/// pressing at the juicer and blender, chopping at the counter, and eating and drinking. A two-bone IK on each arm aims the hand at a moving target in front of the body; it is blended in
/// and out in LateUpdate, so no authored clip is needed. The facing, the shoulder line and the mouth come from the bones, so the model's rotation offset does not matter.
/// KitchenCook starts the cooking ones (a gesture per appliance), Consumption the eating ones. A movement key stops it (PedController.ManualInput).
/// </summary>
public sealed class KitchenAnimator : MonoBehaviour
{
    public enum Gesture { Stir, Crank, Press, Chop, Eat, Drink }

    private Transform _lArm, _lFore, _lHand, _rArm, _rFore, _rHand, _head;
    private PedController _ped;
    private bool _running;
    private Gesture _gesture;
    private float _t, _length;

    /// <summary>Plays a gesture for <paramref name="seconds"/> seconds. False when this ped's skeleton cannot do it (the caller carries on without).</summary>
    public static bool Play(PedController ped, Gesture gesture, float seconds)
    {
        if (ped == null || seconds <= 0f) return false;
        var anim = ped.GetComponent<KitchenAnimator>();
        if (anim == null) anim = ped.gameObject.AddComponent<KitchenAnimator>();
        if (!anim.FindBones()) return false;
        anim._ped = ped;
        anim._gesture = gesture;
        anim._length = seconds;
        anim._t = 0f;
        anim._running = true;
        return true;
    }

    public static void Stop(PedController ped)
    {
        var anim = ped != null ? ped.GetComponent<KitchenAnimator>() : null;
        if (anim != null) anim._running = false;
    }

    public static bool Busy(PedController ped)
    {
        var anim = ped != null ? ped.GetComponent<KitchenAnimator>() : null;
        return anim != null && anim._running;
    }

    private bool FindBones()
    {
        if (_lArm != null && _lFore != null && _lHand != null && _rArm != null && _rFore != null && _rHand != null) return true;
        foreach (Transform t in GetComponentsInChildren<Transform>(true))
        {
            switch (t.name)
            {
                case "LeftArm": _lArm = t; break;
                case "LeftForeArm": _lFore = t; break;
                case "LeftHand": _lHand = t; break;
                case "RightArm": _rArm = t; break;
                case "RightForeArm": _rFore = t; break;
                case "RightHand": _rHand = t; break;
                case "Head": _head = t; break;
            }
        }
        return _lArm != null && _lFore != null && _lHand != null && _rArm != null && _rFore != null && _rHand != null;
    }

    private static float Ease(float x) { x = Mathf.Clamp01(x); return x * x * (3f - 2f * x); }

    private void LateUpdate()
    {
        if (!_running) return;
        if (_ped != null && _ped.ManualInput) { _running = false; return; }
        _t += Time.deltaTime;
        if (_t >= _length) { _running = false; return; }
        const float Ramp = 0.25f;
        float w = Ease(_t / Ramp) * Ease((_length - _t) / Ramp);

        // the body frame from the shoulders: up, forward (what the character faces) and right
        Vector3 up = Vector3.up;
        Vector3 across = _rArm.position - _lArm.position;
        across.y = 0f;
        if (across.sqrMagnitude < 1e-6f) return;
        across.Normalize();
        Vector3 fwd = Vector3.Cross(across, up).normalized;
        Vector3 right = across;
        Vector3 chest = (_rArm.position + _lArm.position) * 0.5f;
        Vector3 mouth = (_head != null ? _head.position : chest + up * 0.25f) + fwd * 0.10f + Vector3.down * 0.07f;

        Vector3? r = null, l = null;
        float a;
        switch (_gesture)
        {
            case Gesture.Stir:
                a = _t * Mathf.PI * 2f * 1.3f;
                r = chest + fwd * 0.42f + Vector3.down * 0.42f + right * (Mathf.Cos(a) * 0.07f) + fwd * (Mathf.Sin(a) * 0.07f);
                break;
            case Gesture.Crank:
                a = _t * Mathf.PI * 2f * 1.1f;
                r = chest + fwd * 0.40f + right * 0.12f + Vector3.down * 0.28f + up * (Mathf.Sin(a) * 0.10f) + fwd * (Mathf.Cos(a) * 0.10f);
                break;
            case Gesture.Press:
                a = _t * Mathf.PI * 2f * 0.9f;
                float dip = -0.10f * (0.5f + 0.5f * Mathf.Sin(a));
                r = chest + fwd * 0.38f + right * 0.14f + Vector3.down * 0.22f + up * dip;
                l = chest + fwd * 0.38f - right * 0.14f + Vector3.down * 0.22f + up * dip;
                break;
            case Gesture.Chop:
                a = _t * Mathf.PI * 2f * 2.6f;
                r = chest + fwd * 0.40f + right * 0.10f + Vector3.down * 0.34f + up * (0.12f * Mathf.Abs(Mathf.Sin(a)));
                l = chest + fwd * 0.40f - right * 0.08f + Vector3.down * 0.36f;
                break;
            case Gesture.Eat:
            {
                Vector3 plate = chest + fwd * 0.34f + Vector3.down * 0.46f;
                float c = (_t % 1.5f) / 1.5f;   // one bite: down to the plate, up to the mouth, a moment there, back
                r = c < 0.3f ? Vector3.Lerp(plate, plate + up * 0.02f, c / 0.3f) : c < 0.6f ? Vector3.Lerp(plate, mouth, Ease((c - 0.3f) / 0.3f)) : c < 0.75f ? mouth : Vector3.Lerp(mouth, plate, Ease((c - 0.75f) / 0.25f));
                break;
            }
            case Gesture.Drink:
            {
                Vector3 rest = chest + fwd * 0.30f + Vector3.down * 0.40f;
                float c = _t / _length;
                r = c < 0.3f ? Vector3.Lerp(rest, mouth, Ease(c / 0.3f)) : c < 0.7f ? mouth : Vector3.Lerp(mouth, rest, Ease((c - 0.7f) / 0.3f));
                break;
            }
        }
        if (r.HasValue) SolveArm(_rArm, _rFore, _rHand, _lArm, r.Value, w);
        if (l.HasValue) SolveArm(_lArm, _lFore, _lHand, _rArm, l.Value, w);
    }

    /// <summary>Two-bone IK: swings the arm and forearm so the hand reaches the target, blended by weight over the animated pose. The elbow bends out (away from the other shoulder) and down.</summary>
    private static void SolveArm(Transform arm, Transform fore, Transform hand, Transform otherArm, Vector3 target, float weight)
    {
        Quaternion armLocal0 = arm.localRotation, foreLocal0 = fore.localRotation;
        Vector3 s = arm.position, e = fore.position, h = hand.position;
        float a = (e - s).magnitude, b = (h - e).magnitude;
        if (a < 1e-4f || b < 1e-4f) return;

        Vector3 toT = target - s;
        float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(a - b) + 0.01f, a + b - 0.01f);
        Vector3 dir = toT.sqrMagnitude > 1e-8f ? toT.normalized : Vector3.down;
        Vector3 outward = s - otherArm.position;
        outward.y = 0f;
        Vector3 hint = outward.normalized * 0.7f + Vector3.down * 0.6f;
        Vector3 pole = hint - dir * Vector3.Dot(hint, dir);
        pole = pole.sqrMagnitude > 1e-6f ? pole.normalized : Vector3.down;
        float x = (a * a + d * d - b * b) / (2f * d);
        float height = Mathf.Sqrt(Mathf.Max(a * a - x * x, 0f));
        Vector3 newElbow = s + dir * x + pole * height;

        arm.rotation = Quaternion.FromToRotation((e - s).normalized, (newElbow - s).normalized) * arm.rotation;
        Vector3 foreNow = fore.position;
        Vector3 wrist = hand.position;
        fore.rotation = Quaternion.FromToRotation((wrist - foreNow).normalized, (s + dir * d - foreNow).normalized) * fore.rotation;

        arm.localRotation = Quaternion.Slerp(armLocal0, arm.localRotation, weight);
        fore.localRotation = Quaternion.Slerp(foreLocal0, fore.localRotation, weight);
    }
}
