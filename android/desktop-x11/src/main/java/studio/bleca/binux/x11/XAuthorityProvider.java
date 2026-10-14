package studio.bleca.binux.x11;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.*;
/** Read-only X11 credentials shared solely with apps signed with the same Binux key. */
public final class XAuthorityProvider extends ContentProvider {
 @Override public boolean onCreate(){return true;}
 @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException {
  if(!"r".equals(mode)||!"/authority".equals(uri.getPath()))throw new FileNotFoundException("Read-only authority endpoint");
  if(!X11RuntimeService.running)throw new FileNotFoundException("Start the X11 display server first");
  return ParcelFileDescriptor.open(new File(getContext().getFilesDir(),"x11/authority"),ParcelFileDescriptor.MODE_READ_ONLY);
 }
 @Override public String getType(Uri u){return "application/x-xauthority";}
 @Override public Cursor query(Uri u,String[] p,String s,String[] a,String o){return null;}
 @Override public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
 @Override public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
 @Override public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
}
