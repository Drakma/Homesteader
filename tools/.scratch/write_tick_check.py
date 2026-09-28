"""Drive a tick + verify label update (use chr 34 for quote)."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\tick_check.json"
Q = chr(34)  # double quote

code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var ts = Homesteader.UI.TimeSystem.Instance;",
    "        ts.SetSpeed(Homesteader.UI.HomesteaderSpeed.Speed9X);",
    "        ts.Tick(60f);",
    "        var hud = GameObject.Find(" + Q + "HudRoot" + Q + ");",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        var root = doc.rootVisualElement;",
    "        var bindings = hud.GetComponent<Homesteader.UI.HudBindings>();",
    "        if (bindings == null) { result.Log(" + Q + "no bindings" + Q + "); return; }",
    "        bindings.SendMessage(" + Q + "Update" + Q + ", SendMessageOptions.DontRequireReceiver);",
    "        var cl = root.Q<Label>(" + Q + "ClockLabel" + Q + ");",
    "        var dx = root.Q<Label>(" + Q + "DayLabel" + Q + ");",
    "        var sl = root.Q<Label>(" + Q + "SeasonLabel" + Q + ");",
    "        var rw = root.Q<Label>(" + Q + "ResourceWaterLabel" + Q + ");",
    "        var msg = " + Q + "Clock=" + Q + " + (cl != null ? cl.text : " + Q + "??" + Q + ");",
    "        msg = msg + " + Q + " Day=" + Q + " + (dx != null ? dx.text : " + Q + "??" + Q + ");",
    "        msg = msg + " + Q + " Season=" + Q + " + (sl != null ? sl.text : " + Q + "??" + Q + ");",
    "        msg = msg + " + Q + " Water=" + Q + " + (rw != null ? rw.text : " + Q + "??" + Q + ");",
    "        result.Log(msg);",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Tick + verify label"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
