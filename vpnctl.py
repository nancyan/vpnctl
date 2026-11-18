#!/usr/bin/env python3
"""Bilingual command-line interface for opt-in Ansible VPN infrastructure operations."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
MESSAGES = {
 'en': {
  'description':'Safely manage SSH-accessible servers with Ansible',
  'list':'Configured hosts (example inventory unless edited):',
  'missing':'Ansible not found. Install: python3 -m pip install -r requirements.txt',
  'ask': 'Type APPLY to run a modifying playbook: ',
  'cancel':'Cancelled; no changes made.',
  'dry':'Check mode selected. No intended changes will be applied.',
  'notice':'Review inventory and secrets before contacting hosts.',
  'host':'Use --host to select one server; --all requires explicit confirmation.',
  'noop':'Missing --apply for this modifying action. No changes made.',
 },
 'ru': {
  'description':'Безопасное управление серверами по SSH через Ansible',
  'list':'Настроенные узлы (пример, пока не заполнен inventory):',
  'missing':'Ansible не найден. Установка: python3 -m pip install -r requirements.txt',
  'ask': 'Введите APPLY для запуска изменяющего сценария: ',
  'cancel':'Отменено, изменений нет.',
  'dry':'Режим проверки. Изменения не должны применяться.',
  'notice':'Проверьте inventory и секреты перед подключением к серверам.',
  'host':'Укажите один сервер через --host; для всех нужен --all.',
  'noop':'Для изменения требуется --apply. Изменений нет.',
 }
}
PLAYBOOKS = {'ping':'ping.yml', 'status':'status.yml', 'backup':'backup.yml', 'clock':'clock.yml', 'discover':'discover.yml', 'bootstrap':'bootstrap.yml', 'stage':'stage.yml', 'activate':'activate.yml'}

def parse():
 p=argparse.ArgumentParser(description='vpnctl / Console for Ansible infrastructure')
 p.add_argument('--lang', choices=['ru','en'], default=os.environ.get('VPNCTL_LANG','ru'))
 p.add_argument('--inventory', default='inventory/hosts.yml')
 sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('hosts',help='Show inventory file (no connections)')
 for command, helptext in [('doctor','Inspect this computer (offline)'), ('keys','Create local UUID/short ID and optional Reality keys'), ('validate','Validate topology offline'), ('plan','Print offline deployment plan')]:
  sub.add_parser(command, help=helptext)
 renderer=sub.add_parser('render',help='Generate Xray/NGINX configs OFFLINE from private topology')
 renderer.add_argument('--topology',required=True)
 renderer.add_argument('--output',required=True)
 for cmd in PLAYBOOKS:
  s=sub.add_parser(cmd)
  s.add_argument('--host',help='Limit to one inventory hostname')
  s.add_argument('--all',action='store_true',help='Target all configured hosts')
  s.add_argument('--apply',action='store_true',help='Perform write operations (backup, clock)')
  s.add_argument('--check',action='store_true',help='Ansible check mode')
  s.add_argument('--yes',action='store_true',help='Skip interactive confirmation for apply')
  s.add_argument('--confirm-fresh-vps',action='store_true',help='Explicit confirmation for fresh VPS bootstrap/stage')
  s.add_argument('--bundle',help='Local rendered bundle path (stage only)')
 return p.parse_args()

def main():
 # Dispatch offline commands before requiring an inventory.
 if len(sys.argv) > 1:
  args=sys.argv[1:]
  lang='ru'
  for idx, arg in enumerate(args):
   if arg=='--lang' and idx+1<len(args): lang=args[idx+1]
  commands={'doctor': ('tools.doctor','main'), 'keys':('tools.keygen','main'),
            'validate':('tools.verify','main'), 'plan':('tools.plan','main')}
  for index, arg in enumerate(args):
   if arg in commands:
    from importlib import import_module
    module, func=commands[arg]
    params=args[index+1:]
    if arg=='doctor' and '--lang' not in params: params+=['--lang',lang]
    return getattr(import_module(module),func)(params)
 a=parse(); t=MESSAGES[a.lang]
 if a.command=='render':
  from tools.render_topology import main as render_main
  return render_main(['--topology',a.topology,'--output',a.output])
 inventory=(BASE/a.inventory).resolve()
 if not inventory.is_file():
  print(f'Inventory not found: {inventory}',file=sys.stderr);return 2
 if a.command=='hosts':
  print(t['list']); print(inventory.read_text());return 0
 if not a.host and not a.all:
  print(t['host'],file=sys.stderr);return 2
 if a.host and a.all:
  print('--host and --all are mutually exclusive',file=sys.stderr);return 2
 modifying = a.command in ('backup','clock','bootstrap','stage','activate')
 if modifying and not a.apply and not a.check:
  print(t['noop']);return 2
 if a.command in ('bootstrap','stage','activate'):
  if a.all or not a.host or not a.confirm_fresh_vps or a.check or not a.apply or a.yes:
   print('Bootstrap/stage/activate requires one --host, --confirm-fresh-vps and --apply, with interactive confirmation; no --all, --check or --yes.',file=sys.stderr)
   return 2
 if a.command == 'stage' and (not a.bundle or not (Path(a.bundle).resolve() / a.host / 'xray.json').is_file()):
  print('Stage requires --bundle with xray.json matching --host',file=sys.stderr);return 2
 if a.command != 'stage' and a.bundle:
  print('--bundle is only valid for stage',file=sys.stderr);return 2
 if a.command == 'backup' and a.check:
  print('Backup is not meaningful in --check mode / Резервная копия не создаётся в --check',file=sys.stderr);return 2
 if a.command in ('ping','status','discover') and a.apply:
  print('--apply not used for read-only operations',file=sys.stderr);return 2
 if not shutil.which('ansible-playbook'):
  print(t['missing'],file=sys.stderr);return 2
 print(t['notice'])
 if a.check: print(t['dry'])
 if modifying and not a.check and not a.yes:
  if input(t['ask']).strip()!='APPLY':
   print(t['cancel']);return 1
 cmd=['ansible-playbook','-i',str(inventory),str(BASE/'playbooks'/PLAYBOOKS[a.command])]
 if a.host:cmd+=['--limit',a.host]
 if a.command=='stage':
  import json
  cmd+=['--extra-vars',json.dumps({'vpnctl_bundle':str(Path(a.bundle).resolve())})]
 if a.check:cmd+=['--check','--diff']
 print('Executing:', ' '.join(cmd),flush=True)
 return subprocess.run(cmd,cwd=BASE,check=False).returncode

if __name__=='__main__':sys.exit(main())
