# 7. Linux 런타임과 실제 패키지

Android 기본 실행은 APK Bash입니다. Debian/Ubuntu는 선택형 ARM64 Linux VM으로
설치하며 각각의 커널·initrd·10 GiB 확장 디스크를 고정 SHA-256으로 검증합니다.
앱 UID로 동작하는 QEMU와 게스트의 root 권한을 구분합니다. Android 12+이 필요합니다.

```bash
binux runtime install debian
binux runtime use debian
pkg update
pkg install python3 nodejs npm git openssh-client
apt install python3-venv
pip install flask fastapi uvicorn
npm install express
binux shell
```

pkg는 선택한 게스트의 apt 호환 명령이며 Android-native 패키지 저장소를 흉내내지
않습니다. pip는 ~/.venv를 만들고 Python도 이를 우선 사용합니다. 프로젝트별 venv는
사용자가 따로 만들 수 있습니다. apt는 배포판 서명을 검증하고 오류를 그대로 반환합니다.
설치/다운로드에 기기 저장공간을 실제 사용합니다. RAM/디스크 부족은 실패 처리합니다.

엔진 소스·정확한 의존성·교차 빌드 절차는 third_party/vm 및 scripts/build-android-vm.sh에,
서명된 배포판에서 이미지를 만드는 과정은 scripts/build-runtime-image.sh에 있습니다.
Android DNS는 고정 공용 DNS로 우회하지 않고 공개 Android DnsResolver API에 연결합니다.

Linux/WSL 도구에는 기존 PRoot rootfs 등록 어댑터도 남아 있습니다. 이는 완전한 커널이나
실제 root 권한을 제공하지 않습니다. Android VM과 같은 실행 엔진으로 소개하지 않습니다.
