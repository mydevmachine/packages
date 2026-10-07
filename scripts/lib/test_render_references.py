import tempfile
import unittest
from pathlib import Path

import render_references as rr

COMMANDS = """# Commands

## run

Runs a command. See [the log](#the-command-log).

## widgets

```text
## not a heading, inside a fence
devmachine widgets list
```

Boards: see [the format](widget-format.md#sizes) and [the log](#the-command-log).
Back to [widgets](#widgets) and [list](#list-and-help).

### list and help

More text.

## aliases

Not copied.

### The command log

Logged.
"""

FORMAT = """# The widget format

[Commands](commands.md#widgets), [aliases](commands.md#aliases), [whole](commands.md),
[packages](../concepts/packages.md).

## Sizes
"""

CONCEPT = """# Widgets

[The CLI](../reference/commands.md#widgets) and [the format](../reference/widget-format.md).
"""

SKILLS = {
    "boards": [
        ("concepts/widgets.md", "concepts/widgets.md"),
        ("reference/widget-format.md", "widget-format.md"),
        ("reference/commands.md", "commands-widgets.md", "widgets"),
    ],
}


class RenderReferencesTest(unittest.TestCase):
    def render(self):
        docs = Path(tempfile.mkdtemp())
        out = Path(tempfile.mkdtemp())
        (docs / "reference").mkdir()
        (docs / "concepts").mkdir()
        (docs / "reference" / "commands.md").write_text(COMMANDS)
        (docs / "reference" / "widget-format.md").write_text(FORMAT)
        (docs / "concepts" / "widgets.md").write_text(CONCEPT)
        rr.render(docs, out, SKILLS)
        return out / "boards"

    def test_a_section_stops_at_the_next_heading_outside_a_fence(self):
        text = (self.render() / "commands-widgets.md").read_text()
        self.assertTrue(text.startswith("## widgets\n"))
        self.assertIn("## not a heading, inside a fence", text)
        self.assertIn("### list and help", text)
        self.assertNotIn("## aliases", text)
        self.assertNotIn("## run", text)

    def test_links_go_to_a_copy_or_to_the_site(self):
        out = self.render()
        section = (out / "commands-widgets.md").read_text()
        self.assertIn("[the format](widget-format.md#sizes)", section)
        self.assertIn("[the log](https://mydevmachine.sh/reference/commands/#the-command-log)", section)
        self.assertIn("[widgets](#widgets)", section)
        self.assertIn("[list](#list-and-help)", section)
        fmt = (out / "widget-format.md").read_text()
        self.assertIn("[Commands](commands-widgets.md#widgets)", fmt)
        self.assertIn("[aliases](https://mydevmachine.sh/reference/commands/#aliases)", fmt)
        self.assertIn("[whole](https://mydevmachine.sh/reference/commands/)", fmt)
        self.assertIn("[packages](https://mydevmachine.sh/concepts/packages/)", fmt)
        concept = (out / "concepts" / "widgets.md").read_text()
        self.assertIn("[The CLI](../commands-widgets.md#widgets)", concept)
        self.assertIn("[the format](../widget-format.md)", concept)

    def test_a_missing_section_stops_the_render(self):
        with self.assertRaises(SystemExit):
            rr.extract_section(COMMANDS, "nope")

    def test_slug(self):
        self.assertEqual(rr.slug("The command log"), "the-command-log")
        self.assertEqual(rr.slug("`widgets add`: flags"), "widgets-add-flags")

    def test_the_real_skill_list_names_the_board_skill(self):
        files = rr.SKILLS["edit-devmachine-boards"]
        self.assertIn(("reference/commands.md", "commands-widgets.md", "widgets"), files)
        self.assertIn(("reference/widget-format.md", "widget-format.md"), files)
        self.assertIn(("concepts/widgets.md", "concepts/widgets.md"), files)


if __name__ == "__main__":
    unittest.main()
