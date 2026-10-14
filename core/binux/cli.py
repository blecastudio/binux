import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from . import __version__
from .state import base, config, set_config, read, write, message

def output(value):
    print(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))

def confirmed(yes, prompt):
    if not yes and input(prompt + " [yes]: ") != "yes":
        raise ValueError("Cancelled")

def parser():
    p = argparse.ArgumentParser(prog="binux", description="binux 0.1.0 / BlecaStudio — Linux/WSL host tools")
    s = p.add_subparsers(dest="group", required=True)
    for name in ("help", "version", "info", "doctor", "update"):
        s.add_parser(name)
    language = s.add_parser("lang").add_subparsers(dest="action", required=True)
    for name in ("list", "show"):
        language.add_parser(name)
    language.add_parser("set").add_argument("language", choices=("ko", "en"))
    bg = s.add_parser("bg").add_subparsers(dest="action", required=True)
    for name in ("status", "list", "enable", "disable", "pause", "resume", "shutdown"):
        bg.add_parser(name)
    run = bg.add_parser("run"); run.add_argument("--restart-on-failure", action="store_true"); run.add_argument("command", nargs=argparse.REMAINDER)
    for name in ("logs", "stop", "restart"):
        bg.add_parser(name).add_argument("job_id")
    bg.add_parser("autostart").add_argument("value", choices=("on", "off"))
    server = s.add_parser("server").add_subparsers(dest="action", required=True)
    server.add_parser("list")
    create = server.add_parser("create"); create.add_argument("name"); create.add_argument("--kind", choices=("python", "node"), default="python"); create.add_argument("--port", type=int, default=8000); create.add_argument("--listen", default="127.0.0.1"); create.add_argument("--allow-network", action="store_true"); create.add_argument("--restart-on-failure", action="store_true")
    register = server.add_parser("add"); register.add_argument("name"); register.add_argument("--cwd", required=True); register.add_argument("--port", type=int); register.add_argument("--restart-on-failure", action="store_true"); register.add_argument("command", nargs=argparse.REMAINDER)
    for name in ("start", "stop", "logs"):
        server.add_parser(name).add_argument("name")
    runtime = s.add_parser("runtime").add_subparsers(dest="action", required=True)
    runtime.add_parser("list")
    register = runtime.add_parser("register"); register.add_argument("name", choices=("debian", "ubuntu")); register.add_argument("rootfs"); register.add_argument("--proot", default="proot")
    run = runtime.add_parser("exec"); run.add_argument("name"); run.add_argument("command", nargs=argparse.REMAINDER)
    package = s.add_parser("package"); package.add_argument("--runtime", choices=("debian", "ubuntu")); package.add_argument("manager", choices=("apt", "pkg", "pip", "npm")); package.add_argument("arguments", nargs=argparse.REMAINDER)
    shell = s.add_parser("shell"); shell.add_argument("--runtime", choices=("debian", "ubuntu"))
    addon = s.add_parser("addon").add_subparsers(dest="action", required=True)
    for name in ("list", "update"):
        addon.add_parser(name)
    for name in ("search", "info", "install", "remove"):
        item = addon.add_parser(name); item.add_argument("name")
        if name == "remove":
            item.add_argument("--yes", action="store_true")
    desktop = s.add_parser("desktop"); desktop.add_argument("--runtime", choices=("debian", "ubuntu"), default="debian"); ds = desktop.add_subparsers(dest="action", required=True)
    for name in ("install", "start", "stop", "status", "update"):
        ds.add_parser(name)
    ds.add_parser("uninstall").add_argument("--yes", action="store_true")
    storage = s.add_parser("storage").add_subparsers(dest="action", required=True)
    for name in ("info", "clean"):
        storage.add_parser(name)
    storage.add_parser("backup").add_argument("archive")
    storage.add_parser("restore").add_argument("archive")
    settings = s.add_parser("settings").add_subparsers(dest="action", required=True)
    settings.add_parser("list")
    setting = settings.add_parser("set"); setting.add_argument("key", choices=("official_repo", "addon_ed25519_key", "font", "theme", "cursor")); setting.add_argument("value")
    return p

