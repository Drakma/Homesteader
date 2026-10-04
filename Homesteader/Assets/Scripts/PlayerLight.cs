using UnityEngine;
using UnityEngine.InputSystem;
using Homesteader.Animation;
using Homesteader.UI;

/// <summary>
/// Player light on F: Off -> Flashlight (forward spot beam) -> Lantern (warm, flickering point
/// light) -> Off. Ignored while a window or text field owns the keyboard.
/// The right arm holds the light (upper-body clips Hold_Flashlight / Hold_Lantern layered over
/// walk / run / idle), the lights follow the right-hand bone, and a small prop is drawn in the hand.
/// Add to the player object.
/// </summary>
public sealed class PlayerLight : MonoBehaviour
{
    public enum Mode { Off, Flashlight, Lantern }

    [Header("Flashlight")]
    public Color flashlightColor = new Color(1f, 0.97f, 0.88f);
    public float flashlightIntensity = 6f;
    public float flashlightRange = 20f;
    public float flashlightAngle = 55f;
    [Tooltip("Degrees the beam points down from horizontal.")]
    public float flashlightPitch = 10f;

    [Header("Lantern")]
    public Color lanternColor = new Color(1f, 0.66f, 0.32f);
    public float lanternIntensity = 3.5f;
    public float lanternRange = 11f;
    [Tooltip("How strongly the lantern flickers (0 = steady).")]
    [Range(0f, 1f)] public float flickerAmount = 0.6f;

    [Header("Hold")]
    public string handBone = "RightHand";
    public string flashlightClip = "Hold_Flashlight";
    public string lanternClip = "Hold_Lantern";
    [Tooltip("Fallback positions (player local) used until the hand bone is found.")]
    public Vector3 fallbackFlashlightPos = new Vector3(0.15f, 1.2f, 0.4f);
    public Vector3 fallbackLanternPos = new Vector3(0.3f, 0.9f, 0.3f);

    public Mode CurrentMode { get; private set; } = Mode.Off;

    private Light _spot;
    private Light _lantern;
    private GameObject _flashlightProp;
    private GameObject _lanternProp;
    private GlbClipPlayer _clips;
    private Transform _hand;
    private float _seed;

    private void Awake()
    {
        _seed = Random.value * 100f;

        _spot = MakeLight("Flashlight", LightType.Spot, flashlightColor, flashlightIntensity, flashlightRange);
        _spot.spotAngle = flashlightAngle;
        _spot.innerSpotAngle = flashlightAngle * 0.55f;

        _lantern = MakeLight("Lantern", LightType.Point, lanternColor, lanternIntensity, lanternRange);

        _flashlightProp = MakeProp("FlashlightProp", PrimitiveType.Cylinder,
            new Vector3(0.05f, 0.09f, 0.05f), new Color(0.15f, 0.15f, 0.17f));
        _lanternProp = MakeProp("LanternProp", PrimitiveType.Cylinder,
            new Vector3(0.10f, 0.075f, 0.10f), new Color(1f, 0.78f, 0.4f));
    }

    private Light MakeLight(string name, LightType type, Color color, float intensity, float range)
    {
        var go = new GameObject(name);
        go.transform.SetParent(transform, false);
        var l = go.AddComponent<Light>();
        l.type = type;
        l.color = color;
        l.intensity = intensity;
        l.range = range;
        // shadows on: the cabin's walls stop the flashlight and the lantern (the window glass casts none, so light still gets through it)
        l.shadows = type == LightType.Spot ? LightShadows.Soft : LightShadows.None;   // the flashlight (a spot) casts shadows; a point lantern would draw the scene six times for them
        l.shadowStrength = 1f;
        l.enabled = false;
        return l;
    }

    private GameObject MakeProp(string name, PrimitiveType type, Vector3 scale, Color color)
    {
        var go = GameObject.CreatePrimitive(type);
        go.name = name;
        var col = go.GetComponent<Collider>();
        if (col != null) Destroy(col);
        go.transform.SetParent(transform, false);
        go.transform.localScale = scale;

        var shader = Shader.Find("Universal Render Pipeline/Unlit");
        if (shader == null) shader = Shader.Find("Sprites/Default");
        var mr = go.GetComponent<MeshRenderer>();
        var mat = new Material(shader);
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", color);
        mat.color = color;
        mr.sharedMaterial = mat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        go.SetActive(false);
        return go;
    }

