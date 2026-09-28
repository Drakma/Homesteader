using System.Collections.Generic;
using Homesteader.Animals;
using Homesteader.Generation;
using Homesteader.Growth;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UIElements;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Homesteader.UI
{
    /// <summary>
    /// A flat isometric map in the lower right corner, toggled with M. It is a plain colour map, not a second render of the
    /// world: every square shows the main colour of its biome (water blue, farmland brown, and so on), placed structures are
    /// small dark marks, and a lit lamp shows as a dot of its own colour. The plane follows the game view: it is
    /// turned by the game camera's yaw and squashed to the game's isometric angle, so when the view rotates with Q / E the map
    /// rotates with it. It is centred on the player (the white dot). The mouse wheel over the map zooms it (and does not zoom
    /// the game view or cycle the toolbar while the pointer is over it). Drag the map to move it; hold Shift and scroll over it
    /// to make it bigger or smaller. Its position, size, zoom and on / off are remembered between runs
    /// (PlayerPrefs "Homesteader.MiniMap.*").
    ///
    /// Bootstraps itself and attaches to the HUD's UI Toolkit root once it exists. Keys: docs/CONTROLS.md.
    /// </summary>
    public sealed class MiniMap : MonoBehaviour
    {
        private const int TexSize = 128;             // pixels across the map texture
        private const float PlaneSidePx = 212f;      // the square plane; turned 45 degrees its diagonal (300 px) fills the panel
        private const float PanelW = 300f, PanelH = 160f;
        private const float MinScale = 0.6f, MaxScale = 2.6f;
        private const string PrefKey = "Homesteader.MiniMap.";
        private const float DefaultHalfExtent = 40f; // metres from the player to the map's edge (half the area shown)
        private const float MinHalfExtent = 10f;
        private const float MaxHalfExtent = 250f;
        private const float IsoSquash = 0.5f;        // sin(30 degrees): the game camera's pitch
        private const int ChunkCells = 16;           // the colour cache is kept in square chunks of 16 x 16 grid cells
        private const float PrefetchMargin = 1.6f;   // colours are cached out to 1.6 x the shown half-width, ahead of the player

        /// <summary>True while the pointer is over the map (other wheel / zoom handlers should leave it alone).</summary>
        public static bool PointerOver { get; private set; }

        /// <summary>Clears the cached biome colours so the map rebuilds after terrain regeneration.</summary>
        public static void InvalidateCache()
        {
            var mm = FindAnyObjectByType<MiniMap>();
            if (mm != null)
            {
                mm.chunks.Clear();
                mm.baseCenter = new Vector2(float.MaxValue, float.MaxValue);
            }
        }

        private VisualElement frame, squash, plane, dot;
          	private readonly List<VisualElement> shadows = new List<VisualElement>();
          	private float scale = 1f;
          	private float posX01 = 1f, posY01 = 1f;     // top left corner as a share of the free space (1, 1 = bottom right)
          	private bool needsLayout = true;
          	private bool dragging;
          	private Vector2 dragOffset;
          	private Texture2D tex;
          	private Color32[] pixels;
          	private bool shown = true;
          	private float halfExtent = DefaultHalfExtent;

          	// Cardinal direction labels around the minimap.
          	private Label dirN, dirS, dirE, dirW;

        	private Camera gameCam;
        private Transform player;
        private HomesteaderTerrainGenerator generator;
        private readonly Dictionary<string, Color> biomeColors = new Dictionary<string, Color>();
        private readonly Dictionary<long, Color32[]> chunks = new Dictionary<long, Color32[]>();
        private readonly Color32 unknown = new Color32(70, 84, 64, 255);

        // The colour grid is cached (Prefetch fills chunks of colours ahead of the map). The texture re-centres by whole pixels on
        // the world's pixel lattice; the plane is slid by the sub-pixel remainder to keep the player centred in between. The overlay
        // (structures, lamp glow) is redrawn twice a second, and living things are cheap UI dots moved every frame.
        private Color32[] baseColors;
        private Vector2 baseCenter = new Vector2(float.MaxValue, float.MaxValue);
        private float baseExtent;
        private bool baseFilling;
        private float nextCompose;
        private float composedExtent;
        private readonly List<VisualElement> livingDots = new List<VisualElement>();

        private static readonly Color PlayerColour = new Color(1f, 0.93f, 0.5f, 0.75f);   // faint yellow
        private static readonly Color DocileColour = new Color(1f, 1f, 1f, 0.9f);         // white
        private static readonly Color AggressiveColour = new Color(1f, 0.25f, 0.2f, 0.95f); // red

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            PointerOver = false;
            // Register for all future scene loads so the MiniMap is re-created
            // after scene reloads (New Game, Load). RuntimeInitializeOnLoadMethod
            // only fires once, so we need sceneLoaded to re-run.
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
            OnSceneLoaded(default, LoadSceneMode.Single);
        }

        private static void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (FindAnyObjectByType<MiniMap>() != null) return;
            new GameObject("MiniMap").AddComponent<MiniMap>();
        }

        private void OnDisable() => PointerOver = false;

        private Label CreateDirLabel(string text)
        {
        	var lbl = new Label(text) { name = $"minimap-dir-{text}" };
        	lbl.pickingMode = PickingMode.Ignore;
        	lbl.style.position = Position.Absolute;
        	lbl.style.unityFontStyleAndWeight = FontStyle.Bold;
        	lbl.style.fontSize = 14;
        	lbl.style.color = Color.white;
        	lbl.style.unityTextAlign = TextAnchor.MiddleCenter;
        	lbl.style.width = 24f;
        	lbl.style.height = 24f;
        	lbl.AddToClassList("minimap-dir");
        	return lbl;
        }

        /// <summary>
        /// Repositions the N/S/E/W labels around the minimap center, rotated by
        /// the camera yaw so they track the map's rotation.  Each label sits at
        /// a fixed radius from the center; its angle is its cardinal bearing
        /// minus the camera yaw (matching the plane's -yaw rotation).
        /// </summary>
        private void UpdateDirLabels(float yaw)
        {
        	if (dirN == null) return;
        	float w = PanelW * scale, h = PanelH * scale;
        	float cx = w * 0.5f, cy = h * 0.5f;
        	float ls = 24f;
        	// Radius from center to label center — keep labels just inside the frame edge.
        	float rx = (w - ls) * 0.5f;
        	float ry = (h - ls) * 0.5f;
        	float rad = Mathf.Min(rx, ry);
        	float yr = yaw * Mathf.Deg2Rad;
        	float cosY = Mathf.Cos(yr), sinY = Mathf.Sin(yr);

        	// Each cardinal starts at a base angle (N=0, E=90, S=180, W=270)
        	// measured clockwise from north in screen space (Y-down).
        	// After rotating by -yaw (the plane's rotation), the screen position is:
        	//   x = r * sin(baseAngle - yaw)
        	//   y = -r * cos(baseAngle - yaw)
        	PlaceDirLabel(dirN, 0f, cx, cy, rad, ls, cosY, sinY);
        	PlaceDirLabel(dirE, 90f, cx, cy, rad, ls, cosY, sinY);
        	PlaceDirLabel(dirS, 180f, cx, cy, rad, ls, cosY, sinY);
        	PlaceDirLabel(dirW, 270f, cx, cy, rad, ls, cosY, sinY);
        }

        private void PlaceDirLabel(Label lbl, float baseAngleDeg, float cx, float cy, float r, float ls, float cosY, float sinY)
        {
        	float a = (baseAngleDeg) * Mathf.Deg2Rad;
        	// Rotate the base position by -yaw (clockwise in screen coords):
        	// x' = x*cos(yaw) + y*sin(yaw)
        	// y' = -x*sin(yaw) + y*cos(yaw)
        	// where base x = r*sin(a), base y = -r*cos(a)
        	float bx = r * Mathf.Sin(a);
        	float by = -r * Mathf.Cos(a);
        	float x = bx * cosY + by * sinY;
        	float y = -bx * sinY + by * cosY;
        	lbl.style.left = cx + x - ls * 0.5f;
        	lbl.style.top = cy + y - ls * 0.5f;
        }

        private void Update()
        {
            if (frame == null) TryBuild();
            if (frame == null) return;
            if (needsLayout) TryApplyLayout();

            if (TogglePressed() && !HudBindings.KeyboardCaptured)
            {
                shown = !shown;
                frame.style.display = shown ? DisplayStyle.Flex : DisplayStyle.None;
                if (!shown) PointerOver = false;
                SavePrefs();
            }

            // Ctrl+M: clear the minimap cache and force a full rebuild.
            if (CtrlMPressed() && !HudBindings.KeyboardCaptured)
            {
                InvalidateCache();
                baseExtent = -1f; // force BuildBase to re-centre on next Update
                nextCompose = 0f; // force Compose to run immediately
            }
            if (!shown) return;

            KeepBehindPhone();

            ResolveScene();
            if (player == null) return;

            // Follow the game view: turn by its yaw, so the map rotates when the view does.
            			float yaw = gameCam != null ? gameCam.transform.eulerAngles.y : 0f;
            			var turn = new Rotate(new Angle(-yaw, AngleUnit.Degree));
            			plane.style.rotate = turn;
            			foreach (VisualElement sh in shadows) sh.style.rotate = turn;
            			// Direction labels rotate with the map — positions track the camera yaw.
            			UpdateDirLabels(yaw);

            			Vector3 p = player.position;
            Vector2 pc = new Vector2(p.x, p.z);

            // 0. Cache colours ahead of the map (one chunk a frame, nearest first), so recentring never waits on a lookup.
            Prefetch(pc);

            // 1. The colour grid re-centres as soon as the player has moved most of ONE map pixel, and always onto the world's
            //    pixel lattice (never onto the player's exact position). So the texture moves by whole pixels, the sub-pixel
            //    rest is the plane's slide below, and no edge of the map ever comes into view: it scrolls, it does not leap.
            //    This is cheap because the colours are already cached (Prefetch), so it is a copy, not a computation.
            float mpp = 2f * halfExtent / TexSize;
            bool zoomed = !Mathf.Approximately(baseExtent, halfExtent);
            bool drifted = Mathf.Abs(pc.x - baseCenter.x) > 0.75f * mpp || Mathf.Abs(pc.y - baseCenter.y) > 0.75f * mpp;
            bool baseChanged = false;
            if (drifted || zoomed || baseFilling)
            {
                if (drifted || zoomed)
                {
                    baseExtent = halfExtent;
                    baseCenter = new Vector2(Mathf.Round(pc.x / mpp) * mpp, Mathf.Round(pc.y / mpp) * mpp);
                }
                BuildBase();
                baseChanged = true;
            }

            // 2. The overlay: twice a second (lamps brighten and dim, things get placed), or right after the grid changed.
            if (baseChanged || Time.unscaledTime >= nextCompose)
            {
                Compose();
                nextCompose = Time.unscaledTime + 0.5f;
            }

            // 3. Every frame, cheap: slide the plane so the player stays centred, and move the living dots.
            float side = PlaneSidePx * scale;
            float ppm = side / (2f * baseExtent);                       // plane pixels per metre at the grid's zoom
            Vector2 slide = -ToPlane(pc - baseCenter, yaw, ppm);
            plane.style.translate = new Translate(slide.x, slide.y);
            UpdateLivingDots(pc, yaw, side, PlaneSidePx * scale / (2f * halfExtent));
        }

        /// <summary>A world offset in metres to plane pixels (x right, y down), turned by the map's rotation, before the squash.</summary>
        private static Vector2 ToPlane(Vector2 metres, float yawDeg, float pixelsPerMetre)
        {
            float px = metres.x * pixelsPerMetre, py = -metres.y * pixelsPerMetre;   // world +Z is up the texture
            float a = -yawDeg * Mathf.Deg2Rad;                                         // the plane turns by -yaw (clockwise positive)
            float c = Mathf.Cos(a), sn = Mathf.Sin(a);
            return new Vector2(px * c - py * sn, px * sn + py * c);
        }

        private void UpdateLivingDots(Vector2 playerXZ, float yawDeg, float sidePx, float pixelsPerMetre)
        {
            float w = PanelW * scale, h = PanelH * scale;
            int used = 0;
            float half = sidePx * 0.5f;
            for (int i = 0; i < AnimalBrain.All.Count; i++)
            {
                AnimalBrain a = AnimalBrain.All[i];
                if (a == null) continue;
                Vector2 rel = new Vector2(a.transform.position.x, a.transform.position.z) - playerXZ;
                // outside the square the map shows: no dot
                if (Mathf.Abs(rel.x * pixelsPerMetre) > half || Mathf.Abs(rel.y * pixelsPerMetre) > half) continue;
                Vector2 v = ToPlane(rel, yawDeg, pixelsPerMetre);
                VisualElement d = Dot(used++);
                d.style.left = w * 0.5f + v.x - 2.5f;
                d.style.top = h * 0.5f + v.y * IsoSquash - 2.5f;
                d.style.backgroundColor = a.IsAggressive ? AggressiveColour : DocileColour;
                d.style.display = DisplayStyle.Flex;
            }
            for (int i = used; i < livingDots.Count; i++) livingDots[i].style.display = DisplayStyle.None;
        }

        private VisualElement Dot(int index)
        {
            while (livingDots.Count <= index)
            {
                var d = new VisualElement();
                d.pickingMode = PickingMode.Ignore;
                d.style.position = Position.Absolute;
                d.style.width = 5; d.style.height = 5;
                d.style.borderTopLeftRadius = 3; d.style.borderTopRightRadius = 3;
                d.style.borderBottomLeftRadius = 3; d.style.borderBottomRightRadius = 3;
                frame.Insert(frame.IndexOf(dot), d);          // under the player's dot and the resize handle
                livingDots.Add(d);
            }
            return livingDots[index];
        }

        // ------------------------------------------------------------------ build

        /// <summary>The phone draws over the map: keep the map below whichever top-level element holds the phone.</summary>
        private void KeepBehindPhone()
        {
            VisualElement root = Root;
            if (root == null) return;
            VisualElement phone = root.Q<VisualElement>("PhoneWrapper");
            if (phone == null) return;
            while (phone.parent != null && phone.parent != root) phone = phone.parent;
            if (phone.parent != root) return;
            if (root.IndexOf(frame) > root.IndexOf(phone)) frame.PlaceBehind(phone);
        }

        private void TryBuild()
        {
            HudBindings hud = HudBindings.Instance;
            VisualElement root = hud != null ? hud.Root : null;
            if (root == null || root.panel == null) return;

            tex = new Texture2D(TexSize, TexSize, TextureFormat.RGBA32, false)
            {
                name = "MiniMap",
                filterMode = FilterMode.Point,
                wrapMode = TextureWrapMode.Clamp,
            };
            pixels = new Color32[TexSize * TexSize];
            baseColors = new Color32[TexSize * TexSize];

            frame = new VisualElement { name = "minimap" };
            frame.pickingMode = PickingMode.Position;
            frame.style.position = Position.Absolute;
            frame.style.overflow = Overflow.Hidden;

            // The plane's own rotation is applied to the plane; the squash to its parent, so the rotation is squashed as a
            // whole (turn first, then flatten to the isometric angle).
            squash = new VisualElement { name = "minimap-squash" };
            squash.pickingMode = PickingMode.Ignore;
            squash.style.position = Position.Absolute;
            squash.style.scale = new Scale(new Vector2(1f, IsoSquash));

            // A faint black shadow under the map: a few stacked copies of its outline, each slightly larger and fainter, dropped a
            // little downward (UI Toolkit has no blur). They sit behind the plane and are not part of the picture.
            for (int i = 0; i < 4; i++)
            {
                var sh = new VisualElement { name = "minimap-shadow" };
                sh.pickingMode = PickingMode.Ignore;
                sh.style.position = Position.Absolute;
                sh.style.backgroundColor = new Color(0f, 0f, 0f, 0.11f);
                sh.style.scale = new Scale(new Vector2(1f + 0.035f * i, 1f + 0.035f * i));
                sh.style.translate = new Translate(0f, 7f);            // in the squashed space: about 3.5 px down on screen
                squash.Add(sh);
                shadows.Add(sh);
            }

            plane = new VisualElement { name = "minimap-plane" };
            plane.pickingMode = PickingMode.Ignore;
            plane.style.backgroundImage = new StyleBackground(Background.FromTexture2D(tex));
            squash.Add(plane);
            frame.Add(squash);

            // The player: a small white dot at the centre.
            			dot = new VisualElement { name = "minimap-player" };
            			dot.pickingMode = PickingMode.Ignore;
            			dot.style.position = Position.Absolute;
            			dot.style.width = 8; dot.style.height = 6;
            			dot.style.borderTopLeftRadius = 4; dot.style.borderTopRightRadius = 4;
            			dot.style.borderBottomLeftRadius = 4; dot.style.borderBottomRightRadius = 4;
            			dot.style.backgroundColor = PlayerColour;
            			frame.Add(dot);

            			// Cardinal direction labels around the minimap.
            			// Positions are recomputed every frame in Update() based on camera yaw,
            			// so they rotate with the map. Stored dimensions for the reposition math.
            			float labelSize = 24f;
            			dirN = CreateDirLabel("N"); frame.Add(dirN);
            			dirS = CreateDirLabel("S"); frame.Add(dirS);
            			dirE = CreateDirLabel("E"); frame.Add(dirE);
            			dirW = CreateDirLabel("W"); frame.Add(dirW);

            						frame.RegisterCallback<PointerDownEvent>(OnFrameDown);
            frame.RegisterCallback<PointerMoveEvent>(OnFrameMove);
            frame.RegisterCallback<PointerUpEvent>(OnFrameUp);
            frame.RegisterCallback<WheelEvent>(OnWheel);
            frame.RegisterCallback<PointerEnterEvent>(_ => PointerOver = true);
            frame.RegisterCallback<PointerLeaveEvent>(_ => PointerOver = false);
            root.Add(frame);

            LoadPrefs();
            frame.style.display = shown ? DisplayStyle.Flex : DisplayStyle.None;
        }

        // ------------------------------------------------------------------ layout, drag, resize, remember

        private VisualElement Root => frame != null ? frame.parent : null;

        /// <summary>Sizes every part for the current scale and puts the frame at its remembered spot (once the HUD has a size).</summary>
        private void TryApplyLayout()
        {
            VisualElement root = Root;
            if (root == null || !(root.layout.width > 1f) || !(root.layout.height > 1f)) return;
            ApplyLayout();
            needsLayout = false;
        }

        private void SizeParts()
        {
            float w = PanelW * scale, h = PanelH * scale, side = PlaneSidePx * scale;
            frame.style.width = w; frame.style.height = h;
            squash.style.width = side; squash.style.height = side;
            squash.style.left = (w - side) * 0.5f; squash.style.top = (h - side) * 0.5f;
            plane.style.width = side; plane.style.height = side;
            foreach (VisualElement sh in shadows) { sh.style.width = side; sh.style.height = side; }
            dot.style.left = w * 0.5f - 4f; dot.style.top = h * 0.5f - 3f;
        }

        private void ApplyLayout()
        {
            VisualElement root = Root;
            SizeParts();
            float w = PanelW * scale, h = PanelH * scale;
            float freeX = Mathf.Max(0f, root.layout.width - w), freeY = Mathf.Max(0f, root.layout.height - h);
            frame.style.left = Mathf.Clamp01(posX01) * freeX;
            frame.style.top = Mathf.Clamp01(posY01) * freeY;
        }

        /// <summary>Stores where the frame is now as a share of the free space, so it keeps its place at other resolutions.</summary>
        private void RememberPosition()
        {
            VisualElement root = Root;
            float w = PanelW * scale, h = PanelH * scale;
            float freeX = Mathf.Max(1f, root.layout.width - w), freeY = Mathf.Max(1f, root.layout.height - h);
            posX01 = Mathf.Clamp01(frame.resolvedStyle.left / freeX);
            posY01 = Mathf.Clamp01(frame.resolvedStyle.top / freeY);
            SavePrefs();
        }

        private void OnFrameDown(PointerDownEvent e)
        {
            if (e.button != 0) return;
            dragging = true;
            Vector2 local = Root.WorldToLocal(e.position);
            dragOffset = new Vector2(local.x - frame.resolvedStyle.left, local.y - frame.resolvedStyle.top);
            frame.CapturePointer(e.pointerId);
            e.StopPropagation();
        }

        private void OnFrameMove(PointerMoveEvent e)
        {
            if (!dragging) return;
            VisualElement root = Root;
            Vector2 local = root.WorldToLocal(e.position);
            float w = PanelW * scale, h = PanelH * scale;
            frame.style.left = Mathf.Clamp(local.x - dragOffset.x, 0f, Mathf.Max(0f, root.layout.width - w));
            frame.style.top = Mathf.Clamp(local.y - dragOffset.y, 0f, Mathf.Max(0f, root.layout.height - h));
        }

        private void OnFrameUp(PointerUpEvent e)
        {
            if (!dragging) return;
            dragging = false;
            frame.ReleasePointer(e.pointerId);
            RememberPosition();
        }

        private void LoadPrefs()
        {
            scale = Mathf.Clamp(PlayerPrefs.GetFloat(PrefKey + "scale", 1f), 0.3f, MaxScale);
            posX01 = PlayerPrefs.GetFloat(PrefKey + "x", 1f);       // default: the lower right corner
            posY01 = PlayerPrefs.GetFloat(PrefKey + "y", 1f);
            halfExtent = Mathf.Clamp(PlayerPrefs.GetFloat(PrefKey + "zoom", DefaultHalfExtent), MinHalfExtent, MaxHalfExtent);
            shown = true;  // always start on
            needsLayout = true;
        }

        private void SavePrefs()
        {
            PlayerPrefs.SetFloat(PrefKey + "scale", scale);
            PlayerPrefs.SetFloat(PrefKey + "x", posX01);
            PlayerPrefs.SetFloat(PrefKey + "y", posY01);
            PlayerPrefs.SetFloat(PrefKey + "zoom", halfExtent);
            PlayerPrefs.SetInt(PrefKey + "shown", shown ? 1 : 0);
            PlayerPrefs.Save();
        }

        private void ResolveScene()
        {
            if (gameCam == null)
            {
                var iso = FindAnyObjectByType<IsometricLockedCamera>();
                gameCam = iso != null ? iso.GetComponent<Camera>() : Camera.main;
            }
            if (player == null)
            {
                var ped = FindAnyObjectByType<PedController>();
                if (ped != null) player = ped.transform;
            }
            if (generator == null)
            {
                generator = FindAnyObjectByType<HomesteaderTerrainGenerator>();
                if (generator != null)
                    foreach (BiomeData b in generator.biomes)
                        if (ColorUtility.TryParseHtmlString(b.color_hex, out Color c)) biomeColors[b.id] = c;
            }
        }

        // ------------------------------------------------------------------ input

        private void OnWheel(WheelEvent e)
        {
            if (e.shiftKey)
            {
                // Shift + wheel: make the map bigger (scroll up) or smaller (down), keeping its bottom right corner where it is.
                VisualElement root = Root;
                float right = frame.resolvedStyle.left + PanelW * scale, bottom = frame.resolvedStyle.top + PanelH * scale;
                float next = scale * (1f - Mathf.Sign(e.delta.y) * 0.1f);
                next = Mathf.Clamp(next, MinScale, MaxScale);
                next = Mathf.Min(next, right / PanelW, bottom / PanelH);        // stay inside the HUD
                scale = Mathf.Max(0.3f, next);
                SizeParts();
                frame.style.left = right - PanelW * scale;
                frame.style.top = bottom - PanelH * scale;
                RememberPosition();
                e.StopPropagation();
                return;
            }

            // Ctrl + wheel: zoom the minimap in/out (more or less area shown).
            if (e.ctrlKey)
            {
                halfExtent = Mathf.Clamp(halfExtent * (1f + Mathf.Sign(e.delta.y) * 0.15f), MinHalfExtent, MaxHalfExtent);
                SavePrefs();
                e.StopPropagation();
                return;
            }

            // Plain scroll over the map: zoom the minimap too, and swallow it so the game / toolbar don't also respond.
            halfExtent = Mathf.Clamp(halfExtent * (1f + Mathf.Sign(e.delta.y) * 0.15f), MinHalfExtent, MaxHalfExtent);
            SavePrefs();
            e.StopPropagation();
        }

        private static bool TogglePressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.mKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.M);
