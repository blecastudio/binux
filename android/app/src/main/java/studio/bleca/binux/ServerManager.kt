package studio.bleca.binux

import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class ServerManager(private val runtime: NativeRuntime, private val jobs: BackgroundProcessManager) {
 private val file=File(runtime.storage.base,"config/servers.json")
 private fun data()=if(file.exists())JSONObject(file.readText()) else JSONObject()
 fun port(name: String)=data().getJSONObject(name).getInt("port").toString()
 fun create(name: String,kind: String,port: Int): String {
  require(name.matches(Regex("[A-Za-z0-9_-]{1,48}")) && kind in listOf("python","node") && port in 1024..65535)
  val project=File(runtime.storage.home,"projects/$name")
  check(!project.exists() && !data().has(name)) { "Project/server already exists" }
  check(project.mkdirs()) { "Cannot create project" }
  val argv=if(kind=="python") {
   File(project,"server.py").writeText("from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nThreadingHTTPServer(('127.0.0.1', $port), SimpleHTTPRequestHandler).serve_forever()\n")
   listOf("python3","-u","server.py")
  } else {
   File(project,"server.js").writeText("const http=require('node:http');\nhttp.createServer((req,res)=>res.end('binux server\\n')).listen($port,'127.0.0.1');\n")
   listOf("node","server.js")
  }
  return register(name,port,project.path,argv)
 }
 fun register(name: String,port: Int,cwd: String,argv: List<String>): String {
  require(name.matches(Regex("[A-Za-z0-9_-]{1,48}"))) { "Invalid server name" }
  require(port in 1024..65535 && argv.isNotEmpty() && File(cwd).isDirectory) { "Expected name port cwd command [args...]" }
  val data=data(); data.put(name,JSONObject().put("port",port).put("cwd",cwd).put("argv",JSONArray(argv)))
  val temp=File(file.path+".tmp");temp.writeText(data.toString(2)); check(temp.renameTo(file)) { "Cannot persist servers" }
  return "Registered $name; preview http://127.0.0.1:$port. Command must bind to loopback."
 }
 fun start(name: String): String {
  check(jobs.jobs.none { it.server==name && it.process.isAlive }) { "Server already running" }
  val config=data().getJSONObject(name); val argv=config.getJSONArray("argv")
  val j=jobs.run(List(argv.length()) { argv.getString(it) },config.getString("cwd"),name,config.optBoolean("restartOnFailure",false))
  return "${j.id}: started $name; configured preview http://127.0.0.1:${config.getInt("port")} (read logs to confirm listening)"
 }
 fun restartPolicy(name: String,on: Boolean): String { val d=data(); d.getJSONObject(name).put("restartOnFailure",on); val temp=File(file.path+".tmp");temp.writeText(d.toString(2));check(temp.renameTo(file));return "restart-on-failure=$on (max 3 retries; next start)" }
 fun stop(name: String): String { val j=jobs.jobs.lastOrNull { it.server==name } ?: error("Server has no job"); jobs.stop(j.id); return "Stop requested ${j.id}" }
 fun logs(name: String)=jobs.logs(jobs.jobs.lastOrNull { it.server==name }?.id ?: error("Server has no job"))
 fun list(): String { val d=data(); return d.keys().asSequence().joinToString("\n") { name -> val j=jobs.jobs.lastOrNull { it.server==name }; "$name :${d.getJSONObject(name).getInt("port")} ${if(j?.process?.isAlive==true)j.state else "stopped"}" }.ifEmpty { "No servers registered" } }
}
