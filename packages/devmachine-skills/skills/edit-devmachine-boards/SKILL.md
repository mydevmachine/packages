---
name: edit-devmachine-boards
description: "Use when the person wants to change what the Devmachine macOS app shows: add, move, remove or resize a widget on Home, the sidebar or a session's context sidebar, or make a new widget that shows a command's output, a web page, a coding harness's answer, a session's screen or a package's data. Triggers on requests like \"add a widget showing disk usage on main to my context sidebar\", \"put the clock on my Home\", \"move usage above shortcuts\", \"remove the links section\", \"show my site's health on Home\", or \"what widgets can I add\". Not for writing a package's widget.yml for publishing (see create-devmachine-package) or for other CLI work (see use-devmachine)."
---

# Edit Devmachine boards

The app draws three areas, each from one board file in the person's
configuration. You change boards through the CLI, which checks every rule
and never writes a broken board. The app picks up the change on its own.

## The areas

| Area | Board | Layout | What a widget there can read |
| --- | --- | --- | --- |
| `home` | `<config>/boards/home.yml` | canvas: each widget has a frame in points | nothing from the app |
| `sidebar` | `<config>/boards/sidebar.yml` | stack: an ordered list | the selected workspace, when there is one |
| `context-sidebar` | `<config>/boards/context-sidebar.yml` | stack: an ordered list | the selected session, its machine, workspace, path, repo and branch |

Find the configuration with `devmachine config path`. Never guess it.

## Read before you change

- `devmachine --format json widgets list --board <area>` — every widget
  that fits that area, with its inputs, sizes, `trust`, and whether it is
  `available` (`unavailable_reason` names the command that fixes it). Its
  `providers` lists every package provider a widget may read.
- `devmachine widgets help <package/widget>` — one widget's inputs, sizes
  and areas.
- Read the board file itself to see what is there and each widget's `id`.
- `devmachine widgets schema --json` — the engine contract: every
  provider, view, size and rule.

## Change a board with the CLI

```bash
devmachine widgets add <package/widget> --board <area> [--id x] [--set name=value]... [--size s]
devmachine widgets add <package/widget> --board sidebar|context-sidebar [--after id | --before id]
devmachine widgets add <package/widget> [--at x,y]          # Home only, in points
devmachine widgets move <id> --after <id> | --before <id> --board sidebar|context-sidebar
devmachine widgets remove <id> --board <area>
```

- Prefer a widget from `widgets list` over writing one: it is checked,
  documented, and sized for its area.
- Without `--at`, Home places the widget at the first free spot. Leave it
  to the CLI unless the person names a place.
- In a sidebar, `--size` is a preset or `auto`; leave it out and the CLI
  picks.
- When a widget is `available: false`, tell the person the command in
  `unavailable_reason` (usually `devmachine packages add …` and `sync`).
  Do not run `sync` on their behalf without asking: it changes machines.

## A widget written in the board

When no widget fits, write one straight into the board: an entry with
`id`, `title`, `source`, `view` and `sizes` (on Home also `frame`, `size`,
`minimized`, `z`). Read `references/widget-format.md` first; it has every
source kind, view and rule.

```yaml
  - id: disk-main
    title: Disk on main
    source: {kind: command, run: df, args: [-h, /], target: {machine: main}, every: 60s}
    view: {kind: text}
    sizes: [medium]
```

Then always run:

```bash
devmachine widgets validate <config>/boards/<area>.yml
```

and fix every problem it reports before you stop. A board with a problem
is one the CLI refuses to change later.

- `run` names one program; its arguments go in `args`. A template such
  as `{{context.workspace}}` may fill an argument, never the program.
- `target` is `local` (the person's computer), `{machine: <name>}` or
  `{workspace: <name>}`; the name must be in `devmachine machines list` or
  `devmachine workspaces list`.
- A package provider is read as `{kind: provider, name: <package>/<command>,
  target: {machine: <name>}, every: <at least its min_every>}`, with a view
  that takes `json` and `view.value: "{{json.<field>}}"`. Its package must
  be added to that machine and synced.

## Approval: tell the person, never work around it

A widget written in a board that runs something — a `command`, `prompt`,
`session` or package provider — shows **Allow** and **Deny** in the app
and runs nothing until the person presses Allow. The same holds for a
widget from a third-party package (`trust: third-party`).

- After adding such a widget, tell the person it waits for their approval
  in the app, and what it will run.
- Never edit, create or delete the app's approvals file, and never try to
  approve a widget yourself. The approval exists so that you cannot.

## Packages from a git address

`devmachine packages install <address>` brings in a package somebody
published. Never run it without the person's go-ahead for that address.
First show them what it brings:

```bash
devmachine --format json packages install <address> --check
```

Its tasks run as root on every machine it is added to, and its widgets
that run code ask before they run. `packages update <name>` and `packages
remove <name>` manage it later.

## Example

"Add a widget showing disk usage on main to my context sidebar":

1. `devmachine --format json widgets list --board context-sidebar` and
   look for one that shows disk use: `devmachine-app/machine-stats`.
2. `devmachine widgets add devmachine-app/machine-stats --board
   context-sidebar --set machine=main`.
3. If the list says `available: false`, `widgets add` refuses it as not
   available yet: tell the person to add the `devmachine-app` package to
   `main` and sync, then add it.
4. Tell them it reads `devmachine-app/stats` on `main` every minute.

If no widget fit, write the `disk-main` entry above into
`context-sidebar.yml`, run `widgets validate`, and tell the person it
waits for their approval in the app.

## References

- `references/concepts/widgets.md` — what a widget, an area and a board are.
- `references/widget-format.md` — every field, source, view and rule, with
  each error message.
- `references/commands-widgets.md` — `devmachine widgets`, every flag and
  its JSON.
