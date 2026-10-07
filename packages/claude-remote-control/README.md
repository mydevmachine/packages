# claude-remote-control

Keeps one account's Claude Code Remote Control session up: a user systemd
unit plus linger on Linux, a launch daemon on macOS, so it survives every
logout. It starts only where that
account has logged in, because there is nothing to connect without a session.

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** `claude-code`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |
| `session_name` | `""` | What this session is called in the phone app. Empty means the workspace's name. |
| `working_directory` | `<home>/dev` | The directory a remote session starts in. |
| `restart_seconds` | `30` | How long to wait before reconnecting. The server gives up on its own after about ten minutes with no network, so the unit restarts for good. |

## Credentials

None of its own; it uses the `claude` login from
[`claude-code`](../claude-code/README.md).

## Add it

```bash
devmachine packages add claude-remote-control --workspace acme
devmachine login claude --workspace acme
devmachine sync
```

## How it stays up on macOS

A workspace account never logs in at the Mac's own screen, and a LaunchAgent
loads only inside a session of its account. So on macOS the session is a
LaunchDaemon, `/Library/LaunchDaemons/devmachine.claude-rc.<user>.plist`, with
`UserName` set to the account: launchd starts it at boot as that account, with
nobody logged in, the way linger does for the systemd unit on Linux. Its output
goes to `~/Library/Logs/claude-rc.log`.

```bash
sudo launchctl print system/devmachine.claude-rc.<user>
```

## Notes

- The unit only starts a session where `claude /login` already ran; add this
  package after logging in, or run `sync` again once you have.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
