using UnityEngine;
using UnityEngine.UIElements;

namespace Homesteader.UI
{
    /// <summary>
    /// A small arrow for the HUD wind indicator, drawn with the vector API (no texture, no emoji or font glyph).
    /// It points up; rotate it with style.rotate. Dim when there is no wind.
    /// </summary>
    public sealed class WindArrowElement : VisualElement
    {
        private float _strength;   // 0 = calm, 1 = strong wind

        public WindArrowElement()
        {
            pickingMode = PickingMode.Ignore;
            generateVisualContent += Draw;
        }

        /// <summary>0..1; scales the brightness so a calm day reads as a faint arrow.</summary>
        public void SetStrength(float strength)
        {
            strength = Mathf.Clamp01(strength);
            if (Mathf.Abs(strength - _strength) < 0.01f) return;
            _strength = strength;
            MarkDirtyRepaint();
        }

        private void Draw(MeshGenerationContext ctx)
        {
            Rect r = contentRect;
            if (r.width < 2f || r.height < 2f) return;

            float w = r.width, h = r.height;
            Painter2D p = ctx.painter2D;
            float alpha = Mathf.Lerp(0.30f, 1f, _strength);
            p.fillColor = new Color(0.62f, 0.80f, 0.96f, alpha);

            // Arrow pointing up, in a unit box scaled to the element.
            p.BeginPath();
            p.MoveTo(new Vector2(w * 0.50f, h * 0.02f));
            p.LineTo(new Vector2(w * 0.78f, h * 0.46f));
            p.LineTo(new Vector2(w * 0.55f, h * 0.46f));
            p.LineTo(new Vector2(w * 0.55f, h * 0.98f));
            p.LineTo(new Vector2(w * 0.45f, h * 0.98f));
            p.LineTo(new Vector2(w * 0.45f, h * 0.46f));
            p.LineTo(new Vector2(w * 0.22f, h * 0.46f));
            p.ClosePath();
            p.Fill();
        }
    }
}
