import os
import re
import shutil
import subprocess
import tempfile
import unittest
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACCOUNT_CONF = os.path.join(ROOT, "zsh", "files", "tmux.conf")
BASE_TASKS = os.path.join(ROOT, "base", "tasks", "main.yml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def system_conf():
    lines = read(BASE_TASKS).splitlines()
    start = next(i for i, line in enumerate(lines) if "dest: /etc/tmux.conf" in line)
    body = start + next(i for i, line in enumerate(lines[start:]) if line.strip() == "content: |") + 1
    content = []
    for line in lines[body:]:
        if line.strip() and not line.startswith(" " * 6):
            break
        content.append(line[6:])
    return "\n".join(content).strip() + "\n"


def clipboard_overrides(text):
    return re.findall(r"terminal-overrides '?,?([^:']+):Ms=([^']+)'", text)


class ClipboardSequence(unittest.TestCase):
    def assert_sequence_reaches_every_terminal(self, text):
        overrides = clipboard_overrides(text)
        self.assertTrue(overrides, "no Ms override")
        for pattern, value in overrides:
            with self.subTest(pattern=pattern):
                self.assertIn("%p1%s", value, "tmux 3.4 sends nothing when %p1 is left out")
                self.assertTrue(value.startswith(r"\E]52;c"), "mosh forwards 52;c; only")
                self.assertIn("%p2%s", value)
        patterns = {pattern for pattern, _ in overrides}
        self.assertTrue({"xterm*", "tmux*"} <= patterns, patterns)

    def test_account_config(self):
        self.assert_sequence_reaches_every_terminal(read(ACCOUNT_CONF))

    def test_system_config(self):
        self.assert_sequence_reaches_every_terminal(system_conf())


class CopyMode(unittest.TestCase):
    def setUp(self):
        self.text = read(ACCOUNT_CONF)

    def test_a_mouse_copy_leaves_copy_mode(self):
        self.assertRegex(self.text, r"copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel\s*$|"
                         r"copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel\n")

    def test_escape_keeps_its_default_meaning(self):
        self.assertNotIn("Escape", self.text)

    def test_selection_matches_the_app(self):
        self.assertIn("set -g mode-style 'bg=#00a6b2'", self.text)


class WheelUp(unittest.TestCase):
    def test_the_first_wheel_up_scrolls_instead_of_entering_copy_mode_in_place(self):
        self.assertIn(
            "bind -n WheelUpPane if-shell -F '#{||:#{pane_in_mode},#{mouse_any_flag}}' "
            "'send-keys -M' 'copy-mode -e; send-keys -X -N 5 scroll-up'",
            system_conf())


@unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
class LoadsInTmux(unittest.TestCase):
    def tmux(self, conf, *args):
        socket = "devmachine-test-" + uuid.uuid4().hex[:8]
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as handle:
            handle.write(conf)
        try:
            subprocess.run(["tmux", "-L", socket, "-f", handle.name, "new-session", "-d"], check=True,
                           capture_output=True, text=True)
            return subprocess.run(["tmux", "-L", socket, *args], check=True, capture_output=True,
                                  text=True).stdout
        finally:
            subprocess.run(["tmux", "-L", socket, "kill-server"], capture_output=True)
            os.unlink(handle.name)

    def test_account_config_loads(self):
        conf = system_conf() + read(ACCOUNT_CONF)
        overrides = self.tmux(conf, "show", "-s", "terminal-overrides")
        self.assertIn("52;c%p1%s;%p2%s", overrides)
        keys = self.tmux(conf, "list-keys", "-T", "copy-mode-vi")
        self.assertRegex(keys, r"MouseDragEnd1Pane\s+send-keys -X copy-pipe-and-cancel\n")

    def test_wheel_up_binding_loads(self):
        keys = self.tmux(system_conf() + read(ACCOUNT_CONF), "list-keys", "-T", "root", "WheelUpPane")
        self.assertIn("copy-mode -e", keys)
        self.assertIn("send-keys -X -N 5 scroll-up", keys)


if __name__ == "__main__":
    unittest.main()