def server_action(args):
    from .daemon import rpc
    file = base() / "config/servers.json"
    records = read(file, {})
    name = getattr(args, "name", "")
    if name:
        import re
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", name):
            raise ValueError("Invalid server name")
    if args.action == "create":
        import ipaddress
        if not 1024 <= args.port <= 65535:
            raise ValueError("Port must be 1024..65535")
        if not ipaddress.ip_address(args.listen).is_loopback and not args.allow_network:
            raise ValueError("Publishing a server requires explicit --allow-network")
        project = base() / "projects" / ("python" if args.kind == "python" else "javascript") / name
        if name in records or project.exists():
            raise ValueError("Server or project already exists")
        project.mkdir()
        if args.kind == "python":
            (project / "server.py").write_text("from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nThreadingHTTPServer((" + repr(args.listen) + ", " + str(args.port) + "), SimpleHTTPRequestHandler).serve_forever()\n")
            command = [sys.executable, "-u", "server.py"]
        else:
            node = shutil.which("node")
            if not node:
                project.rmdir()
                raise ValueError("Node.js is not installed")
            (project / "server.js").write_text("const http = require('node:http');\nhttp.createServer((req,res)=>{res.end('binux server\\n')}).listen(" + str(args.port) + "," + json.dumps(args.listen) + ");\n")
            command = [node, "server.js"]
        records[name] = {"cwd": str(project), "argv": command, "port": args.port, "listen": args.listen, "restart_on_failure": args.restart_on_failure}
        write(file, records)
        return records[name]
    if args.action == "add":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command or not Path(args.cwd).is_dir():
            raise ValueError("Provide an existing cwd and an argv command after --")
        if name in records:
            raise ValueError("Server already registered")
        records[name] = {"cwd": str(Path(args.cwd).resolve()), "argv": command, "port": args.port, "listen": "command-controlled", "restart_on_failure": args.restart_on_failure}
        write(file, records)
        return records[name]
    jobs = rpc("list")
    if args.action == "list":
        return [{"name": name, **record, "state": next((j["state"] for j in reversed(jobs) if j["server"] == name), "stopped")} for name, record in records.items()]
    if name not in records:
        raise ValueError("Server not registered")
    matches = [j for j in jobs if j["server"] == name]
    if args.action == "start":
        if any(j["state"] in ("running", "paused", "stopping") for j in matches):
            raise ValueError("Server is already running")
        return rpc("run", argv=records[name]["argv"], cwd=records[name]["cwd"], server=name, restart_on_failure=records[name].get("restart_on_failure", False))
    if not matches:
        raise ValueError("Server has never started")
    return rpc("stop" if args.action == "stop" else "logs", id=matches[-1]["id"])

