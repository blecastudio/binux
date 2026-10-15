import base64
import contextlib
import hashlib
import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from binux.state import base, read, write, set_config
from binux.packages import Addons, fetch, safe_extract
from binux.daemon import rpc, Supervisor
from binux.desktop import chrome_compatibility

def wait_until(check, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for real process state")

class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"BINUX_HOME": self.temp.name})
        self.env.start()
        base()
    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

class ProcessTests(Isolated):
    def tearDown(self):
        try:
            rpc("shutdown")
            path = base() / "config/runtime.sock"
            wait_until(lambda: not path.exists())
        finally:
            super().tearDown()

    def test_python_real_output_exit_and_argv_preserved(self):
        marker = "; touch should-not-exist; $(id)"
        job = rpc("run", argv=[sys.executable, "-c", "import sys;print('한국어',sys.argv[1]);sys.exit(7)", marker], cwd=self.temp.name)
        row = wait_until(lambda: next((r for r in rpc("list") if r["id"] == job["id"] and r["state"] == "exited"), None))
        self.assertEqual(row["exit_code"], 7)
        self.assertIn("한국어 " + marker, rpc("logs", id=job["id"]))
        self.assertFalse(Path(self.temp.name, "should-not-exist").exists())

    def test_cli_exit_does_not_end_server_and_stop_terminates(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
        command = [sys.executable, "-m", "binux", "bg", "run", sys.executable, "-u", "-m", "http.server", str(port), "--bind", "127.0.0.1"]
        starter = subprocess.run(command, capture_output=True, text=True, cwd=self.temp.name)
        self.assertEqual(starter.returncode, 0, starter.stderr)
        job = json.loads(starter.stdout)
        def reachable():
            try:
                return urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=0.3).status == 200
            except OSError:
                return False
        wait_until(reachable)
        self.assertGreater(job["pid"], 1)
        self.assertIn("GET", rpc("logs", id=job["id"]))
        rpc("stop", id=job["id"])
        wait_until(lambda: next(r for r in rpc("list") if r["id"] == job["id"])["state"] == "exited")
        self.assertFalse(reachable())

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_node_server_template_loopback_http(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
        from binux.cli import main
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["server", "create", "node-test", "--kind", "node", "--port", str(port)]), 0)
            self.assertEqual(main(["server", "start", "node-test"]), 0)
        def reachable():
            try:
                return urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=0.3).read() == b"binux server\n"
            except OSError:
                return False
        wait_until(reachable)
        records = read(base() / "config/servers.json")
        self.assertEqual(records["node-test"]["listen"], "127.0.0.1")

    def test_group_stop_reaches_spawned_child(self):
        script = "import subprocess,time; p=subprocess.Popen(['sleep','120']); print(p.pid,flush=True); time.sleep(120)"
        job = rpc("run", argv=[sys.executable, "-u", "-c", script], cwd=self.temp.name)
        child = int(wait_until(lambda: rpc("logs", id=job["id"]).strip()))
        rpc("stop", id=job["id"])
        def dead():
            path = Path(f"/proc/{child}/stat")
            return not path.exists() or path.read_text().rsplit(") ", 1)[1].startswith("Z ")
        wait_until(dead)

    def test_missing_executable_is_error(self):
        with self.assertRaises(ValueError):
            rpc("run", argv=["/binux/not-installed"], cwd=self.temp.name)

    def test_opt_in_restart_has_bounded_attempts(self):
        job = rpc("run", argv=[sys.executable, "-c", "raise SystemExit(5)"], cwd=self.temp.name, restart_on_failure=True)
        record = wait_until(lambda: next((r for r in rpc("list") if r["id"] == job["id"] and r["state"] == "exited" and r["restart_count"] == 3), None))
        self.assertEqual(record["exit_code"], 5)

    def test_stale_pid_restored_as_interrupted_never_running(self):
        root = base()
        write(root / "config/jobs.json", {"old": {"id": "old", "pid": os.getpid(), "state": "running", "started": 1}})
        supervisor = Supervisor(root)
        self.assertEqual(supervisor.records["old"]["state"], "interrupted")
        self.assertIsNone(supervisor.records["old"]["pid"])

    def test_storage_shortage_refuses_job(self):
        class Full:
            f_bavail = 0
            f_frsize = 4096
        supervisor = Supervisor(base())
        with patch("os.statvfs", return_value=Full()), self.assertRaisesRegex(ValueError, "Insufficient storage"):
            supervisor.start([sys.executable], self.temp.name)

    def test_external_server_requires_explicit_approval_flag(self):
        from binux.cli import main
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["server", "create", "exposed", "--listen", "0.0.0.0"]), 1)
        self.assertFalse((base() / "projects/python/exposed").exists())

    def test_pause_resume_real_process(self):
        job = rpc("run", argv=[sys.executable, "-u", "-c", "import time\nwhile True: print('tick',flush=True);time.sleep(.05)"], cwd=self.temp.name)
        wait_until(lambda: rpc("logs", id=job["id"]))
        rpc("pause")
        wait_until(lambda: Path(f'/proc/{job["pid"]}/stat').read_text().rsplit(") ", 1)[1].startswith("T "))
        before = len(rpc("logs", id=job["id"]))
        time.sleep(0.15)
        self.assertEqual(before, len(rpc("logs", id=job["id"])))
        rpc("resume")
        wait_until(lambda: len(rpc("logs", id=job["id"])) > before)

