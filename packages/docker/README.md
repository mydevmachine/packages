# docker

Docker Engine and the Compose plugin, from Docker's own repository on Debian
and Ubuntu and from the system's own on Arch Linux.

- **Scope:** machine
- **Category:** Containers
- **Needs:** `base`

## Settings

None.

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
- Docker itself is installed here, but nobody is put in the `docker` group by
  this package. That happens through
  [`workspace`](../workspace/README.md)'s `groups` setting, and joining that
  group is effectively root on the machine — add it only to a workspace that
  needs it.
- Docker has no repository for a system built on Debian or Ubuntu, such as
  Linux Mint or Pop!_OS. There it uses the repository of the release the
  system is built on, which `/etc/os-release` names in `UBUNTU_CODENAME` or
  `DEBIAN_CODENAME`. A system that names neither stops the sync with a
  message saying so, before anything is installed.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
