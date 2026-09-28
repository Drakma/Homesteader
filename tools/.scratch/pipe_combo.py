# Probe 6: minimal envelopes without the misleading "type" field.
import json, time

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe6.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

open(LOG, 'w').close()
f = open(PIPE, 'rb+', buffering=0)

def read_frame(timeout=4.0):
    buf = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = f.read(1)
        if not chunk: return None
        buf.extend(chunk)
        if chunk == b'\n': return buf.decode('utf-8', errors='replace')
    return None

def send(obj): f.write((json.dumps(obj) + '\n').encode('utf-8'))
def call(label, obj):
    log(f'>>> [{label}] {json.dumps(obj)[:160]}')
    send(obj)
    r = read_frame()
    log(f'<<< {(r or "NO_RESP")[:400]}')
    log('')

# Handshake.
call('init', {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe6","version":"0.0.1"}}})

# Pure candidates. Read console is safest.
candidates = [
    {"command":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"tool":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"method":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"Unity_GetConsoleLogs":{"maxEntries":2}},
    {"toolName":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"request":{"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}}},
]
for i, c in enumerate(candidates):
    call(f'cand-{i}', c)

f.close()
