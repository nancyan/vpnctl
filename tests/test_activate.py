"""Offline, non-network safety tests for opt-in activation."""
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class ActivationTests(unittest.TestCase):
    def cmd(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'vpnctl.py'), *args], text=True, capture_output=True)

    def test_activation_requires_explicit_apply(self):
        result = self.cmd('activate', '--host', 'eu_entry')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Изменений нет', result.stdout)

    def test_activation_refuses_non_fresh(self):
        result = self.cmd('activate', '--host', 'eu_entry', '--apply')
        self.assertEqual(result.returncode, 2)
        self.assertIn('--confirm-fresh-vps', result.stderr)

    def test_activation_refuses_all(self):
        result = self.cmd('activate', '--all', '--apply', '--confirm-fresh-vps')
        self.assertEqual(result.returncode, 2)

    def test_activation_refuses_noninteractive_yes(self):
        result = self.cmd('activate', '--host', 'eu_entry', '--apply', '--confirm-fresh-vps', '--yes')
        self.assertEqual(result.returncode, 2)

    def test_activation_refuses_check_mode(self):
        result = self.cmd('activate', '--host', 'eu_entry', '--check', '--confirm-fresh-vps')
        self.assertEqual(result.returncode, 2)

if __name__ == '__main__':
    unittest.main()