    private void Update()
    {
        if (PressedF() && !HudBindings.KeyboardCaptured)
        {
            SetMode(CurrentMode == Mode.Off ? Mode.Flashlight
                  : CurrentMode == Mode.Flashlight ? Mode.Lantern
                  : Mode.Off);
        }

        if (CurrentMode == Mode.Lantern) Flicker();
    }

    private void LateUpdate()
    {
        if (CurrentMode == Mode.Off) return;
        FollowHand();
    }

    private static bool PressedF()
    {
        var kb = Keyboard.current;
        if (kb != null) return Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.PlayerLight);
        return Input.GetKeyDown(KeyCode.F);
    }

    public void SetMode(Mode mode)
    {
        CurrentMode = mode;
        _spot.enabled = mode == Mode.Flashlight;
        _lantern.enabled = mode == Mode.Lantern;
        _flashlightProp.SetActive(mode == Mode.Flashlight);
        _lanternProp.SetActive(mode == Mode.Lantern);

        if (_clips == null) _clips = GetComponentInChildren<GlbClipPlayer>();
        if (_clips != null)
        {
            if (mode == Mode.Flashlight) _clips.PlayUpperBody(flashlightClip, "RightArm");
            else if (mode == Mode.Lantern) _clips.PlayUpperBody(lanternClip, "RightArm");
            else _clips.StopUpperBody();
        }

        if (mode == Mode.Lantern) Flicker();
        if (mode != Mode.Off) FollowHand();
    }

    // Lights and props track the hand bone's position; their orientation follows the character heading,
    // not the (animated) hand rotation, so the beam always points where the player is facing.
    private void FollowHand()
    {
        if (_hand == null)
        {
            if (_clips == null) _clips = GetComponentInChildren<GlbClipPlayer>();
            if (_clips != null) _hand = _clips.FindBone(handBone);
        }

        Vector3 fwd = transform.forward;
        fwd.y = 0f;
        if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward;
        fwd.Normalize();
        Quaternion heading = Quaternion.LookRotation(fwd, Vector3.up);

        if (CurrentMode == Mode.Flashlight)
        {
            Vector3 pos = _hand != null ? _hand.position + fwd * 0.05f : transform.TransformPoint(fallbackFlashlightPos);
            _spot.transform.SetPositionAndRotation(pos, heading * Quaternion.Euler(flashlightPitch, 0f, 0f));
            // Cylinder axis is Y: lay it along the beam.
            _flashlightProp.transform.SetPositionAndRotation(pos - fwd * 0.02f, heading * Quaternion.Euler(90f, 0f, 0f));
        }
        else if (CurrentMode == Mode.Lantern)
        {
            Vector3 pos = _hand != null ? _hand.position + Vector3.down * 0.16f + fwd * 0.04f : transform.TransformPoint(fallbackLanternPos);
            _lantern.transform.position = pos;
            _lanternProp.transform.SetPositionAndRotation(pos, Quaternion.identity);
        }
    }

    // Layered noise: a slow drift, a fast shimmer, and the occasional deeper dip.
    private void Flicker()
    {
        float t = Time.time;
        float slow = Mathf.PerlinNoise(_seed, t * 1.3f) - 0.5f;
        float fast = Mathf.PerlinNoise(_seed + 17f, t * 11f) - 0.5f;
        float dip = Mathf.PerlinNoise(_seed + 41f, t * 0.7f);
        float dipAmount = dip > 0.82f ? (dip - 0.82f) * 3.0f : 0f;
        float f = 1f + flickerAmount * (slow * 0.5f + fast * 0.45f) - flickerAmount * dipAmount * 0.5f;
        _lantern.intensity = lanternIntensity * Mathf.Max(0.35f, f);
        _lantern.range = lanternRange * (0.96f + 0.08f * (fast + 0.5f));
    }
}
