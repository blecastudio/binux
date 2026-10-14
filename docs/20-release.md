# 20. GitHub / Release 배포

검증된 실제 원격: https://github.com/blecastudio/binux.git (public, 기본 branch main, 작업 시작 시 commits 없음). 이 작업에서는 push/Release 게시를 실행하지 않았습니다. 로컬 artifacts는 debug/experimental 검증용입니다.

게시 준비 순서:

1. STATUS.md의 미완성/기기 미검증 표시를 유지한 채 소스와 라이선스를 검토합니다.
2. Android ARM64/Windows 실제 테스트와 요구사항 검증표를 업데이트합니다.
3. 개인키/인증서/로컬 데이터가 git diff에 없는지 확인합니다. artifacts 및 user data는 커밋하지 않습니다.
4. 빈 원격의 initial commit과 main branch를 소유자가 게시합니다. 이미 원격에 커밋이 생겼다면 먼저 fetch하고 합칩니다.
5. build.yml은 artifact만 생성합니다. workflow가 release를 자동 게시하지 않습니다.
6. Android release APK를 자신의 keystore로 서명하고 Windows publish 폴더 전체를 ZIP으로 만듭니다. 필요 시 Authenticode 서명을 별도로 적용합니다.
7. APK/ZIP/source archive/NOTICE/LICENSE/SHA256SUMS와 실제 호환성 기록을 0.1.0 experimental Release에 첨부합니다.

공식 보조 패키지 배포:

- 일반 apt/pip/npm과 분리된 Release asset을 생성합니다.
- 각 archive의 SHA-256과 실제 GitHub API browser_download_url을 사용해 binux-addons.json을 생성합니다. 아직 존재하지 않는 URL을 적지 않습니다.
- 매니페스트 package 필드는 name/version/url/sha256/platform/arch/dependencies와 선택 signature입니다. Ed25519 서명은 14-addons.md의 canonical JSON을 따릅니다. 개인키는 CI secret 또는 별도 서명 장치에 두고 로그에 출력하지 않습니다.
- 공개키는 독립된 신뢰 경로로 공지합니다. 같은 공격자가 교체할 수 있는 archive와 checksum만을 완전한 출처 인증이라고 부르지 않습니다.
- scripts/install-addon.sh를 실제 asset으로 게시하고 URL 접근/내용/해시를 확인한 뒤에만 공식 `bash <(curl -Lf 실제_URL)` 설치 명령을 안내합니다.

현재 공식 다운로드 URL과 installer URL은 **미발행**입니다. 실제 저장소가 존재하는 것과 공식 패키지/스크립트가 이미 배포된 것은 구분합니다. GPL 대응 소스 전체(수정한 Termux, Bash/xterm source archives, 빌드 스크립트)를 바이너리와 함께 배포합니다.
