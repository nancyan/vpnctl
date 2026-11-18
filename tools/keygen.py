"""Generate UUID and optionally invoke an installed Xray binary for X25519 keypair."""
import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
import uuid

def key_material(xray_binary=None):
    result={'client_uuid': str(uuid.uuid4()), 'short_id': secrets.token_hex(4)}
    if xray_binary:
        exe=shutil.which(xray_binary)
        if not exe: raise ValueError('Xray binary not found')
        proc=subprocess.run([exe,'x25519'],capture_output=True,text=True,timeout=30)
        if proc.returncode: raise ValueError('Xray x25519 failed')
        values={}
        for line in proc.stdout.splitlines():
            if ':' not in line: continue
            key,val=line.split(':',1)
            if key.strip().lower() in ('private key','public key','password'):
                values['private' if key.strip().lower() in ('private key','password') else 'public']=val.strip()
        if 'private' not in values or 'public' not in values:
            raise ValueError('Could not parse Xray x25519 output; version unsupported')
        for value in values.values():
            if not re.fullmatch(r'[A-Za-z0-9_-]{43}',value):
                raise ValueError('Unexpected X25519 key encoding')
        result['reality_private_key']=values['private']
        result['reality_public_key']=values['public']
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate local credentials; NEVER commit output')
    p.add_argument('--xray-binary',help='Call xray x25519 to create a Reality keypair')
    opts=p.parse_args(argv)
    try: result=key_material(opts.xray_binary)
    except (ValueError,subprocess.TimeoutExpired) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2
    print(json.dumps(result,indent=2))
    print('PRIVATE OUTPUT / СЕКРЕТНЫЕ ДАННЫЕ: do not post or commit',file=sys.stderr)
    return 0
if __name__=='__main__': sys.exit(main())
