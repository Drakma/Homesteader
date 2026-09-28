import sys
import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()
text = data.decode("utf-8")

# Show the broken FormatResourceAmount block in detail
i = text.find("FormatResourceAmount")
block = text[i:i + 600]
print("--- block ---")
for j, ch in enumerate(block):
    if ch == " or ch == "\n": continue
    if j > 0 and (block[j-1] == " or block[j-1] == "\n"): print()
    sys.stdout.write(ch)
print()
print()
print("--- raw ---")
sys.stdout.write(block[:600])
