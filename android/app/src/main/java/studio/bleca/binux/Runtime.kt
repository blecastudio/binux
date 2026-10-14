package studio.bleca.binux

import android.content.Context
import android.os.Build
import java.io.File
import java.util.UUID

object NativeProcess {
 init { System.loadLibrary("binux_process") }
 @JvmStatic external fun signalGroup(pid: Int, signal: Int): Int
 @JvmStatic external fun birth(pid: Int): Long
 @JvmStatic external fun signalSession(pid: Int, birth: Long, signal: Int): Int
}
class StorageManager(context: Context) {
 val base = context.filesDir
 val dirs = listOf("home","rootfs","packages","addons","desktop","projects/python","projects/javascript","logs","repos","cache","wbs","config")
 init { dirs.forEach { File(base,it).mkdirs() } }
 val home get() = File(base,"home")
 fun info() = dirs.joinToString("\n") { name -> val f=File(base,name); "$name: ${f.walkTopDown().filter { it.isFile }.sumOf { it.length() }} bytes" } + "\nfree: ${base.usableSpace} bytes"
 fun clean(): String { val cache=File(base,"cache"); cache.listFiles()?.forEach { it.deleteRecursively() }; return "cache: 0" }
}
class NativeRuntime(val context: Context, val settings: Settings, val storage: StorageManager) {
 val libDir = context.applicationInfo.nativeLibraryDir
 val bash = "$libDir/libbinux_bash.so"
 val ctl = "$libDir/libbinuxctl.so"
 val job = "$libDir/libbinuxjob.so"
 val control = "binux.${android.os.Process.myUid()}.${UUID.randomUUID()}"
 val rc = File(storage.home,".binuxrc")
 init { context.assets.open("binuxrc").use { input -> rc.outputStream().use { input.copyTo(it) } } }
 fun environment(): Map<String,String> = mapOf(
  "HOME" to storage.home.path, "PATH" to "$libDir:/system/bin:/system/xbin", "TMPDIR" to File(storage.base,"cache").path,
  "TERM" to "xterm-256color", "LANG" to "C.UTF-8", "BINUX_RUNTIME" to "native-android",
   "BINUX_LANG" to settings.language, "BINUX_VERSION" to BuildConfig.VERSION_NAME,
  "BINUX_BASH" to bash, "BINUX_CTL" to ctl, "BINUX_CONTROL" to control,
  "BINUX_HOME" to storage.base.path, "BASH_ENV" to rc.path
 )
 fun doctor(): String = listOf(
  "Android API ${Build.VERSION.SDK_INT}, ABI ${Build.SUPPORTED_ABIS.joinToString()}",
  "Bash: ${File(bash).canExecute()} ($bash)", "PTY: ${File("/dev/ptmx").canRead()}",
  "foreground: specialUse; notification permission is user-controlled",
  "Native executables: APK nativeLibraryDir only; downloadable native packages unavailable",
  "PRoot / apt / Python / Node.js: not bundled in Android 0.1.0",
  "Root privileges: unavailable; kernel and SELinux belong to Android"
 ).joinToString("\n")
}
