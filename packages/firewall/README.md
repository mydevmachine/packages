# firewall

ufw, with SSH open and HTTP optional. It needs the `community.general`
Ansible collection on the machine. On macOS it is the Application Firewall
instead; see [On macOS](#on-macos).

- **Scope:** machine
- **Category:** Security
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `http` | `true` | Open 80 and 443. A machine that hosts nothing can turn this off. |
| `mosh_interface` | `""` | The one interface mosh's UDP range is opened on. Empty means it is not opened at all, which keeps the range off a public edge. |
| `mosh_ports` | `"60000:61000"` | The UDP range mosh is given on that interface. |

## Credentials

None.

## Add it

```bash
devmachine packages add firewall --machine main
devmachine sync
```

`firewall` is usually pulled in through [`essentials`](../essentials/README.md).

## Notes

- **mosh is closed by default.** Set `firewall.mosh_interface` (for example
  `eth0`, or a tailnet interface such as `tailscale0`) to open the range; with
  no interface set, `devmachine mosh` cannot reach the machine at all.
- Requires the `community.general` collection on the machine
  (`ansible-galaxy collection install community.general`); `sync` fails with a
  clear message if it is missing.

## On macOS

macOS has no ufw. Its Application Firewall decides per program, not per port,
and only for incoming connections. So on a Mac:

- **SSH stays open, in this order.** Block-all is turned off (it shuts out
  Remote Login), built-in signed software is allowed, and sshd's program
  (`/usr/libexec/sshd-keygen-wrapper`) is permitted. Only then is the firewall
  turned on. A Mac where it is already on keeps it on.
- **`http` permits or blocks Caddy's program.** Caddy usually comes after this
  package, so it permits itself on its first sync; from then on `http: false`
  blocks it.
- **`mosh_interface` cannot be kept to one interface.** Any value permits
  `mosh-server` on every interface, and `mosh_ports` is ignored. The sync says
  so in a warning. Leave it empty on a Mac that faces the internet directly.
- Nothing here needs `community.general`.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Reaching your server](https://mydevmachine.sh/concepts/reaching-your-server/)
