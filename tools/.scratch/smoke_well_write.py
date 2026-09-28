"""Rewrite HudUI.uss to use proper sizes and 2px borders + tint backgrounds."""
import os
import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\HudUI.uss"
with open(p, "r") as f:
    text = f.read()

# Read the file as a sequence of rule blocks. Find rules we want to
# replace.

def replace_block(text, start_marker, end_marker, new_block):
    i = text.find(start_marker)
    if i < 0: return text
    j = text.find(end_marker, i)
    if j < 0: j = len(text)
    return text[:i] + new_block + text[j+len(end_marker):]

# Hold back: don't touch the original comment away. We're selectively rewriting rules.

# Edit individual rule lines.

def replace_rule(text, selector, new_body):
    """Find a rule starting at `selector {` and replace up to its closing `}`."""
    pattern = re.compile(
        re.escape(selector) + r"\s*\{(.*?)\}",
        re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        print(f"missing selector: {selector}")
        return text
    return pattern.sub(selector + " {\n" + new_body.rstrip("\n") + "\n}", text)

# 1. held-asset bar
text = replace_rule(text, ".held-asset-bar", """
    flex-direction: row;
    align-items: center;
    justify-content: center;
    height: 48px;
    padding: 6px 20px;
    border-color: rgb(193, 154, 60);
    border-width: 2px;
    border-radius: 6px;
    background-color: rgb(20, 26, 32);
""")

# 2. status-bar
text = replace_rule(text, ".status-bar", """
    flex-direction: row;
    align-items: center;
    height: 72px;
    flex-shrink: 0;
    padding: 10px 16px;
""")

# 3. status-section
text = replace_rule(text, ".status-section", """
    flex-direction: row;
    align-items: center;
    height: 40px;
    padding-left: 8px;
    padding-right: 8px;
    flex-shrink: 1;
""")

# 4. status-label
text = replace_rule(text, ".status-label", """
    color: rgb(220, 224, 230);
    font-size: 16px;
    -unity-font: var(--font-bold);
    -unity-text-align: middle-center;
    margin-left: 6px;
    margin-right: 6px;
    height: 28px;
""")

# 5. time-label
text = replace_rule(text, ".time-label", """
    color: rgb(241, 196, 15);
    font-size: 20px;
    -unity-font: var(--font-bold);
    -unity-text-align: middle-center;
    height: 30px;
    margin-left: 8px;
""")

# 6. well
text = replace_rule(text, ".well", """
    border-color: rgb(120, 136, 153);
    border-width: 2px;
    border-radius: 6px;
    background-color: rgb(34, 43, 58);
    height: 40px;
    flex-direction: row;
    align-items: center;
    padding-left: 8px;
    padding-right: 8px;
    flex-shrink: 1;
""")

# 7. icon-tile
text = replace_rule(text, ".icon-tile", """
    width: 28px;
    height: 28px;
    margin-right: 4px;
    border-color: rgb(10, 14, 21);
    border-width: 2px;
    border-radius: 4px;
    background-color: rgb(34, 43, 58);
    flex-shrink: 0;
""")

# 8. label-tile
text = replace_rule(text, ".label-tile", """
    color: rgb(220, 224, 230);
    font-size: 16px;
    -unity-font: var(--font);
    -unity-text-align: middle-left;
    padding-left: 6px;
    padding-right: 8px;
    height: 24px;
    white-space: nowrap;
    flex-shrink: 0;
""")

# 9. speed-chip
text = replace_rule(text, ".speed-chip", """
    width: 44px;
    height: 28px;
    margin-left: 4px;
    border-color: rgb(120, 136, 153);
    border-width: 2px;
    border-radius: 4px;
    background-color: rgb(34, 43, 58);
    -unity-font: var(--font-medium);
    color: rgb(220, 224, 230);
    font-size: 13px;
    -unity-text-align: middle-center;
    flex-shrink: 0;
""")

# 10. status-row
text = replace_rule(text, ".status-row", """
    flex-direction: row;
    align-items: center;
    height: 32px;
""")

# 11. toolbar
text = replace_rule(text, ".toolbar", """
    flex-direction: row;
    align-self: center;
    align-items: center;
    height: 120px;
    padding: 12px 20px;
    border-color: rgb(120, 136, 153);
    border-width: 2px;
    border-top-width: 2px;
    border-radius: 8px 8px 0 0;
    background-color: rgb(20, 26, 32);
    margin-top: auto;
    flex-shrink: 0;
""")

# 12. tool-slot
text = replace_rule(text, ".tool-slot", """
    width: 80px;
    height: 80px;
    margin-left: 6px;
    border-color: rgb(120, 136, 153);
    border-width: 2px;
    border-radius: 6px;
    background-color: rgb(34, 43, 58);
    flex-direction: column;
    align-items: center;
    padding: 0;
    flex-shrink: 0;
""")

# 13. tool-slot--selected
text = replace_rule(text, ".tool-slot--selected", """
    border-color: rgb(193, 154, 60);
    border-width: 3px;
    background-color: rgb(60, 76, 92);
""")

# 14. tool-icon
text = replace_rule(text, ".tool-icon", """
    width: 64px;
    height: 64px;
    margin-top: 4px;
    border-color: rgb(10, 14, 21);
    border-width: 2px;
    border-radius: 4px;
    background-color: rgb(60, 76, 92);
    flex-shrink: 0;
""")

# 15. tool-count
text = replace_rule(text, ".tool-count", """
    color: rgb(241, 196, 15);
    font-size: 14px;
    -unity-font: var(--font-bold);
    -unity-text-align: middle-center;
    width: 72px;
    height: 16px;
    margin-top: 4px;
    white-space: nowrap;
""")

with open(p, "w") as f:
    f.write(text)
print("rewrote", p, "size", os.path.getsize(p))
