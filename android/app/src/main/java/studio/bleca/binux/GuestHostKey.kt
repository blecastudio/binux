package studio.bleca.binux

/** systemd journal+console can split printf and cat into separate log records. */
object GuestHostKey {
 fun parse(log: String): String? {
  val marker=log.indexOf("BINUX_SSH_HOSTKEY")
  if(marker<0)return null
  val following=log.substring(marker+"BINUX_SSH_HOSTKEY".length).take(2048)
  return Regex("ssh-ed25519 [A-Za-z0-9+/=]+").find(following)?.value
 }
}
