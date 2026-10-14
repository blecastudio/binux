package studio.bleca.binux.x11;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk={34,35})
public class PreferencesTest {
 @Test public void standaloneSettingsAndEachCategoryOpenWithoutNativeServer() {
  try(org.robolectric.android.controller.ActivityController<LoriePreferences> activity=Robolectric.buildActivity(LoriePreferences.class).setup()) {
   LoriePreferences settings=activity.get();
   settings.getSupportFragmentManager().executePendingTransactions();
   for(String category:new String[]{"main","output","kbd","pointer","other","ekbar","userActions"}) {
    LoriePreferences.LoriePreferenceFragment fragment=new LoriePreferences.LoriePreferenceFragment(category);
    settings.getSupportFragmentManager().beginTransaction().replace(android.R.id.content,fragment).commitNow();
    assertNotNull(fragment.getPreferenceScreen());
    fragment.updatePreferencesLayout();
   }
  }
 }
}
