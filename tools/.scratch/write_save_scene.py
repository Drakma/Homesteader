"""save_scene.py - explicitly mark scene dirty and save it."""
import json
import os

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\save_scene.json"
code_lines = [
    "using UnityEditor;",
    "using UnityEditor.SceneManagement;",
    "using UnityEngine.SceneManagement;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var scn = SceneManager.GetActiveScene();",
    "        if (!scn.IsValid()) { result.Log(\"invalid\"); return; }",
    "        EditorSceneManager.MarkSceneDirty(scn);",
    "        EditorSceneManager.SaveScene(scn);",
    "        result.Log(\"saved \" + scn.path);",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write("{}\n".format(json.dumps({"Code": "\n".join(code_lines), "Title": "Save scene"}, indent=2)))
print("wrote", p, os.path.getsize(p))
