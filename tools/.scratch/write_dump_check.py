"""Write dump_hud_root.json for runtime tree check."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\dump_hud_root.json"
code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(\"HudRoot\");",
    "        if (hud == null) { result.Log(\"no HudRoot\"); return; }",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        if (doc == null) { result.Log(\"no UIDocument\"); return; }",
    "        var root = doc.rootVisualElement;",
    "        if (root == null) { result.Log(\"no root\"); return; }",
    "        result.Log(\"play_state: root.childCount=\" + root.childCount);",
    "        // Print top 2 levels",
    "        Walk(root, 0, result, 2);",
    "    }",
    "",
    "    private static void Walk(VisualElement e, int depth, ExecutionResult r, int maxD)",
    "    {",
    "        var prefix = new string(' ', depth * 2);",
    "        var name = string.IsNullOrEmpty(e.name) ? \"(no-name)\" : e.name;",
    "        r.Log(prefix + name + \" children=\" + e.childCount);",
    "        if (depth + 1 <= maxD)",
    "        {",
    "            foreach (var c in e.Children()) Walk(c, depth + 1, r, maxD);",
    "        }",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Dump runtime tree"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
