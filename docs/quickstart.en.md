# vpnctl: English quick start

## What it does

`vpnctl` manages an Ansible inventory and offers an intentionally separated workflow:

1. Inspect your local workstation (`doctor`), no network.
2. Generate UUID/short ID (`keys`), and X25519 keys only via a locally installed compatible Xray binary (`keys --xray-binary xray`).
3. Define node-to-node routing using `topology.local.json` (not committed).
4. `validate` the graph, optionally validate every generated Xray JSON with `--xray-binary xray`.
5. Generate node-specific private files (`render`).
6. Inspect the intended prerequisites (`plan`).
7. Provision **a disposable, clean VPS only**, with mandatory marker and interactive confirmation (`bootstrap`).
8. Stage rendered Xray JSON on that **test VPS only** (`stage`). This does *not* activate a VPN tunnel or reload services.

## Install the controller

Linux/macOS or Windows WSL, Python 3.10+, SSH, Ansible, rsync:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
python3 vpnctl.py doctor
```

## Local-only usage

```bash
python3 vpnctl.py --lang en keys
python3 vpnctl.py --lang en keys --xray-binary xray
cp examples/topology.example.json topology.local.json
# Replace EVERY placeholder with your own fresh keys; sample is intentionally NOT runnable.
python3 vpnctl.py --lang en validate --topology topology.local.json
python3 vpnctl.py --lang en plan --topology topology.local.json
python3 vpnctl.py --lang en render --topology topology.local.json --output rendered
```

Local rendered configurations include secrets (`xray.json`). Never copy them into Git, paste them into issue reports or share them in public CI. The Stream snippet is **not** a ready nginx.conf; manual integration must account for the existing global `stream {}` section, port 443 conflicts, a valid TLS endpoint and SNI behavior. A config parser check is not a network connectivity test.

## Test VPS staging

Edit a **private** `inventory/local.yml` with a disposable host alias matching the output node folder, host keys verified, and `vpnctl_fresh_host: true`. On the disposable VPS only, create `/etc/vpnctl-allow-bootstrap` manually. Never set this marker on production. Example:

```bash
python3 vpnctl.py --inventory inventory/local.yml bootstrap --host eu_exit --confirm-fresh-vps --apply
python3 vpnctl.py --inventory inventory/local.yml stage --host eu_exit --confirm-fresh-vps --bundle rendered --apply
```

Both actions require interactive `APPLY`. Bootstrap rejects hosts where x-ui or Xray systemd unit already exists. Staging explicitly rejects 3x-ui, writes to `/etc/vpnctl/staged/xray.json`, and tests JSON against the standalone Xray binary if available. No automatic activation. These are **experimental** Ansible playbooks, not production-proven, and all commands require a pre-reviewed test VPS.

### Not yet provided

Automatic DNS/certificate issuance, installed 3x-ui configuration management, actual 443 Stream activation, Xray service activation for staged topology, complete client profile onboarding, failover and end-to-end integration tests. Do not interpret `stage` success as a functioning VPN.

## Experimental activation (disposable test VPS only)

After `bootstrap` and `stage`, the staged Xray config can be activated **separately**. First provision and verify DNS, HTTPS certificates, an HTTPS website on `127.0.0.1:9443`, NGINX Stream on `443`, firewall rules and external dependencies **manually**. The generated `nginx-stream.conf.example` is not automatically installed.

```bash
python3 vpnctl.py --lang en --inventory inventory/local.yml activate --host eu_exit --confirm-fresh-vps --apply
```

An interactive `APPLY` is mandatory. The playbook requires `/etc/vpnctl-allow-bootstrap`, rejects 3x-ui, requires a standalone `/etc/systemd/system/xray.service`, backs up the live JSON, checks the candidate via `xray run -test`, restarts **only Xray**, and checks a loopback listener (default port 3030). On detected failure it attempts to restore the previous JSON and restart Xray. **Rollback is best-effort, not atomic, and not guaranteed.** This does not test external VPN connectivity, TLS/SNI, certificate validity or firewall safety. Never run it on production hosts.
