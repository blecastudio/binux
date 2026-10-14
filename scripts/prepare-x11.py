#!/usr/bin/env python3
"""Reconstruct the Binux X11 dependencies from SHA-256 pinned, vendored sources."""
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
archives=root/'third_party/x11'
source=root/'android/desktop-x11/src/main/cpp'
records=json.loads((archives/'sources.json').read_text())
for name,record in records.items():
    archive=archives/record['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=record['sha256']:
        raise SystemExit('Source integrity verification failed: '+name)
    if name=='xkb-data':
        with tempfile.TemporaryDirectory() as temporary:
            subprocess.run(['dpkg-deb','-x',str(archive),temporary],check=True)
            assets=root/'android/desktop-x11/src/main/assets/xkb'
            shutil.copytree(Path(temporary)/'usr/share/X11/xkb',assets,dirs_exist_ok=True)
        continue
    target=source/name
    stamp=target/'.binux-source'
    if stamp.is_file() and stamp.read_text().strip()==record['sha256']:
        continue
    with tempfile.TemporaryDirectory() as temporary:
        with tarfile.open(archive) as package:
            package.extractall(temporary,filter='data')
        parent=Path(temporary)
        original=next(parent.glob('*/xkbcomp')) if name=='xkbcomp' else next(p for p in parent.iterdir() if p.is_dir())
        if target.exists():shutil.rmtree(target)
        shutil.copytree(original,target)
        stamp.write_text(record['sha256']+'\n')
print('Verified and prepared 17 X11 sources; CMake applies reviewed patches.')