class PackageTests(Isolated):
    def archive(self, name="content.txt", content=b"binux"):
        archive = base() / "cache/package.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            info = tarfile.TarInfo(name); info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        return archive

    def test_archive_traversal_rejected(self):
        archive = self.archive("../../escape")
        with self.assertRaisesRegex(ValueError, "traversal"):
            safe_extract(archive, base() / "addons")
        self.assertFalse((Path(self.temp.name).parent / "escape").exists())

    def test_archive_symlink_rejected(self):
        archive = base() / "cache/link.tar"
        with tarfile.open(archive, "w") as tar:
            info = tarfile.TarInfo("link"); info.type = tarfile.SYMTYPE; info.linkname = "/etc"
            tar.addfile(info)
        with self.assertRaisesRegex(ValueError, "links"):
            safe_extract(archive, base() / "addons")

    def test_sha_mismatch_removes_partial_download(self):
        class Response(io.BytesIO):
            url = "https://github.com/verified/archive"
            headers = {"Content-Length": "6"}
        destination = base() / "cache/bad"
        with patch("urllib.request.urlopen", return_value=Response(b"tamper")), self.assertRaisesRegex(ValueError, "SHA-256"):
            fetch(Response.url, destination, expected_hash="0" * 64)
        self.assertFalse(destination.exists())

    def test_http_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            fetch("http://github.com/unsafe", base() / "cache/bad")

    def test_addon_real_files_signed_install_remove(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        archive = self.archive()
        raw = archive.read_bytes()
        package = {"name": "demo", "version": "0.1.0", "sha256": hashlib.sha256(raw).hexdigest(), "url": "https://github.com/BlecaStudio/test-only/releases/download/test/demo.tar.gz", "platform": "linux", "arch": "any", "dependencies": []}
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        signed = json.dumps(package, sort_keys=True, separators=(",", ":")).encode()
        package["signature"] = base64.b64encode(key.sign(signed)).decode()
        set_config("official_repo", "BlecaStudio/test-only")  # Synthetic test fixture; never a published URL.
        set_config("addon_ed25519_key", base64.b64encode(public).decode())
        def download(url, destination, **kwargs):
            Path(destination).write_bytes(raw)
        with patch("binux.packages.fetch", side_effect=download):
            result = Addons().install("demo", [package])
        self.assertTrue(result["signature_verified"])
        self.assertEqual((base() / "addons/demo/content.txt").read_bytes(), b"binux")
        Addons().remove("demo")
        self.assertFalse((base() / "addons/demo").exists())

    def test_invalid_signature_preserves_previous_install(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        archive = self.archive()
        previous = base() / "addons/demo"; previous.mkdir(); (previous / "old").write_text("keep")
        key = Ed25519PrivateKey.generate()
        set_config("official_repo", "BlecaStudio/test-only")
        set_config("addon_ed25519_key", base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode())
        package = {"name": "demo", "version": "0.2.0", "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "url": "https://github.com/BlecaStudio/test-only/releases/download/test/demo.tar.gz", "platform": "linux", "arch": "any", "dependencies": [], "signature": base64.b64encode(b"0" * 64).decode()}
        with patch("binux.packages.fetch", side_effect=lambda url, target, **kwargs: Path(target).write_bytes(archive.read_bytes())):
            with self.assertRaises(Exception):
                Addons().install("demo", [package])
        self.assertEqual((previous / "old").read_text(), "keep")

    def test_official_repository_unset_returns_error(self):
        with self.assertRaisesRegex(ValueError, "not configured"):
            Addons().catalog()

    def test_wrong_publisher_asset_rejected(self):
        with self.assertRaises(ValueError):
            Addons.validate_url("https://github.com/attacker/repo/releases/download/x/data", "BlecaStudio/test-only")

    def test_proot_chrome_rejected_without_sandbox_bypass(self):
        compatible, reason = chrome_compatibility("aarch64")
        self.assertFalse(compatible)
        self.assertIn("ARM64", reason)
        compatible, reason = chrome_compatibility("x86_64")
        self.assertFalse(compatible)
        self.assertIn("sandbox", reason)

class PtyTests(unittest.TestCase):
    def test_real_bash_tty_unicode_file_commands_and_exit_status(self):
        import pty
        import select
        pid, master = pty.fork()
        if pid == 0:
            os.execv("/bin/bash", ["bash", "--noprofile", "--norc", "-i"])
        try:
            os.write(master, "test -t 0 && printf 'PTY_OK\\n'; d=$(mktemp -d); cd \"$d\"; printf '비눅스\\n' > hello; ls; pwd; cat hello; rm hello; cd /; rmdir \"$d\"; printf '\\033[31mANSI_OK\\033[0m\\n'; exit 13\n".encode())
            data = b""
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(master, 8192)
                    except OSError:
                        break
                    if not chunk:
                        break
                    data += chunk
            _, status = os.waitpid(pid, 0)
            self.assertEqual(os.waitstatus_to_exitcode(status), 13)
            text = data.decode("utf-8")
            self.assertIn("PTY_OK", text)
            self.assertIn("비눅스\r\n", text)
            self.assertIn("\x1b[31mANSI_OK\x1b[0m", text)
        finally:
            os.close(master)

if __name__ == "__main__":
    unittest.main()
