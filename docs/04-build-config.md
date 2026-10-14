> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 4. Gradle 및 네이티브 빌드

Android 설정: `android/settings.gradle`, `android/build.gradle`, `android/app/build.gradle`. 터미널 모듈은 `third_party`의 실제 소스를 빌드합니다. Bash는 GNU source archive로 교차 컴파일하며 단순히 파일 이름만 바꾼 Linux/glibc 바이너리를 사용하지 않습니다.

```bash
bash scripts/build-android-bash.sh
cd android
./gradlew assembleDebug
```

APK 실행 엔트리 `libbinux_bash.so`, `libbinuxctl.so`, `libbinuxjob.so`는 `.so` 이름을 가진 **PIE 실행파일**이며 dlopen으로 로드하는 라이브러리가 아닙니다. JNI `libbinux_process.so`, `libtermux.so`와 구분합니다. `android:extractNativeLibs=true` 및 legacy JNI packaging을 사용합니다. target SDK를 낮춰 Android 실행 정책을 우회하지 않습니다.

Bash 동적 링커는 `/system/bin/linker64`이며 libc/libdl에 연결합니다. NDK 라이브러리와 Bash는 16 KiB LOAD 정렬로 빌드합니다. `scripts/verify-apk.py`가 APK의 모든 ARM64 네이티브 파일을 검사합니다. 이것은 실제 SELinux/기기 실행 성공을 입증하는 테스트는 아닙니다.

```bash
cmake -S native -B native/build/host
cmake --build native/build/host
```

Gradle wrapper ZIP SHA-256도 고정했습니다. 릴리스 APK 서명은 별도의 사용자가 소유한 키로 처리합니다.
