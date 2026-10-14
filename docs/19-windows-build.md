> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 19. Windows 앱 빌드

```powershell
dotnet restore windows -r win-x64
dotnet publish windows -c Release -r win-x64 --self-contained false -o artifacts/windows
.\artifacts\windows\binux.exe
.\artifacts\windows\binux.exe version
```

.NET 10 Desktop Runtime과 Microsoft WebView2 Runtime이 필요합니다. publish 폴더 전체에 exe/dll/runtimeconfig, WebView2Loader 및 local assets를 포함해 배포합니다. xterm 관련 소스 및 MIT license도 포함합니다. 웹 네트워크/CDN 없이 local virtual-host page를 로드합니다.

실제 ConPTY의 입력/output pipe를 xterm Uint8Array와 WebView2 JSON으로 연결합니다. keyboard bytes/resize는 ConPTY로 전달합니다. tabs/split, font/theme 설정 저장, clipboard shortcut, search를 제공합니다. PowerShell은 Windows native이며 WSL 선택에서만 `wsl.exe --exec /bin/bash -i`를 실행합니다. 기본 WSL 배포판은 사용자가 별도 설치해야 하고 binux가 관리자 권한을 획득하지 않습니다.

Child process는 suspended로 생성해 kill-on-close Job Object에 붙인 후 실행합니다. Close/Stop은 child tree를 종료합니다. Windows UI 종료 뒤 해당 탭을 백그라운드 서비스로 유지하는 기능 및 세션 자동 복원은 아직 없습니다. WSL의 독립 host supervisor를 사용할 수 있습니다. native binux 명령은 현재 help/version/info/doctor/lang/storage info/settings list만 제공합니다.

Windows 10 1809+/11 실행, ConPTY pipe shutdown, WebView2 input/IME 및 Job Object 동작은 실제 Windows에서 검증해야 합니다. [Microsoft ConPTY 문서](https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session)를 확인하고 구현했습니다.
