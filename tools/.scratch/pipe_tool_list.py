# Probe 5: capture the FULL tool list (it spans many error-message lines).
import json, time

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe5.log'

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
    log(f'>>> [{label}]')
    send(obj)
    resp = read_frame()
    log(f'<<< len={len(resp) if resp else 0}')
    # dump full body for analysis
    if resp:
        log(resp)
    log('')

# init
call('init', {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe5","version":"0.0.1"}}})

# bad tool name to force the server to dump its full catalog.
call('bad_tool', {"type":"tool","name":"__force_list__","arguments":{}})

# try a real tool call. Use one of the names we saw in the truncated list.
call('Unity_ApplyTextEdits_empty', {"type":"tool","name":"Unity_ApplyTextEdits","arguments":{}})

f.close()
