import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\refresh_toolkit.json"
Q = chr(34)
code_lines = [
    "using UnityEditor;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);",
    "        AssetDatabase.SaveAssets();",
    "        result.Log(" + Q + "refresh complete." + Q + ");",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Refresh"}, indent=2))
print("wrote", p)
