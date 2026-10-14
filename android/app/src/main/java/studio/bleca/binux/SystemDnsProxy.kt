package studio.bleca.binux

import android.content.Context
import android.net.ConnectivityManager
import android.net.DnsResolver
import android.os.CancellationSignal
import java.net.*
import java.io.DataInputStream
import java.io.DataOutputStream
import java.util.concurrent.*

/** Guest DNS through Android's resolver, respecting Private DNS and VPN policy. */
@androidx.annotation.RequiresApi(29)
class SystemDnsProxy(context: Context): AutoCloseable {
 private val network=context.getSystemService(ConnectivityManager::class.java)
 private val udp=DatagramSocket(InetSocketAddress(InetAddress.getLoopbackAddress(),0))
 private val tcp=ServerSocket(udp.localPort,16,InetAddress.getLoopbackAddress())
 private val executor=Executors.newFixedThreadPool(4)
 private val callbacks=java.util.concurrent.Executor { command -> android.os.Handler(android.os.Looper.getMainLooper()).post(command) }
 private val pending=ConcurrentHashMap.newKeySet<CancellationSignal>()
 private val clients=ConcurrentHashMap.newKeySet<Socket>()
 private val slots=Semaphore(16)
 @Volatile private var closed=false
 val port get()=udp.localPort
 init {
  Thread({ while(!closed)try {
   val packet=DatagramPacket(ByteArray(65535),65535);udp.receive(packet)
   if(slots.tryAcquire())executor.execute { try { val reply=query(packet.data.copyOf(packet.length));udp.send(DatagramPacket(reply,reply.size,packet.socketAddress)) } catch(_: Exception) { } finally { slots.release() } }
  } catch(_: Exception) { if(closed)break } },"binux-dns-udp").apply { isDaemon=true;start() }
  Thread({ while(!closed)try {
   val socket=tcp.accept();socket.soTimeout=15000
   if(!slots.tryAcquire()) { socket.close();continue }
   clients.add(socket)
   executor.execute { socket.use { try {
    val input=DataInputStream(it.getInputStream());val output=DataOutputStream(it.getOutputStream())
    while(!closed) { val size=input.readUnsignedShort();require(size in 12..65535);val request=ByteArray(size);input.readFully(request);val reply=query(request);output.writeShort(reply.size);output.write(reply);output.flush() }
   } catch(_: Exception) { } finally { clients.remove(socket);slots.release() } } }
  } catch(_: Exception) { if(closed)break } },"binux-dns-tcp").apply { isDaemon=true;start() }
 }
 private fun query(packet: ByteArray): ByteArray {
  require(packet.size>=12 && packet[2].toInt() and 0x80==0) { "DNS query required" }
  val result=CompletableFuture<ByteArray>();val cancellation=CancellationSignal();pending.add(cancellation)
  try {
   DnsResolver.getInstance().rawQuery(network.activeNetwork,packet,DnsResolver.FLAG_EMPTY,callbacks,cancellation,object: DnsResolver.Callback<ByteArray> {
    override fun onAnswer(answer: ByteArray,rcode: Int) { result.complete(answer) }
    override fun onError(error: DnsResolver.DnsException) { result.completeExceptionally(error) }
   })
   return result.get(12,TimeUnit.SECONDS)
  } catch(_: Exception) {
   // A real SERVFAIL, preserving transaction ID, never an invented IP address.
   return packet.copyOf().apply { this[2]=(this[2].toInt() or 0x80).toByte();this[3]=((this[3].toInt() and 0xf0) or 2).toByte();for(i in 6..11)this[i]=0 }
  } finally { cancellation.cancel();pending.remove(cancellation) }
 }
 override fun close() { closed=true;udp.close();tcp.close();clients.forEach { it.close() };pending.forEach { it.cancel() };executor.shutdownNow() }
}
