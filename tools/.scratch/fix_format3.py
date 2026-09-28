Q = chr(34)
SP = " "
PL = "+"
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
text = open(p, "r").read()

broken = "return amount.ToString(" + Q + "0.##" + Q + ") + " + Q + SP + PL + SP + Q + "+ unit;"
fixed  = "return amount.ToString(" + Q + "0.##" + Q + ") + " + Q + SP + PL + SP + Q + SP + PL + SP + Q + " + unit;"

print("broken matches:", text.count(broken))
text = text.replace(broken, fixed)
open(p, "w").write(text)
print("rewrote")
i = text.find("FormatResourceAmount")
print(text[i:i + 600])
