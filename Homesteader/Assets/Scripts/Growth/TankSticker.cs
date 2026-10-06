using System.Collections.Generic;
using Homesteader.UI;
using UnityEngine;

namespace Homesteader.Growth
{
    /// <summary>
    /// The sticker on the side of a fuel tank names what is in it. A tank model carries its sticker as a material called TankSticker
    /// (tools/case_labels.py, add_tank_sticker); the pictures, one per liquid, are Resources/TankStickers/&lt;liquid id&gt; (painted by the same
    /// tool). What a tank holds: the liquid set with <see cref="Show"/> (the hook for filling and draining), else what the item comes filled
    /// with, else the one liquid it accepts. A tank that takes several liquids and has been told nothing keeps the sticker of its model.
    /// </summary>
    public sealed class TankSticker : MonoBehaviour
    {
        private const string MaterialName = "TankSticker";
        private static readonly int BaseMap = Shader.PropertyToID("_BaseMap");
        private static readonly Dictionary<string, Texture2D> s_pictures = new Dictionary<string, Texture2D>();

        /// <summary>The liquid the sticker names ("" = the model's own sticker).</summary>
        public string LiquidId { get; private set; } = "";

        private readonly List<Material> _stickers = new List<Material>();

        public static void AttachIfTank(PlacedObject placed)
        {
            if (placed == null || !LiquidRules.IsLiquidContainer(placed.ItemId) || placed.GetComponent<TankSticker>() != null) return;
            var found = new List<Material>();
            foreach (Renderer r in placed.GetComponentsInChildren<Renderer>(true))
            {
                Material[] shared = r.sharedMaterials;
                for (int i = 0; i < shared.Length; i++)
                {
                    if (shared[i] == null || !shared[i].name.StartsWith(MaterialName)) continue;
                    found.Add(r.materials[i]);          // this tank's own copy: another tank of the same model keeps its sticker
                }
            }
            if (found.Count == 0) return;               // a container with no sticker on its model
            var sticker = placed.gameObject.AddComponent<TankSticker>();
            sticker._stickers.AddRange(found);
            sticker.Show(DefaultLiquid(placed.ItemId));
        }

        /// <summary>Names this liquid on the tank ("empty" for an empty one; null or "" leaves the sticker as it is).</summary>
        public static void Show(PlacedObject placed, string liquidId)
        {
            TankSticker s = placed != null ? placed.GetComponent<TankSticker>() : null;
            if (s != null) s.Show(liquidId);
        }

        public void Show(string liquidId)
        {
            if (string.IsNullOrEmpty(liquidId) || liquidId == LiquidId) return;
            Texture2D picture = Picture(liquidId);
            if (picture == null) return;
            LiquidId = liquidId;
            foreach (Material m in _stickers)
            {
                if (m == null) continue;
                m.mainTexture = picture;
                if (m.HasProperty(BaseMap)) m.SetTexture(BaseMap, picture);
            }
        }

        /// <summary>What a tank of this item holds when nobody has said: what it is sold filled with, else the only liquid it takes.</summary>
        private static string DefaultLiquid(string itemId)
        {
            var info = HudBindings.GetCatalogItem(itemId);
            if (info == null) return "";
            if (!string.IsNullOrEmpty(info.liquid_filled_with)) return info.liquid_filled_with;
            if (info.liquid_accepts != null && info.liquid_accepts.Count == 1 && !info.liquid_accepts[0].StartsWith("#")) return info.liquid_accepts[0];
            return "";
        }

        private static Texture2D Picture(string liquidId)
        {
            if (!s_pictures.TryGetValue(liquidId, out Texture2D t))
            {
                t = Resources.Load<Texture2D>("TankStickers/" + liquidId);
                s_pictures[liquidId] = t;
            }
            return t;
        }
    }
}
