using UnityEngine;
using UnityEngine.InputSystem;
using Homesteader.UI;

[RequireComponent(typeof(CharacterController))]
public class PedController : MonoBehaviour
{
    public float walkSpeed = 2.0f;
    public float runSpeed = 5.0f;

    [Header("Carrying")]
    [Tooltip("Max Carry Weight (kg). The more the ped carries toward this, the slower it moves; past it the ped is encumbered and moves at 10 percent of its base speed.")]
    public float maxCarryWeight = 70f;
    public const float EncumberedSpeedFactor = 0.10f;
    /// <summary>Encumbrance is OFF for now: carrying slows nothing and nothing warns. The weights are still counted (CarryWeight); set this to true to bring the slowdown back.</summary>
    public const bool EncumbranceOn = false;
    public float gravity = -9.81f;
    public float turnSpeed = 10f;
    public float modelRotationOffset = 180f;
    public Transform cameraTransform; // used to make WASD relative to the current camera facing

    private float _carryWeight;        // kg in the toolbar (items and what the containers hold), refreshed a few times a second
    private float _nextCarryCheck;
    private bool _wasEncumbered;

    /// <summary>Weight of everything in the toolbar, in kg.</summary>
    public float CarryWeight => _carryWeight;
    public bool IsEncumbered => EncumbranceOn && maxCarryWeight > 0f && _carryWeight > maxCarryWeight;

    /// <summary>1 with an empty toolbar, easing down as the load nears Max Carry Weight (0.1 at the limit); 0.1 beyond it.</summary>
    public float CarrySpeedFactor
    {
        get
        {
            if (!EncumbranceOn || maxCarryWeight <= 0f) return 1f;
            float r = _carryWeight / maxCarryWeight;
            if (r > 1f) return EncumberedSpeedFactor;
            return Mathf.Lerp(1f, EncumberedSpeedFactor, r * r);
        }
    }

