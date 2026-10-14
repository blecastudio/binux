# 18. Android APK 빌드

```bash
# Android SDK Manager 설치 후:
sdkmanager 'platforms;android-35' 'build-tools;35.0.0' 'ndk;27.2.12479018' 'cmake;3.22.1'
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
bash scripts/build-android-bash.sh
cd android
./gradlew --no-daemon assembleDebug assembleDebugAndroidTest lintDebug :terminal-emulator:testDebugUnitTest
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n studio.bleca.binux/.MainActivity
```

생성: android/app/build/outputs/apk/debug/app-debug.apk. ARM64만 포함하며 Kotlin UI만 있는 APK가 아닙니다. Bash, JNI PTY, binuxctl, binuxjob, 프로세스 제어 라이브러리를 포함합니다. 빌드 로그를 읽고 verify-apk.py를 실행하세요.

Release는 `./gradlew assembleRelease`로 unsigned APK를 만든 뒤, 소유한 keystore로 zipalign/apksigner를 사용합니다. 비밀키를 저장소에 넣지 않습니다. debug key APK를 공식 배포로 소개하지 않습니다. 현재 compile/target 35는 구현 기준이며 2026년 Play 배포 전 요구되는 target SDK 및 정책을 다시 확인하고 API 36+로의 업그레이드를 검증해야 합니다.

Play Store 제출 시 specialUse foreground service 정당성과 실행파일 배포 모델을 설명해야 합니다. 해당 심사의 승인이나 실제 기기 백그라운드 실행은 이 빌드로 보장되지 않습니다.
