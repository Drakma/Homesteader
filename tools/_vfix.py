import re

src = open('assets/index.html', encoding='utf-8').read()

print('=== dangling references (must all be 0) ===')
for name in ['three: three', 'LIB_READY.three', 'libs[4]', 'libs[5]', 'libs[6]']:
    print(f'  {name:18} -> {src.count(name)}')

print()
print('=== the loader block, as served ===')
i = src.find('window.LIB_READY = (function')
block = src[i:i + 1500]
# Show only the lib array and Promise.all, the parts that matter.
for m in re.finditer(r'var libs = \[(.*?)\];', block, re.S):
    print('--- libs array ---')
    for line in m.group(1).strip().splitlines():
        print('  ', line.strip())

print()
print('=== three.js add-ons are static + ordered ===')
addons = re.findall(r'<script src="[^"]*(OrbitControls|FBXLoader|OBJLoader)[^"]*"', src)
print('static add-on tags found:', addons)

three_pos = src.find('three.min.js')
for a in ['OrbitControls', 'FBXLoader', 'OBJLoader']:
    p = src.find(a)
    print(f'  {a:14} offset {p:7}  after three.min.js ({three_pos})? {p > three_pos}')

print()
print('=== would any add-on be treated as a reportable library? ===')
print('add-ons mentioned in libs array:', any(
    a in re.search(r'var libs = \[(.*?)\];', src, re.S).group(1)
    for a in ['OrbitControls', 'FBXLoader', 'OBJLoader']))

print()
print('=== structure ===')
print('script tags:', len(re.findall(r'<script[^>]*>', src)), '/', src.count('</script>'))
bad = [src[:m.start()].count(chr(10)) + 1
       for m in re.finditer(r'<!--([\s\S]*?)-->', src)
       if '<script' in m.group(1).lower()]
print('comments containing literal <script>:', bad or 'none')
