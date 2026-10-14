"""WBS v1 host prototype: mutually approved, pinned mTLS; no unauthenticated mode."""
import argparse
import base64
import datetime as dt
import hashlib
import ipaddress
import json
import os
import re
import signal
import socket
import socketserver
import ssl
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from .state import base, read, write, message

MAX_FILE = 16 * 1024 * 1024
MAX_FRAME = 24 * 1024 * 1024

def home():
    return base() / "wbs"

def fingerprint(pem):
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()

def identity(ips=("127.0.0.1",)):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    folder = home()
    if (folder / "identity.pem").exists() or (folder / "key.pem").exists():
        raise ValueError("Identity exists. Revoke peer trust before rotating keys; refusing replacement")
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "binux-" + uuid.uuid4().hex[:12])])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(minutes=1))
            .not_valid_after(now + dt.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
    for name, contents in (("key.pem", key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())), ("identity.pem", cert.public_bytes(serialization.Encoding.PEM))):
        fd = os.open(folder / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(contents)
    return fingerprint((folder / "identity.pem").read_text())

def peers():
    return read(home() / "peers.json", {})

def approve(cert_path, name, roots=None, commands=None):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", name):
        raise ValueError("Invalid device name")
    pem = Path(cert_path).read_text()
    fp = fingerprint(pem)
    trusted = peers()
    if name in trusted:
        raise ValueError("Peer exists; explicitly revoke before replacing identity")
    root_map = {key: str(Path(path).resolve(strict=True)) for key, path in (roots or {}).items()}
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", key) or not Path(path).is_dir() for key, path in root_map.items()):
        raise ValueError("Each share must have a valid name and existing directory")
    if not isinstance(commands or [], list) or any(not isinstance(c, list) or not c or not all(isinstance(s, str) for s in c) for c in (commands or [])):
        raise ValueError("Approved commands must be a JSON list of exact argument lists")
    cert_file = home() / (name + ".pem")
    cert_file.write_text(pem)
    os.chmod(cert_file, 0o600)
    trusted[name] = {"fingerprint": fp, "certificate": str(cert_file), "roots": root_map, "commands": commands or []}
    write(home() / "peers.json", trusted)
    return fp

def revoke(name):
    trusted = peers()
    entry = trusted.pop(name)
    write(home() / "peers.json", trusted)
    Path(entry["certificate"]).unlink(missing_ok=True)
    return name

def context(server=False, peer=None):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) if server else ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(home() / "identity.pem", home() / "key.pem")
    ctx.verify_mode = ssl.CERT_REQUIRED
    trusted = peers()
    entries = trusted.values() if server else [trusted[peer]]
    for entry in entries:
        ctx.load_verify_locations(cafile=entry["certificate"])
    if not server:
        ctx.check_hostname = True
    return ctx

def secure_parent(root, relative, create=False):
    """Open each directory through dir_fd + O_NOFOLLOW; no symlink races."""
    if os.name != "posix":
        raise ValueError("Host prototype secure file transport requires POSIX; Windows native transport pending")
    parts = relative.split("/")
    if not parts or any(p in ("", ".", "..") or "\\" in p or "\0" in p for p in parts):
        raise ValueError("Invalid relative file path")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd, parts[-1]
    except Exception:
        os.close(fd)
        raise

