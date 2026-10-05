# packages

The recipes the [devmachine CLI](https://github.com/mydevmachine/devmachine) applies to a
machine. Nothing here is built into the binary: the CLI fetches a release of this
repository, checks it against the checksum published beside it, and runs what it
finds.

## What a package is

An Ansible role, with one extra file beside it:

```
packages/<name>/
  package.yml        what this is, what it needs, what it offers
  tasks/main.yml     required
  skills/*/SKILL.md  optional Agent Skills contributed by this package
  defaults/, vars/, files/, templates/, handlers/
```

Nothing is translated. What is written here is what runs on the machine, so a
failure points at a line somebody wrote rather than at generated YAML they have
never seen.

## What is in this release

| Package | Scope | What it does |
| --- | --- | --- |
| [`essentials`](packages/essentials/README.md) | machine | base, git, firewall, ssh_hardening, caddy and devmachine-app, in one package. |
| [`base`](packages/base/README.md) | machine | The base tools, a shared tmux config, and the `resume` session picker. |
| [`git`](packages/git/README.md) | machine | Installs git. |
| [`docker`](packages/docker/README.md) | machine | Docker Engine and the Compose plugin, from Docker's own repository. |
| [`caddy`](packages/caddy/README.md) | machine | A reverse proxy that gets its own certificates. |
| [`firewall`](packages/firewall/README.md) | machine | ufw, with SSH open and HTTP optional. |
| [`fail2ban`](packages/fail2ban/README.md) | machine | fail2ban, with a jail for sshd. |
| [`hardware-guard`](packages/hardware-guard/README.md) | machine | Watches temperatures and battery, alerts, and shuts the machine down when a limit holds. |
| [`ssh_hardening`](packages/ssh_hardening/README.md) | machine | Password authentication off, for good. |
| [`tailscale`](packages/tailscale/README.md) | machine | Joins the machine to a tailnet, and resolves `tailscale:<name>` addresses. |
| [`cloudflare`](packages/cloudflare/README.md) | machine | DNS zones on Cloudflare. |
| [`hostinger`](packages/hostinger/README.md) | machine | DNS zones on Hostinger. |
| [`mac-brew`](packages/mac-brew/README.md) | machine | Installs Homebrew taps, formulae and casks from lists. |
| [`mac-mise`](packages/mac-mise/README.md) | machine | Installs mise's global tools from a list. |
| [`devmachine-app`](packages/devmachine-app/README.md) | machine | What the Devmachine macOS app asks a machine for. |
| [`workspace`](packages/workspace/README.md) | workspace | The Linux account a person works in. |
| [`zsh`](packages/zsh/README.md) | workspace | zsh, Oh My Zsh, and tmux auto-attach over SSH. |
| [`mise`](packages/mise/README.md) | workspace | The per-project runtime manager, activated for one account. |
| [`dev`](packages/dev/README.md) | workspace | The GitHub CLI, bun, Node LTS and unzip for one account. |
| [`git-key`](packages/git-key/README.md) | workspace | One SSH key the machine pushes with, copied into each workspace. |
| [`glab`](packages/glab/README.md) | workspace | The GitLab CLI, installed for one account. |
| [`sentry`](packages/sentry/README.md) | workspace | The Sentry CLI, installed for one account. |
| [`claude-code`](packages/claude-code/README.md) | workspace | The Claude Code CLI for one account. |
| [`claude-plugins`](packages/claude-plugins/README.md) | workspace | Installs and updates Claude Code plugins in one account. |
| [`claude-remote-control`](packages/claude-remote-control/README.md) | workspace | Keeps one account's Claude Code Remote Control session up. |
| [`antigravity`](packages/antigravity/README.md) | workspace | Google's Antigravity CLI (`agy`) for one account. |
| [`opencode`](packages/opencode/README.md) | workspace | The opencode CLI for one account. |
| [`pi`](packages/pi/README.md) | workspace | The Pi coding agent for one account, without Node. |
| [`kimi-code`](packages/kimi-code/README.md) | workspace | Moonshot AI's Kimi Code CLI (`kimi`) for one account. |
| [`cline`](packages/cline/README.md) | workspace | The Cline CLI for one account. |
| [`codex`](packages/codex/README.md) | workspace | OpenAI's Codex CLI for one account, without Node. |
| [`devmachine-skills`](packages/devmachine-skills/README.md) | workspace | Teaches supported agents to operate Devmachine and create packages. |

## A pin is a tag, never a branch

The CLI is pointed at a release (`packages: v23`), not at `main`. A branch
would mean the set changes under you because somebody pushed an hour ago.
Upgrading is meant to be a deliberate act with a diff to read.

Releases are plain numbered tags (`v2`, `v3`, ...), not semver. A tag is never moved: a fix ships as a new
tag, so a checksum recorded in somebody's lock file stays true.

The release is a tarball built with `tar --sort --owner=0 --group=0
--numeric-owner --mtime`, so the same tree always gives the same checksum. The
checksum goes in the CLI's lock file: content that changes after the fact is
refused and named.

## Rules a recipe keeps

- **No `apt`, `apt_key` or `apt_repository`.** `package:` is what installs
  things. Whatever differs between families — package names, a repository path,
  a service name — lives in `vars/<family>.yml`, loaded with
  `include_vars: "{{ ansible_os_family }}.yml"`.
- **`name:` is the directory name.** A package is found by its directory.
- **`needs:` is written down.** Ordering is declared, never implied by the order
  of a list.
- **Nothing personal.** This repository is public and holds no real hostname,
  domain, address, account or token. Examples use `example.com` and
  `203.0.113.x`.
- **English, everywhere.**

## Extension points

A package can declare a place other packages may write into:

```yaml
provides:
  sites.d: /etc/caddy/sites.d
```

and another package contributes to it:

```yaml
extends:
  caddy.sites.d: files/my-site.caddy
```

It is a contribution, not a patch, and it cannot reach anywhere else. `caddy`
therefore serves nothing by itself — every site is a file some other package
drops into that directory.

## Network packages

A machine package can answer for a private network's addresses:

```yaml
network:
  prefix: tailscale
  resolve: bin/resolve
  join: bin/join
  self_name: bin/self-name
```

A machine's `hosts` entry written `tailscale:<name>` then belongs to this
package. `resolve` runs on the person's computer and prints the addresses,
or exits 3 when the network is not reachable from there. `join` and
`self_name` run on the machine for `devmachine login tailscale`: the first
signs it in, the second prints the name to add to `hosts`. The CLI knows the
prefix and the scripts, never the product — a new network is a new package,
not a new CLI.

The scripts are Python 3.9 with the standard library only, like an
entrypoint, and each network package tests them in its own `test/`. The
contract is in the CLI's
[network package contract](https://mydevmachine.sh/reference/network-package-contract/).

## Adding a recipe

```bash
devmachine packages new <name>
# write it
devmachine packages validate packages/<name>
./scripts/syntax-check.sh
```

`scripts/validate.sh` runs the validator over every recipe, and CI runs both.

## Releasing

Do these steps in order, before you tag a release.

### 1. Sync the skill references, if the CLI shipped new docs

The `devmachine-skills` package keeps a copy of the devmachine CLI's own docs,
under `packages/devmachine-skills/skills/*/references`. CI compares that copy
against the CLI's latest release and fails if they differ. So run this step
right after any CLI release that changed its docs, before you tag a new
release here.

```bash
tag=$(gh release view --repo mydevmachine/devmachine --json tagName -q .tagName)
gh repo clone mydevmachine/devmachine /tmp/cli-docs -- --depth 1 --branch "$tag"
./scripts/sync-skill-references.sh /tmp/cli-docs/docs
git add packages/devmachine-skills
```

The script takes one argument: a checkout of the CLI's `docs/` directory — the
folder that directly holds `reference/`, `concepts/` and
`troubleshooting.md`. This is the same check CI runs, with `--check` added,
on every push: it compares the generated output against what is committed
here and fails the build on any difference, so a stale copy never reaches
main.

Commit the result, if anything changed, before you move on.

### 2. Validate and check for real data

```bash
./scripts/validate.sh
./scripts/check-no-real-data.sh
```

`validate.sh` runs the CLI's own validator over every recipe.
`check-no-real-data.sh` checks the tree against the maintainer's private
pattern list, which lives outside this repository; with no list to check
against, it passes without doing anything.

### 3. Tag and push

Push `main` first and wait for CI to pass. Then tag that commit:

```bash
git tag -s v23 -m v23
git push origin v23
```

Tags here count up from `v2` (`v3`, `v4`, ... `v22`, `v23`, ...) — not semver.
A tag is signed and, once pushed, never moved: a fix ships as a new tag, so a
checksum recorded in somebody's lock file stays true.

Pushing the tag runs the `release` workflow. It builds a reproducible tarball
of `packages/`, writes a `checksums.txt` beside it, and attaches both to the
GitHub release.

### Ordering between the CLI and this repository

A new manifest field, or any new package capability, is useless until a
released CLI version understands it. An older CLI meets an unknown field with
no promise of how it behaves — it may ignore it, or refuse the whole file. So
the CLI release that adds support for something always ships before the
packages release that uses it.

### `category`

`category` is an optional field on a package's `package.yml`. It groups the
package with others like it (for example "Security" or "DNS") on the packages
listing page at https://mydevmachine.sh/packages/.

## Licence

MIT. See [LICENSE](LICENSE).
