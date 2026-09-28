import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\force_exit.json"
Q = chr(34)
code_lines = [
    "using UnityEditor;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        result.Log(" + Q + "isPlaying(before)=" + Q + " + EditorApplication.isPlaying);",
    "        if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;",
    "        result.Log(" + Q + "isPlaying(after)=" + Q + " + EditorApplication.isPlaying);",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Force exit"}, indent=2))
print("wrote", p)
