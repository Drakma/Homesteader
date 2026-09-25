#!/usr/bin/env python3
"""MCP host for the Homesteader toolchain.

Why this exists
---------------
The CodeGPT extension has no MCP client in it, and no agent/tool loop either -
the tool-calling decisions are made on CodeGPT Plus's servers, so there is no
local seam to add a tool at. This file is the other half: a standalone host
that reads .mcp.json, spawns each server over stdio, speaks JSON-RPC to it, and
lets any caller (a script, a terminal, or another agent) list and call those
tools for real.

It is deliberately one file, standard library only, so it runs under the
absolute interpreter this project already standardises on
(C:\\Python313\\python.exe) with nothing installed.

Usage
-----
    python tools/mcp_host.py list                     # every server's tools
    python tools/mcp_host.py list unity-mcp           # one server's tools
    python tools/mcp_host.py schema unity-mcp <tool>  # a tool's input schema
    python tools/mcp_host.py call unity-mcp <tool> --json '{"a": 1}'
    python tools/mcp_host.py call unity-mcp <tool> --args a=1 b=two
    python tools/mcp_host.py shell                    # interactive REPL
    python tools/mcp_host.py selftest                 # handshake every server

Exit codes: 0 = ok, 1 = a call failed, 2 = config/bad usage.

The MCP wire format implemented here
------------------------------------
Transport is newline-delimited JSON over the child's stdin/stdout. Each message
is a JSON-RPC 2.0 object. The handshake is:

    -> {"jsonrpc":"2.0","id":1,"method":"initialize","params":{
           "protocolVersion":"2024-11-05",
           "capabilities":{},
           "clientInfo":{"name":"homesteader-mcp-host","version":"1.0.0"}}}
    <- {"jsonrpc":"2.0","id":1,"result":{...}}
    -> {"jsonrpc":"2.0","method":"notifications/initialized"}

Then `tools/list` and `tools/call` as normal requests. Anything the server
writes to stderr is captured and surfaced on failure, because stdio servers
routinely report their real problem there and nowhere else.
"""

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Secrets live in the gitignored .env, not in .mcp.json. A server whose config
# says "${MESHY_API_KEY}" has that reference resolved from .env here, because
# npx-based servers read the environment and know nothing about dotfiles.
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
import env_loader  # noqa: E402  (path set above, deliberately after)

# The project-root config is the source of truth. The old
# ~/.codegpt/mcp_config.json is a stale duplicate of the same five servers and
# is only consulted as a fallback so an existing setup keeps working.
CONFIG_CANDIDATES = [
    os.path.join(REPO_ROOT, ".mcp.json"),
    os.path.join(os.path.expanduser("~"), ".codegpt", "mcp_config.json"),
]

PROTOCOL_VERSION = "2024-11-05"
CLIENT_INFO = {"name": "homesteader-mcp-host", "version": "1.0.0"}

# A server is allowed this long to answer a request before we give up. Unity's
# relay has to reach the editor's named pipe on first use, which is slower than
# a pure in-process Python server, so this is generous on purpose.
DEFAULT_TIMEOUT = 120.0


def load_config(path=None):
    """Return (config_dict, path_used). Raises RuntimeError if nothing usable."""
    candidates = [path] if path else CONFIG_CANDIDATES
    errors = []
    for candidate in candidates:
        if not candidate or not os.path.isfile(candidate):
            errors.append("%s: not found" % candidate)
            continue
        try:
            with open(candidate, "r", encoding="utf-8-sig") as fh:
                cfg = json.load(fh)
        except Exception as exc:  # malformed JSON is a real answer, not a crash
            errors.append("%s: %s" % (candidate, exc))
            continue
        servers = cfg.get("mcpServers")
        if not isinstance(servers, dict) or not servers:
            errors.append("%s: no mcpServers" % candidate)
            continue
        return cfg, candidate
    raise RuntimeError("no usable MCP config:\n  " + "\n  ".join(errors))


