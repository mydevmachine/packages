# workspace

The account a person works in: a home nobody else can read, a git identity,
`~/dev`, and one environment every shell of the account reads. Almost every
other workspace-scoped package needs this one first.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. It is read from the account; a new account gets `/home/<the account>` unless this says otherwise. On macOS a new account always gets `/Users/<the account>`. |
| `admin_home` | `/root` | The home of the account the CLI provisions with. Whatever reaches that account over SSH is what reaches this workspace. On macOS it is the admin login's own home, read from the system. |
| `groups` | `[]` | Extra groups the account joins. The `docker` group is one of them, and it is effectively root, so nobody joins it by accident. On macOS a group the Mac does not have, such as `docker`, is left out with a note instead of failing. |
| `shell` | `""` | The login shell. Empty means the system's default for a new account (`useradd`'s on Linux, `/bin/bash` on macOS); the package that installs a shell (such as `zsh`) is the one that sets it. |
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
- **On macOS with Remote Login set to "Only these users"**, sshd lets in only
  members of the `com.apple.access_ssh` group, so the account joins it;
  otherwise SSH refuses it with `failed service ACL check`. With "All users"
  that group does not exist and nothing changes. `workspaces destroy` takes
  the account out of it again.

## Every shell gets the same environment

What every shell of the account needs, interactive or not, lives in one file:
`~/.devmachine/shellenv`. It is plain POSIX `sh`, and each package that adds
something writes a block of its own there: this one the workspace's secrets
and, on a Mac, the package manager's `PATH`; `mise` its activation; a tool
such as `claude-code` the folder it installs into.

This package makes every shell read it, whichever login shell the account
has:

| Shell | Reads it from |
| --- | --- |
| zsh, any | `~/.zshenv` |
| bash, not a login, or a command over `ssh` | `~/.bashrc`, at the top, before Debian's and Arch's early `return` |
| bash, a login | `~/.bash_profile` when it exists (Arch), else `~/.profile` (Debian, Ubuntu, a new Mac account) |
| sh, a login | `~/.profile` |

A Mac's bash 3.2 reads no startup file at all in a login shell that is not
interactive and was not given `-l`, such as `su - bob -c cmd` or a script
piped into `ssh -T`. `ssh host cmd`, an interactive login and `bash -lc` all
load shellenv there. Debian's and Ubuntu's bash load it in those two cases
too.

A login bash reads two of those files, and shellenv is loaded once. A shell
started from another one loads it again, because functions and hooks such as
mise's are not inherited. `~/.bash_profile` is never created: a new one would
hide the `~/.profile` a login bash otherwise reads.

An older release wrote all this to `~/.zshenv`, so only zsh got it. A sync
moves it: each package takes its old lines out of `~/.zshenv` in the same run
that writes its block to shellenv.

## Workspace secrets

Every shell in the workspace loads `~/.devmachine/env`, the file
`devmachine secrets set NAME --workspace <ws>` fills. It is sourced from
`~/.devmachine/shellenv`, so a command run over `ssh` sees the values too,
not only an interactive shell, and whatever the login shell is. See
https://mydevmachine.sh/concepts/credentials/.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Machines and workspaces](https://mydevmachine.sh/concepts/machines-and-workspaces/)
