> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 6. PTY와 실제 셸

`TerminalSession.java` → `JNI.java` → `termux.c`에서 `/dev/ptmx`, grantpt/unlockpt, fork, setsid, slave TTY, dup2, execvp, waitpid를 사용합니다. 앱 출력이 아니라 자식 Bash의 stdout/stderr를 읽습니다. 터미널 크기 변경은 ioctl(TIOCSWINSZ)로 전달합니다.

binux의 변경은 비공개 FileDescriptor 필드 접근을 공개 ParcelFileDescriptor.fromFd API로 교체하고, 입력/출력 FD를 각각 소유하게 한 것입니다. fork/PTY 실패는 예외, exec 실패는 실제 errno와 종료 상태로 전달합니다. 실패한 cwd로 명령을 실행하지 않습니다.

Native launcher `job.c`는 setsid 후 PID 파일을 통해 실제 PID를 전달하고 exec합니다. Android Java Process에는 지원되는 pid API가 없으므로 비공개 필드 리플렉션을 사용하지 않습니다. `process.c`는 프로세스 시작 tick을 확인하며 같은 session ID의 자식을 종료합니다. 사용자 프로그램이 의도적으로 새로운 SID로 분리하는 경우 완전한 프로세스 격리/컨테이너가 보장되지는 않습니다.

`host bash`는 지원되는 binux Bash를 실행합니다. `exec`, `wait`는 Bash 원래 내장 기능이고, `fork <argv...>`는 Bash background job을 시작하는 명시적 호환 함수입니다. 원시 시스템 호출을 흉내 내는 출력은 없습니다.