# Node/npm/git are installed on this machine but NOT on PATH in a bare shell
# (see docs/MESH2MOTION_SETUP.md, and AGENTS.md section 4). tools/mesh2motion_mcp.py
# already resolves them by absolute path for the same reason. The config says
# `npx`, so without this the meshy server fails with WinError 2. MCP servers
# should not depend on the user's PATH being right.
KNOWN_TOOL_DIRS = [
    r"C:\Program Files\nodejs",
    r"C:\Program Files (x86)\nodejs",
    os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "npm"),
    r"C:\Program Files\Git\cmd",
]

# Where npm puts globally installed packages on Windows.
NPM_GLOBAL_ROOT = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "npm",
                               "node_modules")


def _cmd_exe():
    """Absolute path to cmd.exe.

    Never use the bare name "cmd.exe": Popen resolves it through PATH, and this
    module deliberately edits the child's PATH, so a PATH without System32
    leaves cmd.exe itself unresolvable. ComSpec is the authoritative answer and
    is what Windows sets for exactly this purpose.
    """
    return os.environ.get("ComSpec") or r"C:\WINDOWS\system32\cmd.exe"


def _local_node_package(package):
    """Find an npm package's entry script in the global node_modules tree.

    Preferred over `npx -y <package>`: npx has to resolve, download-miss, and
    then re-exec `node`, and its .cmd shim needs `node` on PATH even when we
    launched the shim by absolute path. Calling the installed entry script with
    node directly removes both failure modes and is faster to boot.
    """
    base = os.path.join(NPM_GLOBAL_ROOT, *package.split("/"))
    for relative in (os.path.join("dist", "index.js"), "index.js",
                     os.path.join("build", "index.js")):
        candidate = os.path.join(base, relative)
        if os.path.isfile(candidate):
            return candidate
    return None


def _node_exe():
    """Absolute path to node.exe, found without relying on PATH."""
    found = shutil.which("node")
    if found:
        return found
    for directory in KNOWN_TOOL_DIRS:
        for candidate in (os.path.join(directory, "node.exe"),
                          os.path.join(directory, "node")):
            if os.path.isfile(candidate):
                return candidate
    return None


def rewrite_npx_server(spec):
    """If a server is `npx [-y] <pkg> ...`, run the installed package directly.

    Returns a possibly-updated copy of the spec. Leaves anything it does not
    recognise untouched, so a genuine npx-only server still goes through npx.
    """
    if spec.get("command") != "npx":
        return spec
    args = list(spec.get("args") or [])
    # Strip the flags npx accepts before the package name.
    while args and args[0] in ("-y", "--yes", "-q", "--quiet"):
        args.pop(0)
    if not args:
        return spec
    package = args[0]
    if package.startswith("-"):
        return spec
    entry = _local_node_package(package)
    node = _node_exe()
    if not entry or not node:
        return spec
    rewritten = dict(spec)
    rewritten["command"] = node
    rewritten["args"] = [entry] + args[1:]
    return rewritten


def resolve_command(command):
    """Resolve a config command to something CreateProcess will accept.

    The config uses forward slashes, which Windows tolerates, and bare names
    like `npx`, which it does not - there is no shell in Popen, so PATH lookup
    is our job. `npx` is also a .cmd shim, so it must run through cmd.exe
    rather than being executed directly.

    Returns (path, is_shell_script).
    """
    if os.path.isabs(command) or (len(command) > 1 and command[1] == ":"):
        return command, command.lower().endswith((".cmd", ".bat"))

    found = shutil.which(command)
    if not found:
        # Fall back to the known install locations before giving up. Order
        # matters: for `npx`, nodejs ships BOTH an extensionless POSIX shell
        # script and npx.cmd. Windows cannot execute the former (WinError 193),
        # so the Windows-executable suffixes are tried FIRST.
        for directory in KNOWN_TOOL_DIRS:
            for suffix in (".exe", ".cmd", ".bat", ""):
                candidate = os.path.join(directory, command + suffix)
                if os.path.isfile(candidate):
                    found = candidate
                    break
            if found:
                break
    if not found:
        return command, False
    return found, found.lower().endswith((".cmd", ".bat"))


