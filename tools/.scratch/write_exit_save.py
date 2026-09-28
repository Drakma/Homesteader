"""Exit play and re-save scene."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\exit_save_after_disable.json"
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
    "        if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;",
    "        result.Log(" + Q + "exiting." + Q + ");",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Exit play"}, indent=2))
print("wrote", p)
