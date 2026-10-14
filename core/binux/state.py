import json
import os
import tempfile
from pathlib import Path

DIRECTORIES = ("home", "rootfs", "packages", "addons", "desktop", "projects/python", "projects/javascript", "logs", "repos", "cache", "wbs", "config")

def base() -> Path:
    root = Path(os.environ.get("BINUX_HOME", Path.home() / ".local/share/binux")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix" and (root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077):
        raise ValueError("BINUX_HOME must be owned by the current user with mode 0700")
    for name in DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    return root

def read(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))

def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".binux-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def config():
    defaults = {"lang": os.environ.get("BINUX_LANG","ko"), "background": True, "autostart": False}
    if os.environ.get("BINUX_RUNTIME") == "linux-vm" or os.environ.get("BINUX_DEVICE_TARGET") == "windows":
        from .trust import ADDON_ED25519_KEY
        defaults.update(official_repo="blecastudio/binux", official_release="v1.0.0", addon_ed25519_key=ADDON_ED25519_KEY)
    return {**defaults, **read(base() / "config/settings.json", {})}

def set_config(key, value):
    values = config()
    values[key] = value
    write(base() / "config/settings.json", values)

def message(ko, en):
    return ko if config().get("lang", "ko") == "ko" else en
