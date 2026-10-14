package studio.bleca.binux

import android.content.Context
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import java.util.Locale

private val Context.binuxSettings by preferencesDataStore("binux-settings")
class Settings(private val context: Context) {
 private fun data() = runBlocking { context.binuxSettings.data.first() }
 fun text(name: String, fallback: String) = data()[PreferenceKeys.text(name)] ?: fallback
 fun flag(name: String, fallback: Boolean = false) = data()[PreferenceKeys.flag(name)] ?: fallback
 fun set(name: String, value: String) = runBlocking { context.binuxSettings.updateData { previous -> previous.toMutablePreferences().apply { this[PreferenceKeys.text(name)] = value } } }
 fun set(name: String, value: Boolean) = runBlocking { context.binuxSettings.updateData { previous -> previous.toMutablePreferences().apply { this[PreferenceKeys.flag(name)] = value } } }
 val language get() = text("lang", "ko")
 fun message(ko: String, en: String) = if(language == "ko") ko else en
 fun localized(): Context {
  val config = android.content.res.Configuration(context.resources.configuration)
  config.setLocale(Locale.forLanguageTag(if(language == "ko") "ko-KR" else "en-US"))
  return context.createConfigurationContext(config)
 }
}
