# 3. 프로젝트 구조

```text
binux/
  android/                  Gradle wrapper, Compose Android app
    app/src/main/           Kotlin/Java, Manifest, 언어 리소스, Bash rc
    app/src/androidTest/    ARM64 실기기용 테스트
    app/src/test/           API34/35 IME 회귀, 셸 인자, SSH host key 검사
    desktop-x11/           별도 X.Org APK, 설정 UI와 API34/35 회귀 검사
  native/                   JNI 프로세스 제어, binuxctl, setsid launcher
  core/binux/               Linux/WSL CLI와 supervisor, runtime, packages, WBS, Desktop
  windows/                  WinForms, ConPTY, WebView2, local xterm assets
  runtime/                  게스트 초기화/세션 준비, 서명 키링, add-on 소스
  third_party/              Bash/QEMU/GLib/X.Org/Termux/xterm 소스·패치·라이선스
  tests/                    호스트 통합 및 보안 테스트
  scripts/                  Bash/VM 교차 빌드, 이미지 생성/부팅 검사, 서명/해시 검사
  setup-binux-desktop       검토한 공식 XFCE 설치 스크립트
  downloads/1.0/            APK/Windows ZIP/서명 add-on 및 SHA256SUMS
  docs/                     20개 산출물 및 실제 지원 범위
  .github/workflows/        빌드/테스트, 런타임 이미지/Chrome 검증, Release 발행
  artifacts/                로컬 빌드 결과/로그 (git에서 제외)
```

각 실제 파일 경로와 역할은 SOURCE-CATALOG.md에 있습니다. 빌드 디렉터리, 사용자 키, 로컬 캐시, APK 서명키를 저장소에 커밋하지 않습니다.
