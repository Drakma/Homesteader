# Probe 3: strict request/response over the named pipe.
# Each frame: write -> drain until newline -> read next.
import json, sys, time

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe3.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(msg if msg.endswith('\n') else msg + '\n')

open(LOG, 'w').close()

f = open(PIPE, 'rb+', buffering=0)

def read_frame(timeout=4.0):
    buf = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        chunk = f.read(1)
        if not chunk:
            return None
        buf.extend(chunk)
        if chunk == b'\n':
            return buf.decode('utf-8', errors='replace')
    return None

def send(obj):
    f.write((json.dumps(obj) + '\n').encode('utf-8'))

def call(label, obj, want_full=True):
    log(f'>>> {label}: {json.dumps(obj)[:200]}')
    send(obj)
    resp = read_frame()
    if resp is None:
        log('!!! no response\n')
        return
    log(f'<<< response ({len(resp)} chars)')
    log(resp if want_full else resp[:500])

# Step 1: handshake (initialize).
call('initialize', {
    "jsonrpc":"2.0","id":1,"method":"initialize",
    "params":{"protocolVersion":"2024-11-05","capabilities":{},
             "clientInfo":{"name":"probe3","version":"0.0.1"}}
}, want_full=False)

# Step 2: tools/list (we already saw the catalog in handshake but we want a fresh
# server-side list to confirm the JSON-RPC route works).
call('tools/list', {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})

# Step 3: cheap benign tool call. Unity_GetConsoleLogs with maxEntries=2.
call('Unity_GetConsoleLogs', {
    "jsonrpc":"2.0","id":3,"method":"tools/call",
    "params":{"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}}
})

f.close()
log('--- done ---')
