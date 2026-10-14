# binux 1.0.0 개발 프리뷰

Android ARM64에서 기본 Bash/PTY와 선택형 Debian/Ubuntu Linux VM을 분리합니다.
VM 엔진은 APK 내부 실행파일이며 배포판 디스크·커널·initrd는 검증한 데이터입니다.
Android 앱 저장소에 내려받은 Linux ELF를 Android에서 직접 실행하지 않습니다.
게스트 root/sudo는 VM 안의 권한이며 Android root·SELinux 권한을 주지 않습니다.

## 설치 및 개발

두 APK를 같은 서명으로 설치합니다. 기존 0.1.2 위에 `adb install -r`로 업데이트할
때 앱 데이터는 유지됩니다. 배포판은 초기 설치에 포함하지 않습니다.

```bash
binux runtime install debian
binux runtime use debian
# 또는: binux runtime install ubuntu; binux runtime use ubuntu
pkg update
pkg install python3 python3-venv nodejs npm git openssh-client
pip install flask fastapi uvicorn
python3 --version
node --version
npm install express
binux shell
```

`pkg`는 선택한 배포판의 apt 호환 명령입니다. Android 네이티브 다운로드 저장소로
표시하지 않습니다. `apt`/`apt-get`은 게스트 sudo를 사용하고 `pip`는 `~/.venv`에
설치합니다. Python도 같은 venv 경로를 우선 사용합니다. 프로젝트별 격리는 별도
`python3 -m venv PROJECT/.venv`로 구성합니다. `~/`는 Android 앱 전용 공유 홈이며
실제 `pwd` 출력은 변경하지 않습니다. VM별 rootfs/state와 인증키는 홈과 분리합니다.

VM 하나의 기본 RAM은 1024 MiB, 최대 디스크는 10 GiB입니다. 설치기는 다운로드
캐시와 디스크 확장에 필요한 여유 공간을 확인합니다. 두 배포판은 별도 공간을 씁니다.
CLI에 적은 RAM을 할당하려면 `binux settings set vm-memory 512`를 사용하세요.
소프트웨어 CPU 에뮬레이션이므로 네이티브 실행과 같은 성능을 약속하지 않습니다.

```bash
binux runtime list
binux runtime logs debian
binux runtime exec debian uname -a
binux runtime stop debian
# 게스트 패키지/state 삭제 전 백업하고, --yes를 명시합니다. 공유 홈은 유지됩니다.
binux runtime uninstall debian --yes
```

## 백그라운드 및 서버

```bash
binux bg run python3 -u server.py
binux bg run --restart-on-failure node server.js
binux bg list
binux bg logs JOB_ID
binux bg stop JOB_ID
binux server create example python 8000
binux server start example
binux server logs example
binux server stop example
```

서버 템플릿은 게스트 127.0.0.1에 바인딩하며 Android 127.0.0.1에 SSH 포트를
연결합니다. 기존 프로젝트는 `binux server add NAME PORT CWD COMMAND ARGS...`로
등록합니다. 공유 홈 밖의 Android 디렉터리는 게스트에 자동 공개하지 않습니다.
다른 기기에 공개하려는 포트만 `binux runtime forward debian 8000 --allow-network`를
명시하세요. 연결을 종료할 때 `binux runtime unforward debian 8000`을 실행합니다.

재부팅 자동 실행은 기본 off입니다. `binux bg autostart on`과
`binux bg run --autostart COMMAND ARGS...`로 선택한 작업만 대상으로 합니다.
알림의 모두 종료 및 명시적 작업 중지는 자동 실행 선택도 해제합니다.
Android 12~16/OEM 정책이 서비스를 막거나 강제 종료하면 작업은 끊어질 수 있습니다.
이전 PID에 재접속하거나 종료된 작업을 계속 실행 중으로 표시하지 않습니다.
화면 꺼짐·Doze·재부팅·음성 출력은 실기기 검증 전이며 24시간 실행을 보장하지 않습니다.

## Desktop과 출처 확인

```bash
binux desktop source
binux desktop install
# 다음 공식 URL도 지원합니다. APK가 검토한 SHA-256과 다르면 다운로드를 거부합니다.
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
binux bg enable
binux desktop start
binux desktop status
binux desktop stop
binux desktop update
binux desktop uninstall
```

CLI 체크박스로 파일 관리자·Mousepad·오디오·개발 도구·Chromium·WBS 실행기를
선택합니다. 실제 apt 패키지 설치가 성공한 뒤 설치 기록을 저장합니다.
Desktop:X11은 자체 APK의 X.Org 서버이며 loopback TCP와 Xauthority를 사용합니다.
인증 쿠키는 같은 서명 앱 사이에서만 전달하고 공유 홈 밖에 둡니다.
처음 X11 앱을 열어 초기화한 뒤 Desktop을 시작하세요.
두 앱의 설정에서 툴바·보조키·전체화면을 저장할 수 있고 숨겨도 설정 버튼을 쓸 수 있습니다.

