# 8. 명령어 관리

Android: `CommandRouter.kt`가 binux 전용 명령을 처리합니다. Bash 함수 binux가 APK `binuxctl`을 호출하며, argv JSON은 UID 검사된 abstract Unix socket으로 서비스에 전달합니다. 표준 명령의 출력은 이 router가 생성하지 않습니다.

호스트: `core/binux/cli.py`의 argparse 하위 명령은 각각 --help를 제공합니다. `binux help`, version/info/doctor, lang, runtime/package, addon, server, bg, storage, settings, desktop을 지원합니다. `wbs --help`는 별도 CLI입니다. Windows native는 help/version/info/doctor/lang/storage info/settings list를 제공하고 나머지는 WSL 호스트 도구에 연결해야 합니다.

| 호환 명령 | 실제 동작 |
|---|---|
| chdir | cd 내장 함수 |
| unmount | 실제 umount |
| shh | 실제 ssh, 없으면 command not found |
| ifconfip | 실제 ip address, OS 제한이 있으면 실제 실패 |
| getpid/getppid | 현재 Bash BASHPID/PPID |
| host bash | 지원되는 실제 Bash |
| fork command | Bash background job; jobs/wait 사용 |
| exec/wait | 원래 Bash 내장 명령 |

last/who/fsck/mount/chown 등은 Android 또는 선택한 Linux 배포판이 제공할 때만 사용할 수 있습니다. 없는 프로그램, SELinux, 파일 소유권, 실제 루트 권한 제한을 가짜 결과로 대체하지 않습니다. Linux host 명령은 DNS 도구가 존재할 경우 `host example.org` 원래 동작을 유지합니다.
