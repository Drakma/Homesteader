using UnityEngine;

namespace Homesteader.Generation
{
    /// <summary>
    /// Centralised terrain height detection. Every system that needs to place
    /// something on the ground — planted crops, placed structures, dropped
    /// items, spawned animals, zone decals — should call <see cref="GetGroundY"/>
    /// or <see cref="PlaceOnGround"/> instead of doing its own raycast or
    /// SampleHeight call.
    ///
    /// This replaces the scattered duplicate GroundY() methods that lived in
    /// PlacementController, AnimalMover, and GridBrightnessToggle, and the
    /// ad-hoc physics raycasts in WorldItem and GameRules zone creation.
    ///
    /// The detector tries the active Terrain first (fast, sample-based, no
    /// physics), then falls back to a downward physics raycast for non-terrain
    /// ground (the flat "Ground" plane, or any collider tagged as ground).
    /// </summary>
    public static class TerrainHeightDetector
    {
        /// <summary>
        /// How far above the terrain surface to lift an object so it sits
        /// "just on" the ground rather than clipping into it. 5 mm is enough
        /// to prevent z-fighting on flat ground while keeping the object
        /// visually grounded on slopes.
        /// </summary>
        public const float SurfaceOffset = 0.005f;

        /// <summary>
        /// Returns the world-space Y of the ground surface at (x, z).
        /// Uses Terrain.SampleHeight when a terrain exists (fast, no physics);
        /// otherwise falls back to a downward raycast.
        /// Returns 0 if no ground is found.
        /// </summary>
        public static float GetGroundY(float x, float z)
        {
            return GetGroundY(new Vector3(x, 0f, z));
        }

        /// <summary>
        /// Returns the world-space Y of the ground surface at the given
        /// world position (only x and z are used; y is ignored).
        /// Uses Terrain.SampleHeight when a terrain exists (fast, no physics);
        /// otherwise falls back to a downward raycast.
        /// </summary>
        public static float GetGroundY(Vector3 worldPos)
        {
            Terrain t = Terrain.activeTerrain;
            if (t != null)
            {
                // SampleHeight returns terrain-local Y; add the terrain's
                // world Y offset (the terrain sits at Y=-14 so its flat
                // baseline lands at world Y=0).
                return t.SampleHeight(worldPos) + t.transform.position.y;
            }

            // No terrain: raycast down from high above.
            if (Physics.Raycast(
                new Vector3(worldPos.x, 1000f, worldPos.z),
                Vector3.down,
                out RaycastHit hit,
                2000f))
            {
                return hit.point.y;
            }

            return 0f;
        }

        /// <summary>
        /// Returns the ground Y at (x, z) plus <see cref="SurfaceOffset"/>,
        /// so the object sits just above the surface. This is what most
        /// placement code should use.
        /// </summary>
        public static float GetSurfaceY(float x, float z)
        {
            return GetGroundY(x, z) + SurfaceOffset;
        }

        /// <summary>
        /// Returns the ground Y at the given position plus
        /// <see cref="SurfaceOffset"/>, so the object sits just above the
        /// surface.
        /// </summary>
        public static float GetSurfaceY(Vector3 worldPos)
        {
            return GetGroundY(worldPos) + SurfaceOffset;
        }

        /// <summary>
        /// Sets the Y of <paramref name="position"/> to the ground surface
        /// height at its (x, z), plus <see cref="SurfaceOffset"/>.
        /// Returns the modified position.
        /// </summary>
        public static Vector3 PlaceOnGround(Vector3 position)
        {
            position.y = GetSurfaceY(position);
            return position;
        }

        /// <summary>
        /// Sets the Y of <paramref name="position"/> to the ground surface
        /// height at its (x, z), plus an explicit offset (use 0 for exact
        /// surface, or a positive value to lift further).
        /// </summary>
        public static Vector3 PlaceOnGround(Vector3 position, float offset)
        {
            position.y = GetGroundY(position) + offset;
            return position;
        }

        /// <summary>
        /// Sets the transform's Y to the ground surface height at its
        /// current (x, z), plus <see cref="SurfaceOffset"/>.
        /// </summary>
        public static void SnapToGround(Transform transform)
        {
            Vector3 p = transform.position;
            p.y = GetSurfaceY(p);
            transform.position = p;
        }

        /// <summary>
        /// Sets the transform's Y to the ground surface height at its
        /// current (x, z), plus an explicit offset.
        /// </summary>
        public static void SnapToGround(Transform transform, float offset)
        {
            Vector3 p = transform.position;
            p.y = GetGroundY(p) + offset;
            transform.position = p;
        }

        /// <summary>
        /// Returns the slope angle in degrees at the given position,
        /// using a 1-metre finite difference on the terrain height.
        /// </summary>
        public static float GetSlopeDegrees(Vector3 worldPos)
        {
            float h = GetGroundY(worldPos);
            float dx = GetGroundY(worldPos + Vector3.right) - h;
            float dz = GetGroundY(worldPos + Vector3.forward) - h;
            return Mathf.Atan(Mathf.Sqrt(dx * dx + dz * dz)) * Mathf.Rad2Deg;
        }

        /// <summary>
        /// Returns the world-space Y of the water surface (the terrain
        /// generator's water level + terrain Y offset).
        /// </summary>
        public static float GetWaterY()
        {
            Terrain t = Terrain.activeTerrain;
            return HomesteaderTerrainGenerator.WaterLevel + (t != null ? t.transform.position.y : 0f);
        }
    }
}
