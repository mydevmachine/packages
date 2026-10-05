---
name: use-devmachine
description: "Use when running, inspecting, or troubleshooting the Devmachine CLI itself, or when answering ANY question about a machine, workspace, server, or VPS it manages — even a read-only one such as \"what's published on the VPS\", \"DNS entries/records for my domain\", \"is my site/subdomain/certificate working\", \"what packages are installed\", \"logins, tokens, API keys or credentials\", \"how much RAM/disk/load\", \"is the server healthy\", \"open/connect to my workspace\", \"run a command on the server\", \"private access to a port\", \"did the host key/fingerprint change\", or \"where is my config\". Covers adding or editing a machine (including the local self:true machine) or workspace, adding a package to one, running sync, expose, tunnel, dns, credentials, secrets, login, run --package, upload, download, update, Tailscale addresses, or any other devmachine subcommand. Not for writing a new package's Ansible role (see create-devmachine-package)."
---

# Use Devmachine

## Machines: only through devmachine

- Create and change every machine with a devmachine command. A machine
  exists for devmachine only once it is in its configuration: check with
  `devmachine machines list`. Never create, provision or configure a machine
  by hand (`limactl`, `multipass`, raw `ssh`, editing `config.yml`) when a
  devmachine command does it. A machine made by hand is invisible to
  devmachine and to the app.
- A machine on this computer ("a local machine", "a Lima VM"):
  `devmachine machines create-local <name> --add --location local`. It
  needs Lima; if `limactl` is missing, install it with `brew install lima`. `--add` gives
  it the essentials (including `devmachine-app`); then run
  `devmachine sync --machine <name> --yes` to apply them.
- A server: run `devmachine machines scan --address <address>` and show the
  fingerprint to the person to compare with the provider's console. Then
  `devmachine machines add --address <address> --name <name> --fingerprint
  SHA256:… --location <location> [--key agent:SHA256:…] [--user <login>]`.
  Pass `--user` when the login is not root, as on every Mac.
- Before adding a machine, ask the person where it is, for example
  `hostinger`, `home` or `office`, and pass it as `--location`. With no
  answer, a server is `external` and a Lima VM made here is `local`. Change
  it later with `devmachine machines edit <name> --location <location>`.
- Your shell has no terminal, so a command that asks a question waits
  forever. Always pass the non-interactive flags, such as `--yes`, and
  `devmachine skills add --agent <harness> --yes`.
- Find the configuration with `devmachine config path`. Never guess it.

## Setting up a machine: the person decides

A machine runs Debian, Ubuntu, Arch Linux or macOS. `essentials`,
`firewall` and `caddy` are Linux-only; `sync` refuses them on a Mac.

- To set up a machine, use `devmachine setup` (a person at a terminal) or
  `devmachine machines add` (you). Never install Ansible, Homebrew or
  MacPorts yourself.
- When setup asks something — which package manager (Homebrew or
  MacPorts), or whether to install what the machine lacks — ask the person
  and wait for the answer. Never choose for them.
- Without a terminal, pass the person's answer as a flag:
  `--package-manager brew` or `--package-manager ports`, and
  `--install-prerequisites` only after they said yes to the install.
- `--yes` never means consent to install. Never use it, or
  `--install-prerequisites`, to get past a question the person has not
  answered.
- On a Mac already in the configuration, read
  `devmachine --format json doctor --machine <name>` before `setup` or
  `sync`. Each `prerequisite: <name>` entry of `checks[]` is something
  missing. Tell the person what is missing, and the steps only they can do:
  turn Remote Login on (System Settings > General > Sharing), give the admin
  login passwordless sudo, and allow full disk access for remote users when
  a package needs it.
- Before you compose a `devmachine run` command, read
  `devmachine --format json machines show <name>`. Use what is under
  `observed`: `pkg_mgr` (apt, pacman, homebrew, macports), `service_mgr`
  (systemd, launchd) and `path_prefix` (`run` already puts it first on
  `PATH`). `apt list --installed` on a Mac or
  `systemctl` on launchd is a guess, and it fails.

## First, always

Answer any question about a machine, workspace, DNS, published sites,
packages, logins, or configuration by running the matching `devmachine
<command>` below — never by reading or grepping the configuration folder or
an old Ansible repository by hand, even for a read-only question. This
applies whether the question is asked directly or comes up while doing
something else.

A command that contacts a machine (see Safety boundary) still needs the
person's explicit approval for that exact command. Ask for it — never fall
back to reading files instead.

## Question → command

