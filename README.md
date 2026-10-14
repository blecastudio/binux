# binux (비눅스) 0.1.0

Android 최신 수정판은 **0.1.2**이며 Binux Desktop:X11 0.1.0을 별도 제공합니다. 툴바 숨김·전체화면과 제공된 로고를 적용했습니다. [Desktop 설치 및 X11 안내](docs/DESKTOP-X11.md)를 참고하세요. Android 0.1.1에서 터미널 입력 포커스, 키보드 버튼, 분할 패널 입력 대상과 종료 세션 선택을 수정했습니다. [수정 내용 및 검증](docs/ANDROID-0.1.1-INPUT-FIX.md)을 참고하세요. Windows/호스트 도구는 0.1.0으로 유지합니다.

BlecaStudio의 CLI 중심 개발 실행환경. 실제 Bash/PTY Android 앱, 실제 ConPTY Windows 앱, Linux/WSL용 개발 도구 소스를 포함합니다.

**현재 결과는 실험용 최소 버전입니다. 전체 7단계 제품을 완성한 상태가 아닙니다.** Android/Windows 앱은 빌드했고, Linux 호스트에서 프로세스·서버·패키지 보안·WBS 통합을 실행해 검증했습니다. Android 실제 기기와 Windows OS에서 실행한 결과는 아직 없습니다. Android Python/Node.js/PRoot, 앱 간 WBS와 Debian/Ubuntu 실행 엔진은 후속 통합 대상입니다. 별도 X11 앱은 실제 서버 소스로 빌드했으며 기기 실행 검증은 대기입니다. 미지원 명령은 실패 코드를 반환합니다.

[binux 및 Desktop:X11 APK 다운로드](https://github.com/blecastudio/binux/releases/tag/v0.1.2) · [설치·사용·제한 사항](docs/DESKTOP-X11.md)

## 산출물

- [요청한 20개 산출물 안내](docs/INDEX.md)
- [구현 상태와 요구사항 검증표](docs/STATUS.md)
- [파일별 소스 안내](docs/SOURCE-CATALOG.md)
- [Android 빌드](docs/18-android-build.md), [Windows 빌드](docs/19-windows-build.md)
- [실제 테스트 결과](docs/17-tests.md)
- [GitHub 및 Release 배포](docs/20-release.md)

공식 GitHub 저장소: [blecastudio/binux](https://github.com/blecastudio/binux). Desktop 설치기는 지원되는 Debian/Ubuntu 환경에서 다음과 같이 실행합니다. **현재 Android Native APK에는 배포판 실행 엔진이 없어 이 명령은 호환성 오류로 종료합니다.** X11 APK만으로 XFCE를 실행할 수 없습니다.

```bash
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
```

설치기 옵션, Android 제한, 두 앱의 빌드·설정·검증 범위는 [Desktop/X11 문서](docs/DESKTOP-X11.md)를 확인하세요.

## Android 빌드 및 설치

Linux 빌드 호스트에 JDK 21, Android SDK 35, NDK 27.2.12479018, CMake 3.22.1, Python 3.12+, gcc, make, bison, m4, patch, dpkg-deb, tar, xz, sha256sum을 설치합니다.

```bash
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
python3 scripts/prepare-x11.py
bash scripts/build-android-bash.sh
cd android
./gradlew assembleDebug :terminal-emulator:testDebugUnitTest
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n studio.bleca.binux/.MainActivity
```

최초 실행은 언어 선택 → 선택형 백그라운드 허용 → 실제 CLI 순서입니다. Desktop은 설치하지 않습니다. 이 APK는 ARM64 전용입니다. 앱 안에서 `binux doctor`, `ls`, `pwd`, `getpid`, `binux bg run sleep 30` 등을 실행할 수 있게 구현했습니다. 실제 기기 테스트로 확인해야 합니다. `bash script.sh`로 스크립트를 실행하세요. 앱의 쓰기 가능한 디렉터리에서 다운로드한 네이티브 실행파일을 chmod하여 실행하는 방식은 지원하지 않습니다.

## Linux/WSL 실행

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
source .venv/bin/activate
export BINUX_HOME="$PWD/.binux-data"
binux doctor
binux shell
binux server create demo --kind python --port 8000
binux server start demo
binux server list
binux server logs demo
binux server stop demo
binux bg shutdown
```

`binux shell`은 실제 Bash를 PTY에 연결합니다. 호스트 Python/Node.js/Git/SSH를 사용합니다. 위 코드는 Android 앱 안에서 Python이 설치되어 있다는 뜻이 아닙니다. Flask/FastAPI는 프로젝트 venv의 pip, Express는 프로젝트 npm으로 설치하고 `binux server add` 또는 `binux bg run`으로 실제 명령을 등록합니다. 기본 서버 템플릿은 127.0.0.1에 바인딩합니다.

```bash
binux bg run python3 -u server.py
binux bg run --restart-on-failure node server.js
binux bg list
binux bg logs JOB_ID
binux bg stop JOB_ID
```

작업은 CLI 종료 후 별도 supervisor가 관리하며 명시적인 중지 요청을 지원합니다. Linux supervisor의 재시작은 실패 시 최대 3회이며 OS가 앱/daemon을 종료한 후 자동으로 이전 프로세스가 계속 실행 중이라고 표시하지 않습니다.

## Windows 빌드

```powershell
dotnet publish windows -c Release -r win-x64 --self-contained false -o artifacts/windows
.\artifacts\windows\binux.exe
```

.NET 10 Desktop Runtime과 WebView2 Runtime이 필요합니다. Windows 10 1809 이상/Windows 11용이며 PowerShell과 WSL을 선택합니다. Windows 실행 검증은 아직 없습니다. 배포할 때 exe만 복사하지 말고 publish 디렉터리 전체를 배포하세요.

## 테스트

```bash
cmake -S native -B native/build/host
cmake --build native/build/host
bash scripts/test-host.sh
cd android
./gradlew :terminal-emulator:testDebugUnitTest lintDebug assembleDebugAndroidTest
# ARM64 기기가 연결되어 있을 때만:
./gradlew connectedDebugAndroidTest
```

테스트 범위와 기기별 수동 검증 절차는 [테스트 문서](docs/17-tests.md)에 있습니다. 화면 꺼짐, Doze, 제조사 배터리 관리, Android 강제 종료 후 복원은 실기기 검증 전입니다. 백그라운드 24시간 실행을 보장하지 않습니다.

## 확장 및 라이선스

일반 Linux 패키지와 BlecaStudio add-on을 구분합니다. 호스트의 `binux addon`은 GitHub Release 매니페스트, SHA-256, 설정한 Ed25519 키 검증, 안전한 압축 해제를 구현했습니다. 공식 Release가 없으므로 지금 설치할 수 있는 공식 add-on 목록은 없습니다. Android native pkg는 동적 네이티브 패키지 저장소를 제공하지 않습니다.

binux는 GPL-3.0-only입니다. [LICENSE](LICENSE), [오픈소스 고지](third_party/NOTICE.md)를 함께 배포해야 합니다. 사용자의 프로젝트 파일에 binux의 라이선스를 자동 적용하지 않습니다.
