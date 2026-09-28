import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_probe.json"
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
    "        var doc = hud.GetComponent<UIDocument>();",
    "        var root = doc.rootVisualElement;",
    "        var bindings = hud.GetComponent<Homesteader.UI.HudBindings>();",
    "        if (bindings != null)",
    "        {",
    "            bindings.SendMessage(" + Q + "Update" + Q + ", SendMessageOptions.DontRequireReceiver);",
    "        }",
    "        var fillWellness = root.Q<VisualElement>(" + Q + "VitalWellnessFill" + Q + ");",
    "        var fillStamina  = root.Q<VisualElement>(" + Q + "VitalStaminaFill" + Q + ");",
    "        var fillThirst   = root.Q<VisualElement>(" + Q + "VitalThirstFill" + Q + ");",
    "        var fillHunger   = root.Q<VisualElement>(" + Q + "VitalHungerFill" + Q + ");",
    "        result.Log(" + Q + "VitalWellnessFill width=" + Q + " + (fillWellness != null ? fillWellness.style.width.value : -1f) + " + Q + " %; rawValue=" + Q + " + Homesteader.UI.HudState.Active.Vitals[Homesteader.UI.VitalId.Wellness].Value);",
    "        result.Log(" + Q + "VitalStaminaFill  width=" + Q + " + (fillStamina != null ? fillStamina.style.width.value : -1f) + " + Q + " %" + Q + ");",
    "        result.Log(" + Q + "VitalThirstFill   width=" + Q + " + (fillThirst != null ? fillThirst.style.width.value : -1f) + " + Q + " %" + Q + ");",
    "        result.Log(" + Q + "VitalHungerFill   width=" + Q + " + (fillHunger != null ? fillHunger.style.width.value : -1f) + " + Q + " %" + Q + ");",
    "        var pcts = new string[] { " + Q + "VitalWellnessPct" + Q + ", " + Q + "VitalStaminaPct" + Q + ", " + Q + "VitalThirstPct" + Q + ", " + Q + "VitalHungerPct" + Q + " };",
    "        foreach (var n in pcts)",
    "        {",
    "            var l = root.Q<Label>(n);",
    "            result.Log(n + " + Q + " text=" + Q + " + (l != null ? l.text : " + Q + "?" + Q + "));",
    "        }",
    "    }",
    "}",
]
with open(p, "w") as f:
    f.write(json.dumps({"Code": "\n".join(code_lines), "Title": "Vital widths probe"}, indent=2))
print("wrote", p)