class MCPClient(object):
    """One stdio MCP server: a child process plus a JSON-RPC conversation."""

    def __init__(self, name, spec, timeout=DEFAULT_TIMEOUT, debug=False):
        self.name = name
        self.spec = spec
        # Normalise `npx` servers to a direct node invocation once, here, so
        # every code path (start/stop/resolve) agrees on what runs.
        self.spec = rewrite_npx_server(spec)
        self.original_command = spec.get("command")
        self.timeout = timeout
        self.debug = debug
        self.proc = None
        self._next_id = 0
        self._pending = {}
        self._lock = threading.Lock()
        self._reader = None
        self.stderr_lines = []
        self.tools = []
        self.server_info = {}

    # -- process lifecycle -------------------------------------------------

    def start(self):
        command = self.spec.get("command")
        if not command:
            raise RuntimeError("server %r has no command" % self.name)
        args = list(self.spec.get("args") or [])
        resolved, is_shim = resolve_command(self.spec.get("command"))
        if is_shim:
            # A .cmd/.bat shim cannot be exec'd directly and must go through
            # cmd.exe. Passing ["cmd.exe", "/c", '"%s"' % resolved] + args as
            # an argv LIST does not survive: subprocess re-quotes each element
            # and cmd ends up seeing literal \" quotes around the path, so it
            # reports the whole quoted path as an unrecognized command. Build
            # ONE command-line string instead and pass it as a single argument
            # with shell=False, which is what cmd.exe actually expects.
            def _q(part):
                part = str(part)
                return '"%s"' % part if (" " in part or "\t" in part) else part
            command_line = " ".join([_q(resolved)] + [_q(a) for a in args])
            argv = [_cmd_exe(), "/c", command_line]
        else:
            argv = [resolved] + args
        if self.debug:
            sys.stderr.write("[%s exec] %s\n" % (self.name, " ".join(argv)))

        env = os.environ.copy()
        env.update(self.spec.get("env") or {})
        # Unbuffered so the handshake is not delayed by a full pipe buffer.
        env.setdefault("PYTHONUNBUFFERED", "1")
        # Resolving `npx` to its absolute path is not enough: npx.cmd internally
        # calls bare `node`, and node is NOT on PATH on this machine, so the
        # shim dies with "'node' is not recognized". Prepend any known tool
        # directory that actually exists so a shim can find its own siblings.
        extra_path = [d for d in KNOWN_TOOL_DIRS if os.path.isdir(d)]
        if extra_path:
            existing = env.get("PATH", "")
            env["PATH"] = os.pathsep.join(extra_path + [existing]) if existing else \
                os.pathsep.join(extra_path)

        cwd = self.spec.get("cwd") or REPO_ROOT
        self.proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            bufsize=0,
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        threading.Thread(target=self._stderr_loop, daemon=True).start()
        return self

    def _read_loop(self):
        stream = self.proc.stdout
        while True:
            line = stream.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").strip()
            if not text:
                continue
            if self.debug:
                sys.stderr.write("[%s <-] %s\n" % (self.name, text))
            try:
                msg = json.loads(text)
            except ValueError:
                # Log-style output on stdout is a real failure mode; keep it so
                # the error message can show what the server actually said.
                self.stderr_lines.append("stdout (non-JSON): " + text)
                continue
            msg_id = msg.get("id")
            if msg_id is None:
                continue  # a notification; nothing is waiting on it
            with self._lock:
                box = self._pending.pop(msg_id, None)
            if box is not None:
                box.put(msg)
        # EOF: unblock anyone still waiting.
        with self._lock:
            waiters = list(self._pending.values())
            self._pending.clear()
        for box in waiters:
            box.put(None)

    def _stderr_loop(self):
        stream = self.proc.stderr
        while True:
            line = stream.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").rstrip()
            if text:
                self.stderr_lines.append(text)
                if self.debug:
                    sys.stderr.write("[%s stderr] %s\n" % (self.name, text))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

    # -- JSON-RPC ----------------------------------------------------------

    def _send(self, payload):
        data = (json.dumps(payload) + "\n").encode("utf-8")
        if self.debug:
            sys.stderr.write("[%s ->] %s\n" % (self.name, json.dumps(payload)[:400]))
        try:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError(
                "server %r closed its stdin (%s). stderr:\n%s"
                % (self.name, exc, self.stderr_tail())
            )

    def request(self, method, params=None):
        if self.proc is None:
            raise RuntimeError("server %r not started" % self.name)
        with self._lock:
            self._next_id += 1
            msg_id = self._next_id
            box = queue.Queue(maxsize=1)
            self._pending[msg_id] = box
        self._send({
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params if params is not None else {},
        })
        try:
            msg = box.get(timeout=self.timeout)
        except queue.Empty:
            raise RuntimeError(
                "server %r did not answer %s within %.0fs. stderr:\n%s"
                % (self.name, method, self.timeout, self.stderr_tail())
            )
        if msg is None:
            raise RuntimeError(
                "server %r exited during %s (code %s). stderr:\n%s"
                % (self.name, method, self.proc.poll(), self.stderr_tail())
            )
        if "error" in msg:
            err = msg["error"]
            raise RuntimeError(
                "server %r returned an error for %s: %s"
                % (self.name, method, json.dumps(err))
            )
        return msg.get("result", {})

    def notify(self, method, params=None):
        self._send({
            "jsonrpc": "2.0",
            "method": method,
            "params": params if params is not None else {},
        })

    def stderr_tail(self, limit=1200):
        tail = "\n".join(self.stderr_lines[-25:])
        return tail[-limit:] if tail else "(nothing on stderr)"

    # -- MCP ---------------------------------------------------------------

    def initialize(self):
        result = self.request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        })
        self.server_info = result.get("serverInfo", {}) or {}
        self.notify("notifications/initialized")
        return result

    def list_tools(self):
        result = self.request("tools/list")
        self.tools = result.get("tools", []) or []
        return self.tools

    def call_tool(self, tool, arguments):
        return self.request("tools/call", {"name": tool, "arguments": arguments})


