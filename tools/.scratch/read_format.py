import sys
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()
broken = b'return amount.ToString("0.##") + " + unit;'
print("matches broken:", data.count(broken))
# Read 600 bytes around FormatResourceAmount
i = data.find(b'FormatResourceAmount')
sys.stdout.write(repr(data[i:i+600]))
