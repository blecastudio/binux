> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 실제 파일 경로 및 내용 안내

각 링크는 해당 파일 전체 내용을 가리킵니다. Android 0.1.1 수정 소스 ZIP에도 같은 경로와 내용이 있습니다. build/cache 및 사용자 데이터는 제외합니다.

## Android

- [android/app/build.gradle](../android/app/build.gradle)
- [android/app/schemas/studio.bleca.binux.BinuxDatabase/1.json](../android/app/schemas/studio.bleca.binux.BinuxDatabase/1.json)
- [android/app/src/androidTest/java/studio/bleca/binux/RuntimeDeviceTest.kt](../android/app/src/androidTest/java/studio/bleca/binux/RuntimeDeviceTest.kt)
- [android/app/src/androidTest/java/studio/bleca/binux/TerminalInputDeviceTest.kt](../android/app/src/androidTest/java/studio/bleca/binux/TerminalInputDeviceTest.kt)
- [android/app/src/main/AndroidManifest.xml](../android/app/src/main/AndroidManifest.xml)
- [android/app/src/main/assets/binuxrc](../android/app/src/main/assets/binuxrc)
- [android/app/src/main/java/studio/bleca/binux/BackgroundProcessManager.kt](../android/app/src/main/java/studio/bleca/binux/BackgroundProcessManager.kt)
- [android/app/src/main/java/studio/bleca/binux/BinuxRuntimeService.kt](../android/app/src/main/java/studio/bleca/binux/BinuxRuntimeService.kt)
- [android/app/src/main/java/studio/bleca/binux/CommandRouter.kt](../android/app/src/main/java/studio/bleca/binux/CommandRouter.kt)
- [android/app/src/main/java/studio/bleca/binux/Database.kt](../android/app/src/main/java/studio/bleca/binux/Database.kt)
- [android/app/src/main/java/studio/bleca/binux/MainActivity.kt](../android/app/src/main/java/studio/bleca/binux/MainActivity.kt)
- [android/app/src/main/java/studio/bleca/binux/PreferenceKeys.java](../android/app/src/main/java/studio/bleca/binux/PreferenceKeys.java)
- [android/app/src/main/java/studio/bleca/binux/Runtime.kt](../android/app/src/main/java/studio/bleca/binux/Runtime.kt)
- [android/app/src/main/java/studio/bleca/binux/ServerManager.kt](../android/app/src/main/java/studio/bleca/binux/ServerManager.kt)
- [android/app/src/main/java/studio/bleca/binux/SessionManager.kt](../android/app/src/main/java/studio/bleca/binux/SessionManager.kt)
- [android/app/src/main/java/studio/bleca/binux/Settings.kt](../android/app/src/main/java/studio/bleca/binux/Settings.kt)
- [android/app/src/main/java/studio/bleca/binux/TerminalInput.kt](../android/app/src/main/java/studio/bleca/binux/TerminalInput.kt)
- [android/app/src/main/res/values-ko/strings.xml](../android/app/src/main/res/values-ko/strings.xml)
- [android/app/src/main/res/values/strings.xml](../android/app/src/main/res/values/strings.xml)
- [android/app/src/test/java/studio/bleca/binux/TerminalInputTest.kt](../android/app/src/test/java/studio/bleca/binux/TerminalInputTest.kt)
- [android/build.gradle](../android/build.gradle)
- [android/gradle.properties](../android/gradle.properties)
- [android/gradle/wrapper/gradle-wrapper.jar](../android/gradle/wrapper/gradle-wrapper.jar)
- [android/gradle/wrapper/gradle-wrapper.properties](../android/gradle/wrapper/gradle-wrapper.properties)
- [android/gradlew](../android/gradlew)
- [android/gradlew.bat](../android/gradlew.bat)
- [android/settings.gradle](../android/settings.gradle)

## 네이티브 실행 계층

- [native/CMakeLists.txt](../native/CMakeLists.txt)
- [native/ctl.c](../native/ctl.c)
- [native/job.c](../native/job.c)
- [native/process.c](../native/process.c)

## 공통 호스트 도구

- [core/binux/__init__.py](../core/binux/__init__.py)
- [core/binux/__main__.py](../core/binux/__main__.py)
- [core/binux/cli.py](../core/binux/cli.py)
- [core/binux/daemon.py](../core/binux/daemon.py)
- [core/binux/desktop.py](../core/binux/desktop.py)
- [core/binux/packages.py](../core/binux/packages.py)
- [core/binux/runtime.py](../core/binux/runtime.py)
- [core/binux/state.py](../core/binux/state.py)
- [core/binux/wbs.py](../core/binux/wbs.py)

## Windows

