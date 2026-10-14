package studio.bleca.binux
import org.junit.Assert.*
import org.junit.Test
class GuestHostKeyTest {
 @Test fun directSerialRecord() {
  assertEquals("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest==",GuestHostKey.parse("BINUX_SSH_HOSTKEY ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest== root@binux\n"))
 }
 @Test fun splitSystemdRecords() {
  val log="[34.408] binux-first-boot[326]: BINUX_SSH_HOSTKEY\r\n[34.424] binux-first-boot[357]: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest== root@binux\r\n"
  assertEquals("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest==",GuestHostKey.parse(log))
 }
 @Test fun unrelatedOrMissingKeysAreRejected() {
  assertNull(GuestHostKey.parse("ssh-ed25519 unrelated\nBINUX_SSH_HOSTKEY"))
  assertNull(GuestHostKey.parse("ssh-ed25519 unrelated"))
  assertNull(GuestHostKey.parse("BINUX_SSH_HOSTKEY"+"x".repeat(2048)+"ssh-ed25519 distant"))
 }
}
