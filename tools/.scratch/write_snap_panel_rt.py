"""snap_via_panel_rt.json - capture UI by binding PanelSettings.targetTexture."""
import json
import os

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\snap_panel_rt.json"
code_lines = [
    "using UnityEngine;",
    "using UnityEditor;",
    "using UnityEngine.UIElements;",
    "using System.IO;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(\"HudRoot\");",
    "        if (hud == null) { result.Log(\"no HudRoot\"); return; }",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        if (doc == null) { result.Log(\"no UIDocument\"); return; }",
    "        if (doc.rootVisualElement == null) { result.Log(\"no root\"); return; }",
    "        var dir = \"C:/Users/casey/Desktop/Homesteader/tools/.scratch\";",
    "        if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);",
    "        var rt = RenderTexture.GetTemporary(1920, 1080, 24);",
    "        if (doc.panelSettings != null) doc.panelSettings.targetTexture = rt;",
    "        var prevTarget = doc.panelSettings != null ? doc.panelSettings.targetTexture : null;",
    "        // Render camera first (3D scene)",
    "        var camGo = GameObject.Find(\"IsoCamera\");",
    "        if (camGo == null) camGo = GameObject.Find(\"Main Camera\");",
    "        var cam = camGo != null ? camGo.GetComponent<Camera>() : null;",
    "        if (cam != null)",
    "        {",
    "            cam.targetTexture = rt;",
    "            cam.Render();",
    "            cam.targetTexture = null;",
    "        }",
    "        // Sample RT",
    "        var prevActive = RenderTexture.active;",
    "        RenderTexture.active = rt;",
    "        var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);",
    "        tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);",
    "        tex.Apply();",
    "        var bytes = tex.EncodeToPNG();",
    "        File.WriteAllBytes(dir + \"/hud_panel_rt.png\", bytes);",
    "        result.Log(\"wrote bytes=\" + bytes.Length);",
    "        RenderTexture.active = prevActive;",
    "        if (doc.panelSettings != null) doc.panelSettings.targetTexture = prevTarget;",
    "        RenderTexture.ReleaseTemporary(rt);",
    "        Object.DestroyImmediate(tex);",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Capture via PanelSettings RT"}
with open(p, "w") as f:
    f.write("{}\n".format(json.dumps(payload, indent=2)))
print("wrote", p, "size", os.path.getsize(p))
