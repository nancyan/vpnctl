#!/usr/bin/env python3
"""Offline Xray / NGINX Stream configuration renderer. No SSH and no deployment."""
import argparse
import json
from pathlib import Path
import re
import sys
import uuid

ROLES = {'entry', 'relay', 'exit'}
DOMAIN = re.compile(r'^(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$')

class ConfigurationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ConfigurationError(message)

def get_str(obj, key, label):
    val = obj.get(key)
    require(isinstance(val, str) and bool(val.strip()), f'{label}.{key} must be a non-empty string')
    return val.strip()

def validate(data):
    require(isinstance(data, dict) and isinstance(data.get('nodes'), dict) and bool(data['nodes']), 'nodes must be a non-empty object')
    nodes = data['nodes']
    for name, node in nodes.items():
        require(re.fullmatch(r'[a-z][a-z0-9_-]{1,40}', name) is not None, f'Invalid node name: {name}')
        require(isinstance(node, dict), f'{name} must be an object')
        role = get_str(node, 'role', name)
        require(role in ROLES, f'{name}: role must be entry, relay, or exit')
        domain = get_str(node, 'domain', name).lower()
        require(DOMAIN.fullmatch(domain) is not None, f'{name}: invalid domain')
        try:
            uuid.UUID(get_str(node, 'client_uuid', name))
        except ValueError as exc:
            raise ConfigurationError(f'{name}: invalid client_uuid') from exc
        # These credentials are supplied only in an ignored local file. Never fabricate production keys.
        for key in ('reality_private_key', 'reality_public_key'):
            val = get_str(node, key, name)
            require(re.fullmatch(r'[A-Za-z0-9_-]{43}', val) is not None, f'{name}: invalid {key} format')
        short_id = get_str(node, 'short_id', name)
        require(re.fullmatch(r'(?:[0-9a-fA-F]{2}){1,8}', short_id) is not None, f'{name}: short_id must be 2-16 hex chars in full bytes')
        path = get_str(node, 'path', name)
        require(path.startswith('/') and not any(c in path for c in ('?', '#', ' ')), f'{name}: invalid XHTTP path')
        target = node.get('next_hop')
        require((role == 'exit' and target is None) or (role != 'exit' and isinstance(target, str) and target in nodes and target != name), f'{name}: invalid next_hop for role {role}')
    for name in nodes:
        seen = set()
        at = name
        while at is not None:
            require(at not in seen, f'Routing cycle involving {at}')
            seen.add(at)
            at = nodes[at].get('next_hop')
        at = name
        while nodes[at].get('next_hop'):
            at = nodes[at]['next_hop']
        require(nodes[at]['role'] == 'exit', f'{name}: route does not reach exit')
    return nodes

def xray_config(name, node, nodes):
    sni = node['domain'].lower()
    local_port = node.get('local_xray_port', 3030)
    require(type(local_port) is int and 1024 <= local_port <= 65535, f'{name}: invalid local_xray_port')
    inbound = {
        'tag': 'vpnctl-in', 'listen': '127.0.0.1', 'port': local_port,
        'protocol': 'vless', 'settings': {
            'clients': [{'id': node['client_uuid'], 'email': f'{name}-upstream'}],
            'decryption': 'none'},
        'streamSettings': {
            'network': 'xhttp', 'security': 'reality',
            'realitySettings': {
                'show': False, 'dest': '127.0.0.1:9443', 'xver': 0,
                'serverNames': [sni], 'privateKey': node['reality_private_key'],
                'shortIds': [node['short_id']]},
            'xhttpSettings': {'path': node['path'], 'mode': 'auto'}}}
    outbounds = []
    if node['role'] == 'exit':
        outbounds.append({'tag': 'vpnctl-next', 'protocol': 'freedom', 'settings': {}})
    else:
        peer = nodes[node['next_hop']]
        outbounds.append({
            'tag': 'vpnctl-next', 'protocol': 'vless',
            'settings': {'vnext': [{'address': peer['domain'], 'port': 443,
                                    'users': [{'id': peer['client_uuid'], 'encryption': 'none'}]}]},
            'streamSettings': {
                'network': 'xhttp', 'security': 'reality',
                'realitySettings': {'serverName': peer['domain'],
                                    'publicKey': peer['reality_public_key'],
                                    'shortId': peer['short_id'],
                                    'fingerprint': 'chrome'},
                'xhttpSettings': {'path': peer['path'], 'mode': 'auto'}}})
    outbounds.append({'tag': 'vpnctl-block', 'protocol': 'blackhole'})
    return {'log': {'loglevel': 'warning'}, 'inbounds': [inbound], 'outbounds': outbounds,
            'routing': {'domainStrategy': 'AsIs', 'rules': [
                {'type': 'field', 'inboundTag': ['vpnctl-in'], 'outboundTag': 'vpnctl-next'}]}}

def stream_config(name, node):
    # This is a snippet *inside* an existing nginx stream{} context, not a complete nginx.conf.
    domain = node['domain'].lower()
    return f'''# vpnctl generated fragment for {name}; requires ngx_stream_ssl_preread_module.
# Place inside the existing stream {{}} context. Do not create duplicate 443 listeners.
map $ssl_preread_server_name $vpnctl_{name.replace('-', '_')}_backend {{
    {domain} 127.0.0.1:{node.get('local_xray_port', 3030)};
    default 127.0.0.1:9443;
}}
server {{
    listen 443 reuseport;
    proxy_pass $vpnctl_{name.replace('-', '_')}_backend;
    ssl_preread on;
}}
'''

def render(input_path, output_dir):
    nodes = validate(json.loads(Path(input_path).read_text(encoding='utf-8')))
    require(not output_dir.exists() or not any(output_dir.iterdir()), 'Output directory must be absent or empty (avoid overwriting private configurations)')
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_dir.chmod(0o700)
    for name, node in nodes.items():
        target = output_dir / name
        target.mkdir(mode=0o700)
        cfg = target / 'xray.json'
        cfg.write_text(json.dumps(xray_config(name, node, nodes), indent=2) + '\n', encoding='utf-8')
        cfg.chmod(0o600)
        fragment = target / 'nginx-stream.conf.example'
        fragment.write_text(stream_config(name, node), encoding='utf-8')
        fragment.chmod(0o600)
    return len(nodes)

def main(argv=None):
    p = argparse.ArgumentParser(description='Offline topology renderer / Генератор конфигураций без подключения к VPS')
    p.add_argument('--topology', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args(argv)
    try:
        count = render(args.topology, args.output)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    print(f'Rendered {count} node(s) into {args.output}; no servers were contacted.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
