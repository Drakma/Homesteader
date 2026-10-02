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

    // Distance-accumulator footsteps: no animation-event hookup exists yet, so trigger on metres travelled
    // instead - simple, and correct regardless of which clip/animator drives the visual walk.
    private float footstepDistance;
    private const float WalkStepInterval = 2.1f;   // metres per footstep at a walk
    private const float RunStepInterval = 3.0f;    // longer stride at a run, but faster cadence overall

    public bool IsMoving { get; private set; }

    /// <summary>Starts a looping full-body work clip (Chop_Tree_RT, Dig, Hoe ...) and turns to face a point. Walking cancels it.</summary>
    public bool BeginWork(string clip, Vector3 faceToward)
    {
        if (glbPlayer == null) return false;
        Vector3 d = faceToward - transform.position;
        d.y = 0f;
        if (d.sqrMagnitude > 0.01f)
            transform.rotation = Quaternion.LookRotation(d.normalized) * Quaternion.Euler(0f, modelRotationOffset, 0f);
        if (glbPlayer.ActionActive && glbPlayer.CurrentAction == clip) return true;
        return glbPlayer.BeginAction(clip, true, 0.15f);
    }

    /// <summary>Playback time within the running work clip, wrapped to one cycle (false if that clip is not running).</summary>
    public bool WorkPhase(string clip, out float seconds, out float length)
    {
        seconds = length = 0f;
        if (glbPlayer == null || !glbPlayer.ActionClock(clip, out float t, out length)) return false;
        seconds = t % length;
        return true;
    }

    /// <summary>Ends a work clip started by BeginWork.</summary>
    public void EndWork(string clip)
    {
        if (glbPlayer != null && glbPlayer.ActionActive && glbPlayer.CurrentAction == clip) glbPlayer.EndAction();
    }

    /// <summary>When true, walking uses the two-arm carry clip (Walk_Carry).</summary>
    public bool Carrying { get; set; }

    void Awake()
    {
        controller = GetComponent<CharacterController>();
        // Allow the player to step over small banks at water edges and terrace steps.
        controller.stepOffset = 0.5f;
        controller.slopeLimit = 60f;

        // Initialize land ownership so the movement check works even before
        // the welcome menu runs (e.g. Continue/Load).
        Homesteader.Land.LandOwnershipSystem.Initialize();
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

        // Snap the player to the terrain surface so we don't start
        // floating 3m above the ground. CharacterController ignores
        // direct transform changes while enabled, so disable it
        // briefly, move, then re-enable.
        var cc = GetComponent<CharacterController>();
        if (cc != null)
        {
            cc.enabled = false;
            Vector3 pos = transform.position;
            pos.y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(pos);
            transform.position = pos;
            cc.enabled = true;
            Debug.Log($"[PedController] Snapped to ground surface at Y={pos.y:F2}");
        }
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
            // Read through KeyBindings so the keys can be rebound in Settings > Controls.
            if (Homesteader.Controls.KeyBindings.IsPressed(Homesteader.Controls.BindAction.MoveLeft)) h -= 1f;
            if (Homesteader.Controls.KeyBindings.IsPressed(Homesteader.Controls.BindAction.MoveRight)) h += 1f;
            if (Homesteader.Controls.KeyBindings.IsPressed(Homesteader.Controls.BindAction.MoveDown)) v -= 1f;
            if (Homesteader.Controls.KeyBindings.IsPressed(Homesteader.Controls.BindAction.MoveUp)) v += 1f;
            running = Homesteader.Controls.KeyBindings.IsPressed(Homesteader.Controls.BindAction.Run);
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

        // Land ownership check: prevent moving into unowned tiles.
        // The invisible walls handle this physically, but this is a software
        // safety net that also prevents the player from being pushed into
        // an unowned tile by physics glitches.
        Vector3 targetPos = transform.position + velocity * Time.deltaTime;
        if (!Homesteader.Land.LandOwnershipSystem.IsOwned(targetPos.x, targetPos.z))
        {
            // Check if the current position is still owned — if so, zero out
            // the horizontal movement so the player stays in place.
            if (Homesteader.Land.LandOwnershipSystem.IsOwned(transform.position.x, transform.position.z))
            {
                velocity.x = 0f;
                velocity.z = 0f;
            }
        }

        controller.Move(velocity * Time.deltaTime);

        UpdateFootsteps(worldMove, running);

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

    /// <summary>Triggers a footstep sound every WalkStepInterval/RunStepInterval metres travelled while
    /// grounded - not tied to any specific animation clip, so it works regardless of which walk/run clip is
    /// currently assigned.</summary>
    private void UpdateFootsteps(Vector3 worldMove, bool running)
    {
        var audio = Homesteader.Audio.AudioManager.Instance;
        if (audio == null || !IsMoving || !controller.isGrounded) return;

        footstepDistance += worldMove.magnitude * Time.deltaTime;
        float interval = running ? RunStepInterval : WalkStepInterval;
        if (footstepDistance < interval) return;
        footstepDistance = 0f;

        // Cheap surface guess: the same global snow-coverage value WeatherEffectsManager already drives the
        // ground shader with. Real per-biome surface detection (grass/dirt/gravel/wood) can replace this
        // once it's worth the lookup cost - footsteps working at all matters more right now than which of
        // five near-identical procedural ticks plays.
        Vector4 groundFx = Shader.GetGlobalVector("_WeatherGroundEffects");
        var surface = groundFx.x > 0.5f
            ? Homesteader.Audio.AudioManager.FootstepSurface.Snow
            : Homesteader.Audio.AudioManager.FootstepSurface.Grass;

        audio.PlayFootstep(transform.position, surface);
    }
}
