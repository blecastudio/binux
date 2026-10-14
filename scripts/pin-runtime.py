#!/usr/bin/env python3
"""Pin an already published, immutable BlecaStudio runtime Release in the APK."""
import argparse
import json
from pathlib import Path
import re
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('url', help='Published runtime-SHA/manifest.json Release asset URL')
args = parser.parse_args()
prefix = 'https://github.com/blecastudio/binux/releases/download/'
match = re.fullmatch(re.escape(prefix) + r'runtime-([0-9a-f]{12})/manifest.json', args.url)
if not match:
    parser.error('Use the immutable official runtime-SHA Release asset URL')
with urllib.request.urlopen(args.url, timeout=60) as response:
    data = response.read(1024 * 1024 + 1)
if len(data) > 1024 * 1024:
    raise SystemExit('Manifest exceeds 1 MiB')
manifest = json.loads(data)
commit = manifest.get('source_commit', '')
if (manifest.get('schema') != 1 or manifest.get('architecture') != 'aarch64'
        or not re.fullmatch(r'[0-9a-f]{40}', commit) or not commit.startswith(match[1])
        or manifest.get('disk_bytes') != 10737418240):
    raise SystemExit('Invalid runtime identity or disk metadata')
for distribution in ('debian', 'ubuntu'):
    for suffix in ('kernel', 'initrd', 'disk.qcow2'):
        name = f'{distribution}-{suffix}'
        entry = manifest['assets'][name]
        if (not re.fullmatch(r'[0-9a-f]{64}', entry['sha256'])
                or type(entry['bytes']) is not int or entry['bytes'] <= 0
                or entry['url'] != args.url.removesuffix('manifest.json') + name):
            raise SystemExit('Invalid runtime asset: ' + name)
destination = Path(__file__).resolve().parents[1] / 'android/app/src/main/assets/runtime-manifest.json'
temporary = destination.with_suffix('.tmp')
temporary.write_text(json.dumps(manifest, indent=2) + '\n')
temporary.replace(destination)
print('Pinned published runtime', commit)
