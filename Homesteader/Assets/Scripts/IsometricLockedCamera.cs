using UnityEngine;
using UnityEngine.InputSystem;
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

    [Header("Pan Settings (Right-Click Drag)")]
    public float panSpeed = 1.0f;
    public float recenterSpeed = 6.0f;
    private Vector3 _focalPoint;
    private Vector3 _lastTargetPos;
    private bool _isPanned = false;

    private Camera cam;

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
        }
        targetYaw = yawDegrees;
        orbitRadius = Mathf.Sqrt(distance * distance + height * height);
    }

    /// <summary>
    /// Reads the zoom max-level setting from PlayerPrefs. If "Lock" is enabled,
    /// zoom is capped at the specified level; otherwise the default max (15) is used.
    /// Called on Awake and whenever the settings dialog closes.
    /// </summary>
    public void ApplyZoomSettings()
    {
        bool locked = PlayerPrefs.GetInt("ZoomLockEnabled", 0) == 1;
        if (locked)
        {
            int level = PlayerPrefs.GetInt("ZoomMaxLevel", 15);
            maxOrthoSize = Mathf.Clamp(level, (int)minOrthoSize, 100);
        }
        else
        {
            maxOrthoSize = defaultMaxOrthoSize;
        }

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
            if (kb.qKey.wasPressedThisFrame) targetYaw -= 90f;
            if (kb.eKey.wasPressedThisFrame) targetYaw += 90f;
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
        Vector3 offset = lookRot * new Vector3(0f, 0f, -orbitRadius);
        transform.position = _focalPoint + offset;

        transform.rotation = lookRot;

        // Zoomed far out, the ground at the bottom of the screen is CLOSER to the camera than the near plane (the camera sits
        // orbitRadius from the focal point, and the bottom of the view reaches about 2 x zoom back along the ground), so it
        // was clipped away and showed the empty background. An orthographic camera may have a negative near plane, so pull it
        // back by exactly what the current zoom needs, and keep the far plane beyond the top of the screen.
        if (cam != null && cam.orthographic)
            {
                float reach = 2.2f * cam.orthographicSize;
                // Near plane: allow negative (orthographic cameras support it) but clamp to a minimum
                // so we don't clip everything near the camera. -50 is far enough to include the full viewport.
                cam.nearClipPlane = Mathf.Min(0.3f, orbitRadius - reach - 5f);
                cam.nearClipPlane = Mathf.Max(cam.nearClipPlane, -50f);
                cam.farClipPlane = Mathf.Max(cam.farClipPlane, orbitRadius + reach + 100f);
            }
    }
}
