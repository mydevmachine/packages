# claude-code

The Claude Code CLI for one account, its `~/.claude` directory and the
`settings.json` the account starts with. Logging in is a person's job, once,
in each account.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `status_line` | `""` | The command Claude Code runs to draw its status line. Empty leaves the status line alone. It runs outside a login shell, so give it an absolute path. |
| `remote_control_at_startup` | `false` | Connect every session to Remote Control as it opens, instead of waiting for somebody to type `/rc`. |
| `session_name_prefix` | `""` | What each Remote Control session is called in the phone app. Empty means the workspace's name. |
| `env` | `{}` | Environment variables every Claude Code session runs with, as a map. It is how a model-specific or terminal-specific workaround is turned on without this package having an opinion about it. |
| `diff_sidebar` | `null` | Open the `/diff` panel. Unset leaves whatever Claude Code has; amended only where Claude Code's own state file and that preference already exist. |
| `expanded_todos` | `null` | Show the task list under the footer. Unset leaves whatever Claude Code has, same condition as `diff_sidebar`. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `claude` | manual | workspace | yes | `devmachine login claude --workspace acme` |

`claude`'s login runs `claude /login` and stores the session at
`~/.claude/.credentials.json`. Scope is workspace because accounts usually
differ between workspaces — one person's own, one client's — but it can be
shared across workspaces if you work under a single account and say so in
your own configuration.

## Add it

```bash
devmachine packages add claude-code --workspace acme
devmachine login claude --workspace acme
devmachine sync
```

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
