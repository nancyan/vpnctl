"""Build a human-reviewable offline plan from a topology; no network actions."""
import argparse
import json
from pathlib import Path
import sys
from tools.render_topology import validate

def plan(topology):
    nodes=validate(json.loads(Path(topology).read_text(encoding='utf-8')))
    actions=[]
    for name, node in nodes.items():
        actions.append({'node':name,'role':node['role'],
                        'needs':['DNS A/AAAA validation','TLS certificate for HTTPS decoy',
                                 'NGINX Stream enabled','Xray config compatibility test',
                                 'firewall / SSH access review','end-to-end VPN connectivity test'],
                        'next_hop':node.get('next_hop'),'domain':node['domain']})
    return {'mode':'offline_only','automatic_deployment':False,'actions':actions}

def main(argv=None):
    p=argparse.ArgumentParser(description='Offline deployment plan / План без применения')
    p.add_argument('--topology',required=True)
    p.add_argument('--json',action='store_true')
    a=p.parse_args(argv)
    try: result=plan(a.topology)
    except (OSError,ValueError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2
    if a.json: print(json.dumps(result,indent=2,ensure_ascii=False))
    else:
        print('DRY PLAN / ПЛАН БЕЗ ПРИМЕНЕНИЯ')
        for item in result['actions']:
            print(f"\n{item['node']} ({item['role']}) -> {item['next_hop'] or 'internet'}")
            for task in item['needs']:print('  - '+task)
    return 0
if __name__=='__main__': sys.exit(main())
