#!/usr/bin/env python3
import hashlib,json,tarfile,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=root/'third_party/vm';target=root/'native/build/vm/sources';target.mkdir(parents=True,exist_ok=True)
for name,entry in json.loads((base/'sources.json').read_text()).items():
 p=base/entry['archive']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise SystemExit('Source verification failed: '+name)
 stamp=target/(name+'.stamp')
 if stamp.exists() and stamp.read_text()==entry['sha256']:continue
 with tarfile.open(p) as t:
  if 'subproject' in entry:
   dest=target/'qemu-9.2.4/subprojects'/entry['subproject'];dest.mkdir(parents=True,exist_ok=True)
   for member in t.getmembers():
    parts=Path(member.name).parts
    if len(parts)<2:continue
    member.name=str(Path(*parts[1:]));t.extract(member,dest,filter='data')
  else:t.extractall(target,filter='data')
 stamp.write_text(entry['sha256'])
qemu=target/'qemu-9.2.4'
for name in ('berkeley-softfloat-3','berkeley-testfloat-3'):
 shutil.copytree(qemu/'subprojects/packagefiles'/name,qemu/'subprojects'/name,dirs_exist_ok=True)
for patch in sorted((base/'patches').glob('*.patch')):
 destination=qemu if patch.name.startswith('qemu-') else target/'libslirp-v4.8.0'
 raw=patch.read_bytes()
 check=subprocess.run(['patch','--dry-run','-p1','-d',str(destination)],input=raw,capture_output=True)
 if check.returncode==0:subprocess.run(['patch','-p1','-d',str(destination)],input=raw,check=True)
 elif subprocess.run(['patch','--dry-run','-R','-p1','-d',str(destination)],input=raw,capture_output=True).returncode!=0:
  raise SystemExit('QEMU patch no longer applies: '+patch.name)
# libtool 2.5 removed LT_SYS_SYMBOL_USCORE. AArch64 Android has no symbol prefix.
ffi=target/'libffi-3.4.8/configure.ac'
text=ffi.read_text();text=text.replace('LT_SYS_SYMBOL_USCORE','sys_symbol_underscore=no');ffi.write_text(text)
print('VM sources and Bionic compatibility patches verified')
