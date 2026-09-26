using UnityEngine;
using UnityEngine.InputSystem;
using Homesteader.UI;

[RequireComponent(typeof(CharacterController))]
public class PedController : MonoBehaviour
{
    public float walkSpeed = 2.0f;
    public float runSpeed = 5.0f;
    public float gravity = -9.81f;
    public float turnSpeed = 10f;
    public float modelRotationOffset = 180f;
    public Transform cameraTransform; // used to make WASD relative to the current camera facing

    private CharacterController controller;
    private Animator animator;
    private Homesteader.Animation.GlbClipPlayer glbPlayer;
    private float verticalVelocity;

    public bool IsMoving { get; private set; }

    /// <summary>When true, walking uses the two-arm carry clip (Walk_Carry).</summary>
    public bool Carrying { get; set; }

    void Awake()
    {
        controller = GetComponent<CharacterController>();
        animator = GetComponentInChildren<Animator>();
        glbPlayer = GetComponentInChildren<Homesteader.Animation.GlbClipPlayer>();
        ResolveCamera();
    }

    void Start()
    {
        // If spawned with default identity rotation, apply the model's facing offset
        if (transform.rotation == Quaternion.identity)
        {
            transform.rotation = Quaternion.Euler(0f, modelRotationOffset, 0f);
        }
        ResolveCamera();
    }

    void ResolveCamera()
    {
        var isoCam = FindAnyObjectByType<IsometricLockedCamera>();
        if (isoCam != null)
        {
            cameraTransform = isoCam.transform;
        }
        else
        {
            var followCam = FindAnyObjectByType<SimpleFollowCamera>();
            if (followCam != null)
            {
                cameraTransform = followCam.transform;
            }
            else if (Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
            }
        }
    }

    void Update()
    {
        if (TimeSystem.Instance.IsPaused)
        {
            IsMoving = false;
            if (glbPlayer != null) glbPlayer.SetLocomotion(0f);
            if (animator != null)
            {
                animator.SetFloat("Speed", 0f);
            }
            return;
        }

        if (cameraTransform == null)
        {
            ResolveCamera();
        }

        var kb = Keyboard.current;
        float h = 0f;
        float v = 0f;
        bool running = false;

        if (Homesteader.UI.HudBindings.KeyboardCaptured)
        {
            // A HUD window or text field owns the keyboard
        }
        else if (kb != null)
        {
            if (kb.aKey.isPressed) h -= 1f;
            if (kb.dKey.isPressed) h += 1f;
            if (kb.sKey.isPressed) v -= 1f;
            if (kb.wKey.isPressed) v += 1f;
            running = kb.leftShiftKey.isPressed;
        }
        else
        {
            if (Input.GetKey(KeyCode.A)) h -= 1f;
            if (Input.GetKey(KeyCode.D)) h += 1f;
            if (Input.GetKey(KeyCode.S)) v -= 1f;
            if (Input.GetKey(KeyCode.W)) v += 1f;
            running = Input.GetKey(KeyCode.LeftShift);
        }

        Vector3 move = new Vector3(h, 0f, v);
        move = Vector3.ClampMagnitude(move, 1f);
        IsMoving = move.sqrMagnitude > 0.01f;

        // Rotate input by the camera's current yaw so WASD always matches what's on screen,
        // even after Q/E rotates the isometric camera.
        float camYaw = cameraTransform != null ? cameraTransform.eulerAngles.y : 0f;
        Quaternion camYawRot = Quaternion.Euler(0f, camYaw, 0f);

        float speed = running ? runSpeed : walkSpeed;
        Vector3 worldMove = camYawRot * move * speed;

        if (controller.isGrounded)
            verticalVelocity = -0.5f;
        else
            verticalVelocity += gravity * Time.deltaTime;

        Vector3 velocity = worldMove;
        velocity.y = verticalVelocity;
        controller.Move(velocity * Time.deltaTime);

        // Turn character smoothly towards the direction of movement, offset by modelRotationOffset
        if (IsMoving && worldMove.sqrMagnitude > 0.001f)
        {
            Vector3 lookDirection = new Vector3(worldMove.x, 0f, worldMove.z);
            if (lookDirection != Vector3.zero)
            {
                Quaternion targetRot = Quaternion.LookRotation(lookDirection) * Quaternion.Euler(0f, modelRotationOffset, 0f);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRot, turnSpeed * Time.deltaTime);
            }
        }

        if (animator == null)
        {
            animator = GetComponentInChildren<Animator>();
            if (animator != null)
            {
                string ctrlName = animator.runtimeAnimatorController != null ? animator.runtimeAnimatorController.name : "null";
                string avatarName = animator.avatar != null ? animator.avatar.name : "null";
                Debug.Log($"[PedController] Resolved Animator on {animator.gameObject.name}: ctrl={ctrlName}, avatar={avatarName}");
            }
        }

        if (glbPlayer != null)
        {
            if (IsMoving && glbPlayer.ActionActive) glbPlayer.EndAction(); // moving cancels dig / hoe / pet / kneel ...
            // Real ground speed (not the input speed): the gait clip is scaled to it so the feet do not skate,
            // and it drops to ~0 when the ped is pushing against a wall.
            Vector3 cv = controller.velocity;
            float groundSpeed = new Vector2(cv.x, cv.z).magnitude;
            glbPlayer.SetLocomotion(move.magnitude * (running ? 1f : 0.5f), Carrying, groundSpeed);
        }

        if (animator != null)
        {
            float targetSpeed = move.magnitude * (running ? 1f : 0.5f);
            animator.SetFloat("Speed", targetSpeed);

            // Ensure character movement animations continuously loop while moving
            if (IsMoving && !animator.IsInTransition(0))
            {
                var stateInfo = animator.GetCurrentAnimatorStateInfo(0);
                if (!running && stateInfo.IsName("Walk") && stateInfo.normalizedTime >= 0.98f)
                {
                    animator.Play("Walk", 0, 0f);
                }
                else if (running && stateInfo.IsName("Run") && stateInfo.normalizedTime >= 0.98f)
                {
                    animator.Play("Run", 0, 0f);
                }
            }
        }
    }
}