def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        group = args.group
        if group == "help":
            p.print_help(); return 0
        if group == "version":
            result = "binux " + __version__
        elif group == "info":
            result = {"version": __version__, "provider": "BlecaStudio", "runtime": "host-linux (not Android)", "kernel": platform.release(), "home": str(base()), "desktop": read(base() / "config/desktop.json", {}).get("installed", False)}
        elif group == "doctor":
            result = {"platform": platform.platform(), "arch": platform.machine(), "bash": shutil.which("bash"), "python": sys.version.split()[0], "node": shutil.which("node"), "git": shutil.which("git"), "ssh": shutil.which("ssh"), "proot": shutil.which("proot"), "free_bytes": shutil.disk_usage(base()).free, "root_privileges": "not provided by binux", "official_repo": config().get("official_repo", "not configured")}
        elif group == "update":
            raise ValueError("Automatic application update is unavailable; publish and configure a real BlecaStudio GitHub Release first")
        elif group == "lang":
            if args.action == "set":
                set_config("lang", args.language)
            result = {"ko": "한국어 / ko-KR", "en": "English / en-US"} if args.action == "list" else config().get("lang", "ko")
        elif group == "bg":
            from .daemon import rpc
            if args.action == "run":
                if not config().get("background", True):
                    raise ValueError("Enable background preference first: binux bg enable")
                command = args.command[1:] if args.command[:1] == ["--"] else args.command
                result = rpc("run", argv=command, cwd=os.getcwd(), restart_on_failure=args.restart_on_failure)
            elif args.action in ("list", "pause", "resume", "shutdown"):
                result = rpc(args.action)
            elif args.action == "status":
                result = {**rpc("ping"), "background": config().get("background", True), "autostart": config().get("autostart", False)}
            elif args.action in ("stop", "logs", "restart"):
                result = rpc(args.action, id=args.job_id)
            elif args.action == "autostart":
                if args.value == "on":
                    raise ValueError("Reboot autostart is not implemented; use an explicitly configured user service")
                set_config("autostart", False); result = "autostart: off"
            else:
                enabled = args.action == "enable"
                set_config("background", enabled)
                result = "background: " + str(enabled)
                if not enabled:
                    rpc("shutdown")
        elif group == "server":
            result = server_action(args)
        elif group == "runtime":
            from .runtime import DistributionRuntime
            if args.action == "list":
                result = read(base() / "config/runtimes.json", {})
            elif args.action == "register":
                result = DistributionRuntime.register(args.name, args.rootfs, args.proot)
            else:
                return DistributionRuntime(args.name).run(args.command)
        elif group == "package":
            from .runtime import native_packages
            return native_packages(args.manager, args.arguments, args.runtime)
        elif group == "shell":
            import pty
            from .runtime import DistributionRuntime
            if args.runtime:
                return DistributionRuntime(args.runtime).run(["/bin/bash", "-i"])
            rc = base() / "home/.binuxrc"
            rc.write_text("export HISTFILE=$HOME/.bash_history\nHISTSIZE=5000\nshopt -s histappend\nPS1='user@binux:\\w\\$ '\nchdir(){ cd \"$@\"; }\nunmount(){ umount \"$@\"; }\nshh(){ ssh \"$@\"; }\ngetpid(){ printf '%s\\n' \"$BASHPID\"; }\ngetppid(){ printf '%s\\n' \"$PPID\"; }\nifconfip(){ ip address; }\nhost(){ if [[ $1 == bash ]]; then shift; command bash \"$@\"; else command host \"$@\"; fi; }\nfork(){ if (($#)); then \"$@\" & else printf 'fork <command> [args...]\\n' >&2; return 2; fi; }\nprintf 'binux v0.1.0 / BlecaStudio\\nRuntime: Host Bash\\nDesktop: optional\\nType binux help\\n'\n")
            os.environ["HOME"] = str(base() / "home")
            return os.waitstatus_to_exitcode(pty.spawn([shutil.which("bash") or "/bin/bash", "--rcfile", str(rc), "-i"]))
        elif group == "addon":
            from .packages import Addons
            addons = Addons()
            if args.action == "list":
                result = addons.installed()
            elif args.action == "remove":
                confirmed(args.yes, message("보조 기능을 삭제합니까?", "Remove add-on?")); result = addons.remove(args.name)
            elif args.action in ("search", "info"):
                catalog = addons.catalog()
                result = [item for item in catalog if args.name in item["name"]] if args.action == "search" else next(item for item in catalog if item["name"] == args.name)
            else:
                if not config().get("addon_ed25519_key"):
                    print(message("서명 키가 설정되지 않았습니다. HTTPS 및 SHA-256 무결성만 확인합니다. 설치 스크립트를 자동 실행하지 않습니다.", "No signing key configured: verifying HTTPS and SHA-256 integrity only. Install hooks are never executed."), file=sys.stderr)
                progress = lambda done, total: print(f"\r{done}/{total or '?'} bytes", end="", file=sys.stderr, flush=True)
                result = addons.install(args.name, progress=progress) if args.action == "install" else [addons.install(name, progress=progress) for name in addons.installed()]
        elif group == "desktop":
            from .desktop import desktop_action
            result = desktop_action(args)
        elif group == "storage":
            if args.action == "info":
                from .state import DIRECTORIES
                result = {name: sum(f.stat().st_size for f in (base() / name).rglob("*") if f.is_file() and not f.is_symlink()) for name in DIRECTORIES}
                result["free_bytes"] = shutil.disk_usage(base()).free
            elif args.action == "clean":
                cache = base() / "cache"
                for child in cache.iterdir():
                    if child.is_dir() and not child.is_symlink():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                result = "Download cache cleared"
            elif args.action == "backup":
                archive = Path(args.archive).resolve()
                if archive.is_relative_to(base()):
                    raise ValueError("Write the backup outside binux data to avoid recursion")
                if archive.exists():
                    raise ValueError("Backup destination exists; refusing overwrite")
                with tarfile.open(archive, "x:gz") as tar:
                    for name in ("home", "projects", "repos"):
                        tar.add(base() / name, arcname=name, filter=lambda info: info if info.isdir() or info.isfile() else None)
                result = str(archive)
            else:
                from .packages import safe_extract
                import tempfile
                with tempfile.TemporaryDirectory(dir=base() / "cache") as temporary:
                    target = Path(temporary)
                    safe_extract(args.archive, target)
                    stamp = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
                    destination = base() / "projects" / ("restored-" + stamp)
                    if destination.exists():
                        raise ValueError("Restore target exists")
                    target.rename(destination)
                result = str(destination)  # Restore into a new directory, never overwrite projects.
        elif group == "settings":
            if args.action == "set":
                if args.key == "official_repo":
                    import re
                    if not re.fullmatch(r"BlecaStudio/[A-Za-z0-9_.-]+", args.value, re.IGNORECASE):
                        raise ValueError("Expected a real BlecaStudio repository")
                    from .packages import fetch
                    fetch("https://api.github.com/repos/" + args.value, base() / "cache/repo-verification.json", 1024 * 1024)
                set_config(args.key, args.value)
            result = config()
        else:
            raise ValueError("Unsupported command")
        output(result)
        return 0
    except (OSError, ValueError, KeyError, StopIteration, RuntimeError) as error:
        print(message("오류: ", "Error: ") + str(error), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
