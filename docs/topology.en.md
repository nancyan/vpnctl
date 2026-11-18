# vpnctl v0.4: offline topology renderer (EN)

`render` generates per-node Xray JSON and an NGINX Stream snippet **offline**. It never contacts or changes a server.

1. Copy `examples/topology.example.json` to ignored `topology.local.json`.
2. Set your domains, UUIDs, real X25519 Reality key pairs, short IDs and `next_hop` links. Obtain keys using your installed Xray (`xray x25519`). The supplied sample intentionally uses **nonfunctional** key placeholders.
3. Run `python3 vpnctl.py --lang en render --topology topology.local.json --output rendered`.
4. Review `rendered/<node>/xray.json` and `nginx-stream.conf.example`. Generated files include secrets and are Git-ignored.

Roles are `entry`, `relay` and `exit`, with acyclic sequential forwarding. Exit uses `freedom`. The design assumes a separately configured **valid TLS HTTPS site** on `127.0.0.1:9443` for each node domain; REALITY uses that as its destination for unmatched connections. Xray listens only on `127.0.0.1:3030`.

**Limitations:** The Stream snippet belongs inside the existing `stream {}` block for a *fresh test VPS*; do not create a second `443` listener or insert it under `http {}`. This tool does **not** install software, obtain certificates, manage 3x-ui, deploy to servers or implement failover/Observatory. Validate on disposable machines first using `xray run -test -config ...` and `nginx -t`, followed by end-to-end network tests.

**Secrets:** never commit `topology.local.json`, `rendered/`, UUIDs or private Reality keys. Use a vault or secret manager. The generator does not cryptographically verify that a supplied Reality key pair matches.