def operation(peer, request):
    op = request.get("op")
    if op == "info":
        import platform
        return {"protocol": 1, "platform": platform.system(), "name": socket.gethostname(), "shares": list(peer["roots"]), "screen": "unavailable", "port_forward": "unavailable"}
    if op in ("get", "put", "hash"):
        root = peer["roots"].get(request.get("share"))
        if root is None:
            raise PermissionError("Folder not approved for this device")
        parent, name = secure_parent(root, request["path"], create=op == "put")
        try:
            if op in ("get", "hash"):
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd, "rb") as f:
                    import stat
                    meta = os.fstat(f.fileno())
                    if not stat.S_ISREG(meta.st_mode) or meta.st_size > MAX_FILE:
                        raise ValueError("Only regular files up to 16 MiB are supported")
                    data = f.read(MAX_FILE + 1)
                    if len(data) > MAX_FILE:
                        raise ValueError("File limit exceeded")
                result = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
                if op == "get":
                    result["data"] = base64.b64encode(data).decode()
                return result
            data = base64.b64decode(request["data"], validate=True)
            if len(data) > MAX_FILE or hashlib.sha256(data).hexdigest() != request["sha256"]:
                raise ValueError("File size or SHA-256 mismatch")
            temp = ".wbs-" + uuid.uuid4().hex
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                if request.get("overwrite") is not True:
                    # link is atomic and fails if a target already exists.
                    os.link(temp, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
                    os.unlink(temp, dir_fd=parent)
                else:
                    os.replace(temp, name, src_dir_fd=parent, dst_dir_fd=parent)
            finally:
                try:
                    os.unlink(temp, dir_fd=parent)
                except FileNotFoundError:
                    pass
            return {"size": len(data), "sha256": request["sha256"]}
        finally:
            os.close(parent)
    if op == "exec":
        argv = request.get("argv")
        if argv not in peer["commands"]:
            raise PermissionError("Command not approved: exact argv authorization required")
        if os.name != "posix":
            raise ValueError("Windows remote process supervision is not integrated")
        with tempfile.TemporaryFile() as output:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=output, stderr=output, cwd=base() / "home", start_new_session=True)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise ValueError("Approved command exceeded 15 second limit")
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            output.seek(0)
            return {"exit_code": proc.returncode, "output": output.read(128 * 1024).decode("utf-8", errors="replace")}
    raise ValueError("Unsupported WBS operation")

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(15)
        cert = self.request.getpeercert(binary_form=True)
        fp = hashlib.sha256(cert).hexdigest()
        entry = next((p for p in peers().values() if p["fingerprint"] == fp), None)
        if entry is None:
            return  # Revocation checked for each request, not just server startup.
        try:
            raw = self.rfile.readline(MAX_FRAME + 1)
            if len(raw) > MAX_FRAME or not raw.endswith(b"\n"):
                raise ValueError("WBS frame limit exceeded")
            request = json.loads(raw)
            result = {"ok": True, "value": operation(entry, request)}
            event = request.get("op", "unknown")
        except Exception:
            result = {"ok": False, "error": "Request rejected: permission, path, integrity, or operation limit"}
            event = "rejected"
        # Log metadata only; no certificates, keys, file contents or command argv.
        with (home() / "events.jsonl").open("a") as log:
            log.write(json.dumps({"time": time.time(), "peer": fp[:12], "operation": event}) + "\n")
        self.wfile.write((json.dumps(result) + "\n").encode())

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    def __init__(self, address):
        self.tls = context(server=True)
        super().__init__(address, Handler)
    def get_request(self):
        raw, address = super().get_request()
        raw.settimeout(5)
        try:
            return self.tls.wrap_socket(raw, server_side=True), address
        except Exception:
            raw.close()
            raise

def request(ip, peer, payload, port=58290):
    entry = peers()[peer]
    with socket.create_connection((ip, port), timeout=10) as raw:
        with context(peer=peer).wrap_socket(raw, server_hostname=ip) as secure:
            if hashlib.sha256(secure.getpeercert(binary_form=True)).hexdigest() != entry["fingerprint"]:
                raise ssl.SSLError("Device fingerprint mismatch")
            secure.sendall((json.dumps(payload) + "\n").encode())
            data = secure.makefile("rb").readline(MAX_FRAME + 1)
            if len(data) > MAX_FRAME:
                raise ValueError("WBS response exceeds limit")
            response = json.loads(data)
            if not response["ok"]:
                raise PermissionError(response["error"])
            return response["value"]

