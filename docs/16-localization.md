> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 16. 한국어·영어

Android strings.xml과 values-ko/strings.xml에 최초 설정, 권한/배터리 안내, 알림, 작업 제어 라벨을 제공합니다. Settings.message로 binux 주요 오류/상태를 언어 설정에 맞춥니다. Bash 환영 문구는 BINUX_LANG를 사용합니다.

```bash
binux lang list
binux lang set ko
binux lang set en
binux lang show
```

설정은 재시작 후 유지합니다. Android 현재 세션의 환경/환영 문구는 새 세션부터 적용하며 UI는 다시 열면 적용됩니다. Windows 선택 언어와 font/theme은 AppSettings.json에 저장합니다. 호스트 CLI의 공통 오류 접두사와 Desktop/WBS 승인 안내를 번역했습니다. argparse 자체 영어 help, 일부 진단 기술 문자열, Windows 일부 툴바 라벨 및 상세 오류는 아직 전체 번역되지 않았습니다.

기존 Bash, apt, pip, npm, Python 등의 자체 출력은 번역하거나 수정하지 않습니다. ko-KR/en-US UI 선택과 Linux locale는 별개이며 Android Bash에는 C.UTF-8을 전달합니다. 한글 입력 검증은 host PTY에서 수행했고 Android IME는 실기기 검증 대기입니다.
