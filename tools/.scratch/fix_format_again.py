import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "r") as f:
    text = f.read()

# Find specific broken patterns.
k_pat = re.compile(r'return k\.ToString\("[^"]*"\)\s*\+\s*"k"\s*\+\s*unit;')
k_fix = 'return k.ToString("0.00") + "k" + unit;'

print("k broken matches:", len(k_pat.findall(text)))
text = k_pat.sub(k_fix, text)

a_pat = re.compile(r'return amount\.ToString\("[^"]*"\)\s*\+\s*"[^"]*\+ unit;')
a_fix = 'return amount.ToString("0.##") + " + unit;'

print("a broken matches:", len(a_pat.findall(text)))
text = a_pat.sub(a_fix, text)

with open(p, "w") as f:
    f.write(text)
print("rewrote")
i = text.find("FormatResourceAmount")
print(text[i:i+500])