# -- presentation ---------------------------------------------------------


def render_call_result(result):
    """Flatten an MCP tools/call result into text for a terminal."""
    chunks = []
    for item in result.get("content", []) or []:
        kind = item.get("type")
        if kind == "text":
            chunks.append(item.get("text", ""))
        elif kind == "resource":
            res = item.get("resource", {}) or {}
            chunks.append("[resource: %s]" % res.get("uri", "?"))
        elif kind == "image":
            chunks.append("[image: %s bytes, %s]" % (
                len(item.get("data", "") or ""), item.get("mimeType", "?")))
        else:
            chunks.append("[%s]" % kind)
    text = "\n".join(chunks) if chunks else "(no content)"
    if result.get("isError"):
        text = "TOOL REPORTED AN ERROR:\n" + text
    return text


def parse_args_pairs(pairs):
    """Turn ["a=1","b=two"] into {"a":1,"b":"two"}, JSON-decoding values."""
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError("expected key=value, got %r" % pair)
        key, _, raw = pair.partition("=")
        try:
            out[key.strip()] = json.loads(raw)
        except ValueError:
            out[key.strip()] = raw
    return out


def cmd_list(cfg, args):
    names = [args.server] if args.server else sorted(cfg["mcpServers"])
    for name in names:
        spec = cfg["mcpServers"].get(name)
        if spec is None:
            sys.stderr.write("no such server: %s\n" % name)
            return 2
        client = MCPClient(name, spec, timeout=args.timeout, debug=args.debug)
        try:
            client.start()
            client.initialize()
            tools = client.list_tools()
            info = client.server_info
            label = info.get("name", "?")
            ver = info.get("version", "?")
            print("== %s  (%s %s)  %d tool(s)" % (name, label, ver, len(tools)))
            for tool in tools:
                desc = (tool.get("description") or "").strip().splitlines()
                desc = desc[0] if desc else ""
                print("   %-42s %s" % (tool.get("name", "?"), desc[:110]))
        except Exception as exc:
            print("== %s  FAILED" % name)
            print("   %s" % exc)
            if args.strict:
                return 1
        finally:
            client.stop()
    return 0


