# 1.0.0 개발 프리뷰 — 구현과 실행 검증

검증 날짜: 2026-10-14. Android ARM64 기기는 연결되지 않았습니다.
Windows OS도 이 빌드 환경에는 없습니다. APK/EXE 빌드를 실기기 실행으로 소개하지 않습니다.

| 기능 | 구현 | 확인한 범위 |
|---|---|---|
| Native Bash/PTY, 한국어/영어, ANSI | 실제 APK 실행파일/PTY와 Compose 터미널 | NDK/APK/16 KiB ELF 빌드, 호스트 Bash/UTF-8 실행 |
| 입력/키보드/분할/종료 세션 | 실제 IME → 터미널 입력 경로 | API34/35 입력 회귀 테스트 6개 |
| Desktop:X11 설정 충돌 | 보호 메서드 reflection 제거, 공개 API 사용 | 기존 오류 재현 후 API34/35 모든 카테고리 테스트 통과 |
| 홈 프롬프트/설정 | canonical HOME, ~/ 표시; 툴바/전체화면 저장 | 구현/빌드; Android IME 실기기 검증 대기 |
| Debian/Ubuntu VM | APK의 QEMU, 별도 커널/디스크, 9p 공유 홈 | ARM64 NDK 엔진 빌드; 이미지 부팅 CI 결과는 Release와 연결 |
| pkg/apt/pip/npm | 게스트 apt, 사용자 venv, 실제 npm | 호스트 설치 도구/argv 전달 테스트; 게스트 부팅·설치 CI |
| VM SSH/PTY | 앱 소유 키, 게스트 공개 host key 고정, 바이너리 프레임 | 네이티브 프레임·UTF-8·정확한 인자·실제 exit code 테스트 |
| 원격 작업 중지 | 소유 프로세스 그룹/시작시간 검사, 취소 tombstone | 실제 sleep 종료, 선행 취소, Bash controlling PTY 테스트 |
| Android 백그라운드 | specialUse 서비스, 알림, 명시 종료, Room 복원 기록 | 빌드/린트; 화면 꺼짐/Doze/OEM 종료는 미검증 |
| 재부팅 자동 시작 | 명시 on 및 작업별 --autostart 선택; 기본 off | 구현/빌드; Android boot 실행 미검증 |
| 서버 | Python/Node 템플릿, 작업/로그/SSH loopback 포트 | 호스트 HTTP/Node 실행·중지 테스트; Android 실행 미검증 |
| 외부 공개 | 명시 --allow-network만 물리 LAN 연결 | 거부/허용 로직 구현; Android LAN 실기기 미검증 |
| Desktop/XFCE 설치 | apt TUI, 패키지 성공 후 기록, X11/VNC | 기존 Linux host XFCE/Xvfb 실행; Android X11 렌더링 미검증 |
| Desktop 오디오 | SSH PCM → Android AudioTrack, 선택형 | Kotlin 빌드; Android 스피커/지연/절전 미검증 |
| 공식 설치 스크립트 | 실제 BlecaStudio URL + APK 고정 SHA-256 | 출처 URL/파일 일치 확인, 변조는 오류 |
| 공식 add-on | Release JSON + SHA-256 + Ed25519, 안전한 압축 해제 | 서명/해시/오염/rollback/경로 침범 회귀 테스트 |
| WBS | TLS1.3/mTLS, 양쪽 승인, 공유 폴더/정확한 명령, 폐기 | 실제 연결/전송/해시/동기화/인증 실패/폐기 테스트 |
| Windows | ConPTY + WebView2/xterm, WSL 명령 전달 | win-x64 publish 성공; Windows OS 실행 미검증 |
| 저장공간/백업 | 실제 용량/캐시, 호스트 safe tar 새 폴더 복원 | 부족 공간/압축 침범 테스트; Android SAF 내보내기 미구현 |

현재 WBS sync는 단방향이며 파일 하나 16 MiB, 원격 명령 15초의 한도가 있습니다.
화면 공유·Windows 프로그램 Android 직접 실행·Ubuntu snap 자동 구성·Linux ARM64
Chrome 자동 설치는 제공하지 않습니다. 완전한 Phase 7 실기기 안정화가 끝났다고
표시하지 않습니다. 기기 검증을 거치기 전 1.0.0은 개발 프리뷰로 배포합니다.

이전 0.1.x 문서의 Android 실행 엔진 미포함 설명은 당시 상태입니다.
현재 사용법·구조·배포판 선택은 [1.0 안내](RUNTIME-1.0.md)를 기준으로 합니다.

호스트 테스트 43개, Android 앱 테스트 10개, X11 설정 테스트 2개,
터미널 에뮬레이터 테스트 138개가 통과했습니다. 게스트 Bash가 전경 PTY를 받기 전에
SIGTTIN으로 정지하는 경쟁 상태를 강제로 재현한 테스트도 통과합니다.
알림은 열기/모두 종료를 제공합니다. VM 연결 프로세스만 멈춰 게스트 작업까지
중지된 것으로 잘못 표시하는 일시중지 버튼은 제공하지 않습니다.
