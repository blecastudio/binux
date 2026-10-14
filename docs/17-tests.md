# 17. 테스트 및 검증

Android 0.1.1에는 `:app:testDebugUnitTest`로 실행하는 입력 포커스/UTF-8 큐 전달 회귀 테스트 6개(API34/35 Robolectric)가 추가되었습니다. 실제 키보드 표시와 PTY 명령 실행을 검사하는 `TerminalInputDeviceTest` 3개는 ARM64 기기가 필요하며 컴파일만 했습니다. [검증 상세](ANDROID-0.1.1-INPUT-FIX.md).

**실행 결과: host 통합 33개 통과, emulator JUnit 138개 통과(실패/건너뜀 0), Android APK/test APK/린트 빌드 통과(린트 오류 0, 경고 8), APK 모든 native 파일 16 KiB 정렬 및 debug 서명 검사 통과, Windows win-x64 publish 통과, Python wheel 빌드·설치·CLI smoke 통과.** Debian RootFS에서 실제 Bash/한국어/apt-get --version을 PRoot 어댑터로 실행했습니다. 이는 Android PRoot 또는 apt 다운로드 설치 테스트는 아닙니다.

실행 로그는 로컬 artifacts/host-tests.log, android-build.log, windows-publish.log 및 Bash 빌드 로그에 있습니다. 검증표는 STATUS.md에 있습니다. 테스트를 컴파일한 것과 테스트를 실제 실행한 것을 구분합니다.

```bash
cmake -S native -B native/build/host
cmake --build native/build/host
bash scripts/test-host.sh
cd android
./gradlew :terminal-emulator:testDebugUnitTest lintDebug assembleDebug assembleDebugAndroidTest
python ../scripts/verify-apk.py app/build/outputs/apk/debug/app-debug.apk
```

호스트 통합 테스트는 실제 Bash PTY, 한국어, 파일 명령, exit status, Python HTTP/Node HTTP, CLI 종료 후 server 유지, stop/pause/resume, 자식 종료, 부족한 저장공간, opt-in restart 한도, SHA/hash/서명 실패, 압축 traversal/symlink, TLS 성공/실패, 폴더/명령 승인, 실제 파일 전송을 검사합니다. 네트워크는 loopback이며 외부 기기 연결 검증은 아닙니다.

ARM64 기기 연결 후만 다음을 실행하세요:

```bash
cd android
./gradlew connectedDebugAndroidTest
```

RuntimeDeviceTest는 APK Bash 실제 실행, 실제 PTY, 한글/파일 명령, real PID handshake를 검사합니다. **이 작업에는 연결된 Android 기기가 없어 실행하지 않았습니다.** Windows ConPTY GUI도 Windows OS가 없어 교차 빌드만 했습니다.

수동 백그라운드 검증: bg enable 및 사용자 알림/배터리 설정 후 `binux bg run sh -c 'while :; do date; sleep 2; done'`를 실행합니다. 앱을 최소화하고 화면을 끈 뒤 1/10/30분 이후 로그 시간과 실제 PID를 확인합니다. 알림 stop-all과 bg stop으로 작업이 끝나는지 확인합니다. 앱 강제 중지 후 열었을 때 이전 작업을 interrupted로 표시하고 사용자 요청 시 새 프로세스를 시작하는지 확인합니다. Doze 및 제조사 배터리 제한 상태도 각각 기록하세요.

Android Python/Node가 APK에 없으므로 Android Python HTTP 지속 검증은 아직 수행할 수 없습니다. 그 테스트를 호스트 테스트 결과로 대체하지 않습니다. Desktop/VNC 및 Chrome 실행, 실기기 간 WBS, 실제 ENOSPC는 별도의 검증이 필요합니다(호스트 부족 공간 테스트는 statvfs fixture).
