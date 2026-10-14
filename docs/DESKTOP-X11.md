# binux Desktop와 Binux Desktop:X11

Android CLI는 0.1.2, 별도 ARM64 X11 앱은 0.1.0입니다. [APK 다운로드](https://github.com/blecastudio/binux/releases/tag/v0.1.2). 공개 Release의 두 APK를 다시 내려받아 검증된 로컬 빌드와 동일한 것을 확인했습니다. Desktop은 기본 설치에 포함되지 않습니다.

## 설치 링크

BlecaStudio 저장소의 `setup-binux-desktop`은 실제 Debian/Ubuntu apt 패키지를 설치하는 Bash 설치기입니다.

```bash
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
```

다운로드한 스크립트는 사용자 권한으로 실행됩니다. 실행 전 출처와 내용을 검토하세요. Bash 프로세스 치환 실패는 부모 Bash에 전달되지 않을 수 있으므로, 자동화에서는 다운로드가 성공한 후 실행하는 다음 형태를 권장합니다.

```bash
curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop -o setup-binux-desktop
bash setup-binux-desktop --check
bash setup-binux-desktop
```

위 `curl -o` 예시는 일반 Linux curl용입니다. Android Native의 최소 HTTPS 스크립트 어댑터는 `curl -Lf URL` 형태만 지원하며 최대 1 MiB UTF-8 스크립트를 실제 다운로드합니다. 바이너리와 임의 curl 옵션은 지원하지 않습니다. 전체 curl CLI를 제공하는 것으로 표시하지 않습니다.

**현재 Android Native APK에는 Debian/Ubuntu 실행 엔진이 없습니다. 이 환경에서 설치기는 종료 코드 69와 원인을 출력하며 XFCE 설치 성공을 표시하지 않습니다.** X11 APK는 화면 서버이며 배포판, XFCE, Python, Node.js 실행 엔진을 제공하지 않습니다. 최신 Android의 실행파일 제한을 해결하지 않은 PRoot RootFS를 작동한다고 광고하지 않습니다. targetSdk를 낮추거나 SELinux를 해제하거나 `/system/bin/linker`로 정책을 우회하지 않습니다.

지원되는 Debian/Ubuntu 안에서는 번호로 체크박스를 전환하여 파일 관리자(Thunar), 편집기(Mousepad), 오디오(PulseAudio), 개발 도구, Chromium을 선택합니다. 비대화형 옵션도 지원합니다.

```bash
bash setup-binux-desktop --yes --features files,editor,tools --renderer x11
bash setup-binux-desktop --yes --features files --renderer vnc
```

2 GiB 여유 공간, 배포판, 아키텍처, 필요한 명령, 실제 설치된 패키지 상태를 검사합니다. apt가 배포판 저장소 서명을 검증합니다. 관리자 권한이 없는 일반 Linux에서는 sudo를 통해 사용자에게 인증을 요청합니다. 네이티브 Android에 sudo나 루트 권한을 제공하지 않습니다. 모든 패키지 검증 후에만 설치 기록을 작성합니다. 이미 설치된 XFCE 프로그램은 apt가 유지합니다.

Google Chrome는 ARM64용 공식 Linux 패키지가 없으며, PRoot/fake-root에서는 샌드박스 실행을 보장할 수 없습니다. 따라서 자동 Chrome 설치는 보류하고 Chromium을 명시적으로 선택할 수 있도록 했습니다. `--no-sandbox`를 사용하지 않습니다. WBS Desktop Integration은 미구현 오류를 반환합니다.

## 실제 X11 앱

앱 ID는 `studio.bleca.binux.x11`, 이름은 `Binux Desktop:X11`입니다. Termux:X11의 실제 X.Org 서버와 Android 렌더러를 포크했습니다. Termux 앱, Termux 패키지 서버, shared UID, app_process 셸 로더가 필요하지 않습니다. 서버의 APK 네이티브 라이브러리를 JNI로 로드합니다. 별도의 `:xserver` 프로세스와 specialUse Foreground Service가 사용자 시작 세션을 관리하며 알림의 종료 버튼으로 중지합니다.

X11 TCP는 IPv4/IPv6 loopback으로만 바인딩합니다. `DISPLAY=127.0.0.1:1` (6001번 포트), `MIT-MAGIC-COOKIE-1` 인증을 사용합니다. 인증 쿠키는 SecureRandom으로 생성하여 앱 전용 파일에 저장합니다. 읽기 전용 ContentProvider는 같은 binux 서명키로 서명한 앱에만 허용됩니다. 쿠키 값을 로그에 출력하지 않습니다. 새로운 서버 세션은 쿠키를 새로 생성하므로 연결하는 런타임에 다시 가져와야 합니다. 외부 네트워크에 X11을 공개하는 옵션은 제공하지 않습니다.

binux에서 다음 명령을 사용할 수 있습니다.

```bash
binux desktop status
binux desktop installer
binux desktop install     # 실제 설치기 작업 및 로그. Native에서 배포판 누락 오류를 반환합니다.
binux desktop x11 open   # 별도 APK가 설치되어 있어야 합니다.
binux desktop x11 auth   # 같은 서명키 APK에서 인증 파일 가져오기. X11 앱을 먼저 여세요.
```

이 명령으로 가져온 인증 파일은 배포판 런타임 통합 후 X11 클라이언트에 전달할 수 있습니다. 가져오기만으로 GUI 런타임이 생기지 않습니다. 현재 Native Android의 desktop start/update/uninstall은 배포판 실행 엔진 부재 오류를 반환합니다.

## 화면 설정

binux의 설정에서 상단 툴바·보조 키 툴바 표시, 전체화면, 화면 켜짐 유지(앱 사용 중)를 저장합니다. 숨김 상태에서는 오른쪽 위 ⚙ 버튼으로 설정을 다시 엽니다. 터미널을 탭하면 실제 PTY 입력 키보드를 표시합니다.

```bash
binux settings set toolbar off
binux settings set extra-keys off
binux settings set fullscreen on
binux settings set keep-screen-on off
```

CLI로 변경하면 앱을 다시 열어 적용합니다. UI에서 바꾸면 즉시 반영합니다.

Desktop:X11의 ⚙ → 화면(Output) → 전체화면(Fullscreen), 화면 켜짐 유지, 방향, 해상도와 키보드 및 툴바(Keyboard) → 보조 키 툴바 표시(Show additional keyboard)를 설정합니다. 툴바를 숨겨도 ⚙는 유지합니다. 전체화면에서는 가장자리를 밀어 Android 시스템 바를 일시 표시합니다. 설정은 SharedPreferences에 유지됩니다. binux는 DataStore를 사용합니다. 배터리 최적화 설정은 사용자가 직접 승인해야 하며 24시간 실행을 보장하지 않습니다.

제공된 로고 원본은 `branding/`에 보관하고 각 앱 아이콘 및 X11 대기 화면에 적용했습니다. 그림의 픽셀은 수정하지 않았습니다.

## 소스 빌드와 실기기 검사

JDK 21, SDK/build-tools 35, NDK 27.2.12479018, CMake 3.22.1, Python 3.12+, gcc, make, bison, m4, patch, dpkg-deb가 필요합니다. X11의 17개 입력 소스/데이터 아카이브는 `third_party/x11/sources.json`의 SHA-256으로 검증합니다. 펼친 소스는 Git에서 제외하며 검증된 아카이브로 재생성합니다. 패치 적용 실패는 빌드를 중단합니다.

```bash
python3 scripts/prepare-x11.py
bash scripts/build-android-bash.sh
cd android
./gradlew :app:assembleDebug :desktop-x11:assembleDebug \
  :app:assembleDebugAndroidTest :desktop-x11:assembleDebugAndroidTest \
  :app:testDebugUnitTest :app:lintDebug :desktop-x11:lintDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb install -r desktop-x11/build/outputs/apk/debug/desktop-x11-debug.apk
```

두 APK는 같은 서명키로 빌드해야 인증 Provider를 사용할 수 있습니다. 현재 산출물은 개발용 debug 서명이며 운영 Release 키를 생성·게시하지 않았습니다. Google Play 배포와 specialUse 승인 여부는 별도 검토 대상입니다.

```bash
python3 scripts/verify-apk.py android/app/build/outputs/apk/debug/app-debug.apk
python3 scripts/verify-apk.py --kind x11 android/desktop-x11/build/outputs/apk/debug/desktop-x11-debug.apk
# ARM64 Android 12~16 실제 기기를 연결한 뒤:
cd android
./gradlew :app:connectedDebugAndroidTest :desktop-x11:connectedDebugAndroidTest
```

`X11DeviceTest`는 실제 서버의 X11 handshake와 정상 쿠키 인증, 미인증 클라이언트 차단, 설정 버튼 존재를 검사합니다. 이 작업 환경에는 ARM64 Android 기기가 없어 **컴파일만 했고 실행하지 않았습니다**. 실제 휴대폰 X11 화면 출력, IME·터치·마우스, 화면 꺼짐, 최소화, OS 종료 후 복원은 검증 대기입니다. APK 정적 검사는 ARM64 ABI와 모든 ELF의 16 KiB 페이지 정렬을 확인합니다. 별도 Debian 13 amd64 환경에서 실제 apt XFCE 설치, 체크박스 TUI 및 중복 설치, Xvfb의 X11 연결과 Xfwm4 창 관리자 소유권을 확인했습니다. Linux GUI 테스트는 배포판에 UID 1000 사용자를 등록하고 일반 사용자로 실행했습니다. 이 결과는 Android 렌더러 실기기 결과와 구분합니다.

원본 라이선스와 수정 사항은 `third_party/NOTICE.md`, `android/desktop-x11/UPSTREAM-LICENSE`, 각 소스 아카이브에 보관합니다. 서버의 화면과 클라이언트 프로그램은 실제 X11 프로토콜로 통신합니다.
