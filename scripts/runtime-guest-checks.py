#!/usr/bin/env python3
"""Integration checks executed inside a real, disposable ARM64 Linux guest."""
import contextlib
import json
import os
from pathlib import Path
import signal
import shutil
import hashlib
import sys
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
    with tempfile.TemporaryDirectory(prefix='binux-http-test-') as temporary:
        log=Path(temporary)/'server.log'
        with process(argv,logfile=log) as child:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError(f'Server exited ({child.returncode}) before readiness: {argv}\n'+log.read_text(errors='replace')[-8192:])
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=2) as reply:
                        assert reply.status == 200
                        assert expected in reply.read()
                        break
                except (OSError, urllib.error.URLError):
                    time.sleep(.5)
            else:
                raise RuntimeError(f'Server never became ready: {argv}\n'+log.read_text(errors='replace')[-8192:])
    with socket.socket() as closed:
        assert closed.connect_ex(('127.0.0.1', port)) != 0, 'Server did not stop'
    print(f'PASS actual HTTP response and process stop: {argv[0]}', flush=True)


home = Path('/home/binux')
if sys.argv[1:]==['--node-probe']:
    project=home/'test-js'
    script='const app=require(process.argv[1])();app.get("/",(q,s)=>s.send("binux Express"));const server=app.listen(0,"127.0.0.1",()=>{console.log("Express listener ready");server.close();});'
    command=['node','-e',script,str(project/'node_modules/express')]
    result=subprocess.run(command,capture_output=True,text=True,timeout=90)
    print(result.stdout,flush=True)
    if result.returncode:
        print(result.stderr,flush=True)
        package=project/'node_modules/debug/package.json'
        data=package.read_bytes()
        print('Guest debug/package.json:',len(data),hashlib.sha256(data).hexdigest(),repr(data[:128]),flush=True)
        try:json.loads(data);print('Python JSON parsing: valid',flush=True)
        except ValueError as error:print('Python JSON parsing:',error,flush=True)
        for label,extra,env in [('io_uring disabled',[],{**os.environ,'UV_USE_IO_URING':'0'}),('V8 interpreter',['--jitless'],os.environ)]:
            check=subprocess.run(['node',*extra,*command[1:]],capture_output=True,text=True,env=env,timeout=90)
            print(label,check.returncode,check.stdout,check.stderr[-4096:],flush=True)
        with tempfile.TemporaryDirectory(prefix='binux-node-ext4-') as folder:
            shutil.copytree(project/'node_modules',Path(folder)/'node_modules')
            check=subprocess.run(['node','-e',script,str(Path(folder)/'node_modules/express')],capture_output=True,text=True,timeout=90)
            print('Guest ext4 copy:',check.returncode,check.stdout,check.stderr[-4096:],flush=True)
        raise SystemExit(1)
    print('PASS Express module loading and listener creation',flush=True)
    raise SystemExit(0)
if sys.argv[1:]==['--browser-only']:
    subprocess.run(['binux','desktop','install','--yes','--features','chrome'],check=True,timeout=1800)
    browser=json.loads(Path('/var/lib/binux/state/config/desktop.json').read_text())
    assert browser['installed'] and 'google-chrome-stable' in browser['packages']
    assert browser['browser'] in ('google-chrome-stable','unavailable')
    assert browser['browser_sandbox_verified']==(browser['browser']=='google-chrome-stable')
    print('PASS real official Chrome packages; sandbox launch result:',browser['browser'],flush=True)
    raise SystemExit(0)
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