def cmd_schema(cfg, args):
    spec = cfg["mcpServers"].get(args.server)
    if spec is None:
        sys.stderr.write("no such server: %s\n" % args.server)
        return 2
    client = MCPClient(args.server, spec, timeout=args.timeout, debug=args.debug)
    try:
        client.start()
        client.initialize()
        for tool in client.list_tools():
            if tool.get("name") == args.tool:
                print(json.dumps(tool, indent=2))
                return 0
        sys.stderr.write("no such tool on %s: %s\n" % (args.server, args.tool))
        return 2
    finally:
        client.stop()


def cmd_call(cfg, args):
    spec = cfg["mcpServers"].get(args.server)
    if spec is None:
        sys.stderr.write("no such server: %s\n" % args.server)
        return 2
    if args.json:
        raw_json = args.json
        # `--json @path` reads the payload from a file. Windows shells mangle
        # braces, quotes and $ in an inline JSON argument (see AGENTS.md 4), and
        # a C# snippet sent to Unity_RunCommand is full of all three. Passing a
        # file sidesteps the shell's quoting rules entirely.
        if raw_json.startswith("@"):
            json_path = raw_json[1:]
            try:
                with open(json_path, "r", encoding="utf-8-sig") as fh:
                    raw_json = fh.read()
            except OSError as exc:
                sys.stderr.write("cannot read --json file: %s\n" % exc)
                return 2
        try:
            arguments = json.loads(raw_json)
        except ValueError as exc:
            sys.stderr.write("--json is not valid JSON: %s\n" % exc)
            return 2
    else:
        try:
            arguments = parse_args_pairs(args.args)
        except ValueError as exc:
            sys.stderr.write("%s\n" % exc)
            return 2

    client = MCPClient(args.server, spec, timeout=args.timeout, debug=args.debug)
    try:
        client.start()
        client.initialize()
        result = client.call_tool(args.tool, arguments)
        print(render_call_result(result))
        return 1 if result.get("isError") else 0
    except Exception as exc:
        sys.stderr.write("call failed: %s\n" % exc)
        return 1
    finally:
        client.stop()


def cmd_selftest(cfg, args):
    """Handshake every server and report, without caring about tool counts."""
    ok, bad = [], []
    for name in sorted(cfg["mcpServers"]):
        client = MCPClient(name, cfg["mcpServers"][name],
                           timeout=args.timeout, debug=args.debug)
        try:
            client.start()
            client.initialize()
            tools = client.list_tools()
            ok.append((name, len(tools), client.server_info.get("name", "?")))
            print("ok    %-24s %3d tool(s)   %s"
                  % (name, len(tools), client.server_info.get("name", "?")))
        except Exception as exc:
            bad.append((name, str(exc)))
            print("FAIL  %-24s %s" % (name, str(exc).splitlines()[0]))
            if args.debug:
                print("      " + client.stderr_tail(600).replace("\n", "\n      "))
        finally:
            client.stop()
    print("\n%d ok, %d failed" % (len(ok), len(bad)))
    return 0 if not bad else 1


