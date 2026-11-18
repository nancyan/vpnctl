import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
KEY = 'A' * 43

def node(role, index, next_hop=None):
    result = dict(role=role, domain=f'node{index}.example.com',
                  client_uuid=f'00000000-0000-4000-8000-{index:012d}',
                  reality_private_key=KEY, reality_public_key=KEY,
                  short_id='a1b2', path='/connect-v1')
    if next_hop:
        result['next_hop'] = next_hop
    return result

class RenderTests(unittest.TestCase):
    def test_three_node_chain(self):
        topology = {'nodes': {'entry': node('entry', 1, 'relay'),
                              'relay': node('relay', 2, 'exit'),
                              'exit': node('exit', 3)}}
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / 'topology.local.json'
            out = Path(d) / 'rendered'
            inp.write_text(json.dumps(topology))
            p = subprocess.run([sys.executable, str(ROOT/'vpnctl.py'), 'render',
                                '--topology', str(inp), '--output', str(out)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            config = json.loads((out/'entry'/'xray.json').read_text())
            self.assertEqual(config['outbounds'][0]['settings']['vnext'][0]['address'], 'node2.example.com')
            self.assertEqual(config['inbounds'][0]['streamSettings']['realitySettings']['dest'], '127.0.0.1:9443')
            self.assertEqual(json.loads((out/'exit'/'xray.json').read_text())['outbounds'][0]['protocol'], 'freedom')
            self.assertIn('ssl_preread on;', (out/'entry'/'nginx-stream.conf.example').read_text())
            self.assertEqual(oct((out/'entry'/'xray.json').stat().st_mode & 0o777), '0o600')

    def test_reject_cycle_without_files(self):
        topology = {'nodes': {'entry': node('entry', 1, 'relay'),
                              'relay': node('relay', 2, 'entry')}}
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / 'topology.local.json'
            out = Path(d) / 'rendered'
            inp.write_text(json.dumps(topology))
            p = subprocess.run([sys.executable, str(ROOT/'vpnctl.py'), 'render',
                                '--topology', str(inp), '--output', str(out)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertFalse(out.exists())

    def test_reject_existing_nonempty_output(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / 'topology.local.json'
            out = Path(d) / 'rendered'
            inp.write_text(json.dumps({'nodes': {'exit': node('exit', 3)}}))
            out.mkdir()
            (out/'keep.txt').write_text('important')
            p = subprocess.run([sys.executable, str(ROOT/'vpnctl.py'), 'render',
                                '--topology', str(inp), '--output', str(out)],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertEqual((out/'keep.txt').read_text(), 'important')

if __name__ == '__main__':
    unittest.main()
