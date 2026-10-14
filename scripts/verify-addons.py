#!/usr/bin/env python3
import base64,hashlib,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'core'))
from binux.trust import ADDON_ED25519_KEY
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
path=pathlib.Path(sys.argv[1]);manifest=json.loads(path.read_text());assert manifest['schema']==1
key=Ed25519PublicKey.from_public_bytes(base64.b64decode(ADDON_ED25519_KEY,validate=True))
for package in manifest['packages']:
 signed=json.dumps({k:package[k] for k in ('name','version','sha256','url','platform','arch','dependencies')},sort_keys=True,separators=(',',':')).encode()
 key.verify(base64.b64decode(package['signature'],validate=True),signed)
 archive=path.parent/pathlib.PurePosixPath(package['url']).name
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==package['sha256']
 print('PASS Ed25519 / SHA-256',package['name'],package['version'])
