import sys
import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()
text = data.decode("utf-8")
i = text.find("FormatResourceAmount")
print(text[i:i + 600])
