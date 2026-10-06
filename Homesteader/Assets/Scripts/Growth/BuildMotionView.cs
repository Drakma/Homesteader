using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The model of a stage being built, moving with the build progress (<see cref="ConstructionSite.BuildProgress"/>), so the player sees the work:
    ///   tilt_up  the node "Mast" lies on the ground towards the front and is raised upright on its hinge (the base stays put);
    ///   lift     the node "Yaw" (the turbine's head) is hoisted from near the ground up to the top of the mast;
    ///   spin_up  the node "Rotor" is fitted (it grows from nothing) and spins faster and faster.
    /// The stage's model carries those nodes (tools/make_wind_turbines.py). Made by ConstructionSite.RunBuildPreview and destroyed when the build ends.
    /// </summary>
    public sealed class BuildMotionView : MonoBehaviour
    {
        private ConstructionSite _site;
        private string _motion;
        private Transform _node;
        private Vector3 _restPos;
        private Quaternion _restRot;
        private Vector3 _restScale;
        private float _nextFind;
        private float _spin;

        public void Init(ConstructionSite site, string motion)
        {
            _site = site;
            _motion = motion;
        }

        private static float Ease(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }

        private void Update()
        {
            if (_site == null) { Destroy(gameObject); return; }
            if (_node == null)
            {
                if (Time.unscaledTime < _nextFind) return;
                _nextFind = Time.unscaledTime + 0.25f;
                string want = _motion == "tilt_up" ? "Mast" : _motion == "lift" ? "Yaw" : _motion == "spin_up" ? "Rotor" : null;
                if (want == null) { enabled = false; return; }
                foreach (Transform t in GetComponentsInChildren<Transform>(true))
                    if (t.name.StartsWith(want)) { _node = t; break; }
                if (_node == null) return;
                _restPos = _node.localPosition;
                _restRot = _node.localRotation;
                _restScale = _node.localScale;
            }

            float p = _site.BuildProgress;
            switch (_motion)
            {
                case "tilt_up":
                {
                    // lies along the front for the first moments, then swings up to stand (84 degrees to 0)
                    float q = Ease((p - 0.08f) / 0.84f);
                    _node.localRotation = _restRot * Quaternion.AngleAxis(84f * (1f - q), Vector3.right);
                    break;
                }
                case "lift":
                {
                    // hoisted up the mast from a point near the ground, a little out in front
                    float q = Ease((p - 0.05f) / 0.85f);
                    Vector3 start = new Vector3(0f, -(_restPos.y - 0.7f), 1.1f);
                    _node.localPosition = _restPos + Vector3.Lerp(start, Vector3.zero, q);
                    break;
                }
                case "spin_up":
                {
                    _node.localScale = _restScale * Mathf.Lerp(0.01f, 1f, Ease(p * 4f));
                    _spin += 14f * p * p * Mathf.Rad2Deg * Time.deltaTime;
                    _node.localRotation = _restRot * Quaternion.AngleAxis(-_spin, Vector3.forward);
                    break;
                }
            }
        }
    }
}
