# zsh

zsh as the account's login shell, Oh My Zsh, a tmux config, and a shell that
attaches to a tmux session when the connection is over SSH. A tmux server
already running keeps its old configuration until it is told to reload.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `tmux_auto_attach` | `true` | Open a tmux session on every SSH login, so a dropped connection loses nothing. A second connection while the first is live gets a session of its own instead of a second view of the same one. |
| `tmux_config` | `true` | Write the account's `~/.tmux.conf`. Turn it off to keep a config of your own. |

## Credentials

None.

## Add it

```bash
devmachine packages add zsh --workspace acme
devmachine sync
```

## Notes

- Sets `shell` for the account, so `workspace.shell` is normally left empty
  when `zsh` is installed.
- `tmux_config: false` keeps your own `~/.tmux.conf` intact across syncs.
- A copy in tmux (a mouse drag, or `y` in copy mode) reaches the clipboard of
  the computer you connect from through OSC 52, over SSH and over mosh, and
  leaves copy mode. A tmux server that was already running picks this up
  after `tmux source-file ~/.tmux.conf`.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)

## Workspace secrets

Every shell in the workspace loads `~/.devmachine/env`, the file
`devmachine secrets set NAME --workspace <ws>` fills. It is sourced from
`~/.zshenv`, so a command run over `ssh` sees the values too, not only an
interactive shell. See https://mydevmachine.sh/concepts/credentials/.
