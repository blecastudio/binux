# 구현 및 검증 상태 — 0.1.0 experimental

Android 0.1.1 입력 수정: API34/35 Robolectric 입력 회귀 테스트 6개 및 APK/린트/서명 검사가 통과했습니다. 실제 기기 IME 테스트는 실행하지 않았습니다. [수정 상세](ANDROID-0.1.1-INPUT-FIX.md). 아래 표는 초기 전체 기능 범위입니다.

검증 날짜: 2026-10-14 (한국 사용자 기준). 이 표의 **구현/빌드**와 **실제 실행 검증**은 별개입니다. 모든 Phase가 완료된 제품이라고 소개하지 않습니다.

| 요구 기능 | 구현 범위 | 실제 검증 |
|---|---|---|
| Android 첫 실행 언어 선택/CLI | Compose → service → bundled ARM64 Bash/PTY | APK 빌드, 기기 미검증 |
| Bash/파일 명령/UTF-8/ANSI | Android 코드, 호스트 PTY | 호스트 실제 Bash/파일/한글/ANSI; Android 테스트 APK만 빌드 |
| 자동완성/기록/IME/클립보드 | 실제 Bash + upstream TerminalView | emulator 단위 테스트; Android 조합 입력 미검증 |
| Android 탭/분할/보조키/검색 | 실제 세션 연결; 기록 검색 | 빌드만 검증 |
| Windows 탭/분할/ConPTY | WinForms + local xterm/WebView2 | win-x64 실행 파일 교차 빌드; Windows 실행 미검증 |
| Native Bash ABI/링커 | Bionic ARM64 PIE / linker64 | 교차 빌드, APK 포함/ELF/16 KiB 정렬 검사 |
| Python/Node.js | Linux/WSL host runtime | 실제 스크립트/HTTP 서버 통과; Android 미포함 |
| Git/SSH/Curl | 호스트 설치 프로그램, 배포판 apt | 연결/clone/SSH 종단 테스트 미실행; Android 미포함 |
| Debian/Ubuntu RootFS | 기존 RootFS 등록 및 PRoot exec adapter | 호스트 기존 Debian RootFS에서 Bash/한글/apt 버전 실행; 자동 설치 및 Android 통합 없음 |
| apt/pkg/pip/npm | 호스트/선택 배포판 전달; Android pkg/apt 실패 설명 | 일반 패키지 실제 다운로드 설치는 별도 검증; binux wheel 설치 확인 |
| Background Android service | specialUse, notification, UI와 프로세스 수명 분리 | Manifest/빌드/lint; 최소화·화면 꺼짐 실기기 미검증 |
| 실제 BG job/PID/log/stop | Android native setsid/PID handshake, 호스트 supervisor | host 실행/CLI 종료 후 유지/종료/자식 종료/pause-resume 통과 |
| CPU/RAM | 실제 부모 프로세스 RSS/CPU ticks, unavailable 처리 | host 실제 /proc 읽기; Android/OEM 접근 미검증 |
| 실패 감지/재시작 | 명시적 옵션, 최대 3회, 수동 종료 시 중단 | host 재시작 제한 테스트 통과; Android 미검증 |
| OS 종료 복원 | Room/host metadata interrupted; 사용자 요청 시 새 실행 | host stale PID 테스트; Android 강제 종료 미검증 |
| 재부팅 자동 시작 | off만 지원, on은 실패 | boot receiver/자동 재실행 없음 |
| 서버 생성/관리 | host Python/node 템플릿, 실제 argv 등록 및 로그 | 실제 localhost HTTP/Node 서버 및 종료 통과 |
| 서버 외부 공개 | 템플릿 기본 loopback, 명시 --allow-network | 미승인 공개 거부 테스트 통과 |
| 자동 포트 탐지/내부 preview | 미구현; 등록 포트/주소 안내만 | 미실행 |
| 저장공간 확인/캐시 정리 | 실제 파일 크기/free space | host 실행; 부족 공간 fixture 거부 통과 |
| 백업/복원 | host safe tar, 새 폴더 복원 | 코드 구현; 전체 백업 왕복 별도 검증 필요 |
| Android 사용자 export/import | 앱 내부 저장소만 | SAF/외부 export/import 미구현 |
| 공식 add-on manifest/hash/signature | host GitHub Release installer | mock asset 실제 파일/서명/오염/traversal/rollback 테스트 통과 |
| 공식 GitHub 저장소 | blecastudio/binux 존재 확인 | public repository API 및 git remote 접근 확인 |
| 공식 Release/installer URL | 아직 미발행 | 설치 불가로 반환; 가짜 URL 없음 |
| Desktop TUI/XFCE/VNC | host distro installer, 비밀번호/loopback | 설치기 코드; GUI 설치/기동 미검증 |
| Chrome 호환성 | ARM64/PRoot 거부, 사용자 대안 선택 | ARM64/샌드박스 거부 unit tests |
| Chrome 자동 설치 | 호환된 native adapter 아직 없음 | 미지원 |
| Android GUI/touch/audio | 미통합 | 미지원 |
| WBS 인증/기기 정보 | host prototype, TLS1.3/mTLS/양방향 지문 승인 | loopback 두 identity 실제 통신 통과 |
| WBS 파일/폴더 | 허용 폴더, SHA-256, atomic upload, one-way sync | 파일 전송/동기화/symlink/traversal 차단 통과 |
| WBS remote commands | 정확한 argv 승인, timeout, shell=False | 승인 명령 실행/미승인 차단 통과 |
| WBS 인증키 폐기 | 다음 요청부터 차단 | 서버 재시작 없이 폐기 차단 통과 |
| 실제 Windows↔Android WBS | 앱 transport 미통합 | 미검증/미완료 |
| WBS 포트 터널/화면 공유 | 미구현, unavailable | 미지원 |
| 한국어/영어 | Android resources, 주요 CLI 메시지, Windows 설정 | host 한국어 입출력; UI/상세 문구 일부 번역 미완료 |
| 보안 정책/라이선스 | APK-bundled code, private storage, 인증, 고지 | 정적/host 검사; Play 심사/실기기 보안 검증 없음 |

