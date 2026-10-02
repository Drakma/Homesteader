using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering.Universal;
using Homesteader.Generation;

public class IsometricLockedCamera : MonoBehaviour
{
    [Header("Tracking Target")]
    public Transform target;
    public float distance = 12f;
    public float height = 9f;
    public float pitchDegrees = 30f;
    public float yawDegrees = -45f;
    public float followSmoothing = 8f;

    [Header("Zoom Settings (Ctrl + ScrollWheel)")]
    public float zoomSpeed = 6f;
    // Zoom levels start at 3 and step by 1.0 up to a max of 15 (default).
    private const float minOrthoSize = 3f;
    private const float defaultMaxOrthoSize = 15f;
    private const float zoomStep = 1.0f;
    private static float maxOrthoSize = defaultMaxOrthoSize;

    [Header("Rotation Settings (Q / E 90° Orbit)")]
    public float yawRotateSpeed = 6f;
    private float targetYaw;
    private float orbitRadius;

    /// <summary>Fog density multiplier that cancels the camera being pulled back: 1 when the camera sits at its base orbit radius.</summary>
    public static float FogCompensation = 1f;

    [Header("Pan Settings (Right-Click Drag)")]
    public float panSpeed = 1.0f;
    public float recenterSpeed = 6.0f;
    private Vector3 _focalPoint;
    private Vector3 _lastTargetPos;
    private bool _isPanned = false;

    private Camera cam;
    private Transform _listenerAnchor;

    void Awake()
    {
        cam = GetComponent<Camera>();
        ApplyZoomSettings();
        if (cam != null)
        {
            cam.orthographicSize = SnapZoom(7f);
            cam.backgroundColor = Color.black;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.nearClipPlane = -50f;
            // Ensure Camera.main works — many systems rely on it
            if (cam.gameObject.tag != "MainCamera")
                cam.gameObject.tag = "MainCamera";

            // Without this the scene's Global Volume (color grading, etc.) never renders at all — the camera
            // silently skips the whole URP post-processing stack.
            var camData = cam.GetUniversalAdditionalCameraData();
            camData.renderPostProcessing = true;
        }

        // The scene's Main Camera (which holds the only AudioListener) is disabled, so without
        // this the game runs with zero active AudioListeners and all audio is silent.
        // The listener must NOT sit on this camera: the orthographic camera is pulled far back from the action, and the 3D
        // sounds (footsteps, chopping, animals) fall silent beyond 25 m. It lives on an anchor that follows the focal point.
        foreach (AudioListener existing in FindObjectsByType<AudioListener>())
            existing.enabled = false;
        var anchor = new GameObject("AudioListenerAnchor");
        anchor.transform.SetParent(transform.parent, false);
        _listenerAnchor = anchor.transform;
        anchor.AddComponent<AudioListener>();

        targetYaw = yawDegrees;
        orbitRadius = Mathf.Sqrt(distance * distance + height * height);
    }

    /// <summary>
    /// Reads the zoom max-level setting (3 to 50, default 15) from PlayerPrefs.
    /// Called on Awake and whenever the settings dialog closes.
    /// </summary>
    public void ApplyZoomSettings()
    {
        // Settings > General > Zoom Max Level (3 to 50). There is no separate lock any more.
        int level = PlayerPrefs.GetInt("ZoomMaxLevel", (int)defaultMaxOrthoSize);
        maxOrthoSize = Mathf.Clamp(level, (int)minOrthoSize, 50);

        // Clamp current zoom if we're already running and the new max is tighter
        if (cam != null && cam.orthographic && cam.orthographicSize > maxOrthoSize)
            cam.orthographicSize = maxOrthoSize;
    }

    // Snaps to the nearest level on the min + n * step grid and clamps to [min, max].
    private static float SnapZoom(float size)
    {
        float snapped = minOrthoSize + Mathf.Round((size - minOrthoSize) / zoomStep) * zoomStep;
        return Mathf.Clamp(snapped, minOrthoSize, maxOrthoSize);
    }

