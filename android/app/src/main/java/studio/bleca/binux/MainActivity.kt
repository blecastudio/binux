package studio.bleca.binux

import android.Manifest
import android.content.*
import android.content.pm.PackageManager
import android.graphics.Typeface
import android.net.Uri
import android.os.*
import android.provider.Settings as SystemSettings
import android.view.*
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.termux.terminal.TerminalSession
import com.termux.view.TerminalView
import com.termux.view.TerminalViewClient
import kotlinx.coroutines.*

class MainActivity: ComponentActivity() {
 private var service by mutableStateOf<BinuxRuntimeService?>(null)
 private var error by mutableStateOf("")
 private var history by mutableStateOf<List<SessionRecord>>(emptyList())
 private var selectedSessionId by mutableStateOf<String?>(null)
 private var activeSessionId by mutableStateOf<String?>(null)
 private val activityScope=CoroutineScope(SupervisorJob()+Dispatchers.Main)
 private val views=mutableMapOf<String,TerminalView>()
 private var bound=false
 private var visible=false
 private val connection=object: ServiceConnection {
  override fun onServiceConnected(name: ComponentName?,binder: IBinder?) {
   val s=(binder as BinuxRuntimeService.RuntimeBinder).service
   service=s
   s.uiVisibility(visible)
   s.sessions.invalidate={ views.values.forEach { it.onScreenUpdated() } }
   runCatching {
    val selected=s.sessions.sessions.firstOrNull { it.mHandle==selectedSessionId && it.isRunning }
     ?: s.sessions.sessions.lastOrNull { it.isRunning }
     ?: s.sessions.create()
    selectedSessionId=selected.mHandle
    activeSessionId=selected.mHandle
   }.onFailure { error=it.message ?: "Cannot start Bash" }
   activityScope.launch { history=withContext(Dispatchers.IO) { s.database.sessions().history().filter { it.state=="interrupted" } } }
  }
  override fun onServiceDisconnected(name: ComponentName?) { service=null; views.clear() }
 }
 private fun connect() {
  if(bound)return
  val intent=Intent(this,BinuxRuntimeService::class.java)
  try { startForegroundService(intent); bound=bindService(intent,connection,Context.BIND_AUTO_CREATE) }
  catch(e: Exception) { error=e.message ?: "Service startup failed" }
 }
 override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  selectedSessionId=savedInstanceState?.getString("selectedSession")
  val settings=Settings(this)
  setContent {
   val dark=settings.text("theme","dark")=="dark"
   MaterialTheme(colorScheme=if(dark)darkColorScheme() else lightColorScheme()) {
    var configured by remember { mutableStateOf(settings.flag("configured")) }
    Surface(Modifier.fillMaxSize()) {
     if(!configured) Column(Modifier.padding(24.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
      Text(getString(R.string.setup),style=MaterialTheme.typography.headlineSmall)
      Text(getString(R.string.battery))
      var background by remember { mutableStateOf(false) }
      Row { Checkbox(background,{background=it}); Text("Allow background tasks / 백그라운드 작업 허용") }
      listOf("ko" to "한국어", "en" to "English").forEach { (code,label) ->
       Button(onClick={ settings.set("lang",code); settings.set("background",background); settings.set("configured",true); configured=true; connect() }) { Text(label) }
      }
     } else TerminalScreen(settings)
    }
   }
  }
  if(settings.flag("configured"))connect()
 }
 @Composable private fun TerminalScreen(settings: Settings) {
  val s=service
  var toolbar by remember { mutableStateOf(settings.flag("toolbar",true)) }
  var extraKeys by remember { mutableStateOf(settings.flag("extra-keys",true)) }
  var fullscreen by remember { mutableStateOf(settings.flag("fullscreen")) }
  var keepScreenOn by remember { mutableStateOf(settings.flag("keep-screen-on")) }
  LaunchedEffect(fullscreen,keepScreenOn) {
   val controller=WindowCompat.getInsetsController(window,window.decorView)
   controller.systemBarsBehavior=WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
   if(fullscreen)controller.hide(WindowInsetsCompat.Type.systemBars()) else controller.show(WindowInsetsCompat.Type.systemBars())
   if(keepScreenOn)window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) else window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
  }
  var split by remember { mutableStateOf(false) }
  var showSettings by remember { mutableStateOf(false) }
  var showHistory by remember { mutableStateOf(false) }
  var search by remember { mutableStateOf("") }
  var ctrl by remember { mutableStateOf(false) }
  var alt by remember { mutableStateOf(false) }
  val c=settings.localized()
  // Exit state is not a Compose field in the upstream session; observe our revision.
  val sessionRevision=s?.sessions?.stateVersion ?: 0
  val primary=s?.sessions?.sessions?.firstOrNull { it.mHandle==selectedSessionId }
   ?: s?.sessions?.sessions?.lastOrNull { it.isRunning }
   ?: s?.sessions?.sessions?.lastOrNull()
  val secondary=if(split) s?.sessions?.sessions?.firstOrNull { it!==primary && it.isRunning }
   ?: s?.sessions?.sessions?.firstOrNull { it!==primary } else null
  val active=listOfNotNull(primary,secondary).firstOrNull { it.mHandle==activeSessionId } ?: primary
  fun newSession(cwd: String?=null) {
   runCatching {
    val runtime=s ?: error("Runtime unavailable")
    val created=runtime.sessions.create(cwd ?: runtime.runtime.storage.home.path)
    selectedSessionId=created.mHandle;activeSessionId=created.mHandle;error=""
   }.onFailure { error=it.message ?: "Cannot start Bash" }
  }
  fun focusActive(showKeyboard: Boolean=false) { active?.let { session -> views[session.mHandle]?.let { TerminalInput.focus(it,showKeyboard) } } }
  LaunchedEffect(selectedSessionId,activeSessionId,split,sessionRevision) {
   if(activeSessionId!=active?.mHandle)activeSessionId=active?.mHandle
   focusActive()
  }
  Box(Modifier.fillMaxSize().safeDrawingPadding().imePadding()) {
  Column(Modifier.fillMaxSize()) {
   if(toolbar) Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(4.dp)) {
    TextButton(onClick={ newSession() }) { Text("+") }
    TextButton(onClick={ split=!split }) { Text(c.getString(R.string.split)) }
    TextButton(onClick={ showSettings=true }) { Text(c.getString(R.string.settings)) }
    TextButton(onClick={ showHistory=true }) { Text(c.getString(R.string.restore)) }
    s?.sessions?.sessions?.forEach { session -> TextButton(onClick={selectedSessionId=session.mHandle;activeSessionId=session.mHandle}) { Text("${if(selectedSessionId==session.mHandle)"● " else ""}${session.mSessionName}${if(!session.isRunning)" [exit ${session.exitStatus}]" else ""}") } }
   }
   if(error.isNotEmpty()) Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(8.dp))
   if(s!=null && primary!=null && active!=null) {
    Column(Modifier.weight(1f)) {
     key(primary.mHandle) { TerminalPane(primary,settings,{ctrl},{alt},{activeSessionId=primary.mHandle},{activeSessionId==primary.mHandle},Modifier.weight(1f)) }
     if(secondary!=null) key(secondary.mHandle) { HorizontalDivider(); TerminalPane(secondary,settings,{ctrl},{alt},{activeSessionId=secondary.mHandle},{activeSessionId==secondary.mHandle},Modifier.weight(1f)) }
    }
    if(!active.isRunning) Row(Modifier.fillMaxWidth().padding(horizontal=8.dp)) {
     Text(c.getString(R.string.session_ended),Modifier.weight(1f))
     TextButton(onClick={newSession()}) {Text(c.getString(R.string.new_session))}
    }
    if(extraKeys) Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
     TextButton(enabled=active.isRunning,onClick={focusActive(true)}) {Text(c.getString(R.string.keyboard))}
     TextButton(enabled=active.isRunning,onClick={ctrl=!ctrl;focusActive()}) { Text(if(ctrl)"Ctrl ●" else "Ctrl") }
     TextButton(enabled=active.isRunning,onClick={alt=!alt;focusActive()}) { Text(if(alt)"Alt ●" else "Alt") }
     listOf("Esc" to "\u001b","Tab" to "\t","↑" to "\u001b[A","↓" to "\u001b[B","←" to "\u001b[D","→" to "\u001b[C").forEach { (label,bytes) -> TextButton(enabled=active.isRunning,onClick={active.write(bytes);focusActive()}) { Text(label) } }
     TextButton(enabled=active.isRunning,onClick={s.sessions.onPasteTextFromClipboard(active);focusActive()}) { Text("Paste") }
     TextButton(enabled=active.isRunning,onClick={s.sessions.stop(active)}) { Text("Stop") }
    }
   } else Text(if(error.isEmpty())"Starting runtime…" else "Runtime unavailable",Modifier.weight(1f))
  }
  // This small recovery control remains accessible when either toolbar is hidden.
  if(!toolbar || !extraKeys) TextButton(onClick={showSettings=true},modifier=Modifier.align(Alignment.TopEnd)) { Text("⚙") }
  }
  if(showSettings) AlertDialog(onDismissRequest={showSettings=false},confirmButton={TextButton(onClick={showSettings=false}) {Text("OK")}},title={Text(c.getString(R.string.settings))},text={
   Column(Modifier.verticalScroll(rememberScrollState()),verticalArrangement=Arrangement.spacedBy(6.dp)) {
    Row(verticalAlignment=Alignment.CenterVertically) { Checkbox(toolbar,{toolbar=it;settings.set("toolbar",it)}); Text(settings.message("상단 툴바 표시","Show top toolbar")) }
    Row(verticalAlignment=Alignment.CenterVertically) { Checkbox(extraKeys,{extraKeys=it;settings.set("extra-keys",it)}); Text(settings.message("보조 키 툴바 표시","Show extra keys toolbar")) }
    Row(verticalAlignment=Alignment.CenterVertically) { Checkbox(fullscreen,{fullscreen=it;settings.set("fullscreen",it)}); Text(settings.message("전체화면","Fullscreen")) }
    Row(verticalAlignment=Alignment.CenterVertically) { Checkbox(keepScreenOn,{keepScreenOn=it;settings.set("keep-screen-on",it)}); Text(settings.message("화면 켜짐 유지 (앱 사용 중)","Keep screen on while visible")) }
    Text(settings.message("툴바를 숨겨도 오른쪽 위 ⚙ 버튼으로 설정을 열 수 있습니다.","Use the top-right ⚙ button to reopen settings when toolbars are hidden."))
    Text(c.getString(R.string.battery))
    Button(onClick={if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS),7)}) {Text("Notifications / 알림 권한")}
    Button(onClick={startActivity(Intent(SystemSettings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:$packageName")))}) {Text("App battery settings / 배터리 설정")}
    Button(onClick={settings.set("background",!settings.flag("background"))}) {Text("Toggle background / 백그라운드 전환")}
    listOf("ko","en").forEach { code -> TextButton(onClick={settings.set("lang",code); recreate()}) {Text(code)} }
    Text("binux settings set font 28\nbinux settings set theme dark\nbinux settings set cursor 0")
   }
  })
  if(showHistory) AlertDialog(onDismissRequest={showHistory=false},confirmButton={TextButton(onClick={showHistory=false}) {Text("OK")}},title={Text(c.getString(R.string.restore))},text={
   Column(Modifier.verticalScroll(rememberScrollState())) {
    Text(settings.message("이전 프로세스는 종료되었습니다. 기록과 작업 경로를 복원하며 새 셸을 시작합니다.","Previous processes ended. Restore a transcript and working directory into a new shell."))
    history.forEach { record -> TextButton(onClick={newSession(record.cwd);showHistory=false}) {Text("${record.id.take(8)} ${record.cwd}")}; Text(record.transcript.takeLast(2000)) }
    OutlinedTextField(search,{search=it},label={Text("Search transcript / 기록 검색")})
    if(search.isNotEmpty())Text(active?.emulator?.screen?.transcriptText?.lineSequence()?.filter { it.contains(search,true) }?.take(100)?.joinToString("\n") ?: "")
   }
  })
 }
 @Composable private fun TerminalPane(session: TerminalSession,settings: Settings,ctrl: ()->Boolean,alt: ()->Boolean,activate: ()->Unit,isActive: ()->Boolean,modifier: Modifier) {
  val currentActivate by rememberUpdatedState(activate)
  val currentActive by rememberUpdatedState(isActive)
  AndroidView(modifier=modifier.fillMaxWidth(),factory={ context ->
   TerminalView(context,null).apply {
    TerminalInput.prepare(this)
    onFocusChangeListener=View.OnFocusChangeListener { _,focused -> if(focused)currentActivate() }
    setTextSize(settings.text("font","28").toIntOrNull() ?: 28)
    setTypeface(Typeface.MONOSPACE)
    setTerminalViewClient(object: TerminalViewClient {
     override fun onScale(scale: Float): Float { if(scale>1.1f || scale<0.9f) { val size=(settings.text("font","28").toInt()*scale).toInt().coerceIn(14,72); settings.set("font",size.toString()); setTextSize(size); return 1f }; return scale }
     override fun onSingleTapUp(e: MotionEvent) { currentActivate(); TerminalInput.focus(this@apply,true) }
     override fun shouldBackButtonBeMappedToEscape()=false
     override fun shouldEnforceCharBasedInput()=false
     override fun shouldUseCtrlSpaceWorkaround()=false
     override fun isTerminalViewSelected()=currentActive() && hasFocus()
     override fun copyModeChanged(copyMode: Boolean) {}
     override fun onKeyDown(keyCode: Int,e: KeyEvent,s: TerminalSession)=false
     override fun onKeyUp(keyCode: Int,e: KeyEvent)=false
     override fun onLongPress(event: MotionEvent)=false
     override fun readControlKey()=ctrl()
     override fun readAltKey()=alt()
     override fun readShiftKey()=false
     override fun readFnKey()=false
     override fun onCodePoint(codePoint: Int,ctrlDown: Boolean,s: TerminalSession)=false
     override fun onEmulatorSet() {}
     override fun logError(tag: String,message: String) {android.util.Log.e(tag,message)}
     override fun logWarn(tag: String,message: String) {android.util.Log.w(tag,message)}
     override fun logInfo(tag: String,message: String) {}
     override fun logDebug(tag: String,message: String) {}
     override fun logVerbose(tag: String,message: String) {}
     override fun logStackTraceWithMessage(tag: String,message: String,e: Exception) {android.util.Log.e(tag,message,e)}
     override fun logStackTrace(tag: String,e: Exception) {android.util.Log.e(tag,"Terminal view",e)}
    })
    attachSession(session); views[session.mHandle]=this
   }
  },onRelease={view -> if(views[session.mHandle]===view)views.remove(session.mHandle);view.clearFocus()},update={view ->
   view.isFocusable=session.isRunning
   view.isFocusableInTouchMode=session.isRunning
   view.onScreenUpdated()
  })
 }
 override fun onSaveInstanceState(outState: Bundle) { outState.putString("selectedSession",selectedSessionId);super.onSaveInstanceState(outState) }
 override fun onStart() { super.onStart(); visible=true; service?.uiVisibility(true) }
 override fun onStop() { super.onStop(); visible=false; service?.uiVisibility(false); if(!isChangingConfigurations && !Settings(this).flag("background"))service?.stopTasks() }
 override fun onDestroy() { service?.sessions?.invalidate=null; if(bound)unbindService(connection); views.clear(); activityScope.cancel(); super.onDestroy() }
}
