using System;
using UnityEngine;

/// <summary>
/// The fruit-picking gesture, driven by code on top of whatever the ped is already playing: the LEFT arm reaches for the fruit, closes on it (it comes
/// off the plant), then bends in toward the RIGHT hand, which holds the basket, and drops it in (the item reaches the toolbar). It is a two-bone IK on
/// LeftArm / LeftForeArm aiming at a moving target, blended in and out over the playing animation in LateUpdate, so it needs no authored clip.
///
///   Trees: the hand reaches UP toward one fruit, once.
///   Bushes: the player KNEELS (a full-body clip) and stays down while the arm goes STRAIGHT OUT toward the berries, several quick reach-grab-basket
///   cycles in a row that together pick the whole bush; then the player stands.
///
/// Moving cancels it (PedController.IsMoving): a berry already in the hand is dropped into the basket, the rest stay on the plant.
/// ForestTrees / PlantedGrowth / BerryBushes start it.
/// </summary>
public sealed class FruitPickAnimator : MonoBehaviour
{
    // seconds into ONE reach-grab-basket cycle (at speed 1)
    private const float Reach = 0.35f, Grab = 0.5f, Carry = 0.9f, Drop = 1.05f, CycleLen = 1.2f, Tail = 0.25f;
    private const float KneelLead = 0.45f, KneelTail = 0.4f;   // real seconds to get down before the first reach, and to stand up after the last drop

    private static FruitPickAnimator _active;
    public static bool Busy => _active != null && _active._running;

    private Transform _arm, _fore, _hand, _rightHand;
    private PedController _ped;
    private bool _running;
    private float _t;                 // animation seconds (real seconds x speed); negative while the player kneels down
    private float _speed = 1f;
    private int _cycles = 1;
    private int _nextGrab, _nextDrop;
    private Vector3[] _fruitPos;
    private Color _fruitColor;
    private Action<int> _onGrab, _onDrop;
    private GameObject _fruitBall;
    private bool _kneel, _stood;
    private string _kneelClip;
    private float _armLength;
    private Vector3 _handAtStart;

    /// <summary>One reach at one fruit (trees). False if this ped cannot do it (the caller then picks at once).</summary>
    public static bool TryBegin(Component ped, Vector3 fruitPos, Color fruitColor, Action onGrab, Action onDrop, bool kneel = false)
    {
        return TryBeginSequence(ped, new[] { fruitPos }, fruitColor, i => onGrab?.Invoke(), i => onDrop?.Invoke(), kneel, 1f);
    }

    /// <summary>
    /// One reach-grab-basket cycle per entry of <paramref name="fruitPositions"/>, back to back. kneel = low bushes: kneel once, arm straight out.
    /// onGrab(i) is when the fruit of cycle i comes off the plant, onDrop(i) when it lands in the basket. speed &gt; 1 is quicker.
    /// </summary>
    public static bool TryBeginSequence(Component ped, Vector3[] fruitPositions, Color fruitColor, Action<int> onGrab, Action<int> onDrop, bool kneel, float speed)
    {
        if (ped == null || Busy || fruitPositions == null || fruitPositions.Length == 0) return false;
        var anim = ped.GetComponent<FruitPickAnimator>();
        if (anim == null) anim = ped.gameObject.AddComponent<FruitPickAnimator>();
        if (!anim.FindBones()) return false;
        anim.Begin(fruitPositions, fruitColor, onGrab, onDrop, kneel, Mathf.Max(0.5f, speed));
        return true;
    }

    private bool FindBones()
    {
        if (_arm != null && _fore != null && _hand != null && _rightHand != null) return true;
        foreach (Transform t in GetComponentsInChildren<Transform>(true))
        {
            switch (t.name)
            {
                case "LeftArm": _arm = t; break;
                case "LeftForeArm": _fore = t; break;
                case "LeftHand": _hand = t; break;
                case "RightHand": _rightHand = t; break;
            }
        }
        return _arm != null && _fore != null && _hand != null && _rightHand != null;
    }

