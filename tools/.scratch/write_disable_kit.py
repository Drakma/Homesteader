"""Disable _enableKitOverlay on HudSceneBootstrap."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\disable_kit_overlay.json"
Q = chr(34)
code_lines = [
    "using UnityEditor;",
    "using Homesteader.UI;",
    "using UnityEngine;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(" + Q + "HudRoot" + Q + ");",
    "        if (hud == null) { result.Log(" + Q + "no HudRoot" + Q + "); return; }",
    "        var b = hud.GetComponent<HudSceneBootstrap>();",
    "        if (b == null) { result.Log(" + Q + "no bootstrap" + Q + "); return; }",
    "        var so = new UnityEditor.SerializedObject(b);",
    "        var prop = so.FindProperty(" + Q + "_enableKitOverlay" + Q + ");",
    "        if (prop != null)",
    "        {",
    "            bool was = prop.boolValue;",
    "            prop.boolValue = false;",
    "            so.ApplyModifiedProperties();",
    " result.Log(" + Q + "kit overlay: was=" + Q + " + was);",
    "        }",
    "        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());",
    "        UnityEditor.SceneManagement.EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());",
    "        result.Log(" + Q + "scene saved." + Q + ");",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Disable kit overlay + save"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
