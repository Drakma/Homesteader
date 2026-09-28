"""Restore the + suffix; literal in TimeSystem.cs after the previous fix
dropped the word 'suffix'."""
import os
p = os.path.join("C:" + chr(92) * 2, "Users", "casey", "Desktop",
                 "Homesteader", "Homesteader", "Assets", "Scripts",
                 "UI", "TimeSystem.cs")
f = open(p, "rb")
data = f.read()
f.close()

# After fix4 the on-disk line is:
#   return displayHour.ToString() + ":" + mins.ToString("00") + " + " + "
# We want:
#   return displayHour.ToString() + ":" + mins.ToString("00") + " + " + suffix;
#
# The broken line ends with the literal ' + " + " + "' followed by EOL.
# Replace it with the correct concat tail.
broken = bytes([
    0x2B,                 # +
    0x20,                 # space
    0x22,                 # "
    0x20,                 # space
    0x2B,                 # +
    0x20,                 # space
    0x22,                 # "
])
# Append 0xA or 0xD 0xA newline. We'll search for `broken + newline` so
# we replace the run of bytes including its terminator.
eols = [b"\r\n", b"\n", b"\r"]
for eol in eols:
    cnt = data.count(broken + eol)
    print("matches of broken+EOL(" + repr(eol) + "):", cnt)

# Try each EOL until we find a match.
for eol in eols:
    target = broken + eol
    if data.count(target) > 0:
        replacement = (bytes([
            0x2B, 0x20, 0x22, 0x20, 0x2B, 0x20,
            0x22, 0x20, 0x2B, 0x20,                               # + space
            0x73, 0x75, 0x66, 0x66, 0x69, 0x78, 0x3B,             # suffix;
        ]) + eol)
        data = data.replace(target, replacement)
        print("Applied using EOL=" + repr(eol))
        break

open(p, "wb").write(data)
print("written.")

i = data.find(b"public static string Format")
print(data[i:i+700].decode("utf-8", errors="replace"))