    private void Begin(Vector3[] fruitPositions, Color fruitColor, Action<int> onGrab, Action<int> onDrop, bool kneel, float speed)
    {
        _fruitPos = fruitPositions;
        _cycles = fruitPositions.Length;
        _fruitColor = fruitColor;
        _onGrab = onGrab;
        _onDrop = onDrop;
        _nextGrab = _nextDrop = 0;
        _speed = speed;
        _stood = false;
        _t = 0f;
        _kneel = false;
        _ped = GetComponent<PedController>();
        _armLength = Vector3.Distance(_arm.position, _fore.position) + Vector3.Distance(_fore.position, _hand.position);
        _handAtStart = _hand.position;

        if (kneel)
        {
            var clips = GetComponentInChildren<Homesteader.Animation.GlbClipPlayer>();
            _kneelClip = clips != null ? clips.FirstAvailable("Fixing_Kneeling_RT", "Farm_PlantSeed_RT") : null;
            Vector3 flat = fruitPositions[0] - transform.position;
            flat.y = 0f;
            Vector3 facing = flat.sqrMagnitude > 1e-4f ? flat.normalized : transform.forward;
            if (_ped != null && _kneelClip != null && _ped.BeginWork(_kneelClip, transform.position + facing))   // faces the bush and kneels
            {
                _kneel = true;
                _t = -KneelLead * _speed;   // the arm waits until the player is down
            }
        }
        _active = this;
        _running = true;
    }

    private void OnDisable() { Cleanup(); }

    /// <summary>Stops at once, with no callbacks (editor tests).</summary>
    public void Cancel() { Cleanup(); }

    /// <summary>The player moved: a berry already in the hand goes into the basket, the rest of the plant is left as it is.</summary>
    private void Interrupt()
    {
        if (_nextDrop < _nextGrab) { _onDrop?.Invoke(_nextDrop); _nextDrop = _nextGrab; }
        Cleanup();
    }

    private void Cleanup()
    {
        _running = false;
        if (_fruitBall != null) Destroy(_fruitBall);
        if (_kneel && !_stood && _ped != null && _kneelClip != null) _ped.EndWork(_kneelClip);
        _kneel = false;
        if (_active == this) _active = null;
    }

    private static float Ease(float x) { x = Mathf.Clamp01(x); return x * x * (3f - 2f * x); }

    /// <summary>Where the hand goes for the fruit of cycle c: up toward it (trees) or straight out, level with the shoulder (a kneeling bush pick).</summary>
    private Vector3 ReachPoint(int c)
    {
        Vector3 fruit = _fruitPos[Mathf.Clamp(c, 0, _fruitPos.Length - 1)];
        if (_kneel)
        {
            Vector3 flat = fruit - transform.position;
            flat.y = 0f;
            Vector3 outDir = flat.sqrMagnitude > 1e-4f ? flat.normalized : transform.forward;
            return _arm.position + outDir * (_armLength * 0.97f) + Vector3.down * 0.05f;
        }
        // The hand cannot reach a fruit in the crown: it reaches as far toward it as the arm goes (the fruit then comes to the hand).
        Vector3 dir = fruit - _arm.position;
        float d = dir.magnitude;
        if (d < 0.001f) dir = transform.forward + Vector3.up; else dir /= d;
        if (dir.y < 0.25f) { dir.y = 0.25f; dir.Normalize(); }   // up and ahead, not straight behind or down
        return _arm.position + dir * Mathf.Min(d, _armLength * 0.97f);
    }

    private void LateUpdate() { Tick(Time.deltaTime); }

