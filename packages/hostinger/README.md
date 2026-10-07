# hostinger

DNS zones on Hostinger. A DNS provider package — it does not run at `sync`
time; `devmachine dns` calls its entrypoint directly.

- **Scope:** machine
- **Category:** DNS
- **Kind:** `dns`
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `zones` | `[]` | DNS zones this provider may manage. Set this when the token has DNS permission without Domains portfolio permission; an empty list asks the account portfolio instead. |

## Credentials

| Name | Kind | Scope | How to provide it |
| --- | --- | --- | --- |
| `hostinger` | secret | machine | `devmachine secrets set hostinger` then `devmachine credentials push` |

The value is delivered to the machine as the `HOSTINGER_API_TOKEN`
environment variable.

## Add it

```bash
devmachine packages add hostinger --machine main
devmachine secrets set hostinger
devmachine sync
devmachine credentials push
```

## Notes

- Once installed, use `devmachine dns list`, `devmachine dns add`, and
  `devmachine dns status` — not this package directly. `devmachine dns
  providers` shows which zones the token can see.
- If the token has DNS permission but not Domains portfolio permission, set
  `zones` explicitly or `dns list`/`add` cannot find them.
- TTL: a new record with no TTL given gets 3600 seconds. Hostinger, unlike
  Cloudflare, has no "automatic" TTL, so a record cannot be created without a
  number. A record that already exists keeps its own TTL when none is given.
  An explicit TTL below Hostinger's minimum of 60 seconds is rejected with an
  `invalid_record` error, rather than silently raised — the value you asked
  for is not the value you would get.
- On macOS it uses the `python3` of the Command Line Tools and installs
  nothing. The provider runs on that Python's 3.9.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
- [DNS providers](https://mydevmachine.sh/how-it-works/dns-providers/)
