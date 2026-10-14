# 15. binux Desktop 설치기

Desktop은 초기 APK/Windows 실행 파일에 설치하거나 실행하지 않습니다. 호스트 PRoot 배포판에 대해서만 선택형 XFCE/TigerVNC 설치기를 구현했습니다.

```bash
binux desktop --runtime debian install
binux desktop --runtime debian start
binux desktop status
binux desktop stop
binux desktop update
binux desktop uninstall
```

번호로 [x]/[ ] 체크박스를 전환하는 CLI TUI가 Chrome, 파일 관리자, Mousepad 코드 편집기, WBS integration, PulseAudio, 개발 도구를 선택합니다. 미지원 WBS Desktop integration을 선택하면 설치 전에 실패합니다. apt 설치/업데이트가 실패하면 성공을 저장하지 않습니다. 이미 존재한 패키지는 Desktop 소유로 기록하지 않으며 uninstall은 새로 설치한 명시적 패키지만 제거하고 home을 유지합니다. 설치기 소스는 완성되었으나 이 세션에서는 GUI 패키지 설치 및 화면 실행을 검증하지 않았습니다.

VNC는 localhost, VncAuth, 사용자가 입력한 정확히 8 ASCII 글자 비밀번호를 요구합니다. -SecurityTypes None/0.0.0.0 VNC를 기본값으로 쓰지 않습니다. 원격 연결은 별도의 검증된 TLS/SSH 터널을 사용해야 합니다. 비밀번호 및 개인키를 로그에 출력하지 않습니다.

Google Chrome을 기본 선택으로 표시하되 ARM64 또는 PRoot sandbox 호환성을 확보할 수 없으면 설치하지 않습니다. Chromium(샌드박스 유지) 또는 브라우저 제외를 사용자가 선택할 수 있고, 선택하지 않으면 중단합니다. Chromium도 PRoot에서 실행될 것을 보장하지 않습니다. Chrome이 실제 호환된다고 검증된 native/WSL 설치 어댑터는 아직 없으므로 자동 Chrome 설치를 제공하지 않습니다. Android Chrome handoff, Android VNC/X11 renderer, touch/virtual mouse/zoom/audio device routing은 후속 통합 대상입니다. PulseAudio 패키지 설치는 오디오가 Android에서 들린다는 뜻이 아닙니다.
