using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// Works out how a wire between two wall-mounted devices is tacked to the walls (docs/WIRING.md). Everything on a wall is mounted at about the same height, so the wire leaves the first device
    /// and runs at that height along the walls with square corners: straight along one wall, or from wall to wall round the corners of the room (or of the building, outside), the shorter way.
    /// Where it meets a window it dips UNDER it, where it meets a door it goes OVER it, with right-angle jogs. Both devices have to be on the same side of the walls (both inside or both outside);
    /// anything else (a panel on the ground, a roof mount) is drawn as the plain sagging wire. All of it is worked out in the building's own space; the result is world points.
    /// </summary>
    public static class WireRouter
    {
        private const float Off = 0.012f;      // the wire lies this far off the wall
        private static float Clear = 0.07f;     // how far it keeps from a window or a door (inside; outside it is OutsideClear: the conduit is thicker and sits proud of the wall)
        private const float OutsideClear = 0.12f;

        private struct Opening
        {
            public bool Door;
            public Vector3 Min, Max;           // in the building's own space
        }

        /// <summary>The wire's path in world points, or null when it cannot be tacked to the walls (yet: the building's model may still be loading).</summary>
        public static List<Vector3> Route(WireNode a, WireNode b, out bool outside, out bool buried)
        {
            buried = false;
            outside = false;
            string pipeKind = a != null && b != null ? WireNetwork.KindFor(a.Role, b.Role) : null;
            if (pipeKind == "net")
            {
                // Cat6 OUTSIDE is run like a wire (inside a building it is in the walls and not drawn: NetInWalls): a dish or antenna on the roof along the
                // eave and down the wall to the jack (as a panel's run); two things on one building's outside walls along the walls (below); a long run
                // between buildings buried (the AC block below)
                AttachedObject ma = a.GetComponent<AttachedObject>(), mb = b.GetComponent<AttachedObject>();
                if (ma != null && ma.Surface == "roof" && mb != null && mb.Surface == "wall") return RouteFromPanel(a, b, out outside);
                if (mb != null && mb.Surface == "roof" && ma != null && ma.Surface == "wall") return RouteFromPanel(b, a, out outside);
            }
            if (pipeKind == "water" || pipeKind == "sewer")   // a sewer line is laid the same way
            {
                // a water line is laid like a wire: along the walls when both ends are mounted on the same side of one building's walls (the usual run below),
                // otherwise underground when it is long, coming up at each end, or a short pipe straight across (filter to filter, tank to tank in the pump house)
                AttachedObject wa = a.GetComponent<AttachedObject>(), wb = b.GetComponent<AttachedObject>();
                ConstructionSite ia = BuildingInside(a), ib = BuildingInside(b);
                // a building's water inlet goes through the wall: to something inside its building the pipe leaves its INSIDE valve
                if ((a.Role == WireRole.WaterInlet || a.Role == WireRole.SewerOutlet) && wa != null && ib != null && ib == wa.Site) ia = ib;
                if ((b.Role == WireRole.WaterInlet || b.Role == WireRole.SewerOutlet) && wb != null && ia != null && ia == wb.Site) ib = ia;
                bool bothInside = ia != null && ia == ib;
                if (!bothInside || wa == null || wb == null || wa.Site != wb.Site)
                {
                    Vector3 wpa = a.PortToward(b.BasePort), wpb = b.PortToward(a.BasePort);
                    // inside one building (pumps, filters, tanks, the water heater in the pump house): out to the nearest wall, along the walls like a wire, and back out
                    // to the other end (two parts standing side by side: a short pipe straight across)
                    if (bothInside) return RouteInside(ia, a, b, wpa, wpb) ?? new List<Vector3> { wpa, wpb };
                    // anything outside goes UNDERGROUND, coming up out of the ground at each end (at a building's water inlet: up the wall into its riser)
                    outside = true;
                    buried = true;
                    return RouteBuried(wpa, wpb);
                }
            }
            if (a != null && b != null && (WireNetwork.KindFor(a.Role, b.Role) == "propane" || WireNetwork.KindFor(a.Role, b.Role) == "fuel"))   // (a fuel line the same)
            {
                // a propane line: along the walls when both ends are on the same side of one building's walls (the usual run below), otherwise underground, coming up at each end
                AttachedObject pa1 = a.GetComponent<AttachedObject>(), pb1 = b.GetComponent<AttachedObject>();
                if (pa1 == null || pb1 == null || pa1.Site == null || pa1.Site != pb1.Site)
                {
                    outside = true;
                    buried = true;
                    return RouteBuried(a.PortToward(b.BasePort), b.PortToward(a.BasePort));
                }
            }
            if (a != null && b != null && a.Role != WireRole.WindTurbine && b.Role != WireRole.WindTurbine && a.Role != WireRole.StandbyGenerator && b.Role != WireRole.StandbyGenerator && (WireNetwork.KindFor(a.Role, b.Role) == "ac" || WireNetwork.KindFor(a.Role, b.Role) == "net"))   // (a long Cat6 run between buildings is buried the same way)
            {
                // a long AC run (to another building, across a yard): the cable is buried, and a larger conduit rises out of the ground to the bottom of each device. A short one is tacked to the walls as usual.
                Vector3 pa0 = a.PortToward(b.BasePort), pb0 = b.PortToward(a.BasePort);
                if (Vector3.Distance(pa0, pb0) > WireNetwork.MaxSpan && !Net.SameBuilding(a, b))   // (network gear in one building is cabled above ground)
                {
                    outside = true;
                    buried = true;
                    return RouteBuried(pa0, pb0);
                }
            }
            if (a != null && b != null && (a.Role == WireRole.SolarPanel || b.Role == WireRole.SolarPanel))
            {
                // a long run of outdoor DC wire to a panel (a ground rack out in the yard): buried, coming up in conduit at each end, like a long AC run
                Vector3 ps0 = a.PortToward(b.BasePort), ps1 = b.PortToward(a.BasePort);
                if (Vector3.Distance(ps0, ps1) > WireNetwork.MaxSpan)
                {
                    outside = true;
                    buried = true;
                    return RouteBuried(ps0, ps1);
                }
            }
            if (a != null && b != null && (a.Role == WireRole.WindTurbine || b.Role == WireRole.WindTurbine || a.Role == WireRole.StandbyGenerator || b.Role == WireRole.StandbyGenerator)) buried = true;
            if (a != null && b != null)
            {
                if (a.Role == WireRole.WindTurbine && b.Role == WireRole.AcPanel) return RouteWind(b, out outside);
                if (b.Role == WireRole.WindTurbine && a.Role == WireRole.AcPanel) return RouteWind(a, out outside);
                // a standby generator to its lockout box: wired like a breaker box fed from a turbine: buried, the larger conduit coming up out of the ground
                // to the bottom of the box (and up into the generator at the other end)
                if ((a.Role == WireRole.StandbyGenerator && b.Role == WireRole.Lockout) || (b.Role == WireRole.StandbyGenerator && a.Role == WireRole.Lockout))
                {
                    outside = true;
                    return RouteBuried(a.PortToward(b.BasePort), b.PortToward(a.BasePort));
                }
                if (a.Role == WireRole.SolarPanel && b.Role != WireRole.SolarPanel) return RouteFromPanel(a, b, out outside);
                if (b.Role == WireRole.SolarPanel && a.Role != WireRole.SolarPanel) return RouteFromPanel(b, a, out outside);
            }
            AttachedObject aa = a != null ? a.GetComponent<AttachedObject>() : null;
            AttachedObject ab = b != null ? b.GetComponent<AttachedObject>() : null;
            if (aa == null || ab == null || aa.Site == null || aa.Site != ab.Site) return null;
            if (aa.Surface != "wall" || ab.Surface != "wall") return null;
            ConstructionSite site = aa.Site;
            if (site.VisualRoot == null) return null;

            Vector3 pa = a.PortToward(b.BasePort), pb = b.PortToward(a.BasePort);
            Vector3 na = Facing(a, pa), nb = Facing(b, pb);
            bool insideA = site.IsInsideWalls(pa + na * 0.15f), insideB = site.IsInsideWalls(pb + nb * 0.15f);
            if (insideA != insideB) return null;                              // one inside, one outside: not a run along the walls
            outside = !insideA;                                               // outside the building the wire runs in conduit
            Clear = insideA ? 0.07f : OutsideClear;                           // and keeps about 5 cm further from a window (its sides and bottom) for the conduit

            Rect wall = site.WallRect();
            float thick = aa.Thickness > 0.05f ? aa.Thickness : AttachedObject.MeasureWall(site, pa, na);
            thick = Mathf.Clamp(thick, 0.08f, 0.6f);
            // the plane the wire lies on: the inner face of the walls (the rectangle shrunk by their thickness) or the outer face
            Rect run = insideA ? Rect.MinMaxRect(wall.xMin + thick - Off, wall.yMin + thick - Off, wall.xMax - thick + Off, wall.yMax - thick + Off)
                               : Rect.MinMaxRect(wall.xMin - Off, wall.yMin - Off, wall.xMax + Off, wall.yMax + Off);
            if (run.width < 0.3f || run.height < 0.3f) return null;

            Quaternion inv = Quaternion.Inverse(site.transform.rotation);
            Vector3 la = inv * (pa - site.transform.position), lb = inv * (pb - site.transform.position);
            float h = la.y;
            // each device is mounted ON its wall's surface: that, not a thickness guessed from the outline, says where the face is (a wire that sat inside the wall was hidden by it)
            run = Snap(run, EdgeOf(run, la.x, la.z), inv * (Anchor(a, pa) - site.transform.position), insideA);
            run = Snap(run, EdgeOf(run, lb.x, lb.z), inv * (Anchor(b, pb) - site.transform.position), insideA);

            Project(run, la.x, la.z, out float sa, out Vector2 qa);
            Project(run, lb.x, lb.z, out float sb, out Vector2 qb);

            // the path in the building's space: out of the first device to the wall, round the corners at one height, to the second device
            var pts = new List<Vector3>();
            pts.Add(la);
            pts.Add(new Vector3(qa.x, h, qa.y));
            foreach (Vector2 c in CornersBetween(run, sa, sb)) pts.Add(new Vector3(c.x, h, c.y));
            pts.Add(new Vector3(qb.x, h, qb.y));
            if (Mathf.Abs(lb.y - h) > 0.01f) pts.Add(new Vector3(qb.x, lb.y, qb.y));   // up or down to the second device
            pts.Add(lb);
            pts = Compact(pts);

            List<Opening> openings = Openings(site, inv);
            pts = Detour(pts, openings, run);

            var world = new List<Vector3>(pts.Count);
            foreach (Vector3 p in pts) world.Add(site.transform.position + site.transform.rotation * p);
            return world;
        }

        /// <summary>
        /// A pipe between two parts inside one building, at least one of them standing on the floor (a pump, a filter, a tank): out from the first part to the nearest wall,
        /// along the inner face of the walls round the corners (the shorter way, under windows and over doors), and back out to the second part. At the height of the higher
        /// end, so it never runs along the floor. Null when the building's walls are not known yet.
        /// </summary>
        private static List<Vector3> RouteInside(ConstructionSite site, WireNode a, WireNode b, Vector3 pa, Vector3 pb)
        {
            if (site == null || site.VisualRoot == null) return null;
            if (Vector3.Distance(new Vector3(pa.x, 0f, pa.z), new Vector3(pb.x, 0f, pb.z)) < 0.9f) return null;   // side by side: straight across
            Rect wall = site.WallRect();
            Quaternion inv = Quaternion.Inverse(site.transform.rotation);
            Vector3 la = inv * (pa - site.transform.position), lb = inv * (pb - site.transform.position);
            // how thick the walls are: an end mounted on a wall knows; otherwise measure the wall nearest the first part
            AttachedObject at = a.GetComponent<AttachedObject>();
            if (at == null) at = b.GetComponent<AttachedObject>();
            float thick = at != null && at.Thickness > 0.05f ? at.Thickness : 0f;
            if (thick <= 0f)
            {
                Project(wall, la.x, la.z, out float _, out Vector2 q0);
                Vector3 n = Mathf.Abs(q0.x - wall.xMin) < 0.01f ? Vector3.left : Mathf.Abs(q0.x - wall.xMax) < 0.01f ? Vector3.right
                          : Mathf.Abs(q0.y - wall.yMin) < 0.01f ? Vector3.back : Vector3.forward;
                Vector3 face = site.transform.position + site.transform.rotation * new Vector3(q0.x, la.y + 0.5f, q0.y);
                thick = AttachedObject.MeasureWall(site, face, site.transform.rotation * n);
            }
            thick = Mathf.Clamp(thick, 0.08f, 0.6f);
            Rect run = Rect.MinMaxRect(wall.xMin + thick + 0.03f, wall.yMin + thick + 0.03f, wall.xMax - thick - 0.03f, wall.yMax - thick - 0.03f);   // the pipe is thicker than a wire: it stands off the wall by its radius
            if (run.width < 0.3f || run.height < 0.3f) return null;
            float h = Mathf.Max(la.y, lb.y);
            Project(run, la.x, la.z, out float sa, out Vector2 qa);
            Project(run, lb.x, lb.z, out float sb, out Vector2 qb);
            var pts = new List<Vector3> { la };
            if (Mathf.Abs(la.y - h) > 0.01f) pts.Add(new Vector3(la.x, h, la.z));   // up out of the part to the run's height
            pts.Add(new Vector3(qa.x, h, qa.y));
            foreach (Vector2 c in CornersBetween(run, sa, sb)) pts.Add(new Vector3(c.x, h, c.y));
            pts.Add(new Vector3(qb.x, h, qb.y));
            if (Mathf.Abs(lb.y - h) > 0.01f) pts.Add(new Vector3(lb.x, h, lb.z));
            pts.Add(lb);
            pts = Compact(pts);
            float keep = Clear;
            Clear = 0.07f;
            pts = Detour(pts, Openings(site, inv), run);
            Clear = keep;
            var world = new List<Vector3>(pts.Count);
            foreach (Vector3 p in pts) world.Add(site.transform.position + site.transform.rotation * p);
            return world;
        }

        /// <summary>
        /// A solar panel (on a roof or on the ground) to a device on the OUTSIDE of a wall (the wall entry): across to the nearest point of the building's outline at the panel's own height
        /// (along the eave or the ground), straight down or up the wall to the device's height, then tacked along the walls as any other run. All of it outside, so all of it in conduit.
        /// </summary>
        private static List<Vector3> RouteFromPanel(WireNode panel, WireNode dev, out bool outside)
        {
            outside = true;
            AttachedObject ad = dev.GetComponent<AttachedObject>();
            if (ad == null || ad.Site == null || ad.Surface != "wall") return null;
            ConstructionSite site = ad.Site;
            if (site.VisualRoot == null) return null;

            Vector3 pd = dev.PortToward(panel.BasePort);
            Vector3 nd = Facing(dev, pd);
            if (dev.Role == WireRole.WallEntry)
            {
                // a wall entry has a plate on each side of the wall: the run from a panel outside goes to the OUTSIDE plate, whichever is nearer
                bool found = false;
                foreach (Transform c in dev.GetComponentsInChildren<Transform>())
                {
                    if (!c.name.StartsWith("Plate")) continue;
                    Vector3 f = c.forward;
                    f.y = 0f;
                    if (f.sqrMagnitude < 1e-4f) continue;
                    f.Normalize();
                    if (site.IsInsideWalls(c.position + f * 0.15f)) continue;
                    pd = c.position + Vector3.up * 0.08f;
                    nd = f;
                    found = true;
                    break;
                }
                if (!found) return null;
            }
            if (site.IsInsideWalls(pd + nd * 0.15f)) return null;            // a device inside the walls: not an outdoor run

            Clear = OutsideClear;                                             // a run outside: conduit, kept 5 cm further from the windows
            Rect wall = site.WallRect();
            float thick = ad.Thickness > 0.05f ? ad.Thickness : AttachedObject.MeasureWall(site, pd, nd);
            thick = Mathf.Clamp(thick, 0.08f, 0.6f);
            Rect run = Rect.MinMaxRect(wall.xMin - Off, wall.yMin - Off, wall.xMax + Off, wall.yMax + Off);
            if (run.width < 0.3f || run.height < 0.3f) return null;

            Quaternion inv = Quaternion.Inverse(site.transform.rotation);
            Vector3 ld = inv * (pd - site.transform.position);
            Vector3 lp = inv * (panel.PortToward(dev.BasePort) - site.transform.position);
            float h = ld.y;
            run = Snap(run, EdgeOf(run, ld.x, ld.z), inv * (Anchor(dev, pd) - site.transform.position), false);

            Project(run, lp.x, lp.z, out float sp, out Vector2 qp);
            Project(run, ld.x, ld.z, out float sd, out Vector2 qd);
            // the drop down (or up) the wall must not cross a window or a door: move it along the wall to the clear side of any it would meet
            List<Opening> openings = Openings(site, inv);
            qp = AvoidOpenings(qp, EdgeOf(run, qp.x, qp.y), lp.y, h, openings, run);
            Project(run, qp.x, qp.y, out sp, out qp);

            var pts = new List<Vector3>();
            pts.Add(lp);
            pts.Add(new Vector3(qp.x, lp.y, qp.y));                         // across to the wall at the panel's height
            pts.Add(new Vector3(qp.x, h, qp.y));                            // down (or up) the wall to the device's height
            foreach (Vector2 c in CornersBetween(run, sp, sd)) pts.Add(new Vector3(c.x, h, c.y));
            pts.Add(new Vector3(qd.x, h, qd.y));
            pts.Add(ld);
            pts = Compact(pts);
            pts = Detour(pts, openings, run);

            var world = new List<Vector3>(pts.Count);
            foreach (Vector3 p in pts) world.Add(site.transform.position + site.transform.rotation * p);
            return world;
        }

        /// <summary>
        /// A wind turbine's cable is BURIED: all that shows is a larger galvanized conduit coming up out of the ground (or the floor, for a panel indoors) to the bottom of the panel it feeds.
        /// </summary>
        private static List<Vector3> RouteWind(WireNode panel, out bool outside)
        {
            outside = true;
            Vector3 port = panel.PortToward(panel.BasePort + Vector3.down);   // the bottom edge of the panel
            Vector3 from = port + Vector3.down * 0.02f;
            return new List<Vector3> { new Vector3(port.x, GroundBelow(port) - 0.15f, port.z), from };
        }

        /// <summary>A Cat6 cable between two things INSIDE one building (or to its wall jack from inside): it is in the walls, not drawn. Outside it is routed.</summary>
        public static bool NetInWalls(WireLink l)
        {
            if (l == null || l.Kind != "net" || !Net.SameBuilding(l.A, l.B)) return false;
            return Inner(l.A) && Inner(l.B);
        }

        private static bool Inner(WireNode n)
        {
            if (n.Role == WireRole.NetJack) return true;   // a wall jack is on both sides: its inside face
            AttachedObject at = n.GetComponent<AttachedObject>();
            if (at != null) return !at.Exterior && at.Surface != "roof";
            return WireNetwork.SiteAround(n) != null;
        }

        /// <summary>What is under a point: the ground, or the floor of a building (not the device itself, the player or what is mounted).</summary>
        private static float GroundBelow(Vector3 port)
        {
            float groundY = port.y - 1.2f;
            RaycastHit[] hits = Physics.RaycastAll(port + Vector3.down * 0.05f, Vector3.down, 6f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(hits, (x, y) => x.distance.CompareTo(y.distance));
            foreach (RaycastHit h in hits)
            {
                if (h.collider.GetComponentInParent<PedController>() != null || h.collider.GetComponentInParent<AttachedObject>() != null) continue;
                groundY = h.point.y;
                break;
            }
            return groundY;
        }

        /// <summary>A buried run between two devices: down into the ground below the first one, under the terrain (following it, 0.4 m down) to the second, and up out of the ground to it.</summary>
        private static List<Vector3> RouteBuried(Vector3 pa, Vector3 pb)
        {
            float ga = GroundBelow(pa), gb = GroundBelow(pb);
            var pts = new List<Vector3> { pa, new Vector3(pa.x, ga - 0.15f, pa.z) };
            float dist = new Vector2(pb.x - pa.x, pb.z - pa.z).magnitude;
            int steps = Mathf.Max(1, Mathf.CeilToInt(dist / 3f));
            for (int i = 1; i < steps; i++)
            {
                float t = i / (float)steps;
                float x = Mathf.Lerp(pa.x, pb.x, t), z = Mathf.Lerp(pa.z, pb.z, t);
                float y = Homesteader.Generation.TerrainHeightDetector.GetSurfaceY(new Vector3(x, 0f, z)) - 0.4f;
                pts.Add(new Vector3(x, Mathf.Min(y, Mathf.Lerp(ga, gb, t) - 0.15f), z));
            }
            pts.Add(new Vector3(pb.x, gb - 0.15f, pb.z));
            pts.Add(pb);
            return pts;
        }

        /// <summary>Moves a point on the outline of the walls along its wall until a vertical run from height yFrom to yTo there crosses no window or door (with a margin).</summary>
        private static Vector2 AvoidOpenings(Vector2 q, int edge, float yFrom, float yTo, List<Opening> openings, Rect run)
        {
            bool alongX = edge == 0 || edge == 2;
            float u = alongX ? q.x : q.y, line = alongX ? q.y : q.x;
            float lo = Mathf.Min(yFrom, yTo), hi = Mathf.Max(yFrom, yTo);
            float uMin = (alongX ? run.xMin : run.yMin) + 0.1f, uMax = (alongX ? run.xMax : run.yMax) - 0.1f;
            for (int guard = 0; guard < 8; guard++)
            {
                bool moved = false;
                foreach (Opening op in openings)
                {
                    float perp = alongX ? (op.Min.z + op.Max.z) * 0.5f : (op.Min.x + op.Max.x) * 0.5f;
                    if (Mathf.Abs(perp - line) > 0.5f) continue;                                  // not in this wall
                    if (op.Max.y + Clear * 0.5f < lo || op.Min.y - Clear * 0.5f > hi) continue;   // the run is above or below it
                    float a0 = (alongX ? op.Min.x : op.Min.z) - Clear, a1 = (alongX ? op.Max.x : op.Max.z) + Clear;
                    if (u < a0 || u > a1) continue;
                    u = (u - a0 < a1 - u) ? a0 : a1;
                    u = Mathf.Clamp(u, uMin, uMax);
                    moved = true;
                }
                if (!moved) break;
            }
            return alongX ? new Vector2(u, q.y) : new Vector2(q.x, u);
        }

        /// <summary>The building a water device is INSIDE (placed in it, or mounted on the inside of its wall), or null when it is outside.</summary>
        private static ConstructionSite BuildingInside(WireNode n)
        {
            AttachedObject at = n.GetComponent<AttachedObject>();
            if (at != null) return at.Site != null && !at.Exterior && n.Role != WireRole.WaterInlet && n.Role != WireRole.SewerOutlet ? at.Site : null;   // the inlet (and the waste outlet) is met from outside
            Vector3 p = n.transform.position;
            foreach (ConstructionSite s in ConstructionSite.All) if (s != null && s.Finished && s.IsInsideWalls(p + Vector3.up * 0.3f)) return s;
            return null;
        }

        /// <summary>The point where a device meets its wall (its mounting point; a wall entry: the plate nearest the wire).</summary>
        private static Vector3 Anchor(WireNode n, Vector3 port)
        {
            if (n.Role != WireRole.WallEntry) return n.transform.position;
            Transform best = n.transform;
            float bestD = float.MaxValue;
            foreach (Transform c in n.GetComponentsInChildren<Transform>())
            {
                if (!c.name.StartsWith("Plate")) continue;
                float d = (c.position - port).sqrMagnitude;
                if (d < bestD) { bestD = d; best = c; }
            }
            return best.position;
        }

        private static int EdgeOf(Rect r, float x, float z)
        {
            float d0 = Mathf.Abs(z - r.yMin), d1 = Mathf.Abs(x - r.xMax), d2 = Mathf.Abs(z - r.yMax), d3 = Mathf.Abs(x - r.xMin);
            float m = Mathf.Min(Mathf.Min(d0, d1), Mathf.Min(d2, d3));
            return m == d0 ? 0 : m == d1 ? 1 : m == d2 ? 2 : 3;
        }

        /// <summary>Puts one edge of the run rectangle on the surface the device is mounted on, the wire a little off it (towards the room inside, away from the building outside).</summary>
        private static Rect Snap(Rect r, int edge, Vector3 root, bool inside)
        {
            float x0 = r.xMin, x1 = r.xMax, z0 = r.yMin, z1 = r.yMax;
            switch (edge)
            {
                case 0: z0 = root.z + (inside ? Off : -Off); break;
                case 1: x1 = root.x + (inside ? -Off : Off); break;
                case 2: z1 = root.z + (inside ? -Off : Off); break;
                default: x0 = root.x + (inside ? Off : -Off); break;
            }
            return Rect.MinMaxRect(x0, z0, x1, z1);
        }

        /// <summary>Which way a device faces: out of its wall (a wall entry: the plate nearest the wire).</summary>
        private static Vector3 Facing(WireNode n, Vector3 port)
        {
            Transform t = n.transform;
            if (n.Role == WireRole.WallEntry)
            {
                float best = float.MaxValue;
                foreach (Transform c in n.GetComponentsInChildren<Transform>())
                {
                    if (!c.name.StartsWith("Plate")) continue;
                    float d = (c.position - port).sqrMagnitude;
                    if (d < best) { best = d; t = c; }
                }
            }
            Vector3 f = t.forward;
            f.y = 0f;
            return f.sqrMagnitude > 1e-4f ? f.normalized : Vector3.forward;
        }

        // ------------------------------------------------------------------ round the walls

        private static float Perimeter(Rect r) { return 2f * (r.width + r.height); }

        /// <summary>The nearest point of the rectangle's outline to (x, z), and how far along the outline it is (counter-clockwise from the corner at the minimum x and z).</summary>
        private static void Project(Rect r, float x, float z, out float s, out Vector2 q)
        {
            float w = r.width, d = r.height;
            float cx = Mathf.Clamp(x, r.xMin, r.xMax), cz = Mathf.Clamp(z, r.yMin, r.yMax);
            float d0 = Mathf.Abs(z - r.yMin), d1 = Mathf.Abs(x - r.xMax), d2 = Mathf.Abs(z - r.yMax), d3 = Mathf.Abs(x - r.xMin);
            float m = Mathf.Min(Mathf.Min(d0, d1), Mathf.Min(d2, d3));
            if (m == d0) { q = new Vector2(cx, r.yMin); s = cx - r.xMin; }
            else if (m == d1) { q = new Vector2(r.xMax, cz); s = w + (cz - r.yMin); }
            else if (m == d2) { q = new Vector2(cx, r.yMax); s = w + d + (r.xMax - cx); }
            else { q = new Vector2(r.xMin, cz); s = 2f * w + d + (r.yMax - cz); }
        }

        private static Vector2[] Corner(Rect r)
        {
            return new[] { new Vector2(r.xMin, r.yMin), new Vector2(r.xMax, r.yMin), new Vector2(r.xMax, r.yMax), new Vector2(r.xMin, r.yMax) };
        }

        /// <summary>The corners passed going the SHORTER way round from outline position sa to sb, in order.</summary>
        private static List<Vector2> CornersBetween(Rect r, float sa, float sb)
        {
            float L = Perimeter(r);
            float[] at = { 0f, r.width, r.width + r.height, 2f * r.width + r.height };
            Vector2[] corners = Corner(r);
            float forward = Mathf.Repeat(sb - sa, L);
            bool ccw = forward <= L - forward;
            var list = new List<Vector2>();
            float travel = ccw ? forward : L - forward;
            for (int i = 0; i < 4; i++)
            {
                // the distance from sa to this corner in the direction of travel
                float dist = ccw ? Mathf.Repeat(at[i] - sa, L) : Mathf.Repeat(sa - at[i], L);
                if (dist > 0.001f && dist < travel - 0.001f) list.Add(corners[i]);
            }
            list.Sort((p, q) =>
            {
                int ip = System.Array.IndexOf(corners, p), iq = System.Array.IndexOf(corners, q);
                float dp = ccw ? Mathf.Repeat(at[ip] - sa, L) : Mathf.Repeat(sa - at[ip], L);
                float dq = ccw ? Mathf.Repeat(at[iq] - sa, L) : Mathf.Repeat(sa - at[iq], L);
                return dp.CompareTo(dq);
            });
            return list;
        }

        private static List<Vector3> Compact(List<Vector3> pts)
        {
            var o = new List<Vector3>();
            foreach (Vector3 p in pts) if (o.Count == 0 || (p - o[o.Count - 1]).sqrMagnitude > 1e-6f) o.Add(p);
            return o;
        }

        // ------------------------------------------------------------------ windows and doors

        private static List<Opening> Openings(ConstructionSite site, Quaternion inv)
        {
            var list = new List<Opening>();
            Transform root = site.VisualRoot;
            if (root == null) return list;
            foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
            {
                bool door = false, window = false;
                for (Transform t = r.transform; t != null && t != root.parent; t = t.parent)
                {
                    if (t.name.StartsWith("Door")) { door = true; break; }
                    if (t.name == "WindowGlass" || t.name.StartsWith("Window")) { window = true; break; }
                }
                if (!door && !window) continue;
                if (window && AddPanes(r, site, inv, list)) continue;   // a building's panes are ONE object: take them one by one, not as a box round all of them
                Bounds b = r.bounds;
                Vector3 mn = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue), mx = -mn;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    Vector3 l = inv * (c - site.transform.position);
                    mn = Vector3.Min(mn, l);
                    mx = Vector3.Max(mx, l);
                }
                list.Add(new Opening { Door = door, Min = mn, Max = mx });
            }
            return list;
        }

        /// <summary>The panes of a window object whose mesh is one piece per pane: each connected piece of the mesh is a window, with its own bounds. False when the mesh cannot be read.</summary>
        private static readonly Dictionary<Renderer, List<Bounds>> s_paneCache = new Dictionary<Renderer, List<Bounds>>();   // the panes of a window object, in its own space

        private static bool AddPanes(Renderer r, ConstructionSite site, Quaternion inv, List<Opening> list)
        {
            if (s_paneCache.TryGetValue(r, out List<Bounds> cached))
            {
                if (cached == null) return false;
                Matrix4x4 m2w = r.localToWorldMatrix;
                foreach (Bounds pb in cached)
                {
                    Vector3 mn = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue), mx = -mn;
                    for (int i = 0; i < 8; i++)
                    {
                        Vector3 c = pb.center + Vector3.Scale(pb.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                        Vector3 l = inv * (m2w.MultiplyPoint3x4(c) - site.transform.position);
                        mn = Vector3.Min(mn, l);
                        mx = Vector3.Max(mx, l);
                    }
                    list.Add(new Opening { Door = false, Min = mn, Max = mx });
                }
                return true;
            }
            bool ok = BuildPanes(r, site, inv, list, out List<Bounds> built);
            s_paneCache[r] = ok ? built : null;
            return ok;
        }

        private static bool BuildPanes(Renderer r, ConstructionSite site, Quaternion inv, List<Opening> list, out List<Bounds> local)
        {
            local = new List<Bounds>();
            MeshFilter mf = r.GetComponent<MeshFilter>();
            Mesh m = mf != null ? mf.sharedMesh : null;
            if (m == null || !m.isReadable) return false;
            Vector3[] v = m.vertices;
            int[] tri = m.triangles;
            if (v.Length == 0 || tri.Length < 3) return false;
            // weld vertices at the same place (a pane's corners are often split for the normals), then join every triangle's three corners
            var weld = new Dictionary<Vector3Int, int>();
            var id = new int[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                var key = new Vector3Int(Mathf.RoundToInt(v[i].x * 1000f), Mathf.RoundToInt(v[i].y * 1000f), Mathf.RoundToInt(v[i].z * 1000f));
                if (!weld.TryGetValue(key, out int w)) { w = weld.Count; weld[key] = w; }
                id[i] = w;
            }
            var parent = new int[weld.Count];
            for (int i = 0; i < parent.Length; i++) parent[i] = i;
            System.Func<int, int> find = null;
            find = x => { while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
            for (int t = 0; t + 2 < tri.Length; t += 3)
            {
                int a = find(id[tri[t]]), b = find(id[tri[t + 1]]), c = find(id[tri[t + 2]]);
                parent[b] = a;
                parent[find(c)] = find(a);
            }
            var mins = new Dictionary<int, Vector3>();
            var maxs = new Dictionary<int, Vector3>();
            for (int i = 0; i < v.Length; i++)
            {
                int root = find(id[i]);
                if (!mins.ContainsKey(root)) { mins[root] = v[i]; maxs[root] = v[i]; }
                else { mins[root] = Vector3.Min(mins[root], v[i]); maxs[root] = Vector3.Max(maxs[root], v[i]); }
            }
            if (mins.Count < 2) return false;   // one piece: not a set of panes
            foreach (var kv in mins)
            {
                var b = new Bounds();
                b.SetMinMax(kv.Value, maxs[kv.Key]);
                local.Add(b);
            }
            // the first time: the same panes in the building's space
            Matrix4x4 toWorld = r.localToWorldMatrix;
            foreach (Bounds pb in local)
            {
                Vector3 mn = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue), mx = -mn;
                for (int i = 0; i < 8; i++)
                {
                    Vector3 c = pb.center + Vector3.Scale(pb.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    Vector3 l = inv * (toWorld.MultiplyPoint3x4(c) - site.transform.position);
                    mn = Vector3.Min(mn, l);
                    mx = Vector3.Max(mx, l);
                }
                list.Add(new Opening { Door = false, Min = mn, Max = mx });
            }
            return true;
        }

        /// <summary>
        /// Takes the wire under each window and over each door it would cross: along a horizontal stretch, where an opening is in the way it jogs up or down with right angles, runs past it,
        /// and comes back to its height.
        /// </summary>
        private static List<Vector3> Detour(List<Vector3> pts, List<Opening> openings, Rect run)
        {
            if (openings.Count == 0) return pts;
            var o = new List<Vector3> { pts[0] };
            for (int i = 1; i < pts.Count; i++)
            {
                Vector3 p = o[o.Count - 1], q = pts[i];
                bool horizontal = Mathf.Abs(p.y - q.y) < 0.001f;
                float dx = Mathf.Abs(q.x - p.x), dz = Mathf.Abs(q.z - p.z);
                bool alongX = dx > dz;
                if (!horizontal || Mathf.Max(dx, dz) < 0.3f || (dx > 0.01f && dz > 0.01f)) { o.Add(q); continue; }   // a stub, a vertical run or the slant out of a device: leave it
                float h = p.y;
                float line = alongX ? p.z : p.x;                   // the coordinate that stays the same along this stretch
                float u0 = alongX ? p.x : p.z, u1 = alongX ? q.x : q.z;
                float dir = Mathf.Sign(u1 - u0);
                var hits = new List<Opening>();
                foreach (Opening op in openings)
                {
                    float perp = alongX ? (op.Min.z + op.Max.z) * 0.5f : (op.Min.x + op.Max.x) * 0.5f;
                    if (Mathf.Abs(perp - line) > 0.5f) continue;                                // not in this wall
                    float a0 = alongX ? op.Min.x : op.Min.z, a1 = alongX ? op.Max.x : op.Max.z;
                    if (Mathf.Max(a0, Mathf.Min(u0, u1)) > Mathf.Min(a1, Mathf.Max(u0, u1))) continue;   // not along it
                    if (h < op.Min.y - Clear * 0.5f || h > op.Max.y + Clear * 0.5f) continue;   // the wire runs above or below it already
                    hits.Add(op);
                }
                System.Func<Opening, float> order = op => dir > 0f ? (alongX ? op.Min.x : op.Min.z) : -(alongX ? op.Max.x : op.Max.z);   // in the order the wire meets them
                hits.Sort((x, y) => order(x).CompareTo(order(y)));
                foreach (Opening op in hits)
                {
                    float a0 = (alongX ? op.Min.x : op.Min.z) - Clear, a1 = (alongX ? op.Max.x : op.Max.z) + Clear;
                    float enter = dir > 0f ? a0 : a1, leave = dir > 0f ? a1 : a0;
                    float around = op.Door ? op.Max.y + Clear : op.Min.y - Clear;           // over a door, under a window
                    if ((enter - u0) * dir <= 0.01f || (u1 - leave) * dir <= 0.01f) continue; // it starts or ends right at it: no room to go round
                    o.Add(Make(alongX, enter, h, line));
                    o.Add(Make(alongX, enter, around, line));
                    o.Add(Make(alongX, leave, around, line));
                    o.Add(Make(alongX, leave, h, line));
                    u0 = leave;
                }
                o.Add(q);
            }
            return Compact(o);
        }

        private static Vector3 Make(bool alongX, float along, float y, float line)
        {
            return alongX ? new Vector3(along, y, line) : new Vector3(line, y, along);
        }
    }
}
