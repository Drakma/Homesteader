"""Decode a possible compile-error response from the wrapper."""
import json
import sys

p = r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\cons_after_compile.json"
data = json.load(open(p, "r", encoding="utf-16"))
print("ok=", data.get("ok"))
if "error" in data:
    print("error.message:", data["error"].get("message", "")[:600])
else:
    print("raw top-level keys:", list(data.keys()))
    if "content_blocks" in data:
        for b in data["content_blocks"]:
            print(json.dumps(b, indent=2, ensure_ascii=False)[:600])
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1200])
