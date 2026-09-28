"""Patch FormatResourceAmount in HudState.cs so the unit shows without a +."""
import os
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "r") as f:
    text = f.read()
# Replace 'return amount.ToString("0.##") + " + " + unit;' with a proper " + space + unit.
old = 'return amount.ToString("0.##") + " + " + unit;'
new = 'return amount.ToString("0.##") + " + unit;'
print("matches:", text.count(old))
text = text.replace(old, new)
with open(p, "w") as f:
    f.write(text)
print("replaced")
# Verify
i = text.find("FormatResourceAmount")
print(text[i:i+400])
