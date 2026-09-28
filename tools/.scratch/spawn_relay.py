# Spawn a brand new relay_win.exe in --mcp mode and talk MCP to its stdio.
# This bypasses the running relay entirely and gives us a clean stdio MCP server.
import subprocess, json, time, sys, os

RELAY = r'C:\Users\casey\Desktop\Homesteader\Homesteader\Library\PackageCache\com.unity.ai.assistant@8d1e3e89e3a7\RelayApp~\relay_win.exe'
PROJECT = r'C:\Users\casey\Desktop\Homesteader\Homesteader'

env = os.environ.copy()

proc = subprocess.Popen(
    [RELAY, '--mcp', '--name', 'unity-mcp', '--instance-id', '37412', '--project-path', PROJECT],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    bufsize=0,
    text=False,  # raw bytes
)

def log(label, payload):
    sys.stderr.write(f'>>> [{label}] {len(payload)} bytes\n')
    sys.stderr.write(payload.decode('utf-8', errors='replace')[:400] + ('...\n' if len(payload) > 400 else '\n'))
    sys.stderr.flush()

def call(label, obj, want_full=True):
    line = (json.dumps(obj) + '\n').encode('utf-8')
    sys.stderr.write(f'>>> [{label}] {json.dumps(obj)[:200]}\n')
    sys.stderr.flush()
    proc.stdin.write(line)
    proc.stdin.flush()
    # Read one newline-delimited response.
    buf = bytearray()
    deadline = time.time() + 8
    while time.time() < deadline:
        b = proc.stdout.read(1)
        if not b:
            sys.stderr.write(f'!!! [{label}] EOF\n'); return None
        buf.extend(b)
        if b == b'\n':
            text = buf.decode('utf-8', errors='replace')
            sys.stderr.write(f'<<< [{label}] {len(text)} chars\n')
            sys.stderr.write(text if want_full else text[:600] + '\n')
            sys.stderr.flush()
            return text
    sys.stderr.write(f'!!! [{label}] timeout\n')
    return None

# 1) MCP initialize.
call('initialize', {
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'probe_stdio', 'version': '0.0.1'}
    }
}, want_full=False)

# 2) List tools.
call('tools/list', {'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}})

# 3) Safe tool call.
call('Unity_GetConsoleLogs', {
    'jsonrpc':'2.0','id':3,'method':'tools/call',
    'params': {'name':'Unity_GetConsoleLogs','arguments':{'maxEntries':2}}
})

# 4) shutdown
time.sleep(0.5)
proc.stdin.close()
try:
    out, err = proc.communicate(timeout=3)
except Exception:
    proc.kill()
    out, err = proc.communicate()

sys.stderr.write('--- stderr from relay ---\n')
sys.stderr.write(err.decode('utf-8', errors='replace')[-2000:] + '\n')
sys.stderr.flush()
