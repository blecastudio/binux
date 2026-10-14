> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 10. SessionManager / ProcessManager

SessionManager는 TerminalSession을 Activity와 독립적으로 보유하고 5초마다 Room에 cwd, 실제 PID, 상태, 최대 128 KiB 텍스트 기록을 checkpoint합니다. 재시작 시 running 상태를 interrupted와 PID=-1로 바꿉니다. PID만 보고 다른 프로세스에 재연결하거나 종료하지 않습니다.

BackgroundProcessManager는 독립 세션에 속한 실제 프로세스, argv, 작업 디렉터리, PID, start tick, 경과 시간, 종료 코드, 파일 로그를 추적합니다. `/proc/<pid>/status` RSS와 stat CPU tick이 읽히면 실제 값을 보여주며 읽을 수 없으면 unavailable입니다. 이 값은 부모 프로세스 지표이며 전체 자식 트리의 합산 사용량/CPU 백분율은 아닙니다.

Android `bg run --restart-on-failure`와 server restart-policy는 현재 서비스 수명 안에서 최대 3회 재시작합니다. 수동 종료하면 재시작하지 않습니다. OS/앱 프로세스 종료 및 재부팅 후 자동 재실행은 없습니다. `bg autostart on`은 명확히 실패합니다. 로그는 앱 전용 저장소에 있으며 사용자 프로그램 출력이 그대로 기록되므로 비밀값을 출력하는 명령은 직접 주의해야 합니다. WBS 인증키는 로그에 기록하지 않습니다.

호스트 supervisor는 0700 데이터 디렉터리와 0600 Unix socket, Linux SO_PEERCRED로 같은 UID만 허용합니다. Popen의 실제 소유 프로세스를 신호 대상으로 사용하고 PID 재사용을 시작 tick으로 확인합니다. daemon 중단 뒤 저장 상태는 interrupted로 바꾸고 opt-in 재시작 정책도 자동 복구하지 않습니다.
