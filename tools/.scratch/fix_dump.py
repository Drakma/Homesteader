text = open(r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json','r',encoding='utf-8').read()
for sep in ['\r\n', '\n']:
    old = 'foreach (var n in names)' + sep + '        {' + sep
    new = ('foreach (var n in names)' + sep
           + '        {' + sep
           + '            var e = root.Q<VisualElement>(n);' + sep)
    if old in text:
        print('found with sep length:', len(sep))
        text = text.replace(old, new)
        break
open(r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\vitals_dump.json','w',encoding='utf-8',newline='').write(text)
print('rewrote')
