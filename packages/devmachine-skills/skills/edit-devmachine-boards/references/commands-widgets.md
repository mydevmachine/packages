## widgets

```text
devmachine widgets list [--board home|sidebar|context-sidebar|menubar|menubar-panel]
devmachine widgets help <package/widget>
devmachine widgets validate [path...]
devmachine widgets schema [--json]
devmachine widgets add <package/widget> [--board home|sidebar|context-sidebar|menubar|menubar-panel]
    [--id x] [--set name=value]... [--size s] [--at x,y | --after id | --before id]
devmachine widgets remove <id> [--board home|sidebar|context-sidebar|menubar|menubar-panel]
devmachine widgets move <id> (--after id | --before id) --board sidebar|context-sidebar|menubar|menubar-panel
devmachine widgets set <id> --board home|sidebar|context-sidebar|menubar|menubar-panel
    [--title t] [--every d] [--set name=value]...
```

The widgets the app draws, and the boards they sit on. Local only: these
commands never connect to a machine. See [Widgets](concepts/widgets.md)
and [the widget format](widget-format.md).

`list` reads the pinned packages release and your own packages. With
nothing pinned, or no `config.yml` yet, it reads the latest release; when
that cannot be found it fails, with nothing on stdout. `--format json`
prints:

```json
{
  "engine": "1.5",
  "packages_release": "v40",
  "widgets": [
    {
      "name": "claude-code/usage",
      "package": "claude-code",
      "widget": "usage",
      "origin": "release",
      "trust": "official",
      "version": "v40",
      "path": "/Users/alice/.config/devmachine/cache/packages/v40/packages/claude-code/widgets/usage",
      "summary": "Coding-harness usage windows.",
      "requires_engine": ">= 1.0",
      "fits": ["canvas", "stack", "slot"],
      "context": {},
      "inputs": {"harness": {"type": "string", "default": "claude", "summary": "Which harness."}},
      "source": {"kind": "provider", "name": "app/harness-usage", "with": {"harness": "{{inputs.harness}}"}, "every": "60s"},
      "view": {"kind": "app.harness-usage"},
      "sizes": ["small", "medium", "wide"],
      "default_size": "medium",
      "places": ["home"],
      "single": false,
      "surfaces": ["context-sidebar", "home", "sidebar"],
      "available": true,
      "unavailable_reason": ""
    }
  ],
  "providers": {
    "devmachine-app/stats": {
      "package": "devmachine-app",
      "command": "stats",
      "scope": "machine",
      "trust": "official",
      "returns": {"disk": "object", "load": "object", "errors": "list"},
      "min_every": "10s"
    },
    "alice-tools/disk": {
      "package": "alice-tools",
      "command": "disk",
      "scope": "machine",
      "trust": "third-party",
      "package_source": {"url": "https://example.com/alice/tools.git", "ref": "v1", "commit": "0123abc"},
      "returns": {"used": "number"},
      "min_every": "30s"
    }
  },
  "problems": [
    {"path": "/Users/alice/.config/devmachine/packages/mine/widgets/bad/widget.yml", "message": "view.kind \"gauge\" needs engine 1.1"}
  ]
}
```

