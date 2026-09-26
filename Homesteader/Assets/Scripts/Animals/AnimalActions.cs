using System.Collections.Generic;
using UnityEngine;

namespace Homesteader.Animals
{
    /// <summary>The built-in actions a behaviour rule can pick (idle, wander, goto, follow, flee, rest, emote, consume, sequence).</summary>
    public static class AnimalActions
    {
        public abstract class ActionRuntime
        {
            public bool Done;
            protected ActionDef Def;
            protected float Elapsed;
            protected float Duration;

            protected ActionRuntime(ActionDef def) { Def = def; }

            public virtual void Begin(AnimalBrain b)
            {
                Duration = Random.Range(Def.DurationMin, Mathf.Max(Def.DurationMin, Def.DurationMax));
            }

            public void Tick(AnimalBrain b, float dt)
            {
                Elapsed += dt;
                OnTick(b, dt);
            }

            protected abstract void OnTick(AnimalBrain b, float dt);

            public virtual void End(AnimalBrain b) { b.StopAnim(); }
        }

        public static ActionRuntime Create(ActionDef def)
        {
            switch (def.Type)
            {
                case "idle": return new IdleAction(def);
                case "wander": return new WanderAction(def);
                case "goto": return new GoToAction(def);
                case "follow": return new FollowAction(def);
                case "flee": return new FleeAction(def);
                case "rest": return new RestAction(def);
                case "emote": return new EmoteAction(def);
                case "consume": return new ConsumeAction(def);
                case "sequence": return new SequenceAction(def);
            }
            return new IdleAction(def);
        }

        // ------------------------------------------------------------------ idle

