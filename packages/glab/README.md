# glab

The GitLab CLI, installed into one account's own `~/.local/bin`. It installs
the tool only: the login opens a browser, so a person does it once.

- **Scope:** workspace
- **Category:** Developer tools
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `version` | `"1.111.0"` | Which GitLab CLI release to install. It is a release asset rather than a distribution package because no distribution carries `glab`. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `glab` | manual | workspace | yes | `devmachine login glab --workspace acme` |

`glab`'s login writes `~/.config/glab-cli/config.yml`. It is a workspace
credential because the GitLab instance and the account differ between
workspaces.

## Add it

```bash
devmachine packages add glab --workspace acme
devmachine login glab --workspace acme
devmachine sync
```

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
