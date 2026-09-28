import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\enter_play3.json"
Q = chr(34)
code_lines = [
    "using UnityEditor;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;",
    "        EditorApplication.delayCall += () => EditorApplication.isPlaying = true;",
    "        result.Log(" + Q + "queuing play" + Q + ");",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Enter play simple"}, indent=2))
print("wrote", p)
