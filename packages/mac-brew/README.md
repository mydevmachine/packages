# mac-brew

Installs Homebrew taps, formulae and casks from lists. Never removes
anything. On your own Mac (`self: true`) or a Mac reached over SSH.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `prefix` | `/opt/homebrew` | Where Homebrew lives. Left unset, `/opt/homebrew` on Apple Silicon and `/usr/local` on an Intel Mac. |
| `taps` | `[]` | Homebrew taps to add. |
| `formulae` | `[]` | Homebrew formulae to install. |
| `casks` | `[]` | Homebrew casks to install. |
| `trusted_casks` | `[]` | Casks to trust, as full names `<tap>/<cask>`. Recent Homebrew refuses to load a cask from an unofficial tap until it is trusted, per item on purpose rather than per tap. |
| `trusted_formulae` | `[]` | Formulae to trust, as full names `<tap>/<formula>`, for the same reason as `trusted_casks`. |

## Credentials

None.

## Add it

```bash
devmachine machines add --self main
devmachine packages add mac-brew --machine main
devmachine workspaces defaults --add mac-brew
devmachine sync
```

## Bootstrap

`bin/bootstrap` brings a Mac to the point where devmachine can run Ansible on
it. The CLI runs it as the admin login, never as root (Homebrew refuses root);
it reaches root only through `sudo -n`. Progress goes to stderr; stdout holds
one JSON document.

`bootstrap check` changes nothing and lists what is missing:

```json
{"missing": [{"name": "Xcode Command Line Tools", "minutes": 10}, {"name": "Homebrew", "minutes": 5}, {"name": "Ansible", "minutes": 3}]}
```

`bootstrap apply` installs, in order, the Xcode Command Line Tools (headless,
through `softwareupdate`), Homebrew (the official installer with
`NONINTERACTIVE=1`) and Ansible (`brew install ansible`). It skips each step
whose result already exists: an `ansible-playbook` already on `PATH`, in
`~/.local/bin` (pipx) or in a Homebrew prefix is used as it is. It prints the
absolute path the CLI calls Ansible by, and the folders to put first on `PATH`:

```json
{"ansible_playbook": "/opt/homebrew/bin/ansible-playbook", "path_prefix": ["/opt/homebrew/bin", "/opt/homebrew/sbin"]}
```

A failure exits non-zero with the step and what to do:

```json
{"error": {"step": "homebrew", "message": "the Homebrew installer failed; its output is above. It needs passwordless sudo for the admin login."}}
```

## Notes

- On a Mac reached over SSH the play runs as root, so every `brew` call runs
  as the account that owns the Homebrew folder. On your own Mac it runs as
  you, as before.
- Installing formulae or casks runs `brew update` first, as `brew install`
  in a terminal does. A Homebrew whose own code is older than the formulae it
  reads fails with errors such as `unknown keyword`.

- Only installs what you list; it never removes a formula or cask you took
  out of the list.
- A cask or formula from an unofficial tap needs its full name in
  `trusted_casks`/`trusted_formulae` before Homebrew will load it.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Your computer as a machine](https://mydevmachine.sh/how-it-works/your-computer-as-a-machine/)
