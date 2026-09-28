import re
text = open(r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json','r').read()
# Find "foreach (var n in names)\n        {\n"
m = re.search(r'foreach \(var n in names\)\n        \{\n', text)
print('match?', bool(m))
new_text = re.sub(
    r'foreach \(var n in names\)\n        \{\n',
    'foreach (var n in names)\n        {\n            var e = root.Q<VisualElement>(n);\n',
    text,
)
print('changed?', new_text != text)
open(r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json','w').write(new_text)
