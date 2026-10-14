package studio.bleca.binux

import android.os.Process as AndroidProcess
import androidx.compose.runtime.mutableStateListOf
import kotlinx.coroutines.*
import java.io.File
import java.util.UUID
import org.json.JSONArray

@OptIn(ExperimentalCoroutinesApi::class)
class BackgroundProcessManager(private val runtime: NativeRuntime, private val db: BinuxDatabase, private val changed: () -> Unit) {
 data class Job(val id: String, val argv: List<String>, val cwd: String, val process: Process, val pid: Int, val birth: Long, val started: Long, val log: File, val server: String?=null, var state: String="running", var exit: Int?=null, var restartOnFailure: Boolean=false, val retries: Int=3)
 val jobs=mutableStateListOf<Job>()
 private val scope=CoroutineScope(SupervisorJob()+Dispatchers.Main)
 private val persistence=CoroutineScope(SupervisorJob()+Dispatchers.IO.limitedParallelism(1))
 private val autoFile=File(runtime.storage.base,"config/autostart-jobs.json")
 private fun autoRecords()=if(autoFile.exists())org.json.JSONObject(autoFile.readText()) else org.json.JSONObject()
 private fun saveAuto(values: org.json.JSONObject) { val temp=File(autoFile.path+".tmp");temp.writeText(values.toString());check(temp.renameTo(autoFile)) }
 fun startSaved() {
  check(runtime.settings.flag("autostart") && runtime.settings.flag("background"))
  val records=autoRecords();saveAuto(org.json.JSONObject())
  records.keys().forEach { id -> val record=records.getJSONObject(id);val argv=record.getJSONArray("argv");runCatching { run(List(argv.length()) { argv.getString(it) },record.getString("cwd"),autoStart=true) } }
 }
 init { persistence.launch { db.jobs().markInterrupted() } }
 private fun save(j: Job) {
  val row=JobRecord(j.id,JSONArray(j.argv).toString(),j.cwd,j.pid,j.state,j.started,j.log.path,j.server,j.exit)
  persistence.launch { db.jobs().save(row) }
 }
 fun history(): List<JobRecord> = runBlocking(Dispatchers.IO) { db.jobs().history().filter { row -> jobs.none { it.id==row.id } } }
 fun run(argv: List<String>, cwd: String=runtime.storage.home.path, server: String?=null, restartOnFailure: Boolean=false, retries: Int=3,autoStart: Boolean=false): Job {
  require(argv.isNotEmpty()) { "Provide a command" }
  require(File(cwd).isDirectory) { "Working directory does not exist" }
  check(runtime.storage.base.usableSpace > 1024*1024) { "Insufficient storage (need 1 MiB free for logs)" }
  val id=UUID.randomUUID().toString().take(8)
  val log=File(runtime.storage.base,"logs/$id.log")
  // "$@" preserves every argument; no command is reconstructed through string concatenation.
  val guestCommands=setOf("python","python3","pip","pip3","node","npm","pkg","git","ssh","wbs")
  val executableArgs=when(argv.first()) {
   in guestCommands -> listOf(runtime.bridge)+(if(argv.first()=="python")listOf("python3")+argv.drop(1) else argv)
   "apt","apt-get" -> listOf(runtime.bridge,"sudo")+argv
   else -> argv
  }
  val pb=ProcessBuilder(listOf(runtime.job,runtime.bash,"-c","exec \"\$@\"","binux-job")+executableArgs)
   .directory(File(cwd)).redirectErrorStream(true).redirectOutput(log)
  val pidFile=File(runtime.storage.base,"cache/$id.pid")
  pb.environment().clear(); pb.environment().putAll(runtime.environment()); pb.environment()["BINUX_PID_FILE"]=pidFile.path
  val process=pb.start()
  var pid: Int?=null
  for(attempt in 0..200) { pid=runCatching { pidFile.readText().trim().toIntOrNull() }.getOrNull(); if(pid!=null || !process.isAlive)break; Thread.sleep(5) }
  pidFile.delete()
  if(pid==null) { process.destroy(); error("Process PID handshake failed; inspect ${log.name}") }
  val job=Job(id,argv,cwd,process,pid,NativeProcess.birth(pid),System.currentTimeMillis(),log,server,restartOnFailure=restartOnFailure,retries=retries)
  jobs.add(job); save(job); changed()
  if(autoStart) { val records=autoRecords();records.put(id,org.json.JSONObject().put("argv",JSONArray(argv)).put("cwd",cwd));saveAuto(records) }
  scope.launch {
   val code=withContext(Dispatchers.IO) { job.process.waitFor() }
   val stopped=job.state=="stopping"
   NativeProcess.signalSession(job.pid,job.birth,15)
   job.state="exited"; job.exit=code; save(job); changed()
   delay(2000); NativeProcess.signalSession(job.pid,job.birth,9)
   if(code!=0 && !stopped && job.restartOnFailure && job.retries>0) run(job.argv,job.cwd,job.server,true,job.retries-1)
  }
  return job
 }
 fun get(id: String)=jobs.firstOrNull { it.id==id } ?: error("Unknown job: $id")
 fun stop(id: String) {
  val records=autoRecords();records.remove(id);saveAuto(records)
  val j=get(id); j.restartOnFailure=false; if(!j.process.isAlive)return
  j.state="stopping"; NativeProcess.signalSession(j.pid,j.birth,15)
  scope.launch { delay(2000); NativeProcess.signalSession(j.pid,j.birth,9) }
  save(j); changed()
 }
 fun resumeAll() { jobs.filter { it.state=="paused" && it.process.isAlive }.forEach { NativeProcess.signalGroup(it.pid,18); it.state="running" }; changed() }
 fun stopAll() = jobs.toList().forEach { stop(it.id) }
 fun restart(id: String): Job {
  val j=jobs.firstOrNull { it.id==id }
  if(j!=null) { check(!j.process.isAlive) { "Stop the job and wait for exit first" }; return run(j.argv,j.cwd,j.server) }
  val old=runBlocking(Dispatchers.IO) { db.jobs().get(id) } ?: error("Unknown job: $id")
  check(old.state !in listOf("running","paused","stopping")) { "Job metadata recovery is pending" }
  val array=JSONArray(old.argv); return run(List(array.length()) { array.getString(it) },old.cwd,old.server)
 }
 fun describe(j: Job): String {
  val pid=j.pid
  val rss=runCatching { File("/proc/$pid/status").readLines().firstOrNull { it.startsWith("VmRSS:") } ?: "RSS unavailable" }.getOrDefault("RSS unavailable")
  val cpu=runCatching { val fields=File("/proc/$pid/stat").readText().substringAfterLast(") ").split(" "); "CPU ticks ${fields[11].toLong()+fields[12].toLong()}" }.getOrDefault("CPU unavailable")
  return "${j.id} pid=$pid ${if(j.process.isAlive)j.state else "exited"} exit=${j.exit} elapsed=${(System.currentTimeMillis()-j.started)/1000}s $rss $cpu"
 }
 fun logs(id: String): String {
  val f=jobs.firstOrNull { it.id==id }?.log ?: runBlocking(Dispatchers.IO) { db.jobs().get(id) }?.let { File(it.log) } ?: error("Unknown job: $id")
  java.io.RandomAccessFile(f,"r").use { raf -> raf.seek((raf.length()-128*1024).coerceAtLeast(0)); val bytes=ByteArray((raf.length()-raf.filePointer).toInt()); raf.readFully(bytes); return bytes.toString(Charsets.UTF_8) }
 }
}
