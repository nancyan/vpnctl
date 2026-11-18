import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class StageTests(unittest.TestCase):
    def run_cmd(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'vpnctl.py'),*args],capture_output=True,text=True)
    def test_missing_bundle_denied(self):
        p=self.run_cmd('stage','--host','fi_in_1','--confirm-fresh-vps','--apply')
        self.assertEqual(p.returncode,2)
        self.assertIn('bundle',p.stderr.lower())
    def test_no_all_staging(self):
        p=self.run_cmd('stage','--all','--confirm-fresh-vps','--apply')
        self.assertEqual(p.returncode,2)
    def test_no_silent_yes(self):
        p=self.run_cmd('stage','--host','fi_in_1','--confirm-fresh-vps','--apply','--yes')
        self.assertEqual(p.returncode,2)
if __name__=='__main__':unittest.main()
