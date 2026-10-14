#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <fcntl.h>
int main(int argc, char **argv) {
 if (argc < 2) { fprintf(stderr,"usage: binuxjob <executable> [args...]\n"); return 2; }
 if (setsid() < 0) { perror("setsid"); return 1; }
 const char *pid_path=getenv("BINUX_PID_FILE");
 if(pid_path) {
  int fd=open(pid_path,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
  if(fd<0) { perror("pid handshake"); return 1; }
  char buffer[32]; int count=snprintf(buffer,sizeof(buffer),"%ld\n",(long)getpid());
  if(write(fd,buffer,(size_t)count)!=count) { close(fd); return 1; }
  close(fd); unsetenv("BINUX_PID_FILE");
 }
 sigset_t signals;
 sigfillset(&signals); sigprocmask(SIG_UNBLOCK, &signals, NULL);
 execvp(argv[1], argv+1);
 int saved_errno=errno; perror(argv[1]); return saved_errno == ENOENT ? 127 : 126;
}
