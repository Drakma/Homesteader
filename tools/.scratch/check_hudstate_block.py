p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\HudState.cs"
with open(p, "rb") as f:
    data = f.read()

# Print 500 bytes around the broken line to see context.
i = data.find(b"return amount.ToString(")
print("at index:", i)
print()
print(data[max(0, i-200):i+500].decode("utf-8", errors="replace"))
