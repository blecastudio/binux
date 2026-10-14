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
    @unittest.skipUnless((ROOT/"native/build/host/binuxbridge").exists(), "Build native bridge first")
    def test_stream_bridge_frames_unicode_exact_arguments_and_real_exit_code(self):
        import struct
        name="binux-stream-test-"+uuid.uuid4().hex;got=[]
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
            server.bind("\0"+name);server.listen()
            def respond():
                with server.accept()[0] as client:
                    header=b""
                    while not header.endswith(b"\n"):header+=client.recv(1)
                    got.append(json.loads(header))
                    for kind,data in [(b'O','한국어 output\n'.encode()),(b'E',b'real stderr\n'),(b'X',struct.pack('!I',23))]:
                        client.sendall(kind+struct.pack('!I',len(data))+data)
            thread=threading.Thread(target=respond);thread.start()
            argv=['python3','a b','$(id)','한국어\n"quoted"']
            result=subprocess.run([str(ROOT/'native/build/host/binuxbridge'),'--runtime','ubuntu',*argv],input=b'',env={**os.environ,'BINUX_STREAM':name},capture_output=True,timeout=5)
            thread.join(timeout=5)
        self.assertEqual(got[0][0:2],['exec','ubuntu']);self.assertEqual(got[0][6],argv)
        self.assertEqual(result.returncode,23);self.assertEqual(result.stdout,'한국어 output\n'.encode());self.assertEqual(result.stderr,b'real stderr\n')
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