| Question or need | Command |
| --- | --- |
| What's published / my sites / subdomains / Caddy routes | `devmachine expose list` |
| Publish a port as a site | `devmachine expose add <workspace> <port> --host <host>` (live in seconds, no sync needed) |
| DNS records / entries of a domain or zone | `devmachine dns list [zone]` |
| Does my domain/site work, certificate valid | `devmachine dns status [host]` |
| Add or change a DNS record | `devmachine dns add <name> <type> <value>` |
| Which DNS providers / zones are available | `devmachine dns providers` |
| Open / enter / connect to a workspace | `devmachine ssh [workspace]` or `devmachine mosh [workspace]` |
| Run a command on the server | `devmachine run "<command>"` |
| How much RAM / disk / load | `devmachine stats` |
| Is my server healthy / can it connect | `devmachine doctor` |
| What's installed / add a tool | `devmachine packages list` / `devmachine packages add <name>` then `devmachine sync` |
| Logins, tokens, API keys, credentials | `devmachine credentials list`, `devmachine login <credential>`, `devmachine secrets set <name>` then `devmachine credentials push` |
| My app's own secret / API key / `.env` value in a workspace | `devmachine secrets set <NAME> --workspace <workspace> [--env-file <path>] --push` |
| Send a file / screenshot / attachment to a workspace | `devmachine upload <file>... --workspace <workspace> [--dir <folder>]` (prints the path on the machine) |
| Get a file / folder from a workspace to this computer | `devmachine download <remote-path>... --workspace <workspace> [--to <folder>]` (default `~/Downloads`, never overwrites; a folder arrives as one `.tar.gz`) |
| Which address / IP will be used for a machine, Tailscale or Headscale addresses | `devmachine resolve [--machine <m>]`; join a private network with `devmachine login tailscale` (Headscale: set `tailscale.login_server` first) |
| Private access to a port (not a public site) | `devmachine tunnel <workspace> <port>` |
| Server fingerprint / host key changed | `devmachine machines trust [name] --check` (says what changed, changes nothing, and prints the `fix` and `verify` commands); after the person verifies the fingerprint on the server's console, run the printed fix (`--replace --expect <fingerprint>`) |
| Where is my config / what's in it | `devmachine config path` / `devmachine config show` |
| List machines / servers | `devmachine machines list` |
| List workspaces / accounts | `devmachine workspaces list` |
| SSH aliases for my terminal / aliases stale | `devmachine aliases` (check with `devmachine doctor`, fix with `devmachine aliases --write`) |
| Update everything / is devmachine up to date / upgrade | `devmachine update` (updates the CLI, packages pin and skills, runs doctor and `sync --check`, then asks before syncing) |
| Update only the CLI binary, nothing else | `devmachine update --cli-only` |
| Apply pending changes to the server | `devmachine sync` |

Use the CLI as the source of truth. Do not replace a missing CLI operation with
ad-hoc SSH or an old Ansible repository without first identifying the missing
capability.

A **machine** is a server the CLI can reach, or the local computer itself when
marked `self: true` in `config.yml`. A **workspace** is an account on a
machine, Linux or macOS (never on a self machine). Each machine or workspace lists the
**packages** it has — an Ansible role plus `package.yml`, the CLI's only unit
of persistent state. `sync` is what converges a machine to match the
configuration; most other configuration edits, including `expose` (which
writes a route under the workspace, not a live proxy), only take effect once
`sync` runs. `run --package <name>` invokes a package's declared entrypoint
directly, without going through `sync`.

## Start here

Always begin with these local, read-only commands:

```bash
devmachine config path
devmachine help --json
```

Then run `devmachine <command> --help` for the selected operation.

## Reference

Read the matching file under `references/` before guessing at behavior:

| Question | File |
| --- | --- |
| Exact flags, subcommands, or command behavior | `references/commands.md` |
| A configuration key or setting | `references/settings.md` |
| An error message | `references/troubleshooting.md` |
| Machines, workspaces, `self` | `references/concepts/machines-and-workspaces.md` |
| Configuration file layout | `references/concepts/configuration.md` |
| Packages | `references/concepts/packages.md` |
| DNS and public sites | `references/concepts/dns.md` and `references/concepts/publishing.md` |
| Credentials | `references/concepts/credentials.md` |
| Agent skills shipped by a package | `references/concepts/agent-skills.md` |
| What a machine needs before setup, a Mac's prerequisites, consent | `references/what-a-machine-needs.md` |

These are copies of the CLI's own docs, kept in sync by
`scripts/sync-skill-references.sh`. When a copy disagrees with the installed
binary, the binary wins: prefer `devmachine <command> --help` and `devmachine
packages schema` for the running binary's own truth.

For anything the local references do not answer, read
https://mydevmachine.sh/llms-full.txt (every documentation page in
one file) or the page on https://mydevmachine.sh/.

## Safety boundary

- Configuration edits such as `packages add`, `workspaces edit`, and
  `workspaces defaults` are local until `sync`.
- Commands such as `doctor`, `run`, `stats`, `sync --check`, DNS, and `expose`
  may contact a configured machine.
- A machine appearing in `config.yml` is not permission to contact it. Obtain
  explicit approval for the exact command before touching a real machine.
- Use a disposable local machine for development and acceptance. Reuse one
  fake machine for related checks.
- Public writes require the command's explicit consent boundary; for example,
  unattended `expose add` uses `--publish`, not `--yes`.

## Persistent versus volatile state

Leave deliberately volatile software unmanaged. For state that must converge,
reuse a published package or create a local package; do not silently install it
with `run`. Use `run` to invoke a package entrypoint or for an explicitly
temporary operation.

## Before reporting completion

Run the command's dry-run mode when available, inspect the target named by the
effective configuration, apply only with the required approval, and verify the
result through a Devmachine command.