    private void RefreshCarryWeight()
    {
        if (Time.time < _nextCarryCheck) return;
        _nextCarryCheck = Time.time + 0.25f;
        float total = 0f;
        HudState hud = HudState.Active;
        if (hud != null)
        {
            for (int i = 0; i < hud.Toolbar.Count; i++)
            {
                ToolbarSlotData slot = hud.Toolbar[i];
                if (slot.Count <= 0 || string.IsNullOrEmpty(slot.IconId)) continue;
                total += ContainerRules.WeightOf(slot.IconId) * slot.Count + ContainerRules.Used(slot.Contents);
            }
        }
        _carryWeight = total;
        bool encumbered = IsEncumbered;
        if (encumbered && !_wasEncumbered)
            ToastNotificationSystem.ShowWarning("Encumbered", $"Carrying {UnitFormat.Weight(_carryWeight, "0.#")} of {UnitFormat.Weight(maxCarryWeight, "0.#")}. You can only move at {EncumberedSpeedFactor * 100f:0}% speed.");
        _wasEncumbered = encumbered;
    }

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

    /// <summary>
    /// Automatic walking (the build routine of a construction site): while set, the ped walks to this point on its own. Any movement key
    /// takes control back and clears it (AutoCancelled turns true).
    /// </summary>
    public Vector3? AutoTarget { get; private set; }
    public bool AutoCancelled { get; private set; }
    /// <summary>True while the player is pressing a movement key (not automatic walking): what takes control back from a build.</summary>
    public bool ManualInput { get; private set; }

    public void AutoWalkTo(Vector3 target) { AutoTarget = target; AutoCancelled = false; }
    public void AutoStop() { AutoTarget = null; }

    /// <summary>When true, walking uses the two-arm carry clip (Walk_Carry).</summary>
    public bool Carrying { get; set; }

    /// <summary>Pushing a wheelbarrow: movement is slowed by this factor and running is off (1 = not pushing).</summary>
    public float PushSpeedFactor { get; set; } = 1f;
    public bool NoRun { get; set; }

    private static PedController s_current;
    /// <summary>The player, found once (FindAnyObjectByType scans the scene, so it must not run every frame).</summary>
    public static PedController Current
    {
        get { if (s_current == null) s_current = UnityEngine.Object.FindAnyObjectByType<PedController>(); return s_current; }
    }

    void Awake()
    {
        controller = GetComponent<CharacterController>();
        // Allow the player to step over small banks at water edges and terrace steps.
        controller.stepOffset = 0.5f;
        controller.slopeLimit = 60f;

        // Interior doorways are 1.1 m wide and about 2.0 m high: the capsule (its size is multiplied by the transform scale) must fit with room to spare.
        Vector3 sc = transform.lossyScale;
        float sy = Mathf.Max(0.01f, sc.y), sxz = Mathf.Max(0.01f, Mathf.Max(sc.x, sc.z));
        controller.skinWidth = Mathf.Min(controller.skinWidth, 0.02f);
        controller.radius = Mathf.Min(controller.radius, 0.28f / sxz);
        // the capsule top, measured from the player's feet (the transform), must clear a 2.0 m doorway: its centre may sit above the feet
        float bottom = (controller.center.y - controller.height * 0.5f) * sy;
        float top = (controller.center.y + controller.height * 0.5f) * sy;
        Debug.Log("[PedController] capsule before: radius " + (controller.radius * sxz).ToString("F2") + " m, bottom " + bottom.ToString("F2") + " m, top " + top.ToString("F2") + " m above the feet, scale " + sc);
        const float maxTop = 1.85f;
        if (top > maxTop)
        {
            float h = Mathf.Max(controller.radius * 2f + 0.05f, (maxTop - bottom) / sy);
            controller.height = h;
            controller.center = new Vector3(controller.center.x, bottom / sy + h * 0.5f, controller.center.z);
            Debug.Log("[PedController] capsule limited to " + (controller.height * sy).ToString("F2") + " m, top " + ((controller.center.y + controller.height * 0.5f) * sy).ToString("F2") + " m");
        }

        // Initialize land ownership so the movement check works even before
        // the welcome menu runs (e.g. Continue/Load).
        Homesteader.Land.LandOwnershipSystem.Initialize();
        animator = GetComponentInChildren<Animator>();
        glbPlayer = GetComponentInChildren<Homesteader.Animation.GlbClipPlayer>();
        ResolveCamera();
    }

    private Collider _lastSideHit; private float _lastSideLog;

    /// <summary>Diagnostic: names the collider that stops the player from the side (an unexplained invisible wall), at most every 2 s per collider.</summary>
    void OnControllerColliderHit(ControllerColliderHit hit)
    {
        if (hit.normal.y > 0.5f || hit.collider == null) return;
        if (hit.collider == _lastSideHit && Time.time - _lastSideLog < 2f) return;
        _lastSideHit = hit.collider; _lastSideLog = Time.time;
        Transform t = hit.collider.transform; string path = t.name;
        for (int i = 0; i < 6 && t.parent != null; i++) { t = t.parent; path = t.name + "/" + path; }
        var site = hit.collider.GetComponentInParent<Homesteader.Growth.ConstructionSite>();
        string local = site != null ? site.transform.InverseTransformPoint(hit.point).ToString("F2") : "n/a";
        Debug.Log("[PedController] blocked from the side by " + path + " (" + hit.collider.GetType().Name + (hit.collider is MeshCollider mc0 ? ", convex " + mc0.convex : "") + "), point " + hit.point.ToString("F2") + ", in the building " + local + ", normal " + hit.normal.ToString("F2") + ", player " + transform.position.ToString("F2") + ", capsule world y " + hit.controller.bounds.min.y.ToString("F2") + " to " + hit.controller.bounds.max.y.ToString("F2") + ", moving " + hit.moveDirection.ToString("F2") + ", hit collider y " + hit.collider.bounds.min.y.ToString("F2") + " to " + hit.collider.bounds.max.y.ToString("F2"));
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
        ManualInput = move.sqrMagnitude > 0.01f;
        if (AutoTarget.HasValue)
        {
            if (move.sqrMagnitude > 0.01f) { AutoTarget = null; AutoCancelled = true; }   // a key takes control back
            else
            {
                Vector3 to = AutoTarget.Value - transform.position;
                to.y = 0f;
                if (to.sqrMagnitude > 0.04f)
                {
                    float yaw = cameraTransform != null ? cameraTransform.eulerAngles.y : 0f;
                    move = Quaternion.Inverse(Quaternion.Euler(0f, yaw, 0f)) * to.normalized;   // the input is camera-relative
                    running = false;
                }
            }
        }
        move = Vector3.ClampMagnitude(move, 1f);
        IsMoving = move.sqrMagnitude > 0.01f;

        // Rotate input by the camera's current yaw so WASD always matches what's on screen,
        // even after Q/E rotates the isometric camera.
        float camYaw = cameraTransform != null ? cameraTransform.eulerAngles.y : 0f;
        Quaternion camYawRot = Quaternion.Euler(0f, camYaw, 0f);

        RefreshCarryWeight();
        if (NoRun) running = false;
        float speed = (running ? runSpeed : walkSpeed) * CarrySpeedFactor * PushSpeedFactor;
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

        // The controller lifts itself by stepOffset before every sideways move (to climb a step), so it needs its height plus the step in headroom:
        // under a doorway beam or a ceiling joist the step shrinks to what fits, or the beam stops the player like an invisible wall.
        {
            const float fullStep = 0.5f;
            float top = controller.bounds.max.y;
            float step = fullStep;
            Vector3 ahead = new Vector3(worldMove.x, 0f, worldMove.z);
            ahead = ahead.sqrMagnitude > 0.0001f ? ahead.normalized : Vector3.zero;
            // the lifted capsule moves forward too, so the beam to look for is over the player and just ahead of them
            for (int i = 0; i < 4; i++)
            {
                Vector3 o = controller.bounds.center + ahead * (0.2f * i);
                o.y = top - 0.1f;
                if (Physics.SphereCast(o, 0.2f, Vector3.up, out RaycastHit ceil, fullStep + 0.3f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                    step = Mathf.Min(step, Mathf.Clamp(ceil.distance + 0.03f, 0.02f, fullStep));
            }
            controller.stepOffset = step;
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
