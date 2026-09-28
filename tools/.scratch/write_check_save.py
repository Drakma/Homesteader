import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\check_save_state.json"
Q = chr(34)
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
    "        if (!scn.IsValid()) { result.Log(" + Q + "invalid" + Q + "); return; }",
    "        EditorSceneManager.MarkSceneDirty(scn);",
    "        EditorSceneManager.SaveScene(scn);",
    "        result.Log(" + Q + "isPlaying=" + Q + " + EditorApplication.isPlaying);",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Save + check state"}, indent=2))
print("wrote", p)
