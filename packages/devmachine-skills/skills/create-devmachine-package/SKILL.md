---
name: create-devmachine-package
description: Use when writing or editing a Devmachine package — a new Ansible role plus package.yml for persistent machine or workspace state that has no suitable existing package, or converting repeatable custom setup into one. Triggers on requests like "make a package for X", "install X on my server as a package", "write an Ansible role for this", "turn this setup into a reusable package", or "add a new package to devmachine". Not for running or adding an EXISTING package to a machine or workspace, or any other CLI operation (see use-devmachine).
---

# Create a Devmachine Package

A package is an ordinary Ansible role plus `package.yml`. Use the CLI to create
and validate it instead of inventing the layout.

## Decide first

1. If the software is intentionally volatile, leave it unmanaged.
2. If a published package already fits, select it.
3. Otherwise create a local package under the effective configuration's
   `packages/` directory.

Choose `machine` scope for shared host state and `workspace` for state owned by
one account. Workspace names and package names do not imply routing; explicit
package membership does.

## Build from the live contract

```bash
devmachine config path
devmachine packages schema --json
devmachine packages new <name> --scope machine|workspace --into <config-dir>/packages
devmachine packages validate <config-dir>/packages/<name>
```

Read `references/package-format.md` and the generated skeleton before editing.
Keep tasks idempotent and portable: use Ansible modules, declare `needs`, avoid
direct `apt`, and put defaults in the role. A package may also contribute
complete Agent Skill directories with `skills.path`; the CLI owns canonical
installation and harness adapters.

## One package for every system it declares

A machine runs Debian, Ubuntu, Arch Linux or macOS. Write one package, never
`x-debian` and `x-arch`. Read `references/multi-os.md` before writing tasks.

- Declare `platforms` (`[linux]`, `[macos]` or `[linux, macos]`) for what
  the package really runs on. Left out means everywhere.
- Put what differs per system in `vars/`, loaded through the `first_found`
  chain in `references/multi-os.md`, copied as it is. Read facts only as
  `ansible_facts['...']`.
- A system built on Debian, Ubuntu or Arch (Linux Mint, Pop!_OS, Manjaro)
  is set up as its base. Ansible can give it its own `distribution` but
  gives it its base's `os_family`, so decide by `os_family` or `pkg_mgr`.
  A vendor repository has no tree for it: take the base's release name from
  `UBUNTU_CODENAME` or `DEBIAN_CODENAME` in `/etc/os-release`, as `docker`
  and `tailscale` do.
- Install in this order of preference: the project's official installer, a
  release binary by OS and architecture, `mise`, the `package` module with
  names in `vars/`, and `tasks/<System>.yml` only when the steps differ.
- Read a workspace account's home and group from the account (the `user`
  module in check mode), never `/home/<user>` or `group: <user>`.
- Check, never guess: `ansible-doc <module>`, docs.ansible.com,
  `apt-cache policy`, `pacman -Si`, `brew info`, `port info`.

## Reference

Read the matching file under `references/` before guessing at the manifest
format:

| Question | File |
| --- | --- |
| The package manifest format (`package.yml`, `needs`, `kind`, `entrypoint`) | `references/package-format.md` |
| Writing a DNS provider package | `references/dns-provider-contract.md` |
| How scope, ordering, and overrides work | `references/concepts/packages.md` |
| One package on Debian, Ubuntu, Arch Linux and macOS: the vars chain, package names, traps | `references/multi-os.md` |

These are copies of the CLI's own docs, kept in sync by
`scripts/sync-skill-references.sh`. When a copy disagrees with the installed
binary, the binary wins: prefer `devmachine packages schema` and `devmachine
<command> --help` for the running binary's own truth.

For anything the local references do not answer, read
https://mydevmachine.sh/llms-full.txt (every documentation page in
one file) or the page on https://mydevmachine.sh/.

## Prove it on a fake target

Add the package with `devmachine packages add` or `devmachine workspaces edit`.
Use a disposable local machine, run `devmachine sync --check --tags <name>`,
apply once, verify the intended state, then apply the same sync again. The
second run must report `changed=0`. Preserve unrelated files and unmanaged
software. Do this on every system the package's `platforms` declares, not
only one: `devmachine machines create-local <name> --distro arch` makes an
Arch VM beside the default Ubuntu one.

Do not develop or test a package against a real machine. Before any real
`doctor`, `sync --check`, `sync`, `run`, SSH, DNS, or publication command,
show the exact command and obtain explicit approval for that target.

## Completion checklist

- `packages validate` passes.
- Repository syntax and data-leak checks pass when contributing publicly.
- Fake-target behavior and second-run idempotence pass on every system in
  `platforms`.
- Package membership is limited to the intended workspaces.
- No real machine was contacted without exact-command approval.
