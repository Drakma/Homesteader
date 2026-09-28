"""Capture Game view in play-mode using ScreenCapture.CaptureScreenshot()."""
import json
p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\game_capture.json"
Q = chr(34)
code_lines = [
    "using UnityEngine;",
    "using UnityEditor;",
    "using System.IO;",
    "",
    "internal class CommandScript : IRunCommand",
    "{",
    "    public void Execute(ExecutionResult result)",
    "    {",
    "        if (!EditorApplication.isPlaying) { result.Log(" + Q + "not in play" + Q + "); return; }",
    "        // Trigger a deferred capture. CaptureScreenshot writes a PNG to disk.",
    "        EditorApplication.delayCall += () => {",
    "            ScreenCapture.CaptureScreenshot(" + Q + "C:/Users/casey/Desktop/Homesteader/tools/.scratch/game_view.png" + Q + ");",
    "            result.Log(" + Q + "CaptureScreenshot queued" + Q + ");",
    "        };",
    "    }",
    "}",
]
payload = {"Code": "\n".join(code_lines), "Title": "Game view capture (play)"}
with open(p, "w") as f:
    f.write(json.dumps(payload, indent=2))
print("wrote", p)
