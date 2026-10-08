using System.Collections.Generic;
using Homesteader.UI;
using Homesteader.World;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// A push mower (manifest properties.pushable and properties.mower_width_m): taken by the handles like a wheelbarrow (right click with an empty hand), and while it is pushed it cuts a strip of
    /// lawn as wide as its deck along its path (<see cref="LawnSoil"/>): the squares it passes over turn into fresh-cut lawn with stripes that run the way it travelled. It cuts nothing while it
    /// stands, and it does not mow farmland, roads or water. Fuel is not modeled yet. docs/MOWING.md.
    /// </summary>
    public sealed class PushMower : MonoBehaviour
    {
        private PlacedObject _placed;
        private float _width = 0.53f;
        private Vector3 _last;
        private bool _have;
        private readonly List<Vector3> _points = new List<Vector3>();

        /// <summary>Makes a placed object a mower when its manifest gives it a deck width.</summary>
        public static void AttachIfMower(PlacedObject placed)
        {
            if (placed == null || placed.GetComponent<PushMower>() != null) return;
            AssetCatalogItem info = HudBindings.GetCatalogItem(placed.ItemId);
            if (info == null || info.mower_width_m <= 0f) return;
            var m = placed.gameObject.AddComponent<PushMower>();
            m._placed = placed;
            m._width = info.mower_width_m;
        }

        private void LateUpdate()
        {
            if (_placed == null) return;
            bool pushed = WheelbarrowPush.Active != null && WheelbarrowPush.Active.Placed == _placed;
            Vector3 now = _placed.transform.position;
            if (!pushed) { _have = false; return; }
            if (!_have) { _last = now; _have = true; }
            Vector3 move = now - _last;
            move.y = 0f;
            if (move.sqrMagnitude < 0.04f * 0.04f) return;   // it has to travel a few centimetres to cut
            Vector3 dir = move.normalized;
            Vector3 across = new Vector3(-dir.z, 0f, dir.x);
            _points.Clear();
            float step = 0.25f;
            int along = Mathf.Max(1, Mathf.CeilToInt(move.magnitude / step));
            int abreast = Mathf.Max(1, Mathf.CeilToInt(_width / step));
            for (int i = 1; i <= along; i++)
            {
                Vector3 centre = _last + move * (i / (float)along);
                for (int k = 0; k <= abreast; k++)
                    _points.Add(centre + across * ((k / (float)abreast - 0.5f) * _width));
            }
            _last = now;
            LawnSoil.Mow(_points, dir);
        }
    }
}