`origin` is `release` or `local`; `version` is the release tag, or `""`
for your own package. `surfaces` are the areas the widget fits, planned
ones included: the area's layout is in `fits`, the widget's view is
drawn there (in the menu bar, only `text`, `number`, `status` and
`app.brand`), and the area gives every context key the widget requires.
`single` is `true` when a board holds
the widget at most once. `available` is `false` when the widget
needs its package added and synced; `unavailable_reason` then names the
command to run (see [why widgets come from
packages](https://mydevmachine.sh/how-it-works/widgets-come-from-packages/)). A widget with a
problem is left out of `widgets` and listed in `problems`, and the command
still exits 0, so one broken widget never hides the rest. A `package.yml`
that cannot be read is a problem too: its widgets are left out, and when it
is one of your own packages the release package of the same name is not
used in its place.

`trust` says how far the app trusts the widget: `official` for the
pinned release, `local` for a package you wrote in `<config>/packages/`,
and `third-party` for a package installed with `packages install`. A
third-party widget that runs something — a `command`, `prompt`, `session`
or package provider — waits for your approval in the app, like a widget
written in a board (see [where a public widget comes
from](https://mydevmachine.sh/how-it-works/where-a-public-widget-comes-from/)). A third-party
widget also has `package_source`: `{"url", "ref", "commit"}`, where its
package was fetched from. When its `.devmachine-source.yml` cannot be
read, the widget is still third-party but has no `package_source`, and
`problems` says why. A widget that reads a package provider has
`provider`: that provider's `returns` and `min_every`. `providers` lists
every package provider a widget may read, by `<package>/<command>`, with
its package's `scope` and `trust` — a widget written in a board names one
of these. A third-party provider has `package_source` too, the same as its
widgets. The app puts that commit in what you approve for a board widget
that reads it, so when `packages update` brings new code the widget asks
again.

In the text listing, a third-party widget says `(third-party from <url>)`
in place of its origin.

`--board <area>` keeps only the widgets whose `surfaces` include that
area — what the app's gallery offers when you press "Add widget" there.
`problems` are kept as they are.

`help` prints one widget's inputs, context, sizes and the areas it fits,
and `once per board` for a single widget; with `--format json`, the same entry as `list`. `widgets help <widget>`
describes a widget; `--help` shows how to use a command.

`validate` takes a `widget.yml`, a widget folder, a package folder or a
board file. With no path it checks every board in `<config>/boards/` and
every widget in your own packages. For each widget that passes it prints
its full name and the areas it fits (`mine/clock fits home`); a widget
folder that sits in no package's widgets folder prints its name alone
(`clock fits home`). It reports every problem at once, with file and line,
and exits non-zero when there is one. `--format json` prints `{"ok":
false, "checked": [...], "widgets": [{"path": ..., "name": ...,
"surfaces": [...]}], "problems": [{"path": ..., "line": ..., "message":
...}], "warnings": [...]}`, with `name` written the same way and each
warning shaped like a problem.

A widget written in a board that names a machine or a workspace
`config.yml` does not have is a problem. A widget written in a board that
reads a package provider is checked too: the package exists and declares
it, and `every` is not below its `min_every`. With no release in the cache,
a missing package is not reported, since it may be one the release has.
`widgets add`, `move` and `remove` skip that check, so removing a package
never locks a board; they still refuse a provider name that is not
`<package>/<command>` in lower case letters, digits, dashes and
underscores. A package widget that names one
by its literal name is only a warning (`warning: …` lines, and
`"warnings"` in `--format json`), because a published widget is written
for many configurations. A name that holds a template, such as
`{{inputs.machine}}`, is not checked. `widgets add`, `move` and `remove`
never refuse a name, so removing a machine does not lock a board.

`schema` prints the engine contract: areas, providers, views and sizes.
`--json` prints it as JSON, the same document the app is built against.

`add` places a widget on a board and writes `<config>/boards/<board>.yml`.
The id defaults to the widget's name, made unique (`usage`, `usage-2`).
`--set` gives an input a value, converted to the input's type. For a
choice of many, `--set machines=main,backup` writes a list, and
`--set machines=` an empty one, which means all. A name your
`config.yml` lacks is a `warning:` on stderr (and in `"warnings"` with
`--format json`); the widget is still added. The widget must fit the area
(`devmachine widgets list --board <area>` shows which do), and a widget
marked `single` is refused when the board already has it.

On Home (the default), `--size` is a preset the widget takes, default its
`default_size`. `--at x,y` is the top-left corner in points, snapped to
8pt; the widget goes exactly there, even on top of another, because
widgets may overlap on Home. Without it the widget takes the first free
spot, scanning rows of 8pt from 24,24 across a band 1280pt wide and
keeping 8pt from every other widget. `--after` and `--before` are refused.

In the sidebar or the context sidebar, the widget goes at the end of the
list, or right after `--after <id>`, or right before `--before <id>` (one
of the two at most). `--size` is a preset or `auto`; without it the widget
gets `auto` when its view grows with its content and its `default_size`
otherwise. `--at` is refused. When the board file is missing, the CLI
starts from the board the app draws by default, so the workspace list and
the Context tab's sections stay. The default boards are listed in [the
widget format](widget-format.md#a-board-in-a-sidebar).

In the menu bar (`--board menubar`) and its popover (`--board
menubar-panel`), the widget goes in the list the same way, with
`--after` or `--before`. Neither takes `--size` or `--at`. The menu bar
holds 3 widgets, so a 4th is refused, and only a widget whose view draws
one line fits it. A missing board starts from the default, so "❯_", the
pull request count and the two tabs stay. See [the widget
format](widget-format.md#a-board-in-the-menu-bar).

`remove` takes the widget with that id off the board. On a missing
sidebar or menu bar board it starts from the default board, so
`widgets remove publish-port --board context-sidebar` drops that one
section and keeps the rest.

`move` changes a widget's turn in a list (a sidebar, the menu bar or its
popover): right after `--after <id>` or right before `--before <id>`
(exactly one). `--board` is required, and Home is refused: a widget there
has a place, not a turn. A missing board is read as the default board. A
move that leaves the order as it was does not rewrite the file. An empty
`--after ""` or `--before ""` is refused, on `add` as on `move`.

`set` changes one widget on a board and leaves every other entry as it
was. `--title` is the title this copy shows and `--every` how often it
runs (`2m`, or `manual` for any source but a provider); `--title ""` and
`--every ""` take the override off, so the widget's own comes back.
`--every` is refused below what the widget's source allows and on a
stream, with the same words as `widgets validate`. `--set` gives an input
a value as on `add`, `name=a,b` for a choice of many. A widget written in
the board takes `--title` only: to change what it runs, edit its `source`
in the board file, and the app asks for your approval again. `--board`
is required; a missing sidebar or menu bar board is read as its default
board, and a missing Home board is an error. It prints `changed <id> on
the <board> board: <what>`, then any `warning:` about a choice your
`config.yml` lacks. A `set` that changes nothing prints the same line but
does not touch the file, so its comments stay.

All four re-read the board first and write it in one step (a temporary file,
then a rename). A board with a problem is refused and left as it is; so is
a board that changed while the command ran. Comments in a board are lost
when the CLI rewrites it. `--format json` prints
`{"board", "path", "widget", "warnings"}` for `add` (`warnings` only when
there are some; for a widget in a list, which is a sidebar, the menu bar
or its popover, `frame`, `minimized` and `z` are zero and mean nothing,
and in the menu bar and its popover `size` is `""`; `collapsed` appears
when true), `{"board", "path", "removed"}` for `remove`,
`{"board", "path", "moved", "order"}` for `move`, `order` being every id
after the move, and `{"board", "path", "widget", "warnings"}` for `set`.

