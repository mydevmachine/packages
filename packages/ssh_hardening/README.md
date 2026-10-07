# ssh_hardening

Turns off password authentication for good. `devmachine setup` does this once,
at first contact, before Ansible exists; this package keeps it that way on
every `sync`.

- **Scope:** machine
- **Category:** Security
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `service` | `""` | What systemd calls sshd. Empty means the name this distribution family uses — `ssh` on Debian and Ubuntu, `sshd` elsewhere. macOS ignores it. |

## Credentials

None.

## Add it

```bash
devmachine packages add ssh_hardening --machine main
devmachine sync
```

`ssh_hardening` is usually pulled in through
[`essentials`](../essentials/README.md).

## Notes

- Only turns password login off; the key `setup` installed is proven to work
  first, so a `sync` never locks you out of a working key-based login.

## On macOS

- launchd starts a new sshd for every connection, so there is no reload: the
  next login reads the file. It also means a file sshd refuses would lock out
  that next login, so the file is checked with `sshd -t` before it replaces
  the old one, never after.
- macOS turns PAM on, and PAM takes a password through keyboard-interactive
  even with `PasswordAuthentication no`. The file turns
  `KbdInteractiveAuthentication` off as well, and the sync then asks `sshd -T`
  whether both really are off.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`setup`](https://mydevmachine.sh/reference/commands/#setup)
