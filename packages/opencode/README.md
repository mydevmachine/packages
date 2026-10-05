# opencode

The opencode CLI for one account. It runs without a login on opencode's own
free models; logging in to another provider is a person's job, once, in
each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

It runs opencode's own installer, which puts `opencode` in
`~/.opencode/bin`, and adds that folder to the PATH in `~/.zshenv`.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `opencode` | manual | workspace | yes | `devmachine login opencode --workspace acme` |

`opencode`'s login runs `opencode auth login`: pick a provider, then paste
a key or follow its sign-in. Keys are kept at
`~/.local/share/opencode/auth.json`.

## Skills

opencode reads `~/.agents/skills`, where every package's skills already
land, so it needs no link.

## Add it

```bash
devmachine packages add opencode --workspace acme
devmachine sync
devmachine login opencode --workspace acme
```

## Learn more

- [opencode as your coding agent](https://mydevmachine.sh/guides/opencode/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
