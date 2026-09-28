import re

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

# The HudState class needs to close, then the namespace.
# Currently ends: '        }\n            '
# That's closing brace of method + whitespace. We stripped the rest.
# Append: '    }\n}\n' to close class + namespace.
# Verify last_line is the method closing brace, then append.

# Truncate trailing whitespace.
text = text.rstrip() + chr(10)

# Append class close + namespace close.
text += "}" + chr(10) + "}" + chr(10)

open(p, "w").write(text)
print("rewrote")

# Check braces
print("open:", text.count("{"), "close:", text.count("}"))
