"""Own remote process groups; a closed Android client can stop exactly its job."""
import argparse,json,os,pathlib,signal,subprocess,time
from .state import base,write,read
from .daemon import signal_owned_group
def token_path(token):
 import re
 if not re.fullmatch(r'[a-f0-9]{32}',token):raise ValueError('Invalid process token')
 folder=base()/'config/remote';folder.mkdir(mode=0o700,exist_ok=True)
 return folder/(token+'.json')
def birth(pid):
 try:return int(pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(') ',1)[1].split()[19])
 except (FileNotFoundError,ProcessLookupError):return None
def stop(token):
 path=token_path(token)
 # Cancellation can arrive before run records the PID. The tombstone wins the race.
 cancelled=path.with_suffix('.cancelled');cancelled.touch(mode=0o600)
 record=read(path)
 pid=record.get('pid');started=record.get('birth')
 if pid and birth(pid)==started:
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:return
  for _ in range(40):
   if birth(pid)!=started:return
   time.sleep(.05)
  if birth(pid)==started:
   try:os.killpg(pid,signal.SIGKILL)
   except ProcessLookupError:pass
def run(token,command):
 if not command:raise ValueError('Command required')
 path=token_path(token);cancelled=path.with_suffix('.cancelled')
 if cancelled.exists():return 143
 interactive=os.isatty(0)
 signal.signal(signal.SIGTTOU,signal.SIG_IGN)
 process=subprocess.Popen(command,process_group=0) if interactive else subprocess.Popen(command,start_new_session=True)
 process._binux_birth=birth(process.pid)
 if interactive:
  os.tcsetpgrp(0,process.pid)
  # A fast interactive shell can read before the parent hands it the terminal,
  # stopping itself with SIGTTIN. Resume it after foreground ownership is set.
  os.killpg(process.pid,signal.SIGCONT)
 write(path,{'pid':process.pid,'birth':birth(process.pid)})
 try:
  if cancelled.exists():stop(token)
  return process.wait()
 finally:
  signal_owned_group(process,signal.SIGTERM)
  time.sleep(.1)
  signal_owned_group(process,signal.SIGKILL)
  path.unlink(missing_ok=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['run','stop']);p.add_argument('token');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
 return run(a.token,a.command) if a.action=='run' else stop(a.token) or 0
if __name__=='__main__':raise SystemExit(main())
