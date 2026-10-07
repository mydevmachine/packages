# tailscale

Joins the machine to a tailnet, so it is reachable without a public address.

- **Scope:** machine
- **Category:** Network
- **Needs:** `base`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `exit_node` | `false` | Advertise this machine as an exit node. Off unless asked for. |
| `login_server` | *(empty)* | The control server `devmachine login tailscale` joins. Empty means Tailscale's own; a URL means your own, such as Headscale. |

## Where Tailscale comes from

On Debian and Ubuntu from Tailscale's own apt repository, and on Arch Linux
from the system's own. A system built on Debian or Ubuntu, such as Linux
Mint or Pop!_OS, uses the repository of the release it is built on, which
`/etc/os-release` names in `UBUNTU_CODENAME` or `DEBIAN_CODENAME`. A system
that names neither stops the sync with a message saying so, before anything
is installed.

On macOS from Homebrew, as the account that owns it, because Homebrew refuses
root. tailscaled then runs as a launch daemon this package writes,
`/Library/LaunchDaemons/devmachine.tailscaled.plist`, rather than through
`tailscaled install-system-daemon`. That keeps the state at
`/var/lib/tailscale/tailscaled.state`, the path `stored_at` names on Linux too,
and runs the binary Homebrew upgrades instead of a copy of it.

A Mac that already runs Tailscale, through the Tailscale app, `sudo brew services
start tailscale` or a tailscaled installed by hand, is left as it is: a second tailscaled beside it fights it for
the tunnel, which is often the one the Mac is reached through. Log in through
what is already there. `exit_node` turns on IP forwarding only on Linux.

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `tailscale` | manual | machine | no | `devmachine login tailscale` |

`devmachine login tailscale` runs this package's `bin/join` on the machine,
as the admin account, in a real terminal. It calls `tailscale up`, with
`--login-server` when `login_server` is set and `--advertise-exit-node` when
`exit_node` is on. With a login server it first asks for a pre-auth key:
paste one, and it reaches `tailscale up` through a file only its owner can read,
never a command line; leave it empty to sign in through a URL. The login is
not shareable — each machine joins the tailnet for itself — and its state
lives at `/var/lib/tailscale/tailscaled.state`.

A CLI from before network packages ignores `bin/join` and runs the declared
`tailscale up` instead, without the settings.

## The network it answers for

The `network:` block makes this package the answer for `tailscale:<name>`
entries in a machine's `hosts`. The CLI knows nothing about Tailscale itself:

| Script | Runs on | What it does |
| --- | --- | --- |
| `bin/resolve` | your computer | Reads `tailscale status --json` and prints the addresses of the machine whose `HostName` (or MagicDNS name) is `<name>`. Exits 3 — skip this entry — when Tailscale is not installed, not running, or does not know the name. |
| `bin/join` | the machine | Runs `tailscale up` as described above. |
| `bin/self-name` | the machine | Prints the machine's own `HostName` from `tailscale status --json`, which the CLI adds to `hosts` as `tailscale:<name>`. |

The scripts use the Python standard library only, and run on Python 3.9 —
what macOS ships. Their tests are in `test/`:

```bash
python3 -m unittest discover -s packages/tailscale -p 'test_*.py'
```

The tests put a fake `tailscale` first on `PATH`, so they never run the real
one.

## Add it

```bash
devmachine packages add tailscale --machine main
devmachine sync
devmachine login tailscale
```

For your own control server, set it before the login:

```yaml
machines:
  - name: main
    settings:
      tailscale.login_server: https://net.example.com
```

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Reaching your server](https://mydevmachine.sh/concepts/reaching-your-server/)
- [The network package contract](https://mydevmachine.sh/reference/network-package-contract/)
