"""Replace broken WallClock suffix literal in TimeSystem.cs."""
import os

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Scripts\UI\TimeSystem.cs"
with open(p, "r") as f:
    t = f.read()

# Build the literal pieces in Python without messing with embedding
# the source's quote characters.
D = chr(34)        # A double-quote character.
broken = " + suffix;" + D + ";"
fixed  = " + suffix;" + D + " "

# Apply targeted patch anchored on the wall-clock return line.
old_line = "return displayHour.ToString()" + D + ":" + D + " + " + "mins.ToString(" + D + "00" + D + ")" + D + broken
new_line = "return displayHour.ToString()" + D + ":" + D + " + " + "mins.ToString(" + D + "00" + D + ")" + D + fixed + "suffix;"

print("matches of old_line:", t.count(old_line))
t = t.replace(old_line, new_line)
with open(p, "w") as f:
    f.write(t)
print("Applied.")

i = t.find("public static string Format")
print(t[i:i + 700])
