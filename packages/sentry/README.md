# sentry

The Sentry CLI, installed into one account's own `~/.local/bin`. It installs
the tool only: the login opens a browser, so a person does it once in each
workspace — the session is not one this CLI will copy.

- **Scope:** workspace
- **Category:** Developer tools
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `sentry` | manual | workspace | no | `devmachine login sentry --workspace acme` |

`sentry`'s login writes to `~/.config/sentry/cli.db`, a local database rather
than a token file, so it is not shared between workspaces — each one signs in
for itself.

## Add it

```bash
devmachine packages add sentry --workspace acme
devmachine login sentry --workspace acme
devmachine sync
```

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
