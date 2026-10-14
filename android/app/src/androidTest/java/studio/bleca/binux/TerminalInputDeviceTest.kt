package studio.bleca.binux

import android.os.Build
import android.os.SystemClock
import android.view.*
import android.view.accessibility.AccessibilityNodeInfo
import android.view.inputmethod.EditorInfo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.termux.view.TerminalView
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/** End-to-end regression tests for an ARM64 test device with a soft keyboard.
 * They exercise the real MainActivity, Android editor, PTY and bundled Bash.
 * A successful compilation alone does not mean these tests were executed.
 */
@RunWith(AndroidJUnit4::class)
class TerminalInputDeviceTest {
 private fun terminals(view: View): List<TerminalView> = when(view) {
  is TerminalView -> listOf(view)
  is ViewGroup -> (0 until view.childCount).flatMap {terminals(view.getChildAt(it))}
  else -> emptyList()
 }
 private fun waitFor(condition: ()->Boolean) {
  val until=SystemClock.uptimeMillis()+15000
  while(SystemClock.uptimeMillis()<until) {if(condition())return;Thread.sleep(50)}
  fail("Terminal/keyboard did not reach the expected state")
 }
 private fun click(label: String) {
  val automation=InstrumentationRegistry.getInstrumentation().uiAutomation
  waitFor {
   val node=automation.rootInActiveWindow?.findAccessibilityNodeInfosByText(label)?.firstOrNull {it.text?.toString()==label}
   var button=node
   while(button!=null && !button.isClickable)button=button.parent
   button?.performAction(AccessibilityNodeInfo.ACTION_CLICK)==true
  }
 }
 private fun withTerminal(block: (ActivityScenario<MainActivity>)->Unit) {
  val context=InstrumentationRegistry.getInstrumentation().targetContext
  val settings=Settings(context)
  val configured=settings.flag("configured");val background=settings.flag("background");val lang=settings.language
  settings.set("configured",true);settings.set("background",true);settings.set("lang","en")
  val scenario=ActivityScenario.launch(MainActivity::class.java)
  try {
   waitFor {var ready=false;scenario.onActivity {ready=terminals(it.window.decorView).any {v->v.mTermSession?.isRunning==true}};ready}
   block(scenario)
  } finally {
   scenario.onActivity {activity -> terminals(activity.window.decorView).forEach {it.mTermSession?.finishIfRunning()} }
   scenario.close()
   settings.set("configured",configured);settings.set("background",background);settings.set("lang",lang)
  }
 }
 private fun text(scenario: ActivityScenario<MainActivity>,view: TerminalView): String {
  var value="";scenario.onActivity {value=view.mEmulator.screen.transcriptText};return value
 }
 private fun commit(scenario: ActivityScenario<MainActivity>,view: TerminalView,command: String) {
  scenario.onActivity {
   assertTrue(view.hasFocus())
   assertTrue(view.mClient.isTerminalViewSelected)
   assertTrue(view.onCreateInputConnection(EditorInfo()).commitText(command,1))
  }
 }

 @Test fun keyboardButtonFocusesEditorAndImeExecutesKoreanBashCommand() {
  assumeTrue(Build.VERSION.SDK_INT>=30)
  withTerminal {scenario ->
   lateinit var terminal: TerminalView
   scenario.onActivity {terminal=terminals(it.window.decorView).first()}
   click("Keyboard")
   waitFor {var visible=false;scenario.onActivity {visible=terminal.hasFocus() && terminal.rootWindowInsets?.isVisible(WindowInsets.Type.ime())==true};visible}
   // The expected marker is assembled by Bash; an echoed command cannot pass.
   commit(scenario,terminal,"value='한글'; printf '\\111\\115\\105\\137\\117\\113\\137%s\\n' \"\$value\"\n")
   waitFor {text(scenario,terminal).contains("IME_OK_한글")}
   assertTrue(terminal.mTermSession.isRunning)
  }
 }

 @Test fun splitPaneTapAndToolbarTabSendCommandToTheFocusedPane() {
  withTerminal {scenario ->
   click("+");click("Split")
   var panes=emptyList<TerminalView>()
   waitFor {scenario.onActivity {panes=terminals(it.window.decorView)};panes.size==2}
   val upper=panes[0];val lower=panes[1]
   scenario.onActivity {
    val now=SystemClock.uptimeMillis()
    MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,lower.width/2f,lower.height/2f,0).also {lower.dispatchTouchEvent(it);it.recycle()}
    MotionEvent.obtain(now,now+30,MotionEvent.ACTION_UP,lower.width/2f,lower.height/2f,0).also {lower.dispatchTouchEvent(it);it.recycle()}
   }
   waitFor {var focused=false;scenario.onActivity {focused=lower.hasFocus() && lower.mClient.isTerminalViewSelected};focused}
   commit(scenario,lower,"printf")
   click("Tab")
   commit(scenario,lower,"'\\123\\120\\114\\111\\124\\137\\117\\113\\n'\n")
   waitFor {text(scenario,lower).contains("SPLIT_OK")}
   assertFalse(text(scenario,upper).contains("SPLIT_OK"))
  }
 }

 @Test fun aNewSessionAfterExitIsSelectedAndAcceptsImeInput() {
  withTerminal {scenario ->
   lateinit var previous: TerminalView
   scenario.onActivity {previous=terminals(it.window.decorView).first();TerminalInput.focus(previous)}
   commit(scenario,previous,"exit\n")
   waitFor {!previous.mTermSession.isRunning}
   click("New session")
   lateinit var fresh: TerminalView
   waitFor {var ready=false;scenario.onActivity {terminals(it.window.decorView).firstOrNull {v->v.mTermSession!==previous.mTermSession && v.mTermSession.isRunning}?.let {v->fresh=v;ready=v.hasFocus()}};ready}
   commit(scenario,fresh,"printf '\\116\\105\\127\\137\\117\\113\\n'\n")
   waitFor {text(scenario,fresh).contains("NEW_OK")}
  }
 }
}