def cmd_shell(cfg, args):
    """Interactive REPL: `server tool {json}` per line."""
    clients = {}

    def get(name):
        if name not in clients:
            client = MCPClient(name, cfg["mcpServers"][name],
                               timeout=args.timeout, debug=args.debug)
            client.start()
            client.initialize()
            clients[name] = client
        return clients[name]

    print("servers: %s" % ", ".join(sorted(cfg["mcpServers"])))
    print("commands: <server> list | <server> <tool> {json} | :quit")
    try:
        while True:
            try:
                line = input("mcp> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line in (":quit", ":q", "quit", "exit"):
                break
            parts = line.split(None, 2)
            server = parts[0]
            if server not in cfg["mcpServers"]:
                print("no such server: %s" % server)
                continue
            if len(parts) == 1:
                print("usage: %s list | %s <tool> {json}" % (server, server))
                continue
            verb = parts[1]
            try:
                client = get(server)
                if verb == "list":
                    for tool in client.list_tools():
                        print("   %-42s %s" % (
                            tool.get("name", "?"),
                            (tool.get("description") or "").strip().splitlines()[:1]))
                    continue
                raw = parts[2] if len(parts) > 2 else "{}"
                arguments = json.loads(raw) if raw.strip() else {}
                print(render_call_result(client.call_tool(verb, arguments)))
            except Exception as exc:
                print("error: %s" % exc)
    finally:
        for client in clients.values():
            client.stop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mcp_host.py",
        description="Standalone MCP host for the Homesteader toolchain.")
    # --timeout and --debug are accepted BOTH before and after the subcommand.
    # The subparsers below re-declare them; argparse fills whichever the user
    # typed from the parser they land on, and the merge below picks the winner.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--timeout", type=float, default=None,
                        help="seconds to wait for a server reply (default %g)"
                             % DEFAULT_TIMEOUT)
    common.add_argument("--debug", action="store_true",
                        help="print the JSON-RPC traffic and stderr live")

    # Load .env before any subcommand runs, so call/list/schema/selftest/shell
    # all resolve ${...} references in a server's env block identically.
    env_loader.load_env()

    parser.add_argument("--config", help="path to an mcpServers JSON file")
    parser.add_argument("--timeout", type=float, default=None,
                        help="seconds to wait for a server reply (default %g)"
                             % DEFAULT_TIMEOUT)
    parser.add_argument("--debug", action="store_true",
                        help="print the JSON-RPC traffic and stderr live")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add(name, help_text, **kwargs):
        """Subparser that also accepts the shared --timeout/--debug flags."""
        p = sub.add_parser(name, help=help_text, parents=[common], **kwargs)
        return p

    p_list = add("list", "list tools")
    p_list.add_argument("server", nargs="?")
    p_list.add_argument("--strict", action="store_true",
                        help="exit non-zero if any server fails")
    p_list.set_defaults(func=cmd_list)

    p_schema = add("schema", "print one tool's full definition")
    p_schema.add_argument("server")
    p_schema.add_argument("tool")
    p_schema.set_defaults(func=cmd_schema)

    p_call = add("call", "call a tool")
    p_call.add_argument("server")
    p_call.add_argument("tool")
    p_call.add_argument("--json", help="arguments as a JSON object, or @file to"
                                         " read them from a file")
    p_call.add_argument("--args", nargs="*", default=[],
                        help="arguments as key=value pairs")
    p_call.set_defaults(func=cmd_call)

    p_self = add("selftest", "handshake every server")
    p_self.set_defaults(func=cmd_selftest)

    p_shell = add("shell", "interactive REPL")
    p_shell.set_defaults(func=cmd_shell)

    args = parser.parse_args(argv)
    # `default=None` on both sides lets us tell "flag not given" from a real
    # value, so a flag written before the subcommand still takes effect.
    if args.timeout is None:
        args.timeout = DEFAULT_TIMEOUT

    try:
        cfg, path = load_config(args.config)
    except RuntimeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    if args.debug:
        sys.stderr.write("[config] %s\n" % path)

    # Resolve ${NAME} references in each server's env block from .env. A
    # reference with nothing behind it is reported and exits 2, rather than
    # being handed to a server as the literal string "${NAME}" - which would
    # surface later as an opaque 401 from a remote API.
    missing = []
    for name, spec in list(cfg["mcpServers"].items()):
        cfg["mcpServers"][name] = env_loader.resolve_spec_env(spec, missing)
    if missing:
        sys.stderr.write("unresolved env reference(s): %s\n"
                         % ", ".join(sorted(missing)))
        sys.stderr.write("add them to %s (gitignored)\n"
                         % env_loader.DEFAULT_ENV_PATH)
        return 2

    return args.func(cfg, args)


if __name__ == "__main__":
    sys.exit(main())