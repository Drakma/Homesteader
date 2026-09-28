"""Dump UXML tree structure."""
import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\HudUI.uxml"
text = open(p, "r").read()
print("TOTAL LENGTH:", len(text))

# Find <ui:VisualElement ... name="X"> opening and </ui:VisualElement> closing.
i = 0
indent = 0
tag_re = re.compile(r'<ui:VisualElement\b[^>]*name="([^"]+)"[^>]*?>', re.MULTILINE)
close_re = re.compile(r'</ui:VisualElement>', re.MULTILINE)
selfclose_re = re.compile(r'<ui:VisualElement\b[^>]*?/>', re.MULTILINE)

# Self-closing first: not interesting here.
selfclose = list(selfclose_re.finditer(text))
print('self-closing tags:', len(selfclose))

opens = list(tag_re.finditer(text))
closes = list(close_re.finditer(text))
print('opens:', len(opens), 'closes:', len(closes))

# Walk through in order
events = sorted(
    [(m.start(), 'open ', m.group(1)) for m in opens] +
    [(m.start(), 'close', '') for m in closes],
    key=lambda x: x[0]
)
depth = 0
for pos, kind, name in events:
    line = text[:pos].count(chr(10)) + 1
    if kind == 'open ':
        print('  ' * depth + 'open ' + name + ' (line ' + str(line) + ')')
        depth += 1
    else:
        depth -= 1
        print('  ' * depth + 'close (line ' + str(line) + ')')
