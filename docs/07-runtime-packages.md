# 7. Linux Runtime 및 패키지

Android 0.1.0에는 APK에 포함한 Bionic ARM64 Bash와 Android 시스템 명령이 있습니다. Python, Node.js, Git, SSH 및 PRoot는 아직 APK에 포함되지 않습니다. native pkg 저장소도 아직 제공하지 않습니다. apt/pkg 미지원 상황은 실패 코드로 설명합니다.

Linux/WSL 호스트에서는 기존 Python/Node/Git/SSH를 실행하며, 미설치 실행파일은 실제 오류로 처리합니다. `binux package pip ...`, `binux package npm ...`은 해당 호스트 런타임에 전달합니다. pip는 프로젝트 venv에서 실행하는 것이 기본 운영 방식입니다.

```bash
binux runtime register debian /absolute/path/to/debian-rootfs --proot /absolute/path/to/proot
binux runtime exec debian /bin/bash -c 'uname -a; id; cat /etc/os-release'
binux package --runtime debian apt update
binux package --runtime debian apt install python3 nodejs git openssh-client curl
```

이 환경의 기존 Debian 13 amd64 RootFS에서 어댑터를 통해 Bash와 apt-get --version을 실제 실행했습니다(artifacts/runtime-smoke.log). 배포판 전체 설치/apt 다운로드 설치 및 Android PRoot는 별도 검증 대상입니다.

등록할 RootFS는 사용자가 신뢰할 수 있는 배포판 도구로 별도 생성해야 합니다. 현재 자동 RootFS 다운로드/설치기는 없습니다. RootFS의 os-release와 Bash를 검사합니다. PRoot는 격리 보안 경계가 아니며 호스트 /dev,/proc,/sys를 바인딩합니다. 관리자 명령을 안전하게 실행하는 샌드박스라고 소개하면 안 됩니다.

Android target 29+에서는 쓰기 가능한 앱 디렉터리의 execve가 제한됩니다. 그래서 일반 glibc RootFS의 apt 설치 결과를 Android에서 실행 가능하다고 주장하지 않습니다. 다음 단계에서는 정책을 준수하는 interpreter/정식 패키징 모델을 실제 기기로 검증해야 합니다.

검증 근거: [Android 실행파일 정책](https://developer.android.com/about/versions/10/behavior-changes-10).