- [windows/AppSettings.cs](../windows/AppSettings.cs)
- [windows/Binux.Windows.csproj](../windows/Binux.Windows.csproj)
- [windows/ConPty.cs](../windows/ConPty.cs)
- [windows/NativeCli.cs](../windows/NativeCli.cs)
- [windows/Program.cs](../windows/Program.cs)
- [windows/TerminalForm.cs](../windows/TerminalForm.cs)
- [windows/assets/FIT-LICENSE.txt](../windows/assets/FIT-LICENSE.txt)
- [windows/assets/SEARCH-LICENSE.txt](../windows/assets/SEARCH-LICENSE.txt)
- [windows/assets/XTERM-LICENSE.txt](../windows/assets/XTERM-LICENSE.txt)
- [windows/assets/addon-fit.js](../windows/assets/addon-fit.js)
- [windows/assets/addon-search.js](../windows/assets/addon-search.js)
- [windows/assets/terminal.html](../windows/assets/terminal.html)
- [windows/assets/terminal.js](../windows/assets/terminal.js)
- [windows/assets/xterm.css](../windows/assets/xterm.css)
- [windows/assets/xterm.js](../windows/assets/xterm.js)
- [windows/package-lock.json](../windows/package-lock.json)
- [windows/package.json](../windows/package.json)

## 테스트·빌드·배포

- [.github/workflows/build.yml](../.github/workflows/build.yml)
- [scripts/build-android-bash.sh](../scripts/build-android-bash.sh)
- [scripts/install-addon.sh](../scripts/install-addon.sh)
- [scripts/test-host.sh](../scripts/test-host.sh)
- [scripts/verify-apk.py](../scripts/verify-apk.py)
- [tests/test_core.py](../tests/test_core.py)
- [tests/test_native.py](../tests/test_native.py)
- [tests/test_wbs.py](../tests/test_wbs.py)

## 오픈소스·문서

