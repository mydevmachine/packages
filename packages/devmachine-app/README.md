# devmachine-app

What the Devmachine macOS app asks a machine for, reached through
`devmachine run --package devmachine-app`. Not meant to be run by hand.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `github_hosts` | `[]` | GitHub Enterprise hosts the context panel resolves pull requests on, each as `{host, proxy}` with `proxy` optional. `github.com` always works; this adds more. |

The settings land in `/etc/devmachine-app/config.json`, which every workspace
account reads. A Mac reached over SSH keeps them there too. Only your own Mac,
synced without root, keeps them in `~/.config/devmachine-app/config.json`.

## Credentials

None.

## Add it

`devmachine setup` gives a new machine [`essentials`](../essentials/README.md),
which pulls this package in. Add it by hand only to a machine set up without
`essentials`, or before it carried this package:

```bash
devmachine packages add devmachine-app --machine main
devmachine sync
```

## Notes

- Its entrypoint (`bin/devmachine-app`) accepts three commands, called by the
  macOS app itself: `context`, `stats`, and `caddy-logs` — for example
  `devmachine run --package devmachine-app --workspace acme -- context`.
- `stats` and `caddy-logs` run as the machine admin (the package's entrypoint
  is reached that way), so they can read every workspace's processes and
  containers, not only one.

### `stats`

`devmachine run --package devmachine-app -- stats` prints one JSON document
with the machine's health: memory, swap, disk, load, Docker containers, RAM
by user, and listening ports with their owner. It replaces a shell
snippet the app used to send over SSH and parse itself.

On a Mac it prints the same document, read from `sysctl` (load, memory size,
swap), `vm_stat` (memory used, counted as Activity Monitor does), `df` on the
data volume `/System/Volumes/Data`, and `lsof` (listening ports). Homes are
under `/Users/` there, so a container's owner comes from that folder.

A part the machine cannot answer — Docker not installed, nothing listening —
comes back as an empty list rather than a failure. The command only exits
non-zero when it cannot report anything at all. Partial problems are
described in `errors`, a list of short strings.

```json
{
  "collected_at": "2026-09-29T16:23:11+00:00",
  "memory": {"total_bytes": 8589934592, "used_bytes": 4294967296, "available_bytes": 4160749568},
  "swap": {"total_bytes": 2147483648, "used_bytes": 104857600},
  "disk": {"path": "/", "used_bytes": 1073741824, "available_bytes": 8589934592, "used_percent": 11},
  "load": {"load1": 0.52, "load5": 0.58, "load15": 0.59},
  "docker": {
    "available": true,
    "containers": [
      {"name": "web", "mem_used_bytes": 12897075, "mem_limit_bytes": 2086027264, "cpu_percent": 1.5, "owner": "alice"}
    ]
  },
  "users": [
    {"user": "alice", "rss_bytes": 314572800}
  ],
  "ports": [
    {"port": 8810, "owner": "alice"},
    {"port": 22, "owner": "root"}
  ],
  "errors": []
}
```

Field notes:

- Every `*_bytes` field and `rss_bytes` is an integer count of bytes.
  `cpu_percent`, `load1`, `load5`, `load15` are floats.
- `docker.available` is `false` when Docker is not installed or not running;
  `docker.containers` is then `[]`, never missing.
- A container's `owner` is the user its folder belongs to — read from
  the Compose or Supabase CLI working-directory label — or `null` when the
  container carries neither label.
- `users` sums RSS per user across every process, sorted by
  `rss_bytes` descending.
- A port's `owner` is the user of the container publishing it, or otherwise
  the user of the process holding it, or `null` when neither is known.
- `errors` lists a short message per command that failed outright (a
  non-zero exit, a timeout); a tool that is simply not installed is not an
  error.

### `caddy-logs`

`devmachine run --package devmachine-app -- caddy-logs --lines 200` prints
the tail of Caddy's own journal (`journalctl -u caddy -n <lines> --no-pager`)
as plain text on stdout — a log is read, not parsed, so this is not JSON.
`--lines` defaults to 200. On a machine without Caddy, `journalctl` finds no
entries: the output is `-- No entries --` and the exit is zero. A real failure
(`journalctl` missing, a timeout) is reported on stderr with a non-zero exit.
On a Mac, where the `caddy` package does not run, it prints
`-- No entries --` and exits zero without calling anything.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`run`](https://mydevmachine.sh/reference/commands/#run)
