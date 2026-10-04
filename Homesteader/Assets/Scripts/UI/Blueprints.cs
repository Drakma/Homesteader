using Homesteader.Growth;

namespace Homesteader.UI
{
    /// <summary>
    /// Blueprints: structures, paths and roads are bought as a blueprint, once. Holding one starts the build (a construction site, a path or road
    /// route), and it is NEVER used up: it stays in the toolbar for good, cannot be dropped, deleted or sold, and a second one cannot be bought.
    /// What each build costs is its materials, taken as before. A blueprint is any structure that builds in stages, or an item with is_blueprint.
    /// </summary>
    public static class Blueprints
    {
        public static bool IsBlueprint(string id)
        {
            if (string.IsNullOrEmpty(id)) return false;
            if (ConstructionSite.IsStructure(id)) return true;
            AssetCatalogItem item = HudBindings.GetCatalogItem(id);
            return item != null && item.is_blueprint;
        }

        /// <summary>True when the player already has this blueprint (it lives in the toolbar).</summary>
        public static bool Owned(string id)
        {
            HudState hud = HudState.Active;
            if (hud == null) return false;
            foreach (ToolbarSlotData s in hud.Toolbar) if (s.IconId == id && s.Count > 0) return true;
            return false;
        }
    }
}
