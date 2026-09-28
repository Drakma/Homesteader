using UnityEngine;
using UnityEngine.InputSystem;

namespace Homesteader.DebugTools
{
    /// <summary>
    /// F2 cycles the ground grid through 4 levels:
    ///   0 - off
    ///   1 - only the 1m cell under the mouse is outlined
    ///   2 - full grid, dim (dark gray lines)
    ///   3 - full grid, bright (white lines)
    ///
    /// Levels 2/3 drive the active Terrain material's own _GridOpacity (GenerativeTerrainURP
    /// already draws a 1m grid - see TerrainGeneratorBootstrap), since that's what's actually
    /// on screen now. The hand-built line-mesh grid below only kicks in as a fallback for a
    /// scene with no generated Terrain (it used to be the only grid, back when the ground was
    /// the old flat plane with the grid baked into T_Ground_GrassGrid's pixels).
    /// Bootstraps itself on scene load, same pattern as FpsCounter.
    /// </summary>
    public sealed class GridBrightnessToggle : MonoBehaviour
    {
        private const int LevelCount = 4;
        private const float HalfExtent = 60f; // draws a 120x120m grid centered on the origin
        private const float LineY = 0.025f;
        private int _level = 2;

        private LineRenderer _outline;
        private GameObject _gridLines;
        private MeshRenderer _gridRenderer;
        private Material _gridMaterial;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (FindAnyObjectByType<GridBrightnessToggle>() != null) return;
            var go = new GameObject("GridBrightnessToggle");
            DontDestroyOnLoad(go);
            go.AddComponent<GridBrightnessToggle>();
        }

        private void Start()
        {
            // Apply the initial level (defaults to 3 = Bright).
            ApplyLevel();
        }

        private void Update()
        {
            bool pressed = Keyboard.current != null
                ? Keyboard.current.f2Key.wasPressedThisFrame
                : Input.GetKeyDown(KeyCode.F2);

            if (pressed)
            {
                _level = (_level + 1) % LevelCount;
                ApplyLevel();
                string[] names = { "Off", "Cell under the cursor", "Dim", "Bright" };
                Homesteader.UI.ToastNotificationSystem.ShowInfo("Ground grid", names[Mathf.Clamp(_level, 0, names.Length - 1)]);
            }

            if (_level == 1) UpdateOutlinePosition();
        }

        private void ApplyLevel()
        {
            EnsureOutline();
            _outline.gameObject.SetActive(_level == 1);

            // GenerativeTerrainURP (the real Terrain's shader, since TerrainGeneratorBootstrap
            // wired one up) draws its own always-on 1m grid via _GridOpacity/_GridColor - that's
            // the grid actually on screen now, so control that directly instead of the
            // fallback custom mesh below (which nothing renders on top of any more).
            Terrain terrain = Terrain.activeTerrain;
            Material terrainMat = terrain != null ? terrain.materialTemplate : null;
            if (terrainMat != null && terrainMat.HasProperty("_GridOpacity"))
            {
                float opacity = _level switch { 2 => 0.35f, 3 => 1f, _ => 0f };
                terrainMat.SetFloat("_GridOpacity", opacity);
                return;
            }

            // Fallback for a scene with no generated Terrain: the old hand-drawn grid mesh.
            EnsureGridLines();
            bool showGrid = _level >= 2;
            _gridLines.SetActive(showGrid);
            if (showGrid)
            {
                var color = _level == 2 ? new Color(0.35f, 0.35f, 0.35f, 1f) : Color.white;
                _gridMaterial.SetColor("_BaseColor", color);
                if (_gridMaterial.HasProperty("_Color")) _gridMaterial.SetColor("_Color", color);
            }
        }

        private static Material MakeUnlitOpaqueMaterial(Color color)
        {
            var shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (shader == null) shader = Shader.Find("Unlit/Color");
            var mat = new Material(shader);
            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", color);
            if (mat.HasProperty("_Color")) mat.SetColor("_Color", color);
            return mat;
        }

        private void EnsureOutline()
        {
            if (_outline != null) return;

            var go = new GameObject("GridHoverOutline");
            _outline = go.AddComponent<LineRenderer>();
            _outline.loop = true;
            _outline.positionCount = 4;
            _outline.useWorldSpace = true;
            _outline.widthMultiplier = 0.04f;
            _outline.numCapVertices = 2;
            _outline.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _outline.receiveShadows = false;

            var color = Color.white;
            _outline.material = MakeUnlitOpaqueMaterial(color);
            _outline.startColor = color;
            _outline.endColor = color;

            go.SetActive(false);
        }

        private const float LineWidth = 0.05f; // metres

