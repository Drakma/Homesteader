using UnityEngine;

namespace Homesteader.Animals
{
    /// <summary>
    /// Kinematic ground mover for animals: turns toward a point, walks at a speed, hugs the terrain,
    /// refuses steep slopes, and sidesteps simple obstacles. No NavMesh needed (the world is generated at
    /// runtime). Swap this class for a NavMesh version later without touching the AI rules.
    /// </summary>
    public sealed class AnimalMover : MonoBehaviour
    {
        [System.NonSerialized] public MovementDef Def = new MovementDef();
        public float Radius = 0.3f;
        public LayerMask obstacleMask = ~0;

        /// <summary>Metres per second the animal actually moved last frame.</summary>
        public float CurrentSpeed { get; private set; }

        /// <summary>True when the last MoveToward could not make progress (steep slope or blocked).</summary>
        public bool Blocked { get; private set; }

        private float blockedTime;
        private float lastMoveTime = -10f;
        private float altitude;           // air: current height above the ground
        private float avoidSign = 1f;

        public float BlockedSeconds => blockedTime;

        /// <summary>Snaps the animal onto the ground under it.</summary>
        public void SnapToGround()
        {
            Vector3 p = transform.position;
            p.y = LevelY(p);
            transform.position = p;
        }

        /// <summary>Surface height of the water in world space.</summary>
        public static float WaterY()
        {
            return Homesteader.Generation.TerrainHeightDetector.GetWaterY();
        }

        private bool Water => Def.Medium == "water";
        private bool Air => Def.Medium == "air";

        /// <summary>The height this animal stands / floats / flies at over p.</summary>
        private float LevelY(Vector3 p)
        {
            float g = GroundY(p);
            if (Water) return Mathf.Clamp(WaterY() - Def.DepthM, g + 0.1f, WaterY() - 0.1f);
            if (Air) return g + altitude;
            return g;
        }

        private void Update()
        {
            if (!Air && !Water) return;
            if (Air)
            {
                bool moving = Time.time - lastMoveTime < 0.25f;
                altitude = Mathf.MoveTowards(altitude, moving ? Def.HoverM : 0f, 2.5f * Time.deltaTime);
            }
            Vector3 p = transform.position;
            p.y = Mathf.MoveTowards(p.y, LevelY(p), 3f * Time.deltaTime);
            transform.position = p;
        }

        public static float GroundY(Vector3 p)
        {
            return Homesteader.Generation.TerrainHeightDetector.GetGroundY(p);
        }

        /// <summary>Slope in degrees of the ground at p (finite difference, 1 m).</summary>
        public static float SlopeAt(Vector3 p)
        {
            float h = GroundY(p);
            float dx = GroundY(p + Vector3.right) - h;
            float dz = GroundY(p + Vector3.forward) - h;
            return Mathf.Atan(Mathf.Sqrt(dx * dx + dz * dz)) * Mathf.Rad2Deg;
        }

        /// <summary>Moves toward target at speed (m/s). Returns the remaining flat distance.</summary>
        public float MoveToward(Vector3 target, float speed, float dt)
        {
            Vector3 pos = transform.position;
            Vector3 to = target - pos;
            to.y = 0f;
            float dist = to.magnitude;
            if (dist < 0.01f) { CurrentSpeed = 0f; return dist; }

            Vector3 dir = to / dist;
            if (!Air) dir = Avoid(pos, dir);
            lastMoveTime = Time.time;

            // Turn first; only walk once roughly facing the way we are going.
            Quaternion want = Quaternion.LookRotation(dir, Vector3.up);
            transform.rotation = Quaternion.RotateTowards(transform.rotation, want, Def.TurnSpeedDeg * dt);
            float facing = Vector3.Angle(transform.forward, dir);
            float go = facing > 70f ? 0f : Mathf.Clamp01(1f - facing / 90f);

            float step = Mathf.Min(speed * go * dt, dist);
            Vector3 next = pos + transform.forward * step;
            bool cannotGo = Water ? GroundY(next) > WaterY() - 0.2f          // fish stay in the water
                          : (!Air && SlopeAt(next) > Def.MaxSlopeDeg);
            if (step > 0f && cannotGo)
            {
                Block(dt);
                CurrentSpeed = 0f;
                return dist;
            }

            next.y = (Air || Water) ? pos.y : GroundY(next);   // air / water heights are eased in Update
            CurrentSpeed = dt > 0f ? step / dt : 0f;
            if (step < 0.0001f && facing <= 70f) Block(dt); else Unblock();
            transform.position = next;
            return Mathf.Max(0f, dist - step);
        }

        /// <summary>Turns in place toward a point without moving.</summary>
        public void FaceToward(Vector3 target, float dt)
        {
            Vector3 to = target - transform.position;
            to.y = 0f;
            if (to.sqrMagnitude < 0.0001f) return;
            transform.rotation = Quaternion.RotateTowards(transform.rotation,
                Quaternion.LookRotation(to.normalized, Vector3.up), Def.TurnSpeedDeg * dt);
        }

        public void Stop() { CurrentSpeed = 0f; }

        private Vector3 Avoid(Vector3 pos, Vector3 dir)
        {
            Vector3 origin = pos + Vector3.up * 0.35f;
            if (!Physics.SphereCast(origin, Radius, dir, out RaycastHit hit, 1.0f, obstacleMask, QueryTriggerInteraction.Ignore))
                return dir;
            if (hit.collider is TerrainCollider || hit.collider.transform.IsChildOf(transform)) return dir;

            // Blocked ahead: try left and right of the line, take the free side (and remember it).
            for (int i = 1; i <= 3; i++)
            {
                float a = 35f * i * avoidSign;
                Vector3 alt = Quaternion.Euler(0f, a, 0f) * dir;
                if (!Physics.SphereCast(origin, Radius, alt, out _, 1.0f, obstacleMask, QueryTriggerInteraction.Ignore)) return alt;
                alt = Quaternion.Euler(0f, -a, 0f) * dir;
                if (!Physics.SphereCast(origin, Radius, alt, out _, 1.0f, obstacleMask, QueryTriggerInteraction.Ignore))
                { avoidSign = -avoidSign; return alt; }
            }
            return dir;
        }

        private void Block(float dt) { Blocked = true; blockedTime += dt; }
        private void Unblock() { Blocked = false; blockedTime = 0f; }
    }
}
