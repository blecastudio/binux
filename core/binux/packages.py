"""Release manifest installation without unverified hooks or executable extraction."""
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from .state import base, config, read, write

MAX_ARCHIVE = 512 * 1024 * 1024
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")

def fetch(url, destination, limit=MAX_ARCHIVE, expected_hash=None, progress=None):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError("Packages must use HTTPS without embedded credentials")
    destination = Path(destination)
    digest = hashlib.sha256()
    count = 0
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "binux/1.0.0"}), timeout=30) as response, destination.open("wb") as out:
            if urllib.parse.urlsplit(response.url).scheme != "https":
                raise ValueError("Insecure redirect")
            length = int(response.headers.get("Content-Length", 0))
            if length > limit or shutil.disk_usage(destination.parent).free < length + 1024 * 1024:
                raise ValueError("Package exceeds download limit or available storage")
            while chunk := response.read(64 * 1024):
                count += len(chunk)
                if count > limit:
                    raise ValueError("Download limit exceeded")
                digest.update(chunk)
                out.write(chunk)
                if progress:
                    progress(count, length)
        if expected_hash and digest.hexdigest() != expected_hash.lower():
            raise ValueError("SHA-256 verification failed")
        return digest.hexdigest()
    except Exception:
        destination.unlink(missing_ok=True)
        raise

def safe_extract(archive, target, max_size=MAX_ARCHIVE * 4):
    target = Path(target).resolve()
    total = 0
    with tarfile.open(archive, "r:*") as tar:
        members = tar.getmembers()
        for member in members:
            path = target / member.name
            if Path(member.name).is_absolute() or not path.resolve().is_relative_to(target):
                raise ValueError("Archive path traversal")
            if not (member.isfile() or member.isdir()):
                raise ValueError("Archive links, devices, and special files are forbidden")
            total += member.size
            if total > max_size:
                raise ValueError("Expanded archive exceeds limit")
        if shutil.disk_usage(target).free < total + 1024 * 1024:
            raise ValueError("Insufficient storage for extraction")
        for member in members:
            path = target / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, path.open("wb") as out:
                    shutil.copyfileobj(source, out)
                os.chmod(path, member.mode & 0o755)  # Never preserve setuid/setgid.

class Addons:
    def __init__(self):
        self.root = base()
        self.metadata = self.root / "config/addons.json"

    def installed(self):
        return read(self.metadata, {})

    def catalog(self):
        repo = config().get("official_repo")
        if not repo:
            raise ValueError("BlecaStudio official GitHub repository is not configured; no fabricated URL is used")
        if not re.fullmatch(r"BlecaStudio/[A-Za-z0-9_.-]+", repo, re.IGNORECASE):
            raise ValueError("Official repository must belong to BlecaStudio")
        path = self.root / "cache/release.json"
        fetch(f"https://api.github.com/repos/{repo}/releases/latest", path, 1024 * 1024)
        release = read(path)
        asset = next((x for x in release.get("assets", []) if x["name"] == "binux-addons.json"), None)
        if not asset:
            raise ValueError("Release has no binux-addons.json asset")
        manifest_path = self.root / "cache/addons-manifest.json"
        url = asset["browser_download_url"]
        self.validate_url(url, repo)
        fetch(url, manifest_path, 1024 * 1024)
        manifest = read(manifest_path)
        if manifest.get("schema") != 1 or not isinstance(manifest.get("packages"), list):
            raise ValueError("Unsupported add-on manifest schema")
        return manifest["packages"]

    @staticmethod
    def validate_url(url, repo):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.lower().startswith(f"/{repo}/releases/download/".lower()) or parsed.query or parsed.fragment:
            raise ValueError("Official asset URL must belong to the configured GitHub repository release")

    def install(self, name, catalog=None, progress=None):
        if not NAME.fullmatch(name):
            raise ValueError("Invalid add-on name")
        packages = self.catalog() if catalog is None else catalog
        package = next((p for p in packages if p.get("name") == name), None)
        if package is None:
            raise ValueError("Add-on not found")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", package.get("sha256", "")):
            raise ValueError("SHA-256 is required")
        if package.get("platform") != "linux" or package.get("arch") not in (platform.machine(), "any"):
            raise ValueError("Package is incompatible with this host runtime")
        installed = self.installed()
        missing = [d for d in package.get("dependencies", []) if d not in installed]
        if missing:
            raise ValueError("Missing dependencies: " + ", ".join(missing))
        repo = config().get("official_repo")
        if not repo:
            raise ValueError("Official repository is not configured")
        self.validate_url(package["url"], repo)
        with tempfile.TemporaryDirectory(dir=self.root / "cache") as temp:
            archive = Path(temp) / "archive.tar"
            fetch(package["url"], archive, expected_hash=package["sha256"], progress=progress)
            key = config().get("addon_ed25519_key")
            if key:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                public = Ed25519PublicKey.from_public_bytes(base64.b64decode(key, validate=True))
                signed = json.dumps({k: package[k] for k in ("name", "version", "sha256", "url", "platform", "arch", "dependencies")}, sort_keys=True, separators=(",", ":")).encode()
                try:
                    public.verify(base64.b64decode(package.get("signature", ""), validate=True), signed)
                except Exception as error:
                    raise ValueError("Ed25519 package signature verification failed") from error
            staging = Path(temp) / "staging"
            staging.mkdir()
            safe_extract(archive, staging)
            target = self.root / "addons" / name
            backup = Path(temp) / "previous"
            if target.exists():
                target.rename(backup)
            try:
                staging.rename(target)
                installed[name] = package
                write(self.metadata, installed)
            except Exception:
                if target.exists():
                    shutil.rmtree(target)
                if backup.exists():
                    backup.rename(target)
                raise
        return {"name": name, "version": package["version"], "signature_verified": bool(key), "path": str(target)}

    def remove(self, name):
        if not NAME.fullmatch(name):
            raise ValueError("Invalid add-on name")
        installed = self.installed()
        if name not in installed:
            raise ValueError("Add-on is not installed")
        dependents = [k for k, v in installed.items() if name in v.get("dependencies", [])]
        if dependents:
            raise ValueError("Required by: " + ", ".join(dependents))
        target = self.root / "addons" / name
        if target.is_symlink():
            raise ValueError("Refusing symlinked add-on directory")
        with tempfile.TemporaryDirectory(dir=self.root / "cache") as temp:
            backup = Path(temp) / "removed"
            if target.exists():
                target.rename(backup)
            installed.pop(name)
            try:
                write(self.metadata, installed)
            except Exception:
                if backup.exists():
                    backup.rename(target)
                raise
        return name
