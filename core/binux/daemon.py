"""User-owned Linux/WSL process supervisor. Does not attach to persisted PIDs."""
import argparse
import fcntl
import json
import os
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from .state import base, read, write

MAX_FRAME = 64 * 1024

def signal_owned_group(process, sig):
    # If the leader's PID was reused after exit, do not signal the new group.
    # Existing group members keep the original PGID allocated in the kernel.
    path = Path(f"/proc/{process.pid}/stat")
    try:
        birth = int(path.read_text().rsplit(") ", 1)[1].split()[19])
        if birth != getattr(process, "_binux_birth", None):
            return
    except FileNotFoundError:
        pass
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass

def finish_group(process):
    time.sleep(2)
    signal_owned_group(process, signal.SIGKILL)

class Supervisor:
    def __init__(self, root):
        self.root = root
        self.lock = threading.RLock()
        self.records = read(root / "config/jobs.json", {})
        self.processes = {}
        for record in self.records.values():
            if record["state"] in ("running", "stopping", "paused"):
                record.update(state="interrupted", pid=None, finished=time.time())
        self.save()
        self.active = True
        def monitor():
            while self.active:
                self.refresh()
                time.sleep(0.2)
        threading.Thread(target=monitor, daemon=True).start()

    def save(self):
        write(self.root / "config/jobs.json", self.records)

    def refresh(self):
        with self.lock:
            changed = False
            for key, process in tuple(self.processes.items()):
                code = process.poll()
                if code is not None and self.records[key]["state"] != "exited":
                    record = self.records[key]
                    restart = record.get("restart_on_failure", False) and record["state"] == "running" and code != 0 and record.get("restart_count", 0) < 3
                    self.records[key].update(state="exited", exit_code=code, finished=time.time())
                    # Clean up descendants still in our child's original process group.
                    signal_owned_group(process, signal.SIGTERM)
                    threading.Thread(target=finish_group, args=(process,), daemon=True).start()
                    if restart:
                        try:
                            replacement = self.launch(record["argv"], record["cwd"], Path(record["log"]))
                            self.processes[key] = replacement
                            record.update(pid=replacement.pid, state="running", exit_code=None, finished=None, restart_count=record.get("restart_count", 0) + 1)
                        except OSError:
                            record["restart_error"] = "Executable could not be restarted"
                    changed = True
            if changed:
                self.save()

    def launch(self, argv, directory, log):
        with log.open("ab") as output:
            process = subprocess.Popen(argv, cwd=directory, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
                                       env={**os.environ, "BINUX_HOME": str(self.root)})
        process._binux_birth = int(Path(f"/proc/{process.pid}/stat").read_text().rsplit(") ", 1)[1].split()[19])
        return process

    def start(self, argv, cwd, server=None, restart_on_failure=False):
        if not argv or not all(isinstance(x, str) and "\0" not in x for x in argv):
            raise ValueError("Expected command and arguments")
        directory = Path(cwd).resolve(strict=True)
        if not directory.is_dir():
            raise ValueError("Working directory is not a directory")
        if os.statvfs(self.root).f_bavail * os.statvfs(self.root).f_frsize < 1024 * 1024:
            raise ValueError("Insufficient storage: 1 MiB free required for logs")
        key = uuid.uuid4().hex[:12]
        log = self.root / "logs" / (key + ".log")
        process = self.launch(argv, directory, log)
        record = dict(id=key, argv=argv, cwd=str(directory), pid=process.pid, state="running",
                      started=time.time(), exit_code=None, log=str(log), server=server, restart_on_failure=bool(restart_on_failure), restart_count=0)
        self.records[key] = record
        self.processes[key] = process
        self.save()
        return record.copy()

    def stop(self, key):
        process = self.processes.get(key)
        if key not in self.records:
            raise ValueError("Unknown job")
        if process is None or process.poll() is not None:
            return self.records[key].copy()
        self.records[key]["state"] = "stopping"
        signal_owned_group(process, signal.SIGTERM)
        def escalate():
            try:
                process.wait(2)
            except subprocess.TimeoutExpired:
                signal_owned_group(process, signal.SIGKILL)
            self.refresh()
        threading.Thread(target=escalate, daemon=True).start()
        self.save()
        return self.records[key].copy()

    def dispatch(self, request):
        with self.lock:
            self.refresh()
            op = request["op"]
            if op == "ping":
                return {"pid": os.getpid(), "runtime": "host-linux", "jobs": len(self.processes)}
            if op == "run":
                return self.start(request["argv"], request["cwd"], request.get("server"), request.get("restart_on_failure", False))
            if op == "list":
                result = []
                for record in self.records.values():
                    copy = record.copy()
                    copy["elapsed"] = round((copy.get("finished") or time.time()) - copy["started"], 2)
                    copy["rss_kib"] = None
                    copy["cpu_ticks"] = None
                    if copy["state"] in ("running", "paused"):
                        try:
                            copy["rss_kib"] = next(int(line.split()[1]) for line in Path(f'/proc/{copy["pid"]}/status').read_text().splitlines() if line.startswith("VmRSS:"))
                            fields = Path(f'/proc/{copy["pid"]}/stat').read_text().rsplit(") ", 1)[1].split()
                            copy["cpu_ticks"] = int(fields[11]) + int(fields[12])
                        except (OSError, StopIteration, ValueError):
                            pass
                    result.append(copy)
                return result
            if op == "logs":
                path = Path(self.records[request["id"]]["log"])
                with path.open("rb") as f:
                    f.seek(max(0, path.stat().st_size - 128 * 1024))
                    return f.read().decode("utf-8", errors="replace")
            if op == "stop":
                return self.stop(request["id"])
            if op == "restart":
                previous = self.records[request["id"]]
                process = self.processes.get(previous["id"])
                if process is not None and process.poll() is None:
                    raise ValueError("Stop and wait for exit before restarting")
                return self.start(previous["argv"], previous["cwd"], previous["server"], previous.get("restart_on_failure", False))
            if op in ("pause", "resume"):
                for key, process in self.processes.items():
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGSTOP if op == "pause" else signal.SIGCONT)
                        self.records[key]["state"] = "paused" if op == "pause" else "running"
                self.save()
                return op
            if op == "shutdown":
                for key in tuple(self.processes):
                    self.stop(key)
                threading.Thread(target=self.shutdown, daemon=True).start()
                return "stopping"
            raise ValueError("Unknown operation")

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(5)
        try:
            if hasattr(socket, "SO_PEERCRED"):
                import struct
                _, uid, _ = struct.unpack("3i", self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if uid != os.getuid():
                    return
            raw = self.rfile.readline(MAX_FRAME + 1)
            if len(raw) > MAX_FRAME or not raw.endswith(b"\n"):
                raise ValueError("Oversized or incomplete request")
            result = {"ok": True, "value": self.server.supervisor.dispatch(json.loads(raw))}
        except Exception as error:
            result = {"ok": False, "error": str(error)}
        self.wfile.write((json.dumps(result, ensure_ascii=False) + "\n").encode())

def socket_path():
    return base() / "config/runtime.sock"

def rpc(op, **kwargs):
    path = socket_path()
    def call():
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(15)
            sock.connect(str(path))
            sock.sendall((json.dumps(dict(op=op, **kwargs)) + "\n").encode())
            response = json.loads(sock.makefile("rb").readline(1024 * 1024))
            if not response["ok"]:
                raise ValueError(response["error"])
            return response["value"]
    try:
        return call()
    except (FileNotFoundError, ConnectionRefusedError):
        if op == "shutdown":
            return "not running"
        output = (base() / "logs/daemon.log").open("ab")
        try:
            child = subprocess.Popen([sys.executable, "-m", "binux.daemon"], stdin=subprocess.DEVNULL,
                                     stdout=output, stderr=output, start_new_session=True, close_fds=True)
            threading.Thread(target=child.wait, daemon=True).start()
        finally:
            output.close()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                return call()
            except (FileNotFoundError, ConnectionRefusedError):
                time.sleep(0.05)
        raise RuntimeError("Supervisor did not start; see logs/daemon.log")

def main():
    root = base()
    with (root / "config/daemon.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        path = socket_path()
        path.unlink(missing_ok=True)
        with socketserver.ThreadingUnixStreamServer(str(path), Handler) as server:
            server.daemon_threads = True
            server.supervisor = Supervisor(root)
            def shutdown():
                time.sleep(2.2)
                server.shutdown()
            server.supervisor.shutdown = shutdown
            os.chmod(path, 0o600)
            try:
                server.serve_forever(poll_interval=0.1)
            finally:
                server.supervisor.active = False
                path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