        private void EnsureGridLines()
        {
            if (_gridLines != null) return;

            _gridLines = new GameObject("GridBrightnessOverlay");
            var filter = _gridLines.AddComponent<MeshFilter>();
            _gridRenderer = _gridLines.AddComponent<MeshRenderer>();
            _gridRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _gridRenderer.receiveShadows = false;

            _gridMaterial = MakeUnlitOpaqueMaterial(Color.white);
            _gridRenderer.material = _gridMaterial;

            // Each line is a thin quad (2 triangles), not a MeshTopology.Lines segment -
            // GPU "hardware lines" are always 1px and always jagged with no AA. Quads
            // rasterize like any other triangle and anti-alias normally.
            int extent = Mathf.RoundToInt(HalfExtent);
            int lineCount = (extent * 2 + 1) * 2; // both directions
            var vertices = new Vector3[lineCount * 4];
            var triangles = new int[lineCount * 6];
            float half = LineWidth * 0.5f;

            int vi = 0, ti = 0;
            for (int i = -extent; i <= extent; i++)
            {
                // Line of constant X, spanning Z: quad extends in X by the line width.
                AddQuad(vertices, triangles, ref vi, ref ti,
                    new Vector3(i - half, LineY, -HalfExtent), new Vector3(i + half, LineY, -HalfExtent),
                    new Vector3(i + half, LineY, HalfExtent), new Vector3(i - half, LineY, HalfExtent));

                // Line of constant Z, spanning X: quad extends in Z by the line width.
                AddQuad(vertices, triangles, ref vi, ref ti,
                    new Vector3(-HalfExtent, LineY, i - half), new Vector3(HalfExtent, LineY, i - half),
                    new Vector3(HalfExtent, LineY, i + half), new Vector3(-HalfExtent, LineY, i + half));
            }

            var mesh = new Mesh { indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.vertices = vertices;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();
            filter.mesh = mesh;

            _gridLines.SetActive(false);
        }

        private static void AddQuad(Vector3[] vertices, int[] triangles, ref int vi, ref int ti,
            Vector3 a, Vector3 b, Vector3 c, Vector3 d)
        {
            vertices[vi] = a; vertices[vi + 1] = b; vertices[vi + 2] = c; vertices[vi + 3] = d;
            triangles[ti] = vi; triangles[ti + 1] = vi + 1; triangles[ti + 2] = vi + 2;
            triangles[ti + 3] = vi; triangles[ti + 4] = vi + 2; triangles[ti + 5] = vi + 3;
            vi += 4;
            ti += 6;
        }

        private void UpdateOutlinePosition()
        {
            var cam = Camera.main;
            if (cam == null)
            {
                var iso = FindAnyObjectByType<IsometricLockedCamera>();
                if (iso != null) cam = iso.GetComponent<Camera>();
            }
            if (cam == null) return;

            Vector2 mousePos = Mouse.current != null ? Mouse.current.position.ReadValue() : (Vector2)Input.mousePosition;
            Ray ray = cam.ScreenPointToRay(mousePos);

            Vector3 hit;
            // Follow the real (rolling, non-flat) terrain surface height, not a flat y=0 plane -
            // otherwise the outline is buried under hills or floats above valleys almost
            // everywhere except right at y=0.
            Terrain terrain = Terrain.activeTerrain;
            if (terrain != null && Physics.Raycast(ray, out RaycastHit rayHit, 2000f))
            {
                hit = rayHit.point;
            }
            else
            {
                var groundPlane = new Plane(Vector3.up, Vector3.zero);
                if (!groundPlane.Raycast(ray, out float enter)) return;
                hit = ray.GetPoint(enter);
            }

            float x0 = Mathf.Floor(hit.x);
            float z0 = Mathf.Floor(hit.z);
            float y0 = Homesteader.Generation.TerrainHeightDetector.GetGroundY(x0, z0);
            float y1 = Homesteader.Generation.TerrainHeightDetector.GetGroundY(x0 + 1f, z0);
            float y2 = Homesteader.Generation.TerrainHeightDetector.GetGroundY(x0 + 1f, z0 + 1f);
            float y3 = Homesteader.Generation.TerrainHeightDetector.GetGroundY(x0, z0 + 1f);
            const float skin = 0.03f; // lift slightly off the surface to avoid z-fighting

            _outline.SetPosition(0, new Vector3(x0, y0 + skin, z0));
            _outline.SetPosition(1, new Vector3(x0 + 1f, y1 + skin, z0));
            _outline.SetPosition(2, new Vector3(x0 + 1f, y2 + skin, z0 + 1f));
            _outline.SetPosition(3, new Vector3(x0, y3 + skin, z0 + 1f));
        }
    }
}
