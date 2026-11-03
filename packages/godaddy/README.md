# godaddy

DNS zones on GoDaddy. A DNS provider package — it does not run at `sync`
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
| `godaddy` | secret | machine | `devmachine secrets set godaddy` then `devmachine credentials push` |

The value is delivered to the machine as the `GODADDY_API_TOKEN`
environment variable.

## Add it

```bash
devmachine packages add godaddy --machine main
devmachine secrets set godaddy
devmachine sync
devmachine credentials push
```

## Notes

- Record types: A, AAAA, CNAME, TXT, MX, SRV, NS and CAA. A value is written
  the way a zone file writes it: `10 mail.example.com` for MX,
  `10 5 5060 sip.example.com` for SRV, `0 issue "ca.example.net"` for CAA.
  `devmachine dns add --append` adds a value next to the ones a name holds;
  without it the name ends up holding only the new value.
- GoDaddy keeps an SRV's service, protocol, priority, weight and port in
  fields of their own. The provider joins them: `_sip._tcp.voice` with
  `10 5 5060 sip.example.com`. A `PUT` replaces every SRV at the same host, so
  the provider writes the other services back untouched.
- A Personal Access Token from developer.godaddy.com with the DNS scopes. The
  classic key and secret pair is not supported.
- Once installed, use `devmachine dns list`, `devmachine dns add`, and
  `devmachine dns status` — not this package directly. `devmachine dns
  providers` shows which zones the token can see.
- On macOS it uses the `python3` of the Command Line Tools and installs
  nothing.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
- [DNS providers](https://mydevmachine.sh/how-it-works/dns-providers/)
