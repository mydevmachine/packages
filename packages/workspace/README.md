# workspace

The account a person works in: a home nobody else can read, a git identity
and `~/dev`. Almost every other workspace-scoped package needs this one first.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. It is read from the account; a new account gets `/home/<the account>` unless this says otherwise. On macOS a new account always gets `/Users/<the account>`. |
| `admin_home` | `/root` | The home of the account the CLI provisions with. Whatever reaches that account over SSH is what reaches this workspace. On macOS it is the admin login's own home, read from the system. |
| `groups` | `[]` | Extra Linux groups the account joins. The `docker` group is one of them, and it is effectively root, so nobody joins it by accident. |
| `shell` | `""` | The login shell. Empty means whatever `useradd` would pick; the package that installs a shell (such as `zsh`) is the one that sets it. |
| `git_name` | `""` | The name on this workspace's commits. |
| `git_email` | `""` | The address on this workspace's commits. |
| `sign_commits` | `true` | Sign every commit and rebase, once a package such as `git-key` sets up a key. |
| `known_hosts` | `["github.com"]` | The hosts whose SSH host key is trusted in advance, so the first clone does not stop to ask a question nobody is there to answer. |

## Credentials

None.

## Add it

```bash
devmachine workspaces new acme
devmachine sync
```

`workspaces new` adds `workspace` (and the rest of
`defaults.workspace`) automatically; there is usually no need to
`packages add` it by hand.

## Notes

- **The `docker` group is effectively root.** Add it to `groups` only for a
  workspace that genuinely needs it.
- `sign_commits` only takes effect once a key exists — pair it with
  [`git-key`](../git-key/README.md) or a key set up by hand.
- **On macOS** the account is created hidden: it is not on the login window
  or in System Settings. Its primary group is `staff`, and nothing is
  installed for it, because git, `ssh-keygen` and `ssh-keyscan` come with the
  Command Line Tools.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Machines and workspaces](https://mydevmachine.sh/concepts/machines-and-workspaces/)
