# dev

The four tools a workspace is expected to have: the GitHub CLI, bun, the Node
LTS through mise, and unzip. It installs `gh` and declares the login `gh`
needs; one GitHub account normally serves every workspace on a machine.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** `workspace`, `mise`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `gh_version` | `"2.63.2"` | Which GitHub CLI release to install. It is a release asset rather than a distribution package because most distributions do not carry `gh` at all. |
| `node_version` | `"lts"` | Which Node mise installs globally. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `gh` | manual | machine | yes | `devmachine login gh` |

`gh`'s login writes `~/.config/gh/hosts.yml`. Because it is a machine
credential (the ordinary case — one GitHub account for every workspace), a
following `devmachine sync` copies it to every workspace that installs `dev`.
A workspace that needs its own account overrides this in its own
configuration.

## Add it

```bash
devmachine packages add dev --workspace acme
devmachine login gh
devmachine sync
```

## Notes

- `gh` is shared by default; give one workspace its own login with
  `--share gh=own` in `devmachine workspaces edit`.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Sharing a login](https://mydevmachine.sh/concepts/credentials/)
