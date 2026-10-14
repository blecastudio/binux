package studio.bleca.binux

class CommandRouter(private val service: BinuxRuntimeService) {
 data class Result(val code: Int, val text: String)
 private val help=mapOf(
  "binux" to "binux help | version | info | doctor | update | lang | bg | server | storage | settings | addon | desktop | wbs",
  "lang" to "binux lang list | show | set <ko|en>",
  "bg" to "binux bg status | list | enable | disable | run [--restart-on-failure] <command> [args...] | logs <job-id> | stop <job-id> | restart <job-id> | resume | autostart <on|off>",
  "server" to "binux server add <name> <port> <cwd> <command> [args...] | list | start <name> | stop <name> | logs <name> | restart-policy <name> <on|off>",
  "storage" to "binux storage info | clean",
  "settings" to "binux settings list | set <font|cursor|theme|toolbar|extra-keys|fullscreen|keep-screen-on> <value>",
  "addon" to "binux addon list | search <name> | info <name> | install <name> | update | remove <name>",
  "desktop" to "binux desktop install | start | stop | status | update | uninstall | installer | x11 <open|auth>",
  "wbs" to "wbs <windows|android> <IP> | status | devices | pair | disconnect | share <path> | sync <path> | logs | help"
 )
 fun execute(args: List<String>): Result {
  val runtime=service.runtime; val settings=service.settings
  val a=args.ifEmpty { listOf("help") }; val group=a[0]
  if(group in listOf("help","--help") || a.getOrNull(1) in listOf("help","--help") || a.getOrNull(2)=="--help") {
   return Result(0,settings.message("사용법:\n","Usage:\n")+(help[group] ?: help["binux"]))
  }
  return try {
   val text=when(group) {
    "version" -> "binux ${BuildConfig.VERSION_NAME}"
    "info" -> "binux ${BuildConfig.VERSION_NAME} / BlecaStudio\nRuntime: Native Bash / Android kernel\nDesktop: not installed\n${runtime.storage.base}"
    "doctor" -> runtime.doctor()
    "update" -> error(settings.message("공식 Release 저장소가 아직 설정되지 않았습니다. APK 업데이트가 필요합니다.","Official Release repository is not configured; update the APK."))
    "lang" -> when(a.getOrNull(1)) {
     "list" -> "ko: 한국어 (ko-KR)\nen: English (en-US)"
     "show" -> settings.language
     "set" -> { require(a.getOrNull(2) in listOf("ko","en")); settings.set("lang",a[2]); service.notifyTasks(); settings.message("한국어 설정 저장됨. 앱을 다시 열면 적용됩니다.","Language saved; reopen the UI to apply.") }
     else -> error(help.getValue("lang"))
    }
    "bg" -> when(a.getOrNull(1)) {
     "status" -> "background=${settings.flag("background")} sessions=${service.sessions.sessions.count { it.isRunning }} jobs=${service.jobs.jobs.count { it.process.isAlive }}\n"+settings.message("Android는 작업을 종료할 수 있습니다. 알림 및 배터리 설정은 사용자가 승인해야 합니다.","Android may terminate tasks. Notification and battery settings require user approval.")
     "list" -> (service.jobs.jobs.map(service.jobs::describe)+service.jobs.history().map { "${it.id} ${it.state} pid=${it.pid} (restored metadata)" }).joinToString("\n").ifEmpty { settings.message("작업 없음","No jobs") }
     "enable" -> { settings.set("background",true); settings.message("백그라운드 허용 설정 저장됨. Android 권한은 변경하지 않았습니다.","Background preference saved. Android permissions are unchanged.") }
     "disable" -> { settings.set("background",false); settings.message("허용 설정 해제됨. UI를 떠나면 활성 작업을 종료합니다.","Disabled. Active tasks stop when you leave the UI.") }
     "run" -> { val restart=a.getOrNull(2)=="--restart-on-failure"; val j=service.jobs.run(a.drop(if(restart)3 else 2),restartOnFailure=restart); service.jobs.describe(j) }
     "logs" -> service.jobs.logs(a[2])
     "stop" -> { service.jobs.stop(a[2]); "Stop requested ${a[2]}" }
     "restart" -> service.jobs.describe(service.jobs.restart(a[2]))
     "resume" -> { service.jobs.resumeAll(); "Jobs resumed" }
     "autostart" -> { require(a.getOrNull(2) in listOf("on","off")); check(a[2]=="off") { "Reboot autostart unavailable in 0.1.0; no boot receiver is installed" }; settings.set("autostart",false); "autostart: off" }
     else -> error(help.getValue("bg"))
    }
    "server" -> when(a.getOrNull(1)) {
     "list" -> service.servers.list()
     "add" -> service.servers.register(a[2],a[3].toInt(),a[4],a.drop(5))
     "start" -> service.servers.start(a[2])
     "stop" -> service.servers.stop(a[2])
     "logs" -> service.servers.logs(a[2])
     "restart-policy" -> { require(a.getOrNull(3) in listOf("on","off")); service.servers.restartPolicy(a[2],a[3]=="on") }
     else -> error(help.getValue("server"))
    }
    "storage" -> when(a.getOrNull(1)) { "info" -> runtime.storage.info(); "clean" -> runtime.storage.clean(); else -> error(help.getValue("storage")) }
    "settings" -> when(a.getOrNull(1)) {
     "list" -> "font=${settings.text("font","28")} cursor=${settings.text("cursor","0")} theme=${settings.text("theme","dark")} background=${settings.flag("background")} toolbar=${settings.flag("toolbar",true)} extra-keys=${settings.flag("extra-keys",true)} fullscreen=${settings.flag("fullscreen")}"
     "set" -> { val key=a[2]; val value=a[3]; require(when(key) { "font" -> value.toIntOrNull() in 14..72; "cursor" -> value in listOf("0","1","2"); "theme" -> value in listOf("dark","light"); "toolbar","extra-keys","fullscreen","keep-screen-on" -> value in listOf("on","off"); else -> false }) { "Invalid setting" }; if(key in listOf("toolbar","extra-keys","fullscreen","keep-screen-on"))settings.set(key,value=="on") else settings.set(key,value); "Saved; reopen UI to apply" }
     else -> error(help.getValue("settings"))
    }
    "addon" -> when(a.getOrNull(1)) { "list" -> settings.message("설치된 공식 보조 기능 없음","No official add-ons installed"); else -> error(settings.message("BlecaStudio 공식 매니페스트 및 Release 저장소가 설정되지 않았습니다.","BlecaStudio official manifest and Release repository are not configured.")) }
    "desktop" -> DesktopManager(service).execute(a.drop(1))
    "wbs" -> when(a.getOrNull(1)) { "status","devices" -> "WBS: disconnected; Android transport unavailable in 0.1.0"; else -> error("Android WBS transport not integrated; use the host prototype documented in docs/13-wbs.md") }
    else -> error(settings.message("알 수 없는 명령어. binux help를 확인하세요.","Unknown command. See binux help."))
   }
   Result(0,text)
  } catch(e: Exception) { Result(1,settings.message("오류: ","Error: ")+(e.message ?: "Invalid arguments")) }
 }
}