#endif
        }

        private static bool CtrlMPressed()
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            return kb != null && kb.mKey.wasPressedThisFrame
                && (kb.leftCtrlKey.isPressed || kb.rightCtrlKey.isPressed);
#else
            return (Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl))
                && Input.GetKeyDown(KeyCode.M);
#endif
        }

        // ------------------------------------------------------------------ paint the map

        /// <summary>Copies the colours around baseCenter out of the chunk cache. Nothing is worked out here: Prefetch has
        /// already done that ahead of time, so recentring the map is a copy, not a load.</summary>
        private void BuildBase()
        {
            float metresPerPixel = 2f * baseExtent / TexSize;
            int size = CellSize(metresPerPixel);
            float originX = baseCenter.x - baseExtent, originZ = baseCenter.y - baseExtent;

            baseFilling = false;
            long lastKey = long.MinValue;
            Color32[] chunk = null;
            for (int y = 0; y < TexSize; y++)
            {
                float wz = originZ + (y + 0.5f) * metresPerPixel;
                int iz = Mathf.FloorToInt(wz / size);
                int cz = Mathf.FloorToInt(iz / (float)ChunkCells);
                for (int x = 0; x < TexSize; x++)
                {
                    float wx = originX + (x + 0.5f) * metresPerPixel;
                    int ix = Mathf.FloorToInt(wx / size);
                    int cx = Mathf.FloorToInt(ix / (float)ChunkCells);
                    long key = ChunkKey(size, cx, cz);
                    if (key != lastKey) { chunks.TryGetValue(key, out chunk); lastKey = key; }
                    if (chunk == null) { baseColors[y * TexSize + x] = unknown; baseFilling = true; continue; }
                    baseColors[y * TexSize + x] = chunk[(iz - cz * ChunkCells) * ChunkCells + (ix - cx * ChunkCells)];
                }
            }
        }

        // ------------------------------------------------------------------ colour cache (chunks), filled ahead of need

        /// <summary>Metres per cached grid cell: 1 m squares when zoomed in, coarser as the map zooms out.</summary>
        private static int CellSize(float metresPerPixel) => Mathf.Clamp(Mathf.RoundToInt(metresPerPixel), 1, 8);

        private static long ChunkKey(int size, int cx, int cz) => ((long)size << 52) | ((long)(cx + 1048576) << 26) | (long)(cz + 1048576);

        /// <summary>
        /// Works out the colours of the nearest chunk that is missing from the area the map may soon show (the shown area plus a
        /// margin, so the map is always drawn from colours that were ready before it needed them). One chunk a frame, so it
        /// costs a little each frame instead of a lot at once, and it fills the nearest chunks first.
        /// </summary>
        private void Prefetch(Vector2 centre)
        {
            float metresPerPixel = 2f * halfExtent / TexSize;
            int size = CellSize(metresPerPixel);
            float chunkM = ChunkCells * size;
            float reach = halfExtent * PrefetchMargin;
            int x0 = Mathf.FloorToInt((centre.x - reach) / chunkM), x1 = Mathf.FloorToInt((centre.x + reach) / chunkM);
            int z0 = Mathf.FloorToInt((centre.y - reach) / chunkM), z1 = Mathf.FloorToInt((centre.y + reach) / chunkM);

            if (chunks.Count > 6000) chunks.Clear();      // a long session / many zoom levels: start the cache over rather than grow

            int bestX = 0, bestZ = 0;
            float bestD = float.MaxValue;
            for (int cz = z0; cz <= z1; cz++)
                for (int cx = x0; cx <= x1; cx++)
                {
                    if (chunks.ContainsKey(ChunkKey(size, cx, cz))) continue;
                    float dx = (cx + 0.5f) * chunkM - centre.x, dz = (cz + 0.5f) * chunkM - centre.y;
                    float d = dx * dx + dz * dz;
                    if (d < bestD) { bestD = d; bestX = cx; bestZ = cz; }
                }
            if (bestD == float.MaxValue) return;         // everything in range is cached

            Vector3 terrainOrigin = generator != null ? generator.transform.position : Vector3.zero;
            var colours = new Color32[ChunkCells * ChunkCells];
            for (int lz = 0; lz < ChunkCells; lz++)
                for (int lx = 0; lx < ChunkCells; lx++)
                {
                    float wx = ((bestX * ChunkCells + lx) + 0.5f) * size, wz = ((bestZ * ChunkCells + lz) + 0.5f) * size;
                    colours[lz * ChunkCells + lx] = SquareColor(wx, wz, terrainOrigin);
                }
            chunks[ChunkKey(size, bestX, bestZ)] = colours;
        }

        /// <summary>Base grid + placed structures + lamp glow into the texture.</summary>
        private void Compose()
        {
            float metresPerPixel = 2f * baseExtent / TexSize;
            float originX = baseCenter.x - baseExtent, originZ = baseCenter.y - baseExtent;
            System.Array.Copy(baseColors, pixels, pixels.Length);

            foreach (PlacedObject o in PlacedObject.All)
                if (o != null) Mark(o.transform.position, originX, originZ, metresPerPixel, new Color32(40, 40, 46, 255), 1);

            foreach (LightEmitter.Glow g in LightEmitter.ActiveGlows())
                Glow(g, originX, originZ, metresPerPixel);

            tex.SetPixels32(pixels);
            tex.Apply(false);
        }

        private Color32 SquareColor(float wx, float wz, Vector3 terrainOrigin)
        {
            string zone = PlantingZone.BiomeAt(new Vector3(wx, 0f, wz));
            if (zone != null && biomeColors.TryGetValue(zone, out Color zc)) return zc;
            if (generator == null) return unknown;
            BiomeData b = generator.EvaluateBiomeAt(wx - terrainOrigin.x, wz - terrainOrigin.z);
            return b != null && biomeColors.TryGetValue(b.id, out Color c) ? (Color32)c : unknown;
        }

        private void Mark(Vector3 world, float originX, float originZ, float mpp, Color32 colour, int radiusPx)
        {
            int px = Mathf.FloorToInt((world.x - originX) / mpp), py = Mathf.FloorToInt((world.z - originZ) / mpp);
            for (int dy = -radiusPx; dy <= radiusPx; dy++)
                for (int dx = -radiusPx; dx <= radiusPx; dx++)
                {
                    int x = px + dx, y = py + dy;
                    if (x >= 0 && y >= 0 && x < TexSize && y < TexSize) pixels[y * TexSize + x] = colour;
                }
        }

        /// <summary>A lit light is shown only as a dot of its own colour where it stands (no spread over the ground).</summary>
        private void Glow(LightEmitter.Glow g, float originX, float originZ, float mpp)
        {
            Color32 off = new Color32(40, 40, 46, 255);             // the same dark mark a placed object gets when it is unlit
            Color c = Color.Lerp(new Color(off.r / 255f, off.g / 255f, off.b / 255f), g.Colour, Mathf.Clamp01(g.Level * 1.5f));
            Mark(g.Position, originX, originZ, mpp, c, 1);
        }
    }
}
