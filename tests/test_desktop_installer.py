"""Installer contract tests: a missing Android distribution must never report success."""
import os
import subprocess
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'setup-binux-desktop'

class DesktopInstallerTest(unittest.TestCase):
 def run_script(self,*args,**env):
  return subprocess.run(['bash',str(SCRIPT),*args],capture_output=True,text=True,env={**os.environ,**env})
 def test_android_runtime_is_rejected_with_actionable_error(self):
  for language in ('en','ko'):
   result=self.run_script('--yes',BINUX_RUNTIME='native-android',BINUX_LANG=language)
   self.assertEqual(69,result.returncode)
   self.assertIn('Debian/Ubuntu',result.stdout+result.stderr)
   self.assertNotIn('XFCE packages installed',result.stdout)
 def test_unknown_options_do_not_install(self):
  self.assertEqual(2,self.run_script('--unsupported').returncode)
  self.assertEqual(2,self.run_script('--renderer','fake').returncode)
 def test_help_is_available_without_runtime(self):
  result=self.run_script('--help',BINUX_RUNTIME='native-android')
  self.assertEqual(0,result.returncode)
  self.assertIn('--check',result.stdout)
