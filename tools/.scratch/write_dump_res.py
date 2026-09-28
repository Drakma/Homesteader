"""Dump deeper tree info on Resources block and validate binding labels exist."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\dump_resources.json"
code_lines = [
    "using UnityEngine;",
    "using UnityEngine.UIElements;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        var hud = GameObject.Find(\"HudRoot\");",
    "        var doc = hud.GetComponent<UIDocument>();",
    "        var root = doc.rootVisualElement;",
    "        var resourcesView = root.Q<VisualElement>(\"Resources\");",
    "        if (resourcesView == null) { result.Log(\"Resources view NOT found by name\"); return; }",
    "        result.Log(\"Resources children=\" + resourcesView.childCount);",
    "        foreach (var c in resourcesView.Children())",
    "        {",
    "            result.Log(\"  child: name=\" + c.name + \" cls=\" + string.Join(\",\", c.GetClasses()));",
    "            foreach (var gc in c.Children())",
    "            {",
    "                result.Log(\"    gc: name=\" + gc.name + \" cls=\" + string.Join(\",\", gc.GetClasses()));",
    "            }",
    "        }",
    "        // Verify bindings names live somewhere",
    "        var sw = root.Q<Label>(\"SeasonLabel\");",
    "        var dx = root.Q<Label>(\"DayLabel\");",
    "        var cl = root.Q<Label>(\"ClockLabel\");",
    "        var sp = root.Q<Button>(\"Speed1X\");",
    "        var rw = root.Q<Label>(\"ResourceWaterLabel\");",
    "        var vs0 = root.Q<VisualElement>(\"ToolbarSlot0\");",
    "        result.Log(\"SeasonLabel=\" + (sw != null ? sw.text : \"NULL\"));",
    "        result.Log(\"DayLabel=\" + (dx != null ? dx.text : \"NULL\"));",
    "        result.Log(\"ClockLabel=\" + (cl != null ? cl.text : \"NULL\"));",
    "        result.Log(\"Speed1X=\" + (sp != null ? \"found\" : \"NULL\"));",
    "        result.Log(\"ResourceWaterLabel=\" + (rw != null ? rw.text : \"NULL\"));",
    "        result.Log(\"ToolbarSlot0=\" + (vs0 != null ? \"found\" : \"NULL\"));",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Dump resources block + binding names"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
