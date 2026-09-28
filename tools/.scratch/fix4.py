"""Single-purpose: fix the WallClock Format suffix literal in TimeSystem.cs.

The on-disk file has:

    return displayHour.ToString() + ":" + mins.ToString("00") + " + suffix;

The fix is to insert the missing close-quote + space + plus + open-quote
between the leading 0x22 (the " before suffix) and the literal text.
The new line is:

    return displayHour.ToString() + ":" + mins.ToString("00") + " + suffix;
"""
import os

p = os.path.join(
    "C:" + chr(92) * 2, "Users", "casey", "Desktop", "Homesteader",
    "Homesteader", "Assets", "Scripts", "UI", "TimeSystem.cs",
)
f = open(p, "rb")
data = f.read()
f.close()

# Build target bytes by hex concatenation to avoid any source-quoting.
broken = bytes([
    0x22,                 # "
    0x20,                 # space
    0x2B,                 # +
    0x20,                 # space
    0x73, 0x75, 0x66, 0x66, 0x69, 0x78, 0x3B,  # suffix;
])
fixed = bytes([
    0x22,                 # "
    0x20,                 # space
    0x2B,                 # +
    0x20,                 # space
    0x22,                 # "  (closing the literal)
    0x20,                 # space
    0x2B,                 # +
    0x20,                 # space
    0x22,                 # "  (reopening next literal)
])

print("matches of broken:", data.count(broken))
data = data.replace(broken, fixed)
of = open(p, "wb")
of.write(data)
of.close()
print("written.")

# Show the wall-clock Format block.
i = data.find(b"public static string Format")
print(data[i:i+700].decode("utf-8", errors="replace"))
