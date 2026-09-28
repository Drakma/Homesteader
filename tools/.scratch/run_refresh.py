import subprocess, sys, json, os, time

os.chdir(r"C:\Users\casey\Desktop\Homesteader")

def run(cmd, out_name):
    out = os.path.join(r"C:\Users\casey\Desktop\Homesteader\tools\.scratch", out_name)
    with open(out, "wb") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    with open(out, "r", encoding="utf-8") as f:
        text = f.read()
    return text

run(["C:\\Python313\\python.exe", r"C:\Users\casey\Desktop\Homesteader\tools\unity_mcp.py", "call", "Unity_RunCommand", "--args-file", r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\refresh_toolkit.json"], "ref_out.json")
time.sleep(16)

# list tools after reload.
subprocess.run(["C:\\Python313\\python.exe", r"C:\Users\casey\Desktop\Homesteader\tools\unity_mcp.py", "list-tools-table"], stdout=subprocess.DEVNULL)

run(["C:\\Python313\\python.exe", r"C:\Users\casey\Desktop\Homesteader\tools\unity_mcp.py", "call", "Unity_GetConsoleLogs", "--args-file", r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\tk_out.json"], "cons_tk.json")
text = run([], "cons_tk.json")
# (run([]) would fail; just read again
text = open(r"C:\Users\casey\Desktop\Homesteader\tools\.scratch\cons_tk.json", "r", encoding="utf-8").read()
print("--- raw console log ---")
print(text[:1500])
