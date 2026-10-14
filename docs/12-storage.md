> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 12. 저장공간

Android: filesDir 아래 home, rootfs, packages, addons, desktop, projects/python, projects/javascript, logs, repos, cache, wbs, config. 설정은 DataStore, 세션 및 작업 메타데이터는 Room입니다. Android 시스템 디렉터리에 쓰지 않습니다. 외부 저장소의 SAF import/export는 후속 기능입니다.

Windows: `%LOCALAPPDATA%\BlecaStudio\binux`. Linux/WSL: BINUX_HOME 또는 `~/.local/share/binux`. 프로젝트와 다운로드 캐시를 분리합니다. storage info는 실제 파일 크기와 남은 공간을 표시합니다. storage clean은 cache만 삭제합니다.

```bash
binux storage backup /absolute/backup.tar.gz
binux storage restore /absolute/backup.tar.gz
```

home/projects/repos의 일반 파일과 디렉터리를 보관하고 symlink/특수 파일은 제외합니다. WBS 개인키를 기본 백업에 포함하지 않습니다. restore는 기존 프로젝트를 덮어쓰지 않고 projects/restored-시간에 새 디렉터리를 만듭니다. 압축 해제는 traversal, 링크, 특수 파일, 과도한 팽창, 공간 부족을 검사합니다.

지금 작업 로그는 파일에 기록되며 자동 회전은 없습니다. 긴 서버 실행 시 storage info로 확인하고 종료된 로그를 사용자가 관리해야 합니다. 24시간 운영 제품 배포 전 로그 용량 정책을 추가해야 합니다.
