Q = bytes([0x22])
SP = bytes([0x20])
PL = bytes([0x2B])
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

# Find every line containing amount.ToString. Show them
for line in data.splitlines(True):
    if b"amount.ToString" in line:
        print(line)

# Build the broken literal byte-by-byte.
broken_exact = (
    b"return amount.ToString(" + Q + b"0.##" + Q + b") + " + Q + SP + PL + SP
    + Q + b"+ unit;"
)
print("---")
print("broken_exact:", broken_exact)
print("matches:", data.count(broken_exact))
