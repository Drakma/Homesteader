import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\force_compile.json"
code = "using UnityEditor;\nusing UnityEditor.Compilation;\n\ninternal class CommandScript : IRunCommand\n{\n    public void Execute(ExecutionResult result)\n    {\n        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);\n        AssetDatabase.SaveAssets();\n        CompilationPipeline.RequestScriptCompilation();\n        result.Log(\"RequestScriptCompilation done.\");\n    }\n}\n"
payload = {"Code": code, "Title": "Force compile"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
