package studio.bleca.binux

import android.content.Context
import android.media.*
import com.jcraft.jsch.ChannelExec
import kotlinx.coroutines.*

/** Capture a guest PulseAudio monitor over authenticated SSH and play real PCM. */
class DesktopAudio(private val context: Context,private val vm: VmManager,private val changed: ()->Unit) {
 private val scope=CoroutineScope(SupervisorJob()+Dispatchers.IO)
 private var task: Job?=null
 private var track: AudioTrack?=null
 private var session: com.jcraft.jsch.Session?=null
 private val manager=context.getSystemService(AudioManager::class.java)
 private var focus: AudioFocusRequest?=null
 @Volatile var state="stopped";private set
 val active get()=state in listOf("starting","waiting for PCM","playing")
 fun start() {
  check(!active) { "Desktop audio already active" }
  state="starting";changed()
  task=scope.launch {
   val token=java.util.UUID.randomUUID().toString().replace("-","")
   var machine: VmManager.Vm?=null
   try {
    machine=vm.start(vm.defaultName()) { }
    val connected=vm.connect(machine);session=connected
    val attributes=AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build()
    val request=AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN).setAudioAttributes(attributes).setOnAudioFocusChangeListener { value -> if(value==AudioManager.AUDIOFOCUS_LOSS)stop() }.build()
    check(manager.requestAudioFocus(request)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED) { "Audio focus denied" };focus=request
    val minimum=AudioTrack.getMinBufferSize(48000,AudioFormat.CHANNEL_OUT_STEREO,AudioFormat.ENCODING_PCM_16BIT)
    check(minimum>0)
    val player=AudioTrack.Builder().setAudioAttributes(attributes).setAudioFormat(AudioFormat.Builder().setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_STEREO).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build()).setBufferSizeInBytes(minimum*4).setTransferMode(AudioTrack.MODE_STREAM).build()
    track=player
    val channel=connected.openChannel("exec") as ChannelExec
    val script="set -e; command -v parec >/dev/null; pulseaudio --check || pulseaudio --start --exit-idle-time=-1; pactl list short sinks | grep -q binux-audio || pactl load-module module-null-sink sink_name=binux-audio >/dev/null; pactl set-default-sink binux-audio; exec parec --raw --format=s16le --rate=48000 --channels=2 --device=binux-audio.monitor"
    channel.setCommand("/usr/local/bin/binux-entry /home/binux python3 -m binux.remote run $token /bin/bash -ec "+VmManager.quote(script))
    val input=channel.inputStream;val errors=java.io.ByteArrayOutputStream();channel.setErrStream(errors);channel.connect(10000)
    player.play();state="waiting for PCM";changed()
    val buffer=ByteArray(16384)
    while(isActive) {
     val n=input.read(buffer);if(n<0)break
     if(state!="playing") { state="playing";changed() }
     var offset=0
     while(offset<n && isActive) { val written=player.write(buffer,offset,n-offset,AudioTrack.WRITE_BLOCKING);check(written>0) { "AudioTrack write failed" };offset+=written }
    }
    if(isActive && channel.exitStatus!=0)error(errors.toString("UTF-8").takeLast(2048).ifEmpty { "Guest audio capture ended (${channel.exitStatus}); install the Desktop audio feature." })
    channel.disconnect()
   } catch(e: Exception) { state=if(e is CancellationException)"stopped" else "error: ${e.message}" }
   finally {
    session?.disconnect();session=null
    track?.let { runCatching { it.stop() };it.release() };track=null
    focus?.let(manager::abandonAudioFocusRequest);focus=null
    val current=machine
    if(current!=null && current.process.isAlive)runCatching {
     vm.connect(current).let { cleanup -> try { val channel=cleanup.openChannel("exec") as ChannelExec;channel.setCommand("/usr/local/bin/binux-entry /home/binux python3 -m binux.remote stop $token");channel.connect(3000);Thread.sleep(200);channel.disconnect() } finally { cleanup.disconnect() } }
    }
    if(!state.startsWith("error"))state="stopped";changed()
   }
  }
 }
 fun stop() { task?.cancel();session?.disconnect();runCatching { track?.pause() };state="stopped";changed() }
}
