# base

The base tools a development machine needs, plus a shared tmux config and a
`resume` session picker. Most other packages need it first.

- **Scope:** machine
- **Category:** Foundation
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `timezone` | `""` | The machine's timezone, as tzdata spells it. Empty leaves whatever the machine came with. |
| `hostname` | `""` | The machine's hostname. Empty leaves the one it already has. |
| `upgrade` | `false` | Upgrade every package already installed. Off, because that is the owner's decision, not a side effect of installing base tools. Nothing on macOS. |
| `swap` | `""` | Size of a swapfile at `/swapfile`, such as `8G`. Empty leaves the machine alone. Nothing on macOS, which manages its own swap. |

## Credentials

None.

## Add it

```bash
devmachine packages add base --machine main
devmachine sync
```

`base` is usually pulled in through [`essentials`](../essentials/README.md)
rather than added on its own.

## Notes

- `upgrade` is off by default so a sync never upgrades packages nobody asked
  for.
- `swap` only creates the swapfile when a size is given; it never resizes or
  removes one that already exists. On a btrfs root it is made with
  `btrfs filesystem mkswapfile`, because btrfs refuses to swap on a file
  `fallocate` made.
- On Arch Linux the package lists are refreshed only by `upgrade`, as
  `pacman -Syu`. Refreshing them without upgrading and then installing is a
  partial upgrade, which Arch does not support; with `upgrade` off, packages
  come from the lists the machine already has. If pacman cannot download a
  package (a 404 from the mirror), the lists are older than the mirror: turn
  `upgrade` on for one sync.
- On Arch Linux the system locale is also written to `/etc/environment`, so
  an SSH login has a `LANG` and `mosh` starts.
- On macOS it installs tmux, mosh and ffmpeg from Homebrew or MacPorts;
  curl, git, zsh and the build toolchain come with the Command Line Tools. A
  Mac reached over SSH runs the play as root, so Homebrew installs run as the
  account that owns Homebrew, after a `brew update`. `timezone` goes through `systemsetup`. `swap`
  and `upgrade` do nothing there: macOS manages its own swap, and Software
  Update, Homebrew or MacPorts upgrade what they installed. `base` writes
  `/etc/tmux.conf` and `/usr/local/bin/resume`, so on your own Mac (a self
  machine, which runs without root) it stops before changing anything.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Package reference](https://mydevmachine.sh/reference/package-format/)
