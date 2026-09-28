"""Write snap_gameview.json via Python so we don't fight the
bot-backed quote collapsing."""
import json
import os

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\snap_gameview.json"

code_lines = [
    "using UnityEngine;",
    "using UnityEditor;",
    "using System.IO;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        result.Log(\"isPlaying=\" + EditorApplication.isPlaying);",
    "        if (!EditorApplication.isPlaying)",
    "        {",
    "            result.Log(\"not in play mode\");",
    "            return;",
    "        }",
    "        var img = ScreenCapture.CaptureScreenshotAsTexture();",
    "        if (img == null) { result.Log(\"null tex\"); return; }",
    "        var bytes = img.EncodeToPNG();",
    "        var dir = \"C:/Users/casey/Desktop/Homesteader/tools/.scratch\";",
    "        if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);",
    "        File.WriteAllBytes(dir + \"/hud_gameview.png\", bytes);",
    "        result.Log(\"wrote bytes=\" + bytes.Length);",
    "        Object.DestroyImmediate(img);",
    "    }",
    "}",
]
code = "\n".join(code_lines)

payload = {"Code": code, "Title": "Capture game view via ScreenCapture"}

# Write JSON manually so we control all quotes.
json_text = "{}\n".format(json.dumps(payload, indent=2))
with open(p, "w") as f:
    f.write(json_text)

print("wrote", p, "size", os.path.getsize(p))
