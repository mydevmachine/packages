# pi

The Pi coding agent for one account, from its standalone release, so it
needs no Node. Logging in is a person's job, once, in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

It unpacks the latest release for the machine's architecture into
`~/.local/share/pi` and links `~/.local/bin/pi` to it. The release is one
native program, so the process is called `pi` rather than `node`, which is
how the Devmachine app recognises a Pi session. A later sync leaves an
installed Pi alone; `pi update self` updates it.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `pi` | manual | workspace | yes | `devmachine login pi --workspace acme` |

Pi has no login command of its own: `pi`'s login starts Pi, and `/login`
inside it signs in to a provider. Keys are kept at `~/.pi/agent/auth.json`.

## Skills

Pi reads `~/.agents/skills`, where every package's skills already land, so
it needs no link.

## Add it

```bash
devmachine packages add pi --workspace acme
devmachine sync
devmachine login pi --workspace acme
```

## Learn more

- [Pi as your coding agent](https://mydevmachine.sh/guides/pi-coding-agent/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
