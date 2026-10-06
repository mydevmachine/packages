# essentials

What almost every machine wants, in one package: base tools, git, a firewall,
SSH with passwords kept off, Caddy to publish sites with HTTPS, and what the
Devmachine macOS app reads from a machine. Docker is not included — add it with [`docker`](../docker/README.md) when you want it.
It installs nothing itself; it only pulls in the packages it needs.

- **Scope:** machine
- **Category:** Foundation
- **Needs:** `base`, `git`, `firewall`, `ssh_hardening`, `caddy`, `devmachine-app`

## Settings

None of its own; each package it needs keeps its own settings (see their
READMEs).

## Credentials

None of its own.

## Add it

`devmachine setup` adds `essentials` to a new machine automatically, so the
first `sync` installs it. Pass `--no-essentials` to start a machine with no
packages instead.

`essentials` runs only on Linux, because `firewall`, `ssh_hardening` and
`caddy` do. On a Mac, `setup` and `machines add` start the machine with
`base` and `devmachine-app` instead, and say so.

To add it to a machine that does not have it yet:

```bash
devmachine packages add essentials --machine main
devmachine sync
```

## Notes

- Pulls in [`firewall`](../firewall/README.md), whose mosh UDP range stays
  closed until `firewall.mosh_interface` is set.
- Pulls in [`ssh_hardening`](../ssh_hardening/README.md), which turns off
  password login on every sync, same as `devmachine setup` did once at first
  contact.
- Pulls in [`devmachine-app`](../devmachine-app/README.md), three small
  read-only scripts the macOS app calls for sessions, health and Caddy's log.
  It is here because the app may be installed long after the machine was set
  up, and nobody would know to add it then. It needs CLI 0.7.1 or newer, so
  `essentials` does too.
- Only a pinned package release that has `essentials` gets it through
  `setup`; an older pinned release starts the machine empty and says so.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`setup`](https://mydevmachine.sh/reference/commands/#setup)
