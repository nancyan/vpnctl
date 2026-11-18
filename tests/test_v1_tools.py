import json
from pathlib import Path
import tempfile
import unittest
from tools.doctor import inspect
from tools.keygen import key_material
from tools.verify import check
from tools.plan import plan
from tools.render_topology import ConfigurationError

KEY = 'A'*43

def make_topology():
    return {'nodes': {'exit': {'role':'exit','domain':'exit.example.com',
        'client_uuid':'00000000-0000-4000-8000-000000000001',
        'reality_private_key':KEY,'reality_public_key':KEY,
        'short_id':'a1b2','path':'/connect-v1'}}}

class ToolsTests(unittest.TestCase):
    def test_doctor(self):
        self.assertIn('python3',inspect()['tools'])
    def test_uuid_and_short_id(self):
        x=key_material(); y=key_material()
        self.assertNotEqual(x['client_uuid'],y['client_uuid'])
        self.assertEqual(len(x['short_id']),8)
        self.assertNotIn('reality_private_key',x)
    def test_verification_offline_warns(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'topology.local.json';f.write_text(json.dumps(make_topology()))
            result=check(f)
            self.assertEqual(result['node_count'],1)
            self.assertTrue(result['warnings'])
    def test_plan_no_deploy(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'topology.local.json';f.write_text(json.dumps(make_topology()))
            result=plan(f)
            self.assertFalse(result['automatic_deployment'])
            self.assertEqual(result['actions'][0]['role'],'exit')
    def test_invalid_topology(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'topology.local.json';f.write_text('{}')
            with self.assertRaises(ConfigurationError):check(f)

if __name__=='__main__': unittest.main()
