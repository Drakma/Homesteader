import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

old_method = re.compile(r"public static string FormatResourceAmount\(float amount, string unit\)\s*\{[^}]*\}", re.DOTALL)
m = old_method.search(text)
if not m:
    print("no match")
else:
    print("matched:")
    print(m.group(0))
    replacement = 'public static string FormatResourceAmount(float amount, string unit)\n        {\n            if (amount >= 1000f)\n            {\n                float k = amount / 1000f;\n                return k.ToString("0.00") + "k " + unit;\n            }\n            return amount.ToString("0.##") + " + unit;\n        }'
    text = text[:m.start()] + replacement + text[m.end():]
    open(p, "w").write(text)
    print("rewrote")
    raw = open(p, "r").read()
    i = raw.find("FormatResourceAmount(float")
    print("--- new block ---")
    print(raw[i:i+500])
