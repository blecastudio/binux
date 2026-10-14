package studio.bleca.binux
import org.junit.Assert.*
import org.junit.Test
class GuestArgumentsTest {
 @Test fun shellQuotingPreservesMetacharactersAndUnicode() {
  val values=listOf("", "two words", "a'b", "\$(id)", "한국어\nnext")
  val script="printf '%s\\0' "+values.joinToString(" ",transform=VmManager::quote)
  val process=ProcessBuilder("/bin/bash","-c",script).start()
  val output=process.inputStream.readBytes().toString(Charsets.UTF_8).split('\u0000').dropLast(1)
  assertEquals(0,process.waitFor());assertEquals(values,output)
 }
}
