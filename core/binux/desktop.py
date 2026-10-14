"""Opt-in host XFCE/TigerVNC installer. Android renderer integration is pending."""
import getpass
import os
import platform
import shutil
import subprocess
from pathlib import Path
from .state import base, read, write, message
from .runtime import DistributionRuntime

FEATURES = [
    ("chrome", "Google Chrome", []),
    ("files", "GUI file manager / 파일 관리자", ["thunar"]),
    ("editor", "GUI code editor / 코드 편집기 (Mousepad)", ["mousepad"]),
    ("wbs", "WBS Desktop Integration", []),
    ("audio", "Audio / 오디오 (PulseAudio)", ["pulseaudio"]),
    ("tools", "Developer tools / 개발 도구", ["git", "python3", "python3-pip", "nodejs", "npm"]),
]

def choices():
    selected = {"chrome", "files"}
    while True:
        print(message("binux Desktop 설치 — 번호로 선택 전환, Enter로 진행", "binux Desktop installer — toggle numbers; Enter to continue"))
        for number, (key, label, _) in enumerate(FEATURES, 1):
            print(f"{number}. [{'x' if key in selected else ' '}] {label}")
        answer = input("> ").strip()
        if not answer:
            return selected
        for token in answer.split():
            if token.isdigit() and 1 <= int(token) <= len(FEATURES):
                key = FEATURES[int(token) - 1][0]
                selected.symmetric_difference_update({key})

def chrome_compatibility(arch=None, runtime="proot"):
    arch = arch or platform.machine()
    if arch not in ("x86_64", "amd64"):
        return False, "Google Chrome Linux packages do not support this ARM64 architecture; choose Chromium or Android Chrome handoff"
    if runtime == "proot":
        return False, "Chrome sandbox capability cannot be established in PRoot/fake-root. No --no-sandbox fallback is permitted"
    return False, "Native Chrome installation adapter is not implemented for this runtime"

def capture(runtime, command):
    return subprocess.run(runtime.argv(command), capture_output=True, text=True, check=False)

def desktop_action(args):
    from .daemon import rpc
    statefile = base() / "config/desktop.json"
    state = read(statefile, {})
    if args.action == "status":
        if not state.get("installed"):
            return {"installed": False}
        jobs = rpc("list")
        current = next((j for j in reversed(jobs) if j.get("server") == "binux-desktop"), None)
        return {**state, "job": current, "vnc": "127.0.0.1:5901 (VNC password required)"}
    if args.action == "stop":
        current = next((j for j in reversed(rpc("list")) if j.get("server") == "binux-desktop"), None)
        if current is None:
            raise ValueError("Desktop has no running job")
        return rpc("stop", id=current["id"])
    runtime = DistributionRuntime(state.get("runtime", args.runtime))
    if args.action == "install":
        if state.get("installed"):
            raise ValueError("Desktop is already installed")
        selected = choices()
        if "wbs" in selected:
            raise ValueError("WBS Desktop Integration is not implemented; deselect this feature")
        if "chrome" in selected:
            arch = capture(runtime, ["dpkg", "--print-architecture"]).stdout.strip()
            _, reason = chrome_compatibility(arch)
            print(reason)
            print(message("Chrome을 제외하려면 1, Chromium 설치를 시도하려면 2 (샌드박스 유지), 취소는 Enter", "1: exclude browser; 2: install Chromium (sandbox preserved); Enter: cancel"))
            choice = input("> ").strip()
            if choice not in ("1", "2"):
                raise ValueError("Chrome unavailable; installation cancelled")
            selected.remove("chrome")
            if choice == "2":
                selected.add("chromium")
        password = getpass.getpass(message("VNC 비밀번호 (정확히 8자 ASCII): ", "VNC password (exactly 8 ASCII characters): "))
        if len(password) != 8 or not password.isascii() or not password.isprintable():
            raise ValueError("VNC authentication uses 8 printable ASCII characters inside loopback-only VNC; tunnel with TLS/SSH for remote access")
        packages = ["xfce4", "tigervnc-standalone-server", "dbus-x11"]
        for key, _, dependencies in FEATURES:
            if key in selected:
                packages.extend(dependencies)
        if "chromium" in selected:
            packages.append("chromium")
        existing = [package for package in packages if capture(runtime, ["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package]).stdout.startswith("ii")]
        if runtime.run(["apt-get", "-o", "APT::Update::Error-Mode=any", "update"]) != 0:
            raise ValueError("apt update failed")
        if runtime.run(["apt-get", "install", "-y", *packages]) != 0:
            raise ValueError("Desktop dependency installation failed; inspect apt output")
        folder = base() / "home/.vnc"
        folder.mkdir(exist_ok=True, mode=0o700)
        proc = subprocess.run(runtime.argv(["tigervncpasswd", "-f"]), input=password.encode() + b"\n", capture_output=True)
        if proc.returncode != 0 or not proc.stdout:
            raise ValueError("VNC password initialization failed")
        passfile = folder / "binux-passwd"
        passfile.write_bytes(proc.stdout)
        os.chmod(passfile, 0o600)
        startup = folder / "binux-xstartup"
        startup.write_text("#!/bin/sh\nunset SESSION_MANAGER DBUS_SESSION_BUS_ADDRESS\nexec dbus-launch --exit-with-session startxfce4\n")
        os.chmod(startup, 0o700)
        state = {"installed": True, "runtime": args.runtime, "features": sorted(selected), "owned_packages": [p for p in packages if p not in existing], "packages": packages, "browser": "chromium" if "chromium" in selected else "unavailable", "verified_gui_launch": False}
        write(statefile, state)
        return state
    if not state.get("installed"):
        raise ValueError("Desktop not installed")
    if args.action == "start":
        if any(j.get("server") == "binux-desktop" and j["state"] in ("running", "paused", "stopping") for j in rpc("list")):
            raise ValueError("Desktop is already running")
        command = runtime.argv(["tigervncserver", ":1", "-fg", "-localhost", "yes", "-SecurityTypes", "VncAuth", "-PasswordFile", "/root/.vnc/binux-passwd", "-xstartup", "/root/.vnc/binux-xstartup"])
        return rpc("run", argv=command, cwd=str(base() / "home"), server="binux-desktop")
    if args.action == "update":
        if runtime.run(["apt-get", "-o", "APT::Update::Error-Mode=any", "update"]) != 0 or runtime.run(["apt-get", "install", "--only-upgrade", "-y", *state["packages"]]) != 0:
            raise ValueError("Desktop update failed")
        return "Desktop packages updated"
    if args.action == "uninstall":
        from .cli import confirmed
        confirmed(args.yes, message("Desktop 소유 패키지를 제거합니까? 사용자 파일은 유지합니다.", "Remove Desktop-owned packages? User files are retained."))
        if any(j.get("server") == "binux-desktop" and j["state"] in ("running", "paused", "stopping") for j in rpc("list")):
            raise ValueError("Stop Desktop before uninstalling")
        if state["owned_packages"] and runtime.run(["apt-get", "remove", "-y", *state["owned_packages"]]) != 0:
            raise ValueError("Desktop removal failed")
        statefile.unlink()
        return "Desktop-owned packages removed; home retained"
    raise ValueError("Unsupported Desktop operation")
