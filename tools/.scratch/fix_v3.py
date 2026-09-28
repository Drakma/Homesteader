import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

# Find the broken line via regex so we don't depend on literal quote matches.
# The broken line ends with '+ " + unit;' which is unique.
broken_pat = re.compile(r'return amount\.ToString\([^)]*\)\s*\+\s*"[^"]*\+ unit;')
matches = broken_pat.findall(text)
print("broken matches:", len(matches))
for m in matches:
    print(" ", repr(m))

# Construct the fix using bytes.
D = chr(34)  # double quote
S = chr(32)  # space
# Target literal text: " + unit with surrounding spaces.
# Full correct C#:
#   return amount.ToString("0.##") + " + unit;
fixed_text = (
    "return amount.ToString(" + D + "0.##" + D + ") + " + D + S + D + " + unit;"
)
print("fixed:", fixed_text)

text2 = broken_pat.sub(fixed_text, text)
open(p, "w").write(text2)
print("rewrote")
new_text = open(p, "r").read()
i = new_text.find("FormatResourceAmount")
print("--- new block ---")
print(new_text[i:i+500])
