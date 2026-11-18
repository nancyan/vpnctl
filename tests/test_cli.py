import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CliTests(unittest.TestCase):
    def cmd(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'vpnctl.py'),*args],text=True,capture_output=True)
    def test_hosts(self):
        p=self.cmd('--lang','ru','hosts')
        self.assertEqual(p.returncode,0)
        self.assertIn('ru_in',p.stdout)
    def test_requires_host(self):
        p=self.cmd('status')
        self.assertEqual(p.returncode,2)
    def test_discover_requires_host(self):
        p=self.cmd('discover')
        self.assertEqual(p.returncode,2)
    def test_discover_rejects_apply(self):
        p=self.cmd('discover','--host','fi_in_2','--apply')
        self.assertEqual(p.returncode,2)
    def test_writes_require_apply(self):
        p=self.cmd('clock','--host','fi_in_2')
        self.assertEqual(p.returncode,2)
        self.assertIn('Изменений нет',p.stdout)
    def test_bootstrap_requires_fresh_host_confirmation(self):
        p=self.cmd('bootstrap','--host','test_vps','--apply')
        self.assertEqual(p.returncode,2)
        self.assertIn('confirm-fresh-vps',p.stderr)
    def test_bootstrap_disallows_all(self):
        p=self.cmd('bootstrap','--all','--apply','--confirm-fresh-vps')
        self.assertEqual(p.returncode,2)
if __name__=='__main__':unittest.main()
