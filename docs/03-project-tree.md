# 3. 프로젝트 구조

```text
binux/
  android/                  Gradle wrapper, Compose Android app
    app/src/main/           Kotlin/Java, Manifest, 언어 리소스, Bash rc
    app/src/androidTest/    ARM64 실기기용 테스트
  native/                   JNI 프로세스 제어, binuxctl, setsid launcher
  core/binux/               Linux/WSL CLI와 supervisor, runtime, packages, WBS, Desktop
  windows/                  WinForms, ConPTY, WebView2, local xterm assets
  third_party/              Termux 소스, Bash 및 xterm 전체 소스 압축본/라이선스
  tests/                    호스트 통합 및 보안 테스트
  scripts/                  Bash 교차 빌드, APK 검사, 테스트, add-on 설치 진입점
  docs/                     20개 산출물 및 실제 지원 범위
  .github/workflows/        빌드/테스트 workflow (게시 없음)
  artifacts/                로컬 빌드 결과/로그 (git에서 제외)
```

각 실제 파일 경로와 역할은 SOURCE-CATALOG.md에 있습니다. 빌드 디렉터리, 사용자 키, 로컬 캐시, APK 서명키를 저장소에 커밋하지 않습니다.
