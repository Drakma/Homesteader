import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudBindings.cs"
text = open(p, "r").read()
# Try a different approach - use Length directly with auto-converted px.
# The previous put /100 already done. Now make it clear numeric and set unit.
older = "fill.style.width = new StyleLength(new Length(barPercent / 100.0f, LengthUnit.Percent));"
newer = "fill.style.width = Length.Percent(barPercent);"

print("matches:", text.count(older))
text = text.replace(older, newer)
open(p, "w").write(text)
print("rewrote")

i = text.find("fill.style.width")
print(text[max(0, i - 100):i + 200])
