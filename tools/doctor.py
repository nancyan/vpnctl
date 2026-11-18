"""Read-only local environment diagnostics; never contacts a VPS."""
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

BINARIES = ('python3', 'ssh', 'ansible-playbook', 'ansible-galaxy', 'rsync', 'xray', 'nginx')

def inspect():
    result = {'platform': platform.system(), 'python': platform.python_version(),
              'tools': {name: shutil.which(name) is not None for name in BINARIES}}
    result['ready_for_ansible'] = bool(result['tools']['ansible-playbook'] and result['tools']['ssh'])
    return result

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Check local prerequisites / Проверка локальной среды')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--lang', choices=('ru','en'), default='ru')
    opts = parser.parse_args(argv)
    report = inspect()
    if opts.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print('Проверка локальной среды / Local environment' if opts.lang == 'ru' else 'Local environment / Проверка локальной среды')
        print(f"OS: {report['platform']}; Python: {report['python']}")
        for tool, available in report['tools'].items():
            print(f"  {tool:<20} {'OK' if available else 'missing'}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
