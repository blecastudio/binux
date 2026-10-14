package studio.bleca.binux

import android.view.inputmethod.EditorInfo
import android.widget.FrameLayout
import com.termux.terminal.TerminalSession
import com.termux.terminal.TerminalSessionClient
import com.termux.terminal.TerminalEmulator
import com.termux.view.TerminalView
import com.termux.view.TerminalViewClient
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import java.lang.reflect.Proxy

/** Tests Android focus and the actual Java IME -> session byte queue boundary.
 * Native subprocess creation is intentionally not part of a Robolectric JVM test.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[34,35])
class TerminalInputTest {
 private fun fixture(): TerminalView {
  val view=TerminalView(RuntimeEnvironment.getApplication(),null)
  val client=Proxy.newProxyInstance(TerminalSessionClient::class.java.classLoader,arrayOf(TerminalSessionClient::class.java)) { _,method,_ -> if(method.name=="getTerminalCursorStyle")0 else null } as TerminalSessionClient
  val session=TerminalSession("/test-only/not-executed","/",emptyArray(),emptyArray(),100,client)
  // Replace only the native-running boundary; no JNI fork occurs on the host JVM.
  TerminalSession::class.java.getDeclaredField("mShellPid").apply { isAccessible=true;setInt(session,123) }
  view.mTermSession=session
  view.mEmulator=TerminalEmulator(session,80,24,100,client)
  view.setTerminalViewClient(Proxy.newProxyInstance(TerminalViewClient::class.java.classLoader,arrayOf(TerminalViewClient::class.java)) { _,method,_ ->
   when(method.name) { "isTerminalViewSelected" -> view.hasFocus(); "onScale" -> 1f; else -> if(method.returnType==java.lang.Boolean.TYPE)false else null }
  } as TerminalViewClient)
  FrameLayout(view.context).addView(view)
  TerminalInput.prepare(view)
  return view
 }

 private fun drain(view: TerminalView): String {
  val field=TerminalSession::class.java.getDeclaredField("mTerminalToProcessIOQueue").apply {isAccessible=true}
  val queue=field.get(view.mTermSession)
  val read=queue.javaClass.getDeclaredMethod("read",ByteArray::class.java,java.lang.Boolean.TYPE).apply {isAccessible=true}
  val bytes=ByteArray(4096)
  val count=read.invoke(queue,bytes,false) as Int
  return bytes.copyOf(count.coerceAtLeast(0)).toString(Charsets.UTF_8)
 }

 @Test fun touchFocusableTerminalAcceptsImeCommandAndKorean() {
  val view=fixture()
  assertTrue("A terminal tap must be able to focus the native editor",TerminalInput.focus(view))
  assertSame(view,(view.parent as FrameLayout).findFocus())
  val input=view.onCreateInputConnection(EditorInfo())
  assertTrue(input.commitText("printf '비눅스'\n",1))
  assertEquals("printf '비눅스'\r",drain(view))
 }

 @Test fun focusSwitchRoutesTypingToOnlyTheSecondPane() {
  val first=fixture();val second=fixture()
  val parent=first.parent as FrameLayout
  (second.parent as FrameLayout).removeView(second);parent.addView(second)
  assertTrue(TerminalInput.focus(first))
  assertTrue(TerminalInput.focus(second))
  assertFalse(first.hasFocus());assertTrue(second.hasFocus())
  second.onCreateInputConnection(EditorInfo()).commitText("pwd\n",1)
  assertEquals("pwd\r",drain(second));assertEquals("",drain(first))
 }

 @Test fun endedSessionCannotBeUsedAsKeyboardTarget() {
  val view=fixture()
  TerminalSession::class.java.getDeclaredField("mShellPid").apply {isAccessible=true;setInt(view.mTermSession,-1)}
  assertFalse(TerminalInput.focus(view))
 }
}
