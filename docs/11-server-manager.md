# 11. Python·Node.js 서버

Linux/WSL에서 다음을 실행할 수 있습니다.

```bash
binux server create http-demo --kind python --port 8000
binux server create node-demo --kind node --port 3000 --restart-on-failure
binux server start http-demo
binux server logs http-demo
binux server stop http-demo
```

Python은 실제 ThreadingHTTPServer, Node는 실제 node:http 서버입니다. 기본 listen은 127.0.0.1이고 템플릿을 LAN에 공개하려면 --listen 주소와 --allow-network를 함께 지정해야 합니다. 설정된 포트와 실제 listen 성공은 구분합니다. 시작 요청은 프로세스 시작일 뿐이며 로그/HTTP 요청으로 listen을 확인해야 합니다.

```bash
python3 -m venv my-app/.venv
my-app/.venv/bin/python -m pip install flask fastapi uvicorn
binux server add api --cwd /absolute/my-app --port 8000 -- /absolute/my-app/.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
binux server start api
```

Express는 사용자 프로젝트에서 `npm install express` 후 node 명령을 등록합니다. 사용자 등록 명령의 listen 주소는 해당 프로그램이 제어하며 binux는 방화벽/샌드박스로 임의 코드를 통제하지 않습니다. 자동 포트 탐지와 브라우저 내부 미리보기는 아직 없습니다. localhost 주소를 일반 브라우저에서 여세요. Android server manager도 실제 argv를 실행하지만 Python/Node 자체가 APK에 없으므로 해당 실행은 아직 미지원입니다.
