import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_match = re.search(r'<script>([\s\S]*?)</script>', html)
script = script_match.group(1)

ids_in_script = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]", script))
ids_in_html = set(re.findall(r'id=[\'"]([^\'"]+)[\'"]', html))

missing = []
for i in ids_in_script:
    if i not in ids_in_html:
        # check if it's dynamic
        missing.append(i)

print(f"Total IDs referenced in script: {len(ids_in_script)}")
print(f"Missing IDs: {missing}")

# Check filter button IDs
for cat in ['All', 'Farming', 'Ranching', 'Logging', 'Fishing', 'Building', 'Tools', 'Electricity', 'Water', 'Sewage', 'Internet', 'Hud']:
    b_id = f"btnFilter{cat}"
    if b_id not in ids_in_html:
        print(f"Missing filter button: {b_id}")

for fcat in ['All', 'Trees', 'Bushes', 'Brambles', 'Grasses', 'Features']:
    b_id = f"btnFilterFoliage{fcat}"
    if b_id not in ids_in_html:
        print(f"Missing foliage filter button: {b_id}")