## Android 12–16 검토 및 실기기 테스트 계획

| OS | 고려한 차이 | 반드시 실행할 테스트 |
|---|---|---|
| Android 12 / API31–32 | background FGS 시작 제한 및 child process 정책 | UI에서 시작, 최소화, 자식 작업 중단 감지 |
| Android 13 / API33 | notification permission, 사용자의 활성 앱 중지 | 알림 거부/허용, Task Manager stop, 복원 상태 |
| Android 14 / API34 | type별 FGS 권한/선언, specialUse 설명 | type 권한/시작 오류, 명시 stop-all |
| Android 15 / API35 | dataSync 실행시간/boot 제한; 사용 유형과 구분 | Doze/장시간 작업, 16 KiB 기기, 화면 꺼짐 |
| Android 16 / API36 | all-app 정책과 target36 변경 구분, job quota/기기 관리 | target35 앱 실행 및 target36 업그레이드, OEM 종료/대화면 |

현재 APK는 target35입니다. specialUse가 모든 제한을 제거하지 않습니다. JobScheduler/WorkManager로 지속 셸을 실행하지 않으며 Android16에서 FGS가 JobScheduler quota를 면제한다는 가정을 하지 않습니다. 배터리 예외, 24시간 실행, Play 승인, 루트 권한을 보장하지 않습니다. API12–16 실제 기기/에뮬레이터는 현재 연결되어 있지 않아 모두 테스트 대기입니다.

## 다음 단계의 완료 조건

1. Android ARM64 실제 기기에서 RuntimeDeviceTest와 최소화/화면 꺼짐/중지/복원 확인.
2. 정책을 준수하는 Python/Node/Git/SSH 패키징 및 Android runtime adapter 구현/기기 검증.
3. Android PRoot 실행 모델 검증 뒤 Debian/Ubuntu 자동 설치기 추가. 현재 glibc RootFS를 실행 가능하다고 광고하지 않음.
4. WBS native Android/Windows transport, 사용자 승인 UI와 해당 플랫폼의 안전한 파일 접근 구현 후 실제 기기 간 전송 확인.
5. 실제 공식 Release/서명키를 배포하고 add-on real asset 설치를 확인.
6. 선택형 GUI renderer/audio/Chrome 호환 adapter를 구현하고 GUI/배터리/저장공간 검증.

이 구현을 전체 목표의 완료판으로 배포하지 말고 Phase 1과 host 검증 기반으로 개발을 이어가세요.

## 0.1.2 / Desktop:X11 0.1.0

별도 X11 APK의 실제 X.Org 서버·JNI 렌더러, own-package Service, loopback 및 쿠키 인증, 같은 서명키 Provider, 설정 복구 버튼을 구현하고 ARM64 빌드했습니다. binux 툴바/보조 키/전체화면/화면 유지 설정, 로고, HTTPS 스크립트 어댑터와 Desktop 설치기 작업 명령을 추가했습니다. Android 배포판 실행 엔진 부재는 명시적 실패이며 XFCE 설치 성공을 반환하지 않습니다. Linux/Android 결과와 남은 작업은 [Desktop/X11 안내](DESKTOP-X11.md)를 참고하세요. Android X11 실기기 테스트는 컴파일만 했습니다.
