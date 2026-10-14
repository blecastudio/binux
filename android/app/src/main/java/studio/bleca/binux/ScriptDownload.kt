package studio.bleca.binux

import java.net.HttpURLConnection
import java.net.URL
/** Minimal HTTPS text downloader for reviewed installer scripts; not a full curl replacement. */
object ScriptDownload {
 fun fetch(args: List<String>): CommandRouter.Result = try {
  require(args.size==2 && args[0] in listOf("-Lf","-fL","-L","-f")) { "Usage: curl -Lf <https-script-url>. This adapter supports UTF-8 scripts up to 1 MiB." }
  var url=URL(args[1]); val follow='L' in args[0]
  var result: String?=null
  repeat(6) {
   if(result!=null)return@repeat
   require(url.protocol=="https" && url.userInfo==null) { "HTTPS without embedded credentials is required" }
   val connection=url.openConnection() as HttpURLConnection
   connection.instanceFollowRedirects=false;connection.connectTimeout=15000;connection.readTimeout=15000
   try {
    val code=connection.responseCode
    if(code in listOf(301,302,303,307,308)) {
     require(follow) { "Redirect requires -L" }
     url=URL(url,connection.getHeaderField("Location") ?: error("Missing redirect location"))
    } else {
     require(code in 200..299) { "HTTP $code" }
     val bytes=connection.inputStream.use { input ->
      val out=java.io.ByteArrayOutputStream(); val buffer=ByteArray(8192)
      while(out.size()<=1048576) { val n=input.read(buffer); if(n<0)break;out.write(buffer,0,n) }
      out.toByteArray()
     }
     require(bytes.size<=1048576) { "Script exceeds 1 MiB limit" }
     require(bytes.none { it==0.toByte() }) { "Binary download unsupported by the script adapter" }
     result=bytes.toString(Charsets.UTF_8)
    }
   } finally { connection.disconnect() }
  }
  CommandRouter.Result(0,result ?: error("Too many redirects"))
 } catch(e: Exception) { CommandRouter.Result(22,"curl: ${e.message}\n") }
}
