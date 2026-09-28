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
    "        // Walk depth 2 and dump visible element info.",
    "        Walk(root, 0, result);",
    "    }",
    "",
    "    private static void Walk(VisualElement e, int depth, ExecutionResult r)",
    "    {",
    "        var prefix = new string(' ', depth * 2);",
    "        var name = string.IsNullOrEmpty(e.name) ? \"(no-name)\" : e.name;",
    "        var classes = e.GetClasses();",
    "        r.Log(prefix + \"name=\" + name + \" cls=[\" + string.Join(\",\", classes) + \"].childCount=\" + e.childCount);",
    "        foreach (var c in e.Children()) Walk(c, depth + 1, r);",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Dump runtime tree"}
with open(p, "w") as f:
    f.write("{}\n".format(json.dumps(payload, indent=2)))
print("wrote", p)