        private sealed class IdleAction : ActionRuntime
        {
            public IdleAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b)
            {
                base.Begin(b);
                b.Mover.Stop();
                b.StopAnim();
                b.SetMoving(0f);
                if (!string.IsNullOrEmpty(Def.Anim) && b.Def.ClipFor(Def.Anim) != b.Def.ClipFor("idle"))
                    b.PlayAnim(Def.Anim, true);
            }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (Elapsed >= Duration) Done = true;
            }
        }

        // ------------------------------------------------------------------ wander

        private sealed class WanderAction : ActionRuntime
        {
            private Vector3 goal;
            private bool hasGoal;

            public WanderAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b)
            {
                base.Begin(b);
                b.StopAnim();
                Vector3 anchor = b.transform.position;
                if (Def.StayNear == "home") anchor = b.Home;
                else if (Def.StayNear == "player")
                {
                    GameObject p = GameObject.FindWithTag("Player");
                    if (p != null) anchor = p.transform.position;
                }

                for (int i = 0; i < 8; i++)
                {
                    Vector2 c = Random.insideUnitCircle * Def.Radius;
                    Vector3 g = anchor + new Vector3(c.x, 0f, c.y);
                    g.y = AnimalMover.GroundY(g);
                    if (AnimalMover.SlopeAt(g) <= b.Def.Movement.MaxSlopeDeg) { goal = g; hasGoal = true; break; }
                }
                Done = !hasGoal;
            }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                float speed = b.SpeedFor(Def.Speed);
                float left = b.Mover.MoveToward(goal, speed, dt);
                b.SetMoving(b.Mover.CurrentSpeed);
                if (left <= Def.ArriveDist || b.Mover.BlockedSeconds > 1.5f || Elapsed > 45f) Done = true;
            }

            public override void End(AnimalBrain b) { b.Mover.Stop(); b.SetMoving(0f); }
        }

        // ------------------------------------------------------------------ goto

        private class GoToAction : ActionRuntime
        {
            public GoToAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b) { base.Begin(b); b.StopAnim(); }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (!b.TryResolveTarget(Def.Target, out Vector3 pos, out _)) { Done = true; return; }
                float left = b.Mover.MoveToward(pos, b.SpeedFor(Def.Speed), dt);
                b.SetMoving(b.Mover.CurrentSpeed);
                if (left <= Def.ArriveDist || b.Mover.BlockedSeconds > 2f || Elapsed > 60f) Done = true;
            }

            public override void End(AnimalBrain b) { b.Mover.Stop(); b.SetMoving(0f); }
        }

        // ------------------------------------------------------------------ follow

        private sealed class FollowAction : ActionRuntime
        {
            public FollowAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b) { base.Begin(b); b.StopAnim(); }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (!b.TryResolveTarget(Def.Target, out Vector3 pos, out _)) { Done = true; return; }
                if (Def.Until != null && b.Test(Def.Until)) { Done = true; return; }

                float d = AnimalSenses.Flat(b.transform.position, pos);
                if (d > Def.MaxDist)
                {
                    // Catch up: run when far behind, otherwise the configured speed.
                    string speed = d > Def.MaxDist * 1.8f ? "run" : Def.Speed;
                    b.Mover.MoveToward(pos, b.SpeedFor(speed), dt);
                    b.SetMoving(b.Mover.CurrentSpeed);
                }
                else if (d > Def.MinDist)
                {
                    b.Mover.MoveToward(pos, b.SpeedFor("walk"), dt);
                    b.SetMoving(b.Mover.CurrentSpeed);
                }
                else
                {
                    b.Mover.FaceToward(pos, dt);      // close enough: stand and watch
                    b.SetMoving(0f);
                }
            }

            public override void End(AnimalBrain b) { b.Mover.Stop(); b.SetMoving(0f); }
        }

        // ------------------------------------------------------------------ flee

        private sealed class FleeAction : ActionRuntime
        {
            public FleeAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b) { base.Begin(b); b.StopAnim(); }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (!b.TryResolveTarget(Def.Target, out Vector3 threat, out _)) { Done = true; return; }
                Vector3 away = b.transform.position - threat;
                away.y = 0f;
                float d = away.magnitude;
                if (d >= Def.MinDist * 2f || Elapsed > 20f) { Done = true; return; }
                away = d < 0.01f ? b.transform.forward : away / d;

                Vector3 goal = b.transform.position + away * 6f;
                b.Mover.MoveToward(goal, b.SpeedFor(string.IsNullOrEmpty(Def.Speed) ? "run" : Def.Speed), dt);
                b.SetMoving(b.Mover.CurrentSpeed);
            }

            public override void End(AnimalBrain b) { b.Mover.Stop(); b.SetMoving(0f); }
        }

        // ------------------------------------------------------------------ rest (sit / lay / sleep)

        private sealed class RestAction : ActionRuntime
        {
            private bool useUntil;

            public RestAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b)
            {
                base.Begin(b);
                useUntil = Def.Until != null;
                b.Mover.Stop();
                b.SetMoving(0f);
                b.PlayAnim(string.IsNullOrEmpty(Def.Anim) ? "lay" : Def.Anim, true);
            }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (!string.IsNullOrEmpty(Def.Need)) b.AddNeed(Def.Need, Def.RestorePerSecond * dt);
                if (useUntil ? b.Test(Def.Until) : Elapsed >= Duration) Done = true;
                else if (useUntil && Elapsed > 600f) Done = true;
            }
        }

        // ------------------------------------------------------------------ emote (bark, sit briefly, ...)

        private sealed class EmoteAction : ActionRuntime
        {
            public EmoteAction(ActionDef d) : base(d) { }

            public override void Begin(AnimalBrain b)
            {
                base.Begin(b);
                b.Mover.Stop();
                b.SetMoving(0f);
                b.PlayAnim(Def.Anim, false);
            }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (Elapsed >= Duration) Done = true;
            }
        }

        // ------------------------------------------------------------------ consume (eat / drink)

        private sealed class ConsumeAction : GoToAction
        {
            private bool arrived;
            private float eatTime;

            public ConsumeAction(ActionDef d) : base(d) { }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (!arrived)
                {
                    if (!b.TryResolveTarget(Def.Target, out Vector3 pos, out _)) { Done = true; return; }
                    float left = b.Mover.MoveToward(pos, b.SpeedFor(Def.Speed), dt);
                    b.SetMoving(b.Mover.CurrentSpeed);
                    if (b.Mover.BlockedSeconds > 2f || Elapsed > 60f) { Done = true; return; }
                    if (left <= Def.ArriveDist)
                    {
                        arrived = true;
                        b.Mover.Stop();
                        b.SetMoving(0f);
                        b.PlayAnim(string.IsNullOrEmpty(Def.Anim) ? "eat" : Def.Anim, true);
                    }
                    return;
                }

                eatTime += dt;
                if (!string.IsNullOrEmpty(Def.Need)) b.AddNeed(Def.Need, Def.RestorePerSecond * dt);
                if (eatTime >= Duration) Done = true;
            }
        }

        // ------------------------------------------------------------------ sequence

        private sealed class SequenceAction : ActionRuntime
        {
            private readonly List<ActionRuntime> steps = new List<ActionRuntime>();
            private int index;
            private bool began;

            public SequenceAction(ActionDef d) : base(d)
            {
                foreach (ActionDef s in d.Steps) steps.Add(Create(s));
            }

            protected override void OnTick(AnimalBrain b, float dt)
            {
                if (index >= steps.Count) { Done = true; return; }
                ActionRuntime step = steps[index];
                if (!began) { step.Begin(b); began = true; }
                step.Tick(b, dt);
                if (step.Done)
                {
                    step.End(b);
                    index++;
                    began = false;
                }
            }

            public override void End(AnimalBrain b)
            {
                if (began && index < steps.Count) steps[index].End(b);
                b.StopAnim();
            }
        }
    }
}
