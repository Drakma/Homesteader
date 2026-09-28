import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

# Find duplicates of the duplicate-method body.
# After my prior fix, the file ends with:
#   return amount.ToString("0.##") + " + unit;
#       }
#   }
# }
# We want only one method block.

# Strategy: locate the END of HudState class (the final two `}` braces)
# and re-print only the valid methods leading up to it.
# Simpler: pattern-match the trailing duplicate block of `return ...; \n } \n }`
# and delete it.

# That's a specific pattern. The current tail after fixes:
# ... \n      return ...; \n      }\n  }\n}\n
# But now we have ... + " + unit; \n    }   \n} \n} \n}
# (One valid method, then a redundant copy)

# Find ALL instances of "return amount.ToString" and check
hit_indices = []
for m in re.finditer(r'return amount\.ToString\([^)]*\)', text):
    hit_indices.append(m.start())
print("hit positions:", hit_indices)
print("lines:", [text[:i].count(chr(10))+1 for i in hit_indices])

# If there are 2 valid-method blocks, we strip the second. Truncate at
# the LAST 2 lines, since text ends with ' }\\n }\\n' (class end + class close brace).
last_open = hit_indices[-1]
print("last_method_start:", last_open)
print("text after last_method_start:")
print(text[last_open:])
