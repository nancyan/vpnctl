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
    def test_writes_require_apply(self):
        p=self.cmd('clock','--host','fi_in_2')
        self.assertEqual(p.returncode,2)
        self.assertIn('Изменений нет',p.stdout)
if __name__=='__main__':unittest.main()
