# binux 1.0.0 + Binux Desktop:X11 1.0.0 — development preview

실제 Android Bash/PTY에 선택형 Debian/Ubuntu VM을 추가했습니다. VM 엔진은 APK에
포함하고 Linux 커널/디스크는 SHA-256을 확인한 데이터로 설치합니다. pkg/apt, Python
venv/pip, Node/npm, Git/SSH와 XFCE 설치기를 선택한 배포판에 연결합니다.

Desktop:X11 설정 화면의 보호 메서드 reflection 충돌을 수정했습니다. API34/35에서
기존 충돌을 재현한 뒤 모든 설정 카테고리 테스트가 통과했습니다. 첫 홈 프롬프트는
~/로 표시하고 툴바/전체화면 설정 및 원본 로고를 유지합니다.

서버는 loopback + SSH 포트로 연결하고 물리 LAN 공개에는 --allow-network가 필요합니다.
작업 종료/로그/복원 메타데이터, 사용자 선택 재부팅 작업, 선택형 SSH PCM 오디오,
WBS mTLS 전송, 서명 add-on과 Windows WSL 명령 전달을 포함합니다.

APK 2개는 같은 기존 개발 서명이며 업데이트 설치 시 앱 데이터를 유지합니다.
Windows ZIP은 전체 폴더를 풀어 .NET10 Desktop Runtime/WebView2와 사용하세요.
런타임 하나에 10 GiB 디스크 확장 여유와 기본 1024 MiB RAM이 필요합니다.

**Android/Windows 실기기 실행은 아직 검증하지 않았습니다.** 특히 Android VM/JIT,
최소화·화면 꺼짐·부팅 재시작·X11 표시·AudioTrack 출력은 기기 검증 대상입니다.
24시간 실행을 보장하지 않습니다. WBS 파일 한도는 16 MiB, sync는 단방향이며 화면
공유는 없습니다. Chrome은 공식 amd64/ARM64 저장소와 샌드박스 실행 검사 결과에 따라
설치/기본 브라우저 지정을 처리하며, Ubuntu snap은 자동 구성하지 않습니다.

Debian/Ubuntu ARM64 VM에서 실제 pkg/apt·pip·npm 설치, Flask/FastAPI/Express HTTP 응답과
종료, XFCE/xfwm4 실행 검사가 통과했습니다. Google Chrome도 두 배포판에서
샌드박스를 켠 headless 실행에 통과했습니다. Android 화면 렌더링 검증과는 구분합니다.

[설치·명령어 안내](https://github.com/blecastudio/binux/blob/main/docs/RUNTIME-1.0.md) ·
[실제 검증 범위](https://github.com/blecastudio/binux/blob/main/docs/STATUS.md)
