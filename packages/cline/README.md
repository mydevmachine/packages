# cline

The Cline CLI for one account, installed with the account's own Node.
Logging in is a person's job, once, in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`, `dev`

Cline ships only through npm, so it needs the Node the `dev` package
installs. It is installed with `--prefix ~/.local`, not into that Node's
own global directory, so upgrading Node does not take it away.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `cline` | manual | workspace | yes | `devmachine login cline --workspace acme` |

`cline`'s login runs `cline auth`: your Cline account, a ChatGPT
subscription, or your own provider's API key. Keys are kept at
`~/.cline/data/settings/providers.json`. Cline writes that file the first
time it runs, before anybody signs in, so `credentials list` showing it
present means Cline has run, not that a provider is connected.

## Skills

Cline reads skills from `~/.cline/skills`, not from `~/.agents/skills`. A
workspace with this package gets a link there for every skill a package
contributes.

## Add it

```bash
devmachine packages add cline --workspace acme
devmachine sync
devmachine login cline --workspace acme
```

## Learn more

- [Cline as your coding agent](https://mydevmachine.sh/guides/cline/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
