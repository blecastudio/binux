# 18. Android APK 빌드

JDK21과 Python3.12, gcc/make, bison/flex/m4, autoconf/automake/libtool,
pkg-config, Meson1.6.1/Ninja가 필요합니다. SDK/NDK 도구를 정상 설치하세요.

```bash
# Android SDK Manager 설치 후:
sdkmanager 'platforms;android-35' 'build-tools;35.0.0' 'ndk;27.2.12479018' 'cmake;3.22.1'
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
python3 -m pip install meson==1.6.1 ninja==1.11.1.1
python3 scripts/prepare-x11.py
bash scripts/build-android-bash.sh
bash scripts/build-android-vm.sh
# 소스의 고정 runtime-manifest.json은 부팅 검사를 통과한 공식 Release를 가리킵니다.
# 새 이미지를 발행한 경우 scripts/pin-runtime.py로 검증 후 갱신하세요.
cd android
./gradlew --no-daemon assembleDebug assembleDebugAndroidTest lintDebug :app:testDebugUnitTest :desktop-x11:testDebugUnitTest :terminal-emulator:testDebugUnitTest
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb install -r desktop-x11/build/outputs/apk/debug/desktop-x11-debug.apk
adb shell am start -n studio.bleca.binux/.MainActivity
```

ARM64 APK 두 개를 생성합니다. 터미널 APK는 Bash, JNI PTY, 제어/프로세스/VM 브리지와
QEMU 엔진을 포함하며 Desktop:X11은 별도 X.Org 화면 서버입니다. 기본 설치에는 Linux
배포판과 XFCE가 없습니다. `binux runtime install debian` 또는 `ubuntu`로 선택합니다.

```bash
# 저장소 루트에서:
python3 scripts/verify-apk.py android/app/build/outputs/apk/debug/app-debug.apk
python3 scripts/verify-apk.py --kind x11 android/desktop-x11/build/outputs/apk/debug/desktop-x11-debug.apk
```

정적 검사는 APK의 ABI/Android 링커/16 KiB ELF 정렬, 고정 런타임 데이터와 설치기
해시를 확인합니다. Android 실행 테스트는 연결된 실기기에서 별도로 수행해야 합니다.

Release는 `./gradlew assembleRelease`로 unsigned APK를 만든 뒤, 소유한 keystore로 zipalign/apksigner를 사용합니다. 비밀키를 저장소에 넣지 않습니다. 현재 GitHub 개발 프리뷰의 debug 서명을 운영용 보안 서명이라고 표시하지 않습니다. 현재 compile/target 35는 구현 기준이며 2026년 Play 배포 전 요구되는 target SDK 및 정책을 다시 확인하고 API 36+로의 업그레이드를 검증해야 합니다.

Play Store 제출 시 specialUse foreground service 정당성과 실행파일 배포 모델을 설명해야 합니다. 해당 심사의 승인이나 실제 기기 백그라운드 실행은 이 빌드로 보장되지 않습니다.
