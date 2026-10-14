package studio.bleca.binux

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.room.Room
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.atomic.AtomicReference
import java.io.File

/** These require an ARM64 device. Compiling them is not a device test result. */
@RunWith(AndroidJUnit4::class)
class RuntimeDeviceTest {
 @Test fun bundledBashExecutesRealFileCommandsAndKorean() {
  val context=InstrumentationRegistry.getInstrumentation().targetContext
  val runtime=NativeRuntime(context,Settings(context),StorageManager(context))
  val pb=ProcessBuilder(runtime.bash,"-c","test -t 0 && exit 99; d=\$(mktemp -d); cd \"\$d\"; printf '비눅스\\n' > hello; cat hello; pwd; rm hello; cd /; rmdir \"\$d\"; exit 7").redirectErrorStream(true)
  pb.environment().putAll(runtime.environment())
  val process=pb.start();val output=process.inputStream.bufferedReader().readText()
  assertEquals(7,process.waitFor());assertTrue(output.contains("비눅스"))
 }
 @Test fun ptyActuallyProvidesATerminalAndReportsExit() {
  val instrumentation=InstrumentationRegistry.getInstrumentation()
  val context=instrumentation.targetContext
  val runtime=NativeRuntime(context,Settings(context),StorageManager(context))
  val db=Room.inMemoryDatabaseBuilder(context,BinuxDatabase::class.java).build()
  val session=AtomicReference<com.termux.terminal.TerminalSession>()
  instrumentation.runOnMainSync { session.set(SessionManager(runtime,db,{}).create()); session.get().write("test -t 0 && printf 'REAL_PTY_OK\\n'; printf '한국어\\n'; exit 11\n") }
  val output=AtomicReference("")
  try {
   val deadline=System.nanoTime()+10_000_000_000L
   while(System.nanoTime()<deadline) {
    instrumentation.runOnMainSync { output.set(session.get().emulator.screen.transcriptText) }
    if(!session.get().isRunning)break
    Thread.sleep(50)
   }
   assertFalse(session.get().isRunning); assertEquals(11,session.get().exitStatus)
   assertTrue(output.get().contains("REAL_PTY_OK"));assertTrue(output.get().contains("한국어"))
  } finally { instrumentation.runOnMainSync {session.get().finishIfRunning()} }
 }
 @Test fun nativeBackgroundPidHandshakeReturnsItsRealPid() {
  val context=InstrumentationRegistry.getInstrumentation().targetContext
  val runtime=NativeRuntime(context,Settings(context),StorageManager(context))
  val file=File(context.cacheDir,"test-${System.nanoTime()}.pid")
  val pb=ProcessBuilder(runtime.job,runtime.bash,"-c","printf '%s' \"\$BASHPID\"").redirectErrorStream(true)
  pb.environment().putAll(runtime.environment());pb.environment()["BINUX_PID_FILE"]=file.path
  val process=pb.start();val output=process.inputStream.bufferedReader().readText();assertEquals(0,process.waitFor())
  assertEquals(file.readText().trim(),output.trim());file.delete()
 }
}
