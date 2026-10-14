package studio.bleca.binux
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import java.io.File
class BootReceiver: BroadcastReceiver() {
 override fun onReceive(context: Context, intent: Intent) {
  if(intent.action!=Intent.ACTION_BOOT_COMPLETED)return
  val settings=Settings(context)
  if(!settings.flag("autostart") || !settings.flag("background"))return
  try { context.startForegroundService(Intent(context,BinuxRuntimeService::class.java).setAction("autostart")) }
  catch(e: Exception) { val file=File(context.filesDir,"config/autostart-error.txt");file.parentFile?.mkdirs();file.writeText("Android blocked opted-in reboot restart: ${e.javaClass.simpleName}. Open binux to restart selected jobs manually.") }
 }
}
