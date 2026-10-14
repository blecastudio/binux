# Android 0.1.1 — 터미널 입력 불가 수정

버전 코드 2, 앱 패키지 `studio.bleca.binux`. Windows 및 Linux 호스트 도구 버전은 0.1.0으로 유지합니다.

## 원인 및 수정

- Compose에서 만든 native TerminalView에 touch focus 설정이 없어서 requestFocus가 실패하고 IME 입력 대상이 되지 못했습니다. TerminalInput.prepare로 focusable/focusableInTouchMode와 고유 View ID를 지정했습니다.
- 화면 터치 시 활성 패널을 먼저 갱신하고 Android 입력 포커스를 요청합니다. 뷰가 붙고 포커스가 확보된 뒤 키보드를 표시합니다. 이미 활성화된 editor는 불필요하게 restartInput하지 않아 한글 조합을 유지합니다.
- 하단 `키보드 / Keyboard` 버튼을 추가했습니다. 새 패널을 만들 때 다른 패널이 자동으로 포커스를 빼앗지 않도록 선택된 패널만 포커스합니다.
- Ctrl/Alt/Tab/방향키/붙여넣기/중지는 마지막으로 터치하거나 포커스한 분할 패널을 대상으로 합니다.
- 종료된 세션은 즉시 상태 표시를 갱신하고 입력 포커스와 보조 키를 비활성화합니다. 새 세션 버튼을 제공하며 새로 만들거나 복원한 셸을 선택합니다. 앱 재진입 시 실행 중인 세션 또는 새 셸을 선택합니다.
- 제거한 native view는 등록 목록에서도 정리해 이전 뷰가 입력 대상에 남지 않도록 했습니다.

화면의 `signal 9`는 해당 프로세스가 이미 종료되었다는 의미입니다. 이 패치는 종료된 프로세스를 실행 중인 것으로 표시하거나 되살리지 않습니다. signal 9의 OS/사용자/배경 실행 설정 원인을 화면만으로 확정하지 않습니다. 기존 백그라운드 허용 정책은 유지합니다.

## 검증

`TerminalInputTest`를 Robolectric API34/API35에서 실행했고 총 6개가 통과했습니다. Android native View 포커스, IME의 한글/명령 UTF-8 바이트와 Enter의 CR 변환, 두 패널 간 포커스 전환 및 입력 큐 분리, 종료 세션 입력 거부를 검사했습니다. 테스트에서 JNI 프로세스 경계는 대체하며 실제 Android 기기 실행 결과로 소개하지 않습니다.

```bash
cd android
./gradlew :app:testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug
```

APK 및 테스트 APK 빌드, 린트 오류 0, 모든 native 파일 16 KiB 정렬, APK 서명 검사가 통과했습니다. 0.1.0 APK와 서명 인증서가 동일하고 versionCode를 높여 기존 설치를 업데이트할 수 있습니다. 개인키나 앱 데이터 변경 없이 빌드했습니다.

`TerminalInputDeviceTest`에는 실제 MainActivity → keyboard → PTY → Bash 명령 실행, 분할 패널 터치/Tab 입력, 프로세스 종료 후 새 셸 입력의 테스트 3개를 추가했습니다. ARM64 테스트 기기가 연결되지 않아 이 테스트는 컴파일만 했습니다.

```bash
cd android
./gradlew connectedDebugAndroidTest
```

## 설치 후 확인

1. `binux-0.1.1-android-arm64-debug.apk`를 기존 앱 위에 업데이트 설치합니다.
2. 앱을 열고 터미널 화면을 누르거나 하단 `키보드` 버튼을 누릅니다.
3. `pwd`, `ls`, `printf '비눅스\\n'`, `binux version`을 입력하고 Enter를 누릅니다.
4. 분할 화면에서도 누른 패널에 입력되는지 확인합니다. 종료 안내가 보이면 `새 세션`을 누릅니다.

실제 휴대폰의 키보드 표시 및 삼성/Gboard 조합 입력은 이 환경에서 직접 확인하지 못했습니다. 기존 전체 구현/미구현 범위는 STATUS.md를 참고하세요.