def main(argv=None):
    parser = argparse.ArgumentParser(prog="wbs", description="WBS v1 host prototype (Android and Windows app transport pending)")
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init"); init.add_argument("--ip", action="append", default=["127.0.0.1"])
    pair = sub.add_parser("pair"); pair.add_argument("certificate"); pair.add_argument("--name", required=True); pair.add_argument("--approve", action="store_true"); pair.add_argument("--share", action="append", default=[]); pair.add_argument("--commands")
    rev = sub.add_parser("revoke"); rev.add_argument("name")
    serve = sub.add_parser("serve"); serve.add_argument("--bind", default="127.0.0.1"); serve.add_argument("--port", type=int, default=58290); serve.add_argument("--allow-network", action="store_true")
    for target in ("windows", "android"):
        connect = sub.add_parser(target); connect.add_argument("ip"); connect.add_argument("--peer"); connect.add_argument("--port", type=int, default=58290)
    for name in ("devices", "status", "disconnect", "logs", "help"):
        sub.add_parser(name)
    for name in ("share", "sync"):
        transfer = sub.add_parser(name); transfer.add_argument("path"); transfer.add_argument("--remote-share", required=True); transfer.add_argument("--overwrite", action="store_true")
    execute = sub.add_parser("exec"); execute.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        action = args.action
        if action == "init":
            result = {"fingerprint": identity(args.ip), "certificate": str(home() / "identity.pem")}
        elif action == "pair":
            fp = fingerprint(Path(args.certificate).read_text())
            print("Verify this fingerprint through a trusted channel on BOTH devices: " + fp)
            if not args.approve and input(message("이 기기를 승인합니까? [yes]: ", "Approve this device? [yes]: ")) != "yes":
                raise ValueError("Pairing not approved")
            roots = dict(value.split("=", 1) for value in args.share)
            result = approve(args.certificate, args.name, roots, read(Path(args.commands), []) if args.commands else [])
        elif action == "revoke":
            result = revoke(args.name)
        elif action == "serve":
            if not ipaddress.ip_address(args.bind).is_loopback and not args.allow_network:
                raise ValueError("LAN exposure requires explicit --allow-network")
            if not peers():
                raise ValueError("Approve a peer certificate before serving")
            with Server((args.bind, args.port)) as server:
                print(f"WBS mTLS listening {args.bind}:{server.server_address[1]}", flush=True)
                server.serve_forever()
            return 0
        elif action in ("windows", "android"):
            if ipaddress.ip_address(args.ip).is_loopback:
                print(message("루프백 주소는 이 기기 자신입니다. 다른 기기는 상대 기기의 IP가 필요합니다.", "Loopback refers to this device. Use the other device's IP for a remote connection."))
            peer = args.peer or (next(iter(peers())) if len(peers()) == 1 else None)
            if peer is None:
                raise ValueError("Select an approved device with --peer")
            result = request(args.ip, peer, {"op": "info"}, args.port)
            write(home() / "endpoint.json", {"ip": args.ip, "peer": peer, "port": args.port, "last_probe": time.time(), "target_label": action})
        elif action == "devices":
            result = {name: {"fingerprint": value["fingerprint"], "shares": list(value["roots"])} for name, value in peers().items()}
        elif action == "disconnect":
            (home() / "endpoint.json").unlink(missing_ok=True)
            result = "Endpoint selection cleared; each request has its own TLS connection. Use revoke to remove trust."
        elif action == "logs":
            path = home() / "events.jsonl"
            result = "\n".join(path.read_text().splitlines()[-100:]) if path.exists() else "No connection events"
        elif action == "help":
            parser.print_help(); return 0
        else:
            endpoint = read(home() / "endpoint.json")
            if not endpoint:
                raise ValueError("No endpoint selected; run wbs windows|android <IP> first")
            def send(payload):
                return request(endpoint["ip"], endpoint["peer"], payload, endpoint["port"])
            if action == "status":
                result = {"reachable_now": True, "device": send({"op": "info"}), "persistent_connection": False}
            elif action == "exec":
                result = send({"op": "exec", "argv": args.command})
            else:
                path = Path(args.path).resolve(strict=True)
                files = sorted(path.rglob("*")) if path.is_dir() else [path]
                result = []
                for file in files:
                    if file.is_symlink() or not file.is_file():
                        continue
                    if file.stat().st_size > MAX_FILE:
                        raise ValueError("File exceeds 16 MiB prototype limit")
                    data = file.read_bytes()
                    relative = str(file.relative_to(path)) if path.is_dir() else file.name
                    digest = hashlib.sha256(data).hexdigest()
                    if action == "sync":
                        try:
                            previous = send({"op": "hash", "share": args.remote_share, "path": relative})
                        except PermissionError:
                            previous = {}
                        if previous.get("sha256") == digest:
                            continue
                    result.append(send({"op": "put", "share": args.remote_share, "path": relative, "data": base64.b64encode(data).decode(), "sha256": digest, "overwrite": args.overwrite}))
        print(json.dumps(result, ensure_ascii=False, indent=2) if not isinstance(result, str) else result)
        return 0
    except (OSError, ValueError, KeyError, PermissionError) as error:
        print(message("오류: ", "Error: ") + str(error), file=__import__("sys").stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
