import json
p = "C:\\Users\\casey\\Desktop\\Homesteader\\tools\\.scratch\\snap_to_disk.json"
with open(p, "r") as f:
    data = json.load(f)
code = data["Code"]
lines = code.split("\n")
for i, l in enumerate(lines):
    if i >= 30: print(i + 1, repr(l))
