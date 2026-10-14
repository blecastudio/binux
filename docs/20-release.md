# 20. GitHub / Release 배포

공식 저장소는 https://github.com/blecastudio/binux 입니다. 설치 스크립트는 실제 main의
setup-binux-desktop이며 APK의 installer-manifest.json에 검토한 SHA-256을 넣습니다.
검토 후 스크립트가 바뀌면 APK도 새 해시로 빌드해야 합니다.

1. NDK Bash/VM 및 X11 소스 준비, 단위/통합/린트, Windows publish를 완료합니다.
2. Linux 이미지 workflow로 Debian/Ubuntu를 서명된 저장소에서 만들고 실제 커널 부팅,
   SSH/UID/공유 홈/pkg/pip/npm을 검사합니다. 부팅 실패 이미지는 발행하지 않습니다.
3. 대응 소스·패키지 버전·커널·initrd·qcow2를 immutable runtime-SHA Release에 올립니다.
4. 발행된 manifest.json을 검증해 Android assets/runtime-manifest.json에 고정합니다.
   runtime SHA와 asset 크기/해시/공식 Release URL을 확인한 뒤 APK를 다시 빌드합니다.
   `python3 scripts/pin-runtime.py <발행된 runtime-SHA Release의 manifest.json URL>`을
   사용하세요. 검증 이미지가 없으면 Gradle이 배포판 설치가 불가능한 APK 빌드를 거부합니다.
5. scripts/build-addons.py에 외부 보관한 Ed25519 개인 키를 주어 data/source add-on을
   서명합니다. 개인 키는 git/Release/로그에 올리지 않습니다. 공개 키만 core/binux/trust.py에
   포함합니다. 일반 패키지 apt/pip/npm은 별도 신뢰 체계입니다.
6. APK 두 개, 전체 Windows publish ZIP, 서명 add-on 및 SHA256SUMS를 downloads에
   준비합니다. v1.0.0 태그 workflow가 검증 후 개발 프리뷰 Release를 만듭니다.

기존 APK와 같은 서명을 유지해야 데이터 보존 업데이트가 됩니다. 현재 개발 서명을
production 보안 서명으로 소개하지 않습니다. Android/Windows 실기기 및 배터리/OEM
검증이 끝나기 전에는 stable 기능 검증 완료라고 표시하지 않습니다.

모든 바이너리에 LICENSE/third_party/NOTICE 및 대응 소스를 함께 제공합니다.
런타임 이미지의 Debian/Ubuntu 대응 소스는 해당 runtime Release의 별도 tar 자산입니다.
QEMU/GLib/Bash/X.Org/SSH 전체 소스와 수정 패치는 프로젝트 소스 아카이브에 있습니다.
