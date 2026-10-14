package studio.bleca.binux;
import androidx.datastore.preferences.core.Preferences;
import androidx.datastore.preferences.core.PreferencesKeys;
/** Java facade for the stable JVM key factory; usable with AndroidX KMP artifacts. */
public final class PreferenceKeys {
 private PreferenceKeys() {}
 public static Preferences.Key<String> text(String name) { return PreferencesKeys.stringKey(name); }
 public static Preferences.Key<Boolean> flag(String name) { return PreferencesKeys.booleanKey(name); }
}
