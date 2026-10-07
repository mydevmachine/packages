---
name: edit-devmachine-boards
description: "Use when the person wants to change what the Devmachine macOS app shows: add, move, remove or resize a widget on Home, the sidebar, a session's context sidebar or the menu bar, or make a new widget that shows a command's output, a web page, a coding harness's answer, a session's screen or a package's data. Triggers on requests like \"add a widget showing disk usage on main to my context sidebar\", \"put the clock on my Home\", \"move usage above shortcuts\", \"show my open pull requests in the menu bar\", \"remove the links section\", \"show my site's health on Home\", or \"what widgets can I add\". Not for writing a package's widget.yml for publishing (see create-devmachine-package) or for other CLI work (see use-devmachine)."
---

# Edit Devmachine boards

The app draws five areas, each from one board file in the person's
configuration. You change boards through the CLI, which checks every rule
and never writes a broken board. The app picks up the change on its own.
The one exception is a widget written in the board (see below): `widgets
add` cannot create one, so that is the only edit you make by hand.

## The areas

| Area | Board | Layout | What a widget there can read |
| --- | --- | --- | --- |
| `home` | `<config>/boards/home.yml` | canvas: each widget has a frame in points | nothing from the app |
| `sidebar` | `<config>/boards/sidebar.yml` | stack: an ordered list | the selected workspace, when there is one |
| `context-sidebar` | `<config>/boards/context-sidebar.yml` | stack: an ordered list | the selected session, its machine, workspace, path, repo and branch |
| `menubar` | `<config>/boards/menubar.yml` | slot: at most 3 one-line widgets (text up to 24 characters), left to right | nothing from the app |
| `menubar-panel` | `<config>/boards/menubar-panel.yml` | tabs: each widget is one tab of the popover | nothing from the app |

The menu bar title draws only the `text`, `number`, `status` and
`app.brand` views, and runs its widgets whenever the app runs, at most
every 30 seconds. The popover's widgets run only while it is open. By
default the title shows `devmachine-app/brand` and
`devmachine-app/open-pull-requests`, and the popover the
`pull-requests-panel` and `usage-panel` tabs.

Find the configuration with `devmachine config path`: use the path it
prints, without the note in parentheses after it (such as `(from env)`).
Never guess it.

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
devmachine widgets add <package/widget> --board sidebar|context-sidebar|menubar|menubar-panel [--after id | --before id]
devmachine widgets add <package/widget> [--at x,y]          # Home only, in points
devmachine widgets move <id> --after <id> | --before <id> --board sidebar|context-sidebar|menubar|menubar-panel
devmachine widgets remove <id> --board <area>
```

- Prefer a widget from `widgets list` over writing one: it is checked,
  documented, and sized for its area.
- Without `--at`, Home places the widget at the first free spot. Leave it
  to the CLI unless the person names a place.
- In a sidebar, `--size` is a preset or `auto`; leave it out and the CLI
  picks.
- In the menu bar and its popover, leave out `--size` and `--at`: both
  are refused. The menu bar holds 3 widgets; when it is full, ask the
  person which one to take off before you remove anything.
- When a widget is `available: false`, tell the person the command in
  `unavailable_reason` (usually `devmachine packages add …` and `sync`).
  Do not run `sync` on their behalf without asking: it changes machines.

## A widget written in the board

When no widget fits, write one straight into the board: an entry with
`id`, `title`, `source`, `view` and `sizes`. On Home it also needs
`frame`, `size`, `minimized` and `z`; in a sidebar, the menu bar or its popover it
has none of those. Read `references/widget-format.md` first; it has
every source kind, view and rule.

This is the only hand edit, so make it with care:

1. Read the board file right before you edit it.
2. Add or edit only your own entry under `widgets:`. Never touch the
   other entries, `format: 1` or `surface:`.
3. Run `devmachine widgets validate` on that file at once.
4. If it fails, put the file back exactly as it was before your edit.

A context sidebar board with one widget written in it (the entry is
`disk-main`; the board's other lines were already there):

```yaml
format: 1
surface: context-sidebar
widgets:
  - id: todo
    type: devmachine-app/todo
    size: auto
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

and fix every problem it reports before you stop, or restore the file. A
board with a problem is one the CLI refuses to change later.

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
