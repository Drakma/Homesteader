using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// A small filled line graph for the Grid OS app: a series of samples drawn left to right as a line with the area under it filled, on a grid of faint lines. The vertical range is
    /// 0 to <see cref="MaxY"/> (or the series' own peak when MaxY is 0). Drawn with the painter, so it costs nothing until the data changes.
    /// </summary>
    public sealed class GridGraph : VisualElement
    {
        private IList<float> _data;
        public float MaxY;
        public Color Line = new Color(0.95f, 0.52f, 0.11f);
        public Color Fill = new Color(0.95f, 0.52f, 0.11f, 0.22f);
        public int Samples = 96;   // the width of the whole graph in samples: a short series fills from the left

        public GridGraph()
        {
            style.height = 84;
            style.marginTop = 8;
            style.backgroundColor = new Color(0.05f, 0.06f, 0.08f, 1f);
            style.borderTopLeftRadius = style.borderTopRightRadius = style.borderBottomLeftRadius = style.borderBottomRightRadius = 8;
            style.flexShrink = 0;
            generateVisualContent += OnDraw;
        }

        public void SetData(IList<float> data) { _data = data; MarkDirtyRepaint(); }

        private void OnDraw(MeshGenerationContext ctx)
        {
            Rect r = contentRect;
            if (r.width < 4f || r.height < 4f) return;
            Painter2D p = ctx.painter2D;
            const float pad = 6f;
            float w = r.width - 2f * pad, h = r.height - 2f * pad;

            p.lineWidth = 1f;
            p.strokeColor = new Color(1f, 1f, 1f, 0.07f);
            for (int g = 0; g <= 3; g++)
            {
                float y = pad + h * g / 3f;
                p.BeginPath();
                p.MoveTo(new Vector2(pad, y));
                p.LineTo(new Vector2(pad + w, y));
                p.Stroke();
            }
            if (_data == null || _data.Count < 2) return;

            float max = MaxY;
            if (max <= 0f) { foreach (float v in _data) if (v > max) max = v; }
            if (max <= 0f) max = 1f;
            int n = _data.Count, span = Mathf.Max(Samples, n) - 1;
            Vector2 Pt(int i) { return new Vector2(pad + w * i / span, pad + h * (1f - Mathf.Clamp01(_data[i] / max))); }

            p.fillColor = Fill;
            p.BeginPath();
            p.MoveTo(new Vector2(pad, pad + h));
            for (int i = 0; i < n; i++) p.LineTo(Pt(i));
            p.LineTo(new Vector2(pad + w * (n - 1) / span, pad + h));
            p.ClosePath();
            p.Fill();

            p.lineWidth = 2f;
            p.strokeColor = Line;
            p.lineJoin = LineJoin.Round;
            p.BeginPath();
            p.MoveTo(Pt(0));
            for (int i = 1; i < n; i++) p.LineTo(Pt(i));
            p.Stroke();
        }
    }
}
