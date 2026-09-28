Q = bytes([0x22])
SP = bytes([0x20])
PL = bytes([0x2B])
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

broken = (
    b"return amount.ToString(" + Q + b"0.##" + Q + b") + " + Q + SP + PL + SP + Q + b"+ unit;"
)

fixed = (
    b"return amount.ToString(" + Q + b"0.##" + Q + b") + " + Q + SP + PL + SP + Q + SP + PL + SP + Q + b" + unit;"
)

print("broken matches:", data.count(broken))
data = data.replace(broken, fixed)
with open(p, "wb") as f:
    f.write(data)
print("rewrote")

i = data.find(b"FormatResourceAmount")
print(data[i:i + 600])
