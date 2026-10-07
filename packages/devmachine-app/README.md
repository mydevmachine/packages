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

## Widgets

The macOS app draws its Home, its sidebar, the Context tab of a session
and its menu bar item from these. Most read only what the app already
knows, so they work without adding or syncing this package.

Home:

| Widget | Default size | What it shows |
| --- | --- | --- |
| `devmachine-app/clock` | medium | The time, the date and the computer the app runs on. |
| `devmachine-app/summary` | wide | How many sessions, coding-harness sessions and workspaces are open. |
| `devmachine-app/machines` | large | Each machine, online or not, with its CPU, memory, disk and readiness. |
| `devmachine-app/usage` | medium | One coding harness's usage windows, how much of each is used and when it resets. |

`machines` and `usage` let you choose what they show: in the app, ⋯ →
**Choose machines…** picks some machines (none picked shows them all),
and ⋯ → **Choose harness…** picks the harness. From the terminal:
`devmachine widgets set machines --board home --set machines=main,backup`.
The app puts one `usage` card on Home for each harness you use.

On a machine (needs this package added to that machine and synced):

| Widget | Default size | What it shows |
| --- | --- | --- |
| `devmachine-app/machine-stats` | small | How full one machine's disk is, read on the machine every minute. |

Add it with `devmachine widgets add devmachine-app/machine-stats --set
machine=<name>`. The app never places it on its own, because it needs the
`machine` input. It reads the `stats` command, which this package declares
as a provider: `devmachine-app/stats` answers one JSON document with the
machine's memory, swap, disk, load, containers, users and ports, at most
every 10 seconds. A widget written in a board can read it too.

Sidebar (one per board):

| Widget | What it shows |
| --- | --- |
| `devmachine-app/workspaces` | Your machines and workspaces with their sessions, in the order you drag them. |

Context sidebar, in the order the app puts them there (each reads the
selected session):

| Widget | What it shows |
| --- | --- |
| `devmachine-app/shortcuts` | Skill buttons for the machine or workspace of the selected session. |
| `devmachine-app/publish-port` | A button that publishes a port of the selected workspace on a subdomain, when a machine runs Caddy. |
| `devmachine-app/monitors` | The monitors running in the selected session. |
| `devmachine-app/shells` | The background shells of the selected session. |
| `devmachine-app/sub-agents` | The sub-agents the selected session started, and whether each still runs. |
| `devmachine-app/todo` | The plan of the selected session and its to-do list. |
| `devmachine-app/pull-requests` | The pull requests of the selected session, with their checks and review state. |
| `devmachine-app/links` | The links the selected session mentioned. |

Menu bar title, left to right (at most three widgets, each one line):

| Widget | What it shows |
| --- | --- |
| `devmachine-app/brand` | The Devmachine mark, the first thing in the menu bar. |
| `devmachine-app/open-pull-requests` | How many of your pull requests are open, hidden when there are none. |

Menu bar popover, one tab each:

| Widget | What it shows |
| --- | --- |
| `devmachine-app/pull-requests-panel` | Your open pull requests by owner, with their checks and review state. It fits Home and the sidebars too (`large` or `tall`). |
| `devmachine-app/usage-panel` | Every coding harness's usage windows side by side, how much is used and when each resets. |

The sidebar widgets grow with their content (`size: auto`). Remove one in
the app or with `devmachine widgets remove <id> --board context-sidebar`,
and bring it back from the gallery or with `devmachine widgets add
devmachine-app/<name> --board context-sidebar`. `devmachine widgets list
--board sidebar` shows what fits each area.

The menu bar works the same way with `--board menubar` and `--board
menubar-panel`, for example `devmachine widgets move usage-panel
--before pull-requests-panel --board menubar-panel` to open the popover
on Usage.

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
Each workspace account there runs its own colima VM, so `stats` asks every
`/Users/*/.colima/default/docker.sock` it finds and merges the containers. A
container with no folder label belongs to the account whose VM runs it. A
stopped VM is simply not running, not an error.

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
  container carries neither label. On a Mac with colima, the account whose
  VM runs it fills in when no label names one.
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
A Mac has no journal. There it prints the last lines of the log the `caddy`
package writes, `/var/log/devmachine-caddy.log` (JSON, one entry per line).
It prints Caddy's startup output, `/var/log/devmachine-caddy.launchd.log`,
instead only when that log does not exist yet, or when the startup output is
newer and ends in the `Error:` line Caddy exits with. A start that fails never
reaches the older log. With neither file, Caddy is not there: `-- No entries --`,
exit zero.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`run`](https://mydevmachine.sh/reference/commands/#run)
