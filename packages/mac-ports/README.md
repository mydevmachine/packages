# mac-ports

Installs MacPorts ports from a list. Never removes anything. On your own Mac
(`self: true`) or a Mac reached over SSH. The choice beside `mac-brew`: a Mac
uses one of the two.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `ports` | `[]` | MacPorts ports to install, e.g. `git` or `ripgrep`. |

## Credentials

None.

## Add it

```bash
devmachine packages add mac-ports --machine main
devmachine sync
```

## Bootstrap

`bin/bootstrap` brings a Mac to the point where devmachine can run Ansible on
it. The CLI runs it as the admin login, never as root; it reaches root only
through `sudo -n`. Progress goes to stderr; stdout holds one JSON document.

`bootstrap check` changes nothing and lists what is missing:

```json
{"missing": [{"name": "Xcode Command Line Tools", "minutes": 10}, {"name": "MacPorts", "minutes": 5}, {"name": "Ansible (py314-ansible)", "minutes": 15}]}
```

`bootstrap apply` installs, in order, the Xcode Command Line Tools (headless,
through `softwareupdate`), MacPorts (the `.pkg` for the running macOS major
version from the latest
[macports-base release](https://github.com/macports/macports-base/releases),
checked against the SHA-1 published beside it) and Ansible
(`port install py314-ansible`). It skips each step whose result already
exists. It prints the absolute path the CLI calls Ansible by, and the folders
to put first on `PATH`:

```json
{"ansible_playbook": "/opt/local/bin/ansible-playbook-3.14", "path_prefix": ["/opt/local/bin", "/opt/local/sbin"]}
```

A failure exits non-zero with the step and what to do:

```json
{"error": {"step": "macports", "message": "the latest MacPorts release has no installer for macOS 27. Install MacPorts by hand from https://www.macports.org/install.php."}}
```

## Notes

- MacPorts names Python tools with the Python version as a suffix, so
  Ansible's command is `ansible-playbook-3.14`, not `ansible-playbook`. The
  bootstrap reports the real path; it does not run `port select`.
- The bare `ansible` port is an obsolete stub; `py314-ansible` is the one that
  carries Ansible.
- Ports install as root. A Mac reached over SSH runs the play as root already;
  on your own Mac, installing a port needs `sudo` without a password.
- It never runs `port selfupdate` or `port upgrade`: updating MacPorts is
  yours to decide.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Your computer as a machine](https://mydevmachine.sh/how-it-works/your-computer-as-a-machine/)