- [.gitignore](../.gitignore)
- [LICENSE](../LICENSE)
- [README.md](../README.md)
- [docs/01-architecture.md](../docs/01-architecture.md)
- [docs/02-environment.md](../docs/02-environment.md)
- [docs/03-project-tree.md](../docs/03-project-tree.md)
- [docs/04-build-config.md](../docs/04-build-config.md)
- [docs/05-terminal-ui.md](../docs/05-terminal-ui.md)
- [docs/06-pty-engine.md](../docs/06-pty-engine.md)
- [docs/07-runtime-packages.md](../docs/07-runtime-packages.md)
- [docs/08-commands.md](../docs/08-commands.md)
- [docs/09-background-service.md](../docs/09-background-service.md)
- [docs/10-session-process.md](../docs/10-session-process.md)
- [docs/11-server-manager.md](../docs/11-server-manager.md)
- [docs/12-storage.md](../docs/12-storage.md)
- [docs/13-wbs.md](../docs/13-wbs.md)
- [docs/14-addons.md](../docs/14-addons.md)
- [docs/15-desktop.md](../docs/15-desktop.md)
- [docs/16-localization.md](../docs/16-localization.md)
- [docs/17-tests.md](../docs/17-tests.md)
- [docs/18-android-build.md](../docs/18-android-build.md)
- [docs/19-windows-build.md](../docs/19-windows-build.md)
- [docs/20-release.md](../docs/20-release.md)
- [docs/ANDROID-0.1.1-INPUT-FIX.md](../docs/ANDROID-0.1.1-INPUT-FIX.md)
- [docs/INDEX.md](../docs/INDEX.md)
- [docs/STATUS.md](../docs/STATUS.md)
- [pyproject.toml](../pyproject.toml)
- [third_party/NOTICE.md](../third_party/NOTICE.md)
- [third_party/TERMUX-LICENSE.md](../third_party/TERMUX-LICENSE.md)
- [third_party/bash-5.2.37.tar.xz](../third_party/bash-5.2.37.tar.xz)
- [third_party/terminal-emulator/build.gradle](../third_party/terminal-emulator/build.gradle)
- [third_party/terminal-emulator/proguard-rules.pro](../third_party/terminal-emulator/proguard-rules.pro)
- [third_party/terminal-emulator/src/main/AndroidManifest.xml](../third_party/terminal-emulator/src/main/AndroidManifest.xml)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/ByteQueue.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/ByteQueue.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/JNI.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/JNI.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/KeyHandler.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/KeyHandler.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalBuffer.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalBuffer.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalColorScheme.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalColorScheme.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalColors.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalColors.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalEmulator.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalEmulator.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalOutput.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalOutput.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalRow.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalRow.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalSession.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalSession.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalSessionClient.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TerminalSessionClient.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/TextStyle.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/TextStyle.java)
- [third_party/terminal-emulator/src/main/java/com/termux/terminal/WcWidth.java](../third_party/terminal-emulator/src/main/java/com/termux/terminal/WcWidth.java)
- [third_party/terminal-emulator/src/main/jni/Android.mk](../third_party/terminal-emulator/src/main/jni/Android.mk)
- [third_party/terminal-emulator/src/main/jni/termux.c](../third_party/terminal-emulator/src/main/jni/termux.c)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/ByteQueueTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/ByteQueueTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/ControlSequenceIntroducerTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/ControlSequenceIntroducerTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/CursorAndScreenTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/CursorAndScreenTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/DecSetTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/DecSetTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/DeviceControlStringTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/DeviceControlStringTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/HistoryTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/HistoryTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/KeyHandlerTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/KeyHandlerTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/OperatingSystemControlTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/OperatingSystemControlTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/RectangularAreasTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/RectangularAreasTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/ResizeTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/ResizeTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/ScreenBufferTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/ScreenBufferTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/ScrollRegionTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/ScrollRegionTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalRowTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalRowTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalTestCase.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/TerminalTestCase.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/TextStyleTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/TextStyleTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/UnicodeInputTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/UnicodeInputTest.java)
- [third_party/terminal-emulator/src/test/java/com/termux/terminal/WcWidthTest.java](../third_party/terminal-emulator/src/test/java/com/termux/terminal/WcWidthTest.java)
- [third_party/terminal-view/build.gradle](../third_party/terminal-view/build.gradle)
- [third_party/terminal-view/proguard-rules.pro](../third_party/terminal-view/proguard-rules.pro)
- [third_party/terminal-view/src/main/AndroidManifest.xml](../third_party/terminal-view/src/main/AndroidManifest.xml)
- [third_party/terminal-view/src/main/java/com/termux/view/GestureAndScaleRecognizer.java](../third_party/terminal-view/src/main/java/com/termux/view/GestureAndScaleRecognizer.java)
- [third_party/terminal-view/src/main/java/com/termux/view/TerminalRenderer.java](../third_party/terminal-view/src/main/java/com/termux/view/TerminalRenderer.java)
- [third_party/terminal-view/src/main/java/com/termux/view/TerminalView.java](../third_party/terminal-view/src/main/java/com/termux/view/TerminalView.java)
- [third_party/terminal-view/src/main/java/com/termux/view/TerminalViewClient.java](../third_party/terminal-view/src/main/java/com/termux/view/TerminalViewClient.java)
- [third_party/terminal-view/src/main/java/com/termux/view/textselection/CursorController.java](../third_party/terminal-view/src/main/java/com/termux/view/textselection/CursorController.java)
- [third_party/terminal-view/src/main/java/com/termux/view/textselection/TextSelectionCursorController.java](../third_party/terminal-view/src/main/java/com/termux/view/textselection/TextSelectionCursorController.java)
- [third_party/terminal-view/src/main/java/com/termux/view/textselection/TextSelectionHandleView.java](../third_party/terminal-view/src/main/java/com/termux/view/textselection/TextSelectionHandleView.java)
- [third_party/terminal-view/src/main/res/drawable/text_select_handle_left_material.xml](../third_party/terminal-view/src/main/res/drawable/text_select_handle_left_material.xml)
- [third_party/terminal-view/src/main/res/drawable/text_select_handle_right_material.xml](../third_party/terminal-view/src/main/res/drawable/text_select_handle_right_material.xml)
- [third_party/terminal-view/src/main/res/values/strings.xml](../third_party/terminal-view/src/main/res/values/strings.xml)
- [third_party/xterm-addon-fit-0.10.0.tgz](../third_party/xterm-addon-fit-0.10.0.tgz)
- [third_party/xterm-addon-search-0.15.0.tgz](../third_party/xterm-addon-search-0.15.0.tgz)
- [third_party/xterm-xterm-5.5.0.tgz](../third_party/xterm-xterm-5.5.0.tgz)


## 1.0.0 추가 파일

- android/app/src/main/java/studio/bleca/binux/VmManager.kt: 검증 다운로드, QEMU/9p/SSH/포트/메모리/실행 상태.
- GuestBridge.kt 및 native/bridge.c: UID 확인 소켓, 실제 stdin/stdout/stderr/윈도 크기/exit status.
- SystemDnsProxy.kt 및 third_party/vm/patches/slirp-android-dns.patch: Android 시스템 DNS 브로커.
- DesktopAudio.kt: SSH PCM을 AudioTrack으로 재생하고 종료/오류를 보고합니다.
- BootReceiver.kt: 명시 opt-in과 작업별 선택만 부팅 재시작 대상으로 합니다.
- core/binux/remote.py: 취소 race/PID 시작시간/프로세스 그룹/controlling PTY.
- runtime/guest: 실제 guest bootstrap, pkg, venv pip, 셸 시작 설정.
- scripts/build-runtime-image.sh 및 test-runtime-image.py: 실제 서명된 ARM64 배포판·부팅/패키지 검사.
- scripts/build-android-vm.sh, prepare-vm.py 및 third_party/vm: 재현 가능한 APK 엔진 빌드 소스.
- scripts/build-addons.py, core/binux/trust.py, runtime/addons: Ed25519 공개 키·서명 패키지.
- tests/test_remote.py, test_vm_backup.py 및 Android/X11 회귀 테스트: 실제 프로세스/복원/입력/설정 검증.
