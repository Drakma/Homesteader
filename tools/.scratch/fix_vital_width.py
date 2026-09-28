import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudBindings.cs"
text = open(p, "r").read()

# Replace the Length(...) call with StyleLength wrap.
old = "fill.style.width = new Length(barPercent, LengthUnit.Percent);"
new = "fill.style.width = new StyleLength(new Length(barPercent / 100.0f, LengthUnit.Percent));"

print("matches:", text.count(old))
text = text.replace(old, new)
open(p, "w").write(text)
print("rewrote")

i = text.find("fill.style.width")
print(text[max(0, i - 100):i + 200])
