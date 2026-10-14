package studio.bleca.binux.x11;
import android.os.ParcelFileDescriptor;
/** Binux runs the packaged native X server in its own foreground Service process.
 * No app_process shell loader, hidden ActivityManager API or shared UID is used. */
public final class CmdEntryPoint extends ICmdEntryInterface.Stub {
 public static final String ACTION_START="studio.bleca.binux.x11.SERVER_STARTED";
 static { System.loadLibrary("Xlorie"); }
 public static native boolean start(String[] args);
 public native ParcelFileDescriptor getXConnection();
 public native ParcelFileDescriptor getLogcatOutput();
}
