package studio.bleca.binux

import android.net.LocalSocket
import android.net.LocalSocketAddress
import android.os.Build
import com.jcraft.jsch.JSch
import com.jcraft.jsch.KeyPair
import com.jcraft.jsch.Session
import kotlinx.coroutines.delay
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.ServerSocket
import java.net.URL
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

/** APK-managed emulator executes guest data under a separate Linux kernel. */
class VmManager(private val runtime: NativeRuntime, private val changed: () -> Unit) {
 data class Vm(val name: String, val process: Process, val port: Int, val log: File, val qmp: File, var hostKey: String?=null)
 private val machines=java.util.concurrent.ConcurrentHashMap<String,Vm>()
 private val forwards=java.util.concurrent.ConcurrentHashMap<String,Session>()
 private val downloading=java.util.concurrent.ConcurrentHashMap<String,Boolean>()
 private val connections=java.util.concurrent.ConcurrentHashMap<File,HttpURLConnection>()
 private val locks=mapOf("debian" to Mutex(),"ubuntu" to Mutex())
 private var dns: SystemDnsProxy?=null
 private val manifest by lazy {
  runtime.context.assets.open("runtime-manifest.json").use { JSONObject(it.bufferedReader().readText()) }
 }
 private fun directory(name: String): File { require(name in locks) { "Supported runtimes: debian, ubuntu" };return File(runtime.storage.base,"rootfs/$name") }
 val active get()=machines.values.count { it.process.isAlive }
 val downloads get()=downloading.size
 fun list(): String = locks.keys.joinToString("\n") { name ->
  val dir=directory(name);val installed=File(dir,"installed.json").exists()
  "$name installed=$installed running=${machines[name]?.process?.isAlive==true} engine=Linux VM (TCG)"
 }
 fun defaultName()=runtime.settings.text("distribution","debian")
 fun use(name: String) { directory(name);runtime.settings.set("distribution",name) }
 private fun engineCheck() {
  check(Build.VERSION.SDK_INT>=31) { "Linux VM requires Android 12/API 31 or later. Native Bash remains available." }
  check(File(runtime.vm).canExecute()) { "APK-managed ARM64 VM engine is missing. Install a complete binux APK." }
 }
 suspend fun install(name: String, output: (String)->Unit) = locks.getValue(name).withLock {
  engineCheck()
  val dir=directory(name);check(!File(dir,"installed.json").exists()) { "Runtime already installed; apt/pkg update upgrades its packages." }
  val assets=manifest.getJSONObject("assets")
  val names=listOf("$name-kernel","$name-initrd","$name-disk.qcow2")
  val required=manifest.getLong("disk_bytes")+names.sumOf { assets.getJSONObject(it).getLong("bytes") }
  check(runtime.storage.base.usableSpace>required) { "Insufficient storage: need $required bytes including disk growth and download cache." }
  dir.mkdirs()
  downloading[name]=true;changed()
  try {
   for(fileName in names) {
    val item=assets.getJSONObject(fileName);val target=File(dir,fileName)
    download(item,target,output)
   }
   File(dir,"installed.json").writeText(JSONObject().put("source_commit",manifest.getString("source_commit")).put("disk_bytes",manifest.getLong("disk_bytes")).toString())
   output("$name installed. Guest packages occupy this device's storage.\n")
  } catch(e: Exception) { names.forEach { File(dir,it).delete() };throw e }
  finally { downloading.remove(name);changed() }
 }
 private fun download(item: JSONObject, target: File, output: (String)->Unit) {
  val source=URL(item.getString("url"))
  require(source.protocol=="https" && source.host=="github.com" && source.path.startsWith("/blecastudio/binux/releases/download/")) { "Untrusted runtime source" }
  var url=source;var connection: HttpURLConnection?=null
  val temporary=File(target.parentFile,target.name+".part")
  try {
   repeat(6) {
    if(connection!=null)return@repeat
    require(url.protocol=="https" && url.userInfo==null)
    val candidate=url.openConnection() as HttpURLConnection
    candidate.connectTimeout=30000;candidate.readTimeout=30000;candidate.instanceFollowRedirects=false
    if(candidate.responseCode in listOf(301,302,303,307,308)) {
     url=URL(url,candidate.getHeaderField("Location") ?: error("Missing redirect"));candidate.disconnect()
    } else { check(candidate.responseCode in 200..299) { "Download HTTP ${candidate.responseCode}" };connection=candidate }
   }
   val conn=connection ?: error("Too many redirects")
   connections[target]=conn
   val digest=MessageDigest.getInstance("SHA-256");var count=0L;var last=0L;val expected=item.getLong("bytes")
   output("Source: $source\n${target.name}: 0/$expected bytes\n")
   conn.inputStream.use { input -> temporary.outputStream().use { file ->
    val buffer=ByteArray(65536)
    while(true) {
     val n=input.read(buffer);if(n<0)break;count+=n;check(count<=expected) { "Download exceeds manifest size" }
     file.write(buffer,0,n);digest.update(buffer,0,n)
     if(System.currentTimeMillis()-last>1000) { output("${target.name}: $count/$expected bytes\n");last=System.currentTimeMillis() }
    }
    file.fd.sync()
   } }
   check(count==expected && digest.digest().joinToString("") { "%02x".format(it) }==item.getString("sha256")) { "SHA-256/size verification failed: ${target.name}" }
   check(temporary.renameTo(target)) { "Cannot commit verified download" }
   output("${target.name}: SHA-256 verified\n")
  } finally { connections.remove(target);connection?.disconnect();temporary.delete() }
 }
 private fun identity(): File = synchronized(this) {
  val key=File(runtime.storage.base,"config/vm-ssh.pem")
  if(!key.exists()) {
   val pair=KeyPair.genKeyPair(JSch(),KeyPair.RSA,3072)
   try {
    val bytes=ByteArrayOutputStream();pair.writePrivateKey(bytes)
    val temp=File(key.parentFile,"vm-ssh.tmp");temp.writeBytes(bytes.toByteArray());temp.setReadable(false,false);temp.setWritable(false,false);temp.setReadable(true,true);temp.setWritable(true,true)
    check(temp.renameTo(key))
    val public=ByteArrayOutputStream();pair.writePublicKey(public,"binux-app")
    File(key.parentFile,"vm-ssh.pub").writeBytes(public.toByteArray())
   } finally { pair.dispose() }
  }
  val publicFile=File(key.parentFile,"vm-ssh.pub")
  if(!publicFile.exists()) {
   // Recover an initialization interrupted after committing the private key.
   // Keep the existing device identity instead of silently generating a new one.
   val pair=KeyPair.load(JSch(),key.path)
   try {
    val public=ByteArrayOutputStream();pair.writePublicKey(public,"binux-app")
    val temporary=File(publicFile.path+".tmp");temporary.writeBytes(public.toByteArray())
    check(temporary.renameTo(publicFile))
   } finally { pair.dispose() }
  }
  key
 }
 suspend fun start(name: String, output: (String)->Unit): Vm = locks.getValue(name).withLock {
  engineCheck();machines[name]?.takeIf { it.process.isAlive }?.let { return@withLock it }
  val dir=directory(name);check(File(dir,"installed.json").exists()) { "Install a runtime first: binux runtime install $name" }
  val memory=runtime.settings.text("vm-memory","1024").toInt().coerceIn(512,4096)
  val info=android.app.ActivityManager.MemoryInfo()
  runtime.context.getSystemService(android.app.ActivityManager::class.java).getMemoryInfo(info)
  check(!info.lowMemory && info.availMem>(memory+256L)*1024*1024) { "Insufficient available RAM for ${memory} MiB VM. Close other apps or set binux settings set vm-memory 512 for CLI." }
  identity()
  val bootstrap=File(dir,"bootstrap");bootstrap.mkdirs()
  fun copyAsset(path: String, destination: File) {
   val children=runtime.context.assets.list(path) ?: emptyArray()
   if(children.isNotEmpty()) { destination.mkdirs();children.forEach { copyAsset("$path/$it",File(destination,it)) } }
   else runtime.context.assets.open(path).use { input -> destination.outputStream().use { input.copyTo(it) } }
  }
  copyAsset("guest-core",File(bootstrap,"core"))
  copyAsset("setup-binux-desktop",File(bootstrap,"setup-binux-desktop"))
  copyAsset("prepare-guest-session",File(bootstrap,"prepare-guest-session"))
  File(bootstrap,"uid").writeText(android.os.Process.myUid().toString())
  File(bootstrap,"lang").writeText(runtime.settings.language)
  File(runtime.storage.base,"config/vm-ssh.pub").copyTo(File(bootstrap,"authorized_keys"),true)
  val state=File(dir,"state");state.mkdirs();state.setReadable(false,false);state.setWritable(false,false);state.setExecutable(false,false);state.setReadable(true,true);state.setWritable(true,true);state.setExecutable(true,true)
  val port=ServerSocket(0,0,java.net.InetAddress.getByName("127.0.0.1")).use { it.localPort }
  val log=File(runtime.storage.base,"logs/vm-$name.log");val qmp=File(dir,"qmp.sock");qmp.delete()
  val args=mutableListOf(runtime.vm,"-machine","virt","-cpu","cortex-a72","-smp","2","-m",memory.toString(),"-accel","tcg,thread=multi,split-wx=on","-nodefaults","-nographic","-serial","stdio",
   "-object","rng-random,id=entropy,filename=/dev/urandom","-device","virtio-rng-pci,rng=entropy",
   "-kernel",File(dir,"$name-kernel").path,"-initrd",File(dir,"$name-initrd").path,"-append","root=/dev/vda rw console=ttyAMA0 net.ifnames=0",
   "-drive","file=${File(dir,"$name-disk.qcow2").path},if=none,id=root,format=qcow2","-device","virtio-blk-pci,drive=root",
   "-netdev","user,id=net,hostfwd=tcp:127.0.0.1:$port-:22","-device","virtio-net-pci,netdev=net,romfile=",
   "-qmp","unix:${qmp.path},server=on,wait=off")
  for((id,folder,readOnly) in listOf(Triple("binux-bootstrap",bootstrap,true),Triple("binux-home",runtime.storage.home,false),Triple("binux-state",state,false))) {
   args+=listOf("-fsdev","local,id=$id,path=${folder.path},security_model=none${if(readOnly)",readonly=on" else ""}","-device","virtio-9p-pci,fsdev=$id,mount_tag=$id")
  }
  val pb=ProcessBuilder(args).directory(dir).redirectErrorStream(true).redirectOutput(log)
  pb.environment().clear();pb.environment().putAll(runtime.environment())
  if(Build.VERSION.SDK_INT>=31) {
   if(dns==null)dns=SystemDnsProxy(runtime.context)
   pb.environment()["BINUX_DNS_PORT"]=dns!!.port.toString()
  } else error("Linux VM requires Android 12+")
  val vm=Vm(name,pb.start(),port,log,qmp);machines[name]=vm;changed()
  output("Starting $name Linux VM ($memory MiB RAM). Boot log: binux runtime logs $name\n")
  try {
   repeat(180) {
    check(vm.process.isAlive) { "VM exited (${vm.process.exitValue()}); inspect binux runtime logs $name" }
    if(hostKey(vm)!=null) {
     try {
      val session=connect(vm)
      try {
       val channel=session.openChannel("exec") as com.jcraft.jsch.ChannelExec
       val errors=ByteArrayOutputStream();channel.setErrStream(errors)
       channel.setCommand("/usr/local/bin/binux-entry /home/binux /bin/bash /run/binux-bootstrap/prepare-guest-session")
       channel.connect(10000)
       repeat(300) { if(!channel.isClosed)delay(100) }
       val result=channel.exitStatus;channel.disconnect()
       check(result==0) { "Guest environment setup failed ($result): ${errors.toString("UTF-8").takeLast(2048)}" }
      } finally { session.disconnect() }
      output("$name SSH public-key authentication and isolated pip environment verified.\n");return@withLock vm
     } catch(_: com.jcraft.jsch.JSchException) { }
    }
    delay(1000)
   }
   error("Guest boot/SSH timed out; inspect binux runtime logs $name")
  } catch(e: Exception) { vm.process.destroy();machines.remove(name);changed();throw e }
 }
 private fun tail(file: File): String = if(!file.exists())"" else java.io.RandomAccessFile(file,"r").use { input ->input.seek((input.length()-256*1024).coerceAtLeast(0));val bytes=ByteArray((input.length()-input.filePointer).toInt());input.readFully(bytes);bytes.toString(Charsets.UTF_8) }
 private fun hostKey(vm: Vm): String? {
  vm.hostKey?.let { return it }
  val key=GuestHostKey.parse(tail(vm.log)) ?: return null
  vm.hostKey=key;return key
 }
 fun connect(vm: Vm): Session {
  check(vm.process.isAlive) { "Guest process stopped" }
  val key=hostKey(vm) ?: error("Guest host key unavailable")
  val jsch=JSch();jsch.addIdentity(identity().path)
  jsch.setKnownHosts(ByteArrayInputStream("[127.0.0.1]:${vm.port} $key\n".toByteArray()))
  return jsch.getSession("binux","127.0.0.1",vm.port).apply { setConfig("StrictHostKeyChecking","yes");setConfig("PreferredAuthentications","publickey");timeout=15000;connect(10000);setServerAliveInterval(15000) }
 }
 fun logs(name: String)=tail(File(runtime.storage.base,"logs/vm-$name.log")).ifEmpty { "No VM log" }
 suspend fun forward(name: String, port: Int, allowNetwork: Boolean=false): String {
  require(port in 1024..65535)
  val id="$name:$port";check(forwards[id]?.isConnected!=true) { "Port forwarding already active" }
  val machine=start(name) { };val session=connect(machine)
  try {
   val bind=if(allowNetwork)"0.0.0.0" else "127.0.0.1"
   session.setPortForwardingL(bind,port,"127.0.0.1",port)
   forwards[id]=session
   return "$bind:$port -> $name:127.0.0.1:$port (SSH authenticated)"
  } catch(e: Exception) { session.disconnect();throw e }
 }
 fun unforward(name: String,port: Int) { forwards.remove("$name:$port")?.disconnect() }
 suspend fun stop(name: String) {
  val vm=machines[name] ?: return
  forwards.keys.filter { it.startsWith("$name:") }.forEach { forwards.remove(it)?.disconnect() }
  runCatching { qmp(vm,"system_powerdown") }
  repeat(30) { if(!vm.process.isAlive)return@repeat;delay(1000) }
  if(vm.process.isAlive) { vm.process.destroy();vm.process.waitFor(2,TimeUnit.SECONDS);if(vm.process.isAlive)vm.process.destroyForcibly() }
  machines.remove(name);changed()
 }
 suspend fun remove(name: String, confirmed: Boolean) = locks.getValue(name).withLock {
  require(confirmed) { "Runtime removal deletes its packages and private state. Use binux runtime uninstall $name --yes after backing it up. Shared ~/ is kept." }
  check(machines[name]?.process?.isAlive!=true) { "Stop the VM first" }
  check(directory(name).deleteRecursively()) { "Could not remove runtime files" }
 }
 fun stopAll() { connections.values.forEach { it.disconnect() };forwards.values.forEach { it.disconnect() };forwards.clear();machines.values.forEach { runCatching { qmp(it,"system_powerdown") };it.process.destroy() };machines.clear();if(Build.VERSION.SDK_INT>=31)dns?.close();dns=null;changed() }
 private fun qmp(vm: Vm, command: String) {
  LocalSocket().use { socket ->
   socket.soTimeout=2000;socket.connect(LocalSocketAddress(vm.qmp.path,LocalSocketAddress.Namespace.FILESYSTEM))
   val reader=socket.inputStream.bufferedReader();reader.readLine()
   val writer=socket.outputStream.bufferedWriter();writer.write("{\"execute\":\"qmp_capabilities\"}\n");writer.flush();reader.readLine()
   writer.write(JSONObject().put("execute",command).toString()+"\n");writer.flush()
  }
 }
 fun guestDirectory(cwd: String): String {
  val home=runtime.storage.home.canonicalFile;val current=File(cwd).canonicalFile
  require(current==home || current.path.startsWith(home.path+"/")) { "Guest commands need a directory inside ~/ (shared workspace)." }
  return "/home/binux"+current.path.removePrefix(home.path)
 }
 companion object { fun quote(value: String)="'"+value.replace("'","'\"'\"'")+"'" }
}
