"""Write enter_play.json safely via Python."""
import json
import os

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\enter_play2.json"
try: os.remove(p)
except FileNotFoundError: pass

code_lines = [
    "using UnityEditor;",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;",
    "        EditorApplication.delayCall += () => EditorApplication.EnterPlaymode();",
    "        result.Log(\"EnterPlaymode requested.\");",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Enter play"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
