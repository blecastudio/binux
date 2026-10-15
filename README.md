# binux (비눅스) 1.0.0

BlecaStudio의 CLI 중심 개발 실행환경입니다. Android는 실제 Bash/PTY, 선택형
Debian/Ubuntu Linux VM과 별도 **Binux Desktop:X11** APK를 사용합니다.
Windows는 실제 ConPTY와 선택한 WSL 배포판을 사용합니다.

**1.0.0은 개발 프리뷰입니다.** 빌드/호스트 테스트와 Android·Windows 실기기 실행
검증을 구분합니다. 현재 검증 범위 및 제한은 [상태표](docs/STATUS.md)를 확인하세요.
Android OS의 강제 종료 정책을 우회하거나 24시간 실행을 보장하지 않습니다.

[공식 Release](https://github.com/blecastudio/binux/releases) ·
[1.0 설치·명령어·Desktop·WBS 안내](docs/RUNTIME-1.0.md) ·
[20개 산출물](docs/INDEX.md)

## Android 사용

ARM64 APK 두 개를 같은 서명으로 설치하세요. 기본 화면은 CLI이며 Desktop은
자동 설치하지 않습니다. VM은 Android 12 이상, 충분한 RAM/저장공간이 필요합니다.
Android 네이티브 Bash는 API26 이상에서 빌드하도록 구성합니다.

```bash
binux runtime install debian
binux runtime use debian
# Ubuntu도 선택 가능: binux runtime install ubuntu
pkg update
pkg install python3 nodejs npm git openssh-client
pip install flask fastapi uvicorn
npm install express
python3 --version
node --version
binux shell
```

`pkg`/`apt`는 선택한 실제 게스트 배포판에 연결합니다. `pip`는 `~/.venv`를 사용합니다.
VM 엔진은 APK에 포함하고, 커널·rootfs 데이터는 고정 SHA-256으로 검증합니다.
다운로드한 Linux ELF를 Android 앱 저장소에서 직접 실행하는 구현을 사용하지 않습니다.
초기 홈 프롬프트는 `~/`이며 `pwd`의 실제 출력은 바꾸지 않습니다.

## 선택형 Desktop

```bash
binux desktop source
binux desktop install
# 공식 URL 방식:
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
binux bg enable
binux desktop start
binux desktop status
binux desktop stop
```

설치기는 파일 관리자·GUI 편집기·오디오·개발 도구·Chromium·WBS 실행기를 선택하는
CLI TUI입니다. 실제 apt 설치 성공 후에만 XFCE 설치 기록을 저장합니다.
공식 스크립트가 APK에서 검토한 SHA-256과 다르면 다운로드를 거부합니다.
Desktop:X11은 실제 X.Org 서버이며 같은 서명 앱에만 인증 쿠키를 전달합니다.
두 Android 앱의 툴바·전체화면 설정을 저장하고, 숨겨도 설정 버튼을 사용할 수 있습니다.

Google 공식 저장소의 amd64/ARM64 Chrome을 기본 선택으로 제공합니다. 고정한 공개 키와
apt 서명을 확인하고, 샌드박스를 켠 실제 실행에 통과한 경우 기본 브라우저로 설정합니다.
실행하지 못하면 Debian Chromium 또는 Android Chrome을 선택하도록 안내합니다.

## 작업 및 서버

```bash
binux bg run python3 -u server.py
binux bg run --restart-on-failure node server.js
binux bg list
binux bg logs JOB_ID
binux bg stop JOB_ID
binux server create demo python 8000
binux server start demo
binux server logs demo
binux server stop demo
```

Android 서비스는 UI와 작업을 분리하고 알림에서 중지할 수 있습니다. 게스트 서버의
기본 바인딩과 Android 미리보기는 127.0.0.1이며 SSH로 연결합니다.
물리 LAN 공개는 `binux runtime forward debian 8000 --allow-network`를 명시해야 합니다.

## Windows 및 호스트

```powershell
dotnet publish windows -c Release -r win-x64 --self-contained false -o artifacts/windows
.\artifacts\windows\binux.exe
.\artifacts\windows\binux.exe runtime install debian
.\artifacts\windows\binux.exe runtime tools
```

.NET 10 Desktop Runtime과 WebView2 Runtime이 필요합니다. Windows PowerShell과 WSL을
선택하며 WSL의 Linux 명령을 Windows 네이티브 프로그램으로 소개하지 않습니다.
Windows 툴바/전체화면 단축키는 F10/F11입니다. publish 폴더 전체를 배포하세요.

```bash
# Linux/WSL에서 호스트 도구를 별도로 설치할 경우:
python3 -m venv .venv
.venv/bin/python -m pip install .
source .venv/bin/activate
binux doctor
binux server create demo --kind python --port 8000
```

WBS는 TLS1.3/mTLS, 양쪽 기기 승인, 폴더/명령 허용 목록, SHA-256 파일 전송과
기기 인증 폐기를 구현합니다. [페어링 및 실제 한도](docs/RUNTIME-1.0.md)를 확인하세요.
공식 add-on은 일반 apt/pip/npm과 별도로 Release 매니페스트·SHA-256·Ed25519를 검증합니다.

## 빌드와 테스트

Linux 빌드 호스트: JDK21, Android SDK35, NDK27.2.12479018, CMake3.22.1,
Python3.12, gcc/make, bison/flex/m4, autoconf/automake/libtool, pkg-config,
Meson1.6.1, Ninja. SDK/NDK 도구와 라이선스를 정상 설치해야 합니다.

```bash
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
python3 -m pip install meson==1.6.1 ninja==1.11.1.1
python3 scripts/prepare-x11.py
bash scripts/build-android-bash.sh
bash scripts/build-android-vm.sh
cmake -S native -B native/build/host
cmake --build native/build/host
bash scripts/test-host.sh
cd android
./gradlew assembleDebug assembleDebugAndroidTest lintDebug :app:testDebugUnitTest :desktop-x11:testDebugUnitTest
# ARM64 기기가 연결된 경우만:
./gradlew connectedDebugAndroidTest
```

[Android 빌드](docs/18-android-build.md) · [Windows 빌드](docs/19-windows-build.md) ·
[실제 테스트/기기 검증 구분](docs/17-tests.md) · [출시 가이드](docs/20-release.md)

라이선스는 GPL-3.0-only입니다. 독립 실행 QEMU는 자체 GPLv2 라이선스를 유지합니다.
[LICENSE](LICENSE), [오픈소스 고지](third_party/NOTICE.md), 전체 대응 소스/빌드 절차를
바이너리와 함께 제공합니다. 사용자 프로젝트에 binux 라이선스를 자동 적용하지 않습니다.