    /// <summary>Advances the gesture by dt seconds (LateUpdate calls this each frame; it is public so an editor test can step it).</summary>
    public void Tick(float dt)
    {
        if (!_running) return;
        if (_ped != null && _ped.IsMoving) { Interrupt(); return; }   // moving cancels it
        _t += dt * _speed;

        float end = _cycles * CycleLen + Tail;
        // fruit coming off the plant / landing in the basket, in order (a long frame may pass several)
        while (_nextGrab < _cycles && _t >= _nextGrab * CycleLen + Grab)
        {
            _onGrab?.Invoke(_nextGrab);
            if (_fruitBall != null) Destroy(_fruitBall);
            _fruitBall = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            Destroy(_fruitBall.GetComponent<Collider>());
            _fruitBall.transform.localScale = Vector3.one * 0.11f;
            var r = _fruitBall.GetComponent<Renderer>();
            r.material.color = _fruitColor;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _nextGrab++;
        }
        while (_nextDrop < _nextGrab && _t >= _nextDrop * CycleLen + Drop)
        {
            if (_fruitBall != null) Destroy(_fruitBall);
            _onDrop?.Invoke(_nextDrop);                              // it lands in the basket: the item reaches the toolbar
            _nextDrop++;
        }

        // Kneeling: stand up after the last berry, then let go a moment later.
        if (_kneel && !_stood && _t >= _cycles * CycleLen) { _stood = true; if (_ped != null && _kneelClip != null) _ped.EndWork(_kneelClip); }
        if (_t >= end + (_kneel ? KneelTail * _speed : 0f)) { Cleanup(); return; }

        // How strongly the gesture overrides the animation: in over the first 0.2 s, out over the last 0.25 s.
        float w = Ease(_t / (0.2f * _speed)) * (1f - Ease((_t - (end - Tail)) / Tail));
        if (_t < 0f) return;   // still kneeling down

        int c = Mathf.Min(_cycles - 1, Mathf.FloorToInt(_t / CycleLen));
        float lt = Mathf.Min(_t - c * CycleLen, CycleLen);
        Vector3 basket = _rightHand.position + Vector3.up * 0.07f;
        Vector3 reach = ReachPoint(c);
        Vector3 start = c == 0 ? _hand.position : basket;
        Vector3 target;
        if (lt < Reach) target = Vector3.Lerp(start, reach, Ease(lt / Reach));          // up (or straight out) toward the fruit
        else if (lt < Carry)
        {
            // close on it, pull it back a little, then bend the arm in toward the right hand
            float a = Ease((lt - Grab) / (Carry - Grab));
            Vector3 pulled = reach + (_kneel ? -(reach - _arm.position).normalized * 0.10f : Vector3.down * 0.12f) * Ease((lt - Reach) / (Grab - Reach));
            target = Vector3.Lerp(pulled, basket, a);
        }
        else target = basket;                                                                // over the basket, drop it

        SolveLeftArm(target, w);

        if (_fruitBall != null) _fruitBall.transform.position = _hand.position + (_hand.position - _fore.position).normalized * 0.06f;
    }

    /// <summary>Two-bone IK: swings LeftArm and LeftForeArm so the hand reaches the target, blended by weight over the animated pose.</summary>
    private void SolveLeftArm(Vector3 target, float weight)
    {
        Quaternion armLocal0 = _arm.localRotation, foreLocal0 = _fore.localRotation;
        Vector3 s = _arm.position, e = _fore.position, h = _hand.position;
        float a = (e - s).magnitude, b = (h - e).magnitude;
        if (a < 1e-4f || b < 1e-4f) return;

        Vector3 toT = target - s;
        float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(a - b) + 0.01f, a + b - 0.01f);
        Vector3 dir = toT.sqrMagnitude > 1e-8f ? toT.normalized : transform.forward;
        // The elbow bends out and down (away from the body), never through it.
        Vector3 hint = -transform.right * 0.7f + Vector3.down * 0.6f + transform.forward * -0.2f;
        Vector3 pole = hint - dir * Vector3.Dot(hint, dir);
        pole = pole.sqrMagnitude > 1e-6f ? pole.normalized : Vector3.down;
        float x = (a * a + d * d - b * b) / (2f * d);
        float height = Mathf.Sqrt(Mathf.Max(a * a - x * x, 0f));
        Vector3 newElbow = s + dir * x + pole * height;

        _arm.rotation = Quaternion.FromToRotation((e - s).normalized, (newElbow - s).normalized) * _arm.rotation;
        Vector3 forearmNow = _fore.position;
        Vector3 wrist = _hand.position;
        _fore.rotation = Quaternion.FromToRotation((wrist - forearmNow).normalized, (s + dir * d - forearmNow).normalized) * _fore.rotation;

        // blend over the animated pose
        _arm.localRotation = Quaternion.Slerp(armLocal0, _arm.localRotation, weight);
        _fore.localRotation = Quaternion.Slerp(foreLocal0, _fore.localRotation, weight);
    }
}
