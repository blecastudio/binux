#!/usr/bin/env python3
"""Build deterministic, signed data/source add-ons; no automatic install hooks."""
import argparse,base64,hashlib,io,json,pathlib,tarfile
from cryptography.hazmat.primitives.serialization import load_pem_private_key
p=argparse.ArgumentParser();p.add_argument('--key',required=True);p.add_argument('--output',required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
key=load_pem_private_key(pathlib.Path(a.key).read_bytes(),password=None)
from sys import path
path.insert(0,str(root/'core'))
from binux.trust import ADDON_ED25519_KEY
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
assert base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()==ADDON_ED25519_KEY
packages=[]
for name,files in {
 'desktop':{'setup-binux-desktop':root/'setup-binux-desktop','README.md':root/'runtime/addons/DESKTOP.md'},
 'developer-tools':{'install-tools':root/'runtime/addons/install-tools','README.md':root/'runtime/addons/DEVELOPER.md'},
 'wbs':{'README.md':root/'runtime/addons/WBS.md',**{'lib/binux/'+f.name:f for f in (root/'core/binux').glob('*.py')}},
}.items():
 archive=out/(name+'-1.0.0.tar.gz')
 # Tar mtime/permissions/ownership are reproducible. gzip header timestamp is fixed.
 import gzip
 with archive.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w') as tar:
  for destination,source in sorted(files.items()):
   data=source.read_bytes();info=tarfile.TarInfo(destination);info.size=len(data);info.mode=0o644;info.mtime=0
   tar.addfile(info,io.BytesIO(data))
 package={'name':name,'version':'1.0.0','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'url':f'https://github.com/blecastudio/binux/releases/download/v1.0.0/{archive.name}','platform':'linux','arch':'any','dependencies':[]}
 signed=json.dumps(package,sort_keys=True,separators=(',',':')).encode();package['signature']=base64.b64encode(key.sign(signed)).decode();packages.append(package)
(out/'binux-addons.json').write_text(json.dumps({'schema':1,'packages':packages},indent=2)+'\n')
print('Signed add-ons created:',','.join(p['name'] for p in packages))
