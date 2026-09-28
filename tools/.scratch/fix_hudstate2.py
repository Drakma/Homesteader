"""Repair the broken + unit substitution in HudState.cs."""
p = r'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs'
with open(p, 'r') as f:
    text = f.read()

# 1. The k line:  k.ToString("0.00") + "k " + " + unit;
text = text.replace(
    'k.ToString("0.00") + "k " + " + unit;',
    'k.ToString("0.00") + "k " + unit;'
)

# 2. The non-k line is already correct.
with open(p, 'w') as f:
    f.write(text)

# Verify the two relevant lines.
i = text.find('FormatResourceAmount')
print(text[i:i + 450])
