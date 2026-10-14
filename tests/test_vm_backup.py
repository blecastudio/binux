import json,os,pathlib,subprocess,tarfile,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class VmBackupTest(unittest.TestCase):
 def test_actual_shared_home_snapshot_and_restore_do_not_recurse_or_overwrite(self):
  with tempfile.TemporaryDirectory() as folder:
   root=pathlib.Path(folder);home=root/'shared-home';home.mkdir(mode=0o700);state=root/'private-state';state.mkdir(mode=0o700)
   project=home/'project';project.mkdir();(project/'hello.py').write_text('print("비눅스")\n')
   env={**os.environ,'HOME':str(home),'BINUX_HOME':str(state),'BINUX_RUNTIME':'linux-vm','PYTHONPATH':str(ROOT/'core')}
   archive=home/'backup.tar.gz'
   subprocess.run(['python3','-m','binux.cli','storage','backup',str(archive)],env=env,check=True,capture_output=True)
   with tarfile.open(archive) as tar:
    self.assertIn('home/project/hello.py',tar.getnames());self.assertNotIn('home/backup.tar.gz',tar.getnames())
   result=subprocess.run(['python3','-m','binux.cli','storage','restore',str(archive)],env=env,check=True,capture_output=True,text=True)
   restored=pathlib.Path(result.stdout.strip());self.assertTrue(restored.is_relative_to(home))
   self.assertEqual((restored/'home/project/hello.py').read_text(),(project/'hello.py').read_text())
   self.assertNotEqual(subprocess.run(['python3','-m','binux.cli','storage','backup',str(archive)],env=env,capture_output=True).returncode,0)
