# 15. 선택형 Desktop 설치와 X11

```bash
binux desktop source
binux desktop install
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
binux desktop start
binux desktop stop
binux desktop status
binux desktop update
binux desktop uninstall
```

공식 URL은 BlecaStudio의 실제 저장소입니다. Android 다운로드 어댑터는 APK에서
검토한 SHA-256과 다르면 실행 전에 실패합니다. source 명령으로 출처·해시를 확인합니다.
CLI 체크박스는 실제 XFCE apt 패키지와 파일 관리자/편집기/오디오/개발 도구/Chromium/
WBS CLI 실행기를 선택합니다. 패키지 확인 후 설치 기록을 쓰고 이미 있던 패키지는
제거 소유 목록에서 제외합니다. 사용자의 프로젝트 파일을 지우는 제거 훅은 없습니다.

Desktop:X11 APK의 실제 X.Org 서버는 loopback에서 Xauthority 인증을 사용합니다.
같은 서명의 앱만 read-only Provider로 쿠키를 받을 수 있습니다. 인증 정보는 공유 홈 밖의
VM bootstrap에 두고 GUI 앱은 DISPLAY=10.0.2.2:1로 접속합니다. 설정 충돌을 일으킨
보호 메서드 reflection은 제거했으며 API34/35 회귀 테스트를 추가했습니다.

툴바/보조 키/전체화면은 앱마다 저장합니다. 툴바를 숨겨도 설정 복구 버튼을 제공합니다.
ARM64 Linux Chrome은 공식 호환 패키지가 없어 설치하지 않고 Debian Chromium 또는
Android Chrome 실행을 선택하게 합니다. --no-sandbox를 사용하지 않습니다.
오디오는 선택 설치 후 `binux desktop audio start|stop|status`로 제어합니다.
PulseAudio PCM → 인증된 SSH → Android AudioTrack 경로를 사용합니다.
X11 표시/터치/오디오·절전 성능은 Android 실기기 검증 전입니다.
