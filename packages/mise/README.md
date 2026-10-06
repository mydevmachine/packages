# mise

mise, the per-project runtime manager, installed for one account and
activated in `~/.zshenv` so it is on the `PATH` even without a terminal.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** `workspace`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | the account's own home | Where the account's home is. Read from the account. |

## Credentials

None.

## Add it

```bash
devmachine packages add mise --workspace acme
devmachine sync
```

## Notes

- Only installs mise itself; a package such as [`dev`](../dev/README.md)
  uses it to put Node on the `PATH`, and `mac-mise` does the same on a `self`
  machine.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