Linux Google Chrome은 ARM64 공식 패키지가 없어 자동 설치하지 않습니다.
Debian Chromium을 선택하거나 `binux desktop browser https://example.com`으로
설치된 Android Chrome을 열 수 있습니다. Ubuntu Chromium의 snap 구성은 자동화하지
않습니다. 브라우저 샌드박스를 비활성화하는 옵션을 넣지 않습니다.

오디오 기능 설치 후 `binux desktop audio start|stop|status`를 사용합니다.
게스트 PulseAudio 모니터의 PCM을 SSH로 받아 Android AudioTrack에 씁니다.
WBS Desktop 선택 항목은 실제 `wbs` 명령을 여는 XFCE 터미널 실행기입니다.

## 사용자 프로젝트 백업

```bash
binux storage backup backup.tar.gz
binux storage restore backup.tar.gz
```

VM의 실제 공유 홈·프로젝트·저장소를 백업합니다. 복원은 ~/restored-날짜에 새 폴더를
만들고 기존 프로젝트를 덮어쓰지 않습니다. 네이티브 Android 경로 대신 상대 파일명을
사용하세요. 인증키/private state와 전체 VM 디스크는 이 프로젝트 백업에 포함하지 않습니다.
Android SAF 내보내기는 아직 제공하지 않으므로 SSH/WBS 또는 사용자가 승인한 파일 도구를
사용합니다. WBS 파일 한도보다 큰 아카이브는 SSH 등 다른 전송 수단이 필요합니다.

## WBS와 보조 패키지

```bash
wbs init --ip YOUR_DEVICE_IP
# 양쪽에서 공개 identity.pem만 교환하고 지문을 별도 경로로 확인합니다.
wbs pair OTHER_PUBLIC_CERT.pem --name peer --share projects=/home/binux/projects --allow-port 8000
wbs serve
# 수신이 필요한 경우에만 Android의 물리 LAN 포트를 공개합니다.
binux runtime forward debian 58290 --allow-network
wbs windows WINDOWS_IP --peer peer
wbs share ./project --remote-share projects
wbs sync ./project --remote-share projects
wbs forward 9000 8000
# 상대가 페어링에서 허용한 포트만 연결합니다.
wbs revoke peer
binux addon list
binux addon install developer-tools
```

WBS는 TLS1.3/mTLS, 기기별 인증·승인 폴더·정확한 argv 허용 목록과 키 폐기를
구현합니다. sync는 SHA-256을 비교하는 단방향 동기화이며 기본 덮어쓰기를 거부합니다.
현재 파일 하나의 전송 한도는 16 MiB, 원격 명령은 15초입니다. 화면 공유는 제공하지
않습니다. Windows 앱에서는 같은 소스를 WSL에 전달합니다. Windows 실행파일을
Android에서 직접 실행하는 기능으로 소개하지 않습니다.

공식 add-on Release 매니페스트는 SHA-256과 APK에 포함된 Ed25519 공개 키로
검증합니다. 설치 후 자동으로 외부 훅을 실행하지 않습니다. 일반 apt/pip/npm 패키지는
각 배포판/레지스트리 신뢰 체계에 속하며 공식 add-on과 분리합니다.

## 빌드·검증 범위

```bash
python3 scripts/prepare-x11.py
bash scripts/build-android-bash.sh
bash scripts/build-android-vm.sh
cd android
./gradlew assembleDebug assembleDebugAndroidTest lintDebug :app:testDebugUnitTest :desktop-x11:testDebugUnitTest
# Android ARM64 기기가 연결되었을 때만:
./gradlew connectedDebugAndroidTest
```

Linux 이미지: `scripts/build-runtime-image.sh debian OUTPUT` / `ubuntu OUTPUT`를
격리된 sudo 사용 빌드 머신에서 실행합니다. 공식 배포판 서명·해시를 사용하고 모든
대응 소스 및 패키지 버전을 배포합니다. `scripts/test-runtime-image.py`는 실제 ARM64
커널을 부팅해 SSH 인증·공유 홈·pkg/pip/npm 설치를 검사합니다.
게스트 검사에는 Flask/FastAPI/Express의 실제 HTTP 응답과 종료, 검토한 설치기의
XFCE 설치·인증된 Xvfb 위 세션 실행이 포함됩니다. Android X11 표시 검증과는 별개입니다.
Android NDK 빌드와 ELF 16 KiB 검사는 Android 기기 실행 테스트와 구분합니다.
Windows는 `.NET 10 + WebView2`가 필요하며 `dotnet publish windows -c Release
-r win-x64 --self-contained false -o artifacts/windows`로 전체 폴더를 배포합니다.
WSL 도구 설치는 `binux runtime install debian`, `binux runtime tools`를 사용합니다.
Windows 툴바/전체화면 복구 단축키는 F10/F11입니다. Windows OS 실행 검증은 대기입니다.
