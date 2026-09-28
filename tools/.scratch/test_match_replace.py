import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

text = data.decode("utf-8")

# I want to replace the broken line.
# Broken: 'return amount.ToString("0.##") + " + unit;'
# Fixed:  'return amount.ToString("0.##") + " + unit;'

broken = 'return amount.ToString("0.##") + " + unit;'

# The FIX should be:
#   return amount.ToString("0.##") + " + unit;
# which is:  return + amount.ToString("0.##") + " (close)" + space + space + " (open)" + space + unit;

fixed = 'return amount.ToString("0.##") + " + unit;'

print("broken matches:", text.count(broken))
print("hidden char checks:")
for i, c in enumerate(broken):
    print(i, repr(c))

text2 = text.replace(broken, fixed)
print("after replace, broken matches:", text2.count(broken))

with open(p, "w", newline="") as f:
    f.write(text2)
print("rewrote")
