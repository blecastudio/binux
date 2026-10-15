# binux 1.0.0 개발 프리뷰

Android ARM64용 binux와 Desktop:X11 APK는 같은 기존 개발 서명입니다.
기존 앱을 삭제하지 않고 두 APK를 업데이트 설치하면 앱 데이터가 유지됩니다.
Native Bash는 Android 8 이상, 선택형 Linux VM은 Android 12 이상이 필요합니다.
Android 실기기와 Windows UI 실행 검증은 아직 완료하지 않았습니다.

```bash
adb install -r binux-1.0.0-android-arm64-debug.apk
adb install -r binux-desktop-x11-1.0.0-android-arm64-debug.apk
```

앱 터미널에서:

```bash
binux runtime install debian
binux runtime use debian
pkg update
pkg install python nodejs npm git openssh-client
pip install flask fastapi uvicorn
binux desktop source
binux desktop install
binux bg enable
binux desktop start
```

Ubuntu도 `binux runtime install ubuntu`로 설치할 수 있습니다. 배포판마다 10 GiB
디스크 확장 여유와 기본 1024 MiB RAM이 필요합니다. 기본 설치에는 Desktop이 없습니다.
Google Chrome은 공식 서명 저장소 및 기본 샌드박스 실행 검사 결과에 따라 처리합니다.
다른 기기에 서버를 공개하려면 --allow-network를 명시해야 합니다.

Windows ZIP 전체를 풀고 binux.exe를 실행하세요. .NET 10 Desktop Runtime과
WebView2 Runtime이 필요합니다. Linux 도구는 선택한 WSL 배포판에 설치합니다.

SHA256SUMS로 파일을 확인하세요. 공식 add-on은 SHA-256과 Ed25519도 검증합니다.
전체 소스·구성요소 라이선스·이미지 출처·실제 검증 범위는 같은 저장소의
README.md, docs/RUNTIME-1.0.md, docs/STATUS.md를 확인하세요.
