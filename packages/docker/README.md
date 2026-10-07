# docker

Docker Engine and the Compose plugin, from Docker's own repository on Debian
and Ubuntu and from the system's own on Arch Linux. On macOS, colima and the
docker CLI, with Buildx and Compose, from Homebrew, and a VM for each
workspace.

- **Scope:** machine
- **Category:** Containers
- **Needs:** `base`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `workspaces` | `[]` | macOS only: the workspaces that get a Docker VM of their own. Empty means every workspace on the machine. |
| `vm_cpus` | `2` | macOS only. The CPUs each workspace's VM gets. |
| `vm_memory` | `2` | macOS only. The memory each workspace's VM gets, in GiB. |

## On macOS

Docker needs a Linux kernel, so on a Mac it runs in a VM. This package uses
[colima](https://github.com/abiosoft/colima): free, headless, and installed
from Homebrew. Docker Desktop and OrbStack both need someone at the screen, and
a paid licence at company size.

**One VM per workspace, not one for the machine.** colima runs on Lima, which
refuses to run as root, and a VM reaches the Mac's files as the account that
started it. A single VM shared by every workspace would see each workspace's
home as somebody else's: bind mounts of a project would be read-only or
empty, and any workspace with the socket could reach every other one's files.
A VM per account keeps bind mounts working on the account's own home, and keeps
workspaces apart, the way separate accounts are on Linux. The price is memory:
each VM takes `vm_memory`, so narrow `workspaces` on a Mac with many.

Each VM is a launch daemon, `/Library/LaunchDaemons/devmachine.colima.<user>.plist`,
that starts at boot with nobody logged in. It runs as root only long enough to
wait for the account to exist — a sync sets up the machine's packages before
its workspace accounts — then becomes the account and runs
`colima start --foreground`. colima points the account's `docker` CLI at its
own VM, so `docker` and `docker compose` work in the workspace with nothing
else to set. A workspace that leaves the machine, or the `workspaces` list,
has its daemon stopped and removed on the next sync; its VM stays in its home
until the account goes.

The first start downloads the VM's image and takes a few minutes:

```bash
sudo launchctl print system/devmachine.colima.<user>
colima status        # as the workspace account
```


## Credentials

None.

## Add it

```bash
devmachine packages add docker --machine main
devmachine sync
```

## Notes

- Not part of [`essentials`](../essentials/README.md); add it explicitly when
  you want it.
- On Linux, Docker itself is installed here, but nobody is put in the `docker` group by
  this package. That happens through
  [`workspace`](../workspace/README.md)'s `groups` setting, and joining that
  group is effectively root on the machine — add it only to a workspace that
  needs it. On macOS there is no `docker` group: leave it out of `groups`
  there, since each workspace has its own VM.
- Docker has no repository for a system built on Debian or Ubuntu, such as
  Linux Mint or Pop!_OS. There it uses the repository of the release the
  system is built on, which `/etc/os-release` names in `UBUNTU_CODENAME` or
  `DEBIAN_CODENAME`. A system that names neither stops the sync with a
  message saying so, before anything is installed.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
