# git-key

One SSH key the whole machine pushes to a forge with, copied into each
workspace.

- **Scope:** workspace
- **Category:** Developer tools
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `git-key` | manual | machine | yes | `devmachine login git-key` |

`git-key`'s login runs `devmachine-make-git-key` on the machine, as the
admin account, and stores the result at `~/.ssh/id_ed25519`. Because it is a
machine credential, a following `devmachine sync` copies it into every
workspace that installs this package.

## Add it

```bash
devmachine packages add git-key --workspace acme
devmachine login git-key
devmachine sync
```

## Notes

- One key serves every workspace that installs this package; there is no
  per-workspace key.
- Pair it with `workspace.sign_commits` (on by default) to sign commits with
  this key.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Credentials](https://mydevmachine.sh/concepts/credentials/)
