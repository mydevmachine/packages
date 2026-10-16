# scheduled

Runs the workspace's scheduled tasks — a shell command, or a prompt for
Claude or Codex — on a schedule, with nobody logged in and your computer off.

- **Scope:** workspace
- **Platforms:** Linux, macOS
- **Category:** Developer tools
- **Needs:** `workspace`

It installs the devmachine release of the CLI that syncs at
`~/.devmachine/scheduled/devmachine`, checked against the release's checksums,
and one timer that runs `devmachine scheduled local tick` at the start of
every minute: a user systemd timer with linger on Linux, a launch daemon that
runs as the account on macOS. The binary stays off the account's PATH, so the
devmachine you run by hand there is whatever you installed.

Tasks are files under `~/.devmachine/scheduled/`. A sync never touches them.

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `version` | empty | The devmachine release to install. Empty means the release of the CLI that syncs; a CLI built from source falls back to `0.14.0`. |

## Use it

You do not need to add it yourself: the first `devmachine scheduled add` in a
workspace, or the first task created in the app, offers to add it and sync.

```bash
devmachine scheduled add --workspace acme --name "Daily briefing" --folder ~/dev/app \
  --harness claude --prompt "Summarize yesterday's commits" --every weekdays --at 09:00
devmachine scheduled list
devmachine scheduled run <id> --workspace acme
```

A prompt runs as the workspace's account, with its own Claude or Codex login,
so add `claude-code` or `codex` to the workspace and log in once.

See [scheduled tasks](https://mydevmachine.sh/how-it-works/scheduled-tasks/)
for how it works.
