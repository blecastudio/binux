#include <jni.h>
#include <signal.h>
#include <errno.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int read_birth(int pid, long long *birth) {
 char path[64],buffer[4096]; snprintf(path,sizeof(path),"/proc/%d/stat",pid);
 FILE *file=fopen(path,"r"); if(!file)return -1;
 char *line=fgets(buffer,sizeof(buffer),file); fclose(file); if(!line)return -1;
 char *fields=strrchr(buffer,')'); if(!fields)return -1;
 char *save=NULL,*token=strtok_r(fields+2," ",&save);
 for(int index=0;token;index++,token=strtok_r(NULL," ",&save)) if(index==19) { *birth=strtoll(token,NULL,10); return 0; }
 return -1;
}
JNIEXPORT jlong JNICALL Java_studio_bleca_binux_NativeProcess_birth(JNIEnv *env,jclass type,jint pid) {
 (void)env; (void)type; long long value=0; if(read_birth(pid,&value)<0)return 0; return value;
}
JNIEXPORT jint JNICALL Java_studio_bleca_binux_NativeProcess_signalGroup(JNIEnv *env, jclass type, jint pid, jint sig) {
 (void)env; (void)type;
 if (pid <= 1 || (sig != SIGTERM && sig != SIGKILL && sig != SIGSTOP && sig != SIGCONT)) return EINVAL;
 return kill(-pid, sig) == 0 ? 0 : errno;
}
JNIEXPORT jint JNICALL Java_studio_bleca_binux_NativeProcess_signalSession(JNIEnv *env, jclass type, jint leader, jlong expected_birth, jint sig) {
 (void)env; (void)type;
 if(leader<=1 || (sig!=SIGTERM && sig!=SIGKILL)) return EINVAL;
 long long current_birth=0;
 if(expected_birth<=0)return EINVAL;
 if(read_birth(leader,&current_birth)==0 && current_birth!=expected_birth)return ESRCH;
 DIR *proc=opendir("/proc");
 if(!proc)return errno;
 struct dirent *entry; int result=0;
 while((entry=readdir(proc))) {
  char *end; long pid=strtol(entry->d_name,&end,10); if(*end || pid<=1 || pid==getpid())continue;
  char path[64],buffer[4096]; snprintf(path,sizeof(path),"/proc/%ld/stat",pid);
  FILE *file=fopen(path,"r"); if(!file)continue;
  if(fgets(buffer,sizeof(buffer),file)) {
   char *fields=strrchr(buffer,')'); char state; long parent,group,session;
   if(fields && sscanf(fields+2,"%c %ld %ld %ld",&state,&parent,&group,&session)==4 && session==leader) {
    if(kill((pid_t)pid,sig)<0 && errno!=ESRCH)result=errno;
   }
  }
  fclose(file);
 }
 closedir(proc); return result;
}
