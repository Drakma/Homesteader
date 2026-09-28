# Probe 2: receive the handshake, then issue a tools/list and a tools/call.
# Pattern is what we expect: handshake frame, then JSON-RPC frames.
import json
import sys
import time
import threading

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe2.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(msg if msg.endswith('\n') else msg + '\n')

open(LOG, 'w').close()

f = open(PIPE, 'rb+', buffering=0)

# Background reader that captures everything until told to stop.
captured = []
stop = threading.Event()
def reader():
    buf = bytearray()
    while not stop.is_set():
        try:
            chunk = f.read(4096)
            if not chunk:
                # pipe closed -> stop
                stop.set()
                break
            buf.extend(chunk)
            while b'\n' in buf:
                line, rest = bytes(buf).split(b'\n', 1)
                captured.append(line.decode('utf-8', errors='replace'))
                buf = bytearray(rest)
        except Exception as e:
            log(f'reader err: {e}')
            stop.set()
            break
    if buf:
        captured.append(bytes(buf).decode('utf-8', errors='replace'))

t = threading.Thread(target=reader, daemon=True)
t.start()

# 1) Send initialize (matches the prior successful probe).
init = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe2","version":"0.0.1"}}}
f.write((json.dumps(init)+'\n').encode('utf-8'))
time.sleep(0.5)

# 2) Send tools/list.
tlst = {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
f.write((json.dumps(tlst)+'\n').encode('utf-8'))
time.sleep(0.5)

# 3) Send a benign tools/call: Unity_GetConsoleLogs with no args.
call = {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":5}}}
f.write((json.dumps(call)+'\n').encode('utf-8'))
time.sleep(1.5)

stop.set()
try:
    f.close()
except Exception:
    pass
t.join(timeout=2)

log(f'captured {len(captured)} frames')
for i, c in enumerate(captured):
    log(f'--- frame {i} ({len(c)} chars) ---')
    # truncate each frame so log stays small but keep enough to inspect schema
    log(c[:1200] + ('...[truncated]' if len(c) > 1200 else ''))
