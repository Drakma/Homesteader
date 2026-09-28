# Lightweight one-shot probe: open named pipe, send MCP 'initialize', capture reply.
# Stdout / stderr is captured to disk so JSON-RPC frames stay intact (no Python prints into the stream).
import os
import sys
import json
import time

PIPE = r'\\.\pipe\unity-mcp-5aacaf45-37412'
LOG  = r'C:\Users\casey\Desktop\Homesteader\tools\.scratch\pipe_probe.log'

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(msg if msg.endswith('\n') else msg + '\n')

# Truncate log.
open(LOG, 'w').close()

log(f'connect at {time.time()}')
try:
    # Open with raw binary read/write (no newline translation).
    f = open(PIPE, 'rb+', buffering=0)
    log('opened pipe')
    # MCP 'initialize' handshake.
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "probe", "version": "0.0.1"}
        }
    }
    line = (json.dumps(payload) + '\n').encode('utf-8')
    f.write(line)
    log(f'sent {len(line)} bytes: {line!r}')
    # Read whatever is available with a short budget.
    f.flush()
    chunks = []
    deadline = time.time() + 3.0
    while time.time() < deadline:
        try:
            chunk = f.read(4096)
            if not chunk:
                break
            chunks.append(chunk)
        except Exception as e:
            log(f'read err: {e}')
            break
        if chunks and b'\n' in b''.join(chunks):
            break
    body = b''.join(chunks)
    log(f'received {len(body)} bytes')
    log('--- raw ---')
    log(body.decode('utf-8', errors='replace'))
    log('--- end ---')
    f.close()
except Exception as e:
    log(f'top-level error: {type(e).__name__}: {e}')
