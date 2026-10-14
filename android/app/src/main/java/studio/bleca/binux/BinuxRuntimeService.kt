package studio.bleca.binux

import android.app.*
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.LocalServerSocket
import android.os.*
import kotlinx.coroutines.*
import org.json.JSONArray
import java.util.concurrent.CountDownLatch

class BinuxRuntimeService: Service() {
 inner class RuntimeBinder: Binder() { val service get()=this@BinuxRuntimeService }
 private val binder=RuntimeBinder()
 lateinit var settings: Settings; private set
 lateinit var runtime: NativeRuntime; private set
 lateinit var sessions: SessionManager; private set
 lateinit var jobs: BackgroundProcessManager; private set
 lateinit var servers: ServerManager; private set
 lateinit var database: BinuxDatabase; private set
 private val scope=CoroutineScope(SupervisorJob()+Dispatchers.IO)
 private val handler=Handler(Looper.getMainLooper())
 private var control: LocalServerSocket?=null
 private var uiBound=false
 private var uiVisible=true
 private val checkpoint=object: Runnable { override fun run() { sessions.checkpoint(); notifyTasks(); handler.postDelayed(this,5000) } }
 override fun onCreate() {
  super.onCreate()
  settings=Settings(this); runtime=NativeRuntime(this,settings,StorageManager(this)); database=BinuxDatabase.open(this)
  jobs=BackgroundProcessManager(runtime,database,::notifyTasks); servers=ServerManager(runtime,jobs)
  sessions=SessionManager(runtime,database,::notifyTasks)
  val manager=getSystemService(NotificationManager::class.java)
  manager.createNotificationChannel(NotificationChannel("runtime",settings.localized().getString(R.string.channel),NotificationManager.IMPORTANCE_LOW))
  if(Build.VERSION.SDK_INT>=34) startForeground(1,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(1,notification())
  control=LocalServerSocket(runtime.control)
  val router=CommandRouter(this)
  scope.launch {
   while(isActive) {
    val socket=try { control?.accept() ?: break } catch(e: Exception) { break }
    launch {
     socket.use { peer ->
      peer.soTimeout=5000
      // Abstract socket name is private by convention only. Enforce same app UID.
      if(peer.peerCredentials.uid!=Process.myUid())return@use
      try {
       val reader=peer.inputStream.bufferedReader(Charsets.UTF_8)
       val request=StringBuilder()
       while(request.length<65536) { val c=reader.read(); if(c==-1 || c==10)break; request.append(c.toChar()) }
       require(request.length<65536) { "Request too large" }
       val array=JSONArray(request.toString()); require(array.length()<=256)
       val args=List(array.length()) { array.getString(it) }
       var response=CommandRouter.Result(1,"Runtime unavailable")
       val done=CountDownLatch(1)
       if(args.firstOrNull()=="script-download")response=ScriptDownload.fetch(args.drop(1))
       else { handler.post { try { response=router.execute(args) } finally { done.countDown() } };done.await() }
       peer.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write("${response.code}\n${response.text}\n") }
      } catch(e: Exception) { runCatching { peer.outputStream.write("1\nInvalid control request\n".toByteArray()) } }
     }
    }
   }
  }
  handler.post(checkpoint)
 }
 override fun onStartCommand(intent: Intent?, flags: Int,startId: Int): Int {
  when(intent?.action) {
   "stop" -> { stopTasks(); handler.postDelayed({ if(!uiBound && idle())stopSelf() },2500) }
   "pause" -> jobs.pauseAll()
  }
  return START_NOT_STICKY
 }
 override fun onBind(intent: Intent): IBinder { uiBound=true; return binder }
 override fun onRebind(intent: Intent) { uiBound=true }
 override fun onUnbind(intent: Intent): Boolean { uiBound=false; notifyTasks(); return true }
 fun uiVisibility(visible: Boolean) {
  uiVisible=visible
  if(visible) {
   startService(Intent(this,BinuxRuntimeService::class.java))
   if(Build.VERSION.SDK_INT>=34) startForeground(1,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(1,notification())
  } else notifyTasks()
 }
 private fun idle()=::sessions.isInitialized && sessions.sessions.none { it.isRunning } && jobs.jobs.none { it.process.isAlive }
 fun stopTasks() { sessions.stopAll(); jobs.stopAll() }
 fun notifyTasks() {
  if(::sessions.isInitialized) getSystemService(NotificationManager::class.java).notify(1,notification())
  if(!uiVisible && idle())handler.postDelayed({if(!uiVisible && idle()){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()}},2500)
 }
 private fun notification(): Notification {
  val c=settings.localized()
  val open=PendingIntent.getActivity(this,0,Intent(this,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
  fun action(name: String,id: Int)=PendingIntent.getService(this,id,Intent(this,BinuxRuntimeService::class.java).setAction(name),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
  val sessionCount=if(::sessions.isInitialized)sessions.sessions.count { it.isRunning } else 0
  val jobCount=if(::jobs.isInitialized)jobs.jobs.count { it.process.isAlive && it.server==null } else 0
  val serverCount=if(::jobs.isInitialized)jobs.jobs.count { it.process.isAlive && it.server!=null } else 0
  return Notification.Builder(this,"runtime").setSmallIcon(android.R.drawable.ic_menu_manage).setContentTitle("binux ${BuildConfig.VERSION_NAME}")
   .setContentText(c.getString(R.string.notification,sessionCount,jobCount,serverCount)).setContentIntent(open).setOngoing(true)
   .addAction(Notification.Action.Builder(null,c.getString(R.string.open),open).build())
   .addAction(Notification.Action.Builder(null,c.getString(R.string.pause),action("pause",1)).build())
   .addAction(Notification.Action.Builder(null,c.getString(R.string.stop_all),action("stop",2)).build()).build()
 }
 override fun onTaskRemoved(rootIntent: Intent?) { if(!settings.flag("background")) { stopTasks(); handler.postDelayed({stopSelf()},2500) } }
 override fun onDestroy() {
  stopTasks(); handler.removeCallbacks(checkpoint); runCatching { control?.close() }; scope.cancel()
  super.onDestroy()
 }
}
