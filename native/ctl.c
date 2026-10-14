#include <sys/socket.h>
#include <sys/un.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
static int send_all(int fd, const char *p, size_t n) {
 while(n) { ssize_t k=write(fd,p,n); if(k<0 && errno==EINTR) continue; if(k<=0) return -1; p+=k; n-=(size_t)k; } return 0;
}
int main(int argc,char **argv) {
 const char *name=getenv("BINUX_CONTROL");
 if(!name) { fprintf(stderr,"binux: Android runtime control socket unavailable\n"); return 1; }
 struct sockaddr_un addr={.sun_family=AF_UNIX};
 if(strlen(name)>sizeof(addr.sun_path)-2) return 2;
 memcpy(addr.sun_path+1,name,strlen(name));
 int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
 if(fd<0 || connect(fd,(struct sockaddr*)&addr,(socklen_t)(offsetof(struct sockaddr_un,sun_path)+1+strlen(name)))<0) { perror("binux control"); if(fd>=0)close(fd); return 1; }
 FILE *stream=fdopen(dup(fd),"w");
 if(!stream) { close(fd); return 1; }
 fputc('[',stream);
 for(int i=1;i<argc;i++) {
  if(i>1)fputc(',',stream); fputc('"',stream);
  for(const unsigned char *s=(const unsigned char*)argv[i];*s;s++) {
   if(*s=='"'||*s=='\\')fputc('\\',stream);
   if(*s<32)fprintf(stream,"\\u%04x",*s); else fputc(*s,stream);
  }
  fputc('"',stream);
 }
 fputs("]\n",stream); if(fclose(stream)!=0){close(fd);return 1;}
 shutdown(fd,SHUT_WR);
 char code[16]; size_t n=0; int complete=0;
 while(n<sizeof(code)-1) { char c; ssize_t k=read(fd,&c,1); if(k<0&&errno==EINTR)continue; if(k!=1){close(fd);return 1;} if(c=='\n'){complete=1;break;} code[n++]=c; }
 code[n]=0;
 char *end; long status=strtol(code,&end,10);
 if(!complete || n==0 || *end || status<0 || status>255) { close(fd); return 1; }
 char buf[8192]; ssize_t k;
 for(;;) { k=read(fd,buf,sizeof(buf)); if(k<0&&errno==EINTR)continue; if(k<=0)break; if(send_all(STDOUT_FILENO,buf,(size_t)k)<0){close(fd);return 1;} }
 close(fd); return k<0 ? 1 : (int)status;
}
