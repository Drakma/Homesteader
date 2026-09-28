# Probe 4: try various non-MCP envelope shapes for actual tool calls.
# The handshake already told us what tools exist. The question is: what JSON
# does the relay want to actually invoke a tool?
import json, time

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe4.log'

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
        if not chunk: return None
        buf.extend(chunk)
        if chunk == b'\n': return buf.decode('utf-8', errors='replace')
    return None

def send(obj):
    f.write((json.dumps(obj) + '\n').encode('utf-8'))

def call(label, obj):
    log(f'>>> [{label}]: {json.dumps(obj)[:160]}')
    send(obj)
    resp = read_frame()
    log(f'<<< {resp[:300] if resp else "NO RESP"}' )
    log('')

# Handshake first so server knows we're initialized.
call('init', {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe4","version":"0.0.1"}}})

# Plausible envelope candidates for tool invocation.
candidates = [
    # name + arguments
    {"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"tool":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"command":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"method":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"type":"tool","name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"action":"call","name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"type":"call","name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    # claim it is a request
    {"type":"request","name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    {"type":"invoke","name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    # tablet with a body
    {"type":"call","tool":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
    # full JSON-RPC with extra fields
    {"jsonrpc":"2.0","id":2,"type":"call","method":"tools/call","params":{"name":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}}},
    {"jsonrpc":"2.0","id":3,"type":"tool","method":"Unity_GetConsoleLogs","params":{"maxEntries":2}},
    {"jsonrpc":"2.0","id":4,"command":"Unity_GetConsoleLogs","arguments":{"maxEntries":2}},
]

for i, c in enumerate(candidates):
    call(f'cand-{i}', c)

f.close()
log('--- done ---')
