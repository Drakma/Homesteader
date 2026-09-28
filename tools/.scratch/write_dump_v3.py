import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json"
D = chr(34)
S = chr(32)
NL = chr(10)
PLUS = " + "

inner_log_lines = [
    "var e = root.Q<VisualElement>(n);",
    "if (e == null) { result.Log(n + " + D + " NULL" + D + "); continue; }",
    "result.Log(n",
    PLUS + D + " resW=" + D,
    PLUS + "e.resolvedStyle.width",
    PLUS + D + " layoutW=" + D,
    PLUS + "e.layout.width",
    PLUS + D + " flexGrow=" + D,
    PLUS + "e.style.flexGrow.value",
    PLUS + D + " sWv=" + D,
    PLUS + "e.style.width.value",
    ");",
]
inner_log_block = NL.join(" " * 12 + line for line in inner_log_lines)

code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(" + D + "HudRoot" + D + ");",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        var root = doc.rootVisualElement;",
    "        var bindings = hud.GetComponent<Homesteader.UI.HudBindings>();",
    (
        "if (bindings != null) bindings.SendMessage("
        + D + "Update" + D + ", SendMessageOptions.DontRequireReceiver);"
    ),
    (
        "string[] names = new string[] { " + D
        + "VitalWellnessFill" + D + "," + S + D
        + "VitalStaminaFill" + D + "," + S + D
        + "VitalThirstFill" + D + "," + S + D
        + "VitalHungerFill" + D + " };"
    ),
    "        foreach (var n in names)",
    "        {",
]
code_lines.append(inner_log_block)
code_lines += [
    "        }",
    "    }",
    "}",
]
code = NL.join(code_lines)

with open(p, "w") as f:
    f.write(json.dumps({"Code": code, "Title": "Vitals dump"}))
print("wrote", p)
