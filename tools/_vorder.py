import re

src = open('assets/index.html', encoding='utf-8').read()

print('=== real <script src> tags, in document order ===')
pattern = '<script src="[^"]*"'
for m in re.finditer(pattern, src):
    line = src[:m.start()].count('\n') + 1
    tail = m.group(0).rsplit('/', 1)[-1].rstrip('"')
    print(f'  line {line:4}  {tail}')

print()
three = src.find('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"')
print('three.min.js tag offset:', three)
for name in ['OrbitControls.js"', 'FBXLoader.js"', 'OBJLoader.js"']:
    p = src.find(f'<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/'
                 + ('controls/' if 'Orbit' in name else 'loaders/') + f'{name}')
    print(f'  {name:20} tag offset {p:7}  after three tag? {p > three}')
