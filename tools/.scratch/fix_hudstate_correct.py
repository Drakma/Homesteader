Q = bytes([0x22])
SP = bytes([0x20])
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

# Replace the verbatim broken literal with a correct one.
broken = b'return amount.ToString("0.##") + " + unit;'
fixed  = b'return amount.ToString("0.##") + " + unit;'

print("matches:", data.count(broken))
data = data.replace(broken, fixed)
with open(p, "wb") as f:
    f.write(data)
print("rewrote")

i = data.find(b"return amount.ToString(")
print(data[max(0, i-200):i+500].decode("utf-8", errors="replace"))
