import re
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

# Find the duplicate entry: the literal `return amount.ToString("0.##") + " + unit;`
# appears twice. We want to delete the SECOND occurrence plus surrounding
# closing braces.

# First occurrence search
matches = list(re.finditer(r'return amount\.ToString\([^)]*\)', text))
print("found", len(matches))

# If 2 matches, find the LATEST one's index, then keep everything
# before the chunk `\n        }\n    }` that closes the duplicate.
if len(matches) >= 2:
    last_m = matches[-1].start()
    # Substring from last_m onward:
    rest = text[last_m:]
    print("from last match:")
    print(repr(rest[:400]))
    # delete entire rest (the duplicate method block + closing braces)
    text = text[:last_m]
    # Now ensure the file is closed properly. The HudState class ends
    # with `}` and the namespace ends with `}` -- so we add the last
    # two closing braces.
    # Technically the file already had its original brace close AFTER
    # the valid first method. So truncating at last_m is the right move.
    # BUT the first occurrence's closing `}` is still present in text[:last_m].
    # Currently text[:last_m] ends in "... + " + unit;\\n        }\\n    }"}
    # which has the right closing braces. Good.
    open(p, "w").write(text)
    print("dedup done")
else:
    print("no duplicate")
