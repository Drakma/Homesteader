"""Second fix on FormatResourceAmount."""
import os
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

# Use bytes which avoids Python string escape weirdness.

Q = bytes([0x22])  # "
SPACE = bytes([0x20])
PLUS = bytes([0x2B])

broken_b = (
    b'return amount.ToString(' + Q + b'0.##' + Q + b') + ' + Q + SPACE + PLUS +
    SPACE + Q + b'+ unit;'
)
fixed_b = (
    b'return amount.ToString(' + Q + b'0.##' + Q + b') + ' + Q + SPACE +
    PLUS + SPACE + Q + SPACE + PLUS + SPACE + Q + b'+ unit;'
)

# Wait, what's the correct C# source?
correct = (
    b'return amount.ToString(' + Q + b'0.##' + Q + b') + ' + Q + SPACE +
    PLUS + SPACE + Q + SPACE + PLUS + SPACE + Q + b' + unit;'
)

print("broken in data:", data.count(broken_b))
data = data.replace(broken_b, correct)
with open(p, "wb") as f:
    f.write(data)
print("replaced")
import os
os.system("python -c \"" + "print(open(r'" + p + "', 'rb').read().decode('utf-8'))" + "\"")
