"""Offline topology checks and optional Xray configuration parser validation."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tools.render_topology import validate, xray_config, ConfigurationError

def check(topology_path, *, xray_binary=None):
    data = json.loads(Path(topology_path).read_text(encoding='utf-8'))
    nodes = validate(data)
    warnings = []
    if not xray_binary:
        warnings.append('Xray binary not provided: protocol/runtime compatibility NOT verified')
    else:
        executable = shutil.which(xray_binary)
        if not executable:
            raise ConfigurationError(f'Xray executable not found: {xray_binary}')
        import tempfile
        for name, node in nodes.items():
            with tempfile.TemporaryDirectory() as td:
                cfg = Path(td) / 'config.json'
                cfg.write_text(json.dumps(xray_config(name,node,nodes)), encoding='utf-8')
                cfg.chmod(0o600)
                result = subprocess.run([executable, 'run', '-test', '-config', str(cfg)],
                                        capture_output=True, text=True, timeout=30)
                if result.returncode:
                    raise ConfigurationError(f'Xray rejected node {name}: {result.stderr.strip()[:500]}')
    return {'valid_structure': True, 'node_count': len(nodes), 'nodes': {name: obj['role'] for name,obj in nodes.items()}, 'warnings': warnings}

def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate topology offline / Локальная проверка топологии')
    parser.add_argument('--topology', type=Path, required=True)
    parser.add_argument('--xray-binary', help='Optional installed local Xray binary')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = check(args.topology,xray_binary=args.xray_binary)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2
    if args.json:
        print(json.dumps(result, indent=2,ensure_ascii=False))
    else:
        print(f"Topology OK / Топология корректна: {result['node_count']} nodes")
        for name, role in result['nodes'].items(): print(f'  {name}: {role}')
        for warning in result['warnings']: print('WARNING:', warning)
    return 0
if __name__ == '__main__':
    sys.exit(main())
