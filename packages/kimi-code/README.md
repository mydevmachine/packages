# kimi-code

Moonshot AI's Kimi Code CLI (`kimi`) for one account. Logging in is a
person's job, once, in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

It runs Kimi's own installer, which puts `kimi` in `~/.kimi-code/bin`, and
adds that folder to the PATH in `~/.zshenv`.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `kimi` | manual | workspace | no | `devmachine login kimi --workspace acme` |

`kimi`'s login runs `kimi login`, a device-code sign-in: it prints a link
and a code, and waits until you approve it on any device. An account on
kimi.ai rather than kimi.com signs in with `kimi login --region global`.
The tokens are kept in `~/.kimi-code/credentials`, a directory, which is
why the login cannot be shared between workspaces.

## Skills

Kimi Code reads `~/.agents/skills`, where every package's skills already
land, so it needs no link.

## Add it

```bash
devmachine packages add kimi-code --workspace acme
devmachine sync
devmachine login kimi --workspace acme
```

## Learn more

- [Kimi Code as your coding agent](https://mydevmachine.sh/guides/kimi-code/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
