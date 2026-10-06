# claude-plugins

Installs and updates Claude Code plugins in one account. It knows how, never
which: the marketplace and the plugin list are the operator's, and with no
marketplace configured it does nothing.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `claude-code`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `claude` | `<home>/.local/bin/claude` | Where the Claude Code CLI is. It is installed into the account's own `~/.local/bin`, so only a workspace that put it somewhere else says so. |
| `marketplace` | `""` | Where the plugins come from: a GitHub repository written `owner/name`, a git URL, or a path on the machine. Empty installs nothing. |
| `plugins` | `[]` | Which plugins to install, each written `<plugin>@<marketplace>`. The marketplace half is the name the marketplace gives itself. |
| `update` | `false` | Re-fetch the marketplace and update every plugin on each run. Off by default, since it cannot tell whether anything moved, so a run with it on always reports a change. |

## Credentials

None of its own; it uses the `claude` login from
[`claude-code`](../claude-code/README.md).

## Add it

```bash
devmachine packages add claude-plugins --workspace acme
devmachine workspaces edit acme \
  --set claude-plugins.marketplace=owner/repo \
  --set claude-plugins.plugins='["my-plugin@my-marketplace"]'
devmachine sync
```

## Notes

- With `marketplace` empty, this package does nothing — it never guesses a
  source.
- `update: true` always reports a change on `sync --check`; leave it off
  unless you want that on every run.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
