/* binux guest process bridge: real SSH PTY through same-UID Android service. */
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/ioctl.h>
#include <stddef.h>
#include <termios.h>
#include <signal.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
static volatile sig_atomic_t resized,stopped;
static void winch(int sig){ (void)sig;resized=1; }
static void terminate(int sig){ stopped=sig; }
static int all(int fd,const void *data,size_t len){const char*p=data;while(len){ssize_t n=write(fd,p,len);if(n<0&&errno==EINTR&&!stopped)continue;if(n<=0)return -1;p+=n;len-=n;}return 0;}
static int exact(int fd,void *data,size_t len){char*p=data;while(len){ssize_t n=read(fd,p,len);if(n<0&&errno==EINTR&&!stopped)continue;if(n<=0)return -1;p+=n;len-=n;}return 0;}
static int frame(int fd,char type,const void *data,uint32_t size){uint32_t n=htonl(size);return all(fd,&type,1)||all(fd,&n,4)||all(fd,data,size);}
static void quoted(FILE*f,const char*s){fputc('"',f);for(const unsigned char*p=(const unsigned char*)s;*p;p++){if(*p=='"'||*p=='\\')fputc('\\',f);if(*p<32)fprintf(f,"\\u%04x",*p);else fputc(*p,f);}fputc('"',f);}
int main(int argc,char**argv){
 signal(SIGPIPE,SIG_IGN);
 struct sigaction action={.sa_handler=terminate};sigemptyset(&action.sa_mask);sigaction(SIGTERM,&action,NULL);sigaction(SIGHUP,&action,NULL);
 const char*name=getenv("BINUX_STREAM");const char*distro="",*operation="exec";int i=1;
 while(i+1<argc){if(!strcmp(argv[i],"--runtime"))distro=argv[i+1];else if(!strcmp(argv[i],"--operation"))operation=argv[i+1];else break;i+=2;}
 if(!name){fputs("binux: stream service unavailable\n",stderr);return 69;}
 struct sockaddr_un addr={.sun_family=AF_UNIX};if(strlen(name)>sizeof(addr.sun_path)-2)return 2;
 memcpy(addr.sun_path+1,name,strlen(name));int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
 if(fd<0||connect(fd,(struct sockaddr*)&addr,offsetof(struct sockaddr_un,sun_path)+1+strlen(name))<0){perror("binux stream");return 69;}
 struct winsize ws={.ws_row=24,.ws_col=80};ioctl(STDIN_FILENO,TIOCGWINSZ,&ws);
 char cwd[4096];if(!getcwd(cwd,sizeof(cwd))){perror("cwd");close(fd);return 1;}
 FILE*f=fdopen(dup(fd),"w");if(!f){close(fd);return 1;}
 fputc('[',f);quoted(f,operation);fputc(',',f);quoted(f,distro);fputc(',',f);quoted(f,cwd);fprintf(f,",%u,%u,%s,[",ws.ws_col,ws.ws_row,isatty(STDIN_FILENO)?"true":"false");
 for(int a=i;a<argc;a++){if(a>i)fputc(',',f);quoted(f,argv[a]);}fputs("]]\n",f);fclose(f);
 struct termios previous;int raw=isatty(STDIN_FILENO)&&tcgetattr(STDIN_FILENO,&previous)==0;
 if(raw){struct termios next=previous;cfmakeraw(&next);tcsetattr(STDIN_FILENO,TCSANOW,&next);}
 signal(SIGWINCH,winch);int result=1,has_input=1;char buf[65536];
 for(;;){
  if(stopped)break;
  if(resized){resized=0;ioctl(STDIN_FILENO,TIOCGWINSZ,&ws);uint32_t size[2]={htonl(ws.ws_col),htonl(ws.ws_row)};if(frame(fd,'W',size,8))break;}
  struct pollfd p[2]={{fd,POLLIN,0},{has_input?STDIN_FILENO:-1,POLLIN,0}};int n=poll(p,2,-1);if(n<0&&errno==EINTR)continue;if(n<0)break;
  if(p[0].revents&(POLLIN|POLLHUP|POLLERR)){char type;uint32_t len;if(exact(fd,&type,1)||exact(fd,&len,4))break;len=ntohl(len);if(len>sizeof(buf)||exact(fd,buf,len))break;
   if(type=='X'&&len==4){uint32_t code;memcpy(&code,buf,4);result=ntohl(code);break;}
   if(type!='O'&&type!='E')break;if(all(type=='E'?STDERR_FILENO:STDOUT_FILENO,buf,len))break;
  }
  if(p[1].revents&(POLLIN|POLLHUP|POLLERR)){ssize_t got=read(STDIN_FILENO,buf,sizeof(buf));if(got<0&&errno==EINTR)continue;if(got<=0){has_input=0;frame(fd,'I',NULL,0);}else if(frame(fd,'I',buf,(uint32_t)got)){has_input=0;shutdown(fd,SHUT_WR);}}
 }
 if(raw)tcsetattr(STDIN_FILENO,TCSANOW,&previous);close(fd);if(stopped)return 128+stopped;return result>=0&&result<=255?result:1;
}
