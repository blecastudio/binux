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
  "status" -> "XFCE: not installed (Debian/Ubuntu execution engine unavailable)\nBinux Desktop:X11 APK: ${if(available())"installed" else "not installed"}\nX11 renderer and Linux distribution runtime are separate components."
  "installer" -> "bash <(curl -Lf $INSTALLER)"
  "install" -> {
   val script=File.createTempFile("binux-desktop-",".sh",File(service.runtime.storage.base,"cache"))
   val command="curl -Lf \"$INSTALLER\" > \"\$1\" && bash \"\$1\"; result=\$?; rm -f -- \"\$1\"; exit \"\$result\""
   val job=service.jobs.run(listOf(service.runtime.bash,"-c",command,"binux-desktop-installer",script.path))
   "Installer job: ${job.id}\nRead progress/errors: binux bg logs ${job.id}\nThe installer checks runtime compatibility before installing packages."
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
    val file=File(service.runtime.storage.base,"desktop/.Xauthority")
    service.contentResolver.openInputStream(Uri.parse("content://studio.bleca.binux.x11.credentials/authority")).use { input ->
     check(input!=null) { "Open the X11 app to initialize the display first" }
     file.outputStream().use { input.copyTo(it) }
    }
    file.setReadable(false,false);file.setWritable(false,false);file.setReadable(true,true);file.setWritable(true,true)
    "DISPLAY=127.0.0.1:1\nXAUTHORITY=${file.path}\nCredentials copied from the same-signature companion app; values are not logged."
   }
   else -> error("binux desktop x11 open | auth")
  }
  "start","stop","update","uninstall" -> error("Debian/Ubuntu execution engine is not yet integrated into Android Native Runtime. For the X11 display use: binux desktop x11 open; stop it from its notification.")
  else -> error("binux desktop install | status | installer | x11 open | x11 auth")
 }
}
