# caddy

A reverse proxy that gets its own certificates, and a one-page site that
answers 200 to prove the machine is reachable. Every other site is a file
another package drops into `/etc/caddy/sites.d` — `caddy` serves nothing else
by itself.

- **Scope:** machine
- **Category:** Web
- **Needs:** `firewall`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `email` | `""` | The address the certificate authority writes to about an expiring certificate. Empty means an anonymous account. |
| `local_certs` | `false` | Sign certificates locally instead of asking Let's Encrypt. For a machine no name resolves to — a test VM, a private network — where the ACME challenge can never succeed. |
| `site` | `true` | Serve a one-page site straight from Caddy, no container behind it. It answers 200, proving the name, the certificate and the proxy in one request. |
| `site_domain` | `""` | The name the one-page site answers to, with its own certificate. Empty serves it on port 80 at the machine's address, over plain HTTP. It creates no DNS record — pointing the name is `devmachine dns add`. |
| `source` | `auto` | Where Caddy is installed from. `auto` uses Caddy's apt repository, and installs the pinned GitHub release instead when apt cannot check that repository's signature. `apt` uses only the repository and fails when it cannot be checked. `github` always installs the pinned GitHub release and removes the repository. Debian and Ubuntu only: elsewhere Caddy comes from the system's own repository. |
| `version` | `"2.11.4"` | The Caddy release installed from GitHub, by `source: github` or by the `auto` fallback. The apt repository, and every system other than Debian and Ubuntu, ignores it. |

## Credentials

None.

## Add it

```bash
devmachine packages add caddy --machine main
devmachine sync
```

`caddy` is usually pulled in through [`essentials`](../essentials/README.md).

## Extension point

`caddy` declares `sites.d: /etc/caddy/sites.d`. Another package contributes a
site by extending it:

```yaml
extends:
  caddy.sites.d: files/my-site.caddy
```

`devmachine expose add` writes one of these files for a workspace's port; see
`devmachine expose list` to check what is live.

## Where Caddy comes from

On Arch Linux, Caddy comes from the system's own repository, and the rest
of this section does not apply.

On Debian and Ubuntu, by default, Caddy comes from Caddy's own apt
repository, on `dl.cloudsmith.io`. Every sync downloads the repository's
signing key again, so a key Caddy fixes upstream reaches the machine on the
next sync.

That repository can be signed with a key its own published key file lists as
expired: apt then says `EXPKEYSIG 531A6B20FA058A70 Caddy Web Server` and `The
repository ... is not signed`, and refuses it
([caddyserver/dist#130](https://github.com/caddyserver/dist/issues/130)). apt
is right to refuse it, so nothing here turns signature checking off or marks
the repository trusted. What changes is only that the sync goes on:

- Every package's cache refresh (`base`, `docker`, `tailscale`, `workspace`)
  lets through an error about Caddy's repository, and only that one, and
  prints a warning. Every other repository is still refreshed; any other
  error still fails the sync.
- If Caddy is already installed, it stays as it is. It is not upgraded that
  run, and the warning says so.
- If Caddy is not installed, `caddy` downloads the `.deb` for the machine's
  architecture from the GitHub release named by `version`, checks it against
  that release's `caddy_<version>_checksums.txt` (sha512), and installs it.
  A missing line or a mismatch fails the sync; nothing unchecked is installed.

Once Caddy fixes its key, `auto` uses the repository again with no change on
your side. To choose for yourself, set `caddy.source` under the machine's
`settings:` and sync:

```yaml
machines:
  - name: main
    packages: [caddy]
    settings:
      caddy.source: github   # always the pinned release; the repository is removed
      # caddy.source: apt    # only the repository; fail when apt cannot check it
```

With `github`, changing `version` installs that release on the next sync.

## Notes

- `site_domain` never creates a DNS record by itself; point the name at the
  machine with `devmachine dns add` (or `devmachine expose add`, which does
  both).

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Publishing a site](https://mydevmachine.sh/concepts/publishing/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
