using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

/// <summary>
/// After every player build, copies the project's mods folder (Homesteader/mods: the core catalog, the "homesteader" mod, and any others in it) into a
/// "mods" folder next to the built game, where ModManager looks for it (Directory.GetCurrentDirectory()/mods). The game's items, models, recipes and icons
/// all come from there, so a build without it would have none. Mods switched off (.disabled) are left out, and so are .obj / .mtl leftovers.
/// </summary>
public sealed class ShipModsPostBuild : IPostprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPostprocessBuild(BuildReport report)
    {
        string src = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "mods"));
        if (!Directory.Exists(src)) { Debug.LogWarning("[ShipMods] No mods folder at " + src + ": the build has no game content."); return; }
        string outPath = report.summary.outputPath;
        string gameDir = File.Exists(outPath) ? Path.GetDirectoryName(outPath) : outPath;   // Windows: the .exe; other targets: the folder
        string dst = Path.Combine(gameDir, "mods");
        if (Directory.Exists(dst)) Directory.Delete(dst, true);
        int files = Copy(src, dst);
        Debug.Log("[ShipMods] Copied " + files + " mod files to " + dst);
    }

    private static int Copy(string from, string to)
    {
        int n = 0;
        Directory.CreateDirectory(to);
        foreach (string f in Directory.GetFiles(from))
        {
            string ext = Path.GetExtension(f).ToLowerInvariant();
            if (ext == ".obj" || ext == ".mtl" || f.EndsWith(".disabled")) continue;
            File.Copy(f, Path.Combine(to, Path.GetFileName(f)), true);
            n++;
        }
        foreach (string d in Directory.GetDirectories(from))
        {
            if (d.EndsWith(".disabled")) continue;
            n += Copy(d, Path.Combine(to, Path.GetFileName(d)));
        }
        return n;
    }
}
