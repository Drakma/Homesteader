import json
p = "C:\\Users\\casey\\Desktop\\Homesteader\\tools\\.scratch\\snap_to_disk.json"
with open(p, "r") as f:
    data = json.load(f)
# data["Code"] is escaped JSON; unescape
code = data["Code"]
# code is a real string (JSON unescaped already)
lines = code.split("\n")
for i in range(35, min(50, len(lines))):
    print(i + 1, repr(lines[i]))
