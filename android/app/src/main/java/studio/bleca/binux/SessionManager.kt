package studio.bleca.binux

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.util.Log
import androidx.compose.runtime.*
import com.termux.terminal.TerminalSession
import com.termux.terminal.TerminalSessionClient
import kotlinx.coroutines.*
import java.io.File

class SessionManager(private val runtime: NativeRuntime, private val db: BinuxDatabase, private val changed: () -> Unit): TerminalSessionClient {
 val sessions = mutableStateListOf<TerminalSession>()
 var stateVersion by mutableIntStateOf(0)
  private set
 private val births=mutableMapOf<String,Long>()
 val scope = CoroutineScope(SupervisorJob()+Dispatchers.IO)
 var invalidate: (() -> Unit)? = null
 init {
  // PIDs from an earlier application process are never reattached or signalled.
  scope.launch { db.sessions().markInterrupted() }
 }
 fun create(cwd: String = runtime.storage.home.path): TerminalSession {
  require(File(cwd).isDirectory) { "Working directory does not exist" }
  check(File(runtime.bash).canExecute()) { "Bundled ARM64 Bash is missing or not executable" }
  val session=TerminalSession(runtime.bash,cwd,arrayOf(runtime.bash,"--rcfile",runtime.rc.path,"-i"),runtime.environment().map { "${it.key}=${it.value}" }.toTypedArray(),5000,this)
  session.mSessionName="Bash ${sessions.size+1}"
  sessions.add(session)
  try { session.updateSize(80,24) } catch(e: Exception) { sessions.remove(session); throw e }
  births[session.mHandle]=NativeProcess.birth(session.pid)
  changed(); return session
 }
 fun checkpoint() {
  val rows=sessions.map { s -> SessionRecord(s.mHandle,s.cwd ?: runtime.storage.home.path,s.pid,if(s.isRunning)"running" else "exited",System.currentTimeMillis(),s.emulator?.screen?.transcriptText?.takeLast(128*1024) ?: "") }
  scope.launch { rows.forEach { db.sessions().save(it) } }
 }
 fun stop(session: TerminalSession) {
  val leader=session.pid
  val birth=births[session.mHandle] ?: 0
  if(leader>1) NativeProcess.signalSession(leader,birth,15)
  android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ if(leader>1) { NativeProcess.signalSession(leader,birth,9); if(session.pid>1)session.finishIfRunning() } },2000)
 }
 fun stopAll() = sessions.toList().forEach(::stop)
 override fun onTextChanged(changedSession: TerminalSession) { invalidate?.invoke() }
 override fun onTitleChanged(changedSession: TerminalSession) { invalidate?.invoke() }
 override fun onSessionFinished(finishedSession: TerminalSession) { stateVersion++; checkpoint(); changed(); invalidate?.invoke() }
 override fun onCopyTextToClipboard(session: TerminalSession, text: String) { clipboard().setPrimaryClip(ClipData.newPlainText("binux",text)) }
 override fun onPasteTextFromClipboard(session: TerminalSession) { clipboard().primaryClip?.getItemAt(0)?.coerceToText(runtime.context)?.let { session.emulator?.paste(it.toString()) } }
 private fun clipboard()=runtime.context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
 override fun onBell(session: TerminalSession) {}
 override fun onColorsChanged(session: TerminalSession) { invalidate?.invoke() }
 override fun onTerminalCursorStateChange(state: Boolean) { invalidate?.invoke() }
 override fun getTerminalCursorStyle(): Int = runtime.settings.text("cursor","0").toIntOrNull() ?: 0
 override fun logError(tag: String,message: String) { Log.e(tag,message) }
 override fun logWarn(tag: String,message: String) { Log.w(tag,message) }
 override fun logInfo(tag: String,message: String) { Log.i(tag,message) }
 override fun logDebug(tag: String,message: String) {}
 override fun logVerbose(tag: String,message: String) {}
 override fun logStackTraceWithMessage(tag: String,message: String,e: Exception) { Log.e(tag,message,e) }
 override fun logStackTrace(tag: String,e: Exception) { Log.e(tag,"Terminal error",e) }
}
