> 1.0.0 현재 구현·명령·검증 범위는 [1.0 안내](RUNTIME-1.0.md) 및 [상태표](STATUS.md)를 우선 확인하세요. 아래의 0.1.x 제한 설명은 초기 구현 당시의 기록입니다.

# 9. Android 백그라운드 서비스

`BinuxRuntimeService`는 사용자가 보이는 Activity에서 시작한 foreground service입니다. Manifest는 FOREGROUND_SERVICE 및 FOREGROUND_SERVICE_SPECIAL_USE, specialUse subtype 설명을 선언합니다. interactive PTY 및 명시적 local 개발 작업이 목적이며 dataSync를 일반 작업 유형으로 사용하지 않습니다.

알림은 실제 세션/작업/서버 개수, 현재 미지원 다운로드 0/WBS disconnected를 표시하고 열기, 작업 일시중지, 모든 작업 종료를 제공합니다. `binux bg resume`으로 작업을 재개합니다. 작업 종료는 TERM 이후 제한된 유예 시간 후 KILL을 보냅니다. bg disable은 UI를 떠날 때 작업을 종료하는 설정이고 시스템 권한을 얻지 않습니다.

알림 권한은 사용자 버튼으로 요청합니다. 배터리 설정 버튼은 시스템 앱 설정을 열며, 사용자가 제한 없음 여부를 결정합니다. 자동 배터리 예외 요청이나 지속 WakeLock을 사용하지 않습니다. Doze 및 제조사 제한으로 CPU/네트워크가 중지될 수 있습니다. START_NOT_STICKY이며 boot receiver나 강제 중지 우회 기능을 넣지 않았습니다. 마지막 로그/메타데이터는 복구할 수 있으나 실행 프로세스를 되살렸다고 표시하지 않습니다.

specialUse는 임의의 무제한 실행 보장이 아닙니다. Play 배포 시 실제 기능 설명과 서비스 유형 심사가 별도 필요합니다. [공식 서비스 유형 안내](https://developer.android.com/develop/background-work/services/fgs/service-types)를 확인했습니다.
