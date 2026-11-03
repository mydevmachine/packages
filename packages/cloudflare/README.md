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

- Record types: A, AAAA, CNAME, TXT, MX, SRV, NS and CAA. A value is written
  the way a zone file writes it: `10 mail.example.com` for MX,
  `10 5 5060 sip.example.com` for SRV, `0 issue "ca.example.net"` for CAA.
  `devmachine dns add --append` adds a value next to the ones a name holds;
  without it the name ends up holding only the new value.
- Cloudflare keeps an MX priority in a field of its own and an SRV's or CAA's
  parts in a `data` object. The provider joins them into the value `dns list`
  shows and splits the value `dns add` gives it.
- Once installed, use `devmachine dns list`, `devmachine dns add`, and
  `devmachine dns status` — not this package directly. `devmachine dns
  providers` shows which zones the token can see.
- On macOS it uses the `python3` of the Command Line Tools and installs
  nothing.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
- [DNS providers](https://mydevmachine.sh/how-it-works/dns-providers/)
