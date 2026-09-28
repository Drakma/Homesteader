import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\test_inspect_tree.json"
Q = chr(34)
code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(" + Q + "HudRoot" + Q + ");",
    "        if (hud == null) { result.Log(" + Q + "no HudRoot" + Q + "); return; }",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        if (doc == null || doc.rootVisualElement == null) { result.Log(" + Q + "no UIDocument or root" + Q + "); return; }",
    "        var root = doc.rootVisualElement;",
    "        Walk(root, 0, result);",
    "    }",
    "",
    "    private static void Walk(VisualElement e, int depth, ExecutionResult r)",
    "    {",
    "        string prefix = new string(' ', depth * 2);",
    "        string name = string.IsNullOrEmpty(e.name) ? " + Q + "(none)" + Q + " : e.name;",
    "        string cls = " + Q + "[" + Q + " + string.Join(" + Q + "," + Q + ", e.GetClasses()) + " + Q + "]" + Q + ";",
    "        r.Log(prefix + name + cls + " + Q + " children=" + Q + " + e.childCount);",
    "        foreach (var c in e.Children()) Walk(c, depth + 1, r);",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Walk HUD tree"}, indent=2))
print("wrote", p)
