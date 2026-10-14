package studio.bleca.binux.x11;

import android.app.*;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.system.Os;
import android.util.Log;
import java.io.*;
import java.security.SecureRandom;

/** A real X.Org server loaded from the APK, running independently of its Android UI. */
public final class X11RuntimeService extends Service {
 private CmdEntryPoint server;
 private static final String CHANNEL="binux-x11-runtime";
 @Override public void onCreate() {
  super.onCreate();
  NotificationManager manager=getSystemService(NotificationManager.class);
  manager.createNotificationChannel(new NotificationChannel(CHANNEL,"Binux Desktop:X11",NotificationManager.IMPORTANCE_LOW));
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);
  PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,X11RuntimeService.class).setAction("stop"),PendingIntent.FLAG_IMMUTABLE);
  Notification notification=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_menu_view)
   .setContentTitle("Binux Desktop:X11").setContentText(getString(R.string.binux_server_notification))
   .setContentIntent(open).setOngoing(true).addAction(new Notification.Action.Builder(null,getString(R.string.exit_button_text),stop).build()).build();
  if(Build.VERSION.SDK_INT>=34)startForeground(11,notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);else startForeground(11,notification);
  try {
   File data=new File(getFilesDir(),"x11"); File tmp=new File(data,"tmp");
   if(!tmp.isDirectory()&&!tmp.mkdirs())throw new IOException("Cannot create X11 storage");
   File xkb=new File(data,"xkb"); copyAssets("xkb",xkb);
   File auth=new File(data,"authority"); writeAuthority(auth);
   Os.setenv("TMPDIR",tmp.getAbsolutePath(),true);
   Os.setenv("XKB_CONFIG_ROOT",xkb.getAbsolutePath(),true);
   // All X11 TCP sockets are patched to bind loopback, and authentication is mandatory.
   if(!CmdEntryPoint.start(new String[]{":1","-listen","tcp","-auth",auth.getAbsolutePath(),"-noreset"}))
    throw new IOException("Native X11 server initialization failed");
   server=new CmdEntryPoint();
  } catch(Exception e) {
   Log.e("BinuxX11","X server startup failed",e);
   stopSelf();
  }
 }
 private void copyAssets(String source,File target)throws IOException {
  String[] children=getAssets().list(source);
  if(children!=null&&children.length>0) {
   if(!target.isDirectory()&&!target.mkdirs())throw new IOException("Cannot create XKB directory");
   for(String child:children)copyAssets(source+"/"+child,new File(target,child));
  } else if(!target.isFile())try(InputStream in=getAssets().open(source);OutputStream out=new FileOutputStream(target)){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);}
 }
 private void writeAuthority(File file)throws IOException {
  byte[] cookie=new byte[16];new SecureRandom().nextBytes(cookie);
  // Xauthority FamilyWild record: the secret is stored only in private app storage.
  try(DataOutputStream out=new DataOutputStream(new FileOutputStream(file))) {
   out.writeShort(65535);out.writeShort(0);writeField(out,"1".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
   writeField(out,"MIT-MAGIC-COOKIE-1".getBytes(java.nio.charset.StandardCharsets.US_ASCII));writeField(out,cookie);
  }
  if(!file.setReadable(false,false)||!file.setWritable(false,false)||!file.setReadable(true,true)||!file.setWritable(true,true))throw new IOException("Cannot protect Xauthority file");
 }
 private void writeField(DataOutputStream out,byte[] data)throws IOException {out.writeShort(data.length);out.write(data);}
 @Override public IBinder onBind(Intent intent){return server;}
 @Override public int onStartCommand(Intent intent,int flags,int id){if(intent!=null&&"stop".equals(intent.getAction()))stopSelf();return START_NOT_STICKY;}
 @Override public void onDestroy(){stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();android.os.Process.killProcess(android.os.Process.myPid());}
}
