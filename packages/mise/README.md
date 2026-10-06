# mise

mise, the per-project runtime manager, installed for one account and
activated in `~/.devmachine/shellenv` so it is on the `PATH` in every shell,
bash, zsh or sh, even without a terminal.

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
- zsh and bash run mise's own hook, so a tool changes with the folder you
  are in. Any other shell, such as `sh`, gets mise's shims on the `PATH`
  instead, and a shim runs the version the folder asks for too.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
