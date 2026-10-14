package studio.bleca.binux

import android.content.Intent
import android.net.Uri
import java.io.File

class DesktopManager(private val service: BinuxRuntimeService) {
 companion object {
  const val PACKAGE="studio.bleca.binux.x11"
  const val INSTALLER="https://raw.githubusercontent.com/blecastudio/binux/main/setup-binux-desktop"
 }
 private fun available()=runCatching { service.packageManager.getPackageInfo(PACKAGE,0);true }.getOrDefault(false)
 fun execute(args: List<String>): String = when(args.firstOrNull()) {
  "status" -> {
   val name=service.virtualMachines.defaultName()
   val record=File(service.runtime.storage.base,"rootfs/$name/state/config/desktop.json")
   "Runtime: $name\nXFCE: ${if(record.exists() && org.json.JSONObject(record.readText()).optBoolean("installed"))"installed" else "not installed"}\nBinux Desktop:X11 APK: ${if(available())"installed" else "not installed"}\nProcess status: binux runtime exec $name binux desktop status"
  }
  "source" -> service.assets.open("installer-manifest.json").use { val manifest=org.json.JSONObject(it.bufferedReader().readText());"Publisher: BlecaStudio\nSource: ${manifest.getString("url")}\nSHA-256 (pinned in this APK): ${manifest.getString("sha256")}\nDownload is rejected if the official script differs. Guest apt verifies Debian/Ubuntu package signatures." }
  "prepare" -> {
   check(service.settings.flag("background")) { "Desktop:X11 opens a separate app. Enable the background preference with binux bg enable before starting Desktop." }
   execute(listOf("x11","open"))
   var credentials: String?=null
   repeat(100) { if(credentials==null) { credentials=runCatching { execute(listOf("x11","auth")) }.getOrNull();if(credentials==null)Thread.sleep(100) } }
   credentials ?: error("X11 initialization timed out. Open Desktop:X11 manually and retry. Both APKs must have matching signatures.")
  }
  "installer" -> "bash <(curl -Lf $INSTALLER)"
  "audio" -> when(args.getOrNull(1)) {
   "start" -> { service.desktopAudio.start();"Audio capture requested; check binux desktop audio status" }
   "stop" -> { service.desktopAudio.stop();"Audio stopped" }
   "status" -> service.desktopAudio.state
   else -> error("binux desktop audio start | stop | status")
  }
  "browser" -> {
   val uri=Uri.parse(args.getOrNull(1) ?: "https://www.google.com")
   require(uri.scheme in listOf("http","https"))
   service.startActivity(Intent(Intent.ACTION_VIEW,uri).setPackage("com.android.chrome").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
   "Android Chrome launch requested; this is the Android browser, not a Linux ARM64 Chrome package."
  }
  "x11" -> when(args.getOrNull(1)) {
   "open" -> {
    check(available()) { "Install the Binux Desktop:X11 APK first; see https://github.com/blecastudio/binux" }
    val intent=service.packageManager.getLaunchIntentForPackage(PACKAGE) ?: error("X11 launcher unavailable")
    service.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    "X11 app launch requested. The app reports its display server state separately."
   }
   "auth" -> {
    check(available()) { "X11 APK is not installed" }
    val name=service.virtualMachines.defaultName()
    val file=File(service.runtime.storage.base,"rootfs/$name/bootstrap/xauthority");file.parentFile?.mkdirs()
    val temporary=File(file.path+".tmp")
    service.contentResolver.openInputStream(Uri.parse("content://studio.bleca.binux.x11.credentials/authority")).use { input ->
     check(input!=null) { "Open the X11 app to initialize the display first" }
     temporary.outputStream().use { input.copyTo(it) }
    }
    temporary.setReadable(false,false);temporary.setWritable(false,false);temporary.setReadable(true,true);temporary.setWritable(true,true);check(temporary.renameTo(file))
    "DISPLAY=10.0.2.2:1 (guest)\nXAUTHORITY=/run/binux-bootstrap/xauthority\nCredentials copied from the same-signature companion app; values are not logged or copied into shared ~/."
   }
   else -> error("binux desktop x11 open | auth")
  }
  "install","start","stop","update","uninstall" -> error("Use binux Desktop commands from the interactive Bash shell. Install/select a Linux VM first.")
  else -> error("binux desktop install | status | installer | x11 open | x11 auth")
 }
}