    void Start()
    {
        ResolveTarget();
        if (target != null)
        {
            _focalPoint = target.position;
            _lastTargetPos = target.position;
        }
    }

    private void ResolveTarget()
    {
        if (target == null)
        {
            var playerObj = GameObject.FindWithTag("Player");
            if (playerObj != null)
            {
                target = playerObj.transform;
            }
            else
            {
                var ped = FindAnyObjectByType<PedController>();
                if (ped != null)
                {
                    target = ped.transform;
                }
            }
        }
    }

    void Update()
    {
        if (target == null)
        {
            ResolveTarget();
            if (target != null)
            {
                _focalPoint = target.position;
                _lastTargetPos = target.position;
            }
        }

        // Q / E: 90-degree focal point orbit
        // Q: counter-clockwise (-90)
        // E: clockwise (+90)
        var kb = Keyboard.current;
        if (Homesteader.UI.HudBindings.KeyboardCaptured)
        {
            // A HUD window or text field owns the keyboard
        }
        else if (kb != null)
        {
            if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.CameraRotateLeft)) targetYaw -= 90f;
            if (Homesteader.Controls.KeyBindings.WasPressedThisFrame(Homesteader.Controls.BindAction.CameraRotateRight)) targetYaw += 90f;
        }
        else
        {
            if (Input.GetKeyDown(KeyCode.Q)) targetYaw -= 90f;
            if (Input.GetKeyDown(KeyCode.E)) targetYaw += 90f;
        }

        // Check if Ctrl is held down
        bool isCtrlHeld = false;
        if (kb != null)
        {
            isCtrlHeld = kb.leftCtrlKey.isPressed || kb.rightCtrlKey.isPressed;
        }
        else
        {
            isCtrlHeld = Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl);
        }

        var mouse = Mouse.current;
        float scroll = 0f;
        bool isRightClick = false;
        Vector2 mouseDelta = Vector2.zero;

        if (mouse != null)
        {
            scroll = mouse.scroll.ReadValue().y;
            isRightClick = mouse.rightButton.isPressed;
            mouseDelta = mouse.delta.ReadValue();
        }
        else
        {
            scroll = Input.mouseScrollDelta.y * 120f;
            isRightClick = Input.GetMouseButton(1);
            mouseDelta = new Vector2(Input.GetAxis("Mouse X") * 20f, Input.GetAxis("Mouse Y") * 20f);
        }

        // Ctrl + ScrollWheel: Zoom in / out, snapped to discrete steps
        if (isCtrlHeld && cam != null && cam.orthographic && Mathf.Abs(scroll) > 0.01f && !Homesteader.UI.MiniMap.PointerOver)
        {
            cam.orthographicSize = SnapZoom(cam.orthographicSize + Mathf.Sign(-scroll) * zoomStep);
        }

        // Right-Click + Drag: Pan across ground plane
        if (isRightClick && mouseDelta.sqrMagnitude > 0.01f)
        {
            Vector3 camRight = transform.right;
            camRight.y = 0f;
            camRight.Normalize();

            Vector3 camFwd = transform.forward;
            camFwd.y = 0f;
            camFwd.Normalize();

            float orthoScale = (cam != null && cam.orthographic) ? (cam.orthographicSize / 10f) : 1f;
            float factor = orthoScale * 0.02f * panSpeed;
            _focalPoint -= (camRight * mouseDelta.x + camFwd * mouseDelta.y) * factor;
            _isPanned = true;
            ClampFocalPoint();
        }

        // Check if player is moving to re-center viewport
        if (target != null)
        {
            bool playerMoving = false;
            var ped = target.GetComponent<PedController>();
            if (ped != null)
            {
                playerMoving = ped.IsMoving;
            }
            if (!playerMoving && Vector3.Distance(target.position, _lastTargetPos) > (0.1f * Time.deltaTime))
            {
                playerMoving = true;
            }
            _lastTargetPos = target.position;

            if (playerMoving)
            {
                // Smoothly re-center viewport on player when moving
                _focalPoint = Vector3.Lerp(_focalPoint, target.position, recenterSpeed * Time.unscaledDeltaTime);
                if (Vector3.Distance(_focalPoint, target.position) < 0.05f)
                {
                    _focalPoint = target.position;
                    _isPanned = false;
                }
            }
            else if (!_isPanned)
            {
                _focalPoint = target.position;
            }
        }
    }

    /// <summary>
    /// Clamps the focal point to the terrain bounds plus a 5m margin so the
    /// viewport can't pan past the playable area.
    /// </summary>
    private void ClampFocalPoint()
    {
        var gen = FindAnyObjectByType<HomesteaderTerrainGenerator>();
        if (gen == null) return;

        Vector3 origin = gen.transform.position;
        float sizeX = gen.terrainSizeX;
        float sizeZ = gen.terrainSizeZ;
        const float margin = 5f;

        float minX = origin.x - margin;
        float maxX = origin.x + sizeX + margin;
        float minZ = origin.z - margin;
        float maxZ = origin.z + sizeZ + margin;

        _focalPoint.x = Mathf.Clamp(_focalPoint.x, minX, maxX);
        _focalPoint.z = Mathf.Clamp(_focalPoint.z, minZ, maxZ);
    }

    void LateUpdate()
    {
        if (target == null && _focalPoint == Vector3.zero) return;

        yawDegrees = Mathf.LerpAngle(yawDegrees, targetYaw, yawRotateSpeed * Time.unscaledDeltaTime);

        // Locked isometric: pitch stays fixed, only yaw orbits (via Q/E snaps).
        Quaternion lookRot = Quaternion.Euler(pitchDegrees, yawDegrees, 0f);
        // Orthographic: distance changes nothing on screen, so sit far enough back that everything in view is in
        // FRONT of the camera. That lets the near plane stay positive, which keeps shadow cascades and fade sane
        // (a negative near plane skews them, darkening part of the screen).
        float camDistance = orbitRadius;
        if (cam != null && cam.orthographic)
            camDistance = orbitRadius + 2.0f * cam.orthographicSize + 5f;
        FogCompensation = Mathf.Clamp01(orbitRadius / Mathf.Max(camDistance, 0.01f));
        Vector3 offset = lookRot * new Vector3(0f, 0f, -camDistance);
        transform.position = _focalPoint + offset;

        transform.rotation = lookRot;
        if (_listenerAnchor != null) _listenerAnchor.SetPositionAndRotation(_focalPoint, lookRot);

        // Zoomed far out, the ground at the bottom of the screen is CLOSER to the camera than the near plane (the camera sits
        // orbitRadius from the focal point, and the bottom of the view reaches about 2 x zoom back along the ground), so it
        // was clipped away and showed the empty background. An orthographic camera may have a negative near plane, so pull it
        // back by exactly what the current zoom needs, and keep the far plane beyond the top of the screen.
        if (cam != null && cam.orthographic)
            {
                float reach = 2.2f * cam.orthographicSize;
                // The camera is pulled back (above) so the near plane can stay positive.
                cam.nearClipPlane = 0.3f;
                cam.farClipPlane = Mathf.Max(cam.farClipPlane, camDistance + reach + 100f);

                // Fit the shadow range to what is actually on screen. A needlessly long range spreads the shadow map
                // thin, and the edges shimmer as the camera pans. The view reaches about 1.8 x zoom either side of the focal point.
                var urp = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline as UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset;
                if (urp != null)
                {
                    float want = camDistance + 1.8f * cam.orthographicSize + 20f;
                    if (Mathf.Abs(urp.shadowDistance - want) > 2f) urp.shadowDistance = want;
                }
            }
    }
}
