import os
import platform
import shutil
import subprocess
from pathlib import Path
from .state import base, read, write

class DistributionRuntime:
    def __init__(self, name):
        self.name = name
        values = read(base() / "config/runtimes.json", {})
        if name not in values:
            raise ValueError("Distribution is not registered; use binux runtime register")
        self.root = Path(values[name]["root"]).resolve(strict=True)
        self.proot = values[name]["proot"]

    def argv(self, command):
        if not (self.root / "bin/bash").exists():
            raise ValueError("RootFS has no Bash")
        return [self.proot, "-0", "-r", str(self.root), "-b", "/dev", "-b", "/proc", "-b", "/sys", "-b", "/etc/resolv.conf:/etc/resolv.conf", "-b", f'{base() / "home"}:/root', "-w", "/root", "/usr/bin/env", "HOME=/root", "PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", "LANG=C.UTF-8", *command]

    def run(self, command):
        return subprocess.run(self.argv(command), check=False).returncode

    @staticmethod
    def register(name, root, proot):
        if name not in ("debian", "ubuntu"):
            raise ValueError("Supported distribution names: debian, ubuntu")
        path = Path(root).expanduser().resolve(strict=True)
        if not (path / "etc/os-release").exists() or not (path / "bin/bash").exists():
            raise ValueError("RootFS lacks os-release or Bash")
        text = (path / "etc/os-release").read_text()
        distro_id = next((line.removeprefix("ID=").strip('"') for line in text.splitlines() if line.startswith("ID=")), "")
        if distro_id != name:
            raise ValueError(f"RootFS ID {distro_id!r} does not match {name}")
        executable = shutil.which(proot)
        if not executable:
            raise ValueError("PRoot executable not found")
        settings = read(base() / "config/runtimes.json", {})
        settings[name] = {"root": str(path), "proot": executable, "architecture": platform.machine()}
        write(base() / "config/runtimes.json", settings)
        return settings[name]

def native_packages(manager, args, distribution=None):
    if manager == "apt":
        if not distribution:
            raise ValueError("apt belongs to Debian/Ubuntu; provide --runtime")
        return DistributionRuntime(distribution).run(["apt-get", *args])
    if manager == "pkg":
        raise ValueError("Native pkg repository is not configured; downloaded APK-private native executables are not supported on Android target 35")
    executable = shutil.which("python3" if manager == "pip" else "npm")
    if not executable:
        raise ValueError(f"{manager} runtime is not installed")
    command = [executable, "-m", "pip", *args] if manager == "pip" else [executable, *args]
    if distribution:
        command = ["python3", "-m", "pip", *args] if manager == "pip" else ["npm", *args]
        return DistributionRuntime(distribution).run(command)
    return subprocess.run(command, check=False).returncode
