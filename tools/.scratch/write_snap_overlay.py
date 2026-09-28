"""Re-write snap_gameview.json (delayCall version)."""
import json
import os

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\snap_gameview.json"
code_lines = [
    "using UnityEngine;",
    "using UnityEditor;",
    "using System.IO;",
    "using System.Collections;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        if (!EditorApplication.isPlaying)",
    "        {",
    "            result.Log(\"not in play mode\");",
    "            return;",
    "        }",
    "        EditorApplication.delayCall += () => {",
    "            var img = ScreenCapture.CaptureScreenshotAsTexture();",
    "            if (img == null) { result.Log(\"null texture\"); return; }",
    "            var bytes = img.EncodeToPNG();",
    "            var dir = \"C:/Users/casey/Desktop/Homesteader/tools/.scratch\";",
    "            if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);",
    "            File.WriteAllBytes(dir + \"/hud_gameview.png\", bytes);",
    "            result.Log(\"wrote bytes=\" + bytes.Length);",
    "            Object.DestroyImmediate(img);",
    "        };",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Capture game view after end-of-frame"}
with open(p, "w") as f:
    f.write("{}\n".format(json.dumps(payload, indent=2)))
print("wrote", p, "size", os.path.getsize(p))
