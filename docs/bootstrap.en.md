# Fresh VPS bootstrap (experimental v0.3)

**Only for a disposable Ubuntu/Debian VPS that has NO 3x-ui and NO Xray.** No production use or routing/failover setup. No automatic certificate issuance. Version 0.3 installs NGINX with distribution defaults, then optionally installs standalone Xray from a checksum-pinned release and a PRIVATE, pre-validated JSON config. It does not generate VLESS/REALITY settings for you.

1. Create a dedicated test VPS and verify its IP and host key out of band.
2. Manually run `sudo touch /etc/vpnctl-allow-bootstrap` on that TEST VPS.
3. Copy `inventory/hosts.yml` to the gitignored `inventory/local.yml` and add a **new test-only host** with `vpnctl_fresh_host: true`. Never set this flag on production hosts.
4. To install only NGINX, leave `vpnctl_install_xray: false` (default).
5. To install standalone Xray, add `vpnctl_install_xray: true`, `xray_release_url` from a verified official release, its verified **64 hex digit** `xray_release_sha256`, and `xray_config_src` pointing to a local, private JSON file. Validate artifact origin and checksum independently. Never publish JSON containing credentials.
6. Run `python3 vpnctl.py --lang en --inventory inventory/local.yml bootstrap --host test_vps --confirm-fresh-vps --apply` and type `APPLY` when prompted.

The tool refuses hosts without the opt-in marker, with existing `x-ui.service` or `xray.service`, or without `vpnctl_fresh_host: true`. It never changes existing 3x-ui-managed Xray configs. The preflight is intentionally conservative and does NOT establish that a VPN works. Xray service runs as root in this experimental release; harden and integration-test before real exposure. Never put private keys or real production inventories in GitHub.

**Important:** no NGINX Stream/REALITY listener, TLS certificate automation, reverse proxy, or failover is configured yet. The test VPS is not ready to replace a production node.
