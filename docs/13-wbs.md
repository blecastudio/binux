# 13. WBS 프로토콜과 연결

구현 파일: core/binux/wbs.py. **현재 Linux/WSL 호스트 프로토타입이며 Android 앱/Windows 앱 transport는 통합되지 않았습니다.** `windows`와 `android`는 연결 대상 표시이고, 상대 OS 지원을 입증하는 이름이 아닙니다.

WBS v1은 TLS 1.3과 기기별 ECDSA self-signed 인증서, 정확한 SHA-256 인증서 지문 pinning, mTLS를 사용합니다. 페어링은 신뢰할 수 있는 방법으로 공개 인증서만 교환하고 양쪽에서 지문 확인 후 승인합니다. 개인키는 교환하지 않습니다. 무인 최초 승인이나 암호화 없는 최초 연결은 없습니다.

```bash
# 각 기기에서. 실제 LAN IP를 인증서 SAN에 넣습니다.
wbs init --ip 192.168.0.15
# 상대의 PUBLIC identity.pem만 로컬로 전달한 뒤 각 기기에서:
wbs pair /absolute/peer-identity.pem --name phone --share project=/absolute/approved-folder
# 상대에서도 내 인증서를 승인해야 합니다.
wbs serve --bind 192.168.0.15 --allow-network
# 클라이언트에서 상대 인증서를 승인한 이름을 선택:
wbs windows 192.168.0.15 --peer pc
wbs status
wbs share /absolute/file --remote-share project
wbs sync /absolute/folder --remote-share project --overwrite
wbs disconnect
wbs revoke pc
```

서버 기본 bind는 127.0.0.1이고 LAN 노출은 --allow-network를 요구합니다. `wbs windows 127.0.0.1`은 현재 기기 자신이라는 설명을 출력합니다. IP 주소는 예시 LAN 주소이며 공식 URL이 아닙니다. 각 인증서 SAN과 실제 IP가 일치해야 합니다.

JSON line 프레임은 최대 24 MiB, 파일 최대 16 MiB입니다. info/get/put/hash/exec가 구현되어 있습니다. 파일은 허용 share 아래 상대 경로만 사용하고 SHA-256을 검사합니다. POSIX openat/dir_fd/O_NOFOLLOW로 symlink 및 경로 바꿔치기를 차단합니다. 업로드는 atomic link/replace하며 덮어쓰기는 --overwrite로 선택합니다. sync는 선택 폴더의 한 방향 수정 파일 전송이며 양방향 충돌 해결/원격 삭제 기능이 아닙니다.

pair --commands에는 허용된 정확한 argv 배열 목록을 담은 JSON 파일을 지정할 수 있습니다. exec는 목록에 정확히 일치할 때만 shell 없이 15초 한도로 실행합니다. 임의 root/관리 명령 권한을 제공하지 않습니다. 로그는 시각, 지문 일부, operation만 기록합니다. revoke는 새 요청부터 차단하며 disconnect는 선택한 endpoint를 지웁니다. 지속 연결이 없으므로 status는 지금의 연결 가능 여부를 새로 검사합니다.

포트 포워딩, 화면 공유, 데스크톱 원격 조작은 미구현이며 미지원 상태를 반환합니다. Windows 네이티브 프로그램을 Android에서 실행하는 기능도 없습니다. TLS 해제, --insecure, 공유 전체 홈 디렉터리 같은 기본 설정을 넣지 않았습니다.
