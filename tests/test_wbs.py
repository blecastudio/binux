import base64
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from binux import wbs
from test_core import wait_until

class WbsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.a = Path(cls.temp.name) / "a"
        cls.b = Path(cls.temp.name) / "b"
        cls.c = Path(cls.temp.name) / "unapproved"
        cls.share = Path(cls.temp.name) / "shared"; cls.share.mkdir()
        for root in (cls.a, cls.b, cls.c):
            with patch.dict(os.environ, {"BINUX_HOME": str(root)}):
                wbs.identity()
        cls.approved_command = [sys.executable, "-c", "print('approved 한국어')"]
        with patch.dict(os.environ, {"BINUX_HOME": str(cls.a)}):
            wbs.approve(cls.b / "wbs/identity.pem", "client", {"inbox": cls.share}, [cls.approved_command])
        for root in (cls.b, cls.c):
            with patch.dict(os.environ, {"BINUX_HOME": str(root)}):
                wbs.approve(cls.a / "wbs/identity.pem", "server")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); cls.port = sock.getsockname()[1]
        cls.server_log = (Path(cls.temp.name) / "server.log").open("wb")
        cls.server = subprocess.Popen([sys.executable, "-m", "binux.wbs", "serve", "--port", str(cls.port)], env={**os.environ, "BINUX_HOME": str(cls.a)}, stdout=cls.server_log, stderr=cls.server_log)
        def ready():
            with patch.dict(os.environ, {"BINUX_HOME": str(cls.b)}):
                try:
                    return wbs.request("127.0.0.1", "server", {"op": "info"}, cls.port)
                except (OSError, ValueError):
                    return False
        wait_until(ready)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate(); cls.server.wait(timeout=5)
        cls.server_log.close(); cls.temp.cleanup()

    def setUp(self):
        self.env = patch.dict(os.environ, {"BINUX_HOME": str(self.b)})
        self.env.start()
    def tearDown(self):
        self.env.stop()
    def send(self, payload):
        return wbs.request("127.0.0.1", "server", payload, self.port)

    def test_mutual_approval_info(self):
        info = self.send({"op": "info"})
        self.assertEqual(info["protocol"], 1)
        self.assertEqual(info["shares"], ["inbox"])

    def test_unapproved_development_port_is_blocked(self):
        with self.assertRaises(PermissionError):
            wbs.open_port('127.0.0.1','server',8000,self.port)

    def test_approved_port_relays_actual_http_and_revocation_closes_access(self):
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        import threading
        from binux.state import read,write
        http=ThreadingHTTPServer(('127.0.0.1',0),BaseHTTPRequestHandler)
        remote_port=http.server_address[1]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(inner):inner.send_response(200);inner.end_headers();inner.wfile.write(b'WBS authenticated port\n')
            def log_message(inner,*args):pass
        http.RequestHandlerClass=Handler
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        with patch.dict(os.environ,{'BINUX_HOME':str(self.a)}):
            records=wbs.peers();records['client']['ports']=[remote_port];write(wbs.home()/'peers.json',records)
        try:
            with wbs.open_port('127.0.0.1','server',remote_port,self.port) as stream:
                stream.sendall(b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n')
                output=b''
                while data:=stream.recv(4096):output+=data
            self.assertIn(b'WBS authenticated port\n',output)
            with patch.dict(os.environ,{'BINUX_HOME':str(self.a)}):
                records=wbs.peers();records['client']['ports']=[];write(wbs.home()/'peers.json',records)
            with self.assertRaises(PermissionError):wbs.open_port('127.0.0.1','server',remote_port,self.port)
        finally:
            http.shutdown();http.server_close();thread.join(timeout=5)

    def test_real_file_upload_download_and_hash(self):
        data = "binux 파일 전송\n".encode()
        digest = hashlib.sha256(data).hexdigest()
        result = self.send({"op": "put", "share": "inbox", "path": "project/hello.txt", "data": base64.b64encode(data).decode(), "sha256": digest, "overwrite": True})
        self.assertEqual(result["sha256"], digest)
        self.assertEqual((self.share / "project/hello.txt").read_bytes(), data)
        received = self.send({"op": "get", "share": "inbox", "path": "project/hello.txt"})
        self.assertEqual(base64.b64decode(received["data"]), data)

    def test_unapproved_certificate_blocked(self):
        with patch.dict(os.environ, {"BINUX_HOME": str(self.c)}):
            with self.assertRaises((OSError, ValueError)):
                self.send({"op": "info"})

    def test_unapproved_folder_blocked(self):
        with self.assertRaises(PermissionError):
            self.send({"op": "get", "share": "private", "path": "key.pem"})

    def test_path_traversal_blocked(self):
        with self.assertRaises(PermissionError):
            self.send({"op": "get", "share": "inbox", "path": "../a/wbs/key.pem"})

    def test_symlink_escape_blocked(self):
        link = self.share / "escape"
        link.symlink_to(self.a, target_is_directory=True)
        try:
            with self.assertRaises(PermissionError):
                self.send({"op": "get", "share": "inbox", "path": "escape/wbs/key.pem"})
        finally:
            link.unlink()

    def test_corrupted_upload_blocked(self):
        with self.assertRaises(PermissionError):
            self.send({"op": "put", "share": "inbox", "path": "corrupt.txt", "data": base64.b64encode(b"bad").decode(), "sha256": "0" * 64})
        self.assertFalse((self.share / "corrupt.txt").exists())

    def test_exact_approved_command_only(self):
        result = self.send({"op": "exec", "argv": self.approved_command})
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("approved 한국어", result["output"])
        with self.assertRaises(PermissionError):
            self.send({"op": "exec", "argv": ["/bin/sh", "-c", "id"]})

    def test_identity_rotation_requires_revocation(self):
        with self.assertRaisesRegex(ValueError, "Identity exists"):
            wbs.identity()

    def test_sync_is_real_one_way_transfer(self):
        import contextlib
        import io
        from binux.state import write
        folder=Path(self.temp.name)/"sync-source";folder.mkdir()
        (folder/"sync.txt").write_text("version one")
        write(self.b/"wbs/endpoint.json",{"ip":"127.0.0.1","peer":"server","port":self.port})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wbs.main(["sync",str(folder),"--remote-share","inbox","--overwrite"]),0)
            self.assertEqual(wbs.main(["sync",str(folder),"--remote-share","inbox","--overwrite"]),0)
            (folder/"sync.txt").write_text("version two")
            self.assertEqual(wbs.main(["sync",str(folder),"--remote-share","inbox","--overwrite"]),0)
        self.assertEqual((self.share/"sync.txt").read_text(),"version two")

    def test_revocation_blocks_next_request_without_restart(self):
        with patch.dict(os.environ,{"BINUX_HOME":str(self.a)}):
            wbs.revoke("client")
        try:
            with self.assertRaises((ValueError,OSError)):
                self.send({"op":"info"})
        finally:
            with patch.dict(os.environ,{"BINUX_HOME":str(self.a)}):
                wbs.approve(self.b/"wbs/identity.pem","client",{"inbox":self.share},[self.approved_command])

if __name__ == "__main__":
    unittest.main()
