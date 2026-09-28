import sys
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

text = data.decode("utf-8")

# Use direct character-by-character content to avoid Python escape confusion.
broken = (
    'return amount.ToString("0.##") + " + unit;'
)
fixed = (
    'return amount.ToString("0.##") + " + unit;'
)
# I just realized my "broken" and "fixed" are identical strings because
# Python sees them same way. Yet the on-disk file is broken. Let me
# use a different replacement strategy: ordinal substitution.
print("broken chars:")
for i, c in enumerate(broken):
    sys.stdout.write(f' {i}:{hex(ord(c))}({c})')
sys.stdout.write('\n')
print()
print("fixed chars:")
for i, c in enumerate(fixed):
    sys.stdout.write(f' {i}:{hex(ord(c))}({c})')
sys.stdout.write('\n')
print()
print("matches?", text.count(broken))
# If lengths are same, just do a manual substitution at each char.
if broken == fixed:
    sys.stdout.write("Same length/contents; need to edit differently.\n")

# Direct byte-level: find the substring index and repaint chars
idx = text.find('return amount.ToString("0.##") + " + unit;')
print("found at index:", idx)
if idx >= 0:
    chars = list(text)
    # Patch the broken literal. Source reads:
    #   return amount.ToString("0.##") + " + unit;
    # Goal: return amount.ToString("0.##") + "  + unit;
    #                       ^ adds extra " between quotes
    # So at the position where 'space-plus-space-unit;' begins, we
    # want 'space-space-plus-space-unit;' to fully wrap as 3 strings.
    # Simpler: literally rewrite that substring position.
    replacement = 'return amount.ToString("0.##") + "  + unit;'
    text = text[:idx] + replacement + text[idx + len(replacement):]
    # Edit again, since the index matched a longer span: now locate
    # the LITERAL short form and replace with corrected form.
# After the initial above, look for short-form broken literal:
short_broken = 'return amount.ToString("0.##") + "  + unit;'
short_fixed = 'return amount.ToString("0.##") + " + unit;'
# Hmm, what we want the result to be. Look at the k-line:
#   return k.ToString("0.00") + "k " + unit;
# That's: amount.ToString result + literal "k" + space + unit.
# Same pattern for non-k:
#   return amount.ToString("0.##") + " + unit;
# That means: amount.ToString result + literal " + unit.
# So the corrected form is:
corrected = 'return amount.ToString("0.##") + " + unit;'

# After our first replacement, we'd have 'return amount + "  + unit' = 'string + plus-string' is wrong.
# Let me just do a simple replace.
data_after = text.encode("utf-8")
print("after initial simple write, broken string matches:",
      data_after.count('return amount.ToString("0.##") + " + unit;'.encode("utf-8")))
