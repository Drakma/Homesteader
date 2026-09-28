p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

text = data.decode("utf-8")

# The text reads at character level (from dump):
# r e t u r n   a m o u n t . T o S t r i n g ( " 0 . # " )  + " (space) u n i t ;
# So literal: return amount.ToString("0.##") + " + unit;
# With " closing AFTER the leading space: " ";
# then concatenated with `+ unit;` -- where `unit` is the parameter.
# That's: amount.ToString result + " + unit.

broken = 'return amount.ToString("0.##") + " + unit;'
fixed  = 'return amount.ToString("0.##") + " + unit;'

# Both are 42 chars; may be byte-identical. Let me verify by re-typing with explicit escapes.

import typing
broken_v2 = (
    chr(114) + chr(101) + chr(116) + chr(117) + chr(114) + chr(110) + chr(32)
    + chr(97) + chr(109) + chr(111) + chr(117) + chr(110) + chr(116)
    + chr(46) + chr(84) + chr(111) + chr(83) + chr(116) + chr(114) + chr(105) + chr(110) + chr(103)
    + chr(40) + chr(34) + chr(48) + chr(46) + chr(35) + chr(35) + chr(34)
    + chr(41) + chr(32) + chr(43) + chr(32)
    + chr(34) + chr(32) + chr(43) + chr(32) + chr(117) + chr(110) + chr(105) + chr(116) + chr(59)
print("broken_v2:", broken_v2)
print("length:", len(broken_v2))

# Try matching
print("matches:", text.count(broken_v2))
