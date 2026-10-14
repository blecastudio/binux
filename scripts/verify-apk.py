#!/usr/bin/env python3
"""Checks bundled ABI, ELF interpreter/dependencies, and 16 KiB LOAD alignment."""
import argparse
import os
import re
import subprocess
import tempfile
import zipfile
import json,hashlib
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("apk")
p.add_argument("--kind",choices=("terminal","x11"),default="terminal")
p.add_argument("--readelf",default="readelf")
a=p.parse_args()
required={"libbinux_bash.so","libbinuxctl.so","libbinuxjob.so","libbinuxbridge.so","libbinux_vm.so","libbinux_process.so","libtermux.so"}
if a.kind=="x11": required={"libXlorie.so"}
with zipfile.ZipFile(a.apk) as apk, tempfile.TemporaryDirectory() as temporary:
    for notice in ('assets/licenses/LICENSE','assets/licenses/NOTICE.md','assets/licenses/TERMUX-LICENSE.md'):
        if notice not in apk.namelist():
            raise SystemExit('APK is missing bundled license notice: '+notice)
    if a.kind=="terminal":
        manifest=json.loads(apk.read('assets/runtime-manifest.json'))
        if manifest.get('schema')!=1 or manifest.get('architecture')!='aarch64' or not re.fullmatch('[0-9a-f]{40}',manifest.get('source_commit','')):
            raise SystemExit('Invalid pinned runtime manifest')
        for distro in ('debian','ubuntu'):
            for suffix in ('kernel','initrd','disk.qcow2'):
                entry=manifest['assets'][f'{distro}-{suffix}']
                if not re.fullmatch('[0-9a-f]{64}',entry['sha256']) or entry['bytes']<=0 or not entry['url'].startswith('https://github.com/blecastudio/binux/releases/download/runtime-'):
                    raise SystemExit('Invalid pinned runtime asset')
        installer=json.loads(apk.read('assets/installer-manifest.json'))
        source=(Path(__file__).resolve().parents[1]/'setup-binux-desktop').read_bytes()
        if hashlib.sha256(source).hexdigest()!=installer['sha256']:
            raise SystemExit('APK and reviewed installer do not match')
        print('PASS pinned runtime data and reviewed installer metadata')
    entries=[name for name in apk.namelist() if name.startswith("lib/") and name.endswith(".so")]
    actual={Path(name).name for name in entries if name.startswith("lib/arm64-v8a/")}
    if not required <= actual:
        raise SystemExit("APK is missing required executable/library entries: "+str(required-actual))
    for name in entries:
        if not name.startswith("lib/arm64-v8a/"):
            raise SystemExit("Unexpected packaged ABI: "+name)
        path=Path(temporary)/Path(name).name;path.write_bytes(apk.read(name))
        result=subprocess.check_output([a.readelf,"-lW",str(path)],text=True)
        loads=[line for line in result.splitlines() if line.strip().startswith("LOAD")]
        if not loads or any(int(line.split()[-1],16)<16384 for line in loads):
            raise SystemExit("ELF does not support 16 KiB pages: "+name)
        if Path(name).name in {"libbinux_bash.so","libbinuxctl.so","libbinuxjob.so","libbinuxbridge.so","libbinux_vm.so"} and "/system/bin/linker64" not in result:
            raise SystemExit("Missing Android dynamic linker: "+name)
        dynamic=subprocess.check_output([a.readelf,"-dW",str(path)],text=True)
        needed=re.findall(r'Shared library: \[(.*?)\]',dynamic)
        print(f"PASS {name}: 16 KiB, needs {', '.join(needed)}")
print("APK static checks passed; Android runtime execution still requires device tests.")
