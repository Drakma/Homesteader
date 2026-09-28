import sys
p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()
text = data.decode("utf-8")
i = text.find("FormatResourceAmount")
# Print 500 chars with visible CRs
output = text[i:i+500]
sys.stdout.write(repr(output) + "\n")
