import sys
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

# Approach: regex on text.
import re
text = data.decode("utf-8")
m = re.findall(r"return amount\.ToString\([^)]*\)\s*\+\s*[^\n]+", text)
for x in m:
    sys.stdout.write(x + "\n")
