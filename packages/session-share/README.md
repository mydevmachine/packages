# session-share

Share one of the account's tmux sessions with someone else for a limited
time, in a browser or over SSH, read only or typing along.

- **Scope:** workspace
- **Category:** Developer tools
- **Needs:** `workspace`

It installs [session-share](https://github.com/mydevmachine/session-share)
into `~/.local/bin`, checked against the release's checksums, gives the
account's share server its own port, and runs `session-share gc` every five
minutes. The tool itself explains what a guest can and cannot do, and why.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `version` | `0.1.0` | The release to install. A sync replaces a binary of another version. |
| `port` | `7690` | The local port of this account's share server. Every workspace on a machine needs its own. |

## Use it

Always name the workspace: the share runs as that account, which owns the
tmux sessions. Without `--workspace` it would run as root.

```bash
devmachine run --package session-share --workspace acme -- start api --mode read --for 1h
devmachine run --package session-share --workspace acme -- list
devmachine run --package session-share --workspace acme -- stop <id>
```

| Command | What it runs |
| --- | --- |
| `start`, `stop`, `extend`, `list`, `logs`, `expose` | The same `session-share` command. |
| `shares` | `session-share list --all --json`: the provider the app reads. |

## Reach it from outside

The share server listens on `127.0.0.1:<port>`. To give it your own domain,
publish that port and record the address:

```bash
devmachine expose add acme 7690 --host share.example.com
devmachine run --package session-share --workspace acme -- expose proxy --url https://share.example.com
```

On a machine with no public address, `expose funnel` publishes it through
Tailscale Funnel at `https://<machine>.ts.net:10000` instead.

## Add it

```bash
devmachine packages add session-share --workspace acme
devmachine sync
```
