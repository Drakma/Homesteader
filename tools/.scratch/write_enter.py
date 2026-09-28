import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\enter_play_simple.json"
code = (
    "using UnityEditor;\n"
    "internal class CommandScript : IRunCommand\n"
    "{\n"
    "    public void Execute(ExecutionResult result)\n"
    "    {\n"
    "        result.Log(\"isPlaying=\" + EditorApplication.isPlaying + \" isDelayed=\" + EditorApplication.isPlayingDelayed);\n"
    "        if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;\n"
    "        EditorApplication.isPlaying = true;\n"
    "        result.Log(\"set isPlaying=true (req)\");\n"
    "    }\n"
    "}\n"
)
with open(p, "w") as f:
    f.write(json.dumps({"Code": code, "Title": "Enter play direct"}, indent=2))
print("wrote", p)
