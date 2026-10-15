package studio.bleca.binux

import android.net.LocalServerSocket
import android.net.LocalSocket
import com.jcraft.jsch.ChannelExec
import kotlinx.coroutines.*
import org.json.JSONArray
import java.io.DataInputStream
import java.io.DataOutputStream
import java.io.OutputStream

class GuestBridge(private val runtime: NativeRuntime, private val vm: VmManager, private val scope: CoroutineScope) {
 private val server=LocalServerSocket(runtime.stream)
 fun start() { scope.launch {
  while(isActive) {
   val peer=try { server.accept() } catch(_: Exception) { break }
   launch { peer.use { if(it.peerCredentials.uid==android.os.Process.myUid())handle(it) } }
  }
 } }
 fun close() { runCatching { server.close() } }
 private suspend fun handle(peer: LocalSocket)=coroutineScope {
  val input=DataInputStream(peer.inputStream);val output=DataOutputStream(peer.outputStream)
  fun send(type: Char, data: ByteArray, offset: Int=0, length: Int=data.size) = synchronized(output) {
   require(length<=65536);output.writeByte(type.code);output.writeInt(length);output.write(data,offset,length);output.flush()
  }
  fun text(message: String)=send('O',message.toByteArray())
  var code=1
  try {
   val header=java.io.ByteArrayOutputStream()
   while(true) { val c=input.read();check(c>=0) { "Request closed" };if(c==10)break;check(header.size()<65536);header.write(c) }
   val request=JSONArray(header.toString("UTF-8"));require(request.length()==7)
   val operation=request.getString(0);val name=request.getString(1).ifEmpty(vm::defaultName)
   require(name in listOf("debian","ubuntu"))
   when(operation) {
    "install" -> vm.install(name,::text)
    "start" -> vm.start(name,::text)
    "stop" -> { vm.stop(name);text("$name stopped\n") }
    "uninstall" -> { vm.remove(name,request.getJSONArray(6).optString(0)=="--yes");text("$name removed; shared home retained\n") }
    "forward" -> {
     val options=request.getJSONArray(6);val port=options.getString(0).toInt()
     val allowNetwork=options.length()==2 && options.getString(1)=="--allow-network"
     require(options.length()==1 || allowNetwork) { "binux runtime forward distro port [--allow-network]" }
     text(vm.forward(name,port,allowNetwork)+"\n")
    }
    "unforward" -> { vm.unforward(name,request.getJSONArray(6).getString(0).toInt());text("Port forwarding stopped\n") }
    "exec" -> {
     val array=request.getJSONArray(6);require(array.length() in 1..256)
     val original=List(array.length()) { array.getString(it).also { value -> require('\u0000' !in value) } }
     val argv=if(original.first()=="setup-binux-desktop")listOf("/bin/bash","/run/binux-bootstrap/setup-binux-desktop")+original.drop(1) else original
     val guestCwd=vm.guestDirectory(request.getString(2))
     // Keep boot progress out of program stdout (pipes, JSON and curl output).
     val machine=vm.start(name) { send('E',it.toByteArray()) };val session=vm.connect(machine)
     val token=java.util.UUID.randomUUID().toString().replace("-","")
     var remoteFinished=false
     try {
      val channel=session.openChannel("exec") as ChannelExec
      channel.setCommand((listOf("/usr/local/bin/binux-entry",guestCwd,"env","BINUX_DEVICE_TARGET=android","python3","-m","binux.remote","run",token)+argv).joinToString(" ",transform=VmManager::quote))
      channel.setPty(request.getBoolean(5));channel.setPtyType("xterm-256color",request.getInt(3).coerceIn(1,1000),request.getInt(4).coerceIn(1,1000),0,0)
      fun stream(type: Char)=object: OutputStream() {
       override fun write(value: Int)=write(byteArrayOf(value.toByte()),0,1)
       override fun write(bytes: ByteArray, offset: Int, length: Int) { var p=offset;var remaining=length;while(remaining>0) { val n=remaining.coerceAtMost(65536);send(type,bytes,p,n);p+=n;remaining-=n } }
      }
      channel.setOutputStream(stream('O'));channel.setErrStream(stream('E'))
      val stdin=channel.outputStream
      channel.connect(15000)
      val reader=launch(Dispatchers.IO) {
       try {
        while(isActive && !channel.isClosed) {
         val type=input.read();if(type<0)break
         val n=input.readInt();require(n in 0..65536);val data=ByteArray(n);input.readFully(data)
         when(type.toChar()) {
          'I' -> if(n==0)stdin.close() else { stdin.write(data);stdin.flush() }
          'W' -> { require(n==8);val size=DataInputStream(data.inputStream());channel.setPtySize(size.readInt().coerceIn(1,1000),size.readInt().coerceIn(1,1000),0,0) }
          else -> error("Unknown frame")
         }
        }
       } catch(_: Exception) { } finally { if(!channel.isClosed)channel.disconnect() }
      }
      try { while(!channel.isClosed)delay(50);code=channel.exitStatus.takeIf { it in 0..255 } ?: 1;remoteFinished=channel.exitStatus>=0 }
      finally { channel.disconnect();runCatching { peer.shutdownInput() };reader.cancelAndJoin() }
     } finally {
      session.disconnect()
      if(!remoteFinished && machine.process.isAlive)runCatching {
       vm.connect(machine).let { cleanup -> try {
        val stop=cleanup.openChannel("exec") as ChannelExec
        stop.setCommand("/usr/local/bin/binux-entry /home/binux python3 -m binux.remote stop $token")
        stop.connect(5000)
        repeat(50) { if(!stop.isClosed)delay(100) }
        stop.disconnect()
       } finally { cleanup.disconnect() } }
      }
     }
    }
    else -> error("Unsupported VM operation")
   }
   if(operation!="exec")code=0
  } catch(e: Exception) { runCatching { send('E',("binux: ${e.message}\n").toByteArray()) } }
  runCatching { send('X',java.nio.ByteBuffer.allocate(4).putInt(code).array()) }
 }
}
