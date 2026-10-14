#!/usr/bin/env python3
"""Integration checks executed inside a real, disposable ARM64 Linux guest."""
import contextlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request


@contextlib.contextmanager
def process(argv, environment=None, logfile=None):
    output = open(logfile, 'wb') if logfile else subprocess.DEVNULL
    child = subprocess.Popen(argv, env=environment, stdout=output,
                             stderr=subprocess.STDOUT, start_new_session=True)
    try:
        yield child
    finally:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        if logfile:
            output.close()


def http_check(argv, port, expected):
    with process(argv) as child:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError(f'Server exited before readiness: {argv}')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=2) as reply:
                    assert reply.status == 200
                    assert expected in reply.read()
                    break
            except (OSError, urllib.error.URLError):
                time.sleep(.5)
        else:
            raise RuntimeError(f'Server never became ready: {argv}')
    with socket.socket() as closed:
        assert closed.connect_ex(('127.0.0.1', port)) != 0, 'Server did not stop'
    print(f'PASS actual HTTP response and process stop: {argv[0]}', flush=True)


home = Path('/home/binux')
venv = home / '.venv/bin/python'
http_check([str(venv), '-c', 'from flask import Flask;app=Flask(__name__);'
            'app.add_url_rule("/",view_func=lambda:"binux Flask");'
            'app.run(host="127.0.0.1",port=18001)'], 18001, b'binux Flask')
http_check([str(venv), '-c', 'from fastapi import FastAPI;import uvicorn;'
            'app=FastAPI();app.get("/")(lambda:{"runtime":"binux FastAPI"});'
            'uvicorn.run(app,host="127.0.0.1",port=18002)'], 18002, b'binux FastAPI')
http_check(['node', '-e', 'const app=require("/home/binux/test-js/node_modules/express")();'
            'app.get("/",(q,s)=>s.send("binux Express"));'
            'app.listen(18003,"127.0.0.1")'], 18003, b'binux Express')

# Exercise the same reviewed installer and current Python core shipped by the APK.
subprocess.run(['binux', 'desktop', 'install', '--yes', '--features', 'files,editor,wbs'],
               check=True, timeout=1800)
metadata=Path('/var/lib/binux/state/config/desktop.json')
owned=set(json.loads(metadata.read_text())['owned_packages'])
subprocess.run(['/bin/bash','/run/binux-bootstrap/setup-binux-desktop','--yes','--features','none'],
               check=True,timeout=300)
assert owned==set(json.loads(metadata.read_text())['owned_packages']), 'Installer lost previous package ownership'
subprocess.run(['sudo', 'apt-get', 'install', '-y', '--no-install-recommends', 'xvfb'],
               check=True, timeout=600)
with tempfile.TemporaryDirectory(prefix='binux-xfce-test-') as temporary:
    work = Path(temporary)
    authority = work / 'authority'
    authority.touch(mode=0o600)
    subprocess.run(['xauth', '-f', str(authority), 'add', ':9', '.', os.urandom(16).hex()], check=True)
    env = {**os.environ, 'DISPLAY': ':9', 'XAUTHORITY': str(authority)}
    with process(['Xvfb', ':9', '-screen', '0', '1024x768x24', '-nolisten', 'tcp',
                  '-auth', str(authority)], logfile=work/'xvfb.log') as xserver:
        for attempt in range(60):
            if subprocess.run(['xdpyinfo'], env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Authenticated Xvfb did not start')
        with process(['/var/lib/binux/state/desktop/start-x11'], environment=env,
                     logfile=work/'xfce.log') as desktop:
            for attempt in range(120):
                window_manager = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'xfwm4'],
                                                stdout=subprocess.DEVNULL).returncode == 0
                if window_manager and desktop.poll() is None:
                    print('PASS XFCE session and window manager on authenticated Xvfb (Android X11 display remains a device test)', flush=True)
                    break
                if desktop.poll() is not None:
                    raise RuntimeError((work/'xfce.log').read_text(errors='replace'))
                time.sleep(1)
            else:
                raise RuntimeError((work/'xfce.log').read_text(errors='replace'))
assert (home/'Desktop/binux-wbs.desktop').is_file()
print('PASS actual Desktop installer, optional file manager/editor/WBS launcher', flush=True)
