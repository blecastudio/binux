package studio.bleca.binux

import android.content.Context
import android.view.View
import android.view.inputmethod.InputMethodManager
import com.termux.view.TerminalView

/** Native AndroidView must opt in to touch focus before it can receive IME keys. */
object TerminalInput {
 fun prepare(view: TerminalView) {
  view.id=View.generateViewId()
  view.isFocusable=true
  view.isFocusableInTouchMode=true
 }

 fun focus(view: TerminalView,showKeyboard: Boolean=false): Boolean {
  if(view.mTermSession?.isRunning!=true || !view.requestFocus())return false
  if(showKeyboard) view.post {
   if(view.isAttachedToWindow && view.hasWindowFocus() && view.hasFocus() && view.mTermSession?.isRunning==true) {
    val input=view.context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
    // Preserve ongoing Korean composition when tapping an already-active editor.
    if(!input.isActive(view))input.restartInput(view)
    input.showSoftInput(view,InputMethodManager.SHOW_IMPLICIT)
   }
  }
  return true
 }
}
