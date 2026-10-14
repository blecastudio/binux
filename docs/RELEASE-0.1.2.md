binux Android 0.1.2 및 별도 Binux Desktop:X11 0.1.0 개발용 미리보기입니다.

- 기존 입력 포커스 수정 유지. 툴바 숨김, 전체화면, 화면 켜짐 유지와 숨김 상태 설정 버튼.
- 프로젝트 소유자가 제공한 앱별 로고 적용.
- 별도 ARM64 X.Org X11 서버·JNI 화면 앱, own-package Foreground Service, localhost 및 인증 쿠키, 같은 서명키 credential Provider.
- 지원되는 Debian/Ubuntu에서 실제 apt로 XFCE를 설치하는 선택형 Bash 설치기.

설치 명령:

```bash
bash <(curl -Lf https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop)
```

**현재 Android Native APK에는 Debian/Ubuntu 실행 엔진이 없습니다. Android에서 설치기는 이 사유를 설명하고 종료 코드 69를 반환합니다. X11 APK만으로 XFCE를 실행할 수 없습니다.** Linux/WSL 배포판에서 설치기를 사용하세요. Chrome 자동 설치, Android GUI/터치/최소화/화면 꺼짐 검증은 완료하지 않았습니다.

검증: 두 APK 빌드, Lint 오류 0, Android 입력 회귀 6개 통과, ARM64/16 KiB 정렬, Linux 호스트 36개 테스트, Debian 실제 XFCE 설치 및 Xvfb에서 Xfwm4 창 관리자 실행. Android X11 인증 기기 테스트는 컴파일만 했고 실기기에서 실행하지 않았습니다.

두 APK는 같은 개발용 debug 인증서로 서명했습니다. 운영 배포용 서명이 아닙니다. 다운로드 파일은 SHA256SUMS로 확인하세요. 대응 소스 및 서드파티 소스/라이선스는 이 태그의 Source code에서 함께 받으세요. 빌드와 사용법: docs/DESKTOP-X11.md.
