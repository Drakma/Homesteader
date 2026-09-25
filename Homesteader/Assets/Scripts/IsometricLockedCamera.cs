using UnityEngine;
using UnityEngine.InputSystem;

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
    // Locked: not serialized, so scene overrides can't change them.
    // Zoom levels are 2.5, 3.5, 4.5, 5.5, 6.5, 7.5.
    private const float minOrthoSize = 2.5f;
    private const float maxOrthoSize = 7.5f;
    private const float zoomStep = 1.0f;

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
        if (cam != null && cam.orthographic) cam.orthographicSize = SnapZoom(cam.orthographicSize);
        targetYaw = yawDegrees;
        orbitRadius = Mathf.Sqrt(distance * distance + height * height);
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
        if (isCtrlHeld && cam != null && cam.orthographic && Mathf.Abs(scroll) > 0.01f)
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

    void LateUpdate()
    {
        if (target == null && _focalPoint == Vector3.zero) return;

        yawDegrees = Mathf.LerpAngle(yawDegrees, targetYaw, yawRotateSpeed * Time.unscaledDeltaTime);

        // Locked isometric: pitch stays fixed, only yaw orbits (via Q/E snaps).
        Quaternion lookRot = Quaternion.Euler(pitchDegrees, yawDegrees, 0f);
        Vector3 offset = lookRot * new Vector3(0f, 0f, -orbitRadius);
        transform.position = _focalPoint + offset;

        transform.rotation = lookRot;
    }
}
