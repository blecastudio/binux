# 17. 테스트 및 증거

```bash
cmake -S native -B native/build/host
cmake --build native/build/host
bash scripts/test-host.sh
cd android
./gradlew assembleDebug assembleDebugAndroidTest lintDebug :app:testDebugUnitTest :desktop-x11:testDebugUnitTest :terminal-emulator:testDebugUnitTest
```

호스트 테스트는 실제 Bash/PTY, Python/Node HTTP 서버, 종료/재시작/자식 프로세스,
네이티브 소켓 프레임/UTF-8/exit status, 게스트 작업 취소/controlling PTY, 실제 백업 복원,
WBS TLS 인증·파일·해시·폐기·포트 연결, add-on 해시/서명/안전한 추출을 검사합니다.

Android 입력은 API34/35에서 실제 Java IME → 세션 큐 경계를 테스트합니다. JNI fork는
Robolectric이 실행하지 않습니다. X11 설정은 기존 보호 메서드 reflection 충돌을 먼저
재현했으며 수정 후 API34/35의 모든 설정 카테고리가 열립니다.

```bash
python3 scripts/verify-apk.py android/app/build/outputs/apk/debug/app-debug.apk
python3 scripts/verify-apk.py --kind x11 android/desktop-x11/build/outputs/apk/debug/desktop-x11-debug.apk
python3 scripts/test-runtime-image.py debian RUNTIME_OUTPUT
python3 scripts/test-runtime-image.py ubuntu RUNTIME_OUTPUT
```

ELF 검사는 ABI/Android 링커/의존 라이브러리/16 KiB 정렬을 검사합니다. 이미지 검사는
실제 ARM64 커널을 부팅해 host key 고정 SSH·다른 키 거부·공유 홈·apt/pkg/pip/npm을
검사합니다. 실패한 이미지는 설치 가능한 Release로 발행하지 않습니다. 부팅 로그와
이미지 캐시는 CI에 보존해 실패 원인을 다시 검사할 수 있습니다.

2026-10-15 [통합 실행](https://github.com/blecastudio/binux/actions/runs/38683043024)에서
APK와 같은 QEMU 9.2.4 소스로 Debian/Ubuntu ARM64를 모두 부팅했습니다.
두 배포판의 pkg/apt·pip·npm/Express 설치, Flask/FastAPI/Express HTTP 응답과 프로세스
종료, XFCE/xfwm4·인증된 Xvfb 실행 및 설치기 재실행의 패키지 소유권 유지가 통과했습니다.
Ubuntu 공유 홈에서 npm의 JSON 파일이 잘리던 회귀는 배포판별 ext4 npm 캐시와
libuv의 io_uring 비활성화 후 새 설치에서 재현되지 않았습니다. Android 실기기 결과는 아닙니다.

[Chrome 실행](https://github.com/blecastudio/binux/actions/runs/38665106962)도 같은 엔진으로
두 ARM64 배포판에서 공식 apt 설치와 샌드박스를 켠 headless DOM 검사에 통과했습니다.

현재 호스트 44개, 앱 10개, X11 설정 2개, 에뮬레이터 138개 테스트가 통과합니다.
PTY 회귀 테스트는 Bash의 SIGTTIN 정지를 실제로 유도한 뒤 전경 소유권 이전과
SIGCONT로 입력·명령 실행·exit status가 복구되는지 검사합니다.

Android ARM64 실제 기기가 연결된 경우에만 `./gradlew connectedDebugAndroidTest`를
실행하세요. Android12·13·14·15·16별 IME/한글 조합, X11 설정/표시/터치, 화면 꺼짐/Doze,
FGS 알림/사용자 종료, OS 종료 후 interrupted 복원, 명시적 부팅 재시작, PCM 출력,
물리 LAN WBS/승인 실패, 저장공간 부족을 실기기 표에 기록해야 합니다.
현재 이 환경에는 Android 실기기 및 Windows OS가 없어 이 결과는 미검증입니다.
