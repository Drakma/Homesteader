import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json"
Q = chr(34)
SP = chr(32)
PLUS = " + "

names_array = (
    "string[] names = new string[] { "
    + Q + "VitalWellnessFill" + Q + ","
    + SP + Q + "VitalStaminaFill" + Q + ","
    + SP + Q + "VitalThirstFill" + Q + ","
    + SP + Q + "VitalHungerFill" + Q + " };"
)

# Build labeled OK lines by explicit + between parts.
fmt = (
    "n" + PLUS + Q + " resW=" + Q
    + PLUS + "e.resolvedStyle.width"
    + PLUS + Q + " layoutW=" + Q
    + PLUS + "e.layout.width"
    + PLUS + Q + " flexGrow=" + Q
    + PLUS + "e.style.flexGrow.value"
    + PLUS + Q + " sWv=" + Q
    + PLUS + "e.style.width.value"
    + PLUS + Q + " sWu=" + Q
    + PLUS + "(int)e.style.width.unit"
)

inner_log = "result.Log(" + fmt + ");"

code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(" + Q + "HudRoot" + Q + ");",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        var root = doc.rootVisualElement;",
    "        var bindings = hud.GetComponent<Homesteader.UI.HudBindings>();",
    (
        "if (bindings != null) bindings.SendMessage("
        + Q + "Update" + Q + ", SendMessageOptions.DontRequireReceiver);"
    ),
    SP + names_array,
    "        foreach (var n in names)",
    "        {",
    SP + inner_log,
    "        }",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Vitals dump"}, indent=2))
print("wrote", p)
print("\n".join(code_lines))
