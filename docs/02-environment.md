> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 2. 개발 환경

| 플랫폼 | 고정 버전 / 조건 |
|---|---|
| Android 빌드 | Linux x86_64, JDK 21, Gradle 8.11.1, AGP 8.9.3 |
| Android 언어/UI | Kotlin 2.1.20, Compose BOM 2025.04.01 |
| Android SDK | compile/target 35, min 26, Build Tools 35.0.0 |
| Android NDK | 27.2.12479018 / CMake 3.22.1 |
| 저장 | Room 2.7.1, DataStore 1.1.5 |
| Windows | .NET SDK 10, net10.0-windows / win-x64 |
| 터미널 | Termux v0.118.0, xterm.js 5.5.0 |
| 호스트 | Python 3.11+, cryptography 43–50, 선택형 Node.js |

이 작업 환경에서는 `/workspace/.binux-tools/env.sh`를 source하면 준비된 도구를 사용할 수 있습니다. 이 경로는 빌드 소스에 필수 경로로 넣지 않았습니다. 다른 개발 환경에서는 Android Studio SDK Manager 및 .NET 공식 설치기를 사용하세요. 루팅이나 관리자 권한을 가진 앱을 요구하지 않습니다.
