# cloudflare

DNS zones on Cloudflare. A DNS provider package — it does not run at `sync`
time; `devmachine dns` calls its entrypoint directly.

- **Scope:** machine
- **Category:** DNS
- **Kind:** `dns`
- **Needs:** none

## Settings

None.

## Credentials

| Name | Kind | Scope | How to provide it |
| --- | --- | --- | --- |
| `cloudflare` | secret | machine | `devmachine secrets set cloudflare` then `devmachine credentials push` |

The value is delivered to the machine as the `CLOUDFLARE_API_TOKEN`
environment variable.

## Add it

```bash
devmachine packages add cloudflare --machine main
devmachine secrets set cloudflare
devmachine sync
devmachine credentials push
```

## Notes

- Once installed, use `devmachine dns list`, `devmachine dns add`, and
  `devmachine dns status` — not this package directly. `devmachine dns
  providers` shows which zones the token can see.
- On macOS it uses the `python3` of the Command Line Tools and installs
  nothing.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
- [DNS providers](https://mydevmachine.sh/how-it-works/dns-providers/)
