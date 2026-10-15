import os,pathlib,subprocess,tempfile,time,unittest,uuid,json,signal
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RemoteProcessTest(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.base=pathlib.Path(self.folder.name)
  self.env={**os.environ,'BINUX_HOME':str(self.base),'PYTHONPATH':str(ROOT/'core')}
 def tearDown(self):self.folder.cleanup()
 def test_signal_exit_status_matches_shell_convention(self):
  result=subprocess.run(['python3','-m','binux.remote','run',uuid.uuid4().hex,'/bin/sh','-c','kill -TERM $$'],env=self.env)
  self.assertEqual(result.returncode,143)
 def test_cancel_before_launch_never_executes_command(self):
  token=uuid.uuid4().hex
  subprocess.run(['python3','-m','binux.remote','stop',token],env=self.env,check=True)
  marker=self.base/'should-not-exist'
  result=subprocess.run(['python3','-m','binux.remote','run',token,'touch',str(marker)],env=self.env)
  self.assertEqual(result.returncode,143);self.assertFalse(marker.exists())
 def test_cancel_stops_real_background_process_group(self):
  token=uuid.uuid4().hex
  process=subprocess.Popen(['python3','-m','binux.remote','run',token,'sleep','120'],env=self.env)
  try:
   path=self.base/'config/remote'/f'{token}.json'
   deadline=time.monotonic()+5
   while not path.exists() and time.monotonic()<deadline:time.sleep(.05)
   record=json.loads(path.read_text());self.assertTrue(pathlib.Path(f'/proc/{record["pid"]}').exists())
   subprocess.run(['python3','-m','binux.remote','stop',token],env=self.env,check=True,timeout=5)
   self.assertNotEqual(process.wait(timeout=5),0)
   self.assertFalse(pathlib.Path(f'/proc/{record["pid"]}').exists())
  finally:
   if process.poll() is None:process.kill();process.wait()
 def test_interactive_bash_has_real_controlling_pty(self):
  import pty,select
  token=uuid.uuid4().hex;pid,fd=pty.fork()
  if pid==0:
   # Force the real fast-shell race: Bash reads while it is still a background
   # process group, before remote.run can transfer foreground terminal ownership.
   script='''import pathlib,subprocess,sys,time
from binux import remote
original=subprocess.Popen
def stopped(*args,**kwargs):
 process=original(*args,**kwargs)
 end=time.monotonic()+3
 while time.monotonic()<end:
  if pathlib.Path(f'/proc/{process.pid}/stat').read_text().rsplit(') ',1)[1].startswith('T '):
   print('BEFORE_HANDOFF_STOPPED',flush=True)
   return process
  time.sleep(.01)
 raise RuntimeError('Expected Bash to stop with SIGTTIN before terminal handoff')
remote.subprocess.Popen=stopped
raise SystemExit(remote.run(sys.argv[1],['bash','--noprofile','--norc','-i']))
'''
   os.execvpe('python3',['python3','-c',script,token],self.env)
  try:
   os.write(fd,b"test -t 0 && printf 'GUEST_PTY_OK\\n'; jobs; exit 19\n")
   output=b'';deadline=time.monotonic()+5
   while time.monotonic()<deadline:
    if select.select([fd],[],[],.1)[0]:
     try:chunk=os.read(fd,8192)
     except OSError:break
     if not chunk:break
     output+=chunk
   end=time.monotonic()+2
   while True:
    child,status=os.waitpid(pid,os.WNOHANG)
    if child or time.monotonic()>=end:break
    time.sleep(.01)
   if child==0:
    subprocess.run(['python3','-m','binux.remote','stop',token],env=self.env,timeout=5,check=True)
    os.kill(pid,signal.SIGKILL)
    os.waitpid(pid,0)
    self.fail('Interactive Bash did not exit within the PTY deadline')
   self.assertEqual(os.waitstatus_to_exitcode(status),19)
   self.assertIn(b'GUEST_PTY_OK\r\n',output)
   self.assertIn(b'BEFORE_HANDOFF_STOPPED\r\n',output)
   self.assertNotIn(b'no job control',output)
  finally:os.close(fd)
