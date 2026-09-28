"""Repair + unit; quotation typo in HudState.cs."""
p = r'C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs'
with open(p, 'r') as f:
    text = f.read()

old = '" + unit;'
new = '" + " + unit;'
print('old search:', repr(old))
print('matches:', text.count(old))
text = text.replace(old, new)
with open(p, 'w') as f:
    f.write(text)
print('done')
