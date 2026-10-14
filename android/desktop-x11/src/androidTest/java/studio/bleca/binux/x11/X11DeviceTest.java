package studio.bleca.binux.x11;

import android.content.Context;
import android.content.Intent;
import androidx.test.core.app.ActivityScenario;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/** Real ARM64 device tests. These are compiled on the host, never claimed as executed there. */
public class X11DeviceTest {
 private int setup(byte[] cookie)throws IOException {
  byte[] name=cookie.length==0?new byte[0]:"MIT-MAGIC-COOKIE-1".getBytes(StandardCharsets.US_ASCII);
  ByteArrayOutputStream bytes=new ByteArrayOutputStream();
  ByteBuffer header=ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN);
  header.put((byte)'l').put((byte)0).putShort((short)11).putShort((short)0).putShort((short)name.length).putShort((short)cookie.length).putShort((short)0);
  bytes.write(header.array());bytes.write(name);while(bytes.size()%4!=0)bytes.write(0);bytes.write(cookie);while(bytes.size()%4!=0)bytes.write(0);
  try(Socket socket=new Socket("127.0.0.1",6001)) {
   socket.setSoTimeout(5000);socket.getOutputStream().write(bytes.toByteArray());return socket.getInputStream().read();
  }
 }
 @Test public void nativeXServerAcceptsCookieAndRejectsUnauthenticatedClient()throws Exception {
  Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
  try(ActivityScenario<MainActivity> activity=ActivityScenario.launch(MainActivity.class)) {
   File authority=new File(context.getFilesDir(),"x11/authority");
   byte[] cookie=null;
   for(int i=0;i<100;i++) {
    if(authority.isFile()) {
     try(DataInputStream in=new DataInputStream(new FileInputStream(authority))) {
      in.readUnsignedShort();in.skipBytes(in.readUnsignedShort());in.skipBytes(in.readUnsignedShort());in.skipBytes(in.readUnsignedShort());
      byte[] candidate=new byte[in.readUnsignedShort()];in.readFully(candidate);
      if(setup(candidate)==1){cookie=candidate;break;}
     } catch(IOException notReady) { /* Actual native server startup may still be in progress. */ }
    }
    Thread.sleep(100);
   }
   assertNotNull("The actual packaged X server must finish X11 setup",cookie);
   assertEquals("X11 must reject clients without the private cookie",0,setup(new byte[0]));
   activity.onActivity(a -> assertNotNull(a.findViewById(R.id.binux_settings_recovery)));
  } finally { context.stopService(new Intent(context,X11RuntimeService.class)); }
 }
}
