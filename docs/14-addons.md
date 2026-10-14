> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 14. BlecaStudio 공식 보조 패키지

공식 저장소 [blecastudio/binux](https://github.com/blecastudio/binux)의 존재와 쓰기 가능한 Git remote를 확인했습니다. 아직 원격 commits/Release/설치 스크립트 asset이 없으므로 실제 공식 설치 URL을 제공하지 않습니다.

호스트 `Addons`는 설정한 실제 BlecaStudio 저장소의 최신 Release에서 binux-addons.json을 읽습니다. asset URL은 같은 저장소의 releases/download 경로로 제한합니다. 다운로드 진행률, 버전, ABI/platform, 의존성 검사, SHA-256, 선택형 Ed25519, staging/rollback, update/remove를 지원합니다. install hooks는 자동 실행하지 않습니다. 설치 파일은 실제 local addons 디렉터리에 저장합니다.

```bash
# 실제 저장소 존재 여부를 API로 확인한 뒤 설정:
binux settings set official_repo blecastudio/binux
binux addon list
binux addon search desktop
binux addon info desktop
binux addon install desktop
binux addon update
binux addon remove desktop
```

지금 install은 Release 부재로 실패하는 것이 정상입니다. Ed25519 키를 설정하면 서명이 없거나 잘못된 패키지는 거부합니다. 키 미설정 시 SHA-256+HTTPS만 검증한다고 명확히 안내하며 hash를 publisher 서명이라고 부르지 않습니다. 서명 대상은 name/version/sha256/url/platform/arch/dependencies의 sort_keys=True, separators=(",",":") JSON UTF-8 바이트입니다. 독립된 신뢰 경로로 배포한 공개키를 base64로 addon_ed25519_key에 저장합니다.

매니페스트 형식:

```json
{"schema":1,"packages":[]}
```

빈 목록은 실제로 사용 가능한 초기 매니페스트입니다. 패키지 URL과 checksum은 Release asset을 실제로 올린 뒤 생성해야 합니다. scripts/install-addon.sh는 게시 준비용 진입점입니다. 공식 asset이 존재하기 전 `bash <(curl -Lf URL)` 명령을 만들어 제시하지 않습니다. Android 앱에는 add-on 설치 transport를 아직 통합하지 않았습니다.
