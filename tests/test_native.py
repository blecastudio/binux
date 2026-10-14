import json
import os
import socket
import subprocess
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class NativeTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"native/build/host/binuxctl").exists(), "Build native host tools first")
    def test_real_control_socket_preserves_json_arguments_and_exit_code(self):
        name="binux-test-"+uuid.uuid4().hex
        got=[]
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
            server.bind("\0"+name);server.listen()
            def respond():
                with server.accept()[0] as client:
                    got.append(json.loads(client.makefile("rb").readline()))
                    client.sendall("7\n비눅스 control response\n".encode())
            thread=threading.Thread(target=respond);thread.start()
            args=["bg","run",'a"b\\c\n한국어',"$(id)"]
            result=subprocess.run([str(ROOT/"native/build/host/binuxctl"),*args],env={**os.environ,"BINUX_CONTROL":name},capture_output=True,text=True,timeout=5)
            thread.join(timeout=5)
        self.assertEqual(got,[args]);self.assertEqual(result.returncode,7)
        self.assertEqual(result.stdout,"비눅스 control response\n")

    @unittest.skipUnless((ROOT/"native/build/host/binuxjob").exists(), "Build native host tools first")
    def test_real_pid_handshake_and_exec(self):
        with tempfile.TemporaryDirectory() as folder:
            pidfile=Path(folder)/"job.pid"
            result=subprocess.run([str(ROOT/"native/build/host/binuxjob"),"/bin/bash","-c","printf '%s' \"$BASHPID\"; exit 12"],env={**os.environ,"BINUX_PID_FILE":str(pidfile)},capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,12)
            self.assertEqual(pidfile.read_text().strip(),result.stdout)
